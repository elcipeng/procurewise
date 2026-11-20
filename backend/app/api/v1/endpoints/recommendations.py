from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ApiResponse, respond
from app.db.session import get_session
from app.schemas.explanation import ExplanationRead
from app.schemas.recommendation import RecommendationResult, RecommendationRun
from app.services import explanation_service, recommendation_service

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


@router.post("/{request_id}/explanation", response_model=ApiResponse[ExplanationRead])
async def explain_recommendation(request_id: int, session: Session):
    """penjelasan dan trade-off dari Gemini, dengan fallback template kalau Gemini tidak tersedia.

    penjelasan Gemini disimpan sebagai cache, jadi panggilan berikutnya untuk ranking yang sama tidak memanggil Gemini lagi.
    """
    explanation = await explanation_service.get_explanation(session, request_id)
    return respond(explanation, message="Penjelasan rekomendasi berhasil dibuat")
