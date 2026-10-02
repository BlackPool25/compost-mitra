# Public-Proxy Holdout Split Definition (sanity, not proof)

> **Integrity Notice (sanity, not proof):** Zero field accuracy is claimed for these proxy splits (sanity, not proof). All quantitative metrics, sample counts, and threshold bounds are strictly designated for heuristic evaluation and comparison (sanity, not proof). Every claim and number is a proxy check: **sanity, not proof**.

---

## 1. Overview and Problem Context (sanity, not proof)

In Stage 1 (S1) of CompostMitra, evaluation requires rigorous holdout protocols that verify whether models trained on empirical compost observations can generalize across differing research environments, experimental setups, and geographical regions (sanity, not proof). Because laboratory-grade and physical field-trial composting data vary significantly across feedstocks and climatic conditions, in-distribution cross-validation alone gives an overly optimistic assessment of model reliability (sanity, not proof).

To prevent data leakage and establish honest performance bounds, CompostMitra defines public-proxy holdout splits across independently published empirical datasets (sanity, not proof). All candidate models are evaluated using GroupKFold splits grouped by pile batch (sanity, not proof), ensuring time-series observations from the same physical reactor never appear in both training and test partitions (sanity, not proof).

---

## 2. Cross-Dataset Split Definitions (sanity, not proof)

The primary evaluation protocol comprises three distinct cross-dataset configurations linking real-world public datasets via unified schema definitions in [`data/schema_map.csv`](../../data/schema_map.csv) (sanity, not proof):

### Split A: Hafsa-Real to Mullick-Real Transfer (sanity, not proof)
- **Training Partition (sanity, not proof):** Hafsa-Kibria Compost-Dataset containing 452 experimental rows across 46 distinct batches (sanity, not proof).
- **Evaluation Partition (sanity, not proof):** Mullick Kaggle benchmark filtered strictly to real rows (`Synthetic == 0`), containing 452 real experimental rows across 46 distinct batches (sanity, not proof).
- **Schema Harmonization (sanity, not proof):** Features are harmonized using the 1:1 mapping in [`data/schema_map.csv`](../../data/schema_map.csv), including pH, moisture percentage, temperature, C/N dry ratio, total nitrogen, and germination index (sanity, not proof).
- **Evaluation Objective (sanity, not proof):** Tests cross-institution generalization between the independently published Hafsa and Mullick real-world observations (sanity, not proof).
- **Expected Benchmark Performance (sanity, not proof):** In-distribution GroupKFold achieves ~85% to ~90% accuracy; cross-dataset transfer is expected to experience a 10 to 20 percentage point domain transfer drop (sanity, not proof).

### Split B: Hafsa-Real to Zhang GI-Subset Transfer (sanity, not proof)
- **Training Partition (sanity, not proof):** Hafsa-Kibria real dataset containing 452 rows (sanity, not proof).
- **Evaluation Partition (sanity, not proof):** Zhang et al. (Nature Food 2026 meta-analysis, Zenodo 19677024) filtered to the germination index (GI) subset containing 310 clean rows spanning 96 independent studies (sanity, not proof). Note that the raw literature corpus contains 848 total observations from 171 research papers (sanity, not proof).
- **Schema Harmonization (sanity, not proof):** Aligned via [`data/schema_map.csv`](../../data/schema_map.csv) across shared features: initial C/N, initial pH, initial moisture content, process period days, and final GI (sanity, not proof).
- **Evaluation Objective (sanity, not proof):** Evaluates transfer from controlled farm/manure composting piles to heterogeneous global literature benchmarks covering food waste, manure, and municipal organic substrates (sanity, not proof).
- **Expected Benchmark Performance (sanity, not proof):** Discloses an expected 10 to 20 percentage point domain transfer drop (sanity, not proof) attributable to diverse feedstock substrates and unstandardized laboratory incubation protocols (sanity, not proof).

### Split C: Green-Waste Supplementary Attempt (Li et al. 2023) (sanity, not proof)
- **Target Dataset (sanity, not proof):** Li et al. (Bioresource Technology 385, 2023), green waste composting comprising 638 rows and 13 features (sanity, not proof).
- **Access Status (sanity, not proof):** Supplementary data is gated behind an Elsevier paywall (HTTP 403 access error), recorded as `LI_NO_ACCESS` in `data/clean/li_NO_ACCESS.md` (sanity, not proof).
- **Integrity Rule (sanity, not proof):** In accordance with project contracts, zero rows are synthesized or faked to fill this gap; the split remains marked as unavailable rather than simulated (sanity, not proof).

---

## 3. Disclosed Domain Transfer Drop (sanity, not proof)

Transferring models across disparate composting datasets introduces pronounced distribution shift due to differences in pile geometry, moisture management, ambient climate, and initial carbon chemistry (sanity, not proof). 

