from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from buildos.execution_handoff import ExecutionHandoffError, compile_handoff
from tests.test_thin_guard import AI, repository, snapshot_files


class ExecutionHandoffTests(unittest.TestCase):
    def test_compiles_explicit_inputs_with_identity_and_direct_route(self):
        with repository() as (root, _):
            task = root / "TASK.md"
            task.write_text("# Goal\nShip one bounded change.\n", encoding="utf-8")
            design = root / "DESIGN_BASELINE.md"
            design.write_text("# Design Baseline\nKeep execution replaceable.\n", encoding="utf-8")

            result = compile_handoff(root, [Path("TASK.md"), Path("DESIGN_BASELINE.md")])

            self.assertEqual(result["schema"], "cads-execution-handoff-v1")
            self.assertEqual(result["route"], "DIRECT")
            self.assertFalse(result["authority_granted"])
            self.assertFalse(result["persists_state"])
            self.assertFalse(result["starts_harness"])
            self.assertEqual(
                [item["path"] for item in result["inputs"]],
                ["TASK.md", "DESIGN_BASELINE.md"],
            )
            self.assertEqual(
                result["inputs"][0]["sha256"],
                hashlib.sha256(task.read_bytes()).hexdigest(),
            )
            self.assertIn("bounded change", result["inputs"][0]["content"])

    def test_reuses_property_based_governed_routing(self):
        with repository() as (root, _):
            (root / "TASK.md").write_text("# Goal\n", encoding="utf-8")
            result = compile_handoff(
                root,
                [Path("TASK.md")],
                ["durable-recovery", "concurrent-writer-fencing"],
            )
            self.assertEqual(result["route"], "GOVERNED")
            self.assertEqual(
                result["required_properties"],
                ["durable-recovery", "concurrent-writer-fencing"],
            )

    def test_rejects_escape_missing_directory_and_binary_inputs(self):
        with repository() as (root, _):
            (root / "folder").mkdir()
            (root / "binary.dat").write_bytes(b"\xff\xfe")
            outside = root.parent / "outside.txt"
            outside.write_text("outside", encoding="utf-8")

            cases = [
                [outside],
                [Path("missing.md")],
                [Path("folder")],
                [Path("binary.dat")],
            ]
            for paths in cases:
                with self.subTest(paths=paths):
                    with self.assertRaises(ExecutionHandoffError):
                        compile_handoff(root, paths)

    def test_cli_handoff_is_read_only(self):
        with repository() as (root, _):
            (root / "TASK.md").write_text("# Goal\nDirect handoff.\n", encoding="utf-8")
            before = snapshot_files(root)

            proc = subprocess.run(
                [
                    sys.executable,
                    str(AI),
                    "--root",
                    str(root),
                    "handoff",
                    "--input",
                    "TASK.md",
                ],
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=30,
            )

            after = snapshot_files(root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["route"], "DIRECT")
            self.assertFalse(payload["starts_harness"])
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
