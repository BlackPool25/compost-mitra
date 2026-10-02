# CompostMitra

**CompostMitra** is an offline-first, AI-assisted domestic and community composting assistant designed for decentralized organic waste valorization, balanced recipe optimization, and biological maturity prediction.

---

## ⚡ 60-Second Demo Quickstart

Follow this 60-second path to launch and evaluate CompostMitra locally:

### 1. Setup Virtual Environment (Dual OS Commands)

**On Linux / macOS:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**On Windows (PowerShell / Command Prompt):**
```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Verification Suite & Blender Check

```bash
# Verify the pure deterministic Cornell 30:1 blending benchmark (28-32 range)
python scripts/blender.py --cornell-check

# Run contract verification on ingredients, plants, and clean datasets
python scripts/datacheck.py --strict data/clean/*.csv data/ingredients.csv data/plants.csv

# Run automated test suite
python -m pytest tests/ -q
```

### 3. Launch the Streamlit Interface

```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`. Cold start loads in under 3.0 seconds offline.

### 4. Interactive 60-Second Walkthrough in UI
1. **Step 1 (Plants):** Select target garden crops (e.g. Tomato, Rose, Spinach) and pot scale.
2. **Step 2 (Waste):** Enter household kitchen scraps (Vegetable peels, Coffee grounds, Banana peels, Dry leaves).
3. **Step 3 (Recipe):** Review top-3 ranked recipes with C/N balance, NPK delivery estimates, and maturity score.
4. **Step 4 (Impact):** Inspect Leave-One-Out (LOO) sensitivity bars showing the marginal contribution of each feedstock.
5. **Step 5 (Benefits):** Review monthly compost yield (kg/mo), economic savings (₹/mo), and carbon offset metrics.

---

## 📁 Repository Structure & Workspace Paths

All paths in the project are workspace-relative:

```
├── app.py                      # Eco-premium Streamlit user interface (<3s cold start)
├── constants.py                # Single-source of truth for disclaimers and tier footnotes
├── tokens.py                   # Design system color tokens (#2D6A4F, #FFFBEB, #EDF2E7)
├── style.css                   # Custom UI styling and typography
├── data/
│   ├── clean/                  # Verified real datasets (Hafsa 452, Mullick 1314, Zhang 848)
│   ├── ingredients.csv         # 25 sourced organic feedstocks (NPK, C/N, moisture, delta-pH)
│   ├── plants.csv              # 15 plant target nutrient bands with Phosphorus caps (P-cap)
│   └── schema_map.csv          # Column cross-walk mapping across real datasets
├── docs/
│   ├── ARCH_LOCKED.md          # Architecture v3 specification and explicit killed list
│   ├── DATA_CONTRACT_v3.1.md   # S0 frozen data contracts, key mappings, and math basis
│   ├── ADRS.md                 # Architecture Decision Records index (ADR-001 through ADR-011)
│   └── adrs/                   # Individual ADR markdown documents
├── mock/                       # Canonical JSON response fixtures for offline development
├── scripts/
│   ├── blender.py              # Pure deterministic mass-balance blender (Cornell 30:1 tested)
│   ├── datacheck.py            # Strict schema, range, and zero-synthetic row validator
│   ├── check_keys.py           # Contract key case and schema validator
│   ├── check_tier_footnotes.py # Verifies tier footnotes across docs and figures
│   └── check_holdout_labels.py # Verifies sanity/proxy labeling on holdout metrics
├── tests/
│   ├── test_blend.py           # Unit tests for blender calculator and edge fixtures
│   └── test_wording.py         # Guardrail test enforcing absence of prohibited causal claims
└── RUNBOOK.md                  # Comprehensive offline operations guide and M1 gate checklist
```

---

## 🏛️ Architectural Guardrails

- **Zero Synthetic Training Rows:** All machine learning is strictly anchored to real, peer-reviewed laboratory datasets. Blender math operates purely as a deterministic calculator.
- **Single-Source Disclaimers:** Every card and report payload carries the canonical agronomic disclaimer from `constants.py`:  
  *`Supplement, builds soil — not fertilizer replacement`*.
- **Wording Discipline:** Causal claims are prohibited across all source code and documentation; claims are framed as statistical associations or heuristic guidelines.
- **Holdout Reporting Rule:** Every holdout evaluation metric is tagged adjacent to the number with `(sanity check, not proof)` or `(proxy sanity)`.

---

> **Tier Footnote:** `T1 REAL | LIT calc | D1 proxy`  
> **Model Disclaimer:** Supplement, builds soil — not fertilizer replacement. Model estimates reflect statistical associations on historical proxy data (sanity check, not proof).
