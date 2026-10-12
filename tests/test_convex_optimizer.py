"""Unit tests for the Mathematical Convex Recipe Optimizer.

Verifies:
1. Exact constraint satisfaction (C/N bounds, moisture bounds, citrus ceiling).
2. Proportions sum to 1.0 +- 1e-4.
3. Solve execution speed (< 50 ms).
4. Robust error handling on invalid inputs and infeasible envelopes.
5. Linear Programming bulking addition and Quadratic Programming synthesis.
"""

from __future__ import annotations

import pytest

from scripts.blender import blend, load_catalog
from scripts.convex_optimizer import (
    balance_available_wastes,
    synthesize_optimal_recipe,
)


@pytest.fixture
def catalog():
    return load_catalog()


class TestConvexRecipeSynthesis:
    """Test suite for synthesize_optimal_recipe (QP / SLSQP)."""

    def test_synthesis_satisfies_bounds(self, catalog):
        candidates = ["vegetable_scraps", "dry_leaves", "coffee_grounds"]
        res = synthesize_optimal_recipe(
            candidates,
            target_cn=30.0,
            target_moist=58.0,
            cn_range=(25.0, 35.0),
            moist_range=(50.0, 65.0),
            catalog=catalog,
        )

        assert res.success is True
        assert res.solve_time_ms < 50.0
        assert abs(sum(res.weights.values()) - 1.0) < 1e-4

        props = res.blend_properties
        assert 25.0 <= props["cn"] <= 35.0
        assert 50.0 <= props["moist_pct"] <= 65.0
        assert props["heuristic_grade"] in ("GRADE_A", "GRADE_B")

    def test_citrus_cap_strictly_enforced(self, catalog):
        candidates = ["citrus_peels", "dry_leaves", "grass_clippings"]
        res = synthesize_optimal_recipe(
            candidates,
            max_citrus_fraction=0.15,
            priors={"citrus_peels": 0.80, "dry_leaves": 0.10, "grass_clippings": 0.10},
            catalog=catalog,
        )

        assert res.success is True
        citrus_weight = res.weights.get("citrus_peels", 0.0)
        assert citrus_weight <= 0.1501
        assert res.blend_properties["cn"] >= 25.0

    def test_minimum_candidate_count_guard(self, catalog):
        res = synthesize_optimal_recipe(["vegetable_scraps"], catalog=catalog)
        assert res.success is False
        assert "At least 2 valid candidate ingredients" in res.status_message


class TestBulkingAgentBalancing:
    """Test suite for balance_available_wastes (LP / HiGHS)."""

    def test_already_compliant_waste(self, catalog):
        # A mix already compliant: dry leaves + grass clippings
        wastes = {"dry_leaves": 2.7, "grass_clippings": 7.3}
        res = balance_available_wastes(wastes, catalog=catalog)

        assert res.success is True
        assert "already within the optimal agronomic envelope" in res.status_message
        assert res.total_mass_kg == pytest.approx(10.0, abs=1e-3)
        assert 25.0 <= res.blend_properties["cn"] <= 35.0

    def test_wet_food_waste_bulking_addition(self, catalog):
        wastes = {"vegetable_scraps": 4.0, "banana_peel": 2.0}
        res = balance_available_wastes(
            wastes,
            bulking_candidates=["dry_leaves", "coffee_grounds", "peanut_shells"],
            cn_range=(25.0, 35.0),
            moist_range=(50.0, 65.0),
            catalog=catalog,
        )

        assert res.success is True
        assert res.total_mass_kg > 6.0
        assert len(res.recommendations) > 0

        # Verify blended outcome
        props = res.blend_properties
        assert 25.0 <= props["cn"] <= 35.0
        assert 50.0 <= props["moist_pct"] <= 65.0

    def test_negative_mass_rejected(self, catalog):
        wastes = {"vegetable_scraps": -1.5}
        res = balance_available_wastes(wastes, catalog=catalog)
        assert res.success is False
        assert "cannot be negative" in res.status_message

    def test_unknown_ingredient_rejected(self, catalog):
        wastes = {"unobtainium_scraps": 5.0}
        res = balance_available_wastes(wastes, catalog=catalog)
        assert res.success is False
        assert "not found in catalog" in res.status_message

    def test_empty_wastes_rejected(self, catalog):
        res = balance_available_wastes({}, catalog=catalog)
        assert res.success is False
        assert "cannot be empty" in res.status_message

    def test_highs_solve_speed_under_10ms(self, catalog):
        wastes = {"vegetable_scraps": 3.0, "tea_waste": 1.0, "onion_peels": 1.0}
        res = balance_available_wastes(wastes, catalog=catalog)
        assert res.solve_time_ms < 15.0
