"""baseline ranking: weighted sum dan topsis. dihitung per request dari kandidat yang lolos filter.

skor makin besar makin baik. kandidat yang gugur filter diberi skor nan.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from procurewise_ml import config


def _criteria(df: pd.DataFrame) -> tuple[list[str], np.ndarray]:
    names = [name for name, _ in config.BASELINE_CRITERIA]
    is_benefit = np.array([direction == "benefit" for _, direction in config.BASELINE_CRITERIA])
    return names, is_benefit


def _weights_matrix(df: pd.DataFrame, weights_by_row: pd.Series | dict) -> np.ndarray:
    names, _ = _criteria(df)
    if isinstance(weights_by_row, dict):
        return np.tile([weights_by_row[n] for n in names], (len(df), 1))
    return np.array([[w[n] for n in names] for w in weights_by_row])


def weighted_sum(df: pd.DataFrame, weights: dict = config.BASELINE_FIXED_WEIGHTS) -> pd.Series:
    """min-max per request, kriteria cost dibalik, lalu dijumlah berbobot."""
    names, is_benefit = _criteria(df)
    eligible = df[df["is_eligible"]]
    values = eligible[names].astype(float)
    group = eligible["request_id"]
    low = values.groupby(group).transform("min")
    high = values.groupby(group).transform("max")
    span = (high - low).replace(0, np.nan)
    normalized = ((values - low) / span).to_numpy()
    normalized[:, ~is_benefit] = 1.0 - normalized[:, ~is_benefit]
    # kriteria yang nilainya sama di satu grup tidak membedakan kandidat
    normalized = np.where(span.isna().to_numpy(), 1.0, normalized)
    score = (normalized * _weights_matrix(eligible, weights)).sum(axis=1)
    return pd.Series(score, index=eligible.index).reindex(df.index)


def topsis(df: pd.DataFrame, weights: dict | None = None, weights_by_priority: dict | None = None) -> pd.Series:
    """topsis per request dengan normalisasi vektor. bobot tetap atau bobot dari priority request."""
    names, is_benefit = _criteria(df)
    eligible = df[df["is_eligible"]]
    values = eligible[names].astype(float)
    group = eligible["request_id"]
    norm = np.sqrt((values ** 2).groupby(group).transform("sum")).replace(0, np.nan)
    normalized = (values / norm).fillna(0.0)

    if weights_by_priority is not None:
        codes = {code: name for name, code in config.PRIORITY_CODES.items()}
        row_weights = eligible["priority_code"].map(lambda c: weights_by_priority[codes[c]])
        weighted = normalized * _weights_matrix(eligible, row_weights)
    else:
        weighted = normalized * _weights_matrix(eligible, weights or config.BASELINE_FIXED_WEIGHTS)
    weighted = pd.DataFrame(weighted, index=eligible.index, columns=names)

    group_max = weighted.groupby(group).transform("max").to_numpy()
    group_min = weighted.groupby(group).transform("min").to_numpy()
    ideal = np.where(is_benefit, group_max, group_min)
    anti_ideal = np.where(is_benefit, group_min, group_max)
    d_best = np.sqrt(((weighted.to_numpy() - ideal) ** 2).sum(axis=1))
    d_worst = np.sqrt(((weighted.to_numpy() - anti_ideal) ** 2).sum(axis=1))
    total = d_best + d_worst
    # semua kandidat identik di grup ini, beri skor tengah
    with np.errstate(invalid="ignore", divide="ignore"):
        closeness = np.where(total > 0, d_worst / total, 0.5)
    return pd.Series(closeness, index=eligible.index).reindex(df.index)


BASELINES: dict[str, Callable[[pd.DataFrame], pd.Series]] = {
    "weighted_sum": lambda df: weighted_sum(df, config.BASELINE_FIXED_WEIGHTS),
    "topsis": lambda df: topsis(df, weights=config.BASELINE_FIXED_WEIGHTS),
    "topsis_priority": lambda df: topsis(df, weights_by_priority=config.BASELINE_PRIORITY_WEIGHTS),
}
