#!/usr/bin/env python3
"""Compatibility filename exposing the CADS guard surface."""
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[1]
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))

from buildos.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
