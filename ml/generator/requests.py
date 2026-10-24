"""Procurement request historis, kandidat, dan filter keras (bagian 8 dan 9)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from generator import config
from generator.config import Material
from generator.seasons import Calendar
from generator.vendors import VendorPool, availability_prob, market_price, price_at, quoted_at

# Kode alasan gugur filter keras, sama dengan yang nanti dipakai backend
REASON_UNAVAILABLE = "tidak_tersedia"
REASON_MOQ = "moq_lebih_besar"
REASON_CAPACITY = "kapasitas_kurang"
REASON_BUDGET = "melebihi_budget"


def generate_requests(rng: np.random.Generator, materials: list[Material], calendar: Calendar) -> pd.DataFrame:
    """Request diurutkan menurut tanggal, lalu material. Id diberi sesuai urutan itu."""
    base_rates = np.array([m.monthly_rate for m in materials]) / config.DAILY_RATE_DIVISOR
    urgency_names = [u[0] for u in config.URGENCY_LEVELS]
    urgency_probs = [u[1] for u in config.URGENCY_LEVELS]
    urgency_ranges = {u[0]: u[2] for u in config.URGENCY_LEVELS}

    rows = []
    for day in range(calendar.end_idx + 1):
        if not calendar.is_working_day(day):
            continue
        s = calendar.season(day)
        counts = rng.poisson(base_rates * (1 + config.DEMAND_PEAK_FACTOR * s))
        for m, count in zip(materials, counts):
            for _ in range(int(count)):
                rows.append(_request_attributes(rng, m, day, s, urgency_names, urgency_probs, urgency_ranges))

    requests = pd.DataFrame(rows)
    requests.insert(0, "id", np.arange(1, len(requests) + 1))
    return requests


def _request_attributes(rng, m: Material, day: int, s: float, urgency_names, urgency_probs, urgency_ranges) -> dict:
    step = m.qty_step
    raw_qty = rng.lognormal(np.log(m.qty_median * (1 + config.QTY_PEAK_FACTOR * s)), config.QTY_SIGMA)
    qty = max(step, int(round(raw_qty / step)) * step)

    urgency = urgency_names[int(rng.choice(len(urgency_names), p=urgency_probs))]
    u = rng.uniform(*urgency_ranges[urgency])
    extra_weeks = max(0.0, qty / m.weekly_capacity - 1)
    needed_days = max(1, round(m.lead_time_days * u + 7 * extra_weeks))

    priority_probs = config.PRIORITY_BY_URGENCY[urgency]
    priority = config.PRIORITY_VALUES[int(rng.choice(len(priority_probs), p=priority_probs))]

    max_budget = None
    if rng.random() < config.BUDGET_PROB:
        budget = qty * market_price(m.ref_price, day, s) * rng.uniform(*config.BUDGET_RANGE)
        max_budget = float(max(1000, round(budget / 1000) * 1000))

    notes = None
    if rng.random() < config.NOTES_PROB:
        notes = config.NOTE_TEMPLATES[int(rng.integers(len(config.NOTE_TEMPLATES)))]

    created_by = int(rng.integers(1, len(config.USERS) + 1))
    created_seconds = int(rng.integers(config.WORK_HOURS[0] * 3600, config.WORK_HOURS[1] * 3600))

    return {
        "material_id": m.id,
        "request_idx": day,
        "qty": qty,
        "needed_by_idx": day + needed_days,
        "priority": priority,
        "max_budget": max_budget,
        "notes": notes,
        "created_by": created_by,
        "created_seconds": created_seconds,
        "urgency": urgency,
        "season": s,
    }


def build_candidates(rng: np.random.Generator, request, pool: VendorPool) -> pd.DataFrame:
    """Snapshot penawaran semua vendor aktif untuk material request, lalu filter keras."""
    offers = pool.offers_for(request.material_id)
    onboard = pool.vendors.set_index("id")["onboard_idx"]
    offers = offers[onboard.loc[offers["vendor_id"]].to_numpy() <= request.request_idx]

    weeks_available = max(1.0, (request.needed_by_idx - request.request_idx) / 7)
    rows = []
    for offer in offers.itertuples():
        unit_price = price_at(offer.base_price, request.request_idx, request.season)
        available = bool(rng.random() < availability_prob(request.season))

        reasons = []
        if not available:
            reasons.append(REASON_UNAVAILABLE)
        if offer.moq > request.qty:
            reasons.append(REASON_MOQ)
        if request.qty > offer.weekly_capacity * weeks_available:
            reasons.append(REASON_CAPACITY)
        if request.max_budget is not None and not pd.isna(request.max_budget) \
                and unit_price * request.qty > request.max_budget:
            reasons.append(REASON_BUDGET)

        rows.append({
            "request_id": request.id,
            "vendor_id": offer.vendor_id,
            "unit_price": unit_price,
            "moq": offer.moq,
            "quoted_lead_time_days": quoted_at(offer.quoted_base, request.season),
            "weekly_capacity": offer.weekly_capacity,
            "is_available": available,
            "is_eligible": not reasons,
            "filter_reasons": reasons,
            "lead_time_true": offer.lead_time_true,
        })
    return pd.DataFrame(rows)
