# Architecture Decision Records (ADRs)

This document records the architectural and engineering decisions governing **CompostMitra** (Sprint 1 Foundation).

| ADR ID | Decision Title | Status | Scope / Impact |
| :--- | :--- | :--- | :--- |
| **ADR-001** | Streamlit Prototype over React + FastAPI | Accepted | Shell Architecture, zero-latency execution, offline <3s |
| **ADR-002** | Random Forest Model Ladder Parked to Sprint 2 | Accepted | ML Modeling, S1 focus on clean data and deterministic blender |
| **ADR-003** | Sprint 2 Model Kill Bar (+5pp above Majority Baseline) | Accepted | ML Quality Gate, fallback to transparent rules table |
| **ADR-004** | Pure Deterministic Blender for Leave-One-Out (LOO) | Accepted | Explainability, anti-circular logic, zero simulation rows |
| **ADR-005** | Retention of Synthetic Flag in Upstream Datasets | Accepted | Data Hygiene, rigorous S2 ablation without data leakage |
| **ADR-006** | Phosphorus Safety Cap (P-cap) Constraint | Accepted | Agronomic Rule, protects mycorrhizae from nutrient lockout |
| **ADR-007** | Mandatory Supplement Disclaimer Text | Accepted | Agronomic Honesty, avoids misleading fertilizer replacement claims |
| **ADR-008** | Standardization on Python 3.11 over 3.10 | Accepted | Runtime & Toolchain, 10–20% speedups, stable cross-platform wheels |
| **ADR-009** | Reversal of Docker-Deleted Clause for Reproducible CI | Accepted | DevOps & Build, automated headless testing and SBOM generation |
| **ADR-010** | Public-Proxy Holdouts in Place of Physical Canteen Survey | Accepted | Validation Strategy, transparent cross-dataset generalization drop |
| **ADR-011** | XGBoost and SHAP Interpretability Parked to Sprint 2 | Accepted | ML Modeling, S1 uses mock payloads and pure-calculator sensitivity |

---

## ADR-001: Streamlit Prototype over React + FastAPI
- **Status:** Accepted
- **Context:** An initial proposal explored a multi-tier architecture featuring a React (Vite) frontend, a FastAPI REST service, and a PostgreSQL database. However, this introduced Node.js build dependencies, inter-process network configuration overhead, and startup latencies exceeding 8 seconds.
- **Decision:** Build the user-facing interface entirely in Streamlit with an eco-premium CSS theme (`#2D6A4F`, `#FFFBEB`, `#EDF2E7`) and Plotly visual components.
- **Consequences:** Eliminates external network calls, runs completely offline, achieves cold starts under 3.0 seconds, and confines the codebase strictly to Python 3.11.

---

## ADR-002: Random Forest Model Ladder Parked to Sprint 2
- **Status:** Accepted
- **Context:** Training predictive models on unverified raw data risks embedding invalid assumptions into the codebase before column schemas, units, and ranges are stabilized.
- **Decision:** Formal model training (Dummy floor → Ridge baseline → Random Forest 200 trees → XGBoost) is explicitly parked to Sprint 2. Sprint 1 concentrates exclusively on data hygiene, contract freezing, pure blender math, and UI shell integration against mock fixtures.
- **Consequences:** Guarantees that when models are trained in S2, they operate on certified, peer-reviewed, leak-free datasets.

---

## ADR-003: Sprint 2 Model Kill Bar (+5pp above Majority Baseline)
- **Status:** Accepted
- **Context:** Machine learning models for decentralized composting often suffer from domain shift across feedstocks, leading to complex models that fail to outperform trivial heuristic baselines.
- **Decision:** Enforce a strict programmatic kill bar for Sprint 2: the trained Random Forest / XGBoost model must beat the majority class baseline accuracy by at least +5.0 percentage points in GroupKFold cross-validation (proxy sanity check, not proof). If the model fails this threshold, the application automatically defaults to an interpretable rule-based heuristic matrix.
- **Consequences:** Prevents shipping black-box models that offer no real-world predictive advantage.

---

## ADR-004: Pure Deterministic Blender for Leave-One-Out (LOO)
- **Status:** Accepted
- **Context:** Prior synthetic generation pipelines trained models on artificially simulated mixtures, creating circular reasoning where models simply learned their own generative equations.
- **Decision:** Implement `blender.py` as a strictly pure mathematical function (`blend(w) -> dict`) based on dry-matter mass balances and verified against the Cornell 30:1 C/N benchmark (expected 28.0–32.0 range). Leave-One-Out sensitivity is computed by dropping each scrap, re-blending, and evaluating the shift.
- **Consequences:** The blender never generates synthetic training rows; it operates strictly as an inference calculator.

---

