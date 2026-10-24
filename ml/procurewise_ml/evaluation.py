"""evaluasi ranking yang dipakai ulang untuk semua model.

input selalu dataframe dataset (satu baris per request dan vendor) plus series skor dengan index yang sama.
skor makin besar makin baik. kandidat gugur filter diabaikan.

konvensi:
- grup ranking = request dengan minimal config.MIN_ELIGIBLE_CANDIDATES kandidat lolos filter
- gain ndcg = 2^grade - 1. grup yang semua grade-nya 0 diberi ndcg 1, sama dengan konvensi lightgbm
- hit@1 = kandidat peringkat 1 punya grade tertinggi di grupnya
- mrr = 1 / peringkat kandidat pertama yang punya grade tertinggi di grupnya
- skor seri dipecah dengan vendor_id terkecil supaya hasil deterministik
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from procurewise_ml import config


def rank_candidates(df: pd.DataFrame, scores: pd.Series) -> pd.DataFrame:
    """kandidat lolos di grup ranking, diurutkan per request, dengan kolom rank mulai dari 1."""
    eligible = df[df["is_eligible"]].assign(score=scores)
    counts = eligible.groupby("request_id")["vendor_id"].transform("size")
    ranked = eligible[counts >= config.MIN_ELIGIBLE_CANDIDATES]
    if ranked["score"].isna().any():
        raise ValueError("ada kandidat lolos filter yang tidak punya skor")
    ranked = ranked.sort_values(["request_id", "score", "vendor_id"], ascending=[True, False, True], kind="stable")
    return ranked.assign(rank=ranked.groupby("request_id").cumcount() + 1)


def _group_metrics(ranked: pd.DataFrame, k: int) -> pd.DataFrame:
    gain = 2.0 ** ranked["grade"] - 1
    discount = 1.0 / np.log2(ranked["rank"] + 1)
    ranked = ranked.assign(dcg=np.where(ranked["rank"] <= k, gain * discount, 0.0))

    ideal = ranked.sort_values(["request_id", "grade"], ascending=[True, False], kind="stable")
    ideal_rank = ideal.groupby("request_id").cumcount() + 1
    ideal_dcg = np.where(ideal_rank <= k, (2.0 ** ideal["grade"] - 1) / np.log2(ideal_rank + 1), 0.0)
    idcg = pd.Series(ideal_dcg, index=ideal.index).groupby(ideal["request_id"]).sum()

    best = ranked.groupby("request_id")["grade"].transform("max")
    best_grade = ranked.groupby("request_id")["grade"].max()
    first_best = ranked[ranked["grade"] == best].groupby("request_id")["rank"].min()
    top = ranked[ranked["rank"] == 1].set_index("request_id")

    out = pd.DataFrame({
        "split": top["split"],
        "material_category": top["material_category"],
        "dcg": ranked.groupby("request_id")["dcg"].sum(),
        "idcg": idcg,
        "hit_at_1": (top["grade"] == best_grade).astype(float),
        "mrr": 1.0 / first_best,
        "informative": ranked.groupby("request_id")["grade"].nunique() > 1,
    })
    out[f"ndcg_at_{k}"] = np.where(out["idcg"] > 0, out["dcg"] / out["idcg"].replace(0, np.nan), 1.0)
    return out.drop(columns=["dcg", "idcg"])


def ranking_metrics(
    df: pd.DataFrame, scores: pd.Series, k: int = config.RANKING_K, informative_only: bool = False,
) -> pd.DataFrame:
    """ndcg@k, hit@1, mrr per split."""
    groups = _group_metrics(rank_candidates(df, scores), k)
    if informative_only:
        groups = groups[groups["informative"]]
    table = groups.groupby("split").agg(
        n_grup=("mrr", "size"), **{f"ndcg@{k}": (f"ndcg_at_{k}", "mean")},
        **{"hit@1": ("hit_at_1", "mean"), "mrr": ("mrr", "mean")},
    )
    return table.reindex([s for s in config.SPLITS if s in table.index])


def business_metrics(df: pd.DataFrame, scores: pd.Series) -> pd.DataFrame:
    """hasil vendor peringkat 1 menurut simulasi: on-time terhadap needed_by, defect, dan biaya."""
    ranked = rank_candidates(df, scores)
    cheapest = ranked.groupby("request_id")["e_biaya"].transform("min")
    top = ranked.assign(biaya_relatif=ranked["e_biaya"] / cheapest)[ranked["rank"] == 1]
    table = top.groupby("split").agg(
        n_grup=("request_id", "size"),
        on_time=("p_tepat", "mean"),
        defect_rate=("e_cacat", "mean"),
        total_biaya=("e_biaya", "sum"),
        biaya_relatif=("biaya_relatif", "mean"),
        rata_grade=("grade", "mean"),
        top1_grade_0=("grade", lambda g: (g == 0).mean()),
    )
    return table.reindex([s for s in config.SPLITS if s in table.index])


def compare(df: pd.DataFrame, scores: dict[str, pd.Series], split: str, informative_only: bool = False) -> pd.DataFrame:
    """satu baris per model untuk satu split, gabungan metrik ranking dan bisnis."""
    rows = {}
    for name, score in scores.items():
        ranking = ranking_metrics(df, score, informative_only=informative_only)
        business = business_metrics(df, score)
        rows[name] = pd.concat([ranking.loc[split], business.loc[split].drop("n_grup")])
    return pd.DataFrame(rows).T


def coverage(df: pd.DataFrame) -> pd.DataFrame:
    """jumlah request yang keluar dari metrik ranking karena kandidat lolos kurang dari batas, per kategori."""
    per_request = df.groupby("request_id").agg(
        material_category=("material_category", "first"),
        n_eligible=("is_eligible", "sum"),
    )
    per_request["dikeluarkan"] = per_request["n_eligible"] < config.MIN_ELIGIBLE_CANDIDATES
    per_request["tanpa_kandidat"] = per_request["n_eligible"] == 0
    table = per_request.groupby("material_category").agg(
        n_request=("dikeluarkan", "size"),
        dikeluarkan=("dikeluarkan", "sum"),
        tanpa_kandidat_lolos=("tanpa_kandidat", "sum"),
    )
    table.loc["total"] = table.sum()
    table["persen_dikeluarkan"] = table["dikeluarkan"] / table["n_request"]
    return table


def reference_scores(df: pd.DataFrame) -> dict[str, pd.Series]:
    """pembanding: urutan acak, pilihan historis firaza, dan oracle dari label."""
    rng = np.random.default_rng(config.RANDOM_BASELINE_SEED)
    eligible = df["is_eligible"]
    random_score = pd.Series(rng.random(len(df)), index=df.index).where(eligible)
    historical = df["chosen"].astype(float).where(eligible)
    oracle = (df["grade"] + df["skor_hasil"] / 10).where(eligible)
    return {"acak": random_score, "pilihan_historis": historical, "oracle": oracle}


def group_metrics(df: pd.DataFrame, scores: pd.Series, k: int = config.RANKING_K) -> pd.DataFrame:
    """metrik per grup ranking (satu baris per request)."""
    return _group_metrics(rank_candidates(df, scores), k)


def request_segments(df: pd.DataFrame) -> pd.DataFrame:
    """segmen per request dari fitur yang terlihat, untuk breakdown evaluasi."""
    eligible = df[df["is_eligible"]]
    per_request = eligible.groupby("request_id").agg(
        priority_code=("priority_code", "first"),
        median_slack=("slack_days", "median"),
        is_peak_season=("is_peak_season", "first"),
        material_category=("material_category", "first"),
    )
    codes = {code: name for name, code in config.PRIORITY_CODES.items()}
    return pd.DataFrame({
        "priority": per_request["priority_code"].map(codes),
        "slack": np.where(per_request["median_slack"] <= config.TIGHT_SLACK_DAYS, "ketat", "longgar"),
        "musim": np.where(per_request["is_peak_season"] == 1, "puncak", "normal"),
        "kategori": per_request["material_category"],
    }, index=per_request.index)


def segment_compare(
    df: pd.DataFrame, scores: dict[str, pd.Series], split: str, informative_only: bool = True,
    k: int = config.RANKING_K,
) -> pd.DataFrame:
    """ndcg@k dan hit@1 per segmen untuk setiap model di satu split."""
    segments = request_segments(df)
    tables = []
    for name, score in scores.items():
        groups = group_metrics(df, score, k)
        groups = groups[groups["split"] == split]
        if informative_only:
            groups = groups[groups["informative"]]
        groups = groups.join(segments.drop(columns="kategori"))
        for column in ("priority", "slack", "musim", "material_category"):
            part = groups.groupby(column).agg(
                n_grup=("mrr", "size"), ndcg=(f"ndcg_at_{k}", "mean"), hit=("hit_at_1", "mean"))
            part.index = [f"{column}={value}" for value in part.index]
            tables.append(part.assign(model=name))
    out = pd.concat(tables).reset_index(names="segmen")
    wide = out.pivot(index="segmen", columns="model", values=["ndcg", "hit"])
    wide.columns = [f"{metric}@{k}_{model}" if metric == "ndcg" else f"hit@1_{model}" for metric, model in wide.columns]
    wide.insert(0, "n_grup", out.drop_duplicates("segmen").set_index("segmen")["n_grup"])
    return wide


def paired_bootstrap(
    df: pd.DataFrame, score: pd.Series, reference: pd.Series, split: str, informative_only: bool = True,
    n_samples: int = config.BOOTSTRAP_SAMPLES, seed: int = config.BOOTSTRAP_SEED, k: int = config.RANKING_K,
) -> pd.DataFrame:
    """selisih metrik model dikurangi pembanding dengan ci 95% dari bootstrap berpasangan per grup."""
    a, b = group_metrics(df, score, k), group_metrics(df, reference, k)
    keep = a["split"] == split
    if informative_only:
        keep &= a["informative"]
    a, b = a[keep], b.loc[a[keep].index]
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, len(a), size=(n_samples, len(a)))
    rows = {}
    for label, column in ((f"ndcg@{k}", f"ndcg_at_{k}"), ("hit@1", "hit_at_1")):
        diff = (a[column] - b[column]).to_numpy()
        boot = diff[picks].mean(axis=1)
        rows[label] = {
            "n_grup": len(a),
            "selisih": diff.mean(),
            "ci_95_bawah": np.quantile(boot, 0.025),
            "ci_95_atas": np.quantile(boot, 0.975),
            "p_selisih_le_0": (boot <= 0).mean(),
        }
    return pd.DataFrame(rows).T
