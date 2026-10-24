"""Semua parameter generator data sintetis.

Spesifikasi lengkap ada di ml/README.md. Nomor bagian di komentar mengacu ke dokumen itu.
Harga, MOQ, dan lead time per material dibaca dari price_reference.yaml.
Penanda [ASUMSI] dan [KALIBRASI] sama artinya dengan di spesifikasi.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import yaml

PACKAGE_DIR = Path(__file__).resolve().parent
PRICE_REFERENCE_PATH = PACKAGE_DIR / "price_reference.yaml"
DEFAULT_OUT_DIR = PACKAGE_DIR.parent / "data" / "raw"

# Bagian 14. Batch 15, grup I037
DEFAULT_SEED = 15037
# Urutan aliran acak tetap, mengubah satu komponen tidak menggeser komponen lain
RNG_STREAMS = ("vendors", "offers", "requests", "availability", "choice", "transactions", "labels")

# ---------------------------------------------------------------------------
# Bagian 3. Periode data dan split
# ---------------------------------------------------------------------------
PERIOD_START = date(2025, 4, 1)
PERIOD_END = date(2026, 9, 30)
# Pengiriman bisa melewati akhir periode, kalender simulasi dibuat lebih panjang
CALENDAR_END = date(2027, 3, 31)
SPLITS = (
    ("train", date(2025, 4, 1), date(2026, 3, 31)),
    ("val", date(2026, 4, 1), date(2026, 6, 30)),
    ("test", date(2026, 7, 1), date(2026, 9, 30)),
)
TZ_SUFFIX = "+07:00"

# ---------------------------------------------------------------------------
# Bagian 4. Material
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Material:
    id: int
    code: str
    name: str
    category: str
    unit: str
    weekly_capacity: int  # kapasitas mingguan dasar [ASUMSI]
    qty_median: int  # [ASUMSI]
    monthly_rate: float  # laju order dasar per bulan [ASUMSI]
    defect_base: float  # [ASUMSI]
    ref_price: float  # dari price_reference.yaml
    price_p25: float | None
    price_p75: float | None
    moq: int
    lead_time_days: int

    @property
    def qty_step(self) -> int:
        return 1 if self.unit == "kg" else 10


# kode, nama, kategori, satuan, kapasitas mingguan, qty median, laju per bulan, cacat dasar
MATERIAL_CATALOG = (
    ("B01", "Handuk mandi katun 70x140 cm", "bahan", "pcs", 300, 100, 9, 0.020),
    ("B02", "Handuk muka katun 30x30 cm", "bahan", "pcs", 500, 200, 7, 0.020),
    ("B03", "Sajadah tebal polos", "bahan", "pcs", 250, 80, 8, 0.020),
    ("B04", "Sajadah travel lipat", "bahan", "pcs", 200, 60, 5, 0.020),
    ("B05", "Tasbih kayu 33 butir", "bahan", "pcs", 800, 200, 4, 0.020),
    ("J01", "Jasa bordir nama (maks. 12 karakter)", "jasa", "pcs", 250, 100, 8, 0.030),
    ("J02", "Jasa bordir logo atau motif", "jasa", "pcs", 200, 80, 4, 0.030),
    ("J03", "Jasa sablon DTF", "jasa", "pcs", 400, 100, 4, 0.030),
    ("J04", "Cetak kartu ucapan", "jasa", "lembar", 2000, 300, 5, 0.015),
    ("J05", "Cetak stiker label custom", "jasa", "lembar", 3000, 500, 3, 0.015),
    ("P01", "Rigid box hampers", "packaging", "pcs", 250, 100, 6, 0.015),
    ("P02", "Kotak duplex lipat", "packaging", "pcs", 800, 200, 5, 0.015),
    ("P03", "Paper bag", "packaging", "pcs", 800, 200, 4, 0.015),
    ("P04", "Tas spunbond (goodie bag)", "packaging", "pcs", 500, 150, 4, 0.015),
    ("P05", "Kertas serut (filler)", "packaging", "kg", 60, 10, 4, 0.010),
)

# ---------------------------------------------------------------------------
# Bagian 5. Vendor dan karakter tersembunyi
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VendorType:
    key: str
    category: str
    count: int
    core: tuple[str, ...]  # material yang pasti ditawarkan
    optional: tuple[str, ...]  # material yang ditawarkan dengan peluang OPTIONAL_OFFER_PROB
    name_suffixes: tuple[str, ...]
    cities: tuple[tuple[str, float], ...]  # [ASUMSI]


VENDOR_TYPES = (
    VendorType("handuk", "bahan", 4, ("B01", "B02"), (), ("Tekstil", "Textile", "Handuk"),
               (("Bandung", 0.3), ("Majalaya", 0.3), ("Pekalongan", 0.2), ("Solo", 0.2))),
    VendorType("sajadah", "bahan", 2, ("B03", "B04"), (), ("Sajadah", "Karpet"),
               (("Bandung", 0.4), ("Tasikmalaya", 0.3), ("Pekalongan", 0.3))),
    VendorType("perlengkapan_muslim", "bahan", 4, ("B03", "B04", "B05"), ("B02",),
               ("Grosir Muslim", "Busana Muslim", "Perlengkapan Ibadah"),
               (("Jakarta", 0.4), ("Tasikmalaya", 0.3), ("Surabaya", 0.3))),
    VendorType("bordir", "jasa", 4, ("J01", "J02"), ("J03",), ("Bordir", "Konveksi", "Embroidery"),
               (("Tasikmalaya", 0.5), ("Bandung", 0.3), ("Jakarta", 0.2))),
    VendorType("percetakan", "jasa", 5, ("J04", "J05"), ("J03",), ("Printing", "Grafika", "Digital Print"),
               (("Jakarta", 0.3), ("Tangerang", 0.2), ("Bekasi", 0.2), ("Yogyakarta", 0.15),
                ("Surabaya", 0.15))),
    VendorType("produsen_box", "packaging", 4, ("P01", "P02"), (), ("Box", "Kemasan", "Packindo"),
               (("Tangerang", 0.3), ("Bekasi", 0.3), ("Surabaya", 0.2), ("Jakarta", 0.2))),
    VendorType("grosir_packaging", "packaging", 5, ("P02", "P03", "P04", "P05"), (),
               ("Packaging", "Kemasan", "Grosir Kemasan"),
               (("Jakarta", 0.4), ("Tangerang", 0.2), ("Surabaya", 0.2), ("Yogyakarta", 0.2))),
)
CATEGORY_ORDER = ("bahan", "jasa", "packaging")
OPTIONAL_OFFER_PROB = 0.5  # [ASUMSI]
MIN_VENDORS_PER_MATERIAL = 4

NAME_PREFIXES = ("CV", "UD", "PT", "Toko")
NAME_WORDS = (
    "Sinar", "Mitra", "Berkah", "Cahaya", "Karya", "Sumber", "Harapan", "Maju", "Jaya", "Abadi",
    "Mulia", "Barokah", "Lestari", "Sentosa", "Makmur", "Prima", "Insan", "Bintang", "Duta", "Mega",
)
PAYMENT_TERMS = (("cash", 0.40), ("dp_50", 0.40), ("tempo_14", 0.15), ("tempo_30", 0.05))  # [ASUMSI]

# Vendor cold start, 1 per kategori, bergabung di periode validasi atau test
COLD_START_PER_CATEGORY = 1
COLD_START_WINDOW = (date(2026, 4, 1), date(2026, 8, 31))

# Bagian 5.2. Urutan: harga, kualitas, keandalan, lead time, kapasitas [ASUMSI]
TRAIT_NAMES = ("z_p", "z_q", "z_r", "z_l", "z_c")
TRAIT_CORRELATION = np.array([
    [1.00, 0.45, 0.15, 0.10, -0.30],
    [0.45, 1.00, 0.30, 0.15, 0.00],
    [0.15, 0.30, 1.00, -0.30, 0.15],
    [0.10, 0.15, -0.30, 1.00, -0.35],
    [-0.30, 0.00, 0.15, -0.35, 1.00],
])
SIGMA_PRICE_DEFAULT = 0.15  # dipakai selama price_p25/p75 belum dikalibrasi
PRICE_LEVEL_CLIP = (0.70, 1.40)
QUALITY_OFFSET, QUALITY_SCALE = 0.35, 0.60
RELIABILITY_OFFSET, RELIABILITY_SCALE = 0.30, 0.65
LEAD_TIME_SIGMA = 0.25
CAPACITY_SIGMA = 0.50

# Bagian 5.3. nama, jumlah, override nilai z
ARCHETYPES = (
    ("murah_tapi_bagus", 2, {"z_p": -1.2, "z_q": 1.2, "z_r": 0.8}),
    ("mahal_tapi_sering_telat", 2, {"z_p": 1.3, "z_q": 0.5, "z_r": -1.3}),
    ("murah_dan_buruk", 1, {"z_p": -1.3, "z_q": -1.3}),
    ("kecil_tapi_andal", 1, {"z_c": -1.2, "z_r": 1.2}),
)

# ---------------------------------------------------------------------------
# Bagian 6. Penawaran vendor
# ---------------------------------------------------------------------------
OFFER_PRICE_NOISE_SIGMA = 0.05
MOQ_MULTIPLIERS = ((0.5, 0.3), (1.0, 0.5), (2.0, 0.2))  # [ASUMSI]
# Janji lead time = lead_time_asli * (QUOTE_BASE + QUOTE_RELIABILITY_SLOPE * keandalan) [KALIBRASI]
QUOTE_BASE = 0.95
QUOTE_RELIABILITY_SLOPE = 0.65
MONTHLY_INFLATION = 0.003  # [ASUMSI]
PEAK_PRICE_SURCHARGE = 0.05
PEAK_QUOTE_EXTRA = 0.15
AVAILABILITY_BASE = 0.95
AVAILABILITY_PEAK_DROP = 0.10
OFFER_UPDATED_WINDOW_DAYS = 60
DAYS_PER_MONTH = 30.4375

# ---------------------------------------------------------------------------
# Bagian 7. Musim ramai dan libur. Tanggal Hijriah [VERIFIKASI], intensitas [ASUMSI]
# ---------------------------------------------------------------------------
# mulai, selesai, s di awal, s di akhir (beda kalau naik linear), keterangan
SEASONS = (
    (date(2025, 4, 7), date(2025, 5, 27), 0.5, 0.5, "Musim nikah Syawal 2025"),
    (date(2025, 5, 28), date(2025, 6, 25), 0.4, 0.4, "Musim nikah Dzulhijjah 2025"),
    (date(2025, 11, 1), date(2025, 12, 20), 0.6, 0.6, "Akhir tahun 2025"),
    (date(2026, 1, 5), date(2026, 2, 17), 0.3, 1.0, "Menjelang Ramadan 2026"),
    (date(2026, 2, 18), date(2026, 3, 15), 1.0, 1.0, "Ramadan 2026"),
    (date(2026, 3, 28), date(2026, 5, 15), 0.5, 0.5, "Musim nikah Syawal 2026"),
    (date(2026, 5, 18), date(2026, 6, 15), 0.4, 0.4, "Musim nikah Dzulhijjah 2026"),
)
CLOSURES = (
    (date(2025, 4, 1), date(2025, 4, 6), "Libur Lebaran 2025"),
    (date(2026, 3, 16), date(2026, 3, 27), "Libur Lebaran 2026"),
)
DEMAND_PEAK_FACTOR = 1.5
QTY_PEAK_FACTOR = 0.5
LEAD_TIME_PEAK_FACTOR = 0.35
CAPACITY_PEAK_FACTOR = 0.4
DISRUPTION_PEAK = 0.08
DEFECT_PEAK_FACTOR = 0.4

# ---------------------------------------------------------------------------
# Bagian 8. Procurement request historis
# ---------------------------------------------------------------------------
# Laju harian = laju bulanan / pembagi ini. Minggu dan libur Lebaran tidak ada request [KALIBRASI]
DAILY_RATE_DIVISOR = 26
QTY_SIGMA = 0.6
# urgensi, peluang, rentang u untuk needed_by [ASUMSI]
URGENCY_LEVELS = (("ketat", 0.25, (1.1, 1.5)), ("normal", 0.50, (1.5, 2.2)), ("santai", 0.25, (2.2, 3.5)))
PRIORITY_VALUES = ("high", "normal", "low")
PRIORITY_BY_URGENCY = {
    "ketat": (0.70, 0.25, 0.05),
    "normal": (0.20, 0.60, 0.20),
    "santai": (0.05, 0.35, 0.60),
}
BUDGET_PROB = 0.70
# Pengali terhadap harga pasar saat request (harga referensi + inflasi + kenaikan musim ramai)
BUDGET_RANGE = (1.05, 1.45)
NOTES_PROB = 0.5
NOTE_TEMPLATES = (
    "Untuk pesanan hampers corporate",
    "Untuk paket hampers pernikahan",
    "Stok persiapan musim ramai",
    "Restock rutin",
    "Pesanan custom pelanggan",
)
WORK_HOURS = (8, 17)

USERS = (
    (1, "Owner Demo", "owner@example.com", "owner"),
    (2, "Admin Demo", "admin@example.com", "admin"),
)

# ---------------------------------------------------------------------------
# Bagian 10. Pemilihan vendor historis [ASUMSI]
# ---------------------------------------------------------------------------
CHOICE_PRICE_WEIGHT = 1.5
CHOICE_FAMILIARITY_WEIGHT = 0.4
CHOICE_EXPLORATION = 0.15

# ---------------------------------------------------------------------------
# Bagian 11. Simulasi hasil pesanan
# ---------------------------------------------------------------------------
NOISE_SIGMA_BASE = 0.08
NOISE_SIGMA_UNRELIABLE = 0.25
DISRUPTION_BASE = 0.02
DISRUPTION_UNRELIABLE = 0.20
DISRUPTION_GAMMA_SHAPE, DISRUPTION_GAMMA_SCALE = 2.0, 3.0
DEFECT_QUALITY_SLOPE = 3.5
DEFECT_QUALITY_PIVOT = 0.60
DEFECT_RUSH_FACTOR = 0.5
DEFECT_MAX = 0.30
DEFECT_BETA_CONCENTRATION = 60.0
RATING_INTERCEPT = 1.8
RATING_QUALITY = 3.0
RATING_DEFECT = 10.0
RATING_DELAY = 0.12
RATING_NOISE = 0.45
CANCEL_BASE = 0.01
CANCEL_UNRELIABLE = 0.04
TX_PRICE_NOISE_SIGMA = 0.03

# ---------------------------------------------------------------------------
# Bagian 13. Label relevansi
# ---------------------------------------------------------------------------
LABEL_SIMULATIONS = 30
GATE_MIN_ON_TIME = 0.5
GATE_MAX_DEFECT = 0.08
# Bobot (waktu, cacat, biaya) menurut priority [ASUMSI]
LABEL_WEIGHTS = {
    "high": (0.60, 0.25, 0.15),
    "normal": (0.40, 0.30, 0.30),
    "low": (0.25, 0.30, 0.45),
}
GRADE_THRESHOLDS = (0.90, 0.76)  # batas grade 3 dan grade 2 [KALIBRASI]


def load_materials(path: Path = PRICE_REFERENCE_PATH) -> list[Material]:
    reference = yaml.safe_load(path.read_text(encoding="utf-8"))
    catalog_codes = [row[0] for row in MATERIAL_CATALOG]
    if sorted(reference) != sorted(catalog_codes):
        raise ValueError(f"Kode material di {path.name} tidak sama dengan MATERIAL_CATALOG")

    materials = []
    for i, (code, name, category, unit, capacity, qty_median, rate, defect) in enumerate(MATERIAL_CATALOG, 1):
        ref = reference[code]
        materials.append(Material(
            id=i, code=code, name=name, category=category, unit=unit,
            weekly_capacity=capacity, qty_median=qty_median, monthly_rate=rate, defect_base=defect,
            ref_price=float(ref["ref_price"]),
            price_p25=None if ref["price_p25"] is None else float(ref["price_p25"]),
            price_p75=None if ref["price_p75"] is None else float(ref["price_p75"]),
            moq=int(ref["moq"]), lead_time_days=int(ref["lead_time_days"]),
        ))
    return materials


def price_sigma(materials: list[Material]) -> float:
    """Sigma log-harga antar vendor dari kuartil marketplace, atau default kalau belum dikalibrasi."""
    spreads = [
        np.log(m.price_p75 / m.price_p25) / 1.349
        for m in materials
        if m.price_p25 and m.price_p75
    ]
    if len(spreads) < len(materials):
        return SIGMA_PRICE_DEFAULT
    return float(np.median(spreads))


def config_hash() -> str:
    digest = hashlib.sha256()
    for path in (Path(__file__), PRICE_REFERENCE_PATH):
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]
