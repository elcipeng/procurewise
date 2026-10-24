"""bangun dataset training dari ml/data/raw ke ml/data/processed.

pemakaian dari folder ml:
    python -m procurewise_ml.build_dataset
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from procurewise_ml import config
from procurewise_ml.data import DATASET_FILE, PROCESSED_DIR, RAW_DIR, SPEC_FILE, RawData, load_raw
from procurewise_ml.features import build_features
from procurewise_ml.filters import hard_filter

METADATA_COLUMNS = (
    "request_id", "vendor_id", "material_id", "material_category", "request_date", "split",
    "is_eligible", "filter_reasons", "chosen",
)


def build_dataset(raw: RawData) -> pd.DataFrame:
    if set(config.FEATURE_COLUMNS) & set(config.FORBIDDEN_FEATURE_COLUMNS):
        raise ValueError("ada kolom terlarang di daftar fitur")

    features = build_features(raw.requests, raw.candidates, raw.transactions, raw.vendors)

    # filter keras dihitung ulang dengan modul yang sama dengan backend, harus sama dengan generator
    filtered = hard_filter(raw.requests, raw.candidates)
    same = (filtered["is_eligible"] == raw.candidates["is_eligible"]) & (
        filtered["filter_reasons"].map(sorted) == raw.candidates["filter_reasons"].map(sorted)
    )
    if not same.all():
        raise ValueError(f"filter keras beda dengan generator di {int((~same).sum())} kandidat")

    requests = raw.requests.rename(columns={"id": "request_id"})
    materials = raw.materials.rename(columns={"id": "material_id", "category": "material_category"})
    meta = (
        raw.candidates[["request_id", "vendor_id", "is_eligible", "filter_reasons", "chosen"]]
        .merge(requests[["request_id", "material_id", "request_date"]], on="request_id", how="left")
        .merge(materials[["material_id", "material_category"]], on="material_id", how="left")
        .merge(raw.meta[["request_id", "split"]], on="request_id", how="left")
    )
    dataset = meta[list(METADATA_COLUMNS)].merge(features, on=["request_id", "vendor_id"], validate="one_to_one")
    dataset = dataset.merge(
        raw.labels[["request_id", "vendor_id", *config.LABEL_COLUMNS]], on=["request_id", "vendor_id"],
        how="left", validate="one_to_one",
    )

    labeled = dataset["grade"].notna()
    if not (labeled == dataset["is_eligible"]).all():
        raise ValueError("label harus ada tepat untuk kandidat yang lolos filter")
    if dataset[list(config.FEATURE_COLUMNS)].isna().any().any():
        raise ValueError("ada fitur kosong")
    dataset["grade"] = dataset["grade"].astype("Int64")
    return dataset.sort_values(["request_id", "vendor_id"]).reset_index(drop=True)


def write_dataset(dataset: pd.DataFrame, raw: RawData, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    output = dataset.copy()
    output["filter_reasons"] = output["filter_reasons"].map(json.dumps)
    output["request_date"] = output["request_date"].dt.strftime("%Y-%m-%d")
    output.to_csv(out_dir / DATASET_FILE, index=False, lineterminator="\n", float_format="%.6f")

    counts = dataset.groupby("request_id").agg(split=("split", "first"), n_eligible=("is_eligible", "sum"))
    groups = counts[counts["n_eligible"] >= config.MIN_ELIGIBLE_CANDIDATES]
    spec = {
        "source": {"seed": raw.manifest["seed"], "config_hash": raw.manifest["config_hash"]},
        "rows": len(dataset),
        "feature_columns": list(config.FEATURE_COLUMNS),
        "label_columns": list(config.LABEL_COLUMNS),
        "metadata_columns": list(METADATA_COLUMNS),
        "requests_per_split": counts["split"].value_counts().reindex(config.SPLITS).to_dict(),
        "ranking_groups_per_split": groups["split"].value_counts().reindex(config.SPLITS).to_dict(),
    }
    (out_dir / SPEC_FILE).write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    return spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m procurewise_ml.build_dataset")
    parser.add_argument("--raw", type=Path, default=RAW_DIR)
    parser.add_argument("--out", type=Path, default=PROCESSED_DIR)
    args = parser.parse_args(argv)

    raw = load_raw(args.raw)
    dataset = build_dataset(raw)
    spec = write_dataset(dataset, raw, args.out)
    print(f"dataset dari seed {spec['source']['seed']} ditulis ke {args.out.resolve()}")
    print(f"baris: {spec['rows']:,}, fitur: {len(spec['feature_columns'])}")
    print(f"request per split: {spec['requests_per_split']}")
    print(f"grup ranking per split: {spec['ranking_groups_per_split']}")
    print("filter keras modul ml sama dengan generator untuk semua kandidat")
    return 0


if __name__ == "__main__":
    sys.exit(main())
