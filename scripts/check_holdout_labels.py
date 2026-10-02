#!/usr/bin/env python3
"""Validator script checking holdout and report documents for required sanity/proxy labeling.

Constraint 5 rule:
Every holdout/report number must carry 'sanity, not proof' (or 'sanity' | 'proxy' | 'not proof')
adjacent to the number in the same line or paragraph.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

REQUIRED_MARKERS = ["sanity, not proof", "sanity", "proxy", "not proof"]
MARKER_REGEX = re.compile(
    r"(?:sanity,\s*not\s*proof|sanity|proxy|not\s*proof)", re.IGNORECASE
)

# Regex to detect numerical claims, performance metrics, percentages, or ratios
METRIC_NUMBER_REGEX = re.compile(
    r"(?:\b\d+(?:\.\d+)?\s*(?:%|pp|kg|₹|mS/cm|mg/kg)\b|\b(?:accuracy|acc|f1|score|r2|r²|drop|precision|recall|loss|mae|rmse|oob|baseline|gi)\s*[:=~]\s*\d+(?:\.\d+)?|\b\d+\.\d+\b)",
    re.IGNORECASE,
)

# Ignored numerical patterns like section headers, markdown tables dividers, dates, versions
HEADER_OR_DATE_REGEX = re.compile(
    r"^(?:#+|\d+\.|\s*[-*]\s*ADR|\s*\|\s*[-:]+\s*\||\d{4}-\d{2}-\d{2}|v\d+\.\d+)",
    re.IGNORECASE,
)


def check_paragraph_labels(text: str, file_path: Path) -> List[Tuple[int, str, str]]:
    """Check paragraphs in a markdown or text document for metric numbers and required labeling."""
    violations: List[Tuple[int, str, str]] = []
    lines = text.splitlines()

    # Group into paragraphs (blocks separated by empty lines)
    paragraph_lines: List[Tuple[int, str]] = []

    def evaluate_paragraph(p_lines: List[Tuple[int, str]]) -> None:
        if not p_lines:
            return
        p_text = " ".join(line for _, line in p_lines).strip()
        first_line_num = p_lines[0][0]

        # Check if this paragraph contains a metric or holdout number
        has_metric = bool(METRIC_NUMBER_REGEX.search(p_text))
        if has_metric:
            # Check if required sanity / proxy marker is present
            if not MARKER_REGEX.search(p_text):
                metric_match = METRIC_NUMBER_REGEX.search(p_text)
                found_metric = metric_match.group(0) if metric_match else "number"
                violations.append(
                    (
                        first_line_num,
                        found_metric,
                        f"Holdout/report claim '{found_metric}' missing adjacent sanity/proxy marker in paragraph: '{p_text[:80]}...'",
                    )
                )

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            evaluate_paragraph(paragraph_lines)
            paragraph_lines = []
        else:
            paragraph_lines.append((idx, stripped))

    evaluate_paragraph(paragraph_lines)
    return violations


def check_holdout_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Validate a single holdout file."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [(0, "FILE_READ_ERROR", f"Failed to read {file_path}: {exc}")]

    return check_paragraph_labels(content, file_path)


def find_holdout_files(target: Path) -> List[Path]:
    """Find all holdout or report files under the target path."""
    files: List[Path] = []
    if target.is_file():
        files.append(target)
    elif target.is_dir():
        # If target has a 'holdout' subfolder, inspect all markdown files in it
        holdout_sub = target / "holdout"
        if holdout_sub.is_dir():
            for p in holdout_sub.glob("*.md"):
                files.append(p)
        # Also inspect any files with 'holdout' in their name
        for p in target.rglob("*holdout*.md"):
            if p not in files:
                files.append(p)
        # If target itself is a holdout folder
        if "holdout" in target.name.lower():
            for p in target.glob("*.md"):
                if p not in files:
                    files.append(p)
    return sorted(files)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that holdout and report numbers carry required sanity/proxy labeling."
    )
    parser.add_argument(
        "targets",
        nargs="*",
        default=["docs/"],
        help="Files or directories to inspect (defaults to docs/ or docs/holdout/)",
    )
    args = parser.parse_args()

    all_files: List[Path] = []
    for t_str in args.targets:
        t_path = Path(t_str)
        if not t_path.exists():
            print(f"[check_holdout_labels] Target '{t_str}' not found, skipping.")
            continue
        all_files.extend(find_holdout_files(t_path))

    if not all_files:
        print("[check_holdout_labels] No holdout documents found to check. PASS (zero violations).")
        return 0

    total_violations: List[Tuple[Path, int, str, str]] = []
    for f in all_files:
        violations = check_holdout_file(f)
        for line_no, token, msg in violations:
            total_violations.append((f, line_no, token, msg))

    if total_violations:
        print(f"[check_holdout_labels] FAIL: Found {len(total_violations)} holdout claim violation(s):")
        for f, line_no, token, msg in total_violations:
            print(f"  {f}:{line_no}: {msg}")
        return 1

    print(f"[check_holdout_labels] PASS: All {len(all_files)} checked holdout file(s) comply with sanity/proxy labeling rule.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
