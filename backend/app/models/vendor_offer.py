from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, UniqueConstraint, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VendorOffer(Base):
    __tablename__ = "vendor_offers"
    __table_args__ = (
        UniqueConstraint("vendor_id", "material_id", name="uq_vendor_offers_vendor_material"),
        CheckConstraint("unit_price > 0", name="unit_price_positive"),
        CheckConstraint("moq > 0", name="moq_positive"),
        CheckConstraint("quoted_lead_time_days > 0", name="lead_time_positive"),
        CheckConstraint("weekly_capacity > 0", name="capacity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id", ondelete="CASCADE"))
    material_id: Mapped[int] = mapped_column(
        ForeignKey("materials.id", ondelete="RESTRICT"), index=True
    )
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    moq: Mapped[int]
    quoted_lead_time_days: Mapped[int]
    weekly_capacity: Mapped[int]
    is_available: Mapped[bool] = mapped_column(server_default=true())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
