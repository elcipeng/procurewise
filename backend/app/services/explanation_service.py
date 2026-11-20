"""penjelasan rekomendasi dengan Gemini, validasi angka, generate ulang sekali, dan fallback template.

urutan:
1. kalau rekomendasi sudah punya penjelasan Gemini di recommendations.explanation, pakai cache itu.
2. kalau GEMINI_API_KEY kosong, langsung pakai template.
3. panggil Gemini. kalau ada angka yang tidak ada di input, generate ulang sekali dengan catatan perbaikan.
4. kalau API gagal, kena limit, atau angka tetap tidak cocok, pakai template.
penjelasan template tidak di-cache supaya penjelasan Gemini bisa dibuat begitu layanan tersedia lagi.
"""

import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.responses import now_jakarta
from app.models import Recommendation
from app.schemas.explanation import ExplanationContent, ExplanationRead, FallbackReason
from app.schemas.recommendation import RecommendationResult
from app.services import explanation_builder, gemini_client, recommendation_service

logger = logging.getLogger(__name__)

MAX_GEMINI_ATTEMPTS = 2


def _read(content: ExplanationContent, model: str | None, reason: FallbackReason | None) -> ExplanationRead:
    return ExplanationRead(
        **content.model_dump(),
        source="template" if reason else "gemini",
        model=model,
        fallback_reason=reason,
        generated_at=now_jakarta(),
    )


async def build_explanation(result: RecommendationResult) -> ExplanationRead:
    template = explanation_builder.build_template(result)
    settings = get_settings()
    if not settings.gemini_api_key:
        return _read(template, None, "api_key_kosong")

    payload = explanation_builder.build_payload(result)
    allowed = explanation_builder.allowed_numbers(payload)
    expected_ids = {v.vendor_id for v in result.ranked[: explanation_builder.TOP_VENDORS]}
    correction = None
    for attempt in range(1, MAX_GEMINI_ATTEMPTS + 1):
        try:
            content = await gemini_client.generate_explanation(payload, correction)
        except gemini_client.GeminiRateLimited:
            logger.warning("gemini kena batas pemakaian, penjelasan memakai template")
            return _read(template, None, "batas_pemakaian")
        except Exception:
            # aplikasi tidak boleh gagal karena layanan AI, detail error hanya masuk log server
            logger.exception("gemini gagal dipanggil, penjelasan memakai template")
            return _read(template, None, "api_gagal")

        content = explanation_builder.sanitize(content)
        problems = explanation_builder.find_problems(content, allowed, expected_ids)
        if not problems:
            return _read(content, settings.gemini_model, None)
        logger.warning("output gemini percobaan %s ditolak: %s", attempt, " | ".join(problems))
        correction = " dan ".join(problems)

    return _read(template, None, "angka_tidak_cocok")


async def get_explanation(session: AsyncSession, request_id: int) -> ExplanationRead:
    result = await recommendation_service.get_recommendation(session, request_id)
    cached = await session.scalar(
        select(Recommendation.explanation)
        .where(Recommendation.request_id == request_id, Recommendation.explanation.is_not(None))
        .limit(1)
    )
    if cached:
        return ExplanationRead.model_validate(cached)

    explanation = await build_explanation(result)
    if explanation.source == "gemini":
        # disimpan di semua baris request ini. ranking ulang menghapus baris lama, jadi cache ikut hilang
        await session.execute(
            update(Recommendation)
            .where(Recommendation.request_id == request_id)
            .values(explanation=explanation.model_dump(mode="json"))
        )
        await session.commit()
    return explanation
