#!/usr/bin/env python3
"""CompostMitra Blender Calculator.

Deterministic pure calculator for compost recipe proportions.
Computes C/N ratio (dry-matter basis), macronutrients (N, P, K),
moisture percentage, and pH heuristic approximation.

Docstring reference mix (Cornell 30:1):
  exact weights: dry_leaves = 0.60, grass = 0.40
  expected output: CN = 30.x (between 28.0 and 32.0)

Governance:
  - Frozen under DATA_CONTRACT_v3.1.md
  - Pure function blend(w): NO disk, network, or console I/O inside blend()
  - Zero ML / zero synthetic training row generation
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

# Default validated literature catalog (Cornell, UNL, peer-reviewed)
DEFAULT_INGREDIENTS: dict[str, dict[str, Any]] = {
    "dry_leaves": {
        "name": "Dry Leaves",
        "group": "Brown",
        "C": 38.4,
        "N": 0.72,
        "N_pct": 0.9,
        "P_pct": 0.2,
        "K_pct": 0.5,
        "moist_pct": 20.0,
        "dph": -0.5,
        "source": "Cornell",
    },
    "grass": {
        "name": "Grass Clippings",
        "group": "Green",
        "C": 11.25,
        "N": 0.625,
        "N_pct": 2.5,
        "P_pct": 0.5,
        "K_pct": 1.2,
        "moist_pct": 75.0,
        "dph": 0.5,
        "source": "Cornell",
    },
    "meat_scraps": {
        "name": "Meat Scraps",
        "group": "Green",
        "C": 25.0,
        "N": 3.0,
        "N_pct": 6.0,
        "P_pct": 1.0,
        "K_pct": 0.5,
        "moist_pct": 50.0,
        "dph": 0.0,
        "source": "Literature",
    },
    "veg_scraps": {
        "name": "Vegetable Scraps",
        "group": "Green",
        "C": 12.0,
        "N": 0.6,
        "N_pct": 2.0,
        "P_pct": 0.4,
        "K_pct": 1.0,
        "moist_pct": 70.0,
        "dph": 0.0,
        "source": "Literature",
    },
    "coffee_grounds": {
        "name": "Coffee Grounds",
        "group": "Green",
        "C": 25.0,
        "N": 1.25,
        "N_pct": 2.5,
        "P_pct": 0.3,
        "K_pct": 0.6,
        "moist_pct": 50.0,
        "dph": -1.0,
        "source": "Literature",
    },
    "banana_peel": {
        "name": "Banana Peel",
        "group": "Green",
        "C": 10.0,
        "N": 0.33,
        "N_pct": 1.33,
        "P_pct": 0.2,
        "K_pct": 3.0,
        "moist_pct": 75.0,
        "dph": 0.2,
        "source": "Literature",
    },
    "eggshell": {
        "name": "Eggshell",
        "group": "Brown",
        "C": 1.0,
        "N": 0.1,
        "N_pct": 0.1,
        "P_pct": 0.4,
        "K_pct": 0.1,
        "moist_pct": 5.0,
        "dph": 2.0,
        "source": "Literature",
    },
    "cardboard": {
        "name": "Cardboard",
        "group": "Brown",
        "C": 45.0,
        "N": 0.125,
        "N_pct": 0.13,
        "P_pct": 0.05,
        "K_pct": 0.1,
        "moist_pct": 5.0,
        "dph": 0.0,
        "source": "Literature",
    },
}


def blend(
    w: dict[str, float],
    ingredients: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Pure blending calculation for feedstock proportions.

    Args:
        w: Mapping from ingredient identifier to weight proportion.
        ingredients: Optional catalog of ingredient specifications.
            If None, DEFAULT_INGREDIENTS catalog is used.

    Returns:
        Contract-compliant dictionary with lower_snake keys:
        {
            "cn": float,
            "n": float,
            "p": float,
            "k": float,
            "moist_pct": float,
            "ph": float,
            "heuristic_grade": str,
        }

    Raises:
        ValueError: If weights are empty, negative, or sum != 1.0 +- 1e-6.
        KeyError: If an ingredient in w is not in ingredients catalog.
    """
    if not w:
        raise ValueError("Sum of weights must equal 1.0 +- 1e-6 (weights dictionary cannot be empty)")

    catalog = ingredients if ingredients is not None else DEFAULT_INGREDIENTS

    # Precondition: Sum of weights must equal 1.0 +- 1e-6
    weight_sum = sum(w.values())
    if abs(weight_sum - 1.0) > 1e-6:
        raise ValueError(f"Sum of weights must equal 1.0 +- 1e-6 (got {weight_sum})")

    # Verify non-negative weights and ingredient presence
    for item_id, weight in w.items():
        if weight < 0.0:
            raise ValueError(f"Negative weight not allowed for ingredient '{item_id}': {weight}")
        if weight > 0.0 and item_id not in catalog:
            raise KeyError(f"Ingredient '{item_id}' not found in ingredients catalog")

    sum_c_pct = 0.0
    sum_n_pct = 0.0
    n = 0.0
    p = 0.0
    k = 0.0
    moist_pct = 0.0
    sum_dph = 0.0

    for item_id, weight in w.items():
        if weight == 0.0:
            continue

        ing = catalog[item_id]
        m_pct = float(ing.get("moist_pct", ing.get("mc", ing.get("moist", 0.0))))
        moist_pct += weight * m_pct

        # Dry mass conversion: dry = wet * (1 - moist_pct / 100)
        wet = float(ing.get("wet", 100.0))
        dry = wet * (1.0 - m_pct / 100.0)

        # Dry-basis carbon percentage: C_pct = C / dry * 100
        if "C_pct" in ing and "C" not in ing:
            c_pct = float(ing["C_pct"])
        elif "C" in ing:
            c_val = float(ing["C"])
            c_pct = (c_val / dry * 100.0) if dry > 0.0 else 0.0
        else:
            c_pct = float(ing.get("c_pct", 0.0))

        # Dry-basis nitrogen percentage: N_pct = N / dry * 100
        if "N_pct" in ing and "N" not in ing:
            n_pct = float(ing["N_pct"])
        elif "N" in ing:
            n_val = float(ing["N"])
            n_pct = (n_val / dry * 100.0) if dry > 0.0 else 0.0
        else:
            n_pct = float(ing.get("n_pct", 0.0))

        sum_c_pct += weight * c_pct
        sum_n_pct += weight * n_pct

        # Macronutrients (N, P, K)
        n_val = float(ing.get("n", ing.get("N_pct", ing.get("n_pct", ing.get("N", 0.0)))))
        p_val = float(ing.get("p", ing.get("P_pct", ing.get("p_pct", ing.get("P", 0.0)))))
        k_val = float(ing.get("k", ing.get("K_pct", ing.get("k_pct", ing.get("K", 0.0)))))
        n += weight * n_val
        p += weight * p_val
        k += weight * k_val

        # Delta-pH heuristic
        dph_val = float(ing.get("dph", ing.get("dph_i", 0.0)))
        sum_dph += weight * dph_val

    # Blended C/N ratio: dry-basis only
    cn = (sum_c_pct / sum_n_pct) if sum_n_pct > 0.0 else 0.0

    # pH formula: HEURISTIC-linear-approx
    # Note: Compost acidification and microbial buffering are nonlinear biological phenomena.
    # The linear weighted delta-pH formulation is a heuristic approximation.
    ph = 7.0 + sum_dph * 0.35
    ph = max(0.0, min(14.0, ph))

    # Evaluate heuristic_grade (comparison-only grade string)
    has_meat = any(
        w[i] > 0.0
        and (
            "meat" in i.lower()
            or "meat" in catalog[i].get("name", "").lower()
            or catalog[i].get("group", "").lower() == "meat"
        )
        for i in w
    )

    if has_meat:
        heuristic_grade = "BLOCKED_MEAT"
    else:
        all_browns = all(
            catalog[i].get("group", "").lower() == "brown"
            for i in w
            if w[i] > 0.0
        )
        if all_browns:
            heuristic_grade = "FLAG_ALL_BROWNS"
        elif 25.0 <= cn <= 35.0 and 6.0 <= ph <= 8.0:
            heuristic_grade = "GRADE_A"
        elif 20.0 <= cn <= 45.0 and 5.5 <= ph <= 8.5:
            heuristic_grade = "GRADE_B"
        elif cn < 20.0:
            heuristic_grade = "GRADE_C_LOW_CN"
        elif cn > 45.0:
            heuristic_grade = "GRADE_C_HIGH_CN"
        else:
            heuristic_grade = "GRADE_C"

    return {
        "cn": round(cn, 2),
        "n": round(n, 2),
        "p": round(p, 2),
        "k": round(k, 2),
        "moist_pct": round(moist_pct, 2),
        "ph": round(ph, 2),
        "heuristic_grade": heuristic_grade,
    }


def cornell_check() -> int:
    """Run exact Cornell reference check: dry_leaves=0.60, grass=0.40."""
    cornell_mix = {"dry_leaves": 0.60, "grass": 0.40}
    res = blend(cornell_mix)
    cn = res["cn"]
    if 28.0 <= cn <= 32.0:
        print(f"CN={cn:.1f} PASS (28-32)")
        return 0
    print(f"CN={cn:.1f} FAIL (28-32, out of range)")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CompostMitra blender calculator for feedstock recipe proportions."
    )
    parser.add_argument(
        "--cornell-check",
        action="store_true",
        help="Run exact Cornell 30:1 reference validation mix (dry_leaves 0.60, grass 0.40)",
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="JSON file path or inline JSON string of weights {'ingredient_id': weight}",
    )
    args = parser.parse_args()

    if args.cornell_check or (len(sys.argv) > 1 and sys.argv[1] == "--cornell-check"):
        return cornell_check()

    if not args.input:
        parser.print_help()
        return 1

    try:
        # Check if input is a file
        from pathlib import Path

        p = Path(args.input)
        if p.exists() and p.is_file():
            with p.open("r", encoding="utf-8") as f:
                weights = json.load(f)
        else:
            weights = json.loads(args.input)

        result = blend(weights)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
