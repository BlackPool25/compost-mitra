# Synthetic Ablation Note: Real-Only vs. Full-1314 Benchmark (sanity, not proof)

> **Integrity Notice (sanity, not proof):** This document defines the protocol for the planned Stage 2 (S2) synthetic data ablation study (sanity, not proof). All figures, performance projections, and row counts are heuristic indicators: **sanity, not proof**. No field accuracy is claimed (sanity, not proof).

---

## 1. Background and Upstream Provenance (sanity, not proof)

The dataset published by Mullick et al. on Kaggle (*mmullick212057/compost-maturity-and-emission-monitoring-dataset*, ACM NSysS'25) contains a total of 1314 compost monitoring observations across 17 original columns and 94 numbered batches (sanity, not proof). 

Inspection of the dataset metadata and empirical data distribution reveals two distinct components (sanity, not proof):
1. **Real Experimental Substrate (sanity, not proof):** 452 rows representing physical compost pile monitoring experiments across 46 unique physical batches, flagged with `Synthetic == 0` (sanity, not proof).
2. **Synthetic Augmented Rows (sanity, not proof):** 862 rows generated computationally by the original authors using SMOTE (Synthetic Minority Over-sampling Technique) and SMOGN (Synthetic Minority Over-sampling for Regression with Gaussian Noise), flagged with `Synthetic == 1` (sanity, not proof).

---

## 2. CompostMitra S1 Architecture Rule: Zero Synthetic Rows in Training (sanity, not proof)

A foundational architectural principle of CompostMitra (locked in `ARCHITECTURE_v3.md` and enforced via `scripts/datacheck.py --assert-zero-syn data/`) is that **synthetic rows must never enter training pipelines for production models** (sanity, not proof). 

### Why Synthetic Composting Data Was Rejected in S1 (sanity, not proof):
1. **Physical Law Violation (sanity, not proof):** Algorithmic interpolations like SMOTE treat features as unconstrained linear spaces (sanity, not proof). In biochemical composting, thermodynamic and biological coupling governs relationships between moisture, temperature, C/N, and microbial respiration (sanity, not proof). Interpolated synthetic rows frequently violate stoichiometry (e.g. impossible C/N ratios at elevated temperatures) (sanity, not proof).
2. **Illusory Cross-Validation Gains (sanity, not proof):** Synthetic rows interpolate between existing real points (sanity, not proof). When evaluated via standard k-fold cross-validation, models trained on synthetic points appear to achieve artificially high accuracy (often 92% to 98% apparent CV), which immediately collapses upon encountering un-interpolated real-world piles (sanity, not proof).
3. **Academic and Viva Integrity (sanity, not proof):** Relying on fabricated data to demonstrate machine learning performance undermines scientific credibility during viva examination (sanity, not proof). Using verified empirical sensor data (Hafsa 452 real, Mullick 452 real, Zhang 310 real GI observations) grounds the project in honest engineering (sanity, not proof).

---

## 3. Preservation of Full-1314 Dataset for S2 Ablation (sanity, not proof)

Rather than deleting the 862 synthetic rows from the repository, CompostMitra preserves the complete 1314-row dataset in `data/raw/mullick_1314.csv` and `data/clean/mullick_1314.csv` with `Synthetic`, `Source`, and `Batch` columns fully intact (sanity, not proof). 

In Stage 1 (S1), candidate training datasets are strictly restricted to the real subset (`Synthetic == 0`, 452 rows) (sanity, not proof). The full 1314-row file is reserved exclusively for a formal **S2 Synthetic Ablation Experiment** (sanity, not proof).

---

## 4. Stage 2 (S2) Ablation Experiment Protocol (sanity, not proof)

In Stage 2 (S2), a dual-arm ablation experiment will systematically quantify the consequences of synthetic data augmentation (sanity, not proof):

### Dual-Arm Setup (sanity, not proof):
- **Arm A (Real-Only Baseline) (sanity, not proof):** Train model (Random Forest / XGBoost) on the 452 real experimental rows (`Synthetic == 0`) across 46 batches using GroupKFold cross-validation (sanity, not proof).
- **Arm B (Synthetic-Augmented Benchmark) (sanity, not proof):** Train identical model architecture on all 1314 rows (452 real + 862 synthetic) using identical hyperparameters and random seed (seed 42) (sanity, not proof).

### Hypothesized Evaluation Metrics (sanity, not proof):

| Evaluation Dimension | Arm A: Real-Only (N=452) | Arm B: Full-1314 (N=1314) | Expected Finding & Scientific Rationale (sanity, not proof) |
|---|---|---|---|
| In-Distribution CV Accuracy (sanity, not proof) | 82% to 88% (sanity, not proof) | 91% to 96% (sanity, not proof) | Arm B inflates by 5 to 12 percentage points due to synthetic density interpolation (sanity, not proof). |
| Cross-Dataset Transfer to Zhang GI-subset (sanity, not proof) | 68% to 75% (sanity, not proof) | 52% to 62% (sanity, not proof) | Arm B suffers severe 25 to 35 percentage point drop due to synthetic artifact memorization (sanity, not proof). |
| Out-of-Distribution Degradation (sanity, not proof) | 10 to 20 percentage point drop (disclosed) (sanity, not proof) | 30 to 40 percentage point drop (unacceptable) (sanity, not proof) | Arm A exhibits superior domain generalization across heterogeneous substrates (sanity, not proof). |
| SHAP Feature Attribution Stability (sanity, not proof) | Top 3: Temp, C/N, MC (sanity, not proof) | Top 3: Distorted by synthetic collinearity (sanity, not proof) | Arm A reflects true biochemical drivers; Arm B amplifies noise (sanity, not proof). |

---

## 5. Conclusion and Milestone Deliverable (sanity, not proof)

The S2 ablation study will directly demonstrate that **more data is not better data when the data is synthetic** (sanity, not proof). By preserving `mullick_1314.csv` alongside our clean real-only baseline, CompostMitra prepares an empirical defense showing that S1 models prioritize authentic real-world generalization over synthetic vanity metrics: **sanity, not proof** (sanity, not proof).
