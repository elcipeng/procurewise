from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def to_asyncpg_url(url: str) -> str:
    """Ubah URL Postgres biasa (format Neon/Supabase) jadi URL SQLAlchemy + asyncpg."""
    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+asyncpg"

    # asyncpg tidak mengenal sslmode/channel_binding, pakai parameter ssl
    query = []
    for key, value in parse_qsl(parts.query):
        if key == "sslmode":
            query.append(("ssl", value))
        elif key != "channel_binding":
            query.append((key, value))

    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


# folder ml di root repo, berisi modul procurewise_ml dan file model
REPO_ML_DIR = Path(__file__).resolve().parents[3] / "ml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ProcureWise API"
    app_version: str = "0.1.0"
    environment: str = "development"

    database_url: str | None = None
    # Vercel mengisi env VERCEL=1 di fungsi serverless, koneksi DB lalu dibuka per request tanpa pool
    serverless: bool = Field(default=False, validation_alias="VERCEL")
    cors_origins: str = "http://localhost:5173"

    ml_dir: Path = REPO_ML_DIR
    # kosong berarti ml_dir/models. kalau model tidak bisa dimuat dari sini, ranking memakai fallback weighted sum
    ml_model_dir: Path | None = None

    # kosong berarti penjelasan rekomendasi langsung memakai template tanpa memanggil Gemini
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-4-hydrogen"
    gemini_timeout_seconds: float = 20.0

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str | None) -> str | None:
        return to_asyncpg_url(value) if value else None

    @property
    def model_dir(self) -> Path:
        return self.ml_model_dir or self.ml_dir / "models"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
