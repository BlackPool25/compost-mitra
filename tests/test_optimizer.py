"""Unit tests for scripts/optimize.py contract (match/optimize/loo/benefits).

Statistical association only; observational proxy data (sanity check, not proof).
"""

from __future__ import annotations

import re

import pytest

from scripts.optimize import (
    CITRUS_MAX_FRAC,
    benefits,
    load_plant_needs,
    loo,
    match,
    optimize,
)

NEEDS = load_plant_needs("tomato")

POOL = {
    "vegetable_scraps": 2.0,
    "coffee_grounds": 0.5,
    "banana_peel": 1.0,
    "dry_leaves": 3.0,
    "newspaper": 1.0,
    "straw": 1.0,
}

LOWER_SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")


def _near_band_compost() -> dict:
    return {
        "n": 1.95,
        "p": 0.55,
        "k": 1.8,
        "ph": 6.4,
        "cn": 28.0,
        "heuristic_grade": "GRADE_A",
    }


def test_match_returns_unit_interval() -> None:
    far = {"n": 5.0, "p": 3.0, "k": 5.0, "ph": 4.0, "cn": 60.0,
           "heuristic_grade": "GRADE_C"}
    blocked = {"n": 6.0, "p": 1.0, "k": 0.5, "ph": 7.0, "cn": 10.0,
               "heuristic_grade": "BLOCKED_MEAT"}
    for compost in (_near_band_compost(), far, blocked):
        score = match(NEEDS, compost)
        assert 0.0 <= score <= 1.0


def test_match_blocked_meat_scores_zero() -> None:
    compost = {"n": 6.0, "p": 1.0, "k": 0.5, "ph": 7.0, "cn": 10.0,
               "heuristic_grade": "BLOCKED_MEAT"}
    assert match(NEEDS, compost) == 0.0


def test_match_near_band_beats_far_blend() -> None:
    far = {"n": 5.0, "p": 3.0, "k": 5.0, "ph": 4.0, "cn": 60.0,
           "heuristic_grade": "GRADE_C"}
    near_score = match(NEEDS, _near_band_compost())
    assert near_score > 0.0
    assert near_score > match(NEEDS, far)


def test_optimize_returns_top3() -> None:
    results = optimize(NEEDS, POOL, k=3)
    assert len(results) == 3


def test_optimize_is_deterministic() -> None:
    first = optimize(NEEDS, POOL, k=3)
    second = optimize(NEEDS, POOL, k=3)
    assert first == second


def test_optimize_weights_sum_to_one_and_ranked() -> None:
    results = optimize(NEEDS, POOL, k=3)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)
    for res in results:
        assert abs(sum(res["recipe"].values()) - 1.0) <= 1e-6
        assert all(w > 0.0 for w in res["recipe"].values())
        assert set(res) == {"recipe", "score", "cn", "n", "p", "k",
                            "moist_pct", "ph", "heuristic_grade"}


def test_optimize_respects_citrus_bound_and_no_meat() -> None:
    pool = dict(POOL)
    pool["citrus_peels"] = 4.0
    pool["meat_scraps"] = 5.0
    for res in optimize(NEEDS, pool, k=3):
        for ing_id, weight in res["recipe"].items():
            assert "meat" not in ing_id.lower()
            if "citrus" in ing_id.lower():
                assert weight <= CITRUS_MAX_FRAC + 1e-9


def test_meat_only_pool_rejected() -> None:
    with pytest.raises(ValueError):
        optimize(NEEDS, {"meat_scraps": 2.0}, k=3)


def test_loo_nonzero_and_sorted() -> None:
    top1 = optimize(NEEDS, POOL, k=3)[0]
    deltas = loo(top1, NEEDS)
    assert len(deltas) >= 1
    assert any(d != 0.0 for _, d in deltas)
    assert [d for _, d in deltas] == sorted([d for _, d in deltas],
                                            reverse=True)


def test_benefits_keys_and_factors() -> None:
    top1 = dict(optimize(NEEDS, POOL, k=3)[0])
    top1["total_waste_kg"] = 7.0
    top1["pots"] = 5
    ben = benefits(top1)
    assert set(ben) == {"kg_mo", "rs_mo", "co2e"}
    assert ben["kg_mo"] == pytest.approx(max(7.0 * 4.0, 5 * 0.5 * 2.2), abs=0.05)
    assert ben["rs_mo"] == pytest.approx(ben["kg_mo"] * 22.5, abs=0.6)
    assert ben["co2e"] == pytest.approx(ben["kg_mo"] * 0.45, abs=0.05)


def test_result_keys_are_lower_snake() -> None:
    for res in optimize(NEEDS, POOL, k=3):
        assert all(LOWER_SNAKE.match(k) for k in res)
        assert all(LOWER_SNAKE.match(k) for k in res["recipe"])
        assert all(LOWER_SNAKE.match(k) for k in benefits(res))