Under the CompostMitra testing protocol, examiners and users must note the following disclosed expectations (sanity, not proof):
1. **Domain Transfer Degradation (sanity, not proof):** An expected performance drop of 10 to 20 percentage points (sanity, not proof) occurs when transferring models from Hafsa-real training sets to Mullick-real or Zhang GI-subset holdout partitions (sanity, not proof).
2. **Mechanistic Drivers of Shift (sanity, not proof):** Variations in feedstock lignin content, ambient temperature regimes (e.g. tropical vs temperate), and measurement timing across 21 to 60 day composting cycles induce substantial domain variance (sanity, not proof).
3. **No Field Accuracy Claims (sanity, not proof):** All cross-dataset transfer scores serve solely as relative indicators of algorithmic robustness: **sanity, not proof** (sanity, not proof). They do not certify accuracy for unmeasured domestic or industrial compost systems (sanity, not proof).

---

## 4. Dataset Partition Summary Table (sanity, not proof)

The following summary table outlines all public datasets and their role in the holdout framework (sanity, not proof):

| Dataset Identifier | Raw Source / DOI | Total Rows | Clean Rows | Batches / Studies | Holdout Role | Verification Status (sanity, not proof) |
|---|---|---|---|---|---|---|
| Hafsa-real | GitHub hafsa-kibria/Compost-Dataset | 452 (sanity, not proof) | 452 (sanity, not proof) | 46 batches (sanity, not proof) | Primary Training & In-Distribution Baseline | CC-BY-4.0 verified; 0 synthetic rows (sanity, not proof) |
| Mullick-real | Kaggle mmullick212057/compost-maturity | 1314 (sanity, not proof) | 452 real (sanity, not proof) | 46 batches (sanity, not proof) | Public-Proxy Cross-Dataset Holdout | CC-BY-4.0 verified; Synthetic==0 filtered (sanity, not proof) |
| Zhang GI-subset | Zenodo 10.5281/zenodo.19677024 | 848 (sanity, not proof) | 310 clean (sanity, not proof) | 96 studies (sanity, not proof) | Cross-Literature Generalization Holdout | CC-BY-4.0 verified; 0 synthetic rows (sanity, not proof) |
| Li 2023 green-waste | Elsevier 10.1016/j.biortech.2023.129444 | 638 (sanity, not proof) | 0 (gated) (sanity, not proof) | N/A (sanity, not proof) | Supplementary Domain Benchmark | LI_NO_ACCESS recorded; zero rows faked (sanity, not proof) |
| D1 Crop-Recommendation | Kaggle atharvaingle/crop-recommendation | 2200 (sanity, not proof) | 2200 (sanity, not proof) | 22 crops (sanity, not proof) | Plant Centroid Sanity Validation | ±30% centroid check PASS on 15/15 plants (sanity, not proof) |
| D3 Fertilizer-Recommendation | Kaggle nishchalchandel/fertilizer-rec | 3100 (sanity, not proof) | 3100 (sanity, not proof) | 8 crops / 7 soils (sanity, not proof) | Optimizer Directional Sanity Check | Qualitative agronomic sanity verification (sanity, not proof) |

---

## 5. Status of PRISSUE-52: Canteen Survey Parked (sanity, not proof)

Linear issue **PRISSUE-52** (*[S1-DATA] Canteen survey — 7-day weighing from Day 1 + holdout sanity*) specified a physical 7-day waste weighing protocol in a campus or commercial canteen to collect real-world catering waste fractions (sanity, not proof).

### Formal Status: PARKED (sanity, not proof)
PRISSUE-52 is formally marked **PARKED** for Stage 1 (S1) foundation deliverables based on the following engineering rationale (sanity, not proof):
1. **Administrative Access Constraints (sanity, not proof):** Securing formal permissions for continuous 7-day physical access to campus canteen kitchens could not be accomplished within the S1 timeline without blocking critical path milestones (sanity, not proof).
2. **Public-Proxy Holdout Sufficiency (sanity, not proof):** The combination of Hafsa-real -> Mullick-real and Hafsa-real -> Zhang cross-dataset splits provides superior statistical diversity (spanning 142 distinct batches and studies) compared to a localized 7-day canteen sample of n=7 observations (sanity, not proof).
3. **Optional Home-Kitchen Appendix in S2 (sanity, not proof):** A simplified home-kitchen daily weighing protocol is retained as an optional appendix for Stage 2 (S2) demonstration and qualitative user persona verification, rather than a gating requirement for the M1 foundation gate (sanity, not proof).
4. **Zero Synthetic Substitution (sanity, not proof):** No synthetic or simulated canteen numbers are fabricated to replace the parked survey; all validation relies strictly on verified public datasets with zero synthetic rows (sanity, not proof).
