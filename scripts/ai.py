#!/usr/bin/env python3
"""Worker facade for Build OS v1.22 plus explicit baseline disposition."""
import argparse
import json
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[1]
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))

from buildos.cli import main


def _baseline_disposition(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Create a fail-closed baseline-equivalent failure disposition")
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("command", choices=("baseline-disposition",))
    parser.add_argument("--expected-baseline-sha", required=True)
    parser.add_argument("--timeout", type=int, default=360)
    parser.add_argument("--authorization-actor", required=True)
    parser.add_argument("--authorization-reference", required=True)
    parser.add_argument("--inspected-by", required=True)
    parser.add_argument("--operation-id")
    args = parser.parse_args(argv)
    from baseline_equivalence_lifecycle import disposition
    from buildos.model import KernelError
    try:
        value = disposition(
            args.root.resolve(), package_root=PACKAGE,
            expected_baseline_sha=args.expected_baseline_sha, timeout=args.timeout,
            authorization_actor=args.authorization_actor, authorization_reference=args.authorization_reference,
            inspected_by=args.inspected_by, op_id=args.operation_id,
        )
        print(json.dumps(value, sort_keys=True))
        return 0
    except (KernelError, OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "ACTION_REQUIRED", "error": type(exc).__name__, "message": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    if "baseline-disposition" in sys.argv[1:]:
        raise SystemExit(_baseline_disposition(sys.argv[1:]))
    raise SystemExit(main(admin=False))
