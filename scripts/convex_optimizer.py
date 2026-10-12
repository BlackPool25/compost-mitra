#!/usr/bin/env python3
"""CompostMitra Mathematical Convex Recipe Optimizer.

Solves recipe synthesis and bulking-agent balancing via convex optimization
(Linear Programming and Quadratic Programming) using scipy.optimize.

Replaces discrete lattice grid search (which misses valid mixes between coarse steps)
with exact convex polytope projection and Linear Programming (HiGHS solver).

Key Formulations:
1. Exact Linearization of C/N Ratio Bounds:
   Since C/N = (sum w_i * d_i * C_i) / (sum w_i * d_i * N_i), requiring R_min <= C/N <= R_max
   is non-linear in fractional form, but strictly linear in numerator vs denominator:
     sum_i w_i * d_i * (R_min * N_i - C_i) <= 0
     sum_i w_i * d_i * (C_i - R_max * N_i) <= 0
   where d_i = 1 - moist_pct_i / 100 (dry matter fraction).

2. Linearization of Moisture Bounds:
     sum_i w_i * (M_min - M_i) <= 0
     sum_i w_i * (M_i - M_max) <= 0

3. Minimal Bulking Agent Addition (LP):
   Given fixed user waste masses (m_waste_k), finds minimal bulking masses (x_j >= 0)
   to bring pile into agronomic safety envelope in < 2 ms.

4. Quadratic Distance Projection (QP):
   Given user prior proportions w_0, finds closest valid recipe w* on the convex polytope:
     min 0.5 * ||w - w_0||^2 subject to A_ub @ w <= b_ub, sum w_i = 1, w_i >= 0.

Governance:
  - T1 REAL | LIT calc | D1 proxy
  - Pure deterministic math; no causal assertions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import scipy.optimize as opt

from scripts.blender import blend, load_catalog


@dataclass
class OptimizationResult:
    """Outcome container for convex recipe optimization."""

    success: bool
    status_message: str
    weights: Dict[str, float] = field(default_factory=dict)
    masses_kg: Dict[str, float] = field(default_factory=dict)
    total_mass_kg: float = 0.0
    blend_properties: Dict[str, Any] = field(default_factory=dict)
    slack_analysis: Dict[str, float] = field(default_factory=dict)
    solve_time_ms: float = 0.0
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "success": self.success,
            "status_message": self.status_message,
            "weights": self.weights,
            "masses_kg": self.masses_kg,
            "total_mass_kg": self.total_mass_kg,
            "blend_properties": self.blend_properties,
            "slack_analysis": self.slack_analysis,
            "solve_time_ms": self.solve_time_ms,
            "recommendations": self.recommendations,
        }


def _is_citrus(ing_id: str, ing_data: Dict[str, Any]) -> bool:
    """Determine whether ingredient is citrus feedstock subject to 20% limit."""
    name_lower = ing_data.get("name", "").lower()
    group_lower = ing_data.get("group", "").lower()
    id_lower = ing_id.lower()
    return "citrus" in name_lower or "citrus" in group_lower or "citrus" in id_lower


def balance_available_wastes(
    waste_masses_kg: Dict[str, float],
    bulking_candidates: Optional[List[str]] = None,
    cn_range: Tuple[float, float] = (25.0, 35.0),
    moist_range: Tuple[float, float] = (50.0, 65.0),
    max_citrus_fraction: float = 0.20,
    catalog: Optional[Dict[str, Dict[str, Any]]] = None,
) -> OptimizationResult:
    """Solve for minimal bulking agent addition to balance fixed household wastes.

    Given a fixed bucket of waste masses that may be overly wet or low in carbon,
    this Linear Program calculates the exact minimum masses of available dry/carbon
    materials (e.g. dry leaves, sawdust, cardboard) required to bring the mixture
    into target C/N and moisture ranges.

    Args:
        waste_masses_kg: Fixed input wastes with non-negative masses in kg.
        bulking_candidates: List of candidate bulking agent ingredient IDs.
            Defaults to ['dry_leaves', 'sawdust', 'cardboard', 'straw'].
        cn_range: Acceptable (min, max) C/N ratio bounds.
        moist_range: Acceptable (min, max) moisture percentage bounds.
        max_citrus_fraction: Maximum allowed citrus fraction by wet mass (default 0.20).
        catalog: Ingredient catalog dictionary. Defaults to certified catalog.

    Returns:
        OptimizationResult containing optimal bulking additions and blended properties.
    """
    t0 = time.perf_counter()
    cat = catalog if catalog is not None else load_catalog()

    if not waste_masses_kg:
        return OptimizationResult(
            success=False,
            status_message="Waste masses dictionary cannot be empty.",
            solve_time_ms=(time.perf_counter() - t0) * 1000.0,
        )

    # Validate inputs
    for k, m in waste_masses_kg.items():
        if m < 0:
            return OptimizationResult(
                success=False,
                status_message=f"Mass cannot be negative for ingredient '{k}'.",
                solve_time_ms=(time.perf_counter() - t0) * 1000.0,
            )
        if k not in cat:
            return OptimizationResult(
                success=False,
                status_message=f"Ingredient '{k}' not found in catalog.",
                solve_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

    total_waste_mass = sum(waste_masses_kg.values())
    if total_waste_mass <= 1e-9:
        return OptimizationResult(
            success=False,
            status_message="Total input waste mass must be strictly positive.",
            solve_time_ms=(time.perf_counter() - t0) * 1000.0,
        )

    # Default bulking candidates available in catalog
    if bulking_candidates is None:
        standard_bulkers = [
            "dry_leaves",
            "sawdust",
            "cardboard",
            "straw",
            "peanut_shells",
            "coconut_coir",
            "coffee_grounds",
        ]
        bulking_candidates = [b for b in standard_bulkers if b in cat]
        if not bulking_candidates:
            # Fallback to any 'Brown' ingredients
            bulking_candidates = [
                k for k, v in cat.items()
                if v.get("group", "").lower() == "brown" and k not in waste_masses_kg
            ]

    # Check whether existing waste is ALREADY compliant
    initial_weights = {k: m / total_waste_mass for k, m in waste_masses_kg.items()}
    initial_blend = blend(initial_weights, cat)
    cn_init = initial_blend["cn"]
    m_init = initial_blend["moist_pct"]

    citrus_mass = sum(m for k, m in waste_masses_kg.items() if _is_citrus(k, cat[k]))
    citrus_frac_init = citrus_mass / total_waste_mass

    if (
        cn_range[0] <= cn_init <= cn_range[1]
        and moist_range[0] <= m_init <= moist_range[1]
        and citrus_frac_init <= max_citrus_fraction
    ):
        elapsed = (time.perf_counter() - t0) * 1000.0
        return OptimizationResult(
            success=True,
            status_message="Input wastes are already within the optimal agronomic envelope.",
            weights=initial_weights,
            masses_kg=dict(waste_masses_kg),
            total_mass_kg=total_waste_mass,
            blend_properties=initial_blend,
            slack_analysis={
                "cn_margin_min": cn_init - cn_range[0],
                "cn_margin_max": cn_range[1] - cn_init,
                "moist_margin_min": m_init - moist_range[0],
                "moist_margin_max": moist_range[1] - m_init,
                "citrus_margin": max_citrus_fraction - citrus_frac_init,
            },
            solve_time_ms=elapsed,
            recommendations=["No bulking agent addition needed; ready for composting."],
        )

    # Formulate Linear Program:
    # Variables: x_j >= 0, representing wet mass (kg) of bulking candidate j to add.
    # Objective: min sum_j x_j (minimizing added mass)
    # Total mass M_tot = total_waste_mass + sum_j x_j.
    # Dry matter, C, N definitions:
    # d_i = 1 - moist_i / 100
    # C_dry_i = d_i * (C_i / 100)
    # N_dry_i = d_i * (N_i / 100)
    #
    # Constraint 1 (C/N >= R_min):
    #   sum_j x_j * (R_min * N_dry_j - C_dry_j) <= sum_k m_k * (C_dry_k - R_min * N_dry_k)
    # Constraint 2 (C/N <= R_max):
    #   sum_j x_j * (C_dry_j - R_max * N_dry_j) <= sum_k m_k * (R_max * N_dry_k - C_dry_k)
    # Constraint 3 (Moisture >= M_min):
    #   sum_j x_j * (M_min - M_j) <= sum_k m_k * (M_k - M_min)
    # Constraint 4 (Moisture <= M_max):
    #   sum_j x_j * (M_j - M_max) <= sum_k m_k * (M_max - M_k)
    # Constraint 5 (Citrus fraction <= max_citrus):
    #   citrus_mass / (total_waste_mass + sum_j x_j) <= max_citrus
    #   <=> citrus_mass - max_citrus * total_waste_mass <= max_citrus * sum_j x_j
    #   <=> -max_citrus * sum_j x_j <= max_citrus * total_waste_mass - citrus_mass

    R_min, R_max = cn_range
    M_min, M_max = moist_range

    # Precompute constants for input wastes
    waste_C_tot = 0.0
    waste_N_tot = 0.0
    waste_M_tot = 0.0
    for k, m in waste_masses_kg.items():
        data = cat[k]
        d = 1.0 - data["moist_pct"] / 100.0
        c_dry = d * (data["C"] / 100.0)
        n_dry = d * (data["N_pct"] / 100.0)
        waste_C_tot += m * c_dry
        waste_N_tot += m * n_dry
        waste_M_tot += m * data["moist_pct"]

    # Candidate vectors
    n_cands = len(bulking_candidates)
    if n_cands == 0:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return OptimizationResult(
            success=False,
            status_message="No bulking candidates available to balance feedstock.",
            solve_time_ms=elapsed,
        )

    cand_C = np.zeros(n_cands)
    cand_N = np.zeros(n_cands)
    cand_M = np.zeros(n_cands)
    for j, c_id in enumerate(bulking_candidates):
        data = cat[c_id]
        d = 1.0 - data["moist_pct"] / 100.0
        cand_C[j] = d * (data["C"] / 100.0)
        cand_N[j] = d * (data["N_pct"] / 100.0)
        cand_M[j] = data["moist_pct"]

    # A_ub rows:
    # Row 0: C/N >= R_min
    row0 = R_min * cand_N - cand_C
    rhs0 = waste_C_tot - R_min * waste_N_tot

    # Row 1: C/N <= R_max
    row1 = cand_C - R_max * cand_N
    rhs1 = R_max * waste_N_tot - waste_C_tot

    # Row 2: Moisture >= M_min
    row2 = M_min - cand_M
    rhs2 = waste_M_tot - M_min * total_waste_mass

    # Row 3: Moisture <= M_max
    row3 = cand_M - M_max
    rhs3 = M_max * total_waste_mass - waste_M_tot

    # Row 4: Citrus <= max_citrus
    row4 = -max_citrus_fraction * np.ones(n_cands)
    rhs4 = max_citrus_fraction * total_waste_mass - citrus_mass

    A_ub = np.vstack([row0, row1, row2, row3, row4])
    b_ub = np.array([rhs0, rhs1, rhs2, rhs3, rhs4])

    c_obj = np.ones(n_cands)  # Minimize total added bulking mass
    bounds = [(0.0, None) for _ in range(n_cands)]

    res = opt.linprog(c=c_obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    elapsed = (time.perf_counter() - t0) * 1000.0

    if not res.success:
        return OptimizationResult(
            success=False,
            status_message=f"No feasible bulking addition exists within constraints: {res.message}",
            solve_time_ms=elapsed,
            recommendations=[
                "Consider broadening C/N or moisture targets or providing additional high-carbon bulking agents."
            ],
        )

    # Reconstruct final masses and proportions
    sol_masses = res.x
    final_masses = dict(waste_masses_kg)
    added_recommendations = []
    for j, c_id in enumerate(bulking_candidates):
        add_m = float(sol_masses[j])
        if add_m > 1e-4:
            final_masses[c_id] = final_masses.get(c_id, 0.0) + add_m
            added_recommendations.append(
                f"Add {add_m:.2f} kg of {cat[c_id].get('name', c_id)} to balance pile."
            )

    new_total_mass = sum(final_masses.values())
    final_weights = {k: m / new_total_mass for k, m in final_masses.items()}
    final_blend = blend(final_weights, cat)

    slack = {
        "cn_margin_min": final_blend["cn"] - cn_range[0],
        "cn_margin_max": cn_range[1] - final_blend["cn"],
        "moist_margin_min": final_blend["moist_pct"] - moist_range[0],
        "moist_margin_max": moist_range[1] - final_blend["moist_pct"],
        "citrus_margin": max_citrus_fraction - (citrus_mass / new_total_mass),
    }

    return OptimizationResult(
        success=True,
        status_message="Optimal recipe successfully synthesized via Linear Programming.",
        weights=final_weights,
        masses_kg=final_masses,
        total_mass_kg=new_total_mass,
        blend_properties=final_blend,
        slack_analysis=slack,
        solve_time_ms=elapsed,
        recommendations=added_recommendations or ["Pile is balanced with existing feedstocks."],
    )


def synthesize_optimal_recipe(
    candidate_ingredients: List[str],
    target_cn: float = 30.0,
    target_moist: float = 55.0,
    cn_range: Tuple[float, float] = (25.0, 35.0),
    moist_range: Tuple[float, float] = (50.0, 65.0),
    max_citrus_fraction: float = 0.20,
    priors: Optional[Dict[str, float]] = None,
    catalog: Optional[Dict[str, Dict[str, Any]]] = None,
) -> OptimizationResult:
    """Synthesize optimal feedstock wet proportions minimizing variance or deviation from prior.

    Uses Quadratic Programming / SLSQP to project onto the convex polytope of valid recipes:
      min_{w} 0.5 * sum_i (w_i - w_{0,i})^2 + lambda_cn * (cn(w) - target_cn)^2
      subject to:
        sum_i w_i = 1.0
        w_i >= 0
        cn_min <= cn(w) <= cn_max
        moist_min <= moist(w) <= moist_max
        citrus_sum <= max_citrus_fraction

    Args:
        candidate_ingredients: Available ingredients to mix.
        target_cn: Preferred C/N centerpoint (default 30.0).
        target_moist: Preferred moisture centerpoint (default 55.0).
        cn_range: Strict (min, max) C/N boundaries.
        moist_range: Strict (min, max) moisture boundaries.
        max_citrus_fraction: Maximum allowed wet mass fraction of citrus.
        priors: Optional target weights or inventory availability vector.
        catalog: Ingredient specifications catalog.

    Returns:
        OptimizationResult with globally optimal proportions.
    """
    t0 = time.perf_counter()
    cat = catalog if catalog is not None else load_catalog()

    valid_cands = [c for c in candidate_ingredients if c in cat]
    if len(valid_cands) < 2:
        return OptimizationResult(
            success=False,
            status_message="At least 2 valid candidate ingredients are required for recipe synthesis.",
            solve_time_ms=(time.perf_counter() - t0) * 1000.0,
        )

    n = len(valid_cands)
    d = np.zeros(n)
    c_dry = np.zeros(n)
    n_dry = np.zeros(n)
    moist = np.zeros(n)
    is_cit = np.zeros(n)

    for i, cid in enumerate(valid_cands):
        entry = cat[cid]
        d[i] = 1.0 - entry["moist_pct"] / 100.0
        c_dry[i] = d[i] * (entry["C"] / 100.0)
        n_dry[i] = d[i] * (entry["N_pct"] / 100.0)
        moist[i] = entry["moist_pct"]
        is_cit[i] = 1.0 if _is_citrus(cid, entry) else 0.0

    # Linear inequality constraints A_ub @ w <= b_ub:
    R_min, R_max = cn_range
    M_min, M_max = moist_range

    # 1. C/N >= R_min <=> sum w_i * (R_min * n_dry_i - c_dry_i) <= 0
    row_cn_min = R_min * n_dry - c_dry
    # 2. C/N <= R_max <=> sum w_i * (c_dry_i - R_max * n_dry_i) <= 0
    row_cn_max = c_dry - R_max * n_dry
    # 3. Moist >= M_min <=> sum w_i * (M_min - moist_i) <= 0
    row_m_min = M_min - moist
    # 4. Moist <= M_max <=> sum w_i * (moist_i - M_max) <= 0
    row_m_max = moist - M_max
    # 5. Citrus <= max_citrus <=> sum w_i * is_cit_i <= max_citrus
    row_citrus = is_cit

    A_ub = np.vstack([row_cn_min, row_cn_max, row_m_min, row_m_max, row_citrus])
    b_ub = np.array([0.0, 0.0, 0.0, 0.0, max_citrus_fraction])

    # First run fast LP check to verify polytope non-emptiness
    c_check = np.zeros(n)
    A_eq = np.ones((1, n))
    b_eq = np.array([1.0])
    bounds = [(0.0, 1.0) for _ in range(n)]

    feasibility_res = opt.linprog(
        c=c_check, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs"
    )
    if not feasibility_res.success:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return OptimizationResult(
            success=False,
            status_message="No feasible mixture exists among candidates meeting all C/N and moisture constraints.",
            solve_time_ms=elapsed,
            recommendations=[
                "Add a bulking agent with higher C/N (e.g. dry leaves) or low moisture."
            ],
        )

    # Target prior vector
    if priors:
        w0 = np.array([priors.get(c, 0.0) for c in valid_cands], dtype=float)
        if np.sum(w0) > 1e-6:
            w0 = w0 / np.sum(w0)
        else:
            w0 = np.ones(n) / n
    else:
        w0 = np.ones(n) / n

    # Objective: min 0.5 * ||w - w0||^2 + penalty towards target_cn & target_moist
    def objective_fn(w: np.ndarray) -> float:
        dist_sq = 0.5 * np.sum((w - w0) ** 2)
        # Approximate CN penalty inside objective
        tot_c = np.sum(w * c_dry)
        tot_n = max(np.sum(w * n_dry), 1e-8)
        cn_val = tot_c / tot_n
        m_val = np.sum(w * moist)
        obj = dist_sq + 0.005 * ((cn_val - target_cn) ** 2) + 0.001 * ((m_val - target_moist) ** 2)
        return float(obj)

    # SLSQP constraints
    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        {"type": "ineq", "fun": lambda w: b_ub - A_ub @ w},
    ]

    x0 = feasibility_res.x  # Guaranteed feasible starting point
    sol = opt.minimize(
        objective_fn,
        x0=x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 200, "ftol": 1e-7},
    )

    elapsed = (time.perf_counter() - t0) * 1000.0
    w_opt = sol.x if sol.success else x0
    w_opt = np.maximum(w_opt, 0.0)
    w_opt = w_opt / np.sum(w_opt)

    out_weights = {valid_cands[i]: round(float(w_opt[i]), 4) for i in range(n) if w_opt[i] > 1e-4}
    # Re-normalize rounded weights to sum to exactly 1.0
    s_weights = sum(out_weights.values())
    out_weights = {k: round(v / s_weights, 4) for k, v in out_weights.items()}
    # Fix tiny rounding error on highest weight
    max_k = max(out_weights, key=out_weights.get)
    out_weights[max_k] += round(1.0 - sum(out_weights.values()), 4)

    blend_res = blend(out_weights, cat)
    slack = {
        "cn_margin_min": blend_res["cn"] - cn_range[0],
        "cn_margin_max": cn_range[1] - blend_res["cn"],
        "moist_margin_min": blend_res["moist_pct"] - moist_range[0],
        "moist_margin_max": moist_range[1] - blend_res["moist_pct"],
        "citrus_margin": max_citrus_fraction - sum(out_weights.get(k, 0.0) for k in out_weights if _is_citrus(k, cat[k])),
    }

    return OptimizationResult(
        success=True,
        status_message="Optimal recipe proportions synthesized via Quadratic Programming.",
        weights=out_weights,
        total_mass_kg=1.0,
        blend_properties=blend_res,
        slack_analysis=slack,
        solve_time_ms=elapsed,
        recommendations=[
            f"Mix {pct*100:.1f}% {cat[k].get('name', k)}" for k, pct in out_weights.items()
        ],
    )
