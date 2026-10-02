"""Unit tests enforcing wording rules and absence of prohibited causal terms.

Rules:
1. No causal claims in any Python source file in the repository.
   All assertions must reflect association rather than causality.
2. In accordance with project constraints, prohibited words are never written as bare tokens;
   they are constructed dynamically to avoid tripping 'grep -rEw' audits.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

import pytest

import constants

# Prohibited tokens constructed dynamically (strictly avoiding bare words)
WORD_PROVES = "".join(["pro", "ves"])
WORD_CAUSES = "".join(["cau", "ses"])
FORBIDDEN_WORDS = (WORD_PROVES, WORD_CAUSES)

# Word boundary regex pattern for matching whole words only
FORBIDDEN_PATTERN = re.compile(
    rf"\b(?:{re.escape(WORD_PROVES)}|{re.escape(WORD_CAUSES)})\b",
    re.IGNORECASE,
)

IGNORED_DIRS = {
    ".venv",
    "venv",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    "wheels",
}


def scan_file_for_forbidden_words(file_path: Path) -> List[Tuple[int, str, str]]:
    """Scan a single file and return a list of (line_num, matched_word, line_text)."""
    violations: List[Tuple[int, str, str]] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return violations

    for idx, line in enumerate(content.splitlines(), start=1):
        match = FORBIDDEN_PATTERN.search(line)
        if match:
            violations.append((idx, match.group(0), line.strip()))
    return violations


def scan_directory_for_forbidden_words(root_dir: Path) -> List[Tuple[Path, int, str, str]]:
    """Recursively scan a directory for .py files containing prohibited causal words."""
    all_violations: List[Tuple[Path, int, str, str]] = []
    for path in root_dir.rglob("*.py"):
        # Skip ignored directories
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        # Also skip symlinks pointing outside the repo
        if path.is_symlink() and not path.resolve().is_relative_to(root_dir.resolve()):
            continue
        file_violations = scan_file_for_forbidden_words(path)
        for line_no, word, line_txt in file_violations:
            all_violations.append((path, line_no, word, line_txt))
    return all_violations


def test_codebase_has_no_prohibited_causal_words() -> None:
    """Verify that no Python file in the repository contains prohibited causal words."""
    repo_root = Path(__file__).resolve().parent.parent
    violations = scan_directory_for_forbidden_words(repo_root)

    error_lines = [
        f"{p.relative_to(repo_root)}:{line_no} matches '{word}': {text}"
        for p, line_no, word, text in violations
    ]
    assert not violations, (
        f"Found {len(violations)} prohibited causal word violation(s) in codebase:\n"
        + "\n".join(error_lines)
    )


def test_forbidden_words_detector_fail_proof_on_fixture(tmp_path: Path) -> None:
    """Proof test verifying that the scanner reliably fails when prohibited words are present.

    Constructs the prohibited words dynamically in a temporary file fixture to prove
    detection without polluting the static codebase.
    """
    bad_file_1 = tmp_path / "bad_proves.py"
    bad_sentence_1 = f"# This test {WORD_PROVES} that the formulation works."
    bad_file_1.write_text(bad_sentence_1, encoding="utf-8")

    violations_1 = scan_file_for_forbidden_words(bad_file_1)
    assert len(violations_1) == 1
    assert violations_1[0][0] == 1
    assert violations_1[0][1].lower() == WORD_PROVES

    bad_file_2 = tmp_path / "bad_causes.py"
    bad_sentence_2 = f"def check_failure():\n    # excess nitrogen {WORD_CAUSES} leaf burn\n    return False\n"
    bad_file_2.write_text(bad_sentence_2, encoding="utf-8")

    violations_2 = scan_file_for_forbidden_words(bad_file_2)
    assert len(violations_2) == 1
    assert violations_2[0][0] == 2
    assert violations_2[0][1].lower() == WORD_CAUSES

    # Test directory scanner detects both in the temporary directory
    dir_violations = scan_directory_for_forbidden_words(tmp_path)
    assert len(dir_violations) == 2


def test_clean_fixture_passes(tmp_path: Path) -> None:
    """Verify that compliant wording with statistical association and sanity labeling passes."""
    clean_file = tmp_path / "clean_model.py"
    clean_text = (
        '"""Statistical association module for compost monitoring."""\n\n'
        '# Model estimates reflect statistical associations on historical proxy data (sanity check, not proof).\n'
        'TIER_FOOTNOTE = "T1 REAL | LIT calc | D1 proxy"\n'
        'DISCLAIMER = "Supplement, builds soil — not fertilizer replacement"\n'
        'def get_association():\n'
        '    return {"correlation": 0.82, "label": "sanity, not proof"}\n'
    )
    clean_file.write_text(clean_text, encoding="utf-8")

    violations = scan_file_for_forbidden_words(clean_file)
    assert violations == []


def test_constants_tier_and_disclaimer_presence() -> None:
    """Verify that constants.py exports the canonical tier footnote and required disclaimers."""
    assert constants.TIER_FOOTNOTE == "T1 REAL | LIT calc | D1 proxy"
    assert constants.TIER_FOOTNOTE_CANONICAL == "T1 REAL | LIT calc | D1 proxy"
    assert (
        constants.SUPPLEMENT_DISCLAIMER
        == "Supplement, builds soil — not fertilizer replacement"
    )
    assert "sanity check, not proof" in constants.MODEL_DISCLAIMER
    assert len(constants.HOLDOUT_LABEL_MARKERS) >= 3
    assert len(constants.PROHIBITED_CAUSAL_TOKENS) == 2
