"""Unit tests for edge fixtures and graceful failure handling.

Validates that:
  - tests/fixtures/empty.json raises ValueError with descriptive hint (no crash/traceback).
  - tests/fixtures/all-browns.json flags all-browns condition with high C/N.
  - tests/fixtures/meat.json blocks pathogen risk with BLOCKED_MEAT grade.
  - CLI executions handle these edge cases without unhandled exceptions.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.blender import blend

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parent.parent


def test_empty_fixture_in_blender() -> None:
    """Loading empty.json fixture raises ValueError with descriptive hint."""
    empty_path = FIXTURES_DIR / "empty.json"
    assert empty_path.exists()
    with empty_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    with pytest.raises(ValueError, match=r"Sum of weights must equal 1\.0"):
        blend(data)


def test_all_browns_fixture_in_blender() -> None:
    """Loading all-browns.json produces high C/N and FLAG_ALL_BROWNS grade."""
    browns_path = FIXTURES_DIR / "all-browns.json"
    assert browns_path.exists()
    with browns_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    res = blend(data)
    assert res["cn"] > 50.0
    assert res["heuristic_grade"] == "FLAG_ALL_BROWNS"


def test_meat_fixture_in_blender() -> None:
    """Loading meat.json produces BLOCKED_MEAT grade."""
    meat_path = FIXTURES_DIR / "meat.json"
    assert meat_path.exists()
    with meat_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    res = blend(data)
    assert res["heuristic_grade"] == "BLOCKED_MEAT"


def test_cli_empty_fixture_exits_nonzero_with_clean_error() -> None:
    """CLI execution on empty.json exits 1 and emits clean error message."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "blender.py"),
        str(FIXTURES_DIR / "empty.json"),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 1
    assert "ERROR: Sum of weights must equal 1.0" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_cli_all_browns_fixture_exits_zero_with_flag() -> None:
    """CLI execution on all-browns.json exits 0 with JSON output."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "blender.py"),
        str(FIXTURES_DIR / "all-browns.json"),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    parsed = json.loads(proc.stdout)
    assert parsed["heuristic_grade"] == "FLAG_ALL_BROWNS"


def test_cli_meat_fixture_exits_zero_with_blocked() -> None:
    """CLI execution on meat.json exits 0 with BLOCKED_MEAT in JSON."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "blender.py"),
        str(FIXTURES_DIR / "meat.json"),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    parsed = json.loads(proc.stdout)
    assert parsed["heuristic_grade"] == "BLOCKED_MEAT"


def test_pipeline_smoke_tomato_runs_cleanly() -> None:
    """Pipeline smoke test runs end-to-end for tomato demo."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "pipeline_smoke.py"),
        "--demo",
        "tomato",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    assert "C/N" in proc.stdout
    assert "MOCK" in proc.stdout
    assert "SMOKE PIPELINE PASS" in proc.stdout
