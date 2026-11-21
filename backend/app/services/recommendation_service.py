"""ranking vendor untuk satu kebutuhan procurement dan penyimpanannya di tabel recommendations."""

import asyncio
from datetime import date

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ConflictError, FieldValidationError
from app.models import Material, ProcurementRequest, Recommendation, Transaction, Vendor, VendorOffer
from app.schemas.recommendation import (
    FeatureFactor,
    FilterReason,
    OfferSnapshot,
    RankedVendor,
    RecommendationResult,
    RejectedVendor,
    VendorHistory,
)
from app.services import procurement_request_service, ranking_engine

ENTITY_LABEL = "rekomendasi"
# request historis (completed, cancelled) sudah punya transaksi, ranking hanya untuk kebutuhan yang masih berjalan
RANKABLE_STATUSES = ("new", "recommended")
TRANSACTION_COLUMNS = (
    "vendor_id", "qty", "order_date", "promised_date", "delivered_date", "qty_defect", "quality_rating", "status",
)
OFFER_COLUMNS = ("unit_price", "moq", "quoted_lead_time_days", "weekly_capacity", "is_available")

FEATURE_LABELS = {
    "unit_price": "Harga satuan",
    "price_rel_median": "Harga relatif terhadap median penawaran",
    "total_cost": "Total biaya",
    "quoted_lead_time_days": "Janji lead time",
    "moq_ratio": "Rasio MOQ terhadap qty",
    "on_time_rate": "Tingkat tepat waktu",
    "avg_delay_days": "Rata-rata keterlambatan",
    "defect_rate": "Tingkat cacat",
    "avg_rating": "Rata-rata rating kualitas",
    "n_transactions": "Jumlah transaksi selesai",
    "days_since_last_order": "Hari sejak order terakhir",
    "has_history": "Punya histori transaksi",
    "slack_days": "Sisa waktu setelah lead time",
    "qty_capacity_ratio": "Rasio qty terhadap kapasitas mingguan",
    "priority_code": "Prioritas kebutuhan",
    "is_peak_season": "Musim ramai",
}


async def run_recommendation(session: AsyncSession, request_id: int) -> RecommendationResult:
    request = await session.get(ProcurementRequest, request_id)
    if request is None:
        raise FieldValidationError(
            ENTITY_LABEL, "request_id", f"kebutuhan procurement dengan id {request_id} tidak ditemukan"
        )
    if request.status not in RANKABLE_STATUSES:
        raise ConflictError(
            f"Kebutuhan procurement {request_id} berstatus {request.status}, "
            "rekomendasi hanya dibuat untuk kebutuhan berstatus new atau recommended"
        )

    offers = await _load_offers(session, request.material_id)
    if offers.empty:
        raise ConflictError("Belum ada vendor aktif yang menawarkan material ini, rekomendasi butuh minimal satu penawaran")
    transactions = await _load_transactions(session, request.request_date)
    vendors = pd.DataFrame((await session.execute(select(Vendor.id, Vendor.category))).all(), columns=["id", "category"])

    # perhitungan pandas dan LightGBM sinkron, dijalankan di thread supaya event loop tidak tertahan
    result = await asyncio.to_thread(
        ranking_engine.rank_candidates, _request_dict(request), offers, transactions, vendors,
    )
    await _replace_recommendations(session, request, result, offers)
    return await get_recommendation(session, request_id)


async def get_recommendation(session: AsyncSession, request_id: int) -> RecommendationResult:
    request, material = await procurement_request_service.get_request_with_material(session, request_id)
    rows = (
        await session.execute(
            select(Recommendation, Vendor)
            .join(Vendor, Recommendation.vendor_id == Vendor.id)
            .where(Recommendation.request_id == request_id)
            .order_by(Recommendation.rank.asc().nulls_last(), Vendor.name)
        )
    ).all()
    if not rows:
        raise AppError(404, f"Kebutuhan procurement dengan id {request_id} belum punya rekomendasi")

    first = rows[0][0]
    ranked = [_ranked_vendor(rec, vendor) for rec, vendor in rows if rec.is_eligible]
    rejected = [_rejected_vendor(rec, vendor, request, material) for rec, vendor in rows if not rec.is_eligible]
    return RecommendationResult(
        request=procurement_request_service.to_read(request, material),
        model_version=first.model_version,
        is_fallback=first.model_version == ranking_engine.FALLBACK_MODEL_VERSION,
        ranked_at=first.created_at,
        ranked=ranked,
        rejected=rejected,
    )


async def _load_offers(session: AsyncSession, material_id: int) -> pd.DataFrame:
    # vendor nonaktif (soft delete) bukan kandidat sama sekali, berbeda dengan penawaran yang tidak tersedia
    query = (
        select(VendorOffer.vendor_id, *(getattr(VendorOffer, c) for c in OFFER_COLUMNS))
        .join(Vendor, VendorOffer.vendor_id == Vendor.id)
        .where(VendorOffer.material_id == material_id, Vendor.is_active)
    )
    rows = (await session.execute(query)).all()
    offers = pd.DataFrame(rows, columns=["vendor_id", *OFFER_COLUMNS])
    return offers.astype({"unit_price": float})


