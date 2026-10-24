"""Vendor, karakter tersembunyi, dan penawaran (bagian 5 dan 6)."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from generator import config
from generator.config import Material
from generator.seasons import Calendar


@dataclass
class VendorPool:
    # Satu baris per vendor. Berisi kolom publik dan karakter tersembunyi
    vendors: pd.DataFrame
    # Satu baris per (vendor, material). Berisi syarat dasar penawaran dan lead time asli
    offers: pd.DataFrame

    def offers_for(self, material_id: int) -> pd.DataFrame:
        return self.offers[self.offers["material_id"] == material_id]


def build_vendor_pool(
    rng_vendors: np.random.Generator,
    rng_offers: np.random.Generator,
    materials: list[Material],
    calendar: Calendar,
) -> VendorPool:
    vendors = _vendor_skeleton(rng_vendors)
    offered = _offer_structure(rng_offers, vendors, materials)
    vendors["onboard_idx"] = _cold_start(rng_vendors, vendors, offered, materials, calendar)
    vendors = pd.concat([vendors, _traits(rng_vendors, vendors, materials)], axis=1)
    offers = _offer_terms(rng_offers, vendors, offered, materials)
    return VendorPool(vendors=vendors, offers=offers)


def round_price(value: float) -> float:
    """Bulatkan ke Rp100 untuk harga di atas Rp5.000, ke Rp50 untuk sisanya."""
    step = 100 if value > 5000 else 50
    return float(max(step, round(value / step) * step))


def market_price(base_price: float, day_idx: int, season: float) -> float:
    """Harga setelah inflasi dan kenaikan musim ramai, belum dibulatkan."""
    inflation = (1 + config.MONTHLY_INFLATION) ** (day_idx / config.DAYS_PER_MONTH)
    return base_price * inflation * (1 + config.PEAK_PRICE_SURCHARGE * season)


def price_at(base_price: float, day_idx: int, season: float) -> float:
    return round_price(market_price(base_price, day_idx, season))


def quoted_at(quoted_base: float, season: float) -> int:
    return max(1, round(quoted_base * (1 + config.PEAK_QUOTE_EXTRA * season)))


def availability_prob(season: float) -> float:
    return config.AVAILABILITY_BASE - config.AVAILABILITY_PEAK_DROP * season


def _pick(rng: np.random.Generator, items: tuple | list, weights: tuple | list | None = None):
    idx = rng.choice(len(items), p=None if weights is None else np.asarray(weights, dtype=float))
    return items[int(idx)]


def _vendor_skeleton(rng: np.random.Generator) -> pd.DataFrame:
    rows, used_names = [], set()
    for vtype in config.VENDOR_TYPES:
        for _ in range(vtype.count):
            while True:
                prefix = _pick(rng, config.NAME_PREFIXES)
                w1, w2 = (config.NAME_WORDS[int(i)] for i in rng.choice(len(config.NAME_WORDS), 2, replace=False))
                suffix = _pick(rng, vtype.name_suffixes)
                name = f"{prefix} {w1} {w2} {suffix}"
                if name not in used_names:
                    used_names.add(name)
                    break
            cities, city_weights = zip(*vtype.cities)
            terms, term_weights = zip(*config.PAYMENT_TERMS)
            rows.append({
                "id": len(rows) + 1,
                "name": name,
                "category": vtype.category,
                "city": _pick(rng, cities, city_weights),
                # Kontak fiktif, domain example.com dicadangkan untuk contoh
                "contact": re.sub(r"[^a-z]", "", f"{w1}{w2}{suffix}".lower()) + "@example.com",
                "payment_terms": _pick(rng, terms, term_weights),
                "vendor_type": vtype.key,
            })
    return pd.DataFrame(rows)


def _offer_structure(
    rng: np.random.Generator, vendors: pd.DataFrame, materials: list[Material]
) -> dict[int, list[str]]:
    types = {vtype.key: vtype for vtype in config.VENDOR_TYPES}
    order = {m.code: i for i, m in enumerate(materials)}
    offered: dict[int, list[str]] = {}
    for vendor in vendors.itertuples():
        vtype = types[vendor.vendor_type]
        codes = list(vtype.core)
        codes += [code for code in vtype.optional if rng.random() < config.OPTIONAL_OFFER_PROB]
        offered[vendor.id] = codes

    # Setiap material minimal punya MIN_VENDORS_PER_MATERIAL penawar
    for m in materials:
        while sum(m.code in codes for codes in offered.values()) < config.MIN_VENDORS_PER_MATERIAL:
            pool = [
                v.id for v in vendors.itertuples()
                if v.category == m.category and m.code not in offered[v.id]
            ]
            offered[_pick(rng, pool)].append(m.code)

    return {vid: sorted(codes, key=order.__getitem__) for vid, codes in offered.items()}


def _cold_start(
    rng: np.random.Generator,
    vendors: pd.DataFrame,
    offered: dict[int, list[str]],
    materials: list[Material],
    calendar: Calendar,
) -> np.ndarray:
    counts = {m.code: sum(m.code in codes for codes in offered.values()) for m in materials}
    onboard = np.zeros(len(vendors), dtype=int)
    window = [calendar.index(d) for d in config.COLD_START_WINDOW]

    for category in config.CATEGORY_ORDER:
        for _ in range(config.COLD_START_PER_CATEGORY):
            # Vendor yang materialnya tetap punya cukup penawar walau vendor ini belum aktif
            pool = [
                v.id for v in vendors.itertuples()
                if v.category == category and onboard[v.id - 1] == 0
                and all(counts[code] > config.MIN_VENDORS_PER_MATERIAL for code in offered[v.id])
            ]
            if not pool:
                raise ValueError(f"Tidak ada kandidat vendor cold start untuk kategori {category}")
            vid = _pick(rng, pool)
            onboard[vid - 1] = int(rng.integers(window[0], window[1] + 1))
            for code in offered[vid]:
                counts[code] -= 1
    return onboard


def _normal_cdf(x: np.ndarray) -> np.ndarray:
    return np.array([0.5 * (1 + math.erf(v / math.sqrt(2))) for v in x])


def _traits(rng: np.random.Generator, vendors: pd.DataFrame, materials: list[Material]) -> pd.DataFrame:
    n = len(vendors)
    # Gaussian copula: z ~ N(0, R) lewat dekomposisi Cholesky
    chol = np.linalg.cholesky(config.TRAIT_CORRELATION)
    z = pd.DataFrame(rng.standard_normal((n, len(config.TRAIT_NAMES))) @ chol.T, columns=config.TRAIT_NAMES)

    # Arketipe wajib, diambil bergiliran dari kategori berbeda dan bukan vendor cold start
    archetype = pd.Series("", index=vendors.index, dtype=object)
    slot = 0
    for name, count, override in config.ARCHETYPES:
        for _ in range(count):
            category = config.CATEGORY_ORDER[slot % len(config.CATEGORY_ORDER)]
            slot += 1
            pool = [
                i for i, v in vendors.iterrows()
                if v.category == category and v.onboard_idx == 0 and archetype[i] == ""
            ]
            i = _pick(rng, pool)
            archetype[i] = name
            for column, value in override.items():
                z.loc[i, column] = value

    sigma_price = config.price_sigma(materials)
    return pd.DataFrame({
        "archetype": archetype,
        **{column: z[column] for column in config.TRAIT_NAMES},
        "price_level": np.clip(np.exp(sigma_price * z["z_p"]), *config.PRICE_LEVEL_CLIP),
        "true_quality": config.QUALITY_OFFSET + config.QUALITY_SCALE * _normal_cdf(z["z_q"].to_numpy()),
        "true_reliability": config.RELIABILITY_OFFSET
        + config.RELIABILITY_SCALE * _normal_cdf(z["z_r"].to_numpy()),
        "lead_time_factor": np.exp(config.LEAD_TIME_SIGMA * z["z_l"]),
        "capacity_factor": np.exp(config.CAPACITY_SIGMA * z["z_c"]),
    }, index=vendors.index)


def _offer_terms(
    rng: np.random.Generator,
    vendors: pd.DataFrame,
    offered: dict[int, list[str]],
    materials: list[Material],
) -> pd.DataFrame:
    by_code = {m.code: m for m in materials}
    multipliers, multiplier_weights = zip(*config.MOQ_MULTIPLIERS)
    rows = []
    for vendor in vendors.itertuples():
        for code in offered[vendor.id]:
            m = by_code[code]
            lead_time_true = m.lead_time_days * vendor.lead_time_factor
            rows.append({
                "vendor_id": vendor.id,
                "material_id": m.id,
                "base_price": m.ref_price * vendor.price_level
                * rng.lognormal(0.0, config.OFFER_PRICE_NOISE_SIGMA),
                "moq": max(1, round(m.moq * _pick(rng, multipliers, multiplier_weights))),
                "lead_time_true": lead_time_true,
                # Vendor kurang andal menjanjikan lead time lebih pendek dari kemampuan aslinya
                "quoted_base": lead_time_true
                * (config.QUOTE_BASE + config.QUOTE_RELIABILITY_SLOPE * vendor.true_reliability),
                "weekly_capacity": max(1, round(m.weekly_capacity * vendor.capacity_factor)),
            })
    return pd.DataFrame(rows)
