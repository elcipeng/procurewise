from datetime import datetime
from decimal import Decimal
from typing import Annotated, ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    PlainSerializer,
    StringConstraints,
    ValidationInfo,
    field_validator,
    model_validator,
)

from app.core.responses import JAKARTA_TZ

# batas int4 postgres, mencegah error overflow dari DB saat angka terlalu besar
INT32_MAX = 2_147_483_647

# decimal diserialisasi pydantic sebagai string, frontend lebih mudah memakai angka
Money = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]
# DB menyimpan timestamptz dalam utc, ditampilkan dalam zona yang sama dengan timestamp response
JakartaDateTime = Annotated[
    datetime, PlainSerializer(lambda v: v.astimezone(JAKARTA_TZ).isoformat(), return_type=str, when_used="json")
]


def text(max_length: int):
    return Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=max_length)]


class InputSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UpdateSchema(InputSchema):
    """update parsial: field yang tidak dikirim tidak diubah, field wajib tidak boleh dikirim null."""

    NULLABLE_FIELDS: ClassVar[frozenset[str]] = frozenset()

    @field_validator("*", mode="after")
    @classmethod
    def _reject_null(cls, value, info: ValidationInfo):
        if value is None and info.field_name not in cls.NULLABLE_FIELDS:
            raise ValueError("tidak boleh kosong")
        return value

    @model_validator(mode="after")
    def _require_any_field(self):
        if not self.model_fields_set:
            raise ValueError("minimal satu field harus diisi")
        return self

    def changes(self) -> dict:
        return self.model_dump(exclude_unset=True)


class ReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
