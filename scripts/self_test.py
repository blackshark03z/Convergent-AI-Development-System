#!/usr/bin/env python3
"""Run the deterministic v1.22 candidate proof suite."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
        cwd=ROOT,
        check=False,
    )
    if proc.returncode == 0:
        print("FULL_CANDIDATE_SELF_TEST=PASS")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
