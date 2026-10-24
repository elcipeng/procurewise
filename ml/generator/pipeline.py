"""Alur utama generator: vendor, request, transaksi, label, lalu tulis CSV."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from generator import config, schema
from generator.labels import label_group
from generator.requests import build_candidates, generate_requests
from generator.seasons import Calendar
from generator.transactions import choose_vendor, make_transaction
from generator.vendors import VendorPool, availability_prob, build_vendor_pool, price_at, quoted_at


@dataclass
class GeneratedData:
    tables: dict[str, pd.DataFrame]
    extras: dict[str, pd.DataFrame]


def run(seed: int) -> GeneratedData:
    streams = np.random.SeedSequence(seed).spawn(len(config.RNG_STREAMS))
    rng = {name: np.random.default_rng(s) for name, s in zip(config.RNG_STREAMS, streams)}

    calendar = Calendar()
    materials = config.load_materials()
    by_id = {m.id: m for m in materials}
    pool = build_vendor_pool(rng["vendors"], rng["offers"], materials, calendar)
    vendors = pool.vendors.set_index("id")
    requests = generate_requests(rng["requests"], materials, calendar)

    order_counts = {int(v): 0 for v in vendors.index}
    candidate_frames, transactions, labels, meta, statuses = [], [], [], [], []

    # Request diproses berurutan menurut tanggal karena pilihan vendor bergantung pada histori
    for request in requests.itertuples():
        material = by_id[request.material_id]
        candidates = build_candidates(rng["availability"], request, pool)
        eligible = candidates[candidates["is_eligible"]]
        chosen_vendor = None

        if len(eligible) > 0:
            chosen_vendor = choose_vendor(rng["choice"], eligible, order_counts)
            chosen = eligible[eligible["vendor_id"] == chosen_vendor].iloc[0]
            transactions.append(make_transaction(
                rng["transactions"], request, chosen, vendors.loc[chosen_vendor], material, calendar,
            ))
            order_counts[chosen_vendor] += 1
            labels += label_group(rng["labels"], request, eligible, vendors, material, calendar)

        candidates["chosen"] = candidates["vendor_id"] == chosen_vendor
        candidate_frames.append(candidates)
        # Request tanpa kandidat lolos dianggap batal
        statuses.append("completed" if chosen_vendor is not None else "cancelled")
        meta.append({
            "request_id": int(request.id),
            "split": calendar.split_of(request.request_idx),
            "urgency": request.urgency,
            "season_intensity": round(request.season, 4),
            "n_candidates": len(candidates),
            "n_eligible": len(eligible),
            "is_training_group": len(eligible) >= 2,
        })

    requests["status"] = statuses
    candidates_all = pd.concat(candidate_frames, ignore_index=True)

    tables = {
        "users": _users_table(calendar),
        "materials": _materials_table(materials, calendar),
        "vendors": _vendors_table(pool, calendar),
        "vendor_offers": _vendor_offers_table(rng["availability"], pool, calendar),
        "procurement_requests": _requests_table(requests, calendar),
        "transactions": _transactions_table(pd.DataFrame(transactions), calendar),
        "recommendations": pd.DataFrame(columns=schema.TABLE_COLUMNS["recommendations"]),
    }
    extras = {
        schema.HIDDEN_TRAITS_FILE: _hidden_traits_table(pool, calendar),
        schema.LABELS_FILE: _labels_table(pd.DataFrame(labels)),
        schema.CANDIDATES_FILE: _candidates_table(candidates_all),
        schema.REQUEST_META_FILE: _bool_columns(pd.DataFrame(meta), ["is_training_group"]),
    }
    return GeneratedData(tables=tables, extras=extras)


def write(data: GeneratedData, out_dir: Path, seed: int) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in schema.TABLE_ORDER:
        df = data.tables[name]
        assert tuple(df.columns) == schema.TABLE_COLUMNS[name], f"Kolom {name} tidak sesuai skema"
        files[f"{name}.csv"] = df
    files.update(data.extras)

    hashes = {}
    for filename, df in files.items():
        path = out_dir / filename
        df.to_csv(path, index=False, lineterminator="\n", na_rep="")
        hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()

    manifest = {
        "seed": seed,
        "config_hash": config.config_hash(),
        "period": [config.PERIOD_START.isoformat(), config.PERIOD_END.isoformat()],
        "rows": {filename: len(df) for filename, df in files.items()},
        "sha256": hashes,
    }
    (out_dir / schema.MANIFEST_FILE).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


# ---------------------------------------------------------------------------
# Format kolom
# ---------------------------------------------------------------------------


def _timestamp(d: date, seconds: int = 8 * 3600) -> str:
    t = timedelta(seconds=int(seconds))
    hh, rem = divmod(int(t.total_seconds()), 3600)
    mm, ss = divmod(rem, 60)
    return f"{d.isoformat()} {hh:02d}:{mm:02d}:{ss:02d}{config.TZ_SUFFIX}"


def _money(value) -> str | None:
    return None if value is None or pd.isna(value) else f"{value:.2f}"


def _bool_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        df[column] = df[column].map({True: "true", False: "false"})
    return df


def _users_table(calendar: Calendar) -> pd.DataFrame:
    created = _timestamp(calendar.start)
    rows = [
        {"id": i, "name": name, "email": email, "role": role, "created_at": created, "updated_at": created}
        for i, name, email, role in config.USERS
    ]
    return pd.DataFrame(rows, columns=schema.TABLE_COLUMNS["users"])


def _materials_table(materials, calendar: Calendar) -> pd.DataFrame:
    created = _timestamp(calendar.start)
    rows = [
        {"id": m.id, "code": m.code, "name": m.name, "category": m.category, "unit": m.unit,
         "created_at": created, "updated_at": created}
        for m in materials
    ]
    return pd.DataFrame(rows, columns=schema.TABLE_COLUMNS["materials"])


def _vendors_table(pool: VendorPool, calendar: Calendar) -> pd.DataFrame:
    df = pool.vendors.copy()
    df["is_active"] = True
    df["created_at"] = [_timestamp(calendar.to_date(i)) for i in df["onboard_idx"]]
    df["updated_at"] = df["created_at"]
    df = _bool_columns(df, ["is_active"])
    return df[list(schema.TABLE_COLUMNS["vendors"])]


def _vendor_offers_table(rng: np.random.Generator, pool: VendorPool, calendar: Calendar) -> pd.DataFrame:
    """Snapshot penawaran per akhir periode data (bagian 6)."""
    end = calendar.end_idx
    s = calendar.season(end)
    onboard = pool.vendors.set_index("id")["onboard_idx"]
    rows = []
    for i, offer in enumerate(pool.offers.itertuples(), 1):
        available = bool(rng.random() < availability_prob(s))
        earliest = max(end - config.OFFER_UPDATED_WINDOW_DAYS, int(onboard[offer.vendor_id]))
        updated_idx = int(rng.integers(earliest, end + 1))
        seconds = int(rng.integers(config.WORK_HOURS[0] * 3600, config.WORK_HOURS[1] * 3600))
        rows.append({
            "id": i,
            "vendor_id": int(offer.vendor_id),
            "material_id": int(offer.material_id),
            "unit_price": _money(price_at(offer.base_price, end, s)),
            "moq": int(offer.moq),
            "quoted_lead_time_days": quoted_at(offer.quoted_base, s),
            "weekly_capacity": int(offer.weekly_capacity),
            "is_available": available,
            "updated_at": _timestamp(calendar.to_date(updated_idx), seconds),
        })
    df = _bool_columns(pd.DataFrame(rows), ["is_available"])
    return df[list(schema.TABLE_COLUMNS["vendor_offers"])]


def _requests_table(requests: pd.DataFrame, calendar: Calendar) -> pd.DataFrame:
    df = pd.DataFrame({
        "id": requests["id"],
        "material_id": requests["material_id"],
        "qty": requests["qty"],
        "request_date": [calendar.to_date(i).isoformat() for i in requests["request_idx"]],
        "needed_by": [calendar.to_date(i).isoformat() for i in requests["needed_by_idx"]],
        "priority": requests["priority"],
        "max_budget": [_money(v) for v in requests["max_budget"]],
        "notes": requests["notes"],
        "created_by": requests["created_by"],
        "status": requests["status"],
        "created_at": [
            _timestamp(calendar.to_date(i), sec)
            for i, sec in zip(requests["request_idx"], requests["created_seconds"])
        ],
    })
    return df[list(schema.TABLE_COLUMNS["procurement_requests"])]


def _transactions_table(tx: pd.DataFrame, calendar: Calendar) -> pd.DataFrame:
    def to_date(idx):
        return None if idx is None or pd.isna(idx) else calendar.to_date(int(idx)).isoformat()

    def to_int(value):
        return None if value is None or pd.isna(value) else int(value)

    df = pd.DataFrame({
        "id": np.arange(1, len(tx) + 1),
        "vendor_id": tx["vendor_id"],
        "material_id": tx["material_id"],
        "request_id": tx["request_id"],
        "qty": tx["qty"],
        "unit_price": [_money(v) for v in tx["unit_price"]],
        "order_date": [to_date(i) for i in tx["order_idx"]],
        "promised_date": [to_date(i) for i in tx["promised_idx"]],
        "delivered_date": [to_date(i) for i in tx["delivered_idx"]],
        "qty_defect": pd.array([to_int(v) for v in tx["qty_defect"]], dtype="Int64"),
        "quality_rating": pd.array([to_int(v) for v in tx["quality_rating"]], dtype="Int64"),
        "status": tx["status"],
        "created_at": [_timestamp(calendar.to_date(i), sec) for i, sec in zip(tx["order_idx"], tx["created_seconds"])],
    })
    return df[list(schema.TABLE_COLUMNS["transactions"])]


def _hidden_traits_table(pool: VendorPool, calendar: Calendar) -> pd.DataFrame:
    df = pool.vendors[[
        "id", "vendor_type", "archetype", "onboard_idx", *config.TRAIT_NAMES,
        "price_level", "true_quality", "true_reliability", "lead_time_factor", "capacity_factor",
    ]].copy()
    df = df.rename(columns={"id": "vendor_id"})
    df["onboard_date"] = [calendar.to_date(i).isoformat() for i in df.pop("onboard_idx")]
    for column in [*config.TRAIT_NAMES, "price_level", "true_quality", "true_reliability",
                   "lead_time_factor", "capacity_factor"]:
        df[column] = df[column].round(6)
    return df


def _labels_table(labels: pd.DataFrame) -> pd.DataFrame:
    for column in ("p_tepat", "e_cacat", "skor_hasil"):
        labels[column] = labels[column].round(6)
    labels["e_biaya"] = labels["e_biaya"].round(2)
    return labels[["request_id", "vendor_id", "p_tepat", "e_cacat", "e_biaya", "skor_hasil", "grade"]]


def _candidates_table(candidates: pd.DataFrame) -> pd.DataFrame:
    df = candidates.drop(columns=["lead_time_true"]).copy()
    df["unit_price"] = [_money(v) for v in df["unit_price"]]
    # Format sama dengan kolom JSONB recommendations.filter_reasons
    df["filter_reasons"] = [json.dumps(r) if r else None for r in df["filter_reasons"]]
    return _bool_columns(df, ["is_available", "is_eligible", "chosen"])
