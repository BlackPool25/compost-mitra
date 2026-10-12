#!/usr/bin/env python3
"""CompostMitra Carbon & Methane Avoidance Ledger.

Calculates greenhouse gas (GHG) avoidance and environmental credits from diverting
organic waste from anaerobic landfills into managed aerobic composting.

Standards Grounding:
  1. IPCC 2006 Guidelines for National Greenhouse Gas Inventories, Vol 5 (Waste):
     - Chapter 3: First-Order Decay Landfill Methane Generation.
     - Chapter 4: Biological Treatment of Solid Waste (Fugitive CH4 and N2O factors).
  2. 2019 Refinement to the 2006 IPCC Guidelines.
  3. US EPA WARM v15 (Waste Reduction Model):
     - Compost Soil Carbon Sequestration Factor (humification credit).
     - Synthetic Mineral Fertilizer Displacement Equivalents.
  4. Global Warming Potentials (IPCC AR5 100-year horizon):
     - CH4 GWP = 28.0
     - N2O GWP = 265.0

Governance:
  - T1 REAL | LIT calc | D1 proxy
  - Verifiable calculations; zero causal claims.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Default IPCC Degradable Organic Carbon (DOC) wet-basis fractions
IPCC_DOC_DEFAULTS = {
    "food_waste": 0.15,      # Food waste / kitchen scraps (IPCC default: 0.15)
    "yard_waste": 0.20,      # Leaves, garden waste, green clippings (IPCC default: 0.20)
    "paper_cardboard": 0.40, # Paper, cardboard (IPCC default: 0.40)
    "wood_sawdust": 0.43,    # Sawdust, wood chips (IPCC default: 0.43)
    "general_organic": 0.18, # Mixed domestic biowaste
}

# Mapping of ingredient identifiers to DOC categories
FEEDSTOCK_DOC_MAP = {
    "vegetable_scraps": "food_waste",
    "fruit_waste": "food_waste",
    "banana_peel": "food_waste",
    "citrus_peels": "food_waste",
    "onion_peels": "food_waste",
    "apple_pomace": "food_waste",
    "bread_crusts": "food_waste",
    "cooked_rice": "food_waste",
    "tea_waste": "food_waste",
    "coffee_grounds": "food_waste",
    "eggshell": "food_waste",
    "grass_clippings": "yard_waste",
    "grass": "yard_waste",
    "flower_wastes": "yard_waste",
    "weeds_fresh": "yard_waste",
    "dry_leaves": "yard_waste",
    "pine_needles": "yard_waste",
    "straw": "yard_waste",
    "corn_cobs": "yard_waste",
    "peanut_shells": "yard_waste",
    "cardboard": "paper_cardboard",
    "newspaper": "paper_cardboard",
    "sawdust": "wood_sawdust",
    "wood_ash": "wood_sawdust",
    "coconut_coir": "wood_sawdust",
    "cow_dung": "general_organic",
}

# IPCC AR5 100-year Global Warming Potentials
GWP_CH4 = 28.0
GWP_N2O = 265.0

# Gasoline passenger vehicle emission benchmark: ~0.192 kg CO2e per km (EPA GHG Equivalencies)
KM_PER_KG_CO2E = 1.0 / 0.192
# Tree seedling sequestering carbon for 10 years: ~60 kg CO2e per urban tree
TREES_PER_KG_CO2E = 1.0 / 60.0


@dataclass
class CarbonLedgerEntry:
    """Outcome container for carbon and methane avoidance ledger."""

    total_waste_mass_kg: float
    finished_compost_mass_kg: float
    landfill_baseline_ch4_kg: float
    landfill_baseline_ghg_kg_co2e: float
    compost_fugitive_ghg_kg_co2e: float
    soil_carbon_sequestration_kg_co2e: float
    fertilizer_offset_kg_co2e: float
    net_ghg_avoided_kg_co2e: float
    net_ghg_avoided_tonnes_co2e: float
    equivalent_car_km_avoided: float
    equivalent_urban_trees_planted: float
    feedstock_breakdown: List[Dict[str, Any]] = field(default_factory=list)
    methodology_citation: str = (
        "IPCC 2006 Vol 5 Waste (First-Order Decay) + US EPA WARM v15 (Compost Humus Sequestration)"
    )
    tier_classification: str = "T1 REAL | LIT calc | D1 proxy"

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry into serializable dictionary."""
        return {
            "total_waste_mass_kg": round(self.total_waste_mass_kg, 2),
            "finished_compost_mass_kg": round(self.finished_compost_mass_kg, 2),
            "landfill_baseline_ch4_kg": round(self.landfill_baseline_ch4_kg, 3),
            "landfill_baseline_ghg_kg_co2e": round(self.landfill_baseline_ghg_kg_co2e, 2),
            "compost_fugitive_ghg_kg_co2e": round(self.compost_fugitive_ghg_kg_co2e, 2),
            "soil_carbon_sequestration_kg_co2e": round(
                self.soil_carbon_sequestration_kg_co2e, 2
            ),
            "fertilizer_offset_kg_co2e": round(self.fertilizer_offset_kg_co2e, 2),
            "net_ghg_avoided_kg_co2e": round(self.net_ghg_avoided_kg_co2e, 2),
            "net_ghg_avoided_tonnes_co2e": round(self.net_ghg_avoided_tonnes_co2e, 4),
            "equivalent_car_km_avoided": round(self.equivalent_car_km_avoided, 1),
            "equivalent_urban_trees_planted": round(self.equivalent_urban_trees_planted, 2),
            "feedstock_breakdown": self.feedstock_breakdown,
            "methodology_citation": self.methodology_citation,
            "tier_classification": self.tier_classification,
        }


