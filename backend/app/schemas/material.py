from typing import Annotated, Literal

from pydantic import BeforeValidator, StringConstraints

from app.models.enums import CATEGORIES, UNITS
from app.schemas.common import InputSchema, JakartaDateTime, ReadSchema, UpdateSchema, text

# pola dicek setelah dirapikan, supaya input " b09 " tetap diterima sebagai B09
MaterialCode = Annotated[
    str,
    BeforeValidator(lambda v: v.strip().upper() if isinstance(v, str) else v),
    StringConstraints(pattern=r"^[A-Z0-9]{2,10}$"),
]
Category = Literal[CATEGORIES]
Unit = Literal[UNITS]


class MaterialCreate(InputSchema):
    code: MaterialCode
    name: text(150)
    category: Category
    unit: Unit


class MaterialUpdate(UpdateSchema):
    code: MaterialCode | None = None
    name: text(150) | None = None
    category: Category | None = None
    unit: Unit | None = None


class MaterialRead(ReadSchema):
    id: int
    code: str
    name: str
    category: str
    unit: str
    created_at: JakartaDateTime
    updated_at: JakartaDateTime
