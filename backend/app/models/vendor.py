from sqlalchemy import CheckConstraint, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, in_values
from app.models.enums import CATEGORIES, PAYMENT_TERMS


class Vendor(TimestampMixin, Base):
    __tablename__ = "vendors"
    __table_args__ = (
        CheckConstraint(in_values("category", CATEGORIES), name="category"),
        CheckConstraint(in_values("payment_terms", PAYMENT_TERMS), name="payment_terms"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(20), index=True)
    city: Mapped[str] = mapped_column(String(100))
    contact: Mapped[str | None] = mapped_column(String(255))
    payment_terms: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(server_default=true())
