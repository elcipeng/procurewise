from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ApiResponse, PageMeta, PaginatedResponse, respond
from app.db.session import get_session
from app.schemas.procurement_request import ProcurementRequestCreate, ProcurementRequestRead, RequestStatus
from app.services import procurement_request_service

router = APIRouter(prefix="/procurement-requests", tags=["procurement requests"])
Session = Annotated[AsyncSession, Depends(get_session)]
MAX_PAGE_SIZE = 100


@router.get("", response_model=PaginatedResponse[list[ProcurementRequestRead]])
async def list_requests(
    session: Session,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 20,
    status: RequestStatus | None = None,
):
    items, total = await procurement_request_service.list_requests(session, page, page_size, status)
    return respond(items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.post("", response_model=ApiResponse[ProcurementRequestRead], status_code=201)
async def create_request(payload: ProcurementRequestCreate, session: Session):
    request = await procurement_request_service.create_request(session, payload)
    return respond(request, 201, "Kebutuhan procurement berhasil disimpan")


@router.get("/{request_id}", response_model=ApiResponse[ProcurementRequestRead])
async def get_request(request_id: int, session: Session):
    return respond(await procurement_request_service.get_request(session, request_id))
