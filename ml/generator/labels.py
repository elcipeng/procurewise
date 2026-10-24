"""Label relevansi dari simulasi kontrafaktual (bagian 13).

Label dihitung dari hasil pesanan yang disimulasikan memakai karakter tersembunyi vendor,
bukan dari fitur yang dilihat model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from generator import config
from generator.config import Material
from generator.seasons import Calendar
from generator.simulation import simulate_orders


def label_group(
    rng: np.random.Generator,
    request,
    eligible: pd.DataFrame,
    vendors: pd.DataFrame,
    material: Material,
    calendar: Calendar,
) -> list[dict]:
    outcomes = []
    for candidate in eligible.itertuples():
        vendor = vendors.loc[candidate.vendor_id]
        result = simulate_orders(
            rng, config.LABEL_SIMULATIONS,
            calendar=calendar,
            order_idx=request.request_idx,
            qty=request.qty,
            quoted_lead_time=candidate.quoted_lead_time_days,
            weekly_capacity=candidate.weekly_capacity,
            lead_time_true=candidate.lead_time_true,
            reliability=vendor.true_reliability,
            quality=vendor.true_quality,
            defect_base=material.defect_base,
        )
        delivered_ok = ~result.cancelled
        # Ketepatan diukur terhadap needed_by (kebutuhan Firaza), bukan promised_date
        on_time = delivered_ok & (result.delivered_idx <= request.needed_by_idx)
        if delivered_ok.any():
            defect_rate = float(np.mean(result.qty_defect[delivered_ok] / request.qty))
            mean_defect = float(np.mean(result.qty_defect[delivered_ok]))
        else:
            defect_rate, mean_defect = 1.0, float(request.qty)
        outcomes.append({
            "request_id": int(request.id),
            "vendor_id": int(candidate.vendor_id),
            "p_tepat": float(on_time.mean()),
            "e_cacat": defect_rate,
            # Barang cacat dianggap harus dibeli ulang
            "e_biaya": candidate.unit_price * (request.qty + mean_defect),
        })

    w_time, w_defect, w_cost = config.LABEL_WEIGHTS[request.priority]
    min_cost = min(o["e_biaya"] for o in outcomes)
    high, mid = config.GRADE_THRESHOLDS
    for o in outcomes:
        score = (
            w_time * o["p_tepat"]
            + w_defect * (1 - min(1.0, o["e_cacat"] / config.GATE_MAX_DEFECT))
            + w_cost * (min_cost / o["e_biaya"])
        )
        o["skor_hasil"] = score
        if o["p_tepat"] < config.GATE_MIN_ON_TIME or o["e_cacat"] > config.GATE_MAX_DEFECT:
            o["grade"] = 0
        elif score >= high:
            o["grade"] = 3
        elif score >= mid:
            o["grade"] = 2
        else:
            o["grade"] = 1
    return outcomes
