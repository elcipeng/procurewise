"""cek kestabilan model di beberapa seed data dengan hyperparameter yang sama.

data tiap seed dibuat dengan generator lewat subprocess supaya modul ini tidak mengimpor generator.
hasil generator disimpan di ml/data/seeds/seed_<n>/raw dan dipakai ulang kalau sudah ada.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

from procurewise_ml import config
from procurewise_ml import evaluation as ev
from procurewise_ml.baselines import BASELINES
from procurewise_ml.build_dataset import build_dataset
from procurewise_ml.data import ML_DIR, RAW_DIR, load_raw
from procurewise_ml.ranker import predict_scores, train_ranker

SEEDS_DIR = ML_DIR / "data" / "seeds"
MAIN_SEED = 15037


def raw_dir_for(seed: int) -> Path:
    if seed == MAIN_SEED:
        return RAW_DIR
    raw = SEEDS_DIR / f"seed_{seed}" / "raw"
    if not (raw / "_manifest.json").exists():
        subprocess.run(
            [sys.executable, "-m", "generator", "--seed", str(seed), "--out", str(raw)],
            cwd=ML_DIR, check=True, capture_output=True, text=True,
        )
    return raw


def evaluate_seed(seed: int, params: dict) -> dict:
    dataset = build_dataset(load_raw(raw_dir_for(seed)))
    trained = train_ranker(dataset, params)
    scores = {"lightgbm": predict_scores(trained.model, dataset), "weighted_sum": BASELINES["weighted_sum"](dataset)}
    row = {"seed": seed, "best_iteration": trained.best_iteration}
    for label, informative in (("informatif", True), ("semua", False)):
        tables = {name: ev.ranking_metrics(dataset, s, informative_only=informative).loc["test"] for name, s in scores.items()}
        row[f"n_grup_{label}"] = int(tables["lightgbm"]["n_grup"])
        for metric in ("ndcg@3", "hit@1"):
            row[f"{metric}_lgbm_{label}"] = tables["lightgbm"][metric]
            row[f"{metric}_ws_{label}"] = tables["weighted_sum"][metric]
            row[f"{metric}_selisih_{label}"] = tables["lightgbm"][metric] - tables["weighted_sum"][metric]
    return row


def run_stability(params: dict, seeds: tuple[int, ...] = config.STABILITY_SEEDS) -> pd.DataFrame:
    return pd.DataFrame([evaluate_seed(seed, params) for seed in seeds]).set_index("seed")
