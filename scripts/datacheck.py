#!/usr/bin/env python3
"""CompostMitra Dataset & Schema Validator.

Validates datasets, plant tables, ingredient catalogs, and recipe mixtures
against the frozen contract rules defined in docs/DATA_CONTRACT_v3.1.md:
  - NPK values in [0.0, 10.0]
  - C/N dry ratio in [4.0, 150.0]
  - pH in [0.0, 14.0]
  - Weight sum Sigma w = 1.0 +- 1e-6
  - Moisture in [0.0, 100.0]
  - Supports --assert-zero-syn for verifying zero synthetic rows in target datasets
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


def check(df: pd.DataFrame, raise_on_error: bool = False) -> bool:
    """Validate DataFrame against contract v3.1 rules.

    Args:
        df: Input pandas DataFrame to validate.
        raise_on_error: If True, raises ValueError upon failure. If False, returns False.

    Returns:
        True if all contract constraints are satisfied, False otherwise.
    """
    if df is None or df.empty or len(df.columns) == 0:
        if raise_on_error:
            raise ValueError("DataFrame is empty or contains no columns")
        return False

    # 1. NPK check: macronutrients in range [0.0, 10.0]
    npk_cols = [
        c
        for c in df.columns
        if c.lower()
        in {
            "n",
            "p",
            "k",
            "tn",
            "n_pct",
            "p_pct",
            "k_pct",
            "n_lo",
            "n_hi",
            "p_lo",
            "p_hi",
            "k_lo",
            "k_hi",
        }
    ]
    for col in npk_cols:
        series = pd.to_numeric(df[col], errors="coerce")
        if series.isna().any():
            if raise_on_error:
                raise ValueError(f"Column '{col}' contains non-numeric or NaN values")
            return False
        if (series < -1e-6).any() or (series > 10.0 + 1e-6).any():
            if raise_on_error:
                raise ValueError(f"NPK column '{col}' has values outside [0.0, 10.0]")
            return False

    # 2. C/N check: ratio in range [4.0, 150.0]
    cn_cols = [
        c
        for c in df.columns
        if c.lower() in {"cn", "c/n", "c_n", "c_to_n", "c_per_n", "c/n dry ratio"}
    ]
    for col in cn_cols:
        series = pd.to_numeric(df[col], errors="coerce")
        if series.isna().any():
            if raise_on_error:
                raise ValueError(f"Column '{col}' contains non-numeric or NaN values")
            return False
        if (series < 4.0 - 1e-6).any() or (series > 150.0 + 1e-6).any():
            if raise_on_error:
                raise ValueError(f"C/N column '{col}' has values outside [4.0, 150.0]")
            return False

    # 3. pH check: pH in range [0.0, 14.0]
    ph_cols = [c for c in df.columns if c.lower() in {"ph", "ph_lo", "ph_hi"}]
    for col in ph_cols:
        series = pd.to_numeric(df[col], errors="coerce")
        if series.isna().any():
            if raise_on_error:
                raise ValueError(f"Column '{col}' contains non-numeric or NaN values")
            return False
        if (series < -1e-6).any() or (series > 14.0 + 1e-6).any():
            if raise_on_error:
                raise ValueError(f"pH column '{col}' has values outside [0.0, 14.0]")
            return False

    # 4. Moisture check: moisture percentage in range [0.0, 100.0]
    moist_cols = [
        c
        for c in df.columns
        if c.lower() in {"moist_pct", "mc", "moisture", "moisture_pct"}
    ]
    for col in moist_cols:
        series = pd.to_numeric(df[col], errors="coerce")
        if series.isna().any():
            if raise_on_error:
                raise ValueError(f"Column '{col}' contains non-numeric or NaN values")
            return False
        if (series < -1e-6).any() or (series > 100.0 + 1e-6).any():
            if raise_on_error:
                raise ValueError(f"Moisture column '{col}' has values outside [0.0, 100.0]")
            return False

    # 5. Weight sum check: Sigma w = 1.0 +- 1e-6
    # Look for explicit sum column
    sum_cols = [c for c in df.columns if c.lower() in {"sum_w", "weight_sum", "weights_sum", "w_sum"}]
    for col in sum_cols:
        series = pd.to_numeric(df[col], errors="coerce")
        if series.isna().any():
            if raise_on_error:
                raise ValueError(f"Weight sum column '{col}' contains non-numeric or NaN values")
            return False
        if ((series - 1.0).abs() > 1e-6).any():
            if raise_on_error:
                raise ValueError(f"Weight sum in '{col}' violates 1.0 +- 1e-6 tolerance")
            return False

    # Look for proportion columns starting with 'w_'
    prop_cols = [c for c in df.columns if c.startswith("w_") or c.startswith("w-")]
    if len(prop_cols) > 1:
        row_sums = pd.Series(0.0, index=df.index)
        for col in prop_cols:
            series = pd.to_numeric(df[col], errors="coerce")
            if series.isna().any():
                if raise_on_error:
                    raise ValueError(f"Proportion column '{col}' contains NaN/invalid numbers")
                return False
            row_sums += series
        if ((row_sums - 1.0).abs() > 1e-6).any():
            if raise_on_error:
                raise ValueError("Row proportions sum violates 1.0 +- 1e-6 tolerance")
            return False

    # Check for critical schema corrupted data (e.g. non-numeric in all standard columns)
    expected_numeric = [
        c
        for c in df.columns
        if c.lower()
        in {
            "c",
            "n",
            "temp",
            "day",
            "nh3",
            "no3",
            "toc",
            "ec",
            "om",
            "dph",
            "p_cap",
        }
    ]
    for col in expected_numeric:
        series = pd.to_numeric(df[col], errors="coerce")
        if series.isna().all() and len(df) > 0:
            if raise_on_error:
                raise ValueError(f"Expected numeric column '{col}' contains only invalid or NaN values")
            return False

    return True


def check_synthetic(df: pd.DataFrame) -> int:
    """Return count of synthetic rows found in DataFrame.

    Checks for 'Synthetic', 'synthetic', or 'is_synthetic' columns.
    """
    syn_cols = [c for c in df.columns if c.lower() in {"synthetic", "is_syn", "is_synthetic"}]
    count = 0
    for col in syn_cols:
        series = df[col]
        # Match 1, 1.0, '1', True, 'true', 'yes'
        matches = series.astype(str).str.lower().str.strip().isin({"1", "1.0", "true", "yes"})
        count += int(matches.sum())
    return count


def check_file(
    file_path: Path,
    assert_zero_syn: bool = False,
    raise_on_error: bool = False,
) -> tuple[bool, str]:
    """Validate a single CSV file.

    Returns:
        (is_valid, reason_message)
    """
    if not file_path.exists() or not file_path.is_file():
        msg = f"File not found: {file_path}"
        if raise_on_error:
            raise FileNotFoundError(msg)
        return False, msg

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        msg = f"Failed to parse CSV: {e}"
        if raise_on_error:
            raise ValueError(msg) from e
        return False, msg

    is_raw = "raw" in file_path.parts
    if is_raw:
        # Raw datasets have upstream external schemas (e.g. D1 soil kg/ha).
        # Contract ranges apply to clean data and recipe blend tables, not raw files.
        if assert_zero_syn:
            # Mullick 1314 is the published upstream ablation benchmark with intact Synthetic column.
            # Other raw datasets must have zero synthetic indicators.
            if file_path.name != "mullick_1314.csv":
                syn_count = check_synthetic(df)
                if syn_count > 0:
                    msg = f"Found {syn_count} synthetic rows in {file_path.name} (--assert-zero-syn active)"
                    if raise_on_error:
                        raise ValueError(msg)
                    return False, msg
        return True, "OK"

    if not check(df, raise_on_error=raise_on_error):
        return False, f"Contract validation failed for {file_path.name}"

    if assert_zero_syn:
        # Mullick 1314 is the published upstream ablation benchmark with intact Synthetic column.
        # Training datasets (Hafsa, Zhang, ingredients, plants) must have zero synthetic indicators.
        if file_path.name != "mullick_1314.csv":
            syn_count = check_synthetic(df)
            if syn_count > 0:
                msg = f"Found {syn_count} synthetic rows in {file_path.name} (--assert-zero-syn active)"
                if raise_on_error:
                    raise ValueError(msg)
                return False, msg

    return True, "OK"


def collect_csv_files(paths: list[str]) -> list[Path]:
    """Resolve files and directory paths to a sorted list of CSV Paths."""
    collected: set[Path] = set()
    for p_str in paths:
        p = Path(p_str)
        if "*" in p_str or "?" in p_str:
            parent = p.parent if p.parent != Path("") else Path(".")
            pattern = p.name
            if parent.exists():
                for matched in parent.glob(pattern):
                    if matched.is_file() and matched.suffix.lower() == ".csv":
                        collected.add(matched.resolve())
        elif p.exists():
            if p.is_file() and p.suffix.lower() == ".csv":
                collected.add(p.resolve())
            elif p.is_dir():
                for sub in p.glob("**/*.csv"):
                    if sub.is_file():
                        # When scanning data/ root directory, skip uncleaned raw datasets
                        if p.name == "data" and "raw" in sub.parts:
                            continue
                        collected.add(sub.resolve())
    return sorted(collected)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CompostMitra contract validator for CSV datasets and catalogs."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Run strict contract validation across provided datasets",
    )
    parser.add_argument(
        "--assert-zero-syn",
        action="store_true",
        help="Enforce zero synthetic rows in target datasets",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories containing CSV files to validate",
    )
    args = parser.parse_args()

    input_paths = args.paths
    if not input_paths:
        # Default to validating data/ directory if it contains CSVs
        default_dir = Path("data")
        if default_dir.exists():
            input_paths = [str(default_dir)]
        else:
            print("PASS: No input files provided and data/ not present. (rejected=0)")
            return 0

    csv_files = collect_csv_files(input_paths)
    if not csv_files:
        print("PASS: No CSV files found in provided path(s). (rejected=0)")
        return 0

    rejected_count = 0
    total_files = len(csv_files)
    rejection_reasons: list[str] = []

    for f in csv_files:
        ok, reason = check_file(f, assert_zero_syn=args.assert_zero_syn)
        if not ok:
            rejected_count += 1
            rejection_reasons.append(f"  - [{f.name}] {reason}")

    if rejected_count > 0:
        print(f"FAILED: rejected={rejected_count} ({rejected_count}/{total_files} files failed validation):", file=sys.stderr)
        for r in rejection_reasons:
            print(r, file=sys.stderr)
        return 1

    print(f"PASS: {total_files} file(s) checked, 0 rejected. (rejected=0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