async def _load_transactions(session: AsyncSession, request_date: date) -> pd.DataFrame:
    # anti leakage: transaksi yang dipesan setelah request tidak diambil sama sekali.
    # batas yang lebih ketat (delivered_date < request_date untuk metrik hasil) diterapkan di procurewise_ml.features
    query = select(*(getattr(Transaction, c) for c in TRANSACTION_COLUMNS)).where(Transaction.order_date < request_date)
    return pd.DataFrame((await session.execute(query)).all(), columns=list(TRANSACTION_COLUMNS))


def _request_dict(request: ProcurementRequest) -> dict:
    return {
        "material_id": request.material_id,
        "qty": request.qty,
        "request_date": request.request_date,
        "needed_by": request.needed_by,
        "priority": request.priority,
        "max_budget": float(request.max_budget) if request.max_budget is not None else None,
    }


async def _replace_recommendations(
    session: AsyncSession, request: ProcurementRequest, result: ranking_engine.RankingResult, offers: pd.DataFrame,
) -> None:
    """ranking ulang menggantikan hasil lama supaya satu request hanya punya satu ranking aktif."""
    await session.execute(delete(Recommendation).where(Recommendation.request_id == request.id))
    offer_by_vendor = offers.set_index("vendor_id")[list(OFFER_COLUMNS)].to_dict("index")
    for row in result.rows.to_dict("records"):
        eligible = bool(row["is_eligible"])
        session.add(
            Recommendation(
                request_id=request.id,
                vendor_id=int(row["vendor_id"]),
                is_eligible=eligible,
                filter_reasons=None if eligible else list(row["filter_reasons"]),
                rank=int(row["rank"]) if eligible else None,
                score=float(row["score"]) if eligible else None,
                model_version=result.model_version,
                features_json=_features_snapshot(row, offer_by_vendor[row["vendor_id"]]),
            )
        )
    request.status = "recommended"
    await session.commit()


def _features_snapshot(row: dict, offer: dict) -> dict:
    return {
        "offer": {column: _plain(value) for column, value in offer.items()},
        "features": {column: float(row[column]) for column in FEATURE_LABELS},
        "contributions": row["contributions"] if isinstance(row["contributions"], dict) else None,
    }


def _plain(value):
    # nilai numpy dari pandas tidak bisa langsung disimpan ke kolom JSONB
    return value.item() if hasattr(value, "item") else value


def _offer(rec: Recommendation) -> OfferSnapshot:
    return OfferSnapshot(**rec.features_json["offer"])


def _ranked_vendor(rec: Recommendation, vendor: Vendor) -> RankedVendor:
    feats = rec.features_json["features"]
    factors = [
        FeatureFactor(feature=name, label=FEATURE_LABELS[name], value=feats[name], contribution=value)
        for name, value in ranking_engine.top_contributions(rec.features_json["contributions"])
    ]
    return RankedVendor(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        vendor_city=vendor.city,
        rank=rec.rank,
        score=rec.score,
        offer=_offer(rec),
        total_cost=feats["total_cost"],
        slack_days=feats["slack_days"],
        history=VendorHistory(
            on_time_rate=feats["on_time_rate"],
            avg_delay_days=feats["avg_delay_days"],
            defect_rate=feats["defect_rate"],
            avg_rating=feats["avg_rating"],
            n_transactions=int(feats["n_transactions"]),
            has_history=bool(feats["has_history"]),
        ),
        top_factors=factors,
    )


def _rejected_vendor(rec: Recommendation, vendor: Vendor, request: ProcurementRequest, material: Material) -> RejectedVendor:
    offer = _offer(rec)
    return RejectedVendor(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        vendor_city=vendor.city,
        offer=offer,
        total_cost=rec.features_json["features"]["total_cost"],
        reasons=[
            FilterReason(code=code, message=_reason_message(code, offer, request, material.unit))
            for code in rec.filter_reasons or []
        ],
    )


def _reason_message(code: str, offer: OfferSnapshot, request: ProcurementRequest, unit: str) -> str:
    filters = ranking_engine.filters
    # tanpa modul ML kode alasan tidak bisa diterjemahkan, rekomendasi lama tetap tampil dengan kode mentahnya
    if filters is None:
        return code
    if code == filters.REASON_UNAVAILABLE:
        return "Vendor sedang tidak menerima pesanan untuk material ini"
    if code == filters.REASON_MOQ:
        return f"MOQ {offer.moq} {unit} lebih besar dari kebutuhan {request.qty} {unit}"
    if code == filters.REASON_CAPACITY:
        return (
            f"Kapasitas {offer.weekly_capacity} {unit} per minggu tidak cukup untuk {request.qty} {unit} "
            f"sampai {request.needed_by:%d-%m-%Y}"
        )
    if code == filters.REASON_BUDGET:
        return f"Total biaya {_rupiah(offer.unit_price * request.qty)} melebihi budget {_rupiah(request.max_budget)}"
    return code


def _rupiah(value) -> str:
    return "Rp" + f"{float(value):,.0f}".replace(",", ".")

