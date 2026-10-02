# ADR-003: Sprint 2 Model Kill Bar (+5pp above Majority Baseline)

- **Status:** Accepted
- **Date:** 2026-10-02
- **Decision:** Enforces that S2 model must beat majority baseline by at least +5.0 percentage points in GroupKFold cross-validation (proxy sanity check, not proof).
- **Consequences:** Prevents shipping ineffective black-box models; triggers automatic fallback to transparent rules table.

> **Tier Footnote:** `T1 REAL | LIT calc | D1 proxy`  
> **Disclaimer:** Supplement, builds soil — not fertilizer replacement. Model estimates reflect statistical associations on historical proxy data (sanity check, not proof).
