from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
AUTHORITY = PACKAGE / "skills" / "project-lifecycle-bootstrap" / "scripts" / "execution_authority.py"
LEGACY_FACADE = '''#!/usr/bin/env python3
"""Small agent-facing facade over the full ai_os.py kernel."""
import argparse
from pathlib import Path
KERNEL = Path(__file__).resolve().parent / "ai_os.py"
COMMANDS = ("start", "finish", "status", "next")
def main():
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command")
    for command in COMMANDS: sub.add_parser(command)
'''
LEGACY_KERNEL = '''#!/usr/bin/env python3
"""Senior AI Build OS v1.16 lifecycle and goal orchestration CLI."""
import argparse
ACTIVE_TASK = "ACTIVE_TASK.md"
GOAL_STATE = "GOAL_STATE.json"
def main():
    parser = argparse.ArgumentParser(); parser.add_subparsers(dest="command")
'''
LEGACY_VALIDATOR = '''#!/usr/bin/env python3
"""Invariant validator for Senior AI Build OS v1.16."""
import argparse
ACTIVE_TASK = "ACTIVE_TASK.md"
GOAL_STATE = "GOAL_STATE.json"
def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--ci", action="store_true")
'''


def invoke(root: Path, *args: str) -> tuple[int, dict]:
    proc = subprocess.run([sys.executable, str(AUTHORITY), "--root", str(root), *args], text=True, capture_output=True, timeout=30)
    return proc.returncode, json.loads(proc.stdout)


class ExecutionAuthorityTests(unittest.TestCase):
    def authority_root(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory(prefix="buildos-authority-")

    def record(self, root: Path) -> None:
        code, payload = invoke(root, "--package-root", str(PACKAGE), "write-record")
        self.assertEqual(code, 0, payload)

    def test_one_v123_authority_passes(self):
        with self.authority_root() as td:
            root = Path(td); self.record(root)
            code, payload = invoke(root, "check")
            self.assertEqual(code, 0, payload)

    def test_callable_v121_cli_fails(self):
        with self.authority_root() as td:
            root = Path(td); self.record(root)
            (root / "scripts").mkdir(); (root / "scripts" / "ai.py").write_text(LEGACY_FACADE, encoding="utf-8")
            code, payload = invoke(root, "check")
            self.assertEqual(code, 2); self.assertIn("LEGACY_EXECUTABLE_CALLABLE: scripts/ai.py", payload["errors"])
            self.assertTrue(payload["cleanup_required"])

    def test_nested_project_local_executor_fails(self):
        with self.authority_root() as td:
            root = Path(td); self.record(root)
            (root / "legacy" / "scripts").mkdir(parents=True)
            (root / "legacy" / "scripts" / "ai_os.py").write_text(LEGACY_KERNEL, encoding="utf-8")
            code, payload = invoke(root, "check")
            self.assertEqual(code, 2); self.assertIn("AMBIGUOUS_EXECUTOR_CANDIDATE: legacy/scripts/ai_os.py", payload["errors"])
            self.assertTrue(payload["cleanup_required"])

    def test_legitimate_product_ai_and_buildos_modules_pass(self):
        with self.authority_root() as td:
            root = Path(td); self.record(root)
            (root / "src" / "product").mkdir(parents=True)
            (root / "src" / "ai.py").write_text("def choose_move(): return 1\n", encoding="utf-8")
            (root / "src" / "product" / "buildos.py").write_text("class ProductBuildOS: pass\n", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts" / "validate_ai_os.py").write_text(LEGACY_VALIDATOR, encoding="utf-8")
            code, payload = invoke(root, "check")
            self.assertEqual(code, 0, payload)

    def test_authoritative_legacy_ai_state_fails(self):
        with self.authority_root() as td:
            root = Path(td); self.record(root)
            (root / ".ai").mkdir(); (root / ".ai" / "GOAL_STATE.json").write_text("{}", encoding="utf-8")
            code, payload = invoke(root, "check")
            self.assertEqual(code, 2); self.assertIn("LEGACY_STATE_AUTHORITATIVE: .ai/GOAL_STATE.json", payload["errors"])

    def test_archived_source_and_historical_docs_are_ignored(self):
        with self.authority_root() as td:
            root = Path(td); self.record(root)
            (root / "README.md").write_text("Historical Build OS v1.21 notes", encoding="utf-8")
            archive = root.parent / f"archive-v121-{root.name}"; (archive / "scripts").mkdir(parents=True)
            (archive / "scripts" / "ai.py").write_text("legacy", encoding="utf-8")
            code, payload = invoke(root, "check")
            self.assertEqual(code, 0, payload)

    def test_conflicting_worker_instruction_fails(self):
        with self.authority_root() as td:
            root = Path(td); self.record(root)
            (root / "AGENTS.md").write_text("Use Build OS v1.21", encoding="utf-8")
            code, payload = invoke(root, "check")
            self.assertEqual(code, 2); self.assertIn("CONFLICTING_WORKER_INSTRUCTION: AGENTS.md", payload["errors"])

    def test_wrong_identity_and_no_authority_fail(self):
        with self.authority_root() as td:
            root = Path(td)
            code, payload = invoke(root, "check")
            self.assertEqual(code, 2); self.assertIn("AUTHORITY_RECORD_INVALID", payload["errors"][0])
            self.record(root)
            record = root / ".buildos-authority.json"
            value = json.loads(record.read_text(encoding="utf-8")); value["kernel_commit"] = "0" * 40
            record.write_text(json.dumps(value), encoding="utf-8")
            code, payload = invoke(root, "check")
            self.assertEqual(code, 2); self.assertIn("AUTHORITY_IDENTITY_MISMATCH: kernel_commit", payload["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
