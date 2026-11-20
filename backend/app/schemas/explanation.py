from typing import Literal

from pydantic import BaseModel

from app.schemas.common import JakartaDateTime

ExplanationSource = Literal["gemini", "template"]
# alasan memakai template, ditampilkan di UI supaya user tahu penjelasan tidak berasal dari Gemini
FallbackReason = Literal["api_key_kosong", "api_gagal", "batas_pemakaian", "angka_tidak_cocok"]


class VendorExplanation(BaseModel):
    vendor_id: int
    nama_vendor: str
    kelebihan: list[str]
    kekurangan: list[str]


class ExplanationContent(BaseModel):
    """bentuk output yang diminta dari Gemini (response_schema) dan juga dibuat oleh template."""

    ringkasan: str
    per_vendor: list[VendorExplanation]
    trade_off: str
    catatan_risiko: list[str]


class ExplanationRead(ExplanationContent):
    source: ExplanationSource
    model: str | None
    fallback_reason: FallbackReason | None
    generated_at: JakartaDateTime
