# ARCHITECTURE v3 (LOCKED): Compost Maturity & Recipe Recommender

**Document Status:** LOCKED & AUTHORITATIVE (Sprint 1 Foundation)  
**Supersedes:** `ARCHITECTURE.md` (v1) and `ARCHITECTURE_V2.md` on stack, data governance, and ML modeling.  
**Core Stack:** Python 3.11 · Streamlit eco-premium shell (<3s offline load) · Pure deterministic blender calculator · Scikit-learn GroupKFold ML on REAL datasets (Hafsa 452 + Mullick 94 batches) · Zero React/FastAPI/SQLite/simulation rows.

---

## 1. System Architecture v3 Diagram

```
LAYER 0: REAL DATA (No Synthetic Simulation)
  • Hafsa-Kibria (452 real obs): Day, Temp, MC, pH, C/N, NH3, NO3, TN, TOC, EC, OM, GI, Score [CC-BY-4.0]
  • Mullick Kaggle (94 experimental batches, 1314 total rows): Synthetic flag preserved for ablation
  • Literature benchmarks: Cornell C/N (30:1) + UNL G2222 + Permies NPK -> data/ingredients.csv (25 items)
  • Agricultural proxies: D1 Crop Recommendation (2200 rows) + D3 Fertilizer -> data/plants.csv (15 items)
         │
         │ CSV cleaning + strict contract validation (datacheck.py --strict: NPK %, pH 0-14, Σw=1±1e-6)
         ▼
LAYER 1: BLENDER CALCULATOR (Deterministic Pure Function, Zero ML) — scripts/blender.py
  • Input: Proportions vector w (user waste items)
  • Output: {cn, n, p, k, moist_pct, ph, heuristic_grade}
  • Verified vs Cornell benchmark (dry leaves 0.60 + grass 0.40 -> CN=30.x PASS [28-32])
  • NEVER generates synthetic training rows; strictly an inference-time initial condition calculator
         │
         │ Passes blended initial conditions to inference vector {Day=21, Temp=55 defaults}
         ▼
LAYER 2: ML ON REAL DATA (In-Process Scikit-Learn Model) — train.py (Sprint 2)
  • Features: Day, Temp, MC, pH, C/N, NH3, NO3, TN, TOC, EC, OM
  • Split: GroupKFold by batch_key (prevents temporal pile leakage across train/test splits)
  • Evaluation Ladder: Majority Floor -> Ridge/LogReg Baseline -> RF (n_est=200, depth<=10) -> XGBoost
  • Kill Bar: Model ships only if beating majority baseline by >= +5 percentage points
  • Honesty Disclosures: Cross-dataset generalizability drop (10-20pp) + shuffled-y ~= 0 null harness
         │
         │ Provides maturity probability p_mature and Germination Index (GI)
         ▼
LAYER 3: RECOMMENDER & EXPLAINABILITY (Domain Rules, Zero ML)
  • Need Matcher: Cosine similarity between plant target bands and blended compost macronutrients
  • Constraints: Hard Phosphorus Cap (P-cap) penalty + pH excursion penalty (punishes outside 5.5-7.5)
  • Leave-One-Out (LOO) Sensitivity: Drop-one-scrap -> re-blend -> re-predict via pure calculator
  • Impact & Agronomic Benefits: kg/mo yield, financial savings (₹/mo), CO2e emissions reduction
         │
         │ Renders top-3 ranked recipe cards
         ▼
LAYER 4: STREAMLIT APP (Eco-Premium Garden Shell) — app.py
  • Theme Tokens: Forest #2D6A4F · Parchment #FFFBEB · Sage #EDF2E7 (no hardcoded hex colors)
  • Stepper Wizard: 1. Plants -> 2. Waste -> 3. Recipe Cards -> 4. Impact (LOO) -> 5. Benefits & Validation
  • Performance: Offline cold load <3s, session state persistence, printable summary
  • Storage: Lightweight append-only `journal.csv` (zero relational database engine)
```

---

## 2. Explicit "Killed List" (Architectural Decisions & Scope Cuts)

To maintain absolute rigor, prevent hallucinated accuracy, and preserve the ₹0 offline boundary, the following components and approaches have been **explicitly killed**:

1. **KILLED: Synthetic Row Generation & SYN Model Training**  
   - *Rationale:* Generating synthetic recipes via arithmetic perturbation creates circular reasoning where machine learning models merely learn the blender's mathematical formulas rather than true biochemical decomposition kinetics. All training is strictly confined to real laboratory compost datasets (Hafsa 452, Mullick real-subset).
2. **KILLED: SQLite & Relational Databases**  
   - *Rationale:* Embedded SQL engines introduce schema migration friction, file-locking concurrency bugs, and unnecessary overhead for local single-user execution. Replaced with lightweight, transparent append-only CSV journaling (`journal.csv`).
3. **KILLED: React / Vite Frontend Architecture**  
   - *Rationale:* Multi-tier web architectures double context overhead, require complex Node.js build toolchains, break the strict offline requirement, and violate the single-language Python ecosystem constraint.
