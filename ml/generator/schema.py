"""Cerminan skema 7 tabel DB (backend/app/models) untuk output CSV dan validasi.

Kalau model backend berubah, file ini wajib ikut diubah.
"""

TABLE_COLUMNS = {
    "users": ("id", "name", "email", "role", "created_at", "updated_at"),
    "vendors": (
        "id", "name", "category", "city", "contact", "payment_terms", "is_active",
        "created_at", "updated_at",
    ),
    "materials": ("id", "code", "name", "category", "unit", "created_at", "updated_at"),
    "vendor_offers": (
        "id", "vendor_id", "material_id", "unit_price", "moq", "quoted_lead_time_days",
        "weekly_capacity", "is_available", "updated_at",
    ),
    "transactions": (
        "id", "vendor_id", "material_id", "request_id", "qty", "unit_price", "order_date",
        "promised_date", "delivered_date", "qty_defect", "quality_rating", "status", "created_at",
    ),
    "procurement_requests": (
        "id", "material_id", "qty", "request_date", "needed_by", "priority", "max_budget",
        "notes", "created_by", "status", "created_at",
    ),
    "recommendations": (
        "id", "request_id", "vendor_id", "is_eligible", "filter_reasons", "rank", "score",
        "model_version", "features_json", "explanation", "chosen", "created_at",
    ),
}

# Urutan tulis dan seed, tabel induk lebih dulu
TABLE_ORDER = (
    "users", "materials", "vendors", "vendor_offers", "procurement_requests", "transactions",
    "recommendations",
)

# Sama dengan backend/app/models/enums.py
ENUMS = {
    ("users", "role"): ("owner", "admin"),
    ("vendors", "category"): ("bahan", "jasa", "packaging"),
    ("vendors", "payment_terms"): ("cash", "dp_50", "tempo_14", "tempo_30"),
    ("materials", "category"): ("bahan", "jasa", "packaging"),
    ("materials", "unit"): ("pcs", "lembar", "kg"),
    ("transactions", "status"): ("in_progress", "completed", "cancelled"),
    ("procurement_requests", "priority"): ("high", "normal", "low"),
    ("procurement_requests", "status"): ("new", "recommended", "completed", "cancelled"),
}

# Panjang maksimum kolom VARCHAR
MAX_LENGTHS = {
    ("users", "name"): 100,
    ("users", "email"): 255,
    ("vendors", "name"): 150,
    ("vendors", "city"): 100,
    ("vendors", "contact"): 255,
    ("materials", "code"): 10,
    ("materials", "name"): 150,
}

NOT_NULL = {
    "users": ("id", "name", "email", "role"),
    "vendors": ("id", "name", "category", "city", "payment_terms", "is_active"),
    "materials": ("id", "code", "name", "category", "unit"),
    "vendor_offers": (
        "id", "vendor_id", "material_id", "unit_price", "moq", "quoted_lead_time_days",
        "weekly_capacity", "is_available",
    ),
    "transactions": (
        "id", "vendor_id", "material_id", "qty", "unit_price", "order_date", "promised_date", "status",
    ),
    "procurement_requests": (
        "id", "material_id", "qty", "request_date", "needed_by", "priority", "created_by", "status",
    ),
    "recommendations": (
        "id", "request_id", "vendor_id", "is_eligible", "model_version", "features_json", "chosen",
    ),
}

# Kolom karakter tersembunyi dan turunannya, tidak boleh muncul di CSV tabel
HIDDEN_COLUMNS = (
    "price_level", "true_quality", "true_reliability", "lead_time_factor", "capacity_factor",
    "lead_time_true", "archetype", "vendor_type", "onboard_date", "z_p", "z_q", "z_r", "z_l", "z_c",
    "p_tepat", "e_cacat", "e_biaya", "skor_hasil", "grade",
)

# File tambahan di luar 7 tabel. Awalan "_" menandai file yang tidak di-seed ke DB
HIDDEN_TRAITS_FILE = "_hidden_vendor_traits.csv"
LABELS_FILE = "_labels.csv"
CANDIDATES_FILE = "_candidates.csv"
REQUEST_META_FILE = "_request_meta.csv"
MANIFEST_FILE = "_manifest.json"
