from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, in_values
from app.models.enums import CATEGORIES, UNITS


class Material(TimestampMixin, Base):
    __tablename__ = "materials"
    __table_args__ = (
        CheckConstraint(in_values("category", CATEGORIES), name="category"),
        CheckConstraint(in_values("unit", UNITS), name="unit"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Kode material dari spesifikasi generator, contoh B01, J03, P05
    code: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(20), index=True)
    unit: Mapped[str] = mapped_column(String(20))
