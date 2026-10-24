from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, FieldValidationError, NotFoundError
from app.models import Material, Vendor, VendorOffer
from app.schemas.vendor_offer import VendorOfferCreate, VendorOfferRead, VendorOfferUpdate

ENTITY = "Penawaran vendor"
ENTITY_LABEL = "penawaran vendor"


def _base_query():
    return (
        select(VendorOffer, Vendor, Material)
        .join(Vendor, VendorOffer.vendor_id == Vendor.id)
        .join(Material, VendorOffer.material_id == Material.id)
    )


def _to_read(offer: VendorOffer, vendor: Vendor, material: Material) -> VendorOfferRead:
    return VendorOfferRead(
        id=offer.id,
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        vendor_is_active=vendor.is_active,
        material_id=material.id,
        material_code=material.code,
        material_name=material.name,
        material_unit=material.unit,
        unit_price=offer.unit_price,
        moq=offer.moq,
        quoted_lead_time_days=offer.quoted_lead_time_days,
        weekly_capacity=offer.weekly_capacity,
        is_available=offer.is_available,
        updated_at=offer.updated_at,
    )


def _duplicate_pair(vendor: Vendor, material: Material) -> ConflictError:
    return ConflictError(
        f"{vendor.name} sudah punya penawaran untuk material {material.code}, "
        "satu vendor hanya boleh punya satu penawaran per material"
    )


async def list_offers(
    session: AsyncSession, vendor_id: int | None, material_id: int | None, is_available: bool | None,
) -> list[VendorOfferRead]:
    query = _base_query().order_by(Material.code, Vendor.name)
    if vendor_id is not None:
        query = query.where(VendorOffer.vendor_id == vendor_id)
    if material_id is not None:
        query = query.where(VendorOffer.material_id == material_id)
    if is_available is not None:
        query = query.where(VendorOffer.is_available == is_available)
    return [_to_read(*row) for row in (await session.execute(query)).all()]


async def get_offer(session: AsyncSession, offer_id: int) -> VendorOfferRead:
    row = (await session.execute(_base_query().where(VendorOffer.id == offer_id))).first()
    if row is None:
        raise NotFoundError(ENTITY, offer_id)
    return _to_read(*row)


async def create_offer(session: AsyncSession, payload: VendorOfferCreate) -> VendorOfferRead:
    vendor = await session.get(Vendor, payload.vendor_id)
    if vendor is None:
        raise FieldValidationError(ENTITY_LABEL, "vendor_id", f"vendor dengan id {payload.vendor_id} tidak ditemukan")
    material = await session.get(Material, payload.material_id)
    if material is None:
        raise FieldValidationError(
            ENTITY_LABEL, "material_id", f"material dengan id {payload.material_id} tidak ditemukan"
        )
    # vendor nonaktif tidak boleh muncul lagi sebagai kandidat rekomendasi
    if not vendor.is_active:
        raise ConflictError(f"{vendor.name} sedang nonaktif, aktifkan vendor dulu sebelum menambah penawaran")

    existing = await session.scalar(
        select(VendorOffer.id).where(
            VendorOffer.vendor_id == vendor.id, VendorOffer.material_id == material.id
        )
    )
    if existing is not None:
        raise _duplicate_pair(vendor, material)

    offer = VendorOffer(**payload.model_dump())
    session.add(offer)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise _duplicate_pair(vendor, material) from exc
    await session.refresh(offer)
    return await get_offer(session, offer.id)


async def update_offer(session: AsyncSession, offer_id: int, payload: VendorOfferUpdate) -> VendorOfferRead:
    offer = await session.get(VendorOffer, offer_id)
    if offer is None:
        raise NotFoundError(ENTITY, offer_id)
    for field, value in payload.changes().items():
        setattr(offer, field, value)
    await session.commit()
    await session.refresh(offer)
    return await get_offer(session, offer_id)


async def delete_offer(session: AsyncSession, offer_id: int) -> None:
    offer = await session.get(VendorOffer, offer_id)
    if offer is None:
        raise NotFoundError(ENTITY, offer_id)
    await session.delete(offer)
    await session.commit()
