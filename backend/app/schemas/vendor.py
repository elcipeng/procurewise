from typing import Literal

from app.models.enums import CATEGORIES, PAYMENT_TERMS
from app.schemas.common import InputSchema, JakartaDateTime, ReadSchema, UpdateSchema, text

Category = Literal[CATEGORIES]
PaymentTerms = Literal[PAYMENT_TERMS]


class VendorCreate(InputSchema):
    name: text(150)
    category: Category
    city: text(100)
    contact: text(255) | None = None
    payment_terms: PaymentTerms
    is_active: bool = True


class VendorUpdate(UpdateSchema):
    NULLABLE_FIELDS = frozenset({"contact"})

    name: text(150) | None = None
    category: Category | None = None
    city: text(100) | None = None
    contact: text(255) | None = None
    payment_terms: PaymentTerms | None = None
    is_active: bool | None = None


class VendorRead(ReadSchema):
    id: int
    name: str
    category: str
    city: str
    contact: str | None
    payment_terms: str
    is_active: bool
    created_at: JakartaDateTime
    updated_at: JakartaDateTime
