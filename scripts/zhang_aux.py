#!/usr/bin/env python3
"""Zhang OOD Generalization Evaluation (Harmonized GI >= 80 Target).

Evaluates cross-dataset generalization of models trained on real Hafsa data
(data/clean/hafsa_452.csv) and tested out-of-distribution on Zhang et al.
(data/clean/zhang_848.csv, N=310 clean rows).

Target Definition:
    mature = 1 if gi >= 80.0 else 0 (harmonized biological maturity).
    Hafsa prevalence: 188 / 452 = 41.59%
    Zhang prevalence: 241 / 310 = 77.74% (mature-skewed late-stage sample)

Feature Sets Evaluated:
    - shared_sensor: ['day', 'moist_pct', 'ph'] (honest in-situ features)
    - shared_with_cn: ['day', 'moist_pct', 'ph', 'cn'] (ablation showing cn impact)

Outputs:
    Writes summary to docs/holdout/zhang_aux.json.
    Tier Footnote: T1 REAL | LIT calc | D1 proxy
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 42
TAG = "(proxy sanity, not proof)"
ROOT = Path(__file__).resolve().parents[1]
HAFSA_CSV = ROOT / "data" / "clean" / "hafsa_452.csv"
ZHANG_CSV = ROOT / "data" / "clean" / "zhang_848.csv"
OUT_JSON = ROOT / "docs" / "holdout" / "zhang_aux.json"


def main() -> None:
    np.random.seed(SEED)
    hafsa = pd.read_csv(HAFSA_CSV)
    zhang = pd.read_csv(ZHANG_CSV)

    # Harmonized biological maturity target
    y_hafsa_cls = (hafsa["gi"] >= 80.0).astype(int)
    y_zhang_cls = (zhang["gi"] >= 80.0).astype(int)

    # Continuous GI targets
    y_hafsa_reg = hafsa["gi"].to_numpy(dtype=float)
    y_zhang_reg = zhang["gi"].to_numpy(dtype=float)

    # 1. Continuous GI Ridge regression on 4 shared keys
    shared_4 = ["day", "ph", "cn", "moist_pct"]
    reg = make_pipeline(StandardScaler(), Ridge(random_state=SEED))
    reg.fit(hafsa[shared_4], y_hafsa_reg)
    pred_reg = reg.predict(zhang[shared_4])

    rmse = float(np.sqrt(mean_squared_error(y_zhang_reg, pred_reg)))
    mae = float(mean_absolute_error(y_zhang_reg, pred_reg))
    r2 = float(r2_score(y_zhang_reg, pred_reg))

    hafsa_med_gi = float(hafsa["gi"].median())
    zhang_med_gi = float(zhang["gi"].median())

    # 2. Classification Transfer across feature sets
    cls_results: dict[str, dict] = {}

    for fset_name, feats in [
        ("shared_sensor", ["day", "moist_pct", "ph"]),
        ("shared_with_cn", ["day", "moist_pct", "ph", "cn"]),
    ]:
        fset_dict: dict = {}

        # Logistic Regression
        lr = make_pipeline(
            StandardScaler(),
            LogisticRegression(class_weight="balanced", random_state=SEED),
        )
        lr.fit(hafsa[feats], y_hafsa_cls)
        p_lr = lr.predict(zhang[feats])
        pr_lr = lr.predict_proba(zhang[feats])[:, 1]
        cm_lr = confusion_matrix(y_zhang_cls, p_lr, labels=[0, 1]).tolist()

        fset_dict["logreg"] = {
            "accuracy": round(float(accuracy_score(y_zhang_cls, p_lr)), 4),
            "balanced_accuracy": round(
                float(balanced_accuracy_score(y_zhang_cls, p_lr)), 4
            ),
            "pr_auc": round(float(average_precision_score(y_zhang_cls, pr_lr)), 4),
            "roc_auc": round(float(roc_auc_score(y_zhang_cls, pr_lr)), 4),
            "confusion_tn_fp_fn_tp": {
                "tn": cm_lr[0][0],
                "fp": cm_lr[0][1],
                "fn": cm_lr[1][0],
                "tp": cm_lr[1][1],
            },
        }

        # Random Forest
        rf = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=SEED,
        )
        rf.fit(hafsa[feats], y_hafsa_cls)
        p_rf = rf.predict(zhang[feats])
        pr_rf = rf.predict_proba(zhang[feats])[:, 1]
        cm_rf = confusion_matrix(y_zhang_cls, p_rf, labels=[0, 1]).tolist()

        fset_dict["rf"] = {
            "accuracy": round(float(accuracy_score(y_zhang_cls, p_rf)), 4),
            "balanced_accuracy": round(
                float(balanced_accuracy_score(y_zhang_cls, p_rf)), 4
            ),
            "pr_auc": round(float(average_precision_score(y_zhang_cls, pr_rf)), 4),
            "roc_auc": round(float(roc_auc_score(y_zhang_cls, pr_rf)), 4),
            "confusion_tn_fp_fn_tp": {
                "tn": cm_rf[0][0],
                "fp": cm_rf[0][1],
                "fn": cm_rf[1][0],
                "tp": cm_rf[1][1],
            },
        }

        cls_results[fset_name] = fset_dict

    payload = {
        "disclaimer": (
            "Cross-dataset OOD transfer check for context only (proxy sanity, not proof). "
            "Zhang et al. represents an external mature-skewed distribution under distinct operational protocols."
        ),
        "tier_footnote": "T1 REAL | LIT calc | D1 proxy",
        "sample_sizes": {
            "n_train_hafsa": len(hafsa),
            "n_test_zhang": len(zhang),
            "hafsa_positive_prevalence": round(float(y_hafsa_cls.mean()), 4),
            "zhang_positive_prevalence": round(float(y_zhang_cls.mean()), 4),
        },
        "covariate_shift": {
            "day": {
                "hafsa_median": float(hafsa["day"].median()),
                "zhang_median": float(zhang["day"].median()),
                "note": "Zhang samples strictly mature/late stage (day min=20, median=45 vs Hafsa median=12).",
            },
            "moist_pct": {
                "hafsa_mean": round(float(hafsa["moist_pct"].mean()), 2),
                "zhang_mean": round(float(zhang["moist_pct"].mean()), 2),
                "note": "Zhang composting runs at higher forced aeration moisture (63.3% vs Hafsa 49.1%).",
            },
            "gi": {
                "hafsa_median": round(hafsa_med_gi, 2),
                "zhang_median": round(zhang_med_gi, 2),
                "median_gap": round(zhang_med_gi - hafsa_med_gi, 2),
            },
        },
        "regression_ridge_gi": {
            "rmse": round(rmse, 4),
            "mae": round(mae, 4),
            "r2": round(r2, 4),
            "shared_keys": shared_4,
        },
        "classification_transfer_gi80": cls_results,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print("=== ZHANG TRANSFER RESULTS (Harmonized GI >= 80) ===")
    print(f"Regression GI: RMSE={rmse:.2f}, MAE={mae:.2f}, R2={r2:.4f}")
    for fset, models in cls_results.items():
        print(f"\nFeature set: {fset}")
        for mname, m in models.items():
            print(
                f"  {mname:8s} | Acc={m['accuracy']:.4f} | BalAcc={m['balanced_accuracy']:.4f} | "
                f"PR-AUC={m['pr_auc']:.4f} | ROC-AUC={m['roc_auc']:.4f}"
            )
    print(f"\nSaved results to {OUT_JSON}")


if __name__ == "__main__":
    main()
