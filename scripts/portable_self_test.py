#!/usr/bin/env python3
"""Run only tests valid from freshly extracted candidate bytes."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if not (ROOT / "CANDIDATE_MANIFEST.json").is_file():
        print("EXTRACTED_CANDIDATE_REQUIRED: CANDIDATE_MANIFEST.json is missing")
        return 2
    proc = subprocess.run(
        [
            sys.executable, "-m", "unittest", "discover", "-s",
            "portable_tests", "-p", "test_*.py", "-v",
        ],
        cwd=ROOT,
        check=False,
    )
    if proc.returncode == 0:
        print("SIMPLIFIED_PORTABLE_SUITE=PASS")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
