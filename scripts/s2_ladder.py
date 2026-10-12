#!/usr/bin/env python3
"""CompostMitra S2 Maturity Ladder (Harmonized Non-Leakage LOGO Protocol).

Evaluates in-situ compost maturity prediction on real Hafsa experimental batches
(data/clean/hafsa_452.csv, 46 batches, N=452).

Target Definition (Biological Maturity):
    mature = 1 if gi >= 80.0 else 0
    (Dropped target-leakage conjunctions 'cn <= 20' and 't_value < 0.60').
    Prevalence baseline = 188 / 452 = 0.4159 (41.59%).

Feature Sets:
    - sensor (Primary): ['day', 'temp', 'moist_pct', 'ph'] (in-situ non-invasive pile monitoring)
    - lab (Secondary): ['day', 'temp', 'moist_pct', 'ph', 'nh3', 'no3', 'ec', 'om'] (bench tests)
    - leakage_ref (Diagnostic): sensor + ['cn', 'tn', 'toc'] (demonstrates leakage impact)

Evaluation Protocol:
    - Leave-One-Batch-Out (LOGO) cross-validation across all 46 experimental batches.
    - Zero batch leakage across folds.
    - Cluster-bootstrap 95% confidence intervals (B=1000 resamples over the 46 batches).
    - Primary decision metrics: Balanced Accuracy (gate >= 0.70 vs 0.50 chance)
      and PR-AUC / Average Precision (vs 0.4159 prevalence baseline).

Governance:
    - Certified real Hafsa observations only (zero synthetic rows).
    - Random state 42 for reproducible bootstrap sampling.
    - Tier footnote: T1 REAL | LIT calc | D1 proxy
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
)
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
N_BOOTSTRAP = 1000
BAL_ACC_GATE = 0.70
PR_AUC_GATE = 0.50

DATA_PATH = Path("data/clean/hafsa_452.csv")
OUT_PATH = Path("models/metrics_s2.json")

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

EXCLUDED_FROM_OPERATIONAL: list[str] = ["gi", "score", "t_value", "cn", "tn", "toc"]


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load Hafsa data and assign biological maturity target (GI >= 80)."""
    df = pd.read_csv(path)
    if "source" in df.columns and (df["source"] != "hafsa_real").any():
        raise ValueError("Non-hafsa_real rows found; S2 ladder uses Hafsa real data only")
    for col in ("gi", "batch_key"):
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' missing from {path}")
    df = df.dropna(subset=["gi", "batch_key"]).reset_index(drop=True)
    df["mature"] = (df["gi"] >= 80.0).astype(int)
    return df


