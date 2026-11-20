from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ApiResponse, respond
from app.db.session import get_session
from app.schemas.recommendation import RecommendationResult, RecommendationRun
from app.services import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=ApiResponse[RecommendationResult], status_code=201)
async def run_recommendation(payload: RecommendationRun, session: Session):
    """inference ranking vendor: filter keras, fitur, LightGBM (fallback weighted sum), lalu disimpan.

    memanggil ulang untuk request yang sama menggantikan ranking sebelumnya.
    """
    result = await recommendation_service.run_recommendation(session, payload.request_id)
    return respond(result, 201, "Rekomendasi vendor berhasil dibuat")


@router.get("/{request_id}", response_model=ApiResponse[RecommendationResult])
async def get_recommendation(request_id: int, session: Session):
    return respond(await recommendation_service.get_recommendation(session, request_id))
