# Nilai yang diizinkan untuk kolom kategori dan status.
# Disimpan sebagai VARCHAR + CHECK constraint, bukan ENUM native Postgres.

USER_ROLES = ("owner", "admin")
CATEGORIES = ("bahan", "jasa", "packaging")
UNITS = ("pcs", "lembar", "kg")
PAYMENT_TERMS = ("cash", "dp_50", "tempo_14", "tempo_30")
TRANSACTION_STATUSES = ("in_progress", "completed", "cancelled")
PRIORITIES = ("tinggi", "normal", "rendah")
REQUEST_STATUSES = ("baru", "direkomendasikan", "selesai", "dibatalkan")
