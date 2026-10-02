#!/usr/bin/env python3
"""Validator script checking documentation and figures for the canonical tier footnote.

Footnote rule:
Every chart, figure, visualization, or UI recipe card must carry the tier footnote:
    'T1 REAL | LIT calc | D1 proxy'
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

CANONICAL_FOOTNOTE = "T1 REAL | LIT calc | D1 proxy"
FOOTNOTE_REGEX = re.compile(
    r"T1\s+REAL.*?\|\s*LIT\s+calc.*?\|\s*D1\s+proxy", re.IGNORECASE
)

# Patterns that denote visual artifacts, charts, or recipe cards
FIGURE_PATTERNS = [
    re.compile(r"```(?:mermaid|plotly|vega|chart|dot)"),
    re.compile(r"!\[.*?\]\(.*?\)"),
    re.compile(r"<div[^>]*class=[\"'].*?(?:recipe-card|card|metric-card).*?[\"']", re.IGNORECASE),
    re.compile(r"id=[\"']recipe-card-\d+[\"']", re.IGNORECASE),
    re.compile(r"^#+\s+.*?(?:Architecture Diagram|Flowchart|System Diagram)", re.IGNORECASE | re.MULTILINE),
]


def check_file_footnotes(path: Path) -> List[Tuple[int, str]]:
    """Check a single file for figures/cards and verify presence of tier footnote."""
    errors: List[Tuple[int, str]] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [(0, f"Cannot read file {path}: {exc}")]

    has_figure = any(p.search(content) for p in FIGURE_PATTERNS)
    has_footnote = bool(FOOTNOTE_REGEX.search(content))

    if has_figure and not has_footnote:
        # Locate the first figure pattern to give a useful line number
        line_num = 1
        for idx, line in enumerate(content.splitlines(), start=1):
            if any(p.search(line) for p in FIGURE_PATTERNS):
                line_num = idx
                break
        errors.append(
            (
                line_num,
                f"Missing required tier footnote '{CANONICAL_FOOTNOTE}' in file with visual figures/cards",
            )
        )

    # Check for specific recipe card selectors without footnote in UI templates or markdown
    for match in re.finditer(r"(#(?:recipe-card|card)[\w\-]+)", content):
        card_selector = match.group(1)
        # Search surrounding window of 500 characters for footnote or disclaimer
        start_pos = max(0, match.start() - 200)
        end_pos = min(len(content), match.end() + 500)
        card_context = content[start_pos:end_pos]
        if not FOOTNOTE_REGEX.search(card_context) and not FOOTNOTE_REGEX.search(content):
            line_no = content.count("\n", 0, match.start()) + 1
            errors.append(
                (
                    line_no,
                    f"Card selector '{card_selector}' is missing required tier footnote or disclaimer",
                )
            )

    return errors


def check_path(target: Path) -> List[Tuple[Path, int, str]]:
    """Recursively check target file or directory."""
    all_errors: List[Tuple[Path, int, str]] = []
    if target.is_file():
        file_errors = check_file_footnotes(target)
        for line_no, msg in file_errors:
            all_errors.append((target, line_no, msg))
    elif target.is_dir():
        for ext in ("*.md", "*.py", "*.html"):
            for file_path in target.rglob(ext):
                # Skip virtual environments and hidden caches
                if any(p.startswith(".") or p in {"__pycache__", "venv"} for p in file_path.parts):
                    continue
                file_errors = check_file_footnotes(file_path)
                for line_no, msg in file_errors:
                    all_errors.append((file_path, line_no, msg))
    return all_errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check documentation and figures for tier footnotes.")
    parser.add_argument(
        "targets",
        nargs="*",
        default=["docs/"],
        help="Files or directories to inspect (defaults to docs/)",
    )
    args = parser.parse_args()

    total_errors: List[Tuple[Path, int, str]] = []
    for target_str in args.targets:
        target_path = Path(target_str)
        if not target_path.exists():
            print(f"[check_tier_footnotes] Warning: target '{target_str}' does not exist, skipping.")
            continue
        total_errors.extend(check_path(target_path))

    if total_errors:
        print(f"[check_tier_footnotes] FAIL: Found {len(total_errors)} missing tier footnote(s):")
        for p, line_no, msg in total_errors:
            print(f"  {p}:{line_no}: {msg}")
        return 1

    print(f"[check_tier_footnotes] PASS: All checked files comply with tier footnote rule ('{CANONICAL_FOOTNOTE}').")
    return 0


if __name__ == "__main__":
    sys.exit(main())
