#!/usr/bin/env python3
"""Run the active CADS test suite."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    git = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if git.returncode != 0 or Path(git.stdout.strip()).resolve() != ROOT.resolve():
        print(
            "SOURCE_CHECKOUT_REQUIRED: extracted candidates must run "
            "python scripts/portable_self_test.py",
        )
        return 2
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
        cwd=ROOT,
        check=False,
    )
    if proc.returncode == 0:
        print("SIMPLIFIED_ACTIVE_SUITE=PASS")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
