#!/usr/bin/env python3
"""CompostMitra S2 Ladder v2 (Harmonized Biological Target GI >= 80).

Hardened version of scripts/s2_ladder.py. Read-only on clean CSVs; writes only
models/metrics_s2_v2.json.

Target Definition:
    mature = 1 if gi >= 80.0 else 0 (biological germination index maturity).
    Hafsa prevalence baseline: 188 / 452 = 0.4159.

Data:
    data/clean/hafsa_452.csv (hafsa_real only, zero synthetic rows).

Splits:
    6/46-batch holdout (seed 42); StratifiedGroupKFold-5 by batch_key
    over remaining 40 batches (groups never split across folds).

Feature Sets:
    - sensor: ['day', 'temp', 'moist_pct', 'ph'] (in-situ non-invasive pile sensors)
    - lab: ['day', 'temp', 'moist_pct', 'ph', 'nh3', 'no3', 'ec', 'om'] (bench tests)
    - leakage_ref: sensor + ['cn', 'tn', 'toc'] (diagnostic reference)

Models:
    Dummy(most_frequent), LogReg(balanced), RF(balanced 200/d10/leaf5),
    XGB(depth3/reg_lambda1.0).

Metrics per set/model:
    accuracy, balanced_accuracy, F1, PR-AUC, ROC-AUC.
    Platt-sigmoid calibration (CalibratedClassifierCV cv=3) + Brier for RF,
    holdout Wilson 95% CI + confusion, 5-seed (42+i) pass rate,
    Ridge GI RMSE reference.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    mean_squared_error,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
N_HOLDOUT_BATCHES = 6
N_SPLITS = 5
BAL_ACC_GATE = 0.70
PR_AUC_GATE = 0.50
N_SEEDS = 5

DATA_PATH = Path("data/clean/hafsa_452.csv")
OUT_PATH = Path("models/metrics_s2_v2.json")

FEATURE_SETS: dict[str, list[str]] = {
    "sensor": ["day", "temp", "moist_pct", "ph"],
    "lab": ["day", "temp", "moist_pct", "ph", "nh3", "no3", "ec", "om"],
    "leakage_ref": [
        "day",
        "temp",
        "moist_pct",
        "ph",
        "cn",
        "nh3",
        "no3",
        "tn",
        "toc",
        "ec",
        "om",
    ],
}
EXCLUDED_FROM_OPERATIONAL = ["gi", "score", "t_value", "cn", "tn", "toc"]

TIER_FOOTNOTE = (
    "Tier 2 screening aid: batch-associated patterns observed in Hafsa data; "
    "not a maturity certification and not for lot release."
)
DISCLAIMER = (
    "Observational association only; field validation required before operational use."
)


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "source" in df.columns and (df["source"] != "hafsa_real").any():
        raise ValueError("Non-hafsa_real rows found; S2 uses Hafsa real data only")
    for col in ("gi", "batch_key"):
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' missing from {path}")
    df = df.dropna(subset=["gi", "batch_key"]).reset_index(drop=True)
    df["mature"] = (df["gi"] >= 80.0).astype(int)
    return df


def holdout_split(df: pd.DataFrame, seed: int = RANDOM_STATE, n: int = N_HOLDOUT_BATCHES) -> tuple[pd.DataFrame, pd.DataFrame, list[str], list[str]]:
    batches = sorted(df["batch_key"].unique().tolist())
    rng = np.random.RandomState(seed)
    holdout = sorted(rng.choice(batches, size=n, replace=False).tolist())
    train = [b for b in batches if b not in set(holdout)]
    return (
        df[df["batch_key"].isin(train)].reset_index(drop=True),
        df[df["batch_key"].isin(holdout)].reset_index(drop=True),
        train,
        holdout,
    )


def build_models() -> list[tuple[str, Any]]:
    models: list[tuple[str, Any]] = [
        ("dummy", DummyClassifier(strategy="most_frequent")),
        (
            "logreg",
            make_pipeline(
                StandardScaler(),
                LogisticRegression(
                    max_iter=5000,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ),
        (
            "rf",
            RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_leaf=5,
                class_weight="balanced",
                random_state=RANDOM_STATE,
            ),
        ),
    ]
    try:
        from xgboost import XGBClassifier  # type: ignore[import]

        models.append(
            (
                "xgb",
                XGBClassifier(
                    n_estimators=200,
                    max_depth=3,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_lambda=1.0,
                    eval_metric="logloss",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            )
        )
    except ImportError:
        print("NOTE: xgboost not installed; skipping xgb.", file=sys.stderr)
    return models


def wilson_ci(k: int, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    d = 1.0 + z * z / n
    c = p + z * z / (2.0 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4.0 * n * n))
    return [round(max(0.0, (c - m) / d), 4), round(min(1.0, (c + m) / d), 4)]


def safe_scores(y_true: Any, y_pred: Any, y_prob: Any) -> dict[str, Any]:
    m: dict[str, Any] = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_true, y_pred)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
    }
    try:
        m["roc_auc"] = round(float(roc_auc_score(y_true, y_prob)), 4)
    except Exception:
        m["roc_auc"] = None
    try:
        m["pr_auc_ap"] = round(float(average_precision_score(y_true, y_prob)), 4)
    except Exception:
        m["pr_auc_ap"] = None
    return m


def proba_of(est: Any, X: pd.DataFrame) -> np.ndarray:
    if hasattr(est, "predict_proba"):
        return np.asarray(est.predict_proba(X))[:, 1]
    if hasattr(est, "decision_function"):
        s = np.asarray(est.decision_function(X), dtype=float)
        return 1.0 / (1.0 + np.exp(-s))
    return np.asarray(est.predict(X), dtype=float)


def run() -> tuple[dict[str, Any], list[str]]:
    df = load_data()
    n_pos = int(df["mature"].sum())
    n_total = len(df)
    prevalence = round(float(n_pos / n_total), 4)
    train_df, hold_df, train_batches, hold_batches = holdout_split(df)

    metrics: dict[str, Any] = {
        "dataset": str(DATA_PATH),
        "target_definition": "mature = 1 if gi >= 80.0 else 0 (biological germination index maturity)",
        "n_rows": n_total,
        "n_batches": int(df["batch_key"].nunique()),
        "n_mature": n_pos,
        "prevalence_baseline": prevalence,
        "zero_synthetic": True,
        "cv": "StratifiedGroupKFold-5 by batch_key over 40 train batches (groups never split)",
        "holdout_batches": hold_batches,
        "train_batches": train_batches,
        "n_train_rows": int(len(train_df)),
        "n_holdout_rows": int(len(hold_df)),
        "holdout_seed": RANDOM_STATE,
        "sweep_seeds": [RANDOM_STATE + i for i in range(N_SEEDS)],
        "gates": {
            "balanced_accuracy_gate": BAL_ACC_GATE,
            "pr_auc_gate": PR_AUC_GATE,
        },
        "excluded_from_operational": EXCLUDED_FROM_OPERATIONAL,
        "tier_footnote": TIER_FOOTNOTE,
        "disclaimer": DISCLAIMER,
        "feature_sets": {},
    }
    lines = [
        f"{'set':12s} {'model':8s} {'cv_acc':7s} {'cv_bal':7s} {'cv_f1':7s} {'cv_ap':8s} "
        f"{'cv_roc':8s} {'hold_bal':8s} {'hold95CI':17s} {'Gate'} {'seeds5'}"
    ]
    y_hold = hold_df["mature"].astype(int)

    for set_name, feats in FEATURE_SETS.items():
        X_tr = train_df[feats]
        y_tr = train_df["mature"].astype(int)
        g_tr = np.asarray(train_df["batch_key"])
        X_ho = hold_df[feats]
        set_entry: dict[str, Any] = {"features": feats, "models": {}}
        skf = StratifiedGroupKFold(
            n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE
        )

        for name, est in build_models():
            fold_m: dict[str, list[float]] = {}
            for tr_i, va_i in skf.split(X_tr, y_tr, g_tr):
                e = clone(est)
                e.fit(X_tr.iloc[tr_i], y_tr.iloc[tr_i])
                s = safe_scores(
                    y_tr.iloc[va_i],
                    e.predict(X_tr.iloc[va_i]),
                    proba_of(e, X_tr.iloc[va_i]),
                )
                for k, v in s.items():
                    if v is not None:
                        fold_m.setdefault(k, []).append(v)
            cv_mean = {k: round(float(np.mean(v)), 4) for k, v in fold_m.items()}
            cv_std = {k: round(float(np.std(v)), 4) for k, v in fold_m.items()}

            fit = clone(est)
            fit.fit(X_tr, y_tr)
            hp = fit.predict(X_ho)
            hpr = proba_of(fit, X_ho)
            hold = safe_scores(y_hold, hp, hpr)
            k_hold = int((y_hold == hp).sum())
            ci = wilson_ci(k_hold, len(y_hold))
            cm = confusion_matrix(y_hold, hp, labels=[0, 1]).tolist()

            bal_pass = bool(hold["balanced_accuracy"] >= BAL_ACC_GATE)
            pr_pass = bool(hold.get("pr_auc_ap", 0.0) or 0 >= PR_AUC_GATE)
            gate_pass = bool(bal_pass and pr_pass)

            # 5-seed sweep (seeds 42+i, fresh 6-batch holdouts)
            passes = 0
            for i in range(N_SEEDS):
                tr_s, ho_s, _, _ = holdout_split(df, seed=RANDOM_STATE + i)
                e = clone(est)
                e.fit(tr_s[feats], tr_s["mature"].astype(int))
                yh = ho_s["mature"].astype(int)
                preds_s = e.predict(ho_s[feats])
                bacc = float(balanced_accuracy_score(yh, preds_s))
                passes += int(bacc >= BAL_ACC_GATE)

            entry: dict[str, Any] = {
                "cv_mean": cv_mean,
                "cv_std": cv_std,
                "holdout": hold,
                "holdout_confusion_tn_fp_fn_tp": {
                    "tn": cm[0][0],
                    "fp": cm[0][1],
                    "fn": cm[1][0],
                    "tp": cm[1][1],
                },
                "holdout_wilson95": ci,
                "gate_pass": gate_pass,
                "seed_pass_rate_5seed": round(passes / N_SEEDS, 4),
                "seed_pass_count_5seed": f"{passes}/{N_SEEDS}",
            }

            # Platt-sigmoid calibration + Brier for RF
            if name == "rf":
                try:
                    cal = CalibratedClassifierCV(clone(est), method="sigmoid", cv=3)
                    cal.fit(X_tr, y_tr)
                    cal_p = np.asarray(cal.predict_proba(X_ho))[:, 1]
                    entry["calibration"] = {
                        "method": "Platt-sigmoid CalibratedClassifierCV cv=3",
                        "brier_calibrated_holdout": round(
                            float(brier_score_loss(y_hold, cal_p)), 4
                        ),
                        "brier_uncalibrated_holdout": round(
                            float(brier_score_loss(y_hold, hpr)), 4
                        ),
                    }
                except Exception as ex:
                    entry["calibration"] = {"error": str(ex)}

            set_entry["models"][name] = entry
            pr_cv_str = (
                f"{cv_mean.get('pr_auc_ap', 0.0):.4f}"
                if cv_mean.get("pr_auc_ap") is not None
                else "  N/A "
            )
            roc_cv_str = (
                f"{cv_mean.get('roc_auc', 0.0):.4f}"
                if cv_mean.get("roc_auc") is not None
                else "  N/A "
            )
            ci_str = f"{ci}"
            lines.append(
                f"{set_name:12s} {name:8s} {cv_mean.get('accuracy', 0.0):.4f} "
                f"{cv_mean.get('balanced_accuracy', 0.0):.4f} "
                f"{cv_mean.get('f1', 0.0):.4f} "
                f"{pr_cv_str:>8s} {roc_cv_str:>8s} "
                f"{hold['balanced_accuracy']:.4f}   {ci_str:17s} {'PASS' if gate_pass else 'FAIL'} {passes}/{N_SEEDS}"
            )

        # Ridge GI RMSE reference
        ridge = make_pipeline(StandardScaler(), Ridge(random_state=RANDOM_STATE))
        gy = train_df["gi"].astype(float)
        rmses = []
        for tr_i, va_i in skf.split(X_tr, y_tr, g_tr):
            r = clone(ridge)
            r.fit(X_tr.iloc[tr_i], gy.iloc[tr_i])
            p = r.predict(X_tr.iloc[va_i])
            rmses.append(float(np.sqrt(mean_squared_error(gy.iloc[va_i], p))))
        ridge.fit(X_tr, gy)
        hp_r = ridge.predict(X_ho)
        set_entry["models"]["ridge_gi"] = {
            "target": "gi",
            "cv_rmse_mean": round(float(np.mean(rmses)), 4),
            "cv_rmse_std": round(float(np.std(rmses)), 4),
            "holdout_rmse": round(
                float(np.sqrt(mean_squared_error(hold_df["gi"].astype(float), hp_r))), 4
            ),
        }
        lines.append(
            f"{set_name:12s} ridge_gi RMSE cv={np.mean(rmses):.2f}±{np.std(rmses):.2f} "
            f"holdout={set_entry['models']['ridge_gi']['holdout_rmse']:.2f}"
        )
        metrics["feature_sets"][set_name] = set_entry

    return metrics, lines


def main() -> int:
    ap = argparse.ArgumentParser(
        description="S2 ladder v2 (harmonized GI >= 80 target)."
    )
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args()
    try:
        metrics, lines = run()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    for ln in lines:
        print(ln)
    print(f"\nsaved metrics to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
