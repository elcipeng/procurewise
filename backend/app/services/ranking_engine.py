"""jembatan ke modul ml/procurewise_ml untuk inference ranking vendor.

filter keras, fitur, dan baseline diimpor dari modul ML yang sama dengan training, tidak ditulis ulang di sini.
kalau model LightGBM gagal dimuat atau gagal memprediksi, ranking memakai baseline weighted sum
supaya aplikasi tetap memberi rekomendasi. kalau modul procurewise_ml sendiri gagal diimpor, aplikasi tetap
hidup (health dan CRUD jalan) dan hanya pembuatan rekomendasi yang menjawab 503.
"""

import logging
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.core.config import get_settings
from app.core.errors import AppError

logger = logging.getLogger(__name__)

FALLBACK_MODEL_VERSION = "weighted-sum-fallback"
ML_UNAVAILABLE_VERSION = "ml-unavailable"
ML_UNAVAILABLE_MESSAGE = "Modul ranking belum tersedia di server, rekomendasi belum bisa dibuat"
TOP_CONTRIBUTIONS = 3
# satu request di-ranking sendiri, jadi id grup cukup konstanta
GROUP_ID = 0

# saat development folder ml/ di repo didahulukan supaya perubahan modul langsung terpakai,
# di Vercel folder itu tidak ada sehingga yang dipakai paket procurewise_ml terinstal di site-packages
_ML_DIR = get_settings().ml_dir
if _ML_DIR.is_dir() and str(_ML_DIR) not in sys.path:
    sys.path.insert(0, str(_ML_DIR))

try:
    import procurewise_ml
    from procurewise_ml import baselines, features, filters
    from procurewise_ml import config as ml_config
except Exception:
    logger.exception("modul procurewise_ml gagal diimpor, rekomendasi dimatikan tapi aplikasi tetap jalan")
    procurewise_ml = baselines = features = filters = ml_config = None

ML_AVAILABLE = procurewise_ml is not None


@dataclass(frozen=True)
class LoadedModel:
    booster: object
    version: str


@dataclass
class RankingResult:
    """satu baris per kandidat: is_eligible, filter_reasons, score, rank, fitur, dan kontribusi."""

    rows: pd.DataFrame
    model_version: str
    is_fallback: bool


@lru_cache
def load_model() -> LoadedModel | None:
    """muat model sekali per proses. None berarti ranking memakai fallback weighted sum."""
    if not ML_AVAILABLE:
        return None
    try:
        # lightgbm diimpor di sini supaya kegagalan import juga jatuh ke fallback, bukan mematikan aplikasi
        from procurewise_ml import ranker

        booster, metadata = ranker.load_model(_model_dir())
        # backend wajib memakai urutan fitur yang sama dengan saat training
        if metadata["feature_columns"] != list(ml_config.FEATURE_COLUMNS):
            raise ValueError("urutan fitur model berbeda dengan procurewise_ml.config")
        return LoadedModel(booster=booster, version=metadata["model_version"])
    except Exception as exc:
        # tipe dan pesan exception ditulis di baris log supaya penyebabnya terbaca langsung di Vercel Logs
        hint = " (library OpenMP libgomp.so.1 tidak ada di runtime)" if "libgomp" in str(exc) else ""
        logger.exception(
            "model LightGBM gagal dimuat dari %s, ranking memakai fallback weighted sum: %s: %s%s",
            _model_dir() if ML_AVAILABLE else "-", type(exc).__name__, exc, hint,
        )
        return None


def _model_dir() -> Path:
    override = get_settings().ml_model_dir
    if override:
        return override
    # paket terinstal membawa model di procurewise_ml/models, sedangkan di repo model ada di ml/models
    packaged = Path(procurewise_ml.__file__).parent / "models"
    return packaged if packaged.is_dir() else _ML_DIR / "models"


def active_model_version() -> str:
    if not ML_AVAILABLE:
        return ML_UNAVAILABLE_VERSION
    model = load_model()
    return model.version if model else FALLBACK_MODEL_VERSION


def rank_candidates(
    request: dict, offers: pd.DataFrame, transactions: pd.DataFrame, vendors: pd.DataFrame,
) -> RankingResult:
    """ranking semua penawaran untuk satu request.

    request berisi material_id, qty, request_date, needed_by, priority, max_budget.
    offers berisi vendor_id, unit_price, moq, quoted_lead_time_days, weekly_capacity, is_available.
    fitur dihitung untuk semua kandidat (median harga memakai semua penawaran, sama seperti training),
    tapi hanya kandidat yang lolos filter keras yang diberi skor dan peringkat.
    """
    if not ML_AVAILABLE:
        raise AppError(503, ML_UNAVAILABLE_MESSAGE)
    requests = pd.DataFrame([{**request, "id": GROUP_ID}])
    # budget kosong harus NaN (bukan None) supaya filter melebihi_budget melewatinya
    requests["max_budget"] = pd.to_numeric(requests["max_budget"]).astype(float)
    for column in ("request_date", "needed_by"):
        requests[column] = pd.to_datetime(requests[column])
    candidates = offers.assign(request_id=GROUP_ID, unit_price=offers["unit_price"].astype(float))

    feats = features.build_features(requests, candidates, transactions, vendors)
    filtered = filters.hard_filter(requests, candidates)[["vendor_id", "is_eligible", "filter_reasons"]]
    df = feats.merge(filtered, on="vendor_id", validate="one_to_one")

    model = load_model()
    scores, contributions, version = None, None, FALLBACK_MODEL_VERSION
    if model is not None:
        try:
            scores, contributions = _predict_lightgbm(model, df)
            version = model.version
        except Exception:
            logger.exception("prediksi LightGBM gagal, ranking memakai fallback weighted sum")
    if scores is None:
        scores = baselines.weighted_sum(df)

    df["score"] = scores
    df["contributions"] = contributions
    df["rank"] = _ranks(df)
    return RankingResult(rows=df, model_version=version, is_fallback=version == FALLBACK_MODEL_VERSION)


def _predict_lightgbm(model: LoadedModel, df: pd.DataFrame) -> tuple[pd.Series, pd.Series | None]:
    eligible = df[df["is_eligible"]]
    if eligible.empty:
        return pd.Series(float("nan"), index=df.index), None
    matrix = eligible[list(ml_config.FEATURE_COLUMNS)]
    scores = pd.Series(model.booster.predict(matrix), index=eligible.index)
    # kontribusi TreeSHAP bawaan LightGBM, kolom terakhir adalah nilai dasar (bias)
    raw = model.booster.predict(matrix, pred_contrib=True)
    contributions = pd.Series(
        [dict(zip([*ml_config.FEATURE_COLUMNS, "bias"], map(float, row))) for row in raw], index=eligible.index,
    )
    return scores.reindex(df.index), contributions.reindex(df.index)


def _ranks(df: pd.DataFrame) -> pd.Series:
    eligible = df[df["is_eligible"] & df["score"].notna()]
    # skor sama jarang terjadi, total biaya lebih murah didahulukan supaya urutan selalu deterministik
    ordered = eligible.sort_values(["score", "total_cost", "vendor_id"], ascending=[False, True, True])
    ranks = pd.Series(range(1, len(ordered) + 1), index=ordered.index)
    return ranks.reindex(df.index)


def top_contributions(contributions: dict | None) -> list[tuple[str, float]]:
    """fitur dengan kontribusi absolut terbesar terhadap skor, tanpa bias."""
    if not contributions:
        return []
    items = [(name, value) for name, value in contributions.items() if name != "bias"]
    return sorted(items, key=lambda item: abs(item[1]), reverse=True)[:TOP_CONTRIBUTIONS]
