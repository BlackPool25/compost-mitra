#!/usr/bin/env python3
"""Simplex-lattice compost recipe optimizer (ADR-013).

Deterministic offline search over blend-weight simplex:
coarse simplex-lattice ``{10, 10}`` at 10% steps (zeros allowed, sparse
recipes permitted) with pseudo-component bound ``citrus <= 10%``,
followed by 1% Dirichlet refinement around the top-3 coarse seeds
(seed 42). Final ranking:

    final = suit_band(n, p, k vs need bands)
            - 0.35 * phi_p - 0.20 * phi_ph - 1.00 * phi_cn [+ maturity hook]

with ``phi_p = max(0, (p - p_cap) / p_cap) ** 2`` (ADR-006 P-cap),
a piecewise ``phi_ph`` penalty outside pH 6.0-7.5, and
``phi_cn = |cn - 28| / 28`` distance to the Cornell 28:1 target.

Raw cosine saturates near 1.0 here: compost NPK blends are
near-scalar-multiples of need-band midpoints, so any fixed rescaling
keeps vectors near-collinear. Band-normalized distance responds to
per-nutrient deviation instead, which spreads rankings.

Contract (DATA_CONTRACT_v3.1 section 4):
  match(need, compost) -> float (clamped display wrapper)
  match_raw(need, compost) -> float (unclamped, for internal ranking)
  optimize(needs, waste, k=3) -> list[dict]
  loo(recipe) -> list[tuple[str, float]]
  benefits(recipe) -> {"kg_mo", "rs_mo", "co2e"}

All keys strictly lower_snake. stdlib + numpy/pandas only (numpy used
only for Dirichlet draws; stdlib ``random`` fallback when absent).

Model estimates reflect statistical associations on historical proxy
data (sanity check, not proof).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Callable

try:
    from blender import blend
except ImportError:  # pragma: no cover - package-style import fallback
    from scripts.blender import blend

try:
    from dose_calculator import CROP_DEMANDS, calculate_crop_dose
except ImportError:  # pragma: no cover
    from scripts.dose_calculator import CROP_DEMANDS, calculate_crop_dose

# ---------------------------------------------------------------------------
# Frozen constants (ADR-013 / DATA_CONTRACT_v3.1)
# ---------------------------------------------------------------------------

SEED = 42
LATTICE_LEVELS = 10          # {10, 10} lattice -> 10% steps
LATTICE_STEP = 0.10
LAMBDA_P = 0.35
LAMBDA_PH = 0.20
LAMBDA_CN = 1.00
SCORE_GAIN = 2.50
SCORE_PIVOT = 0.50
BLOCKED_RAW_SCORE = -1e9
CN_TARGET = 28.0
BAND_HALF_FLOOR = 0.05  # floor for degenerate zero-width need bands
PH_LO = 6.0
PH_HI = 7.5
CITRUS_MAX_FRAC = 0.10       # pseudo-component bound
MAX_SINGLE_WEIGHT = 0.80     # anti-degeneracy cap: no ingredient above 80%
REFINE_FRAC = 0.01           # 1% Dirichlet refinement
REFINE_DRAWS_PER_SEED = 400
MAX_LATTICE_POOL = 10        # caps coarse grid at 92378 candidates (n=10)

TIER_FOOTNOTE = "T1 REAL | LIT calc | D1 proxy"
DISCLAIMER = (
    "Supplement, builds soil — not fertilizer replacement. "
    "Model estimates reflect statistical associations on historical "
    "proxy data (sanity check, not proof)."
)

# Benefit factors mirroring app.py Step 4 impact view.
KG_PER_WASTE_KG = 4.0
RS_PER_KG = 22.5
CO2E_PER_KG = 0.45

REPO_ROOT = Path(__file__).resolve().parent.parent
INGREDIENTS_CSV = REPO_ROOT / "data" / "ingredients.csv"
PLANTS_CSV = REPO_ROOT / "data" / "plants.csv"

_LAST_NEEDS: dict[str, Any] | None = None

_ING_CACHE: dict[str, dict[str, Any]] | None = None


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_ingredients() -> dict[str, dict[str, Any]]:
    """Load ingredient catalog from data/ingredients.csv (cached)."""
    global _ING_CACHE
    if _ING_CACHE is not None:
        return _ING_CACHE
    catalog: dict[str, dict[str, Any]] = {}
    with INGREDIENTS_CSV.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ing_id = (row.get("id") or "").strip()
            if not ing_id:
                continue
            catalog[ing_id] = {
                "name": row.get("name", ing_id),
                "group": row.get("group", "Green"),
                "C": _to_float(row.get("C")),
                "N": _to_float(row.get("N")),
                "N_pct": _to_float(row.get("N_pct")),
                "P_pct": _to_float(row.get("P_pct")),
                "K_pct": _to_float(row.get("K_pct")),
                "moist_pct": _to_float(row.get("moist_pct")),
                "dph": _to_float(row.get("dph")),
                "source": row.get("source", ""),
                "basis": row.get("basis", "dry"),
            }
    _ING_CACHE = catalog
    return catalog


def load_plant_needs(plant_id: str) -> dict[str, Any]:
    """Load a plant need band from data/plants.csv with lower_snake keys."""
    want = plant_id.strip().lower()
    with PLANTS_CSV.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if (row.get("id") or "").strip().lower() == want:
                return {
                    "plant_id": (row.get("id") or "").strip(),
                    "n_lo": _to_float(row.get("N_lo")),
                    "n_hi": _to_float(row.get("N_hi")),
                    "p_lo": _to_float(row.get("P_lo")),
                    "p_hi": _to_float(row.get("P_hi")),
                    "k_lo": _to_float(row.get("K_lo")),
                    "k_hi": _to_float(row.get("K_hi")),
                    "ph_lo": _to_float(row.get("pH_lo")),
                    "ph_hi": _to_float(row.get("pH_hi")),
                    "p_cap": _to_float(row.get("P_cap")),
                    "stage_note": row.get("stage_note", ""),
                }
    raise KeyError(f"Plant '{plant_id}' not found in plants.csv")


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------

def _is_forbidden(ing_id: str, catalog: dict[str, dict[str, Any]]) -> bool:
    """Meat / dairy block: excluded from every candidate pool."""
    text = f"{ing_id} {catalog.get(ing_id, {}).get('name', '')}".lower()
    group = str(catalog.get(ing_id, {}).get("group", "")).lower()
    return (
        "meat" in text
        or "dairy" in text
        or "milk" in text
        or "cheese" in text
        or "curd" in text
        or group == "meat"
    )


def _is_citrus(ing_id: str) -> bool:
    return "citrus" in ing_id.lower()


def _violates_citrus_bound(weights: dict[str, float]) -> bool:
    return any(
        _is_citrus(ing_id) and w > CITRUS_MAX_FRAC + 1e-12
        for ing_id, w in weights.items()
    )


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _band_mid_half(need: dict[str, Any], prefix: str) -> tuple[float, float]:
    """Midpoint and half-width of a need band, with a floor on width."""
    lo = _to_float(need.get(f"{prefix}_lo"))
    hi = _to_float(need.get(f"{prefix}_hi"))
    return (lo + hi) / 2.0, max((hi - lo) / 2.0, BAND_HALF_FLOOR)


def match_raw(need: dict[str, Any], compost: dict[str, Any]) -> float:
    """Unclamped calibrated score for internal ranking.

    Same pivot/gain calibration as match() but without the [0, 1]
    clamp, so all-bad pools still rank by relative fit instead of
    collapsing to tied 0.0. Hard-blocked (meat) blends return
    BLOCKED_RAW_SCORE, below any feasible blend.
    """
    if compost.get("heuristic_grade") == "BLOCKED_MEAT":
        return BLOCKED_RAW_SCORE
    have = [
        _to_float(compost.get("n")),
        _to_float(compost.get("p")),
        _to_float(compost.get("k")),
    ]
    ph = _to_float(compost.get("ph"), 7.0)
    cn = _to_float(compost.get("cn"), CN_TARGET)

    dev_sum = 0.0
    for value, prefix in zip(have, ("n", "p", "k")):
        mid, half = _band_mid_half(need, prefix)
        z = (value - mid) / half
        dev_sum += z * z
    suitability = 1.0 - dev_sum / 3.0

    p_cap = _to_float(need.get("p_cap"), 0.0)
    if p_cap > 0.0:
        phi_p = max(0.0, (_to_float(compost.get("p")) - p_cap) / p_cap) ** 2
    else:
        phi_p = 0.0

    if ph < PH_LO:
        phi_ph = (PH_LO - ph) ** 2
    elif ph > PH_HI:
        phi_ph = (ph - PH_HI) ** 2
    else:
        phi_ph = 0.0

    phi_cn = abs(cn - CN_TARGET) / CN_TARGET

    raw = (
        suitability
        - LAMBDA_P * phi_p
        - LAMBDA_PH * phi_ph
        - LAMBDA_CN * phi_cn
    )
    return SCORE_PIVOT + SCORE_GAIN * (raw - SCORE_PIVOT)


def match(need: dict[str, Any], compost: dict[str, Any]) -> float:
    """Band-normalized NPK suitability minus P-cap, pH and CN penalties.

    Clamped display wrapper around match_raw(): identical ranking value,
    rounded and clamped to [0, 1] for display. See match_raw() for the
    full formula. Blocked (meat) blends score 0.0.
    """
    return round(max(0.0, min(1.0, match_raw(need, compost))), 4)


_MOIST_LO = 50.0
_MOIST_HI = 60.0


def score_breakdown(
    need: dict[str, Any], compost: dict[str, Any]
) -> dict[str, Any]:
    """Explanation-only penalty breakdown for one blend (pure, lower_snake).

    Mirrors the match_raw() terms without changing them: reports the
    unclamped raw score plus each penalty's share in calibrated units,
    naming the largest as top_penalty with a one-line why_text. Moisture
    uses the shared 50-60% screening band for context only. Never raises;
    statistical association only (sanity check, not proof).
    """
    try:
        have = [
            _to_float(compost.get("n")),
            _to_float(compost.get("p")),
            _to_float(compost.get("k")),
        ]
        ph = _to_float(compost.get("ph"), 7.0)
        cn = _to_float(compost.get("cn"), CN_TARGET)
        moist = _to_float(compost.get("moist_pct", compost.get("moist", 55.0)))

        dev_sum = 0.0
        for value, prefix in zip(have, ("n", "p", "k")):
            mid, half = _band_mid_half(need, prefix)
            z = (value - mid) / half
            dev_sum += z * z
        suitability = 1.0 - dev_sum / 3.0

        p_cap = _to_float(need.get("p_cap"), 0.0)
        if p_cap > 0.0:
            phi_p = max(0.0, (_to_float(compost.get("p")) - p_cap) / p_cap) ** 2
        else:
            phi_p = 0.0
        if ph < PH_LO:
            phi_ph = (PH_LO - ph) ** 2
        elif ph > PH_HI:
            phi_ph = (ph - PH_HI) ** 2
        else:
            phi_ph = 0.0
        phi_cn = abs(cn - CN_TARGET) / CN_TARGET
        if moist < _MOIST_LO:
            phi_moist = (_MOIST_LO - moist) / 55.0
        elif moist > _MOIST_HI:
            phi_moist = (moist - _MOIST_HI) / 55.0
        else:
            phi_moist = 0.0

        raw = match_raw(need, compost)
        penalties = {
            "npk_distance": round(SCORE_GAIN * max(0.0, 1.0 - suitability), 4),
            "p_cap": round(SCORE_GAIN * LAMBDA_P * phi_p, 4),
            "ph_drift": round(SCORE_GAIN * LAMBDA_PH * phi_ph, 4),
            "cn_distance": round(SCORE_GAIN * LAMBDA_CN * phi_cn, 4),
            "moisture": round(SCORE_GAIN * phi_moist, 4),
        }
        top_penalty = max(sorted(penalties), key=lambda key: penalties[key])
        if max(penalties.values()) <= 1e-12:
            why_text = "within all target bands; clamped score reflects pivot"
        else:
            why_text = (
                f"top penalty: {top_penalty.replace('_', ' ')} "
                f"({penalties[top_penalty]:.2f} of raw {raw:.2f})"
            )
        dosing = None
        crop_id = str(need.get("plant_id", "")).strip().lower()
        if crop_id in CROP_DEMANDS:
            try:
                dosing = calculate_crop_dose(crop_id, compost, dose_fresh_g=500.0, pots=1)
            except Exception:
                dosing = None
        return {
            "raw_score": raw,
            "penalties": penalties,
            "top_penalty": top_penalty,
            "why_text": why_text,
            "dosing": dosing,
        }
    except Exception:
        return {
            "raw_score": 0.0,
            "penalties": {},
            "top_penalty": "unknown",
            "why_text": "screening estimate unavailable",
            "dosing": None,
        }


def _score_blend(
    needs: dict[str, Any],
    weights: dict[str, float],
    catalog: dict[str, dict[str, Any]],
    maturity_fn: Callable[[dict[str, Any]], float] | None = None,
    raw: bool = False,
) -> tuple[float, dict[str, Any]]:
    """Blend via blender.blend and rank with match (+ optional maturity hook).

    raw=True scores with unclamped match_raw() for internal ranking and
    LOO deltas; raw=False returns the clamped display score.
    """
    compost = blend(weights, catalog)
    score = match_raw(needs, compost) if raw else match(needs, compost)
    if maturity_fn is not None:
        score = score - float(maturity_fn(compost))
        if not raw:
            score = max(0.0, min(1.0, score))
    return (score if raw else round(score, 4)), compost


# ---------------------------------------------------------------------------
# Lattice + refinement
# ---------------------------------------------------------------------------

def _compositions(levels: int, parts: int) -> Any:
    """Yield integer compositions of `levels` into `parts` bins (zeros allowed)."""
    if parts == 1:
        yield (levels,)
        return
    for first in range(levels + 1):
        for rest in _compositions(levels - first, parts - 1):
            yield (first,) + rest


def _quantize(weights: dict[str, float]) -> dict[str, float]:
    """Round to 4dp and fix residual on the largest weight (sum = 1 ± 1e-6)."""
    if not weights:
        return weights
    out = {ing_id: round(w, 4) for ing_id, w in weights.items()}
    residual = 1.0 - sum(out.values())
    if abs(residual) > 1e-12:
        top = max(sorted(out), key=lambda ing_id: out[ing_id])
        out[top] = out[top] + residual  # exact fix; keeps sum == 1 ± 1e-6
    return {ing_id: w for ing_id, w in out.items() if w > 0.0}


def _cap_single_weight(weights: dict[str, float]) -> dict[str, float]:
    """Cap any single ingredient at MAX_SINGLE_WEIGHT (pure, deterministic).

    Excess above the cap is redistributed proportionally over the other
    ingredients, so the blend stays mixed and sums to 1 ± 1e-6. Single
    entries and already-compliant blends pass through untouched. Sorted
    tie-break keeps the choice deterministic.
    """
    if len(weights) < 2:
        return dict(weights)
    top = max(sorted(weights), key=lambda ing_id: weights[ing_id])
    if weights[top] <= MAX_SINGLE_WEIGHT + 1e-12:
        return dict(weights)
    excess = weights[top] - MAX_SINGLE_WEIGHT
    rest_total = sum(w for ing_id, w in weights.items() if ing_id != top)
    if rest_total <= 1e-12:
        return dict(weights)
    out = {}
    for ing_id, w in weights.items():
        if ing_id == top:
            out[ing_id] = MAX_SINGLE_WEIGHT
        else:
            out[ing_id] = w + excess * (w / rest_total)
    return out


def _dirichlet_row(rng: Any, size: int) -> list[float]:
    """One Dirichlet(1, ..., 1) draw; numpy when present, else stdlib."""
    try:
        import numpy as np  # type: ignore

        if isinstance(rng, np.random.RandomState):
            return [float(v) for v in rng.dirichlet([1.0] * size)]
    except ImportError:
        pass
    import random as _random

    assert isinstance(rng, _random.Random)
    draws = [rng.gammavariate(1.0, 1.0) for _ in range(size)]
    total = sum(draws) or 1.0
    return [v / total for v in draws]


def _make_rng(seed: int = SEED) -> Any:
    try:
        import numpy as np  # type: ignore

        return np.random.RandomState(seed)
    except ImportError:  # pragma: no cover - offline fallback
        import random as _random

        return _random.Random(seed)


def optimize(
    needs: dict[str, Any],
    waste: dict[str, float],
    k: int = 3,
    maturity_fn: Callable[[dict[str, Any]], float] | None = None,
) -> list[dict[str, Any]]:
    """Top-k recipes over the simplex-lattice {10, 10} + Dirichlet refine.

    Internal ranking uses unclamped match_raw() so all-bad pools still
    order by relative fit; the displayed ``score`` is the clamped
    match() value.

    Args:
        needs: plant need band (lower_snake; p_cap read from plants.csv row).
        waste: available feedstocks {ingredient_id: kg_available}; keys define
            the candidate pool. Forbidden meat/dairy entries are blocked.
        k: number of recipes returned.
        maturity_fn: optional hook compost -> penalty (default None; no model
            coupling unless the caller supplies one).
    """
    global _LAST_NEEDS
    catalog = load_ingredients()
    pool = sorted(
        ing_id
        for ing_id in waste
        if ing_id in catalog and not _is_forbidden(ing_id, catalog)
    )
    if not pool:
        raise ValueError("waste pool has no usable ingredients after block checks")
    pool = pool[:MAX_LATTICE_POOL]
    _LAST_NEEDS = dict(needs)

    n = len(pool)
    scored: list[tuple[float, dict[str, float], dict[str, Any]]] = []
    for combo in _compositions(LATTICE_LEVELS, n):
        weights = {
            pool[i]: units / LATTICE_LEVELS
            for i, units in enumerate(combo)
            if units > 0
        }
        if not weights:
            continue
        if n > 1 and len(weights) < 2:
            continue  # anti-degeneracy: pure singles cannot win a blend
        weights = _cap_single_weight(weights)
        if _violates_citrus_bound(weights):
            continue
        score, compost = _score_blend(needs, weights, catalog, maturity_fn, raw=True)
        scored.append((score, weights, compost))
    if not scored:
        raise ValueError("no lattice candidates satisfy citrus/meat guardrails")
    scored.sort(key=lambda row: row[0], reverse=True)

    keep = max(k, len(scored) // 10)
    coarse_top = scored[:keep]
    seeds = [dict(weights) for _, weights, _ in scored[:3]]

    # Stage 2: 1% Dirichlet refinement around the top-3 coarse seeds.
    rng = _make_rng(SEED)
    refined: list[tuple[float, dict[str, float], dict[str, Any]]] = []
    for seed in seeds:
        base = [seed.get(ing_id, 0.0) for ing_id in pool]
        for _ in range(REFINE_DRAWS_PER_SEED):
            draw = _dirichlet_row(rng, n)
            mixed = [
                (1.0 - REFINE_FRAC) * b + REFINE_FRAC * d
                for b, d in zip(base, draw)
            ]
            total = sum(mixed) or 1.0
            mixed = [v / total for v in mixed]
            # pseudo-component citrus bound: clip then rescale remainder
            for i, ing_id in enumerate(pool):
                if _is_citrus(ing_id) and mixed[i] > CITRUS_MAX_FRAC:
                    mixed[i] = CITRUS_MAX_FRAC
            subtotal = sum(mixed) or 1.0
            mixed = [v / subtotal for v in mixed]
            weights = _quantize(
                {pool[i]: mixed[i] for i in range(n) if mixed[i] >= 0.005}
            )
            weights = _cap_single_weight(weights)
            if not weights or _violates_citrus_bound(weights):
                continue
            score, compost = _score_blend(needs, weights, catalog, maturity_fn, raw=True)
            refined.append((score, weights, compost))

    ranked = sorted(
        coarse_top + refined,
        key=lambda row: (row[0], -abs(row[2].get("cn", CN_TARGET) - CN_TARGET)),
        reverse=True,
    )
    # Dedupe near-identical recipes (1% refine draws cluster around seeds)
    # so top-k stays diverse; signature at 2dp keeps full weights intact.
    unique: list[tuple[float, dict[str, float], dict[str, Any]]] = []
    seen: set[tuple[tuple[str, float], ...]] = set()
    for row in ranked:
        sig = tuple(
            sorted(
                (ing, round(w, 1)) for ing, w in row[1].items() if w >= 0.05
            )
        )
        if sig in seen:
            continue
        seen.add(sig)
        unique.append(row)
    results: list[dict[str, Any]] = []
    for _, weights, _ in unique[: max(1, k)]:
        recipe = _cap_single_weight(_quantize(dict(weights)))
        # Re-score the capped blend so the display score matches the mix.
        raw_capped, compost = _score_blend(
            needs, recipe, catalog, maturity_fn, raw=True
        )
        results.append(
            {
                "recipe": recipe,
                "score": round(max(0.0, min(1.0, raw_capped)), 4),
                "cn": compost["cn"],
                "n": compost["n"],
                "p": compost["p"],
                "k": compost["k"],
                "moist_pct": compost["moist_pct"],
                "ph": compost["ph"],
                "heuristic_grade": compost["heuristic_grade"],
            }
        )
    results.sort(key=lambda row: row["score"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# LOO sensitivity + benefits
# ---------------------------------------------------------------------------

def _unwrap_weights(recipe: dict[str, Any]) -> dict[str, float]:
    if "recipe" in recipe and isinstance(recipe["recipe"], dict):
        return {k: float(v) for k, v in recipe["recipe"].items()}
    return {k: float(v) for k, v in recipe.items() if isinstance(v, (int, float))}


def loo(
    recipe: dict[str, Any],
    needs: dict[str, Any] | None = None,
    maturity_fn: Callable[[dict[str, Any]], float] | None = None,
) -> list[tuple[str, float]]:
    """Leave-one-out sensitivity: drop each ingredient, re-blend, re-score.

    Returns [(ingredient_id, score_delta)] sorted by delta descending;
    positive delta marks ingredients whose removal lowers the score.
    Deltas use unclamped raw scores so all-bad pools still resolve.
    """
    active = needs if needs is not None else _LAST_NEEDS
    if active is None:
        raise ValueError("loo needs plant needs: pass needs or run optimize first")
    catalog = load_ingredients()
    weights = _unwrap_weights(recipe)
    base_score, _ = _score_blend(active, weights, catalog, maturity_fn, raw=True)
    deltas: list[tuple[str, float]] = []
    for ing_id in sorted(weights):
        rest = {j: w for j, w in weights.items() if j != ing_id}
        if not rest:
            continue
        total = sum(rest.values()) or 1.0
        rest = {j: w / total for j, w in rest.items()}
        new_score, _ = _score_blend(active, rest, catalog, maturity_fn, raw=True)
        deltas.append((ing_id, round(base_score - new_score, 4)))
    deltas.sort(key=lambda row: row[1], reverse=True)
    return deltas


def benefits(recipe: dict[str, Any]) -> dict[str, float]:
    """Monthly diversion / savings / carbon estimates (factors match app.py).

    kg_mo mirrors app.py Step 4: max(total_waste_kg * 4.0, pots * 0.5 * 2.2);
    rs_mo = kg_mo * 22.5; co2e = kg_mo * 0.45.
    """
    meta = recipe if "recipe" in recipe else {}
    total_waste_kg = _to_float(meta.get("total_waste_kg", 10.0))
    pots = int(meta.get("pots", 4)) if str(meta.get("pots", 4)).strip() else 4
    kg_mo = round(max(total_waste_kg * KG_PER_WASTE_KG, pots * 0.5 * 2.2), 1)
    rs_mo = float(round(kg_mo * RS_PER_KG, 0))
    co2e = round(kg_mo * CO2E_PER_KG, 1)
    return {"kg_mo": kg_mo, "rs_mo": rs_mo, "co2e": co2e}


def crop_dosing_summary(
    compost_blend: dict[str, Any],
    crop_id: str,
    dose_fresh_g: float = 500.0,
    pots: int = 1,
) -> dict[str, Any]:
    """Calculate honest crop nutrient delivery, seasonal coverage, and safety ceilings."""
    return calculate_crop_dose(crop_id, compost_blend, dose_fresh_g=dose_fresh_g, pots=pots)


def loo_nutrient_impact(
    recipe: dict[str, Any],
    crop_id: str = "tomato",
    dose_fresh_g: float = 500.0,
) -> list[dict[str, Any]]:
    """Leave-one-out sensitivity on actual nutrient delivery (grams N available)."""
    weights = _unwrap_weights(recipe)
    catalog = load_ingredients()
    base_blend = blend(weights, catalog)
    crop_key = crop_id.strip().lower()
    if crop_key not in CROP_DEMANDS:
        crop_key = "tomato"
    base_dose = calculate_crop_dose(crop_key, base_blend, dose_fresh_g=dose_fresh_g)
    base_n = base_dose["nutrient_delivery"]["n_avail_year1_range_g"][0]

    impacts = []
    for ing_id in sorted(weights):
        rest = {j: w for j, w in weights.items() if j != ing_id}
        if not rest:
            continue
        total = sum(rest.values()) or 1.0
        rest = {j: w / total for j, w in rest.items()}
        new_blend = blend(rest, catalog)
        new_dose = calculate_crop_dose(crop_key, new_blend, dose_fresh_g=dose_fresh_g)
        new_n = new_dose["nutrient_delivery"]["n_avail_year1_range_g"][0]
        impacts.append({
            "ingredient": ing_id,
            "delta_n_avail_g": round(base_n - new_n, 3),
            "delta_coverage_pct": round(
                base_dose["nutrient_delivery"]["n_demand_coverage_range_pct"][0]
                - new_dose["nutrient_delivery"]["n_demand_coverage_range_pct"][0],
                1,
            ),
        })
    impacts.sort(key=lambda x: x["delta_n_avail_g"], reverse=True)
    return impacts


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

DEMO_WASTE_IDS = [
    "vegetable_scraps",
    "coffee_grounds",
    "banana_peel",
    "eggshell",
    "tea_waste",
    "onion_peels",
    "citrus_peels",
    "newspaper",
    "sawdust",
    "straw",
]


def run_demo(plant_id: str = "tomato", k: int = 3) -> int:
    needs = load_plant_needs(plant_id)
    catalog = load_ingredients()
    waste = {ing_id: 2.0 for ing_id in DEMO_WASTE_IDS if ing_id in catalog}
    results = optimize(needs, waste, k=k)
    print(f"Top-{len(results)} compost recipes for {needs['plant_id']} "
          f"(P_cap={needs['p_cap']})")
    for rank, res in enumerate(results, start=1):
        print(f"\n#{rank} score={res['score']:.4f} "
              f"cn={res['cn']} n={res['n']} p={res['p']} k={res['k']} "
              f"moist_pct={res['moist_pct']} ph={res['ph']} "
              f"grade={res['heuristic_grade']}")
        for ing_id in sorted(res["recipe"]):
            print(f"    {ing_id}: {res['recipe'][ing_id]:.2f}")
    top = results[0]
    print(f"\nbenefits(top-1): {benefits(top)}")
    print("loo(top-1) deltas:")
    for ing_id, delta in loo(top):
        print(f"    {ing_id}: {delta:+.4f}")
    print(f"\n{TIER_FOOTNOTE}")
    print(DISCLAIMER)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ADR-013 simplex-lattice compost recipe optimizer."
    )
    parser.add_argument("--demo", metavar="PLANT",
                        help="run demo for a plant id (e.g. tomato)")
    parser.add_argument("--k", type=int, default=3,
                        help="top-k recipes in demo output")
    args = parser.parse_args(argv)
    if args.demo:
        return run_demo(args.demo, k=args.k)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
