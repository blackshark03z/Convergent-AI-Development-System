from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from buildos.execution_route import (
    ExecutionRouteError,
    PROPERTY_ORDER,
    ROUTE_DIRECT,
    ROUTE_GOVERNED,
    classify,
)
from tests.test_thin_guard import AI, repository, snapshot_files


class ExecutionRouteTests(unittest.TestCase):
    def test_no_runtime_properties_defaults_to_direct(self):
        result = classify([])
        self.assertEqual(result["route"], ROUTE_DIRECT)
        self.assertEqual(result["required_properties"], [])
        self.assertTrue(result["derived_only"])
        self.assertFalse(result["authority_granted"])

    def test_each_declared_runtime_property_requires_governed_substrate(self):
        for prop in PROPERTY_ORDER:
            with self.subTest(prop=prop):
                result = classify([prop])
                self.assertEqual(result["route"], ROUTE_GOVERNED)
                self.assertEqual(result["required_properties"], [prop])

    def test_properties_are_deduplicated_in_stable_contract_order(self):
        result = classify([
            "resource-governance",
            "isolated-mutation",
            "resource-governance",
        ])
        self.assertEqual(
            result["required_properties"],
            ["isolated-mutation", "resource-governance"],
        )

    def test_unknown_property_fails_closed(self):
        with self.assertRaises(ExecutionRouteError):
            classify(["magic-agent-mode"])

    def test_cli_route_is_read_only_and_does_not_create_lifecycle_state(self):
        with repository() as (root, _):
            before = snapshot_files(root)
            direct = subprocess.run(
                [sys.executable, str(AI), "--root", str(root), "route"],
                text=True, encoding="utf-8", errors="replace",
                capture_output=True, timeout=30,
            )
            governed = subprocess.run(
                [
                    sys.executable, str(AI), "--root", str(root), "route",
                    "--require", "concurrent-writer-fencing",
                    "--require", "durable-recovery",
                ],
                text=True, encoding="utf-8", errors="replace",
                capture_output=True, timeout=30,
            )
            after = snapshot_files(root)

            self.assertEqual(direct.returncode, 0, direct.stdout + direct.stderr)
            self.assertEqual(json.loads(direct.stdout)["route"], ROUTE_DIRECT)
            self.assertEqual(governed.returncode, 0, governed.stdout + governed.stderr)
            payload = json.loads(governed.stdout)
            self.assertEqual(payload["route"], ROUTE_GOVERNED)
            self.assertEqual(
                payload["required_properties"],
                ["durable-recovery", "concurrent-writer-fencing"],
            )
            self.assertEqual(before, after)


class DirectExecutionContractTests(unittest.TestCase):
    def test_decision_and_architecture_keep_mar_conditional(self):
        root = Path(__file__).resolve().parents[1]
        index = (root / "docs/decisions/README.md").read_text(encoding="utf-8")
        decision = (
            root / "docs/decisions/0013-direct-execution-and-conditional-governance.md"
        ).read_text(encoding="utf-8")
        architecture = (root / "ARCHITECTURE.md").read_text(encoding="utf-8")

        self.assertIn("DR-0013", index)
        self.assertIn("direct execution is the default route", decision.lower())
        self.assertIn("MAR is one current governed substrate", decision)
        self.assertIn("property-based", architecture)
        self.assertIn("not a mandatory CADS dependency", architecture)

    def test_design_template_and_acceptance_expose_new_boundaries(self):
        root = Path(__file__).resolve().parents[1]
        baseline = (root / "templates/project/DESIGN_BASELINE.md").read_text(
            encoding="utf-8",
        )
        acceptance = (root / "skills/core/product-acceptance.md").read_text(
            encoding="utf-8",
        )

        self.assertIn("Execution Substrate Requirements", baseline)
        self.assertIn("isolated-mutation", baseline)
        self.assertIn("Independent acceptance attack", acceptance)
        self.assertIn("worker's completion narrative", acceptance)


if __name__ == "__main__":
    unittest.main()
