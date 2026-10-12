"""Unit tests for the IPCC Tier 2 / EPA WARM Carbon & Methane Avoidance Ledger.

Verifies:
1. First-order decay landfill methane emissions avoidance math against manual formulas.
2. Composting fugitive emission subtractions per IPCC Table 4.1.
3. Soil humus carbon sequestration credit per US EPA WARM v15.
4. Input validation and edge-case handling.
5. ESG certificate generation and tier footnote compliance.
"""

from __future__ import annotations

import pytest

from scripts.carbon_ledger import (
    calculate_carbon_avoidance,
    generate_esg_certificate,
)


class TestCarbonAvoidanceLedger:
    """Test suite for calculate_carbon_avoidance and generate_esg_certificate."""

    def test_single_feedstock_exact_hand_math(self):
        # 100 kg food waste: DOC=0.15, DOC_f=0.5, F=0.5, 16/12, MCF=0.8, OX=0.1
        # CH4 = 100 * 0.15 * 0.5 * 0.5 * (16/12) * 0.8 * 0.9 = 3.60 kg CH4
        # Baseline CO2e = 3.60 * 28.0 = 100.8 kg CO2e
        # Fugitive = 100 * (0.004 * 28 + 0.0003 * 265) = 19.15 kg CO2e
        # Finished mass = 50 kg
        # Soil sequestration = 50 * 0.20 = 10.0 kg CO2e
        # Fertilizer offset = 50 * 0.035 = 1.75 kg CO2e
        # Net avoided = 100.8 - 19.15 + 10.0 + 1.75 = 93.4 kg CO2e
        res = calculate_carbon_avoidance({"vegetable_scraps": 100.0})

        assert res.total_waste_mass_kg == 100.0
        assert res.finished_compost_mass_kg == 50.0
        assert res.landfill_baseline_ch4_kg == pytest.approx(3.60, abs=1e-3)
        assert res.landfill_baseline_ghg_kg_co2e == pytest.approx(100.80, abs=1e-2)
        assert res.compost_fugitive_ghg_kg_co2e == pytest.approx(19.15, abs=1e-2)
        assert res.soil_carbon_sequestration_kg_co2e == pytest.approx(10.0, abs=1e-2)
        assert res.net_ghg_avoided_kg_co2e == pytest.approx(93.40, abs=0.1)
        assert res.net_ghg_avoided_tonnes_co2e == pytest.approx(0.0934, abs=1e-3)

    def test_multi_feedstock_breakdown(self):
        wastes = {"vegetable_scraps": 30.0, "dry_leaves": 20.0, "cardboard": 10.0}
        res = calculate_carbon_avoidance(wastes)

        assert res.total_waste_mass_kg == 60.0
        assert len(res.feedstock_breakdown) == 3
        assert res.net_ghg_avoided_kg_co2e > 0.0
        assert res.equivalent_car_km_avoided > 100.0
        assert res.equivalent_urban_trees_planted > 0.5

    def test_zero_or_empty_mass_raises_value_error(self):
        with pytest.raises(ValueError, match="Total feedstock mass"):
            calculate_carbon_avoidance({"vegetable_scraps": 0.0})

        with pytest.raises(ValueError, match="Total feedstock mass"):
            calculate_carbon_avoidance({})

    def test_esg_certificate_structure(self):
        entry = calculate_carbon_avoidance({"fruit_waste": 50.0, "sawdust": 20.0})
        cert = generate_esg_certificate(entry, organization_name="Urban Green Garden")

        assert cert["certificate_id"].startswith("CM-ESG-")
        assert cert["beneficiary"] == "Urban Green Garden"
        assert cert["total_organic_waste_diverted_kg"] == 70.0
        assert cert["standards_compliance"]["tier_footnote"] == "T1 REAL | LIT calc | D1 proxy"
        assert "IPCC 2006" in cert["standards_compliance"]["un_ipcc_standard"]

    def test_optional_credits_toggle(self):
        base_res = calculate_carbon_avoidance(
            {"vegetable_scraps": 50.0},
            include_soil_sequestration=False,
            include_fertilizer_offset=False,
        )
        assert base_res.soil_carbon_sequestration_kg_co2e == 0.0
        assert base_res.fertilizer_offset_kg_co2e == 0.0
