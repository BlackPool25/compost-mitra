# ADR-012: Mullick-Real Exclusion from Transfer Claims (Hafsa Duplication)

- **Status:** Accepted
- **Date:** 2026-10-12
- **Context:** `data/clean/hafsa_452.csv` holds 452 real compost observations. `data/clean/mullick_1314.csv` holds 1314 rows with a preserved `Synthetic` flag, of which the `Synthetic == 0` subset is also 452 rows. Row-by-row comparison shows 452/452 rows duplicated between `hafsa_452.csv` and the `mullick_1314.csv` `Synthetic == 0` subset on all mapped contract keys (`cn`, `ph`, `moist_pct`, `temp`, `day`, `nh3`, `no3`, `tn`, `toc`, `ec`, `om`) plus `source` and `batch_key` (46 identical), per `DATA_CONTRACT_v3.1.md` §2 key mapping and §5 file schemas. Treating Mullick-real as an independent holdout would therefore double-count one dataset as two.
- **Decision:** Exclude the Mullick-real (`Synthetic == 0`) subset from all cross-dataset transfer and generalization claims. Transfer evaluation uses Hafsa-real → Zhang (`zhang_848.csv`, N=848, GI maturity indicators) only, reported as an observed generalization gap (sanity check, not proof). Retain `Synthetic`, `Source`/`source`, and `Batch`/`batch_key` columns in `mullick_1314.csv` strictly to support the Sprint 2 ablation (real-only vs synthetic-augmented) with zero synthetic leakage in Sprint 1, per ADR-005. No transfer numbers are restated here.
- **Consequences:** Transfer tables lose one claimed holdout pair (Hafsa-real → Mullick-real is void); Zhang remains the sole public-proxy holdout per ADR-010. Sprint 1 training stays on certified real rows only. Sprint 2 ablation design is unchanged and remains leak-free.

> **Tier Footnote:** `T1 REAL | LIT calc | D1 proxy`  
> **Disclaimer:** Supplement, builds soil — not fertilizer replacement. Model estimates reflect statistical associations on historical proxy data (sanity check, not proof).
