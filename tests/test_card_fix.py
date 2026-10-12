"""Regression tests for the Step-3 triple fix (render unity + raw score + cap).

Statistical association only; proxy sanity markers adjacent to numbers.
"""

from __future__ import annotations

import inspect
import re

import pytest
from test_frontend_wiring import app

from scripts.optimize import (
    MAX_SINGLE_WEIGHT,
    _cap_single_weight,
    load_plant_needs,
    match,
    match_raw,
    optimize,
    score_breakdown,
)

LOWER_SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")
TAG = "(proxy sanity, not proof)"
NEEDS = load_plant_needs("tomato")
TINY_POOL = {"dry_leaves": 3.0, "grass_clippings": 1.5}
TRIO_POOL = {
    "dry_leaves": 3.0,
    "grass_clippings": 1.5,
    "coffee_grounds": 0.5,
}


def _live_cards() -> list[dict]:
    results = optimize(NEEDS, TRIO_POOL, k=3)
    cards = []
    for i, res in enumerate(results):
        mat = app._live_maturity(res)
        cell = app._card_score_cell(NEEDS, res)
        cards.append(
            {
                "card_id": f"recipe-card-{i + 1}",
                "title": f"Recipe {i + 1}: Live Optimizer Blend",
                "grade": res.get("heuristic_grade", "GRADE_B"),
                "cn": res.get("cn", 28.0),
                "moist": res.get("moist_pct", 55.0),
                "ph": res.get("ph", 6.8),
                "npk": f"{res.get('n', 0.0)}% - {res.get('p', 0.0)}% - "
                f"{res.get('k', 0.0)}%",
                "maturity": cell["score_text"],
                "maturity_label": "Match Score",
                "why_text": cell["why_text"],
                "p_mature": mat.get("p_mature", 0.0),
                "p_mature_note": mat.get("p_mature_note", TAG),
                "raw_score": cell["raw_score"],
                "warns": app._render_warns(res),
                "is_best": i == 0,
            }
        )
    return cards


def test_all_cards_share_single_renderer() -> None:
    cards = _live_cards()
    assert len(cards) == 3
    rendered = [app._recipe_card_html(c) for c in cards]
    for html, card in zip(rendered, cards):
        assert card["card_id"] in html
        assert card["title"] in html
        assert "recipe-card eco-card" in html
        assert "grade-badge" in html
    bodies = [re.sub(r"Recipe \d[^<]*", "TITLE", h) for h in rendered]
    markers = ["C/N Ratio", "Moisture", "pH Approx.", "N - P - K"]
    for body in bodies:
        for marker in markers:
            assert marker in body


def test_no_escaped_html_in_cards() -> None:
    for card in _live_cards():
        html = app._recipe_card_html(card)
        assert "&lt;" not in html
        assert "&gt;" not in html
        assert "<div" in html


def test_p_mature_caption_inside_card() -> None:
    for card in _live_cards():
        html = app._recipe_card_html(card)
        assert "P(mature)" in html
        assert TAG in html
        assert html.index("P(mature)") > html.index("recipe-card")
    mock_card = {"card_id": "recipe-card-9", "title": "Mock", "is_best": False}
    assert "P(mature)" not in app._recipe_card_html(mock_card)


def test_score_cell_contains_raw_and_why() -> None:
    res = optimize(NEEDS, TINY_POOL, k=3)[0]
    cell = app._card_score_cell(NEEDS, res)
    assert set(cell) == {"score_text", "why_text", "raw_score"}
    assert "(raw " in cell["score_text"]
    assert f"{match(NEEDS, res):.4f}" in cell["score_text"]
    assert abs(cell["raw_score"] - match_raw(NEEDS, res)) < 1e-9
    assert cell["why_text"].startswith("top penalty: ")


def test_clamped_zero_still_shows_raw() -> None:
    far = {
        "n": 5.0, "p": 3.0, "k": 5.0, "ph": 4.0, "cn": 60.0,
        "moist_pct": 80.0, "score": 0.0,
        "heuristic_grade": "GRADE_C",
    }
    cell = app._card_score_cell(NEEDS, far)
    assert cell["score_text"].startswith("0.0000 (raw ")
    assert cell["raw_score"] < 0.0
    html = app._recipe_card_html(
        {"card_id": "c", "title": "t", "maturity": cell["score_text"],
         "why_text": cell["why_text"], "is_best": False}
    )
    assert cell["score_text"] in html
    assert cell["why_text"] in html


def test_breakdown_raw_matches_match_raw() -> None:
    res = optimize(NEEDS, TINY_POOL, k=3)[0]
    breakdown = score_breakdown(NEEDS, res)
    assert abs(breakdown["raw_score"] - match_raw(NEEDS, res)) < 1e-9
    assert all(LOWER_SNAKE.match(k) for k in breakdown)
    assert all(LOWER_SNAKE.match(k) for k in breakdown["penalties"])


def test_max_weight_cap_on_tiny_pool() -> None:
    assert MAX_SINGLE_WEIGHT == 0.80
    results = optimize(NEEDS, TINY_POOL, k=3)
    assert len(results) >= 1
    for res in results:
        assert max(res["recipe"].values()) <= 0.80 + 1e-9
        assert abs(sum(res["recipe"].values()) - 1.0) <= 1e-6


def test_cap_helper_redistributes_proportionally() -> None:
    out = _cap_single_weight({"dry_leaves": 0.9, "grass_clippings": 0.1})
    assert out["dry_leaves"] == pytest.approx(0.80)
    assert out["grass_clippings"] == pytest.approx(0.20)
    out = _cap_single_weight(
        {"a_green": 0.85, "b_brown": 0.10, "c_brown": 0.05}
    )
    assert out["a_green"] == 0.80
    assert out["b_brown"] == pytest.approx(0.10 + 0.05 * (0.10 / 0.15))
    assert abs(sum(out.values()) - 1.0) <= 1e-6
    calm = {"a_green": 0.5, "b_brown": 0.5}
    assert _cap_single_weight(calm) == calm
    assert _cap_single_weight({"only_one": 1.0}) == {"only_one": 1.0}


def test_cap_holds_across_pools_and_stays_deterministic() -> None:
    pools = [
        TINY_POOL,
        {"vegetable_scraps": 2.0, "coffee_grounds": 0.5, "dry_leaves": 3.0},
        {"vegetable_scraps": 2.0, "coffee_grounds": 0.5, "banana_peel": 1.0,
         "dry_leaves": 3.0, "newspaper": 1.0, "straw": 1.0},
    ]
    for pool in pools:
        first = optimize(NEEDS, pool, k=3)
        second = optimize(NEEDS, pool, k=3)
        assert first == second
        scores = [r["score"] for r in first]
        assert scores == sorted(scores, reverse=True)
        for res in first:
            assert max(res["recipe"].values()) <= 0.80 + 1e-9
            assert abs(sum(res["recipe"].values()) - 1.0) <= 1e-6


def test_new_helpers_pure_tagged_lower_snake() -> None:
    for fn in (app._card_score_cell, app._recipe_card_html):
        src = inspect.getsource(fn)
        assert "streamlit" not in src
        assert "st.markdown" not in src
        assert "st.caption" not in src
        assert "st.write" not in src
        assert "session_state" not in src
    res = optimize(NEEDS, TINY_POOL, k=3)[0]
    cell = app._card_score_cell(NEEDS, res)
    assert all(LOWER_SNAKE.match(k) for k in cell)
    assert TAG in app._recipe_card_html(_live_cards()[0])