def calculate_carbon_avoidance(
    feedstock_masses_kg: Dict[str, float],
    landfill_mcf: float = 0.80,
    landfill_gas_recovery: float = 0.0,
    topsoil_oxidation: float = 0.10,
    include_soil_sequestration: bool = True,
    include_fertilizer_offset: bool = True,
) -> CarbonLedgerEntry:
    """Calculate net GHG avoidance achieved by composting rather than landfilling.

    Mathematical Formulation:
      1. Landfill Methane Generation:
           CH4_gen = Mass_i * DOC_i * DOC_f * F * (16/12) * MCF * (1 - OX) * (1 - R)
         where:
           - DOC_f = 0.50 (dissimilated fraction)
           - F = 0.50 (fraction of CH4 in landfill gas)
           - 16/12 = molecular conversion ratio C to CH4
           - MCF = 0.80 (deep unmanaged landfill default)
           - OX = 0.10 (surface oxidation)
           - R = 0.0 (landfill gas recovery factor)

      2. Composting Fugitive Emissions (IPCC Table 4.1):
           Fugitive = Mass_tot * (0.004 kg CH4/kg * 28 + 0.0003 kg N2O/kg * 265)
                    = Mass_tot * (0.112 + 0.0795) kg CO2e

      3. Soil Organic Carbon Humus Credit (EPA WARM v15):
           Credit = Finished_mass * 0.20 kg CO2e / kg finished compost
           where Finished_mass = 0.50 * Mass_tot

      4. Net Avoided = Landfill_GHG - Fugitive + Soil_Credit + Fertilizer_Offset

    Args:
        feedstock_masses_kg: Dict mapping feedstock ID or name to wet mass in kg.
        landfill_mcf: Methane Correction Factor (0.4 shallow, 0.8 deep unmanaged, 1.0 managed).
        landfill_gas_recovery: Fraction of methane recovered (0.0 for open municipal dumps).
        topsoil_oxidation: Methanotrophic surface oxidation fraction (default 0.10).
        include_soil_sequestration: Whether to include EPA WARM soil carbon humus credit.
        include_fertilizer_offset: Whether to include displaced mineral fertilizer credit.

    Returns:
        CarbonLedgerEntry containing detailed audited GHG avoidance metrics.
    """
    total_mass = sum(m for m in feedstock_masses_kg.values() if m > 0)
    if total_mass <= 1e-6:
        raise ValueError("Total feedstock mass must exceed 0.0 kg.")

    doc_f = 0.50  # IPCC default dissimilated organic carbon
    f_ch4 = 0.50  # IPCC default methane ratio in biogas
    ratio_c_ch4 = 16.0 / 12.0  # C to CH4 molecular mass ratio

    total_ch4_kg = 0.0
    breakdown: List[Dict[str, Any]] = []

    for ing_id, mass in feedstock_masses_kg.items():
        if mass <= 0:
            continue
        cat_key = FEEDSTOCK_DOC_MAP.get(ing_id.lower(), "general_organic")
        doc_val = IPCC_DOC_DEFAULTS.get(cat_key, 0.18)

        # Baseline landfill CH4 production for this component
        ch4_component_kg = (
            mass
            * doc_val
            * doc_f
            * f_ch4
            * ratio_c_ch4
            * landfill_mcf
            * (1.0 - topsoil_oxidation)
            * (1.0 - landfill_gas_recovery)
        )
        total_ch4_kg += ch4_component_kg
        breakdown.append({
            "feedstock_id": ing_id,
            "mass_kg": round(mass, 2),
            "doc_category": cat_key,
            "doc_fraction": doc_val,
            "ch4_avoided_kg": round(ch4_component_kg, 4),
            "ghg_avoided_kg_co2e": round(ch4_component_kg * GWP_CH4, 3),
        })

    landfill_ghg_co2e = total_ch4_kg * GWP_CH4

    # Composting process fugitive emissions (IPCC Chapter 4, Table 4.1 defaults)
    # 4 g CH4 / kg wet mass + 0.3 g N2O / kg wet mass
    compost_fugitive_co2e = total_mass * (0.004 * GWP_CH4 + 0.0003 * GWP_N2O)

    # Finished compost yield (approx 50% mass reduction due to bio-oxidation & moisture loss)
    finished_compost_mass = total_mass * 0.50

    # Soil carbon sequestration credit (EPA WARM v15: 0.20 tCO2e / t finished compost = 0.20 kg/kg)
    soil_seq_co2e = (
        finished_compost_mass * 0.20 if include_soil_sequestration else 0.0
    )

    # Mineral fertilizer displacement credit:
    # Approx 1.2% N, 0.3% P, 0.8% K in finished compost, displacing synthetic N/P/K synthesis
    # Displaced emissions ~ 0.035 kg CO2e per kg finished compost
    fert_offset_co2e = (
        finished_compost_mass * 0.035 if include_fertilizer_offset else 0.0
    )

    net_avoided_co2e = (
        landfill_ghg_co2e
        - compost_fugitive_co2e
        + soil_seq_co2e
        + fert_offset_co2e
    )
    net_avoided_tonnes = net_avoided_co2e / 1000.0

    car_km = net_avoided_co2e * KM_PER_KG_CO2E
    trees = net_avoided_co2e * TREES_PER_KG_CO2E

    return CarbonLedgerEntry(
        total_waste_mass_kg=total_mass,
        finished_compost_mass_kg=finished_compost_mass,
        landfill_baseline_ch4_kg=total_ch4_kg,
        landfill_baseline_ghg_kg_co2e=landfill_ghg_co2e,
        compost_fugitive_ghg_kg_co2e=compost_fugitive_co2e,
        soil_carbon_sequestration_kg_co2e=soil_seq_co2e,
        fertilizer_offset_kg_co2e=fert_offset_co2e,
        net_ghg_avoided_kg_co2e=net_avoided_co2e,
        net_ghg_avoided_tonnes_co2e=net_avoided_tonnes,
        equivalent_car_km_avoided=car_km,
        equivalent_urban_trees_planted=trees,
        feedstock_breakdown=breakdown,
    )


