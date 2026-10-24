from fastapi import APIRouter

from app.api.v1.endpoints import health, materials, vendor_offers, vendors
from app.core.responses import ERROR_RESPONSES

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
for module in (vendors, materials, vendor_offers):
    api_router.include_router(module.router, responses=ERROR_RESPONSES)
