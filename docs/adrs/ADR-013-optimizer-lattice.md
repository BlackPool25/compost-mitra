# ADR-013: Simplex-Lattice Optimizer with Dirichlet Refinement

- **Status:** Accepted
- **Date:** 2026-10-12
- **Context:** `optimize(needs: dict, waste: dict, k: int = 3) -> list[dict]` (per `DATA_CONTRACT_v3.1.md` §4) must return bounded, deterministic, offline top-k recipes over blend weights satisfying Σw = 1 ± 1e-6 with strictly `lower_snake` keys (`cn`, `ph`, `moist_pct`, plus `n`/`p`/`k` blend outputs and `P_cap` from `data/plants.csv`). Unbounded search risks latency and non-reproducibility on viva-defense hardware.
- **Decision:** Lock the optimizer to a simplex-lattice {10, 10} grid yielding 92378 candidates. Stage 1 (coarse): score all lattice points, retain the top 10pct. Stage 2 (refine): run a 1pct Dirichlet perturbation search concentrated around the top-3 coarse recipes. Zero weights are allowed (sparse recipes permitted). Final ranking uses Final = suitability + maturity-penalties with lambdaP = 0.35 and lambdaPH = 0.20, plus the ADR-006 P-cap penalty applied through `match()` scoring. Seed 42 governs all Dirichlet draws per `DATA_CONTRACT_v3.1.md` §1.
- **Consequences:** Search space, seed, weights, and penalty coefficients are frozen and auditable; cold-start stays within the offline <3s budget. Lattice resolution and lambda values change only via contract version bump plus full rerun. Heuristic `ph` blending remains labeled `HEURISTIC-linear-approx`.

> **Tier Footnote:** `T1 REAL | LIT calc | D1 proxy`  
> **Disclaimer:** Supplement, builds soil — not fertilizer replacement. Model estimates reflect statistical associations on historical proxy data (sanity check, not proof).
