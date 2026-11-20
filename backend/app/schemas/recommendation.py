from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.common import INT32_MAX, InputSchema, JakartaDateTime
from app.schemas.procurement_request import ProcurementRequestRead


class RecommendationRun(InputSchema):
    request_id: Annotated[int, Field(ge=1, le=INT32_MAX)]


class OfferSnapshot(BaseModel):
    """penawaran vendor saat ranking dibuat, disimpan karena penawaran bisa berubah setelahnya."""

    unit_price: float
    moq: int
    quoted_lead_time_days: int
    weekly_capacity: int
    is_available: bool


class VendorHistory(BaseModel):
    """metrik histori sebelum request_date. kalau has_history false, nilainya rata-rata kategori."""

    on_time_rate: float
    avg_delay_days: float
    defect_rate: float
    avg_rating: float
    n_transactions: int
    has_history: bool


class FeatureFactor(BaseModel):
    feature: str
    label: str
    value: float
    # kontribusi TreeSHAP terhadap skor model, positif menaikkan peringkat
    contribution: float


class FilterReason(BaseModel):
    code: str
    message: str


class RankedVendor(BaseModel):
    vendor_id: int
    vendor_name: str
    vendor_city: str
    rank: int
    score: float
    offer: OfferSnapshot
    total_cost: float
    slack_days: float
    history: VendorHistory
    top_factors: list[FeatureFactor]


class RejectedVendor(BaseModel):
    vendor_id: int
    vendor_name: str
    vendor_city: str
    offer: OfferSnapshot
    total_cost: float
    reasons: list[FilterReason]


class RecommendationResult(BaseModel):
    request: ProcurementRequestRead
    model_version: str
    # true kalau model LightGBM gagal dimuat dan ranking memakai baseline weighted sum
    is_fallback: bool
    ranked_at: JakartaDateTime
    ranked: list[RankedVendor]
    rejected: list[RejectedVendor]
