from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ApiResponse, EmptyResponse, respond
from app.db.session import get_session
from app.schemas.vendor_offer import VendorOfferCreate, VendorOfferRead, VendorOfferUpdate
from app.services import vendor_offer_service

router = APIRouter(prefix="/vendor-offers", tags=["vendor offers"])
Session = Annotated[AsyncSession, Depends(get_session)]
OptionalId = Annotated[int | None, Query(ge=1)]


@router.get("", response_model=ApiResponse[list[VendorOfferRead]])
async def list_offers(
    session: Session,
    vendor_id: OptionalId = None,
    material_id: OptionalId = None,
    is_available: bool | None = None,
):
    return respond(await vendor_offer_service.list_offers(session, vendor_id, material_id, is_available))


@router.post("", response_model=ApiResponse[VendorOfferRead], status_code=201)
async def create_offer(payload: VendorOfferCreate, session: Session):
    offer = await vendor_offer_service.create_offer(session, payload)
    return respond(offer, 201, "Penawaran vendor berhasil ditambahkan")


@router.get("/{offer_id}", response_model=ApiResponse[VendorOfferRead])
async def get_offer(offer_id: int, session: Session):
    return respond(await vendor_offer_service.get_offer(session, offer_id))


@router.patch("/{offer_id}", response_model=ApiResponse[VendorOfferRead])
async def update_offer(offer_id: int, payload: VendorOfferUpdate, session: Session):
    offer = await vendor_offer_service.update_offer(session, offer_id, payload)
    return respond(offer, message="Penawaran vendor berhasil diperbarui")


@router.delete("/{offer_id}", response_model=EmptyResponse)
async def delete_offer(offer_id: int, session: Session):
    await vendor_offer_service.delete_offer(session, offer_id)
    return respond(None, message="Penawaran vendor berhasil dihapus")
