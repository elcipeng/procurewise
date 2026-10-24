import asyncio
import logging
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import get_settings
from app.core.responses import ApiResponse, respond
from app.db.session import get_engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])
DATABASE_TIMEOUT_SECONDS = 5


class HealthData(BaseModel):
    status: Literal["ok"]
    version: str
    database: Literal["ok", "unavailable", "not_configured"]


async def check_database() -> str:
    engine = get_engine()
    if engine is None:
        return "not_configured"
    try:
        async with asyncio.timeout(DATABASE_TIMEOUT_SECONDS):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        # health check tetap menjawab 200 supaya status aplikasi terpisah dari status database
        logger.exception("health check database gagal")
        return "unavailable"


@router.get("/health", response_model=ApiResponse[HealthData])
async def health():
    data = HealthData(status="ok", version=get_settings().app_version, database=await check_database())
    return respond(data)
