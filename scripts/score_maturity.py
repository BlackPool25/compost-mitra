#!/usr/bin/env python3
"""Score compost maturity for in-situ pile monitoring and recipe screening.

Harmonized Biological Maturity Target:
    mature = 1 if gi >= 80.0 else 0 (germination index maturity).
    Zero target leakage from cn <= 20 or t_value < 0.60.

Architecture:
    Phase 1 (Pre-Pile Recipe Design):
        Blender recipes evaluate stoichiometric mix math (C/N, moisture, pH).
        A blend is NOT an in-situ pile reading; biological maturation requires
        time, aeration, and microbial activity. Recipe screening uses rule gates.

    Phase 2 (Active Pile Monitoring):
        During active composting, physical sensor logs (day, temp, moist_pct, ph)
        match the training distribution of the Hafsa experiment. The honest ML model
        predicts P(mature) from these 4 non-invasive features with zero leakage.

Disclaimers:
    Tier 2 screening aid: batch-associated patterns observed in Hafsa data;
    not a maturity certification and not for lot release. Observational
    association only; field validation required before operational use.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
HAFSA_CSV = REPO_ROOT / "data" / "clean" / "hafsa_452.csv"
SWEEP_IN = REPO_ROOT / "reports" / "sweep_results.json"
MATURITY_OUT = REPO_ROOT / "reports" / "maturity_scores.json"
SEED = 42
TAG = "(proxy sanity, not proof)"

# Primary honest sensor features (zero leakage)
FEATURES_SENSOR = ["day", "temp", "moist_pct", "ph"]

# Full lab feature set (optional)
FEATURES_FULL = [
    "day", "temp", "moist_pct", "ph", "cn",
    "nh3", "no3", "tn", "toc", "ec", "om",
]

# Agronomic reference defaults when converting recipe to proxy sensor
DEFAULTS: dict[str, float] = {
    "day": 21.0,      # curing-stage reference
    "temp": 32.0,     # cooling-phase reference
    "nh3": 710.44,
    "no3": 247.8881,
    "tn": 1.8371,
    "toc": 32.672,
    "ec": 1.9997,
    "om": 62.832,
}


def recipe_to_sensor(blend_profile: dict) -> dict[str, float]:
    """Map blender outputs {cn, ph, moist_pct} + reference defaults to vector.

    A blender profile is not an in-situ sensor reading; this projection is
    a pre-pile proxy sanity heuristic only.
    """
    for k in ("cn", "ph", "moist_pct"):
        if k not in blend_profile:
            raise KeyError(f"blend_profile missing required key '{k}'")
    vec = dict(DEFAULTS)
    vec["cn"] = float(blend_profile["cn"])
    vec["ph"] = float(blend_profile["ph"])
    vec["moist_pct"] = float(blend_profile["moist_pct"])
    return {f: float(vec[f]) for f in FEATURES_FULL}


def rule_gates(blend_profile: dict) -> dict[str, bool]:
    """Rule gates over blender outputs; agronomic screening aid only."""
    cn = float(blend_profile.get("cn", 0.0))
    ph = float(blend_profile.get("ph", 7.0))
    moist = float(blend_profile.get("moist_pct", 55.0))
    return {
        "cn_start_25_35": 25.0 <= cn <= 35.0,
        "cn_mature_le20": cn <= 20.0,
        "ph_6_7p5": 6.0 <= ph <= 7.5,
        "moist_50_60": 50.0 <= moist <= 60.0,
        "all_start_pass": (25.0 <= cn <= 35.0)
        and (6.0 <= ph <= 7.5)
        and (50.0 <= moist <= 60.0),
    }


def _rule_fallback_score(blend_profile: dict) -> float:
    """GI-proxy rule score used when evaluating pre-pile recipes."""
    g = rule_gates(blend_profile)
    score = 0.2
    if g["cn_mature_le20"]:
        score += 0.35
    elif g["cn_start_25_35"]:
        score += 0.20
    if g["ph_6_7p5"]:
        score += 0.20
    if g["moist_50_60"]:
        score += 0.20
    return round(max(0.0, min(1.0, score)), 4)


def _find_pkl() -> str | None:
    cands = sorted(glob.glob(str(REPO_ROOT / "models" / "*.pkl")))
    return cands[0] if cands else None


def load_or_train(feature_set: str = "sensor") -> tuple[dict, str]:
    """Load models/*.pkl when present; else train honest RF (/XGB) in memory.

    Trained strictly on certified real Hafsa data with biological target GI >= 80.
    """
    pkl = _find_pkl()
    if pkl is not None:
        import pickle

        with open(pkl, "rb") as fh:
            obj = pickle.load(fh)
        if isinstance(obj, dict):
            return obj, f"loaded:{Path(pkl).name}"
        return {"rf": obj}, f"loaded:{Path(pkl).name}"

    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier

    df = pd.read_csv(HAFSA_CSV)
    df = df.dropna(subset=["gi"]).reset_index(drop=True)
    y = (df["gi"] >= 80.0).astype(int)

    feats = FEATURES_SENSOR if feature_set == "sensor" else FEATURES_FULL
    X = df[feats]

    models: dict = {}
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=SEED,
    )
    rf.fit(X, y)
    models["rf"] = rf

    try:
        from xgboost import XGBClassifier

        xgb = XGBClassifier(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=1.0,
            eval_metric="logloss",
            random_state=SEED,
            n_jobs=-1,
        )
        xgb.fit(X, y)
        models["xgb"] = xgb
    except ImportError:
        pass

    return models, f"trained-in-memory:GI>=80:{feature_set}:seed42"


def score_pile_monitoring(
    day: float,
    temp: float,
    moist_pct: float,
    ph: float,
    models: dict | None = None,
) -> dict[str, Any]:
    """Score an active composting pile from in-situ physical readings.

    Features passed: day, temp, moist_pct, ph (zero leakage).
    """
    if models is None:
        try:
            models, _ = load_or_train(feature_set="sensor")
        except ImportError:
            models = None

    sensor_dict = {
        "day": float(day),
        "temp": float(temp),
        "moist_pct": float(moist_pct),
        "ph": float(ph),
    }

    out: dict[str, Any] = {
        "inputs": sensor_dict,
        "mode": "Phase 2 Active Pile Monitoring",
        "target": "Biological maturity (GI >= 80.0)",
        "disclaimer": (
            f"Tier 2 screening aid {TAG}; in-situ sensor readings. "
            f"Observational association on Hafsa data."
        ),
    }

    if models:
        import pandas as pd

        X = pd.DataFrame([sensor_dict], columns=FEATURES_SENSOR)
        for name, est in sorted(models.items()):
            try:
                p = float(est.predict_proba(X)[0, 1])
            except Exception:
                p = float(est.predict(X)[0])
            out[f"p_mature_{name}"] = round(p, 4)
            out[f"p_mature_{name}_note"] = TAG
        prefs = [n for n in ("xgb", "rf") if f"p_mature_{n}" in out]
        out["p_mature"] = out[f"p_mature_{prefs[0]}"] if prefs else None
        out["p_mature_note"] = TAG
    else:
        # Simple heuristic fallback if sklearn unavailable
        is_late = day >= 25.0
        is_cool = temp <= 35.0
        is_neutral = 6.5 <= ph <= 8.0
        p_est = 0.2 + (0.3 if is_late else 0.0) + (0.3 if is_cool else 0.0) + (0.2 if is_neutral else 0.0)
        out["p_mature"] = round(p_est, 4)
        out["p_mature_note"] = f"heuristic fallback {TAG}"

    return out


def score_blend(
    blend_profile: dict,
    models: dict | None = None,
    source: str = "rule-fallback",
) -> dict[str, Any]:
    """Score one blender profile; pre-pile recipe screening."""
    vec = recipe_to_sensor(blend_profile)
    gates = rule_gates(blend_profile)
    out: dict[str, Any] = {
        "blend": {k: blend_profile.get(k) for k in ("cn", "ph", "moist_pct")},
        "sensor_vector": vec,
        "gates": gates,
        "model_source": source,
        "disclaimer": (
            f"Tier 2 screening aid {TAG}; pre-pile recipe profile is not "
            f"an in-situ sensor reading. Observational association only."
        ),
    }
    if models:
        import pandas as pd

        # Check if model was trained on FEATURES_SENSOR or FEATURES_FULL
        first_est = next(iter(models.values()))
        feats = getattr(first_est, "feature_names_in_", None)
        if feats is None or list(feats) == FEATURES_SENSOR:
            X = pd.DataFrame([vec], columns=FEATURES_SENSOR)
        else:
            X = pd.DataFrame([vec], columns=FEATURES_FULL)

        for name, est in sorted(models.items()):
            try:
                p = float(est.predict_proba(X)[0, 1])
            except Exception:
                p = float(est.predict(X)[0])
            out[f"p_mature_{name}"] = round(p, 4)
            out[f"p_mature_{name}_note"] = TAG
        prefs = [n for n in ("xgb", "rf") if f"p_mature_{n}" in out]
        out["p_mature"] = out[f"p_mature_{prefs[0]}"] if prefs else None
        out["p_mature_note"] = TAG
    else:
        out["p_mature"] = _rule_fallback_score(blend_profile)
        out["p_mature_note"] = f"rule GI-proxy {TAG}"
    return out


def _blends_from_data(data: Any) -> list[dict]:
    """Flatten sweep JSON (list / results / runs->top3) to blend profiles."""
    blends: list[dict] = []

    def _pick(r: dict) -> dict | None:
        if all(k in r for k in ("cn", "ph", "moist_pct")):
            return r
        for key in ("compost", "blend", "recipe_blend"):
            inner = r.get(key, {})
            if isinstance(inner, dict) and all(
                k in inner for k in ("cn", "ph", "moist_pct")
            ):
                return {**r, **inner}
        return None

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                p = _pick(item)
                if p is not None:
                    blends.append(p)
    elif isinstance(data, dict):
        if "results" in data and isinstance(data["results"], list):
            for item in data["results"]:
                if isinstance(item, dict):
                    p = _pick(item)
                    if p is not None:
                        blends.append(p)
        elif "runs" in data and isinstance(data["runs"], list):
            for run in data["runs"]:
                if isinstance(run, dict):
                    for r in run.get("top3", []):
                        if isinstance(r, dict):
                            p = _pick(r)
                            if p is not None:
                                blends.append(p)
    return blends


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score compost recipes or pile readings for maturity."
    )
    parser.add_argument(
        "--in",
        dest="in_path",
        default=str(SWEEP_IN),
        help="Input sweep results JSON",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        default=str(MATURITY_OUT),
        help="Output JSON path",
    )
    parser.add_argument(
        "--pile",
        action="store_true",
        help="Run sample in-situ pile monitoring calculation",
    )
    args = parser.parse_args()

    if args.pile:
        res = score_pile_monitoring(day=28.0, temp=30.0, moist_pct=52.0, ph=7.2)
        print(json.dumps(res, indent=2))
        return 0

    in_file = Path(args.in_path)
    if not in_file.exists():
        print(f"Warning: {in_file} does not exist; running sample blend test.")
        sample = {"cn": 28.0, "ph": 6.8, "moist_pct": 55.0}
        scored = score_blend(sample)
        print(json.dumps(scored, indent=2))
        return 0

    with in_file.open("r", encoding="utf-8") as fh:
        raw_data = json.load(fh)

    blends = _blends_from_data(raw_data)
    try:
        models, source = load_or_train(feature_set="sensor")
    except ImportError:
        models, source = None, "rule-fallback:no-sklearn"

    scored_records = [score_blend(b, models=models, source=source) for b in blends]
    out_file = Path(args.out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as fh:
        json.dump(
            {
                "disclaimer": (
                    "Tier 2 screening aid (proxy sanity, not proof); "
                    "observational association only."
                ),
                "n_scored": len(scored_records),
                "model_source": source,
                "scores": scored_records,
            },
            fh,
            indent=2,
        )

    print(f"Scored {len(scored_records)} blend records -> {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