## ADR-005: Retention of Synthetic Flag in Upstream Datasets
- **Status:** Accepted
- **Context:** The upstream Mullick dataset contains 1314 total observations, of which 452 are physical laboratory observations and the remainder are generated via SMOTE/SMOGN techniques.
- **Decision:** Retain the raw `Synthetic`, `Source`, and `Batch` columns in `data/clean/mullick_1314.csv`. S1 training datasets exclude all synthetic entries, but preserving the flag enables a formal ablation study in S2 comparing real-only vs synthetic-augmented models.
- **Consequences:** Guarantees zero synthetic leakage in S1 while preserving scientific reproducibility for S2 ablation.

---

## ADR-006: Phosphorus Safety Cap (P-cap) Constraint
- **Status:** Accepted
- **Context:** Heavy application of high-phosphorus organic wastes (e.g., concentrated animal manures, bone meal) can elevate soil phosphorus beyond plant absorption limits, inhibiting mycorrhizal fungi and inducing iron/zinc chlorosis.
- **Decision:** Enforce an agronomic Phosphorus Cap (`P_cap`) in `data/plants.csv`. When a blended compost mixture exceeds the crop's threshold, the recipe recommender applies an automatic penalty to the recipe matching score.
- **Consequences:** Protects target plants against nutrient toxicity and prevents environmental runoff.

---

## ADR-007: Mandatory Supplement Disclaimer Text
- **Status:** Accepted
- **Context:** Overstating the chemical potency of domestic compost misleads urban gardeners into treating unfinished or low-potency compost as a direct replacement for balanced fertilizers.
- **Decision:** Centralize and mandate the canonical disclaimer: `Supplement, builds soil — not fertilizer replacement` across all user interface cards, export payloads, and documentation. Single-sourced from `constants.py`.
- **Consequences:** Establishes agronomic clarity and compliance with agricultural extension guidelines.

---

## ADR-008: Standardization on Python 3.11 over 3.10
- **Status:** Accepted
- **Context:** Earlier charter documents mentioned Python 3.10, but Python 3.11 introduces significant performance optimizations in the CPython interpreter (Specializing Adaptive Interpreter) and enhanced tracebacks.
- **Decision:** Standardize all development, virtual environments, Docker images, and CI pipelines on Python 3.11 (`.python-version` pinned to 3.11). Support dual invocation commands: `py -3.11` (Windows) and `python3.11` (Linux/macOS).
- **Consequences:** 10–20% faster runtime execution for data validation and clean cross-platform dependency wheel compatibility.

---

## ADR-009: Reversal of Docker-Deleted Clause for Reproducible CI
- **Status:** Accepted
- **Context:** An earlier ticket (PRISSUE-48) suggested removing Docker configuration to simplify local file management. However, this degraded CI auditability and prevented automated verification of zero-network offline execution.
- **Decision:** Reverse the deletion clause and maintain a lightweight `Dockerfile` (`python:3.11-slim`), `docker-compose.yml`, and GitHub Actions workflow. The container enforces an image budget under 800MB and generates CycloneDX Software Bills of Materials (SBOM).
- **Consequences:** Ensures fully reproducible, isolated, and verifiable builds across diverse developer environments.

---

## ADR-010: Public-Proxy Holdouts in Place of Physical Canteen Survey
- **Status:** Accepted
- **Context:** Initial project plans called for physical weighing and chemical analysis of 7-day dining hall/canteen waste (PRISSUE-52). Campus administrative and access limitations precluded completion during Sprint 1.
- **Decision:** Park the physical survey and establish public-proxy holdouts using peer-reviewed datasets: Hafsa-real (452 obs) evaluated against Mullick-real (452 obs) and Zhang (848 obs). The anticipated 10.0–20.0 percentage point generalizability drop is explicitly disclosed (sanity check, not proof).
- **Consequences:** Unblocks S1 validation with open, reproducible scientific data while remaining transparent about domain variance.

---

## ADR-011: XGBoost and SHAP Interpretability Parked to Sprint 2
- **Status:** Accepted
- **Context:** Introducing gradient boosting frameworks (XGBoost, CatBoost) and SHAP TreeExplainer computations during S1 adds heavy dependency overhead before basic data contracts and UI shells are stabilized.
- **Decision:** Park all XGBoost training and SHAP calculations to Sprint 2. In Sprint 1, UI shell explainability is demonstrated using mock response fixtures, and scrap sensitivity is computed deterministically via Leave-One-Out blender math.
- **Consequences:** Enforces a clean separation between foundational data contracts and advanced machine learning modeling.

---

> **Tier Footnote:** `T1 REAL | LIT calc | D1 proxy`  
> **Model Disclaimer:** Supplement, builds soil — not fertilizer replacement. Model estimates reflect statistical associations on historical proxy data (sanity check, not proof).
