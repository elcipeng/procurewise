"""lightgbm lambdarank untuk ranking vendor.

protokol:
- model dilatih di split train
- early stopping dan pemilihan hyperparameter hanya memakai split val
- split test hanya dipakai sekali untuk evaluasi akhir, di luar modul ini
"""

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from procurewise_ml import config
from procurewise_ml import evaluation as ev

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"


@dataclass
class TrainedRanker:
    model: lgb.LGBMRanker
    params: dict
    best_iteration: int
    val_ndcg_lgbm: float


def ranking_rows(df: pd.DataFrame, split: str) -> pd.DataFrame:
    """kandidat lolos di grup ranking pada satu split, diurutkan per request untuk parameter group."""
    eligible = df[(df["split"] == split) & df["is_eligible"]]
    counts = eligible.groupby("request_id")["vendor_id"].transform("size")
    rows = eligible[counts >= config.MIN_ELIGIBLE_CANDIDATES]
    return rows.sort_values(["request_id", "vendor_id"], kind="stable")


def _group_sizes(rows: pd.DataFrame) -> np.ndarray:
    return rows.groupby("request_id", sort=True).size().to_numpy()


def train_ranker(df: pd.DataFrame, params: dict) -> TrainedRanker:
    train, val = ranking_rows(df, "train"), ranking_rows(df, "val")
    features = list(config.FEATURE_COLUMNS)
    model = lgb.LGBMRanker(**{**config.LGBM_BASE_PARAMS, **params})
    model.fit(
        train[features], train["grade"].astype(int), group=_group_sizes(train),
        eval_X=(val[features],), eval_y=(val["grade"].astype(int),), eval_group=[_group_sizes(val)],
        eval_at=[config.RANKING_K],
        callbacks=[lgb.early_stopping(config.EARLY_STOPPING_ROUNDS, verbose=False)],
    )
    best = int(model.best_iteration_)
    return TrainedRanker(model, params, best, float(model.best_score_["valid_0"][f"ndcg@{config.RANKING_K}"]))


def predict_scores(model, df: pd.DataFrame) -> pd.Series:
    """skor untuk kandidat lolos filter, nan untuk yang gugur. menerima lgbmranker atau booster."""
    eligible = df[df["is_eligible"]]
    scores = model.predict(eligible[list(config.FEATURE_COLUMNS)])
    return pd.Series(scores, index=eligible.index).reindex(df.index)


def tune(df: pd.DataFrame, grid: dict = config.LGBM_TUNING_GRID) -> tuple[pd.DataFrame, dict]:
    """latih semua kombinasi grid, nilai di grup informatif val. test tidak disentuh."""
    rows = []
    keys = list(grid)
    for values in itertools.product(*(grid[k] for k in keys)):
        params = dict(zip(keys, values))
        trained = train_ranker(df, params)
        scores = predict_scores(trained.model, df)
        informative = ev.ranking_metrics(df, scores, informative_only=True).loc["val"]
        rows.append({
            **params,
            "best_iteration": trained.best_iteration,
            "val_ndcg@3_informatif": informative["ndcg@3"],
            "val_hit@1_informatif": informative["hit@1"],
            "val_ndcg@3_lightgbm": trained.val_ndcg_lgbm,
        })
    results = pd.DataFrame(rows).sort_values(
        ["val_ndcg@3_informatif", "val_hit@1_informatif", "best_iteration"], ascending=[False, False, True],
        kind="stable",
    ).reset_index(drop=True)
    best = {k: results.loc[0, k] for k in keys}
    best = {k: (int(v) if float(v).is_integer() and k != "learning_rate" else float(v)) for k, v in best.items()}
    return results, best


def contributions(model, rows: pd.DataFrame) -> pd.DataFrame:
    """kontribusi shap tiap fitur (treeshap bawaan lightgbm). kolom bias berisi nilai dasar."""
    values = model.predict(rows[list(config.FEATURE_COLUMNS)], pred_contrib=True)
    return pd.DataFrame(values, index=rows.index, columns=[*config.FEATURE_COLUMNS, "bias"])


def save_model(trained: TrainedRanker, metadata: dict, directory: Path = MODELS_DIR) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    model_path = directory / f"{config.MODEL_VERSION.replace('-', '_')}.txt"
    trained.model.booster_.save_model(str(model_path), num_iteration=trained.best_iteration)
    meta_path = model_path.with_suffix(".json")
    meta_path.write_text(json.dumps(metadata, indent=2, default=_json_default) + "\n", encoding="utf-8")
    return model_path, meta_path


def load_model(directory: Path = MODELS_DIR) -> tuple[lgb.Booster, dict]:
    model_path = directory / f"{config.MODEL_VERSION.replace('-', '_')}.txt"
    metadata = json.loads(model_path.with_suffix(".json").read_text(encoding="utf-8"))
    return lgb.Booster(model_file=str(model_path)), metadata


def _json_default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    raise TypeError(f"tidak bisa disimpan ke json: {type(value)}")
