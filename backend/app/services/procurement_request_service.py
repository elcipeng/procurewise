from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, FieldValidationError, NotFoundError
from app.core.responses import now_jakarta
from app.models import Material, ProcurementRequest, User
from app.schemas.procurement_request import ProcurementRequestCreate, ProcurementRequestRead

ENTITY = "Kebutuhan procurement"
ENTITY_LABEL = "kebutuhan procurement"
# belum ada login, jadi request baru dicatat atas nama owner
DEFAULT_CREATOR_ROLE = "owner"


def _base_query():
    return select(ProcurementRequest, Material).join(Material, ProcurementRequest.material_id == Material.id)


def to_read(request: ProcurementRequest, material: Material) -> ProcurementRequestRead:
    return ProcurementRequestRead(
        id=request.id,
        material_id=material.id,
        material_code=material.code,
        material_name=material.name,
        material_unit=material.unit,
        material_category=material.category,
        qty=request.qty,
        request_date=request.request_date,
        needed_by=request.needed_by,
        priority=request.priority,
        max_budget=request.max_budget,
        notes=request.notes,
        status=request.status,
        created_at=request.created_at,
    )


async def list_requests(
    session: AsyncSession, page: int, page_size: int, status: str | None,
) -> tuple[list[ProcurementRequestRead], int]:
    query = _base_query()
    count_query = select(func.count()).select_from(ProcurementRequest)
    if status is not None:
        query = query.where(ProcurementRequest.status == status)
        count_query = count_query.where(ProcurementRequest.status == status)
    total = await session.scalar(count_query)
    rows = await session.execute(
        query.order_by(ProcurementRequest.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return [to_read(*row) for row in rows.all()], total


async def get_request_with_material(session: AsyncSession, request_id: int) -> tuple[ProcurementRequest, Material]:
    row = (await session.execute(_base_query().where(ProcurementRequest.id == request_id))).first()
    if row is None:
        raise NotFoundError(ENTITY, request_id)
    return row.tuple()


async def get_request(session: AsyncSession, request_id: int) -> ProcurementRequestRead:
    return to_read(*await get_request_with_material(session, request_id))


async def create_request(session: AsyncSession, payload: ProcurementRequestCreate) -> ProcurementRequestRead:
    today = now_jakarta().date()
    if payload.needed_by < today:
        raise FieldValidationError(ENTITY_LABEL, "needed_by", "tidak boleh sebelum hari ini")
    if await session.get(Material, payload.material_id) is None:
        raise FieldValidationError(
            ENTITY_LABEL, "material_id", f"material dengan id {payload.material_id} tidak ditemukan"
        )
    creator_id = await session.scalar(
        select(User.id).where(User.role == DEFAULT_CREATOR_ROLE).order_by(User.id).limit(1)
    )
    if creator_id is None:
        raise ConflictError("Belum ada user owner di database, kebutuhan procurement butuh user pencatat")

    request = ProcurementRequest(
        **payload.model_dump(), request_date=today, created_by=creator_id, status="new",
    )
    session.add(request)
    await session.commit()
    return await get_request(session, request.id)