def build_models() -> list[tuple[str, Any]]:
    """Return model ladder: Dummy, LogReg, RF, and XGBoost (if installed)."""
    models: list[tuple[str, Any]] = [
        ("dummy", DummyClassifier(strategy="most_frequent")),
        (
            "logreg",
            make_pipeline(
                StandardScaler(),
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=5000,
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


def _predict_probabilities(estimator: Any, X: pd.DataFrame) -> np.ndarray:
    """Safely extract positive-class predicted probabilities or decision scores."""
    if hasattr(estimator, "predict_proba"):
        return np.asarray(estimator.predict_proba(X))[:, 1]
    if hasattr(estimator, "decision_function"):
        s = np.asarray(estimator.decision_function(X), dtype=float)
        return 1.0 / (1.0 + np.exp(-s))
    return np.asarray(estimator.predict(X), dtype=float)


def cluster_bootstrap_cis(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    groups: np.ndarray,
    n_boot: int = N_BOOTSTRAP,
    seed: int = RANDOM_STATE,
) -> dict[str, list[float]]:
    """Cluster-bootstrap 95% CIs by resampling batch clusters with replacement."""
    rng = np.random.RandomState(seed)
    unique_groups = np.unique(groups)
    n_groups = len(unique_groups)
    group_map = {g: np.where(groups == g)[0] for g in unique_groups}

    bal_accs: list[float] = []
    pr_aucs: list[float] = []
    accs: list[float] = []
    roc_aucs: list[float] = []
    f1s: list[float] = []

    for _ in range(n_boot):
        boot_groups = rng.choice(unique_groups, size=n_groups, replace=True)
        boot_idx = np.concatenate([group_map[g] for g in boot_groups])

        yt = y_true[boot_idx]
        yp = y_pred[boot_idx]
        ypr = y_prob[boot_idx]

        if len(np.unique(yt)) > 1:
            bal_accs.append(float(balanced_accuracy_score(yt, yp)))
            accs.append(float(accuracy_score(yt, yp)))
            f1s.append(float(f1_score(yt, yp, zero_division=0)))
            try:
                pr_aucs.append(float(average_precision_score(yt, ypr)))
            except Exception:
                pass
            try:
                roc_aucs.append(float(roc_auc_score(yt, ypr)))
            except Exception:
                pass

    def _ci(arr: list[float]) -> list[float]:
        if not arr:
            return [0.0, 0.0]
        lo, hi = np.percentile(arr, [2.5, 97.5])
        return [round(float(lo), 4), round(float(hi), 4)]

    return {
        "balanced_accuracy_95ci": _ci(bal_accs),
        "pr_auc_95ci": _ci(pr_aucs),
        "accuracy_95ci": _ci(accs),
        "roc_auc_95ci": _ci(roc_aucs),
        "f1_95ci": _ci(f1s),
    }


def evaluate_logo(
    estimator: Any,
    X: pd.DataFrame,
    y: pd.Series,
    groups: pd.Series,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray, np.ndarray]:
    """Run Leave-One-Batch-Out CV and return aggregated out-of-fold metrics."""
    logo = LeaveOneGroupOut()
    y_true_list: list[int] = []
    y_pred_list: list[int] = []
    y_prob_list: list[float] = []
    group_list: list[str] = []

    for tr_idx, te_idx in logo.split(X, y, groups):
        est = clone(estimator)
        est.fit(X.iloc[tr_idx], y.iloc[tr_idx])
        preds = est.predict(X.iloc[te_idx])
        probs = _predict_probabilities(est, X.iloc[te_idx])

        y_true_list.extend(y.iloc[te_idx].tolist())
        y_pred_list.extend(preds.tolist())
        y_prob_list.extend(probs.tolist())
        group_list.extend(groups.iloc[te_idx].tolist())

    y_true = np.asarray(y_true_list, dtype=int)
    y_pred = np.asarray(y_pred_list, dtype=int)
    y_prob = np.asarray(y_prob_list, dtype=float)
    grp_arr = np.asarray(group_list)

    acc = float(accuracy_score(y_true, y_pred))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    try:
        pr_auc = float(average_precision_score(y_true, y_prob))
    except Exception:
        pr_auc = float("nan")
    try:
        roc_auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        roc_auc = float("nan")

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    cis = cluster_bootstrap_cis(y_true, y_pred, y_prob, grp_arr)

    metrics = {
        "accuracy": round(acc, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "f1": round(f1, 4),
        "pr_auc": round(pr_auc, 4) if not np.isnan(pr_auc) else None,
        "roc_auc": round(roc_auc, 4) if not np.isnan(roc_auc) else None,
        "confusion_matrix_tn_fp_fn_tp": {
            "tn": cm[0][0],
            "fp": cm[0][1],
            "fn": cm[1][0],
            "tp": cm[1][1],
        },
        "cluster_bootstrap_95ci": cis,
        "gate_balanced_acc_ge_70": bool(bal_acc >= BAL_ACC_GATE),
        "gate_pr_auc_ge_50": bool(not np.isnan(pr_auc) and pr_auc >= PR_AUC_GATE),
    }
    return metrics, y_true, y_pred, y_prob


def run() -> tuple[dict[str, Any], list[str]]:
    """Run the complete LOGO ladder across all feature sets and models."""
    df = load_data()
    groups = df["batch_key"]
    y = df["mature"].astype(int)
    n_pos = int(y.sum())
    n_total = len(df)
    prevalence = round(float(n_pos / n_total), 4)

    metrics: dict[str, Any] = {
        "dataset": str(DATA_PATH),
        "target_definition": "mature = 1 if gi >= 80.0 else 0 (biological germination index maturity)",
        "n_rows": n_total,
        "n_batches": int(groups.nunique()),
        "n_mature": n_pos,
        "prevalence_baseline": prevalence,
        "chance_balanced_acc": 0.5000,
        "cv_protocol": "LeaveOneGroupOut (LOGO) across all 46 batches",
        "bootstrap_protocol": f"Cluster-bootstrap over 46 batches (B={N_BOOTSTRAP})",
        "gates": {
            "balanced_accuracy_gate": BAL_ACC_GATE,
            "pr_auc_gate": PR_AUC_GATE,
        },
        "excluded_from_operational": EXCLUDED_FROM_OPERATIONAL,
        "tier_footnote": "T1 REAL | LIT calc | D1 proxy",
        "feature_sets": {},
    }

    lines: list[str] = [
        f"LOGO CV Evaluation on Hafsa Real Data (46 batches, N={n_total}, Preval={prevalence:.4f})",
        f"{'Feature Set':12s} {'Model':8s} {'Acc':6s} {'BalAcc':7s} {'PR-AUC':7s} {'ROC-AUC':7s} {'BalAcc 95% CI':17s} {'Gate'}",
        "-" * 80,
    ]

    for fset_name, feats in FEATURE_SETS.items():
        X = df[feats]
        set_entry: dict[str, Any] = {"features": feats, "models": {}}

        for mname, estimator in build_models():
            res, _, _, _ = evaluate_logo(estimator, X, y, groups)
            set_entry["models"][mname] = res

            gate_str = "PASS" if (res["gate_balanced_acc_ge_70"] and res["gate_pr_auc_ge_50"]) else "FAIL"
            ci_str = f"{res['cluster_bootstrap_95ci']['balanced_accuracy_95ci']}"
            pr_str = f"{res['pr_auc']:.4f}" if res["pr_auc"] is not None else " N/A  "
            roc_str = f"{res['roc_auc']:.4f}" if res["roc_auc"] is not None else " N/A  "

            lines.append(
                f"{fset_name:12s} {mname:8s} {res['accuracy']:.4f} {res['balanced_accuracy']:.4f}  "
                f"{pr_str}  {roc_str}  {ci_str:17s} {gate_str}"
            )

        # Ridge regression reference on continuous GI
        ridge = make_pipeline(StandardScaler(), Ridge(random_state=RANDOM_STATE))
        gy = df["gi"].astype(float)
        logo = LeaveOneGroupOut()
        g_preds = np.zeros(len(gy))
        for tr_idx, te_idx in logo.split(X, gy, groups):
            r = clone(ridge)
            r.fit(X.iloc[tr_idx], gy.iloc[tr_idx])
            g_preds[te_idx] = r.predict(X.iloc[te_idx])

        rmse = float(np.sqrt(mean_squared_error(gy, g_preds)))
        mae = float(mean_absolute_error(gy, g_preds))
        set_entry["models"]["ridge_gi"] = {
            "target": "gi",
            "logo_rmse": round(rmse, 4),
            "logo_mae": round(mae, 4),
        }
        lines.append(f"{fset_name:12s} {'ridge_gi':8s} RMSE={rmse:.2f} MAE={mae:.2f}")

        metrics["feature_sets"][fset_name] = set_entry

    return metrics, lines


def main() -> int:
    parser = argparse.ArgumentParser(
        description="S2 maturity ladder with Leave-One-Batch-Out CV and cluster bootstrap."
    )
    parser.add_argument(
        "--out",
        default=str(OUT_PATH),
        help="Output JSON path (default: models/metrics_s2.json)",
    )
    args = parser.parse_args()

    try:
        metrics, lines = run()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    for line in lines:
        print(line)
    print(f"\nsaved metrics to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
