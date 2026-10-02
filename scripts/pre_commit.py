#!/usr/bin/env python3
"""Pre-commit hook script for CompostMitra.

Runs contract key validation on mock files in WARN-ONLY mode during development.
Strict mode will be enabled in later foundation phases.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    check_keys_script = repo_root / "scripts" / "check_keys.py"
    datacheck_script = repo_root / "scripts" / "datacheck.py"
    mock_dir = repo_root / "mock"

    mock_files = list(mock_dir.glob("*.json"))
    if mock_files:
        cmd1 = [
            sys.executable,
            str(check_keys_script),
            "--warn-only",
            *[str(f) for f in mock_files],
        ]
        print(f"[pre-commit] Running: {' '.join(cmd1)}")
        res1 = subprocess.run(cmd1, check=False)
        if res1.returncode != 0:
            return res1.returncode

    # Run datacheck in strict mode across data/ CSVs
    cmd2 = [sys.executable, str(datacheck_script), "--strict"]
    print(f"[pre-commit] Running: {' '.join(cmd2)}")
    res2 = subprocess.run(cmd2, check=False)
    return res2.returncode


if __name__ == "__main__":
    sys.exit(main())

