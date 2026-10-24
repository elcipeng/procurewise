from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.common import INT32_MAX, InputSchema, JakartaDateTime, Money, UpdateSchema

UnitPrice = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=2)]
PositiveInt = Annotated[int, Field(ge=1, le=INT32_MAX)]


class VendorOfferCreate(InputSchema):
    vendor_id: PositiveInt
    material_id: PositiveInt
    unit_price: UnitPrice
    moq: PositiveInt
    quoted_lead_time_days: PositiveInt
    weekly_capacity: PositiveInt
    is_available: bool = True


class VendorOfferUpdate(UpdateSchema):
    """pasangan vendor dan material tidak bisa diubah, buat penawaran baru kalau perlu."""

    unit_price: UnitPrice | None = None
    moq: PositiveInt | None = None
    quoted_lead_time_days: PositiveInt | None = None
    weekly_capacity: PositiveInt | None = None
    is_available: bool | None = None


class VendorOfferRead(BaseModel):
    id: int
    vendor_id: int
    vendor_name: str
    vendor_is_active: bool
    material_id: int
    material_code: str
    material_name: str
    material_unit: str
    unit_price: Money
    moq: int
    quoted_lead_time_days: int
    weekly_capacity: int
    is_available: bool
    updated_at: JakartaDateTime
