"""konfigurasi fitur, baseline, dan evaluasi.

modul ini tidak bergantung pada generator. semua yang ada di sini juga berlaku saat inference di backend.
"""

from datetime import date

# kalender bisnis publik untuk flag musim ramai. bukan parameter tersembunyi generator,
# firaza tahu kalender ini di dunia nyata. tanggal hijriah perlu dicek ke kalender kemenag
PEAK_SEASONS = (
    (date(2025, 4, 7), date(2025, 5, 27), "musim nikah syawal 2025"),
    (date(2025, 5, 28), date(2025, 6, 25), "musim nikah dzulhijjah 2025"),
    (date(2025, 11, 1), date(2025, 12, 20), "akhir tahun 2025"),
    (date(2026, 1, 5), date(2026, 3, 15), "menjelang ramadan dan ramadan 2026"),
    (date(2026, 3, 28), date(2026, 5, 15), "musim nikah syawal 2026"),
    (date(2026, 5, 18), date(2026, 6, 15), "musim nikah dzulhijjah 2026"),
    # periode berikutnya untuk inference di aplikasi
    (date(2026, 11, 1), date(2026, 12, 20), "akhir tahun 2026"),
    (date(2026, 12, 28), date(2027, 3, 5), "menjelang ramadan dan ramadan 2027"),
)

PRIORITY_CODES = {"low": 0, "normal": 1, "high": 2}

# nilai awal kalau kategori vendor belum punya histori sama sekali
GLOBAL_HISTORY_DEFAULTS = {
    "on_time_rate": 0.80,
    "avg_delay_days": 1.0,
    "defect_rate": 0.03,
    "avg_rating": 3.0,
}
# vendor yang belum pernah menerima order diberi nilai ini
DAYS_SINCE_LAST_ORDER_CAP = 365

OFFER_FEATURES = (
    "unit_price",
    "price_rel_median",
    "total_cost",
    "quoted_lead_time_days",
    "moq_ratio",
)
HISTORY_FEATURES = (
    "on_time_rate",
    "avg_delay_days",
    "defect_rate",
    "avg_rating",
    "n_transactions",
    "days_since_last_order",
    "has_history",
)
CONTEXT_FEATURES = (
    "slack_days",
    "qty_capacity_ratio",
    "priority_code",
    "is_peak_season",
)
FEATURE_COLUMNS = OFFER_FEATURES + HISTORY_FEATURES + CONTEXT_FEATURES

# kolom yang berasal dari karakter tersembunyi atau simulasi, tidak boleh jadi fitur
LABEL_COLUMNS = ("grade", "p_tepat", "e_cacat", "e_biaya", "skor_hasil")
FORBIDDEN_FEATURE_COLUMNS = LABEL_COLUMNS + (
    "price_level", "true_quality", "true_reliability", "lead_time_factor", "capacity_factor",
    "archetype", "vendor_type", "season_intensity", "urgency", "chosen",
)

# ---------------------------------------------------------------------------
# baseline. kriteria (fitur, arah). "benefit" makin besar makin baik, "cost" makin kecil makin baik
# ---------------------------------------------------------------------------
BASELINE_CRITERIA = (
    ("total_cost", "cost"),
    ("quoted_lead_time_days", "cost"),
    ("on_time_rate", "benefit"),
    ("defect_rate", "cost"),
    ("avg_rating", "benefit"),
)

# bobot tetap untuk weighted sum dan topsis
BASELINE_FIXED_WEIGHTS = {
    "total_cost": 0.30,
    "quoted_lead_time_days": 0.15,
    "on_time_rate": 0.25,
    "defect_rate": 0.20,
    "avg_rating": 0.10,
}

# bobot topsis menurut priority request
BASELINE_PRIORITY_WEIGHTS = {
    "high": {
        "total_cost": 0.15,
        "quoted_lead_time_days": 0.25,
        "on_time_rate": 0.35,
        "defect_rate": 0.15,
        "avg_rating": 0.10,
    },
    "normal": BASELINE_FIXED_WEIGHTS,
    "low": {
        "total_cost": 0.45,
        "quoted_lead_time_days": 0.10,
        "on_time_rate": 0.15,
        "defect_rate": 0.20,
        "avg_rating": 0.10,
    },
}

# ---------------------------------------------------------------------------
# evaluasi
# ---------------------------------------------------------------------------
RANKING_K = 3
# request dengan kandidat lolos kurang dari ini tidak masuk metrik ranking
MIN_ELIGIBLE_CANDIDATES = 2
SPLITS = ("train", "val", "test")
RANDOM_BASELINE_SEED = 0

# ---------------------------------------------------------------------------
# segmen evaluasi
# ---------------------------------------------------------------------------
# request dianggap ketat kalau median slack_days kandidat lolos <= nilai ini.
# 0 berarti janji lead time vendor yang tipikal sudah menghabiskan semua waktu sampai needed_by
TIGHT_SLACK_DAYS = 0
BOOTSTRAP_SAMPLES = 2000
BOOTSTRAP_SEED = 0

# ---------------------------------------------------------------------------
# lightgbm lambdarank (tahap m1)
# ---------------------------------------------------------------------------
MODEL_VERSION = "lgbm-v1"
LGBM_BASE_PARAMS = {
    "objective": "lambdarank",
    "metric": "ndcg",
    "n_estimators": 2000,
    "subsample": 1.0,
    "colsample_bytree": 1.0,
    "reg_lambda": 1.0,
    "random_state": 0,
    "deterministic": True,
    "force_row_wise": True,
    "n_jobs": 1,
    "verbose": -1,
}
EARLY_STOPPING_ROUNDS = 100
# tuning kecil, dipilih dari ndcg@3 di grup informatif split val
LGBM_TUNING_GRID = {
    "learning_rate": (0.03, 0.1),
    "num_leaves": (7, 15, 31),
    "min_child_samples": (10, 40),
}
STABILITY_SEEDS = (1, 2, 3, 42, 43)
