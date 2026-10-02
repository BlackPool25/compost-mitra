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
    mock_dir = repo_root / "mock"

    mock_files = list(mock_dir.glob("*.json"))
    if not mock_files:
        print("[pre-commit] No mock JSON files found to validate.")
        return 0

    cmd = [
        sys.executable,
        str(check_keys_script),
        "--warn-only",
        *[str(f) for f in mock_files],
    ]
    print(f"[pre-commit] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
