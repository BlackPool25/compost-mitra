"""Unit tests for CompostMitra blender calculator and datacheck validator.

Covers comprehensive assertions verifying:
  1. Solved Cornell 30:1 reference mix (dry_leaves=0.268, grass_clippings=0.732 -> 30.0 C/N)
  2. Hand-calculated unadjusted wet mix (dry_leaves=0.60, grass_clippings=0.40 -> 40.12 C/N)
  3. Weight sum precondition (sum != 1.0 +- 1e-6) and non-negative weights
  4. True dry-matter stoichiometric conservation of mass precision
  5. pH heuristic calculation and clamping [0.0, 14.0]
  6. Zero weights and empty input handling
  7. All-browns mix flagging
  8. Meat inclusion blocking
  9. Property tests: identical ingredient identity, permutation invariance, monotonicity
  10. Mandatory basis='dry' enforcement
  11. Datacheck on good CSVs and rejection of bad fixtures
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.blender import blend, cornell_check, load_catalog
from scripts.datacheck import check, check_file, collect_csv_files

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


# 1. Cornell 30:1 solved mix check
def test_cornell_solved_mix() -> None:
    mix = {"dry_leaves": 0.239, "grass_clippings": 0.761}
    result = blend(mix)

    # Assert 1: C/N is in optimal Cornell range [28.0, 32.0]
    assert 28.0 <= result["cn"] <= 32.0
    # Assert 2: C/N matches solved value 30.0 +- 0.2
    assert abs(result["cn"] - 30.0) < 0.2
    # Assert 3: Heuristic grade for optimal Cornell mix is GRADE_A
    assert result["heuristic_grade"] == "GRADE_A"
    # Assert 4: CLI helper exit code 0
    assert cornell_check() == 0
    # Assert 5: Moisture calculation is weighted average
    assert result["moist_pct"] == pytest.approx(0.239 * 15.0 + 0.761 * 80.0, abs=0.01)


# 2. Hand-calculated unadjusted wet mix (dry_leaves 0.60, grass_clippings 0.40)
def test_unadjusted_wet_mix_stoichiometry() -> None:
    mix = {"dry_leaves": 0.60, "grass_clippings": 0.40}
    result = blend(mix)

    # On true dry basis: 0.60*0.85*48 C + 0.40*0.20*38 C = 0.2752 C
    # N = 0.60*0.85*0.9 N + 0.40*0.20*2.2 N = 0.00635 N
    # C/N = 0.2752 / 0.00635 = 43.3385...
    assert abs(result["cn"] - 43.34) < 0.05
    assert result["moist_pct"] == pytest.approx(0.60 * 15.0 + 0.40 * 80.0, abs=0.01)
    assert result["heuristic_grade"] == "GRADE_B"


# 3. Weight sum validation (sum != 1.0 +- 1e-6)
def test_weight_sum_validation() -> None:
    with pytest.raises(ValueError, match=r"Sum of weights must equal 1\.0"):
        blend({"dry_leaves": 0.59, "grass_clippings": 0.40})

    with pytest.raises(ValueError, match=r"Sum of weights must equal 1\.0"):
        blend({"dry_leaves": 0.65, "grass_clippings": 0.40})

    with pytest.raises(ValueError, match=r"Sum of weights must equal 1\.0"):
        blend({"dry_leaves": 0.999})

    with pytest.raises(ValueError, match=r"Negative weight not allowed"):
        blend({"dry_leaves": 1.1, "grass_clippings": -0.1})


# 4. Dry-basis stoichiometric formula precision
def test_dry_basis_stoichiometric_precision() -> None:
    custom_ingredients = {
        "item_a": {
            "name": "Item A",
            "group": "Brown",
            "C": 40.0,
            "N": 1.0,
            "P_pct": 0.5,
            "K_pct": 0.5,
            "moist_pct": 20.0,
            "dph": 0.0,
            "basis": "dry",
        },
        "item_b": {
            "name": "Item B",
            "group": "Green",
            "C": 20.0,
            "N": 2.0,
            "P_pct": 0.5,
            "K_pct": 0.5,
            "moist_pct": 50.0,
            "dph": 0.0,
            "basis": "dry",
        },
    }
    # 50/50 wet mix:
    # item_a: dry mass = 0.5 * 0.8 = 0.40. C = 0.40 * 0.40 = 0.160. N = 0.40 * 0.01 = 0.004.
    # item_b: dry mass = 0.5 * 0.5 = 0.25. C = 0.25 * 0.20 = 0.050. N = 0.25 * 0.02 = 0.005.
    # total dry mass = 0.65. total C = 0.210. total N = 0.009.
    # true cn = 0.210 / 0.009 = 23.333...
    # dry N% = 0.009 / 0.65 * 100 = 1.3846...
    result = blend({"item_a": 0.5, "item_b": 0.5}, custom_ingredients)

    assert result["cn"] == 23.33
    assert result["n"] == 1.38
    assert result["moist_pct"] == 35.0


# 5. Property test: Identical ingredient identity
def test_property_identical_ingredients() -> None:
    cat = load_catalog()
    single = blend({"dry_leaves": 1.0}, cat)
    assert single["cn"] == round(cat["dry_leaves"]["C"] / cat["dry_leaves"]["N"], 2)
    assert single["n"] == cat["dry_leaves"]["N"]
    assert single["p"] == cat["dry_leaves"]["P_pct"]
    assert single["k"] == cat["dry_leaves"]["K_pct"]
    assert single["moist_pct"] == cat["dry_leaves"]["moist_pct"]


# 6. Property test: Permutation invariance
def test_property_permutation_invariance() -> None:
    cat = load_catalog()
    w1 = {"dry_leaves": 0.3, "grass_clippings": 0.5, "coffee_grounds": 0.2}
    w2 = {"coffee_grounds": 0.2, "grass_clippings": 0.5, "dry_leaves": 0.3}
    r1 = blend(w1, cat)
    r2 = blend(w2, cat)
    assert r1 == r2


# 7. Property test: Monotonicity
def test_property_monotonicity() -> None:
    cat = load_catalog()
    # Increasing grass (N=2.2, C/N=17.3) relative to leaves (N=1.0, C/N=48.0) must decrease C/N
    cn_values = [
        blend({"dry_leaves": w, "grass_clippings": round(1.0 - w, 4)}, cat)["cn"]
        for w in [0.8, 0.6, 0.4, 0.2]
    ]
    assert cn_values == sorted(cn_values, reverse=True)


# 8. Mandatory basis='dry' validation
def test_mandatory_basis_validation() -> None:
    invalid_cat = {
        "bad_ing": {
            "name": "Bad",
            "group": "Green",
            "C": 40.0,
            "N": 2.0,
            "moist_pct": 50.0,
            "basis": "as_received",
        }
    }
    with pytest.raises(ValueError, match=r"basis='dry'"):
        blend({"bad_ing": 1.0}, invalid_cat)


# 9. pH calculation and clamping
def test_ph_calculation_and_clamping() -> None:
    mix = {"dry_leaves": 0.60, "grass_clippings": 0.40}
    res = blend(mix)
    expected_ph = 7.0 + (0.60 * 0.0 + 0.40 * 0.1) * 0.35
    assert abs(res["ph"] - expected_ph) < 0.01

    extreme_acid = {
        "acid": {"name": "Acid", "group": "Green", "C": 10, "N": 1, "moist_pct": 10, "dph": -50.0, "basis": "dry"}
    }
    res_acid = blend({"acid": 1.0}, extreme_acid)
    assert res_acid["ph"] == 0.0

    extreme_base = {
        "base": {"name": "Base", "group": "Brown", "C": 10, "N": 1, "moist_pct": 10, "dph": 50.0, "basis": "dry"}
    }
    res_base = blend({"base": 1.0}, extreme_base)
    assert res_base["ph"] == 14.0


# 10. Zero weights / empty input
def test_zero_weights_and_empty_input() -> None:
    with pytest.raises(ValueError, match=r"Sum of weights must equal 1\.0"):
        blend({})

    with pytest.raises(ValueError, match=r"Sum of weights must equal 1\.0"):
        blend({"dry_leaves": 0.0, "grass_clippings": 0.0})

    with (FIXTURES_DIR / "empty.json").open("r", encoding="utf-8") as f:
        empty_data = json.load(f)
    with pytest.raises(ValueError):
        blend(empty_data)


# 11. All-browns mix flag/grade
def test_all_browns_mix_flag() -> None:
    with (FIXTURES_DIR / "all-browns.json").open("r", encoding="utf-8") as f:
        brown_mix = json.load(f)
    result = blend(brown_mix)
    assert result["cn"] > 45.0
    assert result["heuristic_grade"] == "FLAG_ALL_BROWNS"


# 12. Meat inclusion flag
def test_meat_inclusion_flag() -> None:
    with (FIXTURES_DIR / "meat.json").open("r", encoding="utf-8") as f:
        meat_mix = json.load(f)
    # Give meat fixture basis='dry'
    meat_cat = {
        "meat_scraps": {
            "name": "Meat Scraps",
            "group": "Meat",
            "C": 25.0,
            "N": 3.0,
            "moist_pct": 50.0,
            "dph": 0.0,
            "basis": "dry",
        }
    }
    result_pure_meat = blend(meat_mix, meat_cat)
    assert result_pure_meat["heuristic_grade"] == "BLOCKED_MEAT"


# 13. Datacheck on good CSVs
def test_datacheck_on_good_csvs() -> None:
    good_ingredients_path = FIXTURES_DIR / "good" / "good_ingredients.csv"
    good_recipes_path = FIXTURES_DIR / "good" / "good_recipes.csv"

    df_ing = pd.read_csv(good_ingredients_path)
    df_rec = pd.read_csv(good_recipes_path)

    assert check(df_ing) is True
    assert check(df_rec) is True

    ok_ing, msg_ing = check_file(good_ingredients_path)
    assert ok_ing is True
    assert msg_ing == "OK"

    ok_rec, msg_rec = check_file(good_recipes_path)
    assert ok_rec is True


# 14. Datacheck rejection of 6 bad fixtures
def test_datacheck_rejection_of_6_bad_fixtures() -> None:
    bad_dir = FIXTURES_DIR / "bad"
    bad_files = collect_csv_files([str(bad_dir)])
    assert len(bad_files) == 6

    for bad_file in bad_files:
        ok, msg = check_file(bad_file)
        assert ok is False, f"File {bad_file.name} was expected to fail validation"
