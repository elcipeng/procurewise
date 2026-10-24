from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ApiResponse, respond
from app.db.session import get_session
from app.schemas.vendor import Category, VendorCreate, VendorRead, VendorUpdate
from app.services import vendor_service

router = APIRouter(prefix="/vendors", tags=["vendors"])
Session = Annotated[AsyncSession, Depends(get_session)]


def _read(vendor) -> VendorRead:
    return VendorRead.model_validate(vendor)


@router.get("", response_model=ApiResponse[list[VendorRead]])
async def list_vendors(
    session: Session,
    search: Annotated[str | None, Query(max_length=100, description="cari di nama atau kota")] = None,
    category: Category | None = None,
    is_active: bool | None = None,
):
    vendors = await vendor_service.list_vendors(session, search, category, is_active)
    return respond([_read(v) for v in vendors])


@router.post("", response_model=ApiResponse[VendorRead], status_code=201)
async def create_vendor(payload: VendorCreate, session: Session):
    vendor = await vendor_service.create_vendor(session, payload)
    return respond(_read(vendor), 201, "Vendor berhasil ditambahkan")


@router.get("/{vendor_id}", response_model=ApiResponse[VendorRead])
async def get_vendor(vendor_id: int, session: Session):
    return respond(_read(await vendor_service.get_vendor(session, vendor_id)))


@router.patch("/{vendor_id}", response_model=ApiResponse[VendorRead])
async def update_vendor(vendor_id: int, payload: VendorUpdate, session: Session):
    vendor = await vendor_service.update_vendor(session, vendor_id, payload)
    return respond(_read(vendor), message="Vendor berhasil diperbarui")


@router.delete("/{vendor_id}", response_model=ApiResponse[VendorRead])
async def deactivate_vendor(vendor_id: int, session: Session):
    """soft delete, vendor dinonaktifkan lewat is_active dan bisa diaktifkan lagi dengan patch."""
    vendor = await vendor_service.deactivate_vendor(session, vendor_id)
    return respond(_read(vendor), message="Vendor berhasil dinonaktifkan")