4. **KILLED: FastAPI / REST Service Layer**  
   - *Rationale:* Running an external API daemon alongside a web frontend introduces inter-process latency and networking configuration issues. All calculations and inference run in-process within Streamlit.
5. **KILLED: Exact-Days-to-Maturity Regression ($R^2 = 0.47$)**  
   - *Rationale:* Predicting exact elapsed completion days yields an unacceptably weak regression fit ($R^2 < 0.50$) due to unmeasured ambient microclimates. Replaced by biologically grounded Germination Index ($GI \ge 80\%$) and binary maturity classification ($P(\text{mature})$).
6. **KILLED: Lab-Grade NPK Replacement Claims**  
   - *Rationale:* Domestic and decentralized compost is a living biological soil conditioner and organic matter supplement, not a standardized chemical fertilizer. Claiming lab-certified NPK precision is agronomically dishonest.
7. **KILLED: Computer Vision (CNN) & IoT Hardware Sensors**  
   - *Rationale:* Image classification from smartphone cameras and real-time probe sensors introduce excessive hardware dependency, high failure rates, and scope creep, distracting from robust mathematical blending and statistical modeling.

---

## 3. Kept and Added Architecture Elements

### Kept from Foundational Specifications
- **Deterministic Cornell Blending Math:** Pure dry-matter weighted mass balance ($C_{\text{pct}}, N_{\text{pct}}$) benchmarked against Cornell 30:1 $\pm 2$.
- **Agronomic Safety Guards:** Hard Phosphorus cap (P-cap) against mycorrhizal toxicity; strict exclusion of meat, dairy, and oils; citrus and high-carbon flags.
- **Explainability Hierarchy:** Three-tier explainability: L1 per-recipe SHAP bars, L2 per-scrap Leave-One-Out (LOO) deltas, and L3 global cross-dataset honesty tables.
- **Standardized Disclaimers:** Mandatory single-source disclaimer: `Supplement, builds soil — not fertilizer replacement`.

### Added in Architecture v3
- **REAL Sensor Training Protocol:** Grounded entirely in peer-reviewed datasets (Hafsa CC-BY-4.0, Mullick 94 batches, Zhang 848 meta-analysis).
- **GroupKFold Batch Splitting:** Prevents optimistic cross-validation leakage by clustering experimental batch rows together.
- **Model Kill Bar:** S2 ML pipeline automatically falls back to an interpretable rules engine if model accuracy does not exceed the majority baseline by $\ge 5$ percentage points.
- **Cross-Dataset Generalization Table:** Discloses the anticipated 10–20 percentage point performance reduction across different geographic feedstocks (e.g. Middle Eastern manure vs Indian kitchen scraps).

---

## 4. Parallel Workstreams & S0 Governance Contract

To enable concurrent execution without git merge conflicts, work is partitioned into four independent streams:

| Lane | Focus | Key Deliverables | Dependencies |
| :--- | :--- | :--- | :--- |
| **P1 Data** | Tables & Proxies | `ingredients.csv` (25), `plants.csv` (15), D1 centroid checks | S0 Data Contract v3.1 |
| **P2 ML** | Real Datasets | Clean datasets, GroupKFold splits, cross-dataset maps | S0 Contract + Raw Data |
| **P3 Eng** | Blender & Rules | Pure calculator `blender.py`, strict validation `datacheck.py` | S0 Math Specification |
| **P4 App** | Streamlit UI | 5-step eco-premium wizard, Plotly charts, offline runbook | S0 JSON Mock Payloads |

### S0 Freeze Rule
The interfaces defined in `DATA_CONTRACT_v3.1.md` (contract keys, function signatures, mathematical formulas, and JSON mock structures) are frozen. Any modification requires a formal contract version increment and re-running the full validation suite.

---

## 5. Architectural Risk Matrix

| Risk ID | Description | Severity | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **R1** | Geographic feedstock domain shift (Hafsa Qatar manure vs domestic kitchen scraps) | High | Transparently report cross-dataset performance drops; evaluate public-proxy holdouts; disclose `sanity, not proof` labeling. |
| **R2** | Feedstock parameter extremes violating plant tolerance | Medium | Enforce D1 centroid $\pm 30\%$ limits; trigger automatic P-cap deductions and pH penalty flags. |
| **R3** | Offline presentation failure during demonstration | High | Zero-network architecture; containerized offline bundle; pre-cached Python 3.11 wheels; exported static PDF/HTML backups. |
| **R4** | Scope creep into sensor hardware or deep learning | Medium | Strict architectural guardrails; enforce explicit killed list in pre-commit and CI gates. |

---

> **Tier Footnote:** `T1 REAL | LIT calc | D1 proxy`  
> **Model Disclaimer:** Supplement, builds soil — not fertilizer replacement. Model estimates reflect statistical associations on historical proxy data (sanity check, not proof).
