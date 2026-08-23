#!/usr/bin/env python3
"""Administrative facade; normal Workers should use scripts/ai.py."""
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[1]
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))

from buildos.cli import main
from scripts.ai import _adoption_preflight


def _admin_preflight(argv: list[str]) -> int:
    """Apply normal admission only to admin operations that create execution state."""
    return _adoption_preflight(argv)


if __name__ == "__main__":
    preflight = _admin_preflight(sys.argv[1:])
    raise SystemExit(preflight or main(admin=True))
