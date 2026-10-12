import asyncio
import logging
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import get_engine

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    database: Literal["ok", "unavailable", "not_configured"]


async def check_database() -> str:
    engine = get_engine()
    if engine is None:
        return "not_configured"
    try:
        async with asyncio.timeout(5):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        logger.exception("Health check database gagal")
        return "unavailable"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=get_settings().app_version,
        database=await check_database(),
    )
