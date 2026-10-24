"""filter keras sebelum ranking (ml/README.md bagian 9). dipakai juga oleh backend."""

from __future__ import annotations

import numpy as np
import pandas as pd

REASON_UNAVAILABLE = "tidak_tersedia"
REASON_MOQ = "moq_lebih_besar"
REASON_CAPACITY = "kapasitas_kurang"
REASON_BUDGET = "melebihi_budget"


def hard_filter(requests: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    """kembalikan candidates dengan kolom is_eligible dan filter_reasons (list kode alasan).

    requests butuh kolom id, qty, request_date, needed_by, max_budget.
    candidates butuh kolom request_id, unit_price, moq, weekly_capacity, is_available.
    """
    df = candidates.merge(
        requests[["id", "qty", "request_date", "needed_by", "max_budget"]].rename(columns={"id": "request_id"}),
        on="request_id", how="left", validate="many_to_one",
    )
    days = (pd.to_datetime(df["needed_by"]) - pd.to_datetime(df["request_date"])).dt.days
    weeks_available = np.maximum(1.0, days / 7)

    checks = {
        REASON_UNAVAILABLE: ~df["is_available"].astype(bool),
        REASON_MOQ: df["moq"] > df["qty"],
        REASON_CAPACITY: df["qty"] > df["weekly_capacity"] * weeks_available,
        REASON_BUDGET: df["max_budget"].notna() & (df["unit_price"] * df["qty"] > df["max_budget"]),
    }
    reasons = [[] for _ in range(len(df))]
    for code, failed in checks.items():
        for i in np.flatnonzero(failed.to_numpy()):
            reasons[i].append(code)

    out = candidates.copy()
    out["filter_reasons"] = reasons
    out["is_eligible"] = [not r for r in reasons]
    return out
