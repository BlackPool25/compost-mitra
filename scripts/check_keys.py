#!/usr/bin/env python3
"""Contract key validator for CompostMitra.

Validates that JSON files conform strictly to the lower_snake contract keys
defined in docs/DATA_CONTRACT_v3.1.md. Rejects camelCase, PascalCase, and
unnormalized uppercase keys (e.g., pH, MC, CN, Temp).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Canonical allowed contract keys (all lower_snake)
CONTRACT_KEYS = {
    "cn",
    "ph",
    "moist_pct",
    "temp",
    "day",
    "nh3",
    "no3",
    "tn",
    "toc",
    "ec",
    "om",
    "n",
    "p",
    "k",
    "p_mature",
    "gi",
    "cn_pred",
    "shap",
    "conf",
    "heuristic_grade",
    "kg_mo",
    "rs_mo",
    "co2e",
    "recipe",
    "score",
    "status",
    "message",
    "id",
    "name",
    "group",
    "source",
    "batch_key",
}

# Mapping from non-standard / uppercase / camelCase keys to contract keys
KEY_MAPPINGS: dict[str, str] = {
    "C/N": "cn",
    "c/n": "cn",
    "CN": "cn",
    "pH": "ph",
    "PH": "ph",
    "MC": "moist_pct",
    "mc": "moist_pct",
    "moist": "moist_pct",
    "moisture": "moist_pct",
    "moisture_pct": "moist_pct",
    "moistPct": "moist_pct",
    "Temp": "temp",
    "TEMP": "temp",
    "temperature": "temp",
    "Day": "day",
    "DAY": "day",
    "NH3": "nh3",
    "nh3_mg_kg": "nh3",
    "NO3": "no3",
    "no3_mg_kg": "no3",
    "TN": "tn",
    "TOC": "toc",
    "EC": "ec",
    "OM": "om",
    "N": "n",
    "P": "p",
    "K": "k",
    "pMature": "p_mature",
    "PMature": "p_mature",
    "p_maturity": "p_mature",
    "cnPred": "cn_pred",
    "CN_pred": "cn_pred",
    "heuristicGrade": "heuristic_grade",
    "heuristic_Grade": "heuristic_grade",
    "confidence": "conf",
    "Conf": "conf",
    "GI": "gi",
    "SHAP": "shap",
}


def to_snake_case(s: str) -> str:
    """Convert camelCase or PascalCase string to lower_snake_case."""
    s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s2 = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s1)
    return s2.replace("-", "_").replace("/", "_").lower().strip("_")


def find_expected_key(key: str) -> str:
    """Determine expected contract key for an offending key."""
    if key in KEY_MAPPINGS:
        return KEY_MAPPINGS[key]
    snake = to_snake_case(key)
    if snake in KEY_MAPPINGS:
        return KEY_MAPPINGS[snake]
    if snake in CONTRACT_KEYS:
        return snake
    return snake


def is_valid_contract_key(key: str) -> bool:
    """Check if key is valid contract key in lower_snake format."""
    if key not in CONTRACT_KEYS:
        return False
    # Strict regex check for lower_snake: only lowercase letters, digits, and underscores
    return bool(re.match(r"^[a-z][a-z0-9_]*$", key))


def validate_object(data: Any, path: str = "") -> list[tuple[str, str, str]]:
    """Recursively validate keys in JSON object.

    Returns list of tuples: (key_path, offending_key, expected_key)
    """
    errors: list[tuple[str, str, str]] = []
    if isinstance(data, dict):
        for k, v in data.items():
            curr_path = f"{path}.{k}" if path else k
            if not is_valid_contract_key(k):
                expected = find_expected_key(k)
                errors.append((curr_path, k, expected))
            errors.extend(validate_object(v, curr_path))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            curr_path = f"{path}[{idx}]"
            errors.extend(validate_object(item, curr_path))
    return errors


def check_file(file_path: Path) -> list[tuple[str, str, str]]:
    """Parse JSON file and validate all keys."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return validate_object(data)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate that JSON keys strictly adhere to contract v3.1 lower_snake conventions."
    )
    parser.add_argument("files", nargs="+", help="JSON files to validate")
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Report violations as warnings without exiting with error code",
    )
    args = parser.parse_args()

    total_files = 0
    all_violations: list[tuple[str, str, str, str]] = []

    for file_pattern in args.files:
        p = Path(file_pattern)
        matched_files = [p] if p.exists() else list(Path().glob(file_pattern))
        if not matched_files and not p.exists():
            matched_files = [p]

        for file_path in matched_files:
            total_files += 1
            try:
                violations = check_file(file_path)
                for key_path, offending, expected in violations:
                    all_violations.append((str(file_path), key_path, offending, expected))
            except (json.JSONDecodeError, OSError) as e:
                print(f"ERROR: Failed reading {file_path}: {e}", file=sys.stderr)
                if not args.warn_only:
                    return 1

    if all_violations:
        prefix = "WARNING" if args.warn_only else "ERROR"
        print(
            f"{prefix}: Found {len(all_violations)} key-casing violation(s) across {total_files} file(s):",
            file=sys.stderr if not args.warn_only else sys.stdout,
        )
        for fpath, key_path, offending, expected in all_violations:
            msg = f"  - [{fpath}] Key '{offending}' (at {key_path}) violates contract. Expected contract key: '{expected}'"
            print(msg, file=sys.stderr if not args.warn_only else sys.stdout)

        if args.warn_only:
            print("WARN-ONLY mode active: not blocking.", file=sys.stdout)
            return 0
        return 1

    print(f"PASS: {total_files} file(s) checked. All keys strictly conform to contract v3.1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
