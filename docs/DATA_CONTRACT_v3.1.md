# DATA CONTRACT v3.1 (frozen S0 freeze — change = version bump + full rerun)

## 1. Governance & Freeze Rules
- **Status:** FROZEN (v3.1)
- **Random Seed:** 42
- **Inference Defaults:** `day = 21`, `temp = 55.0` (frozen here for model feature vector completion)
- **Weight Normalization Rule:** $\Sigma w = 1 \pm 1\times 10^{-6}$. An error must be raised if weights do not sum to 1 within this tolerance; never normalize silently.
- **Key Casing Policy:** Strict `lower_snake` case across all JSON responses, feature vectors, and mock fixtures. CamelCase, PascalCase, or uppercase column abbreviations (e.g. `CN`, `pH`, `MC`) are strictly forbidden in serialization payloads and API contracts.

---

## 2. Explicit Key & Column Mapping Table

| Contract Key | REAL Source Col | Basis / Constraints | Example |
| :--- | :--- | :--- | :--- |
| `cn` | `C/N dry ratio` | unitless dry-weight ratio | `28.5` |
| `ph` | `pH` | 0–14 hard range; warning outside 5.5–7.5 | `6.8` |
| `moist_pct` | `MC` | 0–100 percentage ONLY (never 0–1 fraction) | `55.0` |
| `temp` | `Temp` | °C (compost internal temperature) | `55.0` |
| `day` | `Day` | days elapsed | `21` |
| `nh3` | `NH3` | mg/kg | `120.0` |
| `no3` | `NO3` | mg/kg | `350.0` |
| `tn` | `TN` | % dry-weight | `1.8` |
| `toc` | `TOC` | % dry-weight | `42.0` |
| `ec` | `EC` | mS/cm | `2.4` |
| `om` | `OM` | % organic matter | `65.0` |

---

## 3. Mathematical Basis & Formulations

### 3.1 C, N Dry-Weight Basis
All elemental ratios and mass fractions are computed on a dry-matter basis:
- Dry mass conversion:
  $$\text{dry} = \text{wet} \times \left(1 - \frac{\text{moist\_pct}}{100}\right)$$
- Dry-weight percentages:
  $$C_{\text{pct}} = \frac{C}{\text{dry}} \times 100$$
  $$N_{\text{pct}} = \frac{N}{\text{dry}} \times 100$$
- Blended C/N ratio:
  $$CN = \frac{\sum w_i \cdot C_{\text{pct}, i}}{\sum w_i \cdot N_{\text{pct}, i}} \quad (\text{dry-basis only})$$

### 3.2 pH Blending Formula (`HEURISTIC-linear-approx`)
$$\text{ph} = 7.0 + \sum w_i \cdot \text{dph}_i \times 0.35$$
> **Chemistry Note (`HEURISTIC-linear-approx`):** Compost acidification, organic acid generation, and microbial buffering are nonlinear biological and chemical phenomena. The linear weighted delta-pH formulation is a heuristic approximation intended strictly for initial feedstock blending guidance, not an equilibrium geochemical model.

---

## 4. Function Signatures & Data Interfaces

- `blend(w: dict[id, float]) -> {"cn": float, "n": float, "p": float, "k": float, "moist_pct": float, "ph": float, "heuristic_grade": str}`
  - Preconditions: $\sum w_i = 1 \pm 10^{-6}$.
  - Purity: Pure function; no disk or network I/O.
  - Return: All keys strictly `lower_snake`.

- `predict(vec: dict) -> {"p_mature": float, "gi": float, "cn_pred": float, "shap": dict[str, float], "conf": float}`
  - Input vector keys: `cn`, `ph`, `moist_pct`, `temp`, `day`, `nh3`, `no3`, `tn`, `toc`, `ec`, `om`.
  - Missing inference inputs default to `day = 21`, `temp = 55.0`.
  - SHAP explanation map keys must match the contract keys.

- `match(need: dict, compost: dict) -> float`
  - Cosine matching score between 0.0 and 1.0.

- `optimize(needs: dict, waste: dict, k: int = 3) -> list[dict]`
  - Produces top-k recipe recommendations with phosphorus cap (P-cap).

- `loo(recipe: dict) -> list[tuple[str, float]]`
  - Leave-One-Out ingredient sensitivity analysis via re-blend and re-predict.

- `benefits(recipe: dict) -> {"kg_mo": float, "rs_mo": float, "co2e": float}`
  - Monthly output mass estimate, economic savings, and carbon offset estimation.

- `check(df: pd.DataFrame) -> bool`
  - Validates schemas, non-null constraints, ranges, and types on every CSV load.

---

## 5. File Schemas & Storage Targets

- **`data/ingredients.csv` (25 items):**
  `id,name,group,C,N,N_pct,P_pct,K_pct,moist_pct,dph,source`
  - `group`: `Green` | `Brown`
  - Ranges: NPK 0–10, C/N 4–150, dph −3.0..+3.0.
  - Every cell sourced from validated literature (Cornell, UNL, peer-reviewed studies).

- **`data/plants.csv` (15 items):**
  `id,name,family,N_lo,N_hi,P_lo,P_hi,K_lo,K_hi,pH_lo,pH_hi,stage_note,P_cap,source`
  - Target ranges for macronutrients and pH.
  - Stage notes mandatory for fruiting and vegetative stages.

- **`data/clean/*.csv`:**
  - `hafsa_452.csv`: Real compost experiments ($N=452$).
  - `mullick_1314.csv`: Extended experimental compost observations ($N=1314$, with `Synthetic` flag preserved for ablation).
  - `zhang_848.csv`: Literature dataset ($N=848$, filtered for GI maturity indicators).
  - Every clean file contains standard mapped contract keys, `source`, and `batch_key`.

- **`mock/recipe_response.json`:**
  Canonical mock response for blender output.

- **`mock/predict_response.json`:**
  Canonical mock response for model prediction output.

- **`metrics.json`:**
  `{"cv_acc_mean": float, "std": float, "oob": float, "shuffled_y": float, "maturity_baseline": float, "cross_dataset": dict, "seed": 42, "sklearn_ver": str}`

---

## 6. Gates & Verification Checks
- **M1 Gate:** Blender Cornell 30:1 test ($\pm 2$), `check_keys.py` green, `datacheck.py --strict` green.
- **M2 Gate:** Group-5-fold accuracy beats majority baseline by +5pp; shuffled-y control $\approx 0$; cross-dataset table evaluated.
- **M3 Gate:** End-to-end tomato scenario verification; non-zero LOO delta; tier footnotes on UI cards.

---

> **Tier Footnote:** `T1 REAL | LIT calc | D1 proxy`  
> **Model Disclaimer:** Supplement, builds soil — not fertilizer replacement. Model estimates reflect statistical associations on historical proxy data (sanity check, not proof).

