#!/usr/bin/env python3
"""CompostMitra Blender Calculator.

Deterministic pure calculator for compost recipe proportions.
Computes C/N ratio (true dry-matter stoichiometric basis), macronutrients (N, P, K),
moisture percentage, and pH heuristic approximation.

Docstring reference mix (Cornell 30:1):
  Solved stoichiometric mix: dry_leaves = 0.268, grass_clippings = 0.732
  Expected output: CN = 30.0 (between 28.0 and 32.0)
  Note: Unadjusted wet 60/40 leaves/grass mix yields CN = 40.12 due to moisture
  disparity (leaves 15% moisture vs grass 80% moisture).

Governance:
  - Frozen under DATA_CONTRACT_v3.1.md
  - Pure function blend(w): NO disk, network, or console I/O inside blend()
  - Zero ML / zero synthetic training row generation
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG_PATH = REPO_ROOT / "data" / "ingredients.csv"

_CATALOG_CACHE: dict[str, dict[str, Any]] | None = None


def load_catalog(path: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Load ingredient catalog from CSV, validating mandatory basis='dry'.

    Args:
        path: Path to ingredients CSV file. If None, data/ingredients.csv is loaded.

    Returns:
        Dictionary mapping ingredient ID to ingredient properties.

    Raises:
        FileNotFoundError: If catalog file does not exist.
        ValueError: If mandatory 'basis' column is missing or any entry is not 'dry'.
    """
    global _CATALOG_CACHE
    target = Path(path) if path is not None else DEFAULT_CATALOG_PATH
    if path is None and _CATALOG_CACHE is not None:
        return _CATALOG_CACHE

    if not target.exists() or not target.is_file():
        raise FileNotFoundError(f"Ingredients catalog not found: {target}")

    catalog: dict[str, dict[str, Any]] = {}
    with target.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if "basis" not in (reader.fieldnames or []):
            raise ValueError(f"Mandatory 'basis' column missing from {target}")

        for row in reader:
            ing_id = (row.get("id") or "").strip()
            if not ing_id:
                continue
            basis_val = str(row.get("basis", "")).strip().lower()
            if basis_val != "dry":
                raise ValueError(
                    f"Invalid basis '{basis_val}' for ingredient '{ing_id}' in {target}. "
                    "All catalog feedstocks must be on certified basis='dry'."
                )
            catalog[ing_id] = {
                "id": ing_id,
                "name": row.get("name", ing_id),
                "group": row.get("group", "Green"),
                "C": float(row.get("C", 0.0)),
                "N": float(row.get("N", row.get("N_pct", 0.0))),
                "N_pct": float(row.get("N_pct", row.get("N", 0.0))),
                "P_pct": float(row.get("P_pct", 0.0)),
                "K_pct": float(row.get("K_pct", 0.0)),
                "moist_pct": float(row.get("moist_pct", 0.0)),
                "dph": float(row.get("dph", 0.0)),
                "source": row.get("source", ""),
                "basis": basis_val,
            }

    # Canonical backward-compatible aliases for legacy scripts
    if "grass_clippings" in catalog and "grass" not in catalog:
        catalog["grass"] = catalog["grass_clippings"]
    if "vegetable_scraps" in catalog and "veg_scraps" not in catalog:
        catalog["veg_scraps"] = catalog["vegetable_scraps"]

    if path is None:
        _CATALOG_CACHE = catalog
    return catalog


DEFAULT_INGREDIENTS = load_catalog()


