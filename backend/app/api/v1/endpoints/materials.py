from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ApiResponse, EmptyResponse, respond
from app.db.session import get_session
from app.schemas.material import Category, MaterialCreate, MaterialRead, MaterialUpdate
from app.services import material_service

router = APIRouter(prefix="/materials", tags=["materials"])
Session = Annotated[AsyncSession, Depends(get_session)]


def _read(material) -> MaterialRead:
    return MaterialRead.model_validate(material)


@router.get("", response_model=ApiResponse[list[MaterialRead]])
async def list_materials(
    session: Session,
    search: Annotated[str | None, Query(max_length=100, description="cari di kode atau nama")] = None,
    category: Category | None = None,
):
    materials = await material_service.list_materials(session, search, category)
    return respond([_read(m) for m in materials])


@router.post("", response_model=ApiResponse[MaterialRead], status_code=201)
async def create_material(payload: MaterialCreate, session: Session):
    material = await material_service.create_material(session, payload)
    return respond(_read(material), 201, "Material berhasil ditambahkan")


@router.get("/{material_id}", response_model=ApiResponse[MaterialRead])
async def get_material(material_id: int, session: Session):
    return respond(_read(await material_service.get_material(session, material_id)))


@router.patch("/{material_id}", response_model=ApiResponse[MaterialRead])
async def update_material(material_id: int, payload: MaterialUpdate, session: Session):
    material = await material_service.update_material(session, material_id, payload)
    return respond(_read(material), message="Material berhasil diperbarui")


@router.delete("/{material_id}", response_model=EmptyResponse)
async def delete_material(material_id: int, session: Session):
    await material_service.delete_material(session, material_id)
    return respond(None, message="Material berhasil dihapus")
