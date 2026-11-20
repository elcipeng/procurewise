from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.models.enums import PRIORITIES, REQUEST_STATUSES
from app.schemas.common import INT32_MAX, InputSchema, JakartaDateTime, Money

Priority = Literal[PRIORITIES]
RequestStatus = Literal[REQUEST_STATUSES]
NOTES_MAX_LENGTH = 1000


class ProcurementRequestCreate(InputSchema):
    """request_date selalu hari ini (Asia/Jakarta) dan diisi server, bukan oleh user.

    tanggal ini menjadi cutoff anti leakage fitur histori dan acuan slack_days.
    """

    material_id: Annotated[int, Field(ge=1, le=INT32_MAX)]
    qty: Annotated[int, Field(ge=1, le=INT32_MAX)]
    needed_by: date
    priority: Priority = "normal"
    max_budget: Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=2)] | None = None
    notes: Annotated[str, Field(max_length=NOTES_MAX_LENGTH)] | None = None


class ProcurementRequestRead(BaseModel):
    id: int
    material_id: int
    material_code: str
    material_name: str
    material_unit: str
    material_category: str
    qty: int
    request_date: date
    needed_by: date
    priority: Priority
    max_budget: Money | None
    notes: str | None
    status: RequestStatus
    created_at: JakartaDateTime
