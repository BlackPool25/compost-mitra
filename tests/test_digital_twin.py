"""Unit tests for the Biophysical Kinetic Digital Twin simulation engine.

Verifies:
1. Coupled ODE integration stability and realistic biological trajectories.
2. Peak temperature thermophilic rise (> 50°C) for well-insulated piles.
3. Temperature inhibition sensitivity under poor insulation or extreme moisture.
4. US EPA 503 PFRP pathogen destruction compliance determination.
5. Error bounds and input parameter validation.
6. Serialization and Plotly figure generation.
"""

from __future__ import annotations

import numpy as np
import pytest

from scripts.kinetic_digital_twin import (
    build_digital_twin_figure,
    simulate_composting_pile,
)


class TestDigitalTwinSimulation:
    """Test suite for simulate_composting_pile."""

    def test_standard_pile_simulation(self):
        res = simulate_composting_pile(
            initial_wet_mass_kg=25.0,
            initial_moisture_pct=58.0,
            duration_days=30.0,
            insulation_level="moderate",
        )

        assert res.max_temperature_c > 50.0
        assert len(res.days) > 100
        assert res.days[0] == 0.0
        assert res.days[-1] == 30.0
        assert res.consecutive_days_above_55c >= 0.0
        assert res.stabilization_day > 5
        assert res.cumulative_co2_kg[-1] > 0.0

    def test_insulation_impact_on_peak_temp(self):
        # Higher insulation retains more biological metabolic heat
        res_high = simulate_composting_pile(
            initial_wet_mass_kg=30.0,
            initial_moisture_pct=58.0,
            insulation_level="high",
        )
        res_low = simulate_composting_pile(
            initial_wet_mass_kg=30.0,
            initial_moisture_pct=58.0,
            insulation_level="low",
        )

        assert res_high.max_temperature_c > res_low.max_temperature_c

    def test_pfrp_pathogen_destruction_check(self):
        res = simulate_composting_pile(
            initial_wet_mass_kg=40.0,
            initial_moisture_pct=55.0,
            insulation_level="high",
            duration_days=35.0,
        )

        # Insulated batch achieves EPA PFRP threshold
        assert res.consecutive_days_above_55c >= 3.0
        assert res.pfrp_compliant is True
        assert res.pathogen_log_reduction[-1] >= 4.0

    def test_invalid_parameters_raise_value_error(self):
        with pytest.raises(ValueError, match="Initial wet mass"):
            simulate_composting_pile(initial_wet_mass_kg=0.05)

        with pytest.raises(ValueError, match="Initial moisture percentage"):
            simulate_composting_pile(initial_moisture_pct=95.0)

    def test_to_dict_serialization(self):
        res = simulate_composting_pile(initial_wet_mass_kg=15.0, duration_days=20.0)
        d = res.to_dict()

        expected_keys = {
            "max_temperature_c",
            "days_above_55c",
            "consecutive_days_above_55c",
            "pfrp_compliant",
            "stabilization_day",
            "final_temperature_c",
            "final_moisture_pct",
            "total_bvs_degraded_pct",
            "cumulative_co2_kg",
            "pathogen_log_reduction",
            "metadata",
        }
        assert expected_keys.issubset(set(d.keys()))

    def test_plotly_figure_generation(self):
        res = simulate_composting_pile(initial_wet_mass_kg=20.0, duration_days=25.0)
        fig = build_digital_twin_figure(res)

        assert fig is not None
        assert len(fig.data) >= 2
        assert "Biophysical Kinetic Digital Twin" in fig.layout.title.text
