# Semua model diimpor di sini supaya terdaftar di Base.metadata (dipakai Alembic autogenerate)
from app.db.base import Base
from app.models.material import Material
from app.models.procurement_request import ProcurementRequest
from app.models.recommendation import Recommendation
from app.models.transaction import Transaction
from app.models.user import User
from app.models.vendor import Vendor
from app.models.vendor_offer import VendorOffer

__all__ = [
    "Base",
    "Material",
    "ProcurementRequest",
    "Recommendation",
    "Transaction",
    "User",
    "Vendor",
    "VendorOffer",
]
