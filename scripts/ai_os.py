#!/usr/bin/env python3
"""Administrative facade; normal Workers should use scripts/ai.py."""
from pathlib import Path
import sys
import argparse

PACKAGE = Path(__file__).resolve().parents[1]
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))

from buildos.cli import execute, parse_invocation
from scripts.ai import _adoption_preflight, _epoch_preflight


def _admin_preflight(args: argparse.Namespace) -> int:
    """Guard active-authority creation/mutation while preserving break glass."""
    return _adoption_preflight(args) or _epoch_preflight(args)


def run(argv: list[str] | None = None) -> int:
    args = parse_invocation(argv, admin=True)
    return _admin_preflight(args) or execute(args)


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
