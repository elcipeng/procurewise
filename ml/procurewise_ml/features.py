"""feature engineering, satu baris per pasangan (request, vendor kandidat).

semua fungsi di sini murni: menerima dataframe dan mengembalikan dataframe baru tanpa membaca file.
backend memanggil build_features yang sama saat inference, cukup dengan data dari database.

aturan anti leakage untuk fitur histori:
- metrik hasil (on_time_rate, avg_delay_days, defect_rate, avg_rating) dan n_transactions hanya dari
  transaksi completed dengan delivered_date < request_date, karena hasilnya baru diketahui saat barang diterima
- days_since_last_order dari transaksi dengan order_date < request_date, karena order sudah diketahui saat dibuat
- transaksi cancelled tidak dipakai untuk metrik hasil karena tanggal pembatalannya tidak tercatat
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from procurewise_ml import config

# kolom input minimum
REQUEST_COLUMNS = ("id", "material_id", "qty", "request_date", "needed_by", "priority")
CANDIDATE_COLUMNS = ("request_id", "vendor_id", "unit_price", "moq", "quoted_lead_time_days", "weekly_capacity")
TRANSACTION_COLUMNS = (
    "vendor_id", "qty", "order_date", "promised_date", "delivered_date", "qty_defect", "quality_rating", "status",
)
VENDOR_COLUMNS = ("id", "category")

OUTCOME_METRICS = ("on_time_rate", "avg_delay_days", "defect_rate", "avg_rating")


def build_features(
    requests: pd.DataFrame,
    candidates: pd.DataFrame,
    transactions: pd.DataFrame,
    vendors: pd.DataFrame,
) -> pd.DataFrame:
    """gabungkan fitur penawaran, histori, dan konteks.

    candidates adalah snapshot penawaran semua vendor untuk material request pada saat request dibuat.
    hasil berisi request_id, vendor_id, dan semua kolom config.FEATURE_COLUMNS dengan urutan yang sama.
    """
    _require(requests, REQUEST_COLUMNS, "requests")
    _require(candidates, CANDIDATE_COLUMNS, "candidates")
    _require(transactions, TRANSACTION_COLUMNS, "transactions")
    _require(vendors, VENDOR_COLUMNS, "vendors")

    pairs = candidates[list(CANDIDATE_COLUMNS)].merge(
        _clean_requests(requests).rename(columns={"id": "request_id"}),
        on="request_id", how="left", validate="many_to_one",
    )
    if pairs["request_date"].isna().any():
        raise ValueError("ada kandidat dengan request_id yang tidak ada di requests")

    offer = offer_features(pairs)
    history = history_features(pairs[["request_id", "vendor_id", "request_date"]], transactions, vendors)
    context = context_features(pairs)

    out = pd.concat([pairs[["request_id", "vendor_id"]], offer, history, context], axis=1)
    return out[["request_id", "vendor_id", *config.FEATURE_COLUMNS]]


def offer_features(pairs: pd.DataFrame) -> pd.DataFrame:
    # median dihitung dari semua penawaran untuk material yang sama pada saat request itu
    median_price = pairs.groupby("request_id")["unit_price"].transform("median")
    return pd.DataFrame({
        "unit_price": pairs["unit_price"].astype(float),
        "price_rel_median": pairs["unit_price"] / median_price,
        "total_cost": pairs["unit_price"] * pairs["qty"],
        "quoted_lead_time_days": pairs["quoted_lead_time_days"].astype(float),
        "moq_ratio": pairs["moq"] / pairs["qty"],
    }, index=pairs.index)


def context_features(pairs: pd.DataFrame) -> pd.DataFrame:
    days_available = (pairs["needed_by"] - pairs["request_date"]).dt.days
    priority = pairs["priority"].map(config.PRIORITY_CODES)
    if priority.isna().any():
        raise ValueError(f"priority tidak dikenal: {sorted(set(pairs['priority'][priority.isna()]))}")
    return pd.DataFrame({
        "slack_days": (days_available - pairs["quoted_lead_time_days"]).astype(float),
        "qty_capacity_ratio": pairs["qty"] / pairs["weekly_capacity"],
        "priority_code": priority.astype(int),
        "is_peak_season": pairs["request_date"].map(is_peak_season).astype(int),
    }, index=pairs.index)


def is_peak_season(day) -> bool:
    d = day.date() if hasattr(day, "date") else day
    return any(start <= d <= end for start, end, _ in config.PEAK_SEASONS)


def history_features(pairs: pd.DataFrame, transactions: pd.DataFrame, vendors: pd.DataFrame) -> pd.DataFrame:
    """metrik histori vendor per (request, vendor), hanya dari transaksi sebelum request_date."""
    tx = _clean_transactions(transactions)
    category = vendors.set_index("id")["category"]
    request_date = pd.to_datetime(pairs["request_date"]).to_numpy()
    vendor_ids = pairs["vendor_id"].to_numpy()
    vendor_categories = category.reindex(vendor_ids).to_numpy()

    done = tx[(tx["status"] == "completed") & tx["delivered_date"].notna()].copy()
    done["on_time"] = (done["delivered_date"] <= done["promised_date"]).astype(float)
    done["delay"] = (done["delivered_date"] - done["promised_date"]).dt.days.clip(lower=0).astype(float)
    done["category"] = category.reindex(done["vendor_id"]).to_numpy()

    own = _cumulative_stats(done, "vendor_id", vendor_ids, request_date)
    prior = _cumulative_stats(done, "category", vendor_categories, request_date)

    out = pd.DataFrame(index=pairs.index)
    has_history = own["n"] > 0
    for metric in OUTCOME_METRICS:
        # vendor tanpa histori memakai rata-rata kategori sampai request_date, lalu nilai global
        fallback = np.where(prior["n"] > 0, prior[metric], config.GLOBAL_HISTORY_DEFAULTS[metric])
        out[metric] = np.where(has_history, own[metric], fallback)
    out["n_transactions"] = own["n"].astype(int)
    out["days_since_last_order"] = _days_since_last_order(tx, vendor_ids, request_date)
    out["has_history"] = has_history.astype(int)
    return out


def _cumulative_stats(done: pd.DataFrame, key: str, keys: np.ndarray, request_date: np.ndarray) -> dict:
    """agregat transaksi selesai dengan delivered_date < request_date untuk tiap baris pasangan."""
    n = np.zeros(len(keys))
    sums = {name: np.zeros(len(keys)) for name in ("on_time", "delay", "qty_defect", "qty", "rating", "rated")}
    for value, group in done.sort_values("delivered_date", kind="stable").groupby(key, sort=True):
        rows = np.flatnonzero(keys == value)
        if len(rows) == 0:
            continue
        # side left berarti hanya transaksi yang diterima sebelum hari request
        position = np.searchsorted(group["delivered_date"].to_numpy(), request_date[rows], side="left")
        rated = group["quality_rating"].notna().astype(float).to_numpy()
        columns = {
            "on_time": group["on_time"].to_numpy(),
            "delay": group["delay"].to_numpy(),
            "qty_defect": group["qty_defect"].fillna(0).to_numpy(dtype=float),
            "qty": group["qty"].to_numpy(dtype=float),
            "rating": group["quality_rating"].fillna(0).to_numpy(dtype=float),
            "rated": rated,
        }
        n[rows] = position
        for name, values in columns.items():
            sums[name][rows] = np.concatenate([[0.0], np.cumsum(values)])[position]

    with np.errstate(invalid="ignore", divide="ignore"):
        return {
            "n": n,
            "on_time_rate": sums["on_time"] / n,
            "avg_delay_days": sums["delay"] / n,
            "defect_rate": sums["qty_defect"] / sums["qty"],
            "avg_rating": sums["rating"] / sums["rated"],
        }


def _days_since_last_order(tx: pd.DataFrame, vendor_ids: np.ndarray, request_date: np.ndarray) -> np.ndarray:
    out = np.full(len(vendor_ids), float(config.DAYS_SINCE_LAST_ORDER_CAP))
    for vendor_id, group in tx.sort_values("order_date", kind="stable").groupby("vendor_id"):
        rows = np.flatnonzero(vendor_ids == vendor_id)
        if len(rows) == 0:
            continue
        dates = group["order_date"].to_numpy()
        position = np.searchsorted(dates, request_date[rows], side="left")
        seen = position > 0
        last = dates[np.maximum(position - 1, 0)]
        days = (request_date[rows] - last) / np.timedelta64(1, "D")
        out[rows] = np.where(seen, np.minimum(days, config.DAYS_SINCE_LAST_ORDER_CAP), out[rows])
    return out


def _clean_requests(requests: pd.DataFrame) -> pd.DataFrame:
    df = requests[list(REQUEST_COLUMNS)].copy()
    for column in ("request_date", "needed_by"):
        df[column] = pd.to_datetime(df[column])
    return df


def _clean_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
    df = transactions[list(TRANSACTION_COLUMNS)].copy()
    for column in ("order_date", "promised_date", "delivered_date"):
        df[column] = pd.to_datetime(df[column])
    return df


def _require(df: pd.DataFrame, columns: tuple[str, ...], name: str) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{name} tidak punya kolom {missing}")