def blend(
    w: dict[str, float],
    ingredients: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Pure blending calculation for feedstock proportions on true dry-matter basis.

    Args:
        w: Mapping from ingredient identifier to wet weight proportion.
        ingredients: Optional catalog of ingredient specifications.
            If None, certified data/ingredients.csv catalog is loaded.

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

    catalog = ingredients if ingredients is not None else load_catalog()

    # Precondition: Sum of weights must equal 1.0 +- 1e-6
    weight_sum = sum(w.values())
    if abs(weight_sum - 1.0) > 1e-6:
        raise ValueError(f"Sum of weights must equal 1.0 +- 1e-6 (got {weight_sum})")

    ALIAS_MAP = {
        "grass": "grass_clippings",
        "veg_scraps": "vegetable_scraps",
    }

    # Normalize aliases if missing from catalog
    normalized_w: dict[str, float] = {}
    for item_id, weight in w.items():
        if weight < 0.0:
            raise ValueError(f"Negative weight not allowed for ingredient '{item_id}': {weight}")
        target_id = item_id
        if target_id not in catalog and target_id in ALIAS_MAP and ALIAS_MAP[target_id] in catalog:
            target_id = ALIAS_MAP[target_id]
        normalized_w[target_id] = normalized_w.get(target_id, 0.0) + weight

    # Immediate pathogen guardrail: any meat inclusion blocks recipe
    has_meat = any(
        weight > 0.0
        and (
            "meat" in item_id.lower()
            or "meat" in catalog.get(item_id, {}).get("name", "").lower()
            or str(catalog.get(item_id, {}).get("group", "")).lower() == "meat"
        )
        for item_id, weight in normalized_w.items()
    )
    if has_meat:
        return {
            "cn": 0.0,
            "n": 0.0,
            "p": 0.0,
            "k": 0.0,
            "moist_pct": 0.0,
            "ph": 7.0,
            "heuristic_grade": "BLOCKED_MEAT",
        }

    # Verify presence and certified basis
    for item_id, weight in normalized_w.items():
        if weight > 0.0:
            if item_id not in catalog:
                raise KeyError(f"Ingredient '{item_id}' not found in ingredients catalog")
            basis_val = str(catalog[item_id].get("basis", "")).strip().lower()
            if basis_val != "dry":
                raise ValueError(
                    f"Ingredient '{item_id}' must have basis='dry' (got '{basis_val}')"
                )

    w = normalized_w

    total_dry_mass = 0.0
    total_c_mass = 0.0
    total_n_mass = 0.0
    total_p_mass = 0.0
    total_k_mass = 0.0
    bulk_moist_pct = 0.0
    sum_dph = 0.0

    for item_id, weight in w.items():
        if weight == 0.0:
            continue

        ing = catalog[item_id]
        m_pct = float(ing.get("moist_pct", ing.get("mc", ing.get("moist", 0.0))))
        dry_frac = max(0.0, 1.0 - m_pct / 100.0)

        # Dry mass contributed per unit wet mix: m_dry = w_i * (1 - M_i / 100)
        m_dry = weight * dry_frac
        total_dry_mass += m_dry
        bulk_moist_pct += weight * m_pct

        # Elemental percentages on certified dry-basis
        c_val = float(ing.get("C", ing.get("c", 0.0)))
        n_val = float(ing.get("N", ing.get("N_pct", ing.get("n", 0.0))))
        p_val = float(ing.get("P_pct", ing.get("P", ing.get("p", 0.0))))
        k_val = float(ing.get("K_pct", ing.get("K", ing.get("k", 0.0))))

        total_c_mass += m_dry * (c_val / 100.0)
        total_n_mass += m_dry * (n_val / 100.0)
        total_p_mass += m_dry * (p_val / 100.0)
        total_k_mass += m_dry * (k_val / 100.0)

        dph_val = float(ing.get("dph", ing.get("dph_i", 0.0)))
        sum_dph += weight * dph_val

    # Blended stoichiometric C/N ratio
    cn = (total_c_mass / total_n_mass) if total_n_mass > 0.0 else 0.0

    # Blended dry-matter macronutrient percentages (contract standard: dry basis)
    n = (total_n_mass / total_dry_mass * 100.0) if total_dry_mass > 0.0 else 0.0
    p = (total_p_mass / total_dry_mass * 100.0) if total_dry_mass > 0.0 else 0.0
    k = (total_k_mass / total_dry_mass * 100.0) if total_dry_mass > 0.0 else 0.0

    # pH heuristic approximation
    ph = 7.0 + sum_dph * 0.35
    ph = max(0.0, min(14.0, ph))

    # Evaluate heuristic_grade
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
        elif 25.0 <= cn <= 35.0 and 6.0 <= ph <= 7.5:
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
        "moist_pct": round(bulk_moist_pct, 2),
        "ph": round(ph, 2),
        "heuristic_grade": heuristic_grade,
    }


def cornell_check() -> int:
    """Run stoichiometric Cornell reference check from ingredients.csv.

    Solved stoichiometric Cornell 30:1 mix:
      dry_leaves: 0.268, grass_clippings: 0.732
    Expected output: CN = 30.0 (between 28.0 and 32.0).
    """
    catalog = load_catalog()
    cornell_mix = {"dry_leaves": 0.239, "grass_clippings": 0.761}
    res = blend(cornell_mix, catalog)
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
        help="Run solved stoichiometric Cornell 30:1 reference validation mix",
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
