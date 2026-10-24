from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models import Material, ProcurementRequest, Transaction, VendorOffer
from app.schemas.material import MaterialCreate, MaterialUpdate

ENTITY = "Material"
# tabel yang merujuk materials.id dengan ondelete restrict
REFERENCES = (
    (VendorOffer, "penawaran vendor"),
    (Transaction, "transaksi"),
    (ProcurementRequest, "kebutuhan procurement"),
)


def _duplicate_code(code: str) -> ConflictError:
    return ConflictError(f"Kode material {code} sudah dipakai, kode material harus unik")


async def list_materials(session: AsyncSession, search: str | None, category: str | None) -> list[Material]:
    query = select(Material).order_by(Material.code)
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(Material.code.ilike(pattern), Material.name.ilike(pattern)))
    if category:
        query = query.where(Material.category == category)
    return list((await session.scalars(query)).all())


async def get_material(session: AsyncSession, material_id: int) -> Material:
    material = await session.get(Material, material_id)
    if material is None:
        raise NotFoundError(ENTITY, material_id)
    return material


async def _ensure_code_free(session: AsyncSession, code: str, exclude_id: int | None = None) -> None:
    query = select(Material.id).where(Material.code == code)
    if exclude_id is not None:
        query = query.where(Material.id != exclude_id)
    if await session.scalar(query) is not None:
        raise _duplicate_code(code)


async def _commit(session: AsyncSession, material: Material) -> Material:
    try:
        await session.commit()
    except IntegrityError as exc:
        # pengecekan awal bisa kalah balapan dengan request lain, unique constraint DB tetap jadi penjaga terakhir
        await session.rollback()
        raise _duplicate_code(material.code) from exc
    await session.refresh(material)
    return material


async def create_material(session: AsyncSession, payload: MaterialCreate) -> Material:
    await _ensure_code_free(session, payload.code)
    material = Material(**payload.model_dump())
    session.add(material)
    return await _commit(session, material)


async def update_material(session: AsyncSession, material_id: int, payload: MaterialUpdate) -> Material:
    material = await get_material(session, material_id)
    changes = payload.changes()
    if "code" in changes:
        await _ensure_code_free(session, changes["code"], exclude_id=material_id)
    for field, value in changes.items():
        setattr(material, field, value)
    return await _commit(session, material)


async def delete_material(session: AsyncSession, material_id: int) -> None:
    """material hanya bisa dihapus kalau belum dipakai di penawaran, transaksi, atau kebutuhan procurement."""
    material = await get_material(session, material_id)
    used = []
    for model, label in REFERENCES:
        count = await session.scalar(select(func.count()).where(model.material_id == material_id))
        if count:
            used.append(f"{count} {label}")
    if used:
        raise ConflictError(
            f"Material {material.code} tidak bisa dihapus karena masih dipakai oleh {', '.join(used)}"
        )
    await session.delete(material)
    await session.commit()
