from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, in_values
from app.models.enums import PRIORITIES, REQUEST_STATUSES


class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"
    __table_args__ = (
        CheckConstraint("qty > 0", name="qty_positive"),
        CheckConstraint("max_budget IS NULL OR max_budget > 0", name="max_budget_positive"),
        CheckConstraint("needed_by >= request_date", name="needed_by_after_request"),
        CheckConstraint(in_values("priority", PRIORITIES), name="priority"),
        CheckConstraint(in_values("status", REQUEST_STATUSES), name="status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(
        ForeignKey("materials.id", ondelete="RESTRICT"), index=True
    )
    qty: Mapped[int]
    # Tanggal kebutuhan diajukan, jadi acuan slack_days dan cutoff anti leakage fitur histori
    request_date: Mapped[date] = mapped_column(server_default=func.current_date(), index=True)
    needed_by: Mapped[date]
    priority: Mapped[str] = mapped_column(String(20))
    max_budget: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(20), server_default="new", index=True)
    # Audit saja, tidak dipakai untuk perhitungan fitur
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
