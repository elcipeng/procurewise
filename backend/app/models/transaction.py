from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, in_values
from app.models.enums import TRANSACTION_STATUSES


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("qty > 0", name="qty_positive"),
        CheckConstraint("unit_price > 0", name="unit_price_positive"),
        CheckConstraint("promised_date >= order_date", name="promised_after_order"),
        CheckConstraint(
            "delivered_date IS NULL OR delivered_date >= order_date", name="delivered_after_order"
        ),
        CheckConstraint(
            "qty_defect IS NULL OR (qty_defect >= 0 AND qty_defect <= qty)", name="qty_defect_range"
        ),
        CheckConstraint(
            "quality_rating IS NULL OR quality_rating BETWEEN 1 AND 5", name="quality_rating_range"
        ),
        CheckConstraint(in_values("status", TRANSACTION_STATUSES), name="status"),
        # Hanya transaksi selesai yang punya tanggal terima
        CheckConstraint(
            "(status = 'completed') = (delivered_date IS NOT NULL)", name="delivered_iff_completed"
        ),
        # Fitur histori selalu dihitung per vendor dan dibatasi tanggal (anti leakage)
        Index("ix_transactions_vendor_order_date", "vendor_id", "order_date"),
        Index("ix_transactions_vendor_delivered_date", "vendor_id", "delivered_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id", ondelete="RESTRICT"))
    material_id: Mapped[int] = mapped_column(
        ForeignKey("materials.id", ondelete="RESTRICT"), index=True
    )
    # Request asal transaksi, kosong kalau transaksi dicatat tanpa request
    request_id: Mapped[int | None] = mapped_column(
        ForeignKey("procurement_requests.id", ondelete="SET NULL"), index=True
    )
    qty: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    order_date: Mapped[date]
    promised_date: Mapped[date]
    delivered_date: Mapped[date | None]
    qty_defect: Mapped[int | None]
    quality_rating: Mapped[int | None]
    status: Mapped[str] = mapped_column(String(20), server_default="in_progress")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
