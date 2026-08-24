#!/usr/bin/env python3
"""Run the deterministic release suite and emit one structured result object."""
from __future__ import annotations

from contextlib import redirect_stdout
import json
from pathlib import Path
import sys
import unittest


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    loader = unittest.defaultTestLoader
    suite = loader.discover(str(root / "tests"), pattern="test_*.py", top_level_dir=str(root))
    discovered = suite.countTestCases()
    with redirect_stdout(sys.stderr):
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    payload = {
        "schema": "buildos.release-suite-result.v1",
        "successful": result.wasSuccessful(),
        "discovered_test_count": discovered,
        "tests_run": result.testsRun,
        "failure_count": len(result.failures),
        "error_count": len(result.errors),
        "skipped_test_ids": sorted(test.id() for test, _ in result.skipped),
        "expected_failure_count": len(result.expectedFailures),
        "unexpected_success_count": len(result.unexpectedSuccesses),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if result.wasSuccessful() and result.testsRun == discovered else 2


if __name__ == "__main__":
    raise SystemExit(main())
