"""pemeriksaan kebocoran data pada fitur.

pemakaian dari folder ml:
    python -m procurewise_ml.leakage_check

1. statis: daftar fitur tidak memuat kolom label atau karakter tersembunyi, modul fitur tidak membaca file tersembunyi
2. perturbasi masa depan: transaksi setelah cutoff dirusak dan ditambah transaksi palsu, fitur request
   sebelum cutoff harus tetap identik
3. brute force: fitur histori dihitung ulang dengan cara naif untuk sampel pasangan, hasilnya harus sama
4. korelasi: tidak ada fitur yang hampir sempurna menebak grade
"""

from __future__ import annotations

import inspect
import sys

import numpy as np
import pandas as pd

from procurewise_ml import config, data, features, filters
from procurewise_ml.features import build_features

CUTOFFS = ("2025-08-01", "2025-12-15", "2026-03-20", "2026-07-01")
SAMPLE_PAIRS = 400
SUSPICIOUS_CORRELATION = 0.8


def check_static() -> list[str]:
    problems = []
    overlap = set(config.FEATURE_COLUMNS) & set(config.FORBIDDEN_FEATURE_COLUMNS)
    if overlap:
        problems.append(f"fitur memuat kolom terlarang {sorted(overlap)}")
    for module in (features, filters):
        source = inspect.getsource(module)
        for word in ("_hidden", "vendor_traits", "_labels", "true_quality", "true_reliability", "price_level"):
            if word in source:
                problems.append(f"{module.__name__} menyebut {word!r}")
    if any("hidden" in f for f in data.FEATURE_SOURCES.values()):
        problems.append("data.FEATURE_SOURCES memuat file tersembunyi")
    return problems


def _corrupt_future(tx: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    tx = tx.copy()
    known_after = tx["delivered_date"] >= cutoff
    tx.loc[known_after, "delivered_date"] += pd.Timedelta(days=30)
    tx.loc[known_after, "qty_defect"] = tx.loc[known_after, "qty"]
    tx.loc[known_after, "quality_rating"] = 1
    ordered_after = tx["order_date"] >= cutoff
    tx.loc[ordered_after, "order_date"] += pd.Timedelta(days=5)
    # transaksi palsu untuk setiap vendor tepat di hari cutoff
    fake = tx.drop_duplicates("vendor_id").copy()
    fake["order_date"] = cutoff
    fake["promised_date"] = cutoff
    fake["delivered_date"] = cutoff + pd.Timedelta(days=60)
    fake["status"] = "completed"
    fake["qty_defect"] = fake["qty"]
    fake["quality_rating"] = 1
    return pd.concat([tx, fake], ignore_index=True)


def check_future_perturbation(raw: data.RawData, base: pd.DataFrame) -> list[str]:
    problems = []
    request_dates = raw.requests.set_index("id")["request_date"]
    for cutoff_text in CUTOFFS:
        cutoff = pd.Timestamp(cutoff_text)
        corrupted = build_features(raw.requests, raw.candidates, _corrupt_future(raw.transactions, cutoff), raw.vendors)
        before = request_dates.reindex(base["request_id"]).to_numpy() <= cutoff
        columns = list(config.FEATURE_COLUMNS)
        a = base.loc[before, columns].to_numpy(dtype=float)
        b = corrupted.loc[before, columns].to_numpy(dtype=float)
        changed = ~np.isclose(a, b, equal_nan=True)
        if changed.any():
            bad = sorted({columns[j] for j in np.flatnonzero(changed.any(axis=0))})
            problems.append(f"cutoff {cutoff_text}: fitur {bad} berubah karena data masa depan")
        else:
            print(f"  cutoff {cutoff_text}: {int(before.sum()):,} pasangan, fitur identik")
    return problems


def _naive_history(row, tx: pd.DataFrame, category: pd.Series) -> dict:
    done = tx[(tx["status"] == "completed") & (tx["delivered_date"] < row.request_date)]
    own = done[done["vendor_id"] == row.vendor_id]
    pool = own if len(own) else done[done["vendor_id"].map(category) == category[row.vendor_id]]

    def metrics(df: pd.DataFrame) -> dict:
        if len(df) == 0:
            return dict(config.GLOBAL_HISTORY_DEFAULTS)
        delay = (df["delivered_date"] - df["promised_date"]).dt.days
        return {
            "on_time_rate": (delay <= 0).mean(),
            "avg_delay_days": delay.clip(lower=0).mean(),
            "defect_rate": df["qty_defect"].sum() / df["qty"].sum(),
            "avg_rating": df["quality_rating"].mean(),
        }

    out = metrics(pool)
    out["n_transactions"] = len(own)
    out["has_history"] = int(len(own) > 0)
    orders = tx[(tx["vendor_id"] == row.vendor_id) & (tx["order_date"] < row.request_date)]
    out["days_since_last_order"] = (
        min((row.request_date - orders["order_date"].max()).days, config.DAYS_SINCE_LAST_ORDER_CAP)
        if len(orders) else config.DAYS_SINCE_LAST_ORDER_CAP
    )
    return out


def check_brute_force(raw: data.RawData, base: pd.DataFrame) -> list[str]:
    rng = np.random.default_rng(0)
    sample = base.loc[rng.choice(len(base), SAMPLE_PAIRS, replace=False)]
    sample = sample.merge(raw.requests[["id", "request_date"]], left_on="request_id", right_on="id")
    category = raw.vendors.set_index("id")["category"]
    problems = []
    for row in sample.itertuples():
        expected = _naive_history(row, raw.transactions, category)
        for name, value in expected.items():
            if not np.isclose(getattr(row, name), value):
                problems.append(f"request {row.request_id} vendor {row.vendor_id}: {name} {getattr(row, name)} != {value}")
    print(f"  {len(sample)} pasangan acak dicek ulang dengan cara naif")
    return problems[:10]


def check_correlation(dataset: pd.DataFrame) -> list[str]:
    eligible = dataset[dataset["is_eligible"]]
    corr = eligible[list(config.FEATURE_COLUMNS)].corrwith(eligible["grade"].astype(float), method="spearman")
    print("  korelasi spearman fitur vs grade (kandidat lolos filter):")
    for name, value in corr.sort_values(key=np.abs, ascending=False).items():
        print(f"    {name:<24} {value:+.3f}")
    suspicious = corr[corr.abs() > SUSPICIOUS_CORRELATION]
    return [f"{name} terlalu kuat menebak grade ({value:+.2f})" for name, value in suspicious.items()]


def main() -> int:
    from procurewise_ml.build_dataset import build_dataset

    raw = data.load_raw()
    base = build_features(raw.requests, raw.candidates, raw.transactions, raw.vendors)
    dataset = build_dataset(raw)

    results = {}
    print("1. pemeriksaan statis")
    results["statis"] = check_static()
    print("2. perturbasi data masa depan")
    results["perturbasi"] = check_future_perturbation(raw, base)
    print("3. hitung ulang brute force")
    results["brute force"] = check_brute_force(raw, base)
    print("4. korelasi dengan label")
    results["korelasi"] = check_correlation(dataset)

    failed = False
    print("\nhasil")
    for name, problems in results.items():
        print(f"  {name:<12} {'lolos' if not problems else 'GAGAL'}")
        for problem in problems:
            print(f"    - {problem}")
        failed |= bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
