from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
SCRIPT = PACKAGE / "scripts" / "bootstrap_project.py"
TEMPLATES = PACKAGE / "templates" / "project"
CANONICAL = (
    "AGENTS.md",
    "TASK.md",
    "ARCHITECTURE.md",
    "docs/decisions/README.md",
)


def invoke(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
        check=False,
    )


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


class BootstrapProjectTests(unittest.TestCase):
    def test_empty_target_creates_canonical_files(self):
        with tempfile.TemporaryDirectory(prefix="buildos-bootstrap-") as raw:
            root = Path(raw)
            result = invoke(root)
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["result"], "READY")
            self.assertEqual(payload["created"], list(CANONICAL))
            self.assertEqual(payload["preserved"], [])
            self.assertEqual(set(snapshot(root)), set(CANONICAL))

    def test_second_run_changes_nothing_and_reports_preserved_ready(self):
        with tempfile.TemporaryDirectory(prefix="buildos-bootstrap-") as raw:
            root = Path(raw)
            self.assertEqual(invoke(root).returncode, 0)
            before = snapshot(root)

            result = invoke(root)
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 0)
            self.assertEqual(snapshot(root), before)
            self.assertEqual(payload["result"], "READY")
            self.assertEqual(payload["created"], [])
            self.assertEqual(payload["preserved"], list(CANONICAL))

    def assert_existing_file_preserved(self, name: str) -> None:
        with tempfile.TemporaryDirectory(prefix="buildos-bootstrap-") as raw:
            root = Path(raw)
            original = b"\x00owner bytes\r\n\xff"
            (root / name).write_bytes(original)

            result = invoke(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / name).read_bytes(), original)
            self.assertIn(name, json.loads(result.stdout)["preserved"])

    def test_existing_agents_is_preserved_byte_for_byte(self):
        self.assert_existing_file_preserved("AGENTS.md")

    def test_existing_task_is_preserved_byte_for_byte(self):
        self.assert_existing_file_preserved("TASK.md")

    def test_existing_architecture_is_preserved_byte_for_byte(self):
        self.assert_existing_file_preserved("ARCHITECTURE.md")

    def test_existing_decision_index_is_preserved_byte_for_byte(self):
        with tempfile.TemporaryDirectory(prefix="buildos-bootstrap-") as raw:
            root = Path(raw)
            target = root / "docs" / "decisions" / "README.md"
            target.parent.mkdir(parents=True)
            original = b"owner decision index\r\n"
            target.write_bytes(original)

            result = invoke(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(target.read_bytes(), original)
            self.assertIn(
                "docs/decisions/README.md",
                json.loads(result.stdout)["preserved"],
            )

    def test_mixed_target_creates_only_missing_files(self):
        with tempfile.TemporaryDirectory(prefix="buildos-bootstrap-") as raw:
            root = Path(raw)
            owner = b"owner task\n"
            (root / "TASK.md").write_bytes(owner)

            result = invoke(root)
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 0)
            self.assertEqual(
                payload["created"],
                ["AGENTS.md", "ARCHITECTURE.md", "docs/decisions/README.md"],
            )
            self.assertEqual(payload["preserved"], ["TASK.md"])
            self.assertEqual((root / "TASK.md").read_bytes(), owner)

    def test_check_makes_zero_filesystem_changes(self):
        with tempfile.TemporaryDirectory(prefix="buildos-bootstrap-") as raw:
            root = Path(raw)
            marker = root / "owner.bin"
            marker.write_bytes(b"keep")
            before = snapshot(root)

            result = invoke(root, "--check")

            self.assertEqual(result.returncode, 1)
            self.assertEqual(snapshot(root), before)

    def test_check_complete_project_reports_ready(self):
        with tempfile.TemporaryDirectory(prefix="buildos-bootstrap-") as raw:
            root = Path(raw)
            for name in CANONICAL:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(name, encoding="utf-8")

            result = invoke(root, "--check")
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 0)
            self.assertEqual(payload["result"], "READY")
            self.assertEqual(payload["missing"], [])

    def test_check_incomplete_project_reports_required_and_missing(self):
        with tempfile.TemporaryDirectory(prefix="buildos-bootstrap-") as raw:
            root = Path(raw)
            (root / "AGENTS.md").write_text("owner", encoding="utf-8")

            result = invoke(root, "--check")
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(payload["result"], "BOOTSTRAP_REQUIRED")
            self.assertEqual(
                payload["missing"],
                ["TASK.md", "ARCHITECTURE.md", "docs/decisions/README.md"],
            )

    def test_invalid_root_fails_clearly(self):
        with tempfile.TemporaryDirectory(prefix="buildos-bootstrap-") as raw:
            missing = Path(raw) / "does-not-exist"

            result = invoke(missing)
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 2)
            self.assertEqual(payload["result"], "BLOCK")
            self.assertIn("does not exist", payload["message"])

    def test_templates_exist_and_contain_canonical_concepts(self):
        agents = (TEMPLATES / "AGENTS.md").read_text(encoding="utf-8")
        task = (TEMPLATES / "TASK.md").read_text(encoding="utf-8")
        architecture = (TEMPLATES / "ARCHITECTURE.md").read_text(encoding="utf-8")
        decisions = (TEMPLATES / "docs" / "decisions" / "README.md").read_text(
            encoding="utf-8",
        )

        self.assertIn("minimum CADS activation contract", agents)
        self.assertIn("Knowledge-gap responsibility", agents)
        self.assertIn("Git/source owns implementation reality", agents)
        self.assertIn("tests/CI as verification evidence", agents)
        self.assertIn("predefined Goal acceptance oracle", agents)
        self.assertIn("whole-journey/composition level", agents)
        self.assertIn("Concern Coverage Review", agents)
        self.assertIn("relationships/cardinality", agents)
        self.assertIn("material gap", agents)
        self.assertIn("what must be true", agents)
        self.assertIn("happy-path", agents)
        self.assertIn("isolated feature/subsystem PASS", agents)
        self.assertIn("remains unverified", agents)
        for procedure in (
            "Product Goal Framing", "Concern Coverage Review", "Goal Execution",
            "Systematic Debugging", "Product Acceptance", "Workspace Hygiene", "User-Facing Workflow",
            "Frontend Design", "UI Quality Review",
        ):
            self.assertIn(procedure, agents)
        for heading in (
            "# Goal", "# Critical User Journey", "# Acceptance",
            "# Acceptance Fixture / Golden Input", "# Non-goals", "# Constraints",
            "# Material Decisions", "# Progress", "# Discoveries / Blockers",
            "# Next Safe Action",
        ):
            self.assertIn(heading, task)
        self.assertIn("Owner supplies the desired product outcome", task)
        self.assertIn("AI Tech Lead owns engineering judgment", task)
        for heading in (
            "# System Purpose", "# Architecture", "# Components",
            "# Data / Control Flow", "# Authority / State Boundaries",
            "# Stable Invariants", "# Important Tradeoffs / Decisions",
            "# External Boundaries", "# Deprecated / Legacy Notes",
        ):
            self.assertIn(heading, architecture)
        self.assertIn("# Active Decision Index", decisions)
        self.assertIn("material", decisions.lower())
        self.assertIn("Superseded", decisions)

    def test_core_skill_library_contains_event_routed_playbooks(self):
        skills = PACKAGE / "skills" / "core"
        for name in (
            "project-cold-start.md",
            "product-goal-framing.md",
            "concern-coverage-review.md",
            "goal-execution.md",
            "systematic-debugging.md",
            "product-acceptance.md",
            "workspace-hygiene.md",
        ):
            self.assertTrue((skills / name).is_file(), name)

    def test_product_ui_skill_library_contains_conditional_playbooks(self):
        skills = PACKAGE / "skills" / "product"
        for name in (
            "user-facing-workflow.md",
            "frontend-design.md",
            "ui-quality-review.md",
        ):
            self.assertTrue((skills / name).is_file(), name)

    def test_bootstrap_never_creates_buildos_runtime_state(self):
        with tempfile.TemporaryDirectory(prefix="buildos-bootstrap-") as raw:
            root = Path(raw)

            result = invoke(root)

            self.assertEqual(result.returncode, 0)
            self.assertFalse((root / ".buildos").exists())
            self.assertFalse((root / ".git").exists())
            self.assertEqual(set(snapshot(root)), set(CANONICAL))


if __name__ == "__main__":
    unittest.main()
