"""Unit tests for CompostMitra blender calculator and datacheck validator.

Covers at least 20 assertions verifying:
  1. Cornell 30:1 reference mix (dry_leaves=0.60, grass=0.40 -> 28-32 C/N)
  2. Weight sum precondition (sum != 1.0 +- 1e-6)
  3. Dry-basis C/N formula mathematical precision
  4. pH calculation and clamping [0.0, 14.0]
  5. Zero weights and empty input handling
  6. All-browns mix flagging
  7. Meat inclusion blocking
  8. Datacheck on good CSVs
  9. Datacheck rejection of 6 bad fixtures
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.blender import blend, cornell_check
from scripts.datacheck import check, check_file, collect_csv_files

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


# 1. Cornell 30:1 check
def test_cornell_reference_mix() -> None:
    mix = {"dry_leaves": 0.60, "grass": 0.40}
    result = blend(mix)

    # Assert 1: C/N is in optimal Cornell range [28.0, 32.0]
    assert 28.0 <= result["cn"] <= 32.0
    # Assert 2: C/N is approximately 30.4
    assert abs(result["cn"] - 30.39) < 0.1
    # Assert 3: Heuristic grade for optimal Cornell mix is GRADE_A
    assert result["heuristic_grade"] == "GRADE_A"
    # Assert 4: CLI helper exit code 0
    assert cornell_check() == 0
    # Assert 5: Moisture calculation is weighted average
    assert result["moist_pct"] == pytest.approx(0.60 * 20.0 + 0.40 * 75.0)


# 2. Weight sum error (sum != 1.0 +- 1e-6)
def test_weight_sum_validation() -> None:
    # Assert 6: Sum 0.99 raises ValueError
    with pytest.raises(ValueError, match=r"Sum of weights must equal 1\.0"):
        blend({"dry_leaves": 0.59, "grass": 0.40})

    # Assert 7: Sum 1.05 raises ValueError
    with pytest.raises(ValueError, match=r"Sum of weights must equal 1\.0"):
        blend({"dry_leaves": 0.65, "grass": 0.40})

    # Assert 8: Single weight 0.999 raises ValueError
    with pytest.raises(ValueError, match=r"Sum of weights must equal 1\.0"):
        blend({"dry_leaves": 0.999})

    # Assert 9: Negative weight raises ValueError
    with pytest.raises(ValueError, match=r"Negative weight not allowed"):
        blend({"dry_leaves": 1.1, "grass": -0.1})


# 3. Dry-basis C/N formula precision
def test_dry_basis_cn_formula_precision() -> None:
    # Test hand-computed exact values:
    # item_a: moist=20%, wet=100 -> dry=80, C=40 -> C_pct=50%, N=0.8 -> N_pct=1.0%
    # item_b: moist=50%, wet=100 -> dry=50, C=20 -> C_pct=40%, N=1.0 -> N_pct=2.0%
    # 50/50 mix:
    # sum_c_pct = 0.5 * 50 + 0.5 * 40 = 25 + 20 = 45.0
    # sum_n_pct = 0.5 * 1.0 + 0.5 * 2.0 = 0.5 + 1.0 = 1.5
    # expected_cn = 45.0 / 1.5 = 30.0
    custom_ingredients = {
        "item_a": {
            "name": "Item A",
            "group": "Brown",
            "C": 40.0,
            "N": 0.8,
            "moist_pct": 20.0,
            "dph": 0.0,
            "n": 1.0,
            "p": 0.5,
            "k": 0.5,
        },
        "item_b": {
            "name": "Item B",
            "group": "Green",
            "C": 20.0,
            "N": 1.0,
            "moist_pct": 50.0,
            "dph": 0.0,
            "n": 2.0,
            "p": 0.5,
            "k": 0.5,
        },
    }
    result = blend({"item_a": 0.5, "item_b": 0.5}, custom_ingredients)

    # Assert 10: Dry-basis C/N matches hand calculation exactly
    assert result["cn"] == 30.0
    # Assert 11: NPK matches weight average
    assert result["n"] == 1.5
    # Assert 12: Moisture is weighted average
    assert result["moist_pct"] == 35.0


# 4. pH calculation and clamping
def test_ph_calculation_and_clamping() -> None:
    # Assert 13: Linear heuristic formula matches 7.0 + sum(w_i * dph_i) * 0.35
    mix = {"dry_leaves": 0.60, "grass": 0.40}
    res = blend(mix)
    expected_ph = 7.0 + (0.60 * (-0.5) + 0.40 * 0.5) * 0.35
    assert abs(res["ph"] - expected_ph) < 0.01

    # Assert 14: Extreme acid dph clamped to 0.0
    extreme_acid = {
        "acid": {"name": "Acid", "group": "Green", "C": 10, "N": 1, "moist_pct": 10, "dph": -50.0}
    }
    res_acid = blend({"acid": 1.0}, extreme_acid)
    assert res_acid["ph"] == 0.0

    # Assert 15: Extreme base dph clamped to 14.0
    extreme_base = {
        "base": {"name": "Base", "group": "Brown", "C": 10, "N": 1, "moist_pct": 10, "dph": 50.0}
    }
    res_base = blend({"base": 1.0}, extreme_base)
    assert res_base["ph"] == 14.0


# 5. Zero weights / empty input
def test_zero_weights_and_empty_input() -> None:
    # Assert 16: Empty dictionary raises ValueError
    with pytest.raises(ValueError, match=r"Sum of weights must equal 1\.0"):
        blend({})

    # Assert 17: All-zero weights dictionary raises ValueError
    with pytest.raises(ValueError, match=r"Sum of weights must equal 1\.0"):
        blend({"dry_leaves": 0.0, "grass": 0.0})

    # Assert 18: Loading empty.json fixture raises ValueError
    with (FIXTURES_DIR / "empty.json").open("r", encoding="utf-8") as f:
        empty_data = json.load(f)
    with pytest.raises(ValueError):
        blend(empty_data)


# 6. All-browns mix flag/grade
def test_all_browns_mix_flag() -> None:
    with (FIXTURES_DIR / "all-browns.json").open("r", encoding="utf-8") as f:
        brown_mix = json.load(f)
    result = blend(brown_mix)

    # Assert 19: All-browns C/N is high (> 50)
    assert result["cn"] > 50.0
    # Assert 20: Heuristic grade flags all-browns condition
    assert result["heuristic_grade"] == "FLAG_ALL_BROWNS"


# 7. Meat inclusion flag
def test_meat_inclusion_flag() -> None:
    with (FIXTURES_DIR / "meat.json").open("r", encoding="utf-8") as f:
        meat_mix = json.load(f)
    result_pure_meat = blend(meat_mix)

    # Assert 21: Pure meat mix is blocked
    assert result_pure_meat["heuristic_grade"] == "BLOCKED_MEAT"

    # Assert 22: Recipe including even small fraction of meat is blocked
    result_mixed_meat = blend({"dry_leaves": 0.80, "grass": 0.15, "meat_scraps": 0.05})
    assert result_mixed_meat["heuristic_grade"] == "BLOCKED_MEAT"


# 8. Datacheck on good CSVs
def test_datacheck_on_good_csvs() -> None:
    good_ingredients_path = FIXTURES_DIR / "good" / "good_ingredients.csv"
    good_recipes_path = FIXTURES_DIR / "good" / "good_recipes.csv"

    df_ing = pd.read_csv(good_ingredients_path)
    df_rec = pd.read_csv(good_recipes_path)

    # Assert 23: Good ingredients DataFrame passes check()
    assert check(df_ing) is True
    # Assert 24: Good recipes DataFrame passes check()
    assert check(df_rec) is True
    # Assert 25: Good ingredients file check passes
    ok_ing, msg_ing = check_file(good_ingredients_path)
    assert ok_ing is True
    assert msg_ing == "OK"
    # Assert 26: Good recipes file check passes
    ok_rec, msg_rec = check_file(good_recipes_path)
    assert ok_rec is True


# 9. Datacheck rejection of 6 bad fixtures
def test_datacheck_rejection_of_6_bad_fixtures() -> None:
    bad_dir = FIXTURES_DIR / "bad"
    bad_files = collect_csv_files([str(bad_dir)])

    # Assert 27: Exactly 6 bad CSV fixtures exist in tests/fixtures/bad/
    assert len(bad_files) == 6

    # Asserts 28-33: Each of the 6 bad files is rejected
    expected_bad_stems = {
        "bad_cn",
        "bad_moist",
        "bad_npk",
        "bad_ph",
        "bad_schema",
        "bad_sum",
    }
    actual_stems = {f.stem for f in bad_files}
    assert actual_stems == expected_bad_stems

    for bad_file in bad_files:
        ok, msg = check_file(bad_file)
        assert ok is False, f"File {bad_file.name} was expected to fail validation"
