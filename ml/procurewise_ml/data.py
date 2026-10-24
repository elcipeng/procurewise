"""baca csv generator dan dataset hasil olahan. hanya modul ini yang menyentuh file."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ML_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ML_DIR / "data" / "raw"
PROCESSED_DIR = ML_DIR / "data" / "processed"
DATASET_FILE = "dataset.csv"
SPEC_FILE = "dataset_spec.json"

# file yang boleh dibaca untuk fitur. _hidden_vendor_traits.csv sengaja tidak ada di sini
FEATURE_SOURCES = {
    "requests": "procurement_requests.csv",
    "candidates": "_candidates.csv",
    "transactions": "transactions.csv",
    "vendors": "vendors.csv",
    "materials": "materials.csv",
}
# label dan split, hanya untuk training dan evaluasi
LABEL_SOURCES = {
    "labels": "_labels.csv",
    "meta": "_request_meta.csv",
}


@dataclass
class RawData:
    requests: pd.DataFrame
    candidates: pd.DataFrame
    transactions: pd.DataFrame
    vendors: pd.DataFrame
    materials: pd.DataFrame
    labels: pd.DataFrame
    meta: pd.DataFrame
    manifest: dict


def load_raw(raw_dir: Path = RAW_DIR) -> RawData:
    frames = {}
    for name, filename in {**FEATURE_SOURCES, **LABEL_SOURCES}.items():
        frames[name] = pd.read_csv(raw_dir / filename)
    frames["requests"]["request_date"] = pd.to_datetime(frames["requests"]["request_date"])
    frames["requests"]["needed_by"] = pd.to_datetime(frames["requests"]["needed_by"])
    for column in ("order_date", "promised_date", "delivered_date"):
        frames["transactions"][column] = pd.to_datetime(frames["transactions"][column])
    frames["candidates"]["filter_reasons"] = frames["candidates"]["filter_reasons"].fillna("[]").map(json.loads)
    manifest = json.loads((raw_dir / "_manifest.json").read_text(encoding="utf-8"))
    return RawData(**frames, manifest=manifest)


def load_dataset(processed_dir: Path = PROCESSED_DIR) -> tuple[pd.DataFrame, dict]:
    spec = json.loads((processed_dir / SPEC_FILE).read_text(encoding="utf-8"))
    df = pd.read_csv(processed_dir / DATASET_FILE, parse_dates=["request_date"])
    df["filter_reasons"] = df["filter_reasons"].fillna("[]").map(json.loads)
    return df, spec
