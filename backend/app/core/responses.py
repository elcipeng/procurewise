"""format response standar untuk semua endpoint, termasuk error."""

from datetime import datetime, timedelta, timezone
from typing import Any, Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# asia/jakarta tidak punya daylight saving, jadi offset tetap cukup tanpa paket tzdata
JAKARTA_TZ = timezone(timedelta(hours=7), "Asia/Jakarta")
SUCCESS_MESSAGE = "Success"

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status: int
    message: str
    timestamp: datetime
    data: T


class FieldError(BaseModel):
    field: str
    error: str


class EmptyResponse(ApiResponse[None]):
    pass


class ErrorResponse(ApiResponse[None]):
    pass


class ValidationErrorResponse(ApiResponse[list[FieldError]]):
    pass


def now_jakarta() -> datetime:
    return datetime.now(JAKARTA_TZ).replace(microsecond=0)


def respond(data: Any = None, status_code: int = 200, message: str = SUCCESS_MESSAGE) -> JSONResponse:
    body = {"status": status_code, "message": message, "timestamp": now_jakarta(), "data": data}
    return JSONResponse(status_code=status_code, content=jsonable_encoder(body))


# dipakai di openapi supaya swagger menampilkan bentuk error yang sebenarnya
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "Data tidak ditemukan"},
    409: {"model": ErrorResponse, "description": "Melanggar aturan bisnis"},
    422: {"model": ValidationErrorResponse, "description": "Data tidak valid"},
}
