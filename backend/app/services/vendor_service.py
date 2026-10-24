from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate

ENTITY = "Vendor"


async def list_vendors(
    session: AsyncSession, search: str | None, category: str | None, is_active: bool | None,
) -> list[Vendor]:
    query = select(Vendor).order_by(Vendor.id)
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(Vendor.name.ilike(pattern), Vendor.city.ilike(pattern)))
    if category:
        query = query.where(Vendor.category == category)
    if is_active is not None:
        query = query.where(Vendor.is_active == is_active)
    return list((await session.scalars(query)).all())


async def get_vendor(session: AsyncSession, vendor_id: int) -> Vendor:
    vendor = await session.get(Vendor, vendor_id)
    if vendor is None:
        raise NotFoundError(ENTITY, vendor_id)
    return vendor


async def create_vendor(session: AsyncSession, payload: VendorCreate) -> Vendor:
    vendor = Vendor(**payload.model_dump())
    session.add(vendor)
    await session.commit()
    await session.refresh(vendor)
    return vendor


async def update_vendor(session: AsyncSession, vendor_id: int, payload: VendorUpdate) -> Vendor:
    vendor = await get_vendor(session, vendor_id)
    for field, value in payload.changes().items():
        setattr(vendor, field, value)
    await session.commit()
    await session.refresh(vendor)
    return vendor


async def deactivate_vendor(session: AsyncSession, vendor_id: int) -> Vendor:
    """soft delete: histori transaksi dan rekomendasi tetap merujuk ke vendor ini, jadi baris tidak dihapus."""
    vendor = await get_vendor(session, vendor_id)
    if vendor.is_active:
        vendor.is_active = False
        await session.commit()
        await session.refresh(vendor)
    return vendor
