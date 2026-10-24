"""error aplikasi dan handler global supaya semua error memakai format response standar."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import InterfaceError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.responses import respond

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1/"
# label entitas untuk pesan 422, diambil dari segmen path pertama setelah prefix
ENTITY_LABELS = {
    "vendors": "vendor",
    "materials": "material",
    "vendor-offers": "penawaran vendor",
}
DEFAULT_ENTITY_LABEL = "request"

# pesan validasi pydantic diterjemahkan supaya bisa langsung tampil di bawah field pada UI
VALIDATION_MESSAGES = {
    "missing": "wajib diisi",
    "string_too_short": "tidak boleh kosong",
    "string_too_long": "maksimal {max_length} karakter",
    "string_pattern_mismatch": "format tidak valid",
    "string_type": "harus berupa teks",
    "int_parsing": "harus berupa bilangan bulat",
    "int_type": "harus berupa bilangan bulat",
    "int_from_float": "harus berupa bilangan bulat",
    "decimal_parsing": "harus berupa angka",
    "decimal_type": "harus berupa angka",
    "decimal_max_digits": "maksimal {max_digits} digit",
    "decimal_max_places": "maksimal {decimal_places} angka di belakang koma",
    "decimal_whole_digits": "angka di depan koma terlalu panjang",
    "bool_parsing": "harus true atau false",
    "bool_type": "harus true atau false",
    "greater_than": "harus lebih dari {gt}",
    "greater_than_equal": "minimal {ge}",
    "less_than_equal": "maksimal {le}",
    "literal_error": "harus salah satu dari: {expected}",
    "extra_forbidden": "field tidak dikenal",
    "json_invalid": "format JSON tidak valid",
    "model_attributes_type": "format data tidak valid",
    "dict_type": "format data tidak valid",
}


class AppError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class NotFoundError(AppError):
    def __init__(self, entity: str, entity_id: int) -> None:
        super().__init__(404, f"{entity} dengan id {entity_id} tidak ditemukan")


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(409, message)


class FieldValidationError(AppError):
    """422 yang ditemukan di service, misalnya foreign key di body yang tidak ada."""

    def __init__(self, entity: str, field: str, error: str) -> None:
        super().__init__(422, f"Data {entity} tidak valid")
        self.errors = [{"field": field, "error": error}]


def _entity_label(path: str) -> str:
    if not path.startswith(API_PREFIX):
        return DEFAULT_ENTITY_LABEL
    segment = path[len(API_PREFIX):].split("/", 1)[0]
    return ENTITY_LABELS.get(segment, DEFAULT_ENTITY_LABEL)


def _field_name(location: tuple) -> str:
    # buang penanda sumber (body, query, path) supaya nama field sama dengan nama di form
    parts = [str(p) for p in location if p not in ("body", "query", "path")]
    return ".".join(parts) or "body"


def _translate(error: dict) -> str:
    template = VALIDATION_MESSAGES.get(error["type"])
    if template is None:
        # value error dari validator kustom sudah berbahasa indonesia
        return error["msg"].removeprefix("Value error, ")
    context = dict(error.get("ctx", {}))
    if "expected" in context:
        context["expected"] = context["expected"].replace("'", "").replace(" or ", ", ")
    return template.format(**context)


async def _app_error_handler(_: Request, exc: AppError):
    return respond(getattr(exc, "errors", None), exc.status_code, exc.message)


async def _validation_handler(request: Request, exc: RequestValidationError):
    errors = [
        # untuk json rusak, loc berisi posisi karakter, bukan nama field
        {"field": "body" if e["type"] == "json_invalid" else _field_name(e["loc"]), "error": _translate(e)}
        for e in exc.errors()
    ]
    return respond(errors, 422, f"Data {_entity_label(request.url.path)} tidak valid")


async def _http_error_handler(_: Request, exc: StarletteHTTPException):
    messages = {404: "Endpoint tidak ditemukan", 405: "Metode tidak diizinkan untuk endpoint ini"}
    return respond(None, exc.status_code, messages.get(exc.status_code, str(exc.detail)))


async def _database_error_handler(_: Request, exc: Exception):
    logger.exception("database tidak dapat diakses", exc_info=exc)
    return respond(None, 503, "Database sedang tidak dapat diakses, coba lagi nanti")


async def _unexpected_error_handler(_: Request, exc: Exception):
    # aplikasi tidak boleh crash, detail error hanya masuk log server
    logger.exception("error tidak terduga", exc_info=exc)
    return respond(None, 500, "Terjadi kesalahan pada server")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(StarletteHTTPException, _http_error_handler)
    for error in (OperationalError, InterfaceError, ConnectionError, TimeoutError):
        app.add_exception_handler(error, _database_error_handler)
    app.add_exception_handler(Exception, _unexpected_error_handler)