def generate_esg_certificate(
    ledger_entry: CarbonLedgerEntry,
    organization_name: str = "Community Compost Mitra Project",
    batch_reference: str = "BATCH-2026-10",
) -> Dict[str, Any]:
    """Generate structured ESG verification certificate for audited compost batch."""
    issue_date = datetime.date.today().isoformat()
    return {
        "certificate_id": f"CM-ESG-{batch_reference}",
        "issue_date": issue_date,
        "beneficiary": organization_name,
        "total_organic_waste_diverted_kg": ledger_entry.total_waste_mass_kg,
        "finished_compost_produced_kg": ledger_entry.finished_compost_mass_kg,
        "net_ghg_avoided_kg_co2e": ledger_entry.net_ghg_avoided_kg_co2e,
        "net_ghg_avoided_tonnes_co2e": ledger_entry.net_ghg_avoided_tonnes_co2e,
        "environmental_equivalents": {
            "gasoline_car_distance_avoided_km": ledger_entry.equivalent_car_km_avoided,
            "urban_tree_seedlings_equivalent": ledger_entry.equivalent_urban_trees_planted,
        },
        "standards_compliance": {
            "un_ipcc_standard": "IPCC 2006 / 2019 Refinement Vol 5 Chapter 3 & 4",
            "us_epa_standard": "US EPA WARM v15 Solid Waste Model",
            "gwp_metric": "IPCC AR5 100-Year GWP (CH4=28, N2O=265)",
            "tier_footnote": ledger_entry.tier_classification,
        },
    }
