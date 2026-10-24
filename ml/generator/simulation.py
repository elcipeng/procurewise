"""Simulasi hasil pesanan (bagian 11).

Fungsi yang sama dipakai untuk transaksi historis (1 simulasi) dan label (K simulasi).
Semua angka acak selalu diambil dengan jumlah yang sama, termasuk untuk pesanan yang batal,
supaya pemakaian aliran acak tidak bergantung pada hasil simulasi.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from generator import config
from generator.seasons import Calendar


@dataclass
class SimResult:
    promised_idx: int
    delivered_idx: np.ndarray
    cancelled: np.ndarray
    qty_defect: np.ndarray
    rating: np.ndarray


def promised_idx(order_idx: int, qty: int, quoted_lead_time: int, weekly_capacity: int) -> int:
    # Vendor menjanjikan tanggal dari kapasitas nominal, bukan kapasitas efektif saat musim ramai
    extra_weeks = max(0, math.ceil(qty / weekly_capacity) - 1)
    return order_idx + quoted_lead_time + 7 * extra_weeks


def simulate_orders(
    rng: np.random.Generator,
    n: int,
    *,
    calendar: Calendar,
    order_idx: int,
    qty: int,
    quoted_lead_time: int,
    weekly_capacity: int,
    lead_time_true: float,
    reliability: float,
    quality: float,
    defect_base: float,
) -> SimResult:
    s = calendar.season(order_idx)
    unreliability = 1.0 - reliability
    promised = promised_idx(order_idx, qty, quoted_lead_time, weekly_capacity)

    # 11.2 Lead time aktual
    effective_capacity = weekly_capacity / (1 + config.CAPACITY_PEAK_FACTOR * s)
    load = qty / effective_capacity
    production_days = lead_time_true * (1 + config.LEAD_TIME_PEAK_FACTOR * s) + 7 * max(0.0, load - 1)
    noise = rng.lognormal(0.0, config.NOISE_SIGMA_BASE + config.NOISE_SIGMA_UNRELIABLE * unreliability, n)
    p_disruption = config.DISRUPTION_BASE + config.DISRUPTION_UNRELIABLE * unreliability + config.DISRUPTION_PEAK * s
    disrupted = rng.random(n) < p_disruption
    disruption_days = rng.gamma(config.DISRUPTION_GAMMA_SHAPE, config.DISRUPTION_GAMMA_SCALE, n) * disrupted
    total_days = np.ceil(production_days * noise + disruption_days).astype(int)
    # Vendor berhenti produksi selama libur Lebaran
    total_days = total_days + calendar.closed_days(order_idx, total_days)
    delivered = order_idx + total_days

    # 11.5 Pembatalan
    cancelled = rng.random(n) < config.CANCEL_BASE + config.CANCEL_UNRELIABLE * unreliability

    # 11.3 Cacat
    rushed = 1.0 if load > 1 else 0.0
    p_defect = min(
        defect_base
        * math.exp(config.DEFECT_QUALITY_SLOPE * (config.DEFECT_QUALITY_PIVOT - quality))
        * (1 + config.DEFECT_PEAK_FACTOR * s)
        * (1 + config.DEFECT_RUSH_FACTOR * rushed),
        config.DEFECT_MAX,
    )
    concentration = config.DEFECT_BETA_CONCENTRATION
    p_draw = rng.beta(concentration * p_defect, concentration * (1 - p_defect), n)
    qty_defect = rng.binomial(qty, p_draw)

    # 11.4 Rating
    delay = delivered - promised
    latent = (
        config.RATING_INTERCEPT
        + config.RATING_QUALITY * quality
        - config.RATING_DEFECT * (qty_defect / qty)
        - config.RATING_DELAY * np.maximum(0, delay)
        + rng.normal(0.0, config.RATING_NOISE, n)
    )
    rating = np.clip(np.rint(latent), 1, 5).astype(int)

    return SimResult(promised, delivered, cancelled, qty_defect, rating)
