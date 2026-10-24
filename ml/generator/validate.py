"""Validasi output generator dan ringkasan terminal.

Validasi membaca ulang CSV dari disk:
1. Constraint DB (kolom, NOT NULL, PK, FK, unique, enum, CHECK, panjang VARCHAR). Gagal = error.
2. Konsistensi antar file generator (label, kandidat, request). Gagal = error.
3. Pengecekan kewajaran bagian 16 spesifikasi. Di luar target = peringatan saja.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from generator import config, schema

BOOL_VALUES = {"true", "false"}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    sanity: list[tuple[str, str, str, bool]] = field(default_factory=list)

    def check(self, ok: bool, message: str) -> None:
        if not ok:
            self.errors.append(message)


def load(out_dir: Path) -> dict[str, pd.DataFrame]:
    files = [f"{t}.csv" for t in schema.TABLE_ORDER] + [
        schema.HIDDEN_TRAITS_FILE, schema.LABELS_FILE, schema.CANDIDATES_FILE, schema.REQUEST_META_FILE,
    ]
    return {
        f.removesuffix(".csv"): pd.read_csv(out_dir / f, dtype=str, keep_default_na=False)
        for f in files
    }


def _num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace("", np.nan))


def _date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series.replace("", None), format="%Y-%m-%d", errors="raise")


def validate(out_dir: Path) -> tuple[Report, dict[str, pd.DataFrame]]:
    data = load(out_dir)
    report = Report()
    _check_db_constraints(data, report)
    if not report.errors:
        _check_generator_consistency(data, report)
        _check_sanity(data, report)
    return report, data


def _check_db_constraints(data: dict[str, pd.DataFrame], r: Report) -> None:
    for table, columns in schema.TABLE_COLUMNS.items():
        df = data[table]
        r.check(tuple(df.columns) == columns, f"{table}: kolom {list(df.columns)} tidak sama dengan skema DB")
        leaked = set(df.columns) & set(schema.HIDDEN_COLUMNS)
        r.check(not leaked, f"{table}: kolom tersembunyi bocor {sorted(leaked)}")
        for column in schema.NOT_NULL[table]:
            r.check(not (df[column] == "").any(), f"{table}.{column}: ada nilai kosong")
        if len(df):
            ids = _num(df["id"])
            r.check(ids.is_unique and (ids > 0).all(), f"{table}.id: tidak unik atau tidak positif")
    if r.errors:
        return

    for (table, column), values in schema.ENUMS.items():
        bad = sorted(set(data[table][column]) - set(values))
        r.check(not bad, f"{table}.{column}: nilai di luar enum {bad}")
    for (table, column), limit in schema.MAX_LENGTHS.items():
        r.check((data[table][column].str.len() <= limit).all(), f"{table}.{column}: lebih dari {limit} karakter")
    for table, column in [("vendors", "is_active"), ("vendor_offers", "is_available")]:
        r.check(set(data[table][column]) <= BOOL_VALUES, f"{table}.{column}: bukan boolean")

    users, vendors, materials = data["users"], data["vendors"], data["materials"]
    offers, requests, tx = data["vendor_offers"], data["procurement_requests"], data["transactions"]

    # Unique
    r.check(users["email"].is_unique, "users.email: duplikat")
    r.check(materials["code"].is_unique, "materials.code: duplikat")
    r.check(not offers.duplicated(["vendor_id", "material_id"]).any(), "vendor_offers: (vendor_id, material_id) duplikat")

    # Foreign key
    def fk(child: pd.DataFrame, column: str, parent: pd.DataFrame, name: str) -> None:
        values = set(child[column]) - {""}
        missing = values - set(parent["id"])
        r.check(not missing, f"{name}.{column}: FK tidak ditemukan {sorted(missing)[:5]}")

    fk(offers, "vendor_id", vendors, "vendor_offers")
    fk(offers, "material_id", materials, "vendor_offers")
    fk(requests, "material_id", materials, "procurement_requests")
    fk(requests, "created_by", users, "procurement_requests")
    fk(tx, "vendor_id", vendors, "transactions")
    fk(tx, "material_id", materials, "transactions")
    fk(tx, "request_id", requests, "transactions")

    # CHECK vendor_offers
    for column in ("unit_price", "moq", "quoted_lead_time_days", "weekly_capacity"):
        r.check((_num(offers[column]) > 0).all(), f"vendor_offers.{column}: harus > 0")

    # CHECK procurement_requests
    r.check((_num(requests["qty"]) > 0).all(), "procurement_requests.qty: harus > 0")
    budget = _num(requests["max_budget"])
    r.check((budget.isna() | (budget > 0)).all(), "procurement_requests.max_budget: harus kosong atau > 0")
    r.check((_date(requests["needed_by"]) >= _date(requests["request_date"])).all(),
            "procurement_requests: needed_by < request_date")

    # CHECK transactions
    qty, defect, rating = _num(tx["qty"]), _num(tx["qty_defect"]), _num(tx["quality_rating"])
    order, promised, delivered = _date(tx["order_date"]), _date(tx["promised_date"]), _date(tx["delivered_date"])
    r.check((qty > 0).all(), "transactions.qty: harus > 0")
    r.check((_num(tx["unit_price"]) > 0).all(), "transactions.unit_price: harus > 0")
    r.check((promised >= order).all(), "transactions: promised_date < order_date")
    r.check((delivered.isna() | (delivered >= order)).all(), "transactions: delivered_date < order_date")
    r.check((defect.isna() | ((defect >= 0) & (defect <= qty))).all(), "transactions.qty_defect: di luar 0 s.d. qty")
    r.check((rating.isna() | rating.between(1, 5)).all(), "transactions.quality_rating: di luar 1 s.d. 5")
    r.check(((tx["status"] == "completed") == delivered.notna()).all(),
            "transactions: delivered_date harus terisi jika dan hanya jika status completed")


def _check_generator_consistency(data: dict[str, pd.DataFrame], r: Report) -> None:
    requests, tx, offers = data["procurement_requests"], data["transactions"], data["vendor_offers"]
    candidates, labels, meta = data["_candidates"], data["_labels"], data["_request_meta"]

    counts = offers.groupby("material_id").size()
    r.check(counts.min() >= 4 and len(counts) == len(data["materials"]),
            "vendor_offers: ada material dengan kurang dari 4 vendor penawar")

    r.check(set(labels["grade"]) <= {"0", "1", "2", "3"}, "_labels.grade: di luar 0 s.d. 3")
    eligible = candidates[candidates["is_eligible"] == "true"]
    key = ["request_id", "vendor_id"]
    r.check(
        len(labels) == len(eligible)
        and labels[key].merge(eligible[key], how="inner").shape[0] == len(labels),
        "_labels: tidak sama dengan kandidat yang lolos filter",
    )
    r.check(((candidates["is_eligible"] == "true") == (candidates["filter_reasons"] == "")).all(),
            "_candidates: is_eligible tidak konsisten dengan filter_reasons")

    joined = tx.merge(requests, left_on="request_id", right_on="id", suffixes=("", "_req"))
    r.check(len(joined) == len(tx), "transactions: request_id tidak lengkap")
    r.check((joined["material_id"] == joined["material_id_req"]).all(), "transactions: material beda dengan request")
    r.check((joined["order_date"] == joined["request_date"]).all(), "transactions: order_date beda dengan request_date")
    chosen = candidates[candidates["chosen"] == "true"]
    r.check(
        tx[key].merge(chosen[key], how="inner").shape[0] == len(tx) == len(chosen),
        "transactions: vendor terpilih bukan kandidat yang lolos filter",
    )
    has_tx = requests["id"].isin(tx["request_id"])
    r.check(((requests["status"] == "completed") == has_tx).all(), "procurement_requests: status tidak konsisten")
    r.check(len(meta) == len(requests), "_request_meta: jumlah baris beda dengan request")


def _check_sanity(data: dict[str, pd.DataFrame], r: Report) -> None:
    tx, traits = data["transactions"], data["_hidden_vendor_traits"]
    candidates, labels, meta = data["_candidates"], data["_labels"], data["_request_meta"]

    def add(name: str, value: float, low: float | None, high: float | None, fmt: str = "{:.1%}") -> None:
        ok = (low is None or value >= low) and (high is None or value <= high)
        target = " s.d. ".join(fmt.format(v) for v in (low, high) if v is not None)
        if low is not None and high is None:
            target = f">= {fmt.format(low)}"
        elif high is not None and low is None:
            target = f"<= {fmt.format(high)}"
        r.sanity.append((name, fmt.format(value), target, ok))

    add("Jumlah transaksi", len(tx), 1800, 2200, "{:,.0f}")

    corr = np.corrcoef(_num(traits["price_level"]), _num(traits["true_quality"]))[0, 1]
    add("Korelasi price_level vs true_quality", corr, 0.2, 0.6, "{:.2f}")

    done = tx[tx["status"] == "completed"]
    on_time = _date(done["delivered_date"]) <= _date(done["promised_date"])
    add("Tepat waktu (terhadap promised_date)", on_time.mean(), 0.70, 0.85)

    season = done.merge(meta, on="request_id")["season_intensity"].astype(float).to_numpy()
    peak, normal = on_time.to_numpy()[season >= 0.5], on_time.to_numpy()[season == 0]
    add("Selisih tepat waktu normal vs musim ramai", normal.mean() - peak.mean(), 0.10, None)

    defect_rate = _num(done["qty_defect"]).sum() / _num(done["qty"]).sum()
    add("Tingkat cacat rata-rata", defect_rate, 0.01, 0.04)
    add("Proporsi transaksi batal", (tx["status"] == "cancelled").mean(), None, 0.05)
    add("Kandidat gugur filter keras", (candidates["is_eligible"] == "false").mean(), 0.10, 0.30)
    add("Request layak jadi grup training", (meta["is_training_group"] == "true").mean(), 0.85, None)

    grades = labels["grade"].astype(int)
    add("Proporsi grade 0", (grades == 0).mean(), 0.15, 0.25)
    add("Proporsi grade 3", (grades == 3).mean(), 0.10, 0.20)

    training = meta.loc[meta["is_training_group"] == "true", "request_id"]
    group_grades = labels[labels["request_id"].isin(training)].groupby("request_id")["grade"].nunique()
    add("Grup training dengan semua grade sama", (group_grades == 1).mean(), None, 0.15)


def print_summary(report: Report, data: dict[str, pd.DataFrame], manifest: dict) -> None:
    print(f"\nSeed {manifest['seed']}, config hash {manifest['config_hash']}")

    print("\nJumlah baris")
    for filename, rows in manifest["rows"].items():
        print(f"  {filename:<28} {rows:>7,}")

    if report.errors:
        print(f"\nVALIDASI GAGAL ({len(report.errors)} error)")
        for message in report.errors:
            print(f"  - {message}")
        return
    print("\nValidasi constraint DB dan konsistensi file: OK")

    vendors, tx, traits = data["vendors"], data["transactions"], data["_hidden_vendor_traits"]
    done = tx[tx["status"] == "completed"].copy()
    done["on_time"] = _date(done["delivered_date"]) <= _date(done["promised_date"])
    done["delay"] = (_date(done["delivered_date"]) - _date(done["promised_date"])).dt.days.clip(lower=0)
    done["defect"] = _num(done["qty_defect"]) / _num(done["qty"])
    done["rating"] = _num(done["quality_rating"])
    per_vendor = done.groupby("vendor_id").agg(
        n=("id", "size"), on_time=("on_time", "mean"), delay=("delay", "mean"),
        defect=("defect", "mean"), rating=("rating", "mean"),
    )
    n_all = tx.groupby("vendor_id").size().rename("n_all")
    table = (
        vendors[["id", "name", "category"]]
        .merge(traits[["vendor_id", "archetype", "onboard_date"]], left_on="id", right_on="vendor_id")
        .merge(n_all, left_on="id", right_index=True, how="left")
        .merge(per_vendor, left_on="id", right_index=True, how="left")
    )
    table["id_num"] = table["id"].astype(int)
    print("\nOn-time rate per vendor (transaksi completed, terhadap promised_date)")
    print(f"  {'id':>3} {'vendor':<36} {'kategori':<10} {'order':>5} {'selesai':>7} {'on-time':>8}"
          f" {'telat':>6} {'cacat':>6} {'rating':>6}  catatan")
    for row in table.sort_values("id_num").itertuples():
        notes = row.archetype or ""
        if row.onboard_date != config.PERIOD_START.isoformat():
            notes = (notes + " cold start " + row.onboard_date).strip()
        if pd.isna(row.n):
            print(f"  {row.id:>3} {row.name[:36]:<36} {row.category:<10} {0 if pd.isna(row.n_all) else int(row.n_all):>5}"
                  f" {0:>7} {'-':>8} {'-':>6} {'-':>6} {'-':>6}  {notes}")
            continue
        print(f"  {row.id:>3} {row.name[:36]:<36} {row.category:<10} {int(row.n_all):>5} {int(row.n):>7}"
              f" {row.on_time:>8.1%} {row.delay:>6.1f} {row.defect:>6.1%} {row.rating:>6.2f}  {notes}")

    offers, materials = data["vendor_offers"], data["materials"]
    print("\nSebaran harga per material (Rp per satuan)")
    print(f"  {'kode':<5} {'satuan':<7} {'vendor':>6} {'min':>9} {'median':>9} {'max':>9} {'max/min':>8}"
          f" {'median transaksi':>17}")
    tx_price = tx.assign(p=_num(tx["unit_price"])).groupby("material_id")["p"].median()
    offer_price = offers.assign(p=_num(offers["unit_price"])).groupby("material_id")["p"]
    stats = offer_price.agg(["size", "min", "median", "max"])
    for m in materials.itertuples():
        s = stats.loc[m.id]
        print(f"  {m.code:<5} {m.unit:<7} {int(s['size']):>6} {s['min']:>9,.0f} {s['median']:>9,.0f}"
              f" {s['max']:>9,.0f} {s['max'] / s['min']:>8.2f} {tx_price.get(m.id, float('nan')):>17,.0f}")

    grades = data["_labels"]["grade"].value_counts().sort_index()
    total = grades.sum()
    print("\nDistribusi grade label: " + ", ".join(f"{g}: {n:,} ({n / total:.1%})" for g, n in grades.items()))

    split = data["_request_meta"].groupby("split", sort=False)["is_training_group"].agg(
        requests="size", groups=lambda s: (s == "true").sum())
    print("Request per split: " + ", ".join(f"{name} {row.requests:,} ({row.groups:,} grup training)"
                                            for name, row in split.iterrows()))

    print("\nPengecekan kewajaran (bagian 16 spesifikasi)")
    for name, value, target, ok in report.sanity:
        print(f"  [{'OK' if ok else '!!'}] {name:<44} {value:>8}   target {target}")
    outside = [name for name, _, _, ok in report.sanity if not ok]
    if outside:
        print(f"\n  {len(outside)} pengecekan di luar target. Parameter [KALIBRASI] di config.py perlu disetel.")


def load_manifest(out_dir: Path) -> dict:
    return json.loads((out_dir / schema.MANIFEST_FILE).read_text(encoding="utf-8"))
