from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from buildos import effect_store
from buildos.external_effect import execute_external_effect
from buildos.thin_guard import check
from tests.test_thin_guard import append, repository, run_git


PACKAGE = Path(__file__).resolve().parents[1]


class SimplifiedEndToEndScenarios(unittest.TestCase):
    def test_normal_bugfix_uses_native_commit_without_lifecycle_ceremony(self):
        with repository() as (root, _):
            append(root / "app.py", "# ordinary bugfix\n")
            run_git(root, "add", "app.py")
            run_git(root, "commit", "-qm", "ordinary bugfix")

            self.assertEqual(run_git(root, "status", "--porcelain"), "")
            self.assertFalse((root / ".buildos" / "control" / "CURRENT").exists())
            self.assertFalse((root / ".buildos" / "control" / "generations").exists())

    def test_fixing_scope_reality_then_rerunning_passes_without_resume(self):
        with repository() as (root, base):
            append(root / "outside.txt")
            blocked = check(
                root, base=base, boundary="R3", strict_paths=["app.py"],
            )
            (root / "outside.txt").write_text("outside baseline\n", encoding="utf-8")
            passed = check(
                root, base=base, boundary="R3", strict_paths=["app.py"],
            )

            self.assertEqual(blocked["result"], "BLOCK")
            self.assertEqual(passed["result"], "PASS")
            self.assertFalse((root / ".buildos" / "control" / "CURRENT").exists())

    def test_repo_local_cold_start_exposes_goal_acceptance_constraints_and_next_action(self):
        agents = (PACKAGE / "AGENTS.md").read_text(encoding="utf-8")
        architecture = (PACKAGE / "ARCHITECTURE.md").read_text(encoding="utf-8")
        task = (PACKAGE / "TASK.md").read_text(encoding="utf-8")
        status = run_git(PACKAGE, "status", "--short")
        log = run_git(PACKAGE, "log", "-3", "--oneline")

        for heading in (
            "# Goal", "# Acceptance", "# Non-goals", "# Constraints",
            "# Material Decisions", "# Progress / Discoveries / Next",
        ):
            self.assertIn(heading, task)
        self.assertIn("TASK.md", agents)
        self.assertIn("ARCHITECTURE.md", agents)
        self.assertIn("Git owns product bytes and history", architecture)
        self.assertIn("Next:", task)
        self.assertIn("8970dc8", task)
        self.assertTrue(status)
        self.assertTrue(log)
        self.assertLess(len(agents), 4_000)
        self.assertLess(len(task), 10_000)

    def test_effect_ambiguity_survives_replacement_worktree_without_migration(self):
        with tempfile.TemporaryDirectory(prefix="buildos-replacement-") as raw:
            container = Path(raw)
            root = container / "primary"
            replacement = container / "replacement"
            root.mkdir()
            run_git(root, "init", "-q")
            run_git(root, "config", "user.name", "Replacement Test")
            run_git(root, "config", "user.email", "replacement@example.invalid")
            (root / "app.py").write_text("print('base')\n", encoding="utf-8")
            run_git(root, "add", "app.py")
            run_git(root, "commit", "-qm", "base")
            base = run_git(root, "rev-parse", "HEAD")
            effect_intent = {
                "effect_id": "replacement-effect",
                "operation": "create",
                "target": "provider://resource",
                "request_digest": hashlib.sha256(b"replacement request").hexdigest(),
            }
            execute_external_effect(
                root,
                base=base,
                intent=effect_intent,
                dispatcher=lambda _: (_ for _ in ()).throw(RuntimeError("ambiguous")),
            )
            run_git(
                root, "worktree", "add", "-q", "-b", "replacement-worker",
                str(replacement), base,
            )

            reloaded = effect_store.load(replacement, "replacement-effect")

            self.assertEqual(reloaded["state"], "DISPATCH_UNCERTAIN")
            self.assertFalse((replacement / ".buildos").exists())


if __name__ == "__main__":
    unittest.main()
