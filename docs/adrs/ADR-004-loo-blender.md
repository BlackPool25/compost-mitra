# ADR-004: Pure Deterministic Blender for Leave-One-Out (LOO)

- **Status:** Accepted
- **Date:** 2026-10-02
- **Decision:** Pure deterministic math function in blender.py based on dry-matter mass balances benchmarked against Cornell 30:1 (28.0-32.0 range).
- **Consequences:** Zero simulation rows generated; LOO sensitivity computed via pure calculator.

> **Tier Footnote:** `T1 REAL | LIT calc | D1 proxy`  
> **Disclaimer:** Supplement, builds soil — not fertilizer replacement. Model estimates reflect statistical associations on historical proxy data (sanity check, not proof).
