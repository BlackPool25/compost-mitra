#!/usr/bin/env python3
"""CompostMitra Crop Nutrient Dosing Calculator.

Replaces naive percentage-matching with an agronomic mass-and-mineralization
dosing model:
  1. Biological transformation: converts raw feedstock mix to finished cured
     compost accounting for 40-60% respiration mass loss, mineral concentration
     (P, K), and partial N volatilization.
  2. Nutrient availability: applies first-year organic mineralization rate
     (10-20% for N, 75% for P, 85% for K) with explicit uncertainty propagation.
  3. Container crop demands: grounded in ICAR/IIHR/FAO container standards
     (grams of N, P, K per 12-15L pot per season).
  4. Agronomic ceilings: enforces volumetric soil ceiling (<=25% of potting mix
     by volume to prevent salinity/EC scorch) and seasonal P loading cap (<=3.0g P/pot).

Governance:
  - Pure deterministic calculator.
  - Sourced from ICAR, Oregon State Extension (EM 9245), and UF/IFAS Circular 1051.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Standard 12-15L container pot demands (grams of elemental N, P, K per pot per season).
# Converted from ICAR/IIHR crop packages and container gardening extension guides
# assuming ~10-12 kg dry soil volume, 0.07 m2 surface area, standard season length.
CROP_DEMANDS: dict[str, dict[str, Any]] = {
    "tomato": {
        "name": "Tomato",
        "family": "Solanaceae",
        "season_days": 120,
        "n_demand_g": 12.0,
        "p_demand_g": 2.0,
        "k_demand_g": 12.0,
        "p_ceiling_g": 3.0,
        "source": "ICAR Tomato Package; UGA Extension Veg Guide",
    },
    "spinach": {
        "name": "Spinach",
        "family": "Amaranthaceae",
        "season_days": 45,
        "n_demand_g": 4.0,
        "p_demand_g": 0.7,
        "k_demand_g": 3.0,
        "p_ceiling_g": 1.5,
        "source": "TNAU Agritech Spinach Portal; FAO Fertilizer Specs",
    },
    "coriander": {
        "name": "Coriander",
        "family": "Apiaceae",
        "season_days": 40,
        "n_demand_g": 3.5,
        "p_demand_g": 0.6,
        "k_demand_g": 2.5,
        "p_ceiling_g": 1.5,
        "source": "ICAR Spices & Herbs; TNAU Portal",
    },
    "chilli": {
        "name": "Green Chilli",
        "family": "Solanaceae",
        "season_days": 150,
        "n_demand_g": 10.0,
        "p_demand_g": 1.8,
        "k_demand_g": 8.5,
        "p_ceiling_g": 2.8,
        "source": "ICAR Vegetable Guidelines; TNAU Chilli",
    },
    "brinjal": {
        "name": "Brinjal",
        "family": "Solanaceae",
        "season_days": 140,
        "n_demand_g": 11.0,
        "p_demand_g": 1.9,
        "k_demand_g": 9.0,
        "p_ceiling_g": 3.0,
        "source": "ICAR Vegetable Production; TNAU Portal",
    },
    "rose": {
        "name": "Rose",
        "family": "Rosaceae",
        "season_days": 120,
        "n_demand_g": 10.0,
        "p_demand_g": 2.5,
        "k_demand_g": 8.0,
        "p_ceiling_g": 3.0,
        "source": "Royal Horticultural Society Rose Care; ICAR",
    },
    "hibiscus": {
        "name": "Hibiscus",
        "family": "Malvaceae",
        "season_days": 120,
        "n_demand_g": 8.0,
        "p_demand_g": 1.2,
        "k_demand_g": 9.5,
        "p_ceiling_g": 2.0,
        "source": "American Hibiscus Society; TNAU Floriculture",
    },
    "marigold": {
        "name": "Marigold",
        "family": "Asteraceae",
        "season_days": 90,
        "n_demand_g": 6.0,
        "p_demand_g": 1.5,
        "k_demand_g": 5.0,
        "p_ceiling_g": 2.5,
        "source": "ICAR Floriculture Portal; TNAU Flowers",
    },
    "tulsi": {
        "name": "Holy Basil",
        "family": "Lamiaceae",
        "season_days": 90,
        "n_demand_g": 4.5,
        "p_demand_g": 0.8,
        "k_demand_g": 3.5,
        "p_ceiling_g": 1.8,
        "source": "CIMAP Medicinal Plants Bulletin; TNAU Herbs",
    },
    "mint": {
        "name": "Garden Mint",
        "family": "Lamiaceae",
        "season_days": 60,
        "n_demand_g": 5.0,
        "p_demand_g": 0.9,
        "k_demand_g": 3.5,
        "p_ceiling_g": 2.0,
        "source": "CIMAP Aromatic Crop Guide; RHS Herbs",
    },
    "money_plant": {
        "name": "Money Plant",
        "family": "Araceae",
        "season_days": 90,
        "n_demand_g": 3.0,
        "p_demand_g": 0.6,
        "k_demand_g": 2.5,
        "p_ceiling_g": 1.5,
        "source": "UGA Extension Indoor Foliage; RHS",
    },
    "carrot": {
        "name": "Carrot",
        "family": "Apiaceae",
        "season_days": 90,
        "n_demand_g": 5.0,
        "p_demand_g": 1.5,
        "k_demand_g": 6.0,
        "p_ceiling_g": 2.5,
        "source": "ICAR Tuber & Root Crops; FAO Vegetable Production",
    },
    "beans": {
        "name": "French Beans",
        "family": "Fabaceae",
        "season_days": 75,
        "n_demand_g": 3.0,  # Symbiotic rhizobia fix majority of N
        "p_demand_g": 1.5,
        "k_demand_g": 4.5,
        "p_ceiling_g": 2.5,
        "source": "ICAR Pulse Guidelines",
    },
    "banana": {
        "name": "Dwarf Banana",
        "family": "Musaceae",
        "season_days": 180,
        "n_demand_g": 25.0,
        "p_demand_g": 4.0,
        "k_demand_g": 35.0,
        "p_ceiling_g": 5.0,
        "source": "NRC Banana Trichy; Container Tub Standards",
    },
    "papaya": {
        "name": "Papaya",
        "family": "Caricaceae",
        "season_days": 180,
        "n_demand_g": 20.0,
        "p_demand_g": 3.5,
        "k_demand_g": 25.0,
        "p_ceiling_g": 4.5,
        "source": "TNAU Horticulture Portal; Container Tub Standards",
    },
}

# Physical composting transformation constants (documented ranges)
# 40-60% respiration loss of dry organic mass (CO2, H2O loss)
DEFAULT_DRY_YIELD = 0.50  # 50% dry mass retained (range 0.40 - 0.60)
DEFAULT_N_RETENTION = 0.70  # 70% N retained (range 0.60 - 0.80)
DEFAULT_MINERAL_RETENTION = 1.00  # P and K are non-volatile (100% retained)
DEFAULT_FINISHED_MOISTURE = 40.0  # Finished cured compost moisture % (range 35-45%)

# First-year nutrient availability (mineralization fractions)
# Parameter range for organic nitrogen release in potting soil: 10% to 20%
N_MIN_LO = 0.10
N_MIN_HI = 0.20
P_AVAIL_RATE = 0.75  # ~75% P available in Year 1
K_AVAIL_RATE = 0.85  # ~85% K water-soluble in Year 1

# Potting container soil capacity and safety limits
DEFAULT_POT_SOIL_KG = 10.0  # ~12-15L container holds ~10kg dry potting soil mix
MAX_COMPOST_VOL_FRAC = 0.25  # Maximum 25% compost by volume (salinity/EC limit)
MAX_COMPOST_FRESH_KG_PER_POT = DEFAULT_POT_SOIL_KG * MAX_COMPOST_VOL_FRAC  # 2.5 kg


def raw_to_finished_compost(
    raw_blend: dict[str, Any],
    dry_yield: float = DEFAULT_DRY_YIELD,
    n_retention: float = DEFAULT_N_RETENTION,
    finished_moisture: float = DEFAULT_FINISHED_MOISTURE,
) -> dict[str, float]:
    """Transform raw feedstock mix stoichiometry into finished cured compost properties.

    During thermophilic composting, microbes respire 40-60% of initial dry matter
    as CO2. Non-volatile minerals (P, K) concentrate proportionally, while some
    nitrogen volatilizes as ammonia.

    Args:
        raw_blend: Output from blender.blend() with dry-basis n, p, k percentages.
        dry_yield: Fraction of initial dry mass remaining (default 0.50).
        n_retention: Fraction of initial total N retained (default 0.70).
        finished_moisture: Moisture % of finished cured compost (default 40.0%).

    Returns:
        Dictionary of finished compost nutrient percentages (both dry and wet basis).
    """
    raw_n_dry = float(raw_blend["n"])
    raw_p_dry = float(raw_blend["p"])
    raw_k_dry = float(raw_blend["k"])

    # Concentration of nutrients on dry basis
    fin_n_dry = (raw_n_dry * n_retention) / dry_yield
    fin_p_dry = (raw_p_dry * DEFAULT_MINERAL_RETENTION) / dry_yield
    fin_k_dry = (raw_k_dry * DEFAULT_MINERAL_RETENTION) / dry_yield

    # As-received (fresh / wet) percentages for the gardener
    fin_dry_frac = max(0.0, 1.0 - finished_moisture / 100.0)
    fin_n_fresh = fin_n_dry * fin_dry_frac
    fin_p_fresh = fin_p_dry * fin_dry_frac
    fin_k_fresh = fin_k_dry * fin_dry_frac

    return {
        "finished_n_dry_pct": round(fin_n_dry, 3),
        "finished_p_dry_pct": round(fin_p_dry, 3),
        "finished_k_dry_pct": round(fin_k_dry, 3),
        "finished_n_fresh_pct": round(fin_n_fresh, 3),
        "finished_p_fresh_pct": round(fin_p_fresh, 3),
        "finished_k_fresh_pct": round(fin_k_fresh, 3),
        "finished_moisture_pct": finished_moisture,
        "dry_mass_loss_pct": round((1.0 - dry_yield) * 100.0, 1),
    }


def calculate_crop_dose(
    crop_id: str,
    raw_blend: dict[str, Any],
    dose_fresh_g: float = 500.0,
    pots: int = 1,
) -> dict[str, Any]:
    """Calculate agronomic nutrient delivery, demand coverage, and safety ceilings.

    Args:
        crop_id: Identifier of target crop in CROP_DEMANDS.
        raw_blend: Output of blender.blend() for the recipe.
        dose_fresh_g: Proposed application of fresh cured compost (grams per pot).
        pots: Number of companion pots.

    Returns:
        Structured dosing report with NPK supply, coverage intervals, and ceiling checks.
    """
    crop_key = crop_id.strip().lower()
    if crop_key not in CROP_DEMANDS:
        raise KeyError(
            f"Crop '{crop_id}' not found in dosing catalog. Supported crops: {list(CROP_DEMANDS.keys())}"
        )
    demand = CROP_DEMANDS[crop_key]
    fin = raw_to_finished_compost(raw_blend)

    # Total elemental nutrient applied per pot in fresh compost (grams)
    # dose_fresh_g * fresh_pct / 100
    n_applied_total_g = dose_fresh_g * (fin["finished_n_fresh_pct"] / 100.0)
    p_applied_total_g = dose_fresh_g * (fin["finished_p_fresh_pct"] / 100.0)
    k_applied_total_g = dose_fresh_g * (fin["finished_k_fresh_pct"] / 100.0)

    # First-year available nutrient delivery
    n_avail_lo_g = n_applied_total_g * N_MIN_LO
    n_avail_hi_g = n_applied_total_g * N_MIN_HI
    p_avail_g = p_applied_total_g * P_AVAIL_RATE
    k_avail_g = k_applied_total_g * K_AVAIL_RATE

    # Percent of seasonal crop requirement met
    n_demand = demand["n_demand_g"]
    p_demand = demand["p_demand_g"]
    k_demand = demand["k_demand_g"]

    n_coverage_lo_pct = round((n_avail_lo_g / n_demand) * 100.0, 1) if n_demand > 0 else 0.0
    n_coverage_hi_pct = round((n_avail_hi_g / n_demand) * 100.0, 1) if n_demand > 0 else 0.0
    p_coverage_pct = round((p_avail_g / p_demand) * 100.0, 1) if p_demand > 0 else 0.0
    k_coverage_pct = round((k_avail_g / k_demand) * 100.0, 1) if k_demand > 0 else 0.0

    # Guardrail checks
    p_ceiling = demand["p_ceiling_g"]
    p_load_pass = p_applied_total_g <= p_ceiling
    vol_cap_pass = dose_fresh_g <= (MAX_COMPOST_FRESH_KG_PER_POT * 1000.0)

    # Monthly maintenance dosing rate
    season_months = max(1.0, demand["season_days"] / 30.0)
    monthly_dose_g = round(dose_fresh_g / season_months, 1)

    return {
        "crop_id": crop_key,
        "crop_name": demand["name"],
        "dose_per_pot_fresh_g": round(dose_fresh_g, 1),
        "monthly_dose_per_pot_g": monthly_dose_g,
        "total_batch_fresh_kg": round((dose_fresh_g * pots) / 1000.0, 2),
        "pots": pots,
        "nutrient_delivery": {
            "n_total_applied_g": round(n_applied_total_g, 2),
            "n_avail_year1_range_g": [round(n_avail_lo_g, 2), round(n_avail_hi_g, 2)],
            "n_demand_coverage_range_pct": [n_coverage_lo_pct, n_coverage_hi_pct],
            "p_avail_year1_g": round(p_avail_g, 2),
            "p_demand_coverage_pct": p_coverage_pct,
            "k_avail_year1_g": round(k_avail_g, 2),
            "k_demand_coverage_pct": k_coverage_pct,
        },
        "guardrails": {
            "p_seasonal_loading_g": round(p_applied_total_g, 2),
            "p_ceiling_g": p_ceiling,
            "p_loading_status": "PASS" if p_load_pass else "EXCEEDED_P_CEILING",
            "volume_fraction_pct": round((dose_fresh_g / (DEFAULT_POT_SOIL_KG * 1000.0)) * 100.0, 1),
            "volume_ceiling_pct": round(MAX_COMPOST_VOL_FRAC * 100.0, 1),
            "volume_status": "PASS" if vol_cap_pass else "EXCEEDED_SALINITY_LIMIT",
        },
        "honest_assessment": (
            f"At {dose_fresh_g:.0f}g/pot, compost covers approximately "
            f"{n_coverage_lo_pct:.0f}%–{n_coverage_hi_pct:.0f}% of seasonal nitrogen demand "
            f"(assuming 10–20% year-one organic mineralization). Compost functions as a "
            f"soil-building organic conditioner; supplementary organic amendments are "
            f"recommended for intensive fruit-bearing yields."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CompostMitra Crop Nutrient Dosing Calculator."
    )
    parser.add_argument(
        "--crop",
        default="tomato",
        help="Target crop identifier (e.g. tomato, spinach, rose, chilli)",
    )
    parser.add_argument(
        "--dose",
        type=float,
        default=500.0,
        help="Fresh compost dose in grams per pot (default 500g)",
    )
    parser.add_argument(
        "--pots",
        type=int,
        default=4,
        help="Number of companion pots (default 4)",
    )
    args = parser.parse_args()

    # Demo Cornell mix
    from scripts.blender import blend, load_catalog

    cat = load_catalog()
    raw_blend = blend({"dry_leaves": 0.239, "grass_clippings": 0.761}, cat)

    res = calculate_crop_dose(args.crop, raw_blend, dose_fresh_g=args.dose, pots=args.pots)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
