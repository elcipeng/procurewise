from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, false, func, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Recommendation(Base):
    """Satu baris per kandidat vendor dalam satu request, termasuk yang gugur filter keras."""

    __tablename__ = "recommendations"
    __table_args__ = (
        # Satu request bisa di-ranking ulang dengan versi model lain tanpa menimpa hasil lama
        UniqueConstraint(
            "request_id", "vendor_id", "model_version", name="uq_recommendations_request_vendor_model"
        ),
        CheckConstraint("rank IS NULL OR rank >= 1", name="rank_positive"),
        # Kandidat lolos punya rank dan skor, kandidat gugur punya alasan dan tanpa rank
        CheckConstraint(
            "(is_eligible AND rank IS NOT NULL AND score IS NOT NULL)"
            " OR (NOT is_eligible AND rank IS NULL AND filter_reasons IS NOT NULL)",
            name="eligible_consistency",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Tanpa index terpisah, sudah tercakup unique constraint yang diawali request_id
    request_id: Mapped[int] = mapped_column(
        ForeignKey("procurement_requests.id", ondelete="CASCADE")
    )
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id", ondelete="RESTRICT"))
    is_eligible: Mapped[bool] = mapped_column(server_default=true())
    # Kode alasan gugur filter keras, contoh ["moq_lebih_besar", "melebihi_budget"]
    filter_reasons: Mapped[list[str] | None] = mapped_column(JSONB)
    rank: Mapped[int | None]
    score: Mapped[float | None]
    model_version: Mapped[str] = mapped_column(String(50))
    # Snapshot fitur dan kontribusi SHAP saat ranking dibuat
    features_json: Mapped[dict[str, Any]] = mapped_column(JSONB)
    # Cache penjelasan dari Gemini atau template fallback
    explanation: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    chosen: Mapped[bool] = mapped_column(server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
