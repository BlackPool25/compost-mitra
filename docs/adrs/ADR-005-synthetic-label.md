# ADR-005: Retention of Synthetic Flag in Upstream Datasets

- **Status:** Accepted
- **Date:** 2026-10-02
- **Decision:** Preserves Synthetic, Source, and Batch columns in clean Mullick 1314 dataset.
- **Consequences:** Enables strict S2 ablation study comparing real-only (452 rows) vs synthetic-augmented models with zero leakage in S1.

> **Tier Footnote:** `T1 REAL | LIT calc | D1 proxy`  
> **Disclaimer:** Supplement, builds soil — not fertilizer replacement. Model estimates reflect statistical associations on historical proxy data (sanity check, not proof).
