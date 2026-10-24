"""Pemilihan vendor historis dan transaksi (bagian 10 dan 12)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from generator import config
from generator.config import Material
from generator.seasons import Calendar
from generator.simulation import simulate_orders
from generator.vendors import round_price


def choose_vendor(rng: np.random.Generator, eligible: pd.DataFrame, order_counts: dict[int, int]) -> int:
    """Kebijakan pemilihan Firaza di masa lalu: bias ke harga murah dan vendor langganan."""
    n = len(eligible)
    explore = rng.random() < config.CHOICE_EXPLORATION
    random_pick = int(rng.integers(n))
    gumbel = rng.gumbel(0.0, 1.0, n)

    prices = eligible["unit_price"].to_numpy(dtype=float)
    std = prices.std()
    z_price = (prices - prices.mean()) / std if std > 0 else np.zeros(n)
    familiarity = np.log1p([order_counts[v] for v in eligible["vendor_id"]])
    score = -config.CHOICE_PRICE_WEIGHT * z_price + config.CHOICE_FAMILIARITY_WEIGHT * familiarity + gumbel

    position = random_pick if explore else int(np.argmax(score))
    return int(eligible["vendor_id"].iloc[position])


def make_transaction(
    rng: np.random.Generator,
    request,
    candidate,
    vendor,
    material: Material,
    calendar: Calendar,
) -> dict:
    unit_price = round_price(candidate.unit_price * rng.lognormal(0.0, config.TX_PRICE_NOISE_SIGMA))
    result = simulate_orders(
        rng, 1,
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

    delivered = int(result.delivered_idx[0])
    if result.cancelled[0]:
        status = "cancelled"
    elif delivered > calendar.end_idx:
        # Barang belum diterima di akhir periode data
        status = "in_progress"
    else:
        status = "completed"
    done = status == "completed"

    return {
        "vendor_id": int(candidate.vendor_id),
        "material_id": material.id,
        "request_id": int(request.id),
        "qty": int(request.qty),
        "unit_price": unit_price,
        "order_idx": int(request.request_idx),
        "promised_idx": result.promised_idx,
        "delivered_idx": delivered if done else None,
        "qty_defect": int(result.qty_defect[0]) if done else None,
        "quality_rating": int(result.rating[0]) if done else None,
        "status": status,
        "created_seconds": int(request.created_seconds),
    }
