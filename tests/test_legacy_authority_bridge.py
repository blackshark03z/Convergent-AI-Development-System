from __future__ import annotations

from contextlib import contextmanager
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


PACKAGE = Path(__file__).resolve().parents[1]
BRIDGE = PACKAGE / "skills" / "project-lifecycle-bootstrap" / "scripts" / "legacy_authority_bridge.py"
AUTHORITY = PACKAGE / "skills" / "project-lifecycle-bootstrap" / "scripts" / "execution_authority.py"
AI = PACKAGE / "scripts" / "ai.py"
TRANSITION = "legacy-v116-fixture"
TERMINAL_AUTH_ENV = "BUILDOS_TRUSTED_LEGACY_TERMINAL_DISPOSITION_SHA256"
TERMINAL_AUTH_SCHEMA = "buildos.legacy-terminal-disposition-authorization.v1"
TERMINAL_DISPOSITION = "TERMINALIZE_BLOCKED_LEGACY_GOAL_FOR_V125_ADOPTION"

LEGACY_FACADE = '''#!/usr/bin/env python3
"""Small agent-facing facade over the full ai_os.py kernel."""
import argparse
from pathlib import Path
KERNEL = Path(__file__).resolve().parent / "ai_os.py"
COMMANDS = ("start", "finish", "status", "next")
def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for command in COMMANDS: sub.add_parser(command)
if __name__ == "__main__": main()
'''

LEGACY_KERNEL = '''#!/usr/bin/env python3
"""Senior AI Build OS v1.16 lifecycle and goal orchestration CLI."""
import argparse
ACTIVE_TASK = "ACTIVE_TASK.md"
GOAL_STATE = "GOAL_STATE.json"
def main():
    parser = argparse.ArgumentParser()
    parser.add_subparsers(dest="command", required=True)
if __name__ == "__main__": main()
'''


def run_git(root: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args], text=True, encoding="utf-8",
        errors="replace", capture_output=True, timeout=30,
    )
    if check and completed.returncode:
        raise AssertionError(completed.stdout + completed.stderr)
    return completed.stdout.strip()


def invoke(
    root: Path, command: str, *args: str, env: dict[str, str] | None = None,
    package_root: Path | None = None,
) -> tuple[int, dict]:
    package_args = ["--package-root", str(package_root)] if package_root is not None else []
    completed = subprocess.run(
        [sys.executable, str(BRIDGE), "--root", str(root), *package_args, command, *args],
        text=True, encoding="utf-8", errors="replace", capture_output=True,
        timeout=60, env=env,
    )
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(completed.stdout + completed.stderr) from exc
    return completed.returncode, value


def authority(root: Path, command: str) -> tuple[int, dict]:
    completed = subprocess.run(
        [
            sys.executable, str(AUTHORITY), "--root", str(root),
            "--package-root", str(PACKAGE), command,
        ],
        text=True, encoding="utf-8", errors="replace", capture_output=True,
        timeout=60,
    )
    return completed.returncode, json.loads(completed.stdout)


def task_text(status: str = "COMPLETED", lease: str = "RELEASED") -> str:
    return (
        "# Legacy task\n\n"
        f"Task Status: {status}\n"
        "Task ID: LEGACY-TASK\n\n"
        "## Execution Lease\n\n"
        f"- Lease Status: {lease}\n"
        "- Writer Role: WORKER\n"
    )


def goal_value(status: str = "COMPLETED", *, node_status: str = "DONE") -> dict:
    return {
        "schema_version": 1,
        "goal_id": "LEGACY-GOAL",
        "status": status,
        "tasks": {"ONE": {"status": node_status, "outcome": "legacy outcome"}},
        "decisions_required": ([{"reason": "owner disposition required"}] if status == "BLOCKED" else []),
    }


@contextmanager
def legacy_fixture(
    *, task_status: str = "COMPLETED", lease: str = "RELEASED",
    goal_status: str = "COMPLETED", node_status: str = "DONE",
):
    with tempfile.TemporaryDirectory(prefix="buildos-v116-bridge-") as raw:
        root = Path(raw)
        run_git(root, "init", "-q")
        run_git(root, "config", "user.email", "fixture@example.invalid")
        run_git(root, "config", "user.name", "Fixture")
        run_git(root, "remote", "add", "origin", "https://example.invalid/legacy-fixture.git")
        (root / "app.txt").write_text("product baseline\n", encoding="utf-8")
        (root / "scripts").mkdir()
        (root / "scripts" / "ai.py").write_text(LEGACY_FACADE, encoding="utf-8")
        (root / "scripts" / "ai_os.py").write_text(LEGACY_KERNEL, encoding="utf-8")
        (root / "AGENTS.md").write_text("Use Senior AI Build OS v1.16 via scripts/ai.py.\n", encoding="utf-8")
        (root / ".ai" / "history").mkdir(parents=True)
        (root / ".ai" / "ACTIVE_TASK.md").write_text(task_text(task_status, lease), encoding="utf-8")
        (root / ".ai" / "GOAL_STATE.json").write_text(
            json.dumps(goal_value(goal_status, node_status=node_status), indent=2) + "\n",
            encoding="utf-8",
        )
        (root / ".ai" / "STATE.md").write_text("legacy state evidence\n", encoding="utf-8")
        (root / ".ai" / "history" / "task.json").write_text('{"immutable":true}\n', encoding="utf-8")
        run_git(root, "add", ".")
        run_git(root, "commit", "-qm", "legacy baseline")
        yield root


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def authorization_evidence(root: Path, *, mutate=None) -> tuple[Path, dict[str, str], dict]:
    goal_path = root / ".ai" / "GOAL_STATE.json"
    goal = json.loads(goal_path.read_text(encoding="utf-8"))
    decisions = goal.get("decisions_required", [])
    bindings = []
    for index, row in enumerate(decisions):
        identity = row.strip() if isinstance(row, str) and row.strip() else None
        if isinstance(row, dict):
            identity = next((str(row[key]).strip() for key in ("request_id", "decision_id", "id") if isinstance(row.get(key), str) and str(row[key]).strip()), None)
        bindings.append({"index": index, "identity": identity, "sha256": hashlib.sha256(canonical_bytes(row)).hexdigest()})
    repository = {
        "origin": run_git(root, "remote", "get-url", "origin"),
        "root_commits": sorted(run_git(root, "rev-list", "--max-parents=0", "HEAD").splitlines()),
        "branch": run_git(root, "symbolic-ref", "--quiet", "--short", "HEAD"),
        "head": run_git(root, "rev-parse", "HEAD"),
        "tree": run_git(root, "rev-parse", "HEAD^{tree}"),
    }
    value = {
        "schema": TERMINAL_AUTH_SCHEMA,
        "authorization_id": "OWNER-AUTH-LEGACY-GOAL-TERMINAL-DISPOSITION",
        "repository": repository,
        "legacy_goal": {
            "goal_id": goal.get("goal_id"),
            "path": ".ai/GOAL_STATE.json",
            "status": str(goal.get("status", "")).upper(),
            "sha256": hashlib.sha256(goal_path.read_bytes()).hexdigest(),
            "decision_bindings": bindings,
        },
        "disposition": TERMINAL_DISPOSITION,
        "authority": {
            "role": "OWNER",
            "identity": "fixture-owner",
            "authority_reference": "OWNER-AUTHORIZED-RC6-TERMINAL-DISPOSITION",
            "authorized_at": "2026-08-25T00:00:00Z",
        },
    }
    if mutate is not None:
        mutate(value)
    value["authorization_sha256"] = hashlib.sha256(canonical_bytes(value)).hexdigest()
    path = Path(run_git(root, "rev-parse", "--git-path", "buildos-test-terminal-authorization.json"))
    if not path.is_absolute():
        path = root / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))
    environment = os.environ.copy()
    environment[TERMINAL_AUTH_ENV] = hashlib.sha256(canonical_bytes(value)).hexdigest()
    return path, environment, value


def prepare_args(*, blocked: bool = False, authorization_path: Path | None = None) -> list[str]:
    rows = ["--transition-id", TRANSITION]
    if blocked:
        rows.extend(["--terminalize-blocked-goal"])
        if authorization_path is not None:
            rows.extend(["--terminal-disposition-authorization", str(authorization_path)])
    return rows


def prepare_and_retire(root: Path, *, blocked: bool = False) -> dict:
    authorization_path = None
    environment = None
    if blocked:
        authorization_path, environment, _ = authorization_evidence(root)
    code, prepared = invoke(
        root, "prepare", *prepare_args(blocked=blocked, authorization_path=authorization_path),
        env=environment,
    )
    if code:
        raise AssertionError(prepared)
    code, retired = invoke(root, "retire", "--transition-id", TRANSITION)
    if code:
        raise AssertionError(retired)
    return retired


class LegacyTerminalityTests(unittest.TestCase):
    def test_clean_terminal_v116_is_eligible(self):
        with legacy_fixture() as root:
            code, value = invoke(root, "inspect")
            self.assertEqual(code, 0, value)
            self.assertTrue(value["eligible"])
            self.assertEqual(value["legacy"]["task"]["status"], "COMPLETED")
            self.assertEqual(value["legacy"]["goal"]["status"], "COMPLETED")

    def test_every_live_task_state_is_refused_without_writes(self):
        for status in ("READY", "ACTIVE", "PAUSED", "BLOCKED"):
            with self.subTest(status=status), legacy_fixture(task_status=status) as root:
                code, value = invoke(root, "prepare", *prepare_args())
                self.assertEqual(code, 2)
                self.assertIn("LEGACY_TASK_LIVE", value["error"])
                self.assertFalse((root / ".buildos-legacy").exists())
                self.assertEqual(run_git(root, "status", "--porcelain"), "")

    def test_terminal_task_with_claimed_lease_is_refused(self):
        with legacy_fixture(lease="CLAIMED") as root:
            code, value = invoke(root, "inspect")
            self.assertEqual(code, 2)
            self.assertIn("LEGACY_TASK_LEASE_LIVE", value["error"])

    def test_active_goal_is_refused_even_when_task_is_terminal(self):
        with legacy_fixture(goal_status="ACTIVE") as root:
            code, value = invoke(root, "prepare", *prepare_args())
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "LEGACY_GOAL_LIVE:ACTIVE")

    def test_blocked_goal_requires_machine_verifiable_authorization(self):
        with legacy_fixture(goal_status="BLOCKED", node_status="BLOCKED") as root:
            code, value = invoke(root, "prepare", *prepare_args())
            self.assertEqual(code, 2)
            self.assertIn("REQUIRES_TERMINAL_DISPOSITION_AUTHORIZATION", value["error"])
            code, value = invoke(root, "prepare", *prepare_args(blocked=True))
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "TERMINAL_DISPOSITION_AUTHORIZATION_FILE_REQUIRED")
            path, environment, _ = authorization_evidence(root)
            code, value = invoke(
                root, "prepare", *prepare_args(blocked=True, authorization_path=path),
                env=environment,
            )
            self.assertEqual(code, 0, value)
            self.assertEqual(value["state"], "TRANSITION_PREPARED")

    def test_arbitrary_authorization_reference_is_refused(self):
        with legacy_fixture(goal_status="BLOCKED", node_status="BLOCKED") as root:
            code, value = invoke(
                root, "prepare", "--transition-id", TRANSITION,
                "--terminalize-blocked-goal", "--authorization-reference",
                "NOT-A-REAL-OWNER-AUTHORIZATION",
            )
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "TERMINAL_DISPOSITION_AUTHORIZATION_REFERENCE_UNSUPPORTED")

    def test_authorization_for_another_goal_is_refused(self):
        with legacy_fixture(goal_status="BLOCKED", node_status="BLOCKED") as root:
            path, environment, _ = authorization_evidence(
                root, mutate=lambda value: value["legacy_goal"].update(goal_id="OTHER-GOAL"),
            )
            code, value = invoke(
                root, "prepare", *prepare_args(blocked=True, authorization_path=path), env=environment,
            )
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "TERMINAL_DISPOSITION_AUTHORIZATION_GOAL_MISMATCH")

    def test_authorization_copied_from_another_repository_is_refused(self):
        with legacy_fixture(goal_status="BLOCKED", node_status="BLOCKED") as source, legacy_fixture(goal_status="BLOCKED", node_status="BLOCKED") as target:
            path, environment, _ = authorization_evidence(source)
            run_git(target, "remote", "set-url", "origin", "https://example.invalid/other-legacy-repository.git")
            code, value = invoke(
                target, "prepare", *prepare_args(blocked=True, authorization_path=path), env=environment,
            )
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "TERMINAL_DISPOSITION_AUTHORIZATION_REPOSITORY_MISMATCH")

    def test_authorization_for_earlier_goal_fingerprint_is_refused(self):
        with legacy_fixture(goal_status="BLOCKED", node_status="BLOCKED") as root:
            path, environment, _ = authorization_evidence(
                root, mutate=lambda value: value["legacy_goal"].update(sha256="0" * 64),
            )
            code, value = invoke(
                root, "prepare", *prepare_args(blocked=True, authorization_path=path), env=environment,
            )
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "TERMINAL_DISPOSITION_AUTHORIZATION_GOAL_MISMATCH")

    def test_goal_mutation_after_authorization_is_refused(self):
        with legacy_fixture(goal_status="BLOCKED", node_status="BLOCKED") as root:
            path, environment, _ = authorization_evidence(root)
            goal_path = root / ".ai" / "GOAL_STATE.json"
            goal = json.loads(goal_path.read_text(encoding="utf-8"))
            goal["tasks"]["ONE"]["outcome"] = "mutated after authorization"
            goal_path.write_text(json.dumps(goal, indent=2) + "\n", encoding="utf-8")
            run_git(root, "add", ".ai/GOAL_STATE.json")
            run_git(root, "commit", "-qm", "mutate goal after authorization")
            code, value = invoke(
                root, "prepare", *prepare_args(blocked=True, authorization_path=path), env=environment,
            )
            self.assertEqual(code, 2)
            self.assertIn("TERMINAL_DISPOSITION_AUTHORIZATION_", value["error"])

    def test_authorization_requires_exact_trusted_launcher_hash(self):
        with legacy_fixture(goal_status="BLOCKED", node_status="BLOCKED") as root:
            path, environment, _ = authorization_evidence(root)
            environment[TERMINAL_AUTH_ENV] = "0" * 64
            code, value = invoke(
                root, "prepare", *prepare_args(blocked=True, authorization_path=path), env=environment,
            )
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "TERMINAL_DISPOSITION_AUTHORIZATION_TRUSTED_BINDING_MISMATCH")

    def test_blocked_goal_authorization_never_overrides_active_node(self):
        with legacy_fixture(goal_status="BLOCKED", node_status="ACTIVE") as root:
            path, environment, _ = authorization_evidence(root)
            code, value = invoke(
                root, "prepare", *prepare_args(blocked=True, authorization_path=path), env=environment,
            )
            self.assertEqual(code, 2)
            self.assertIn("LEGACY_GOAL_NODE_LIVE", value["error"])

    def test_completed_goal_with_unfinished_node_is_refused(self):
        with legacy_fixture(goal_status="COMPLETED", node_status="PLANNED") as root:
            code, value = invoke(root, "prepare", *prepare_args())
            self.assertEqual(code, 2)
            self.assertIn("LEGACY_COMPLETED_GOAL_HAS_UNFINISHED_NODES", value["error"])
            self.assertTrue((root / "scripts" / "ai.py").is_file())

    def test_malformed_task_state_fails_closed(self):
        with legacy_fixture() as root:
            (root / ".ai" / "ACTIVE_TASK.md").write_text("Task Status: COMPLETED\n", encoding="utf-8")
            run_git(root, "add", ".ai/ACTIVE_TASK.md")
            run_git(root, "commit", "-qm", "malformed legacy state")
            code, value = invoke(root, "inspect")
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "LEGACY_TASK_STATE_MALFORMED")

    def test_runtime_goal_status_active_is_refused(self):
        with legacy_fixture() as root:
            runtime = root / ".ai" / "runtime"
            runtime.mkdir()
            (runtime / "goal.json").write_text(
                json.dumps({"goal_status": "ACTIVE"}) + "\n", encoding="utf-8",
            )
            run_git(root, "add", ".ai/runtime/goal.json")
            run_git(root, "commit", "-qm", "live runtime goal")
            code, value = invoke(root, "prepare", *prepare_args())
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "LEGACY_RUNTIME_GOAL_LIVE:ACTIVE")
            self.assertTrue((root / "scripts" / "ai.py").is_file())

    def test_runtime_blocked_goal_requires_terminal_disposition_authorization(self):
        with legacy_fixture() as root:
            runtime = root / ".ai" / "runtime"
            runtime.mkdir()
            (runtime / "goal.json").write_text(
                json.dumps({"goal_status": "BLOCKED"}) + "\n", encoding="utf-8",
            )
            run_git(root, "add", ".ai/runtime/goal.json")
            run_git(root, "commit", "-qm", "blocked runtime goal")
            code, value = invoke(root, "prepare", *prepare_args())
            self.assertEqual(code, 2)
            self.assertIn("REQUIRES_TERMINAL_DISPOSITION_AUTHORIZATION", value["error"])
            code, value = invoke(root, "prepare", *prepare_args(blocked=True))
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "TERMINAL_DISPOSITION_AUTHORIZATION_UNEXPECTED")

    def test_ai_regular_file_is_refused_before_mutation(self):
        with legacy_fixture() as root:
            shutil.rmtree(root / ".ai")
            (root / ".ai").write_text("malformed legacy authority\n", encoding="utf-8")
            run_git(root, "add", "-A")
            run_git(root, "commit", "-qm", "malformed ai path")
            code, value = invoke(root, "prepare", *prepare_args())
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "LEGACY_AI_STATE_PATH_INVALID")
            self.assertTrue((root / "scripts" / "ai.py").is_file())
            self.assertFalse((root / ".buildos-legacy").exists())

    def test_dirty_repository_and_tracked_buildos_are_refused(self):
        with legacy_fixture() as root:
            (root / "app.txt").write_text("owner work\n", encoding="utf-8")
            code, value = invoke(root, "prepare", *prepare_args())
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "DIRTY_REPOSITORY_REFUSED")
        with legacy_fixture() as root:
            (root / ".buildos").mkdir()
            (root / ".buildos" / "forged.json").write_text("{}\n", encoding="utf-8")
            run_git(root, "add", "-f", ".buildos/forged.json")
            run_git(root, "commit", "-qm", "tracked control")
            code, value = invoke(root, "prepare", *prepare_args())
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "TRACKED_BUILDOS_REFUSED")

    def test_prepare_is_product_read_only_and_cancellable(self):
        with legacy_fixture() as root:
            before = run_git(root, "status", "--porcelain")
            head = run_git(root, "rev-parse", "HEAD")
            code, value = invoke(root, "prepare", *prepare_args())
            self.assertEqual(code, 0, value)
            self.assertEqual(run_git(root, "status", "--porcelain"), before)
            self.assertEqual(run_git(root, "rev-parse", "HEAD"), head)
            code, value = invoke(root, "cancel", "--transition-id", TRANSITION)
            self.assertEqual(code, 0, value)
            self.assertEqual(value["state"], "LEGACY_ACTIVE")
            self.assertTrue((root / "scripts" / "ai.py").is_file())

    def test_prepare_does_not_leave_callable_executor_backups(self):
        with legacy_fixture() as root:
            self.assertEqual(invoke(root, "prepare", *prepare_args())[0], 0)
            common = Path(run_git(root, "rev-parse", "--git-common-dir"))
            if not common.is_absolute():
                common = root / common
            bridge_state = common / "buildos-legacy-bridge" / TRANSITION
            callable_backups = [path for path in bridge_state.rglob("*") if path.is_file() and path.suffix == ".py"]
            self.assertEqual(callable_backups, [])

    def test_head_and_dirty_drift_after_prepare_are_refused(self):
        with legacy_fixture() as root:
            self.assertEqual(invoke(root, "prepare", *prepare_args())[0], 0)
            (root / "other.txt").write_text("new commit\n", encoding="utf-8")
            run_git(root, "add", "other.txt")
            run_git(root, "commit", "-qm", "head drift")
            code, value = invoke(root, "retire", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertIn("REPOSITORY_BINDING_DRIFT:head", value["error"])
        with legacy_fixture() as root:
            self.assertEqual(invoke(root, "prepare", *prepare_args())[0], 0)
            (root / "app.txt").write_text("dirty race\n", encoding="utf-8")
            code, value = invoke(root, "retire", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "DIRTY_REPOSITORY_REFUSED")

    def test_transition_id_path_traversal_is_refused(self):
        with legacy_fixture() as root:
            code, value = invoke(root, "prepare", "--transition-id", "../escape")
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "TRANSITION_ID_INVALID")

    def test_already_active_current_authority_is_refused(self):
        with legacy_fixture() as root:
            info_exclude = Path(run_git(root, "rev-parse", "--git-path", "info/exclude"))
            if not info_exclude.is_absolute():
                info_exclude = root / info_exclude
            with info_exclude.open("a", encoding="utf-8") as handle:
                handle.write("\n.buildos/\n")
            current = root / ".buildos" / "control" / "CURRENT"
            current.parent.mkdir(parents=True)
            current.write_text("{}\n", encoding="utf-8")
            code, value = invoke(root, "inspect")
            self.assertEqual(code, 2)
            self.assertEqual(value["error"], "CURRENT_AUTHORITY_ALREADY_PRESENT")


class LegacyRetirementTests(unittest.TestCase):
    def test_retirement_preserves_exact_bytes_and_removes_callable_authority(self):
        with legacy_fixture() as root:
            old_ai = (root / "scripts" / "ai.py").read_bytes()
            old_agents = (root / "AGENTS.md").read_bytes()
            old_history = (root / ".ai" / "history" / "task.json").read_bytes()
            value = prepare_and_retire(root)
            self.assertEqual(value["state"], "LEGACY_RETIRED")
            archive = root / ".buildos-legacy" / "archives" / TRANSITION / "legacy"
            ai_archive = root / ".buildos-legacy" / "archives" / TRANSITION / "legacy-ai.zip"
            encoded = root / ".buildos-legacy" / "archives" / TRANSITION / "encoded-executors" / "scripts" / "ai.py.base64"
            self.assertEqual(base64.b64decode(encoded.read_bytes(), validate=True), old_ai)
            self.assertEqual((archive / "AGENTS.md").read_bytes(), old_agents)
            with zipfile.ZipFile(ai_archive) as stored_ai:
                self.assertEqual(stored_ai.read(".ai/history/task.json"), old_history)
            self.assertFalse((root / "scripts" / "ai.py").exists())
            self.assertFalse((root / "scripts" / "ai_os.py").exists())
            self.assertFalse((root / ".ai").exists())
            self.assertNotIn("v1.16", (root / "AGENTS.md").read_text(encoding="utf-8"))
            invoked = subprocess.run(
                [sys.executable, str(root / "scripts" / "ai.py"), "status"],
                text=True, capture_output=True, timeout=10,
            )
            self.assertNotEqual(invoked.returncode, 0)

    def test_retirement_retry_is_idempotent(self):
        with legacy_fixture() as root:
            first = prepare_and_retire(root)
            second_code, second = invoke(root, "retire", "--transition-id", TRANSITION)
            self.assertEqual(second_code, 0, second)
            self.assertEqual(second["receipt_sha256"], first["receipt_sha256"])

    def test_deep_legacy_evidence_is_committable_without_archive_path_expansion(self):
        with legacy_fixture() as root:
            deep = root / ".ai" / "evidence" / ("a" * 40) / ("b" * 40) / ("c" * 40)
            deep.mkdir(parents=True)
            member = deep / "historical-evidence-record.json"
            member.write_text('{"preserved":true}\n', encoding="utf-8")
            relative = member.relative_to(root).as_posix()
            run_git(root, "add", relative)
            run_git(root, "commit", "-qm", "deep legacy evidence")
            expected_bytes = member.read_bytes()
            prepare_and_retire(root)
            ai_archive = root / ".buildos-legacy" / "archives" / TRANSITION / "legacy-ai.zip"
            with zipfile.ZipFile(ai_archive) as stored_ai:
                self.assertEqual(stored_ai.read(relative), expected_bytes)
            run_git(root, "add", "-A")
            run_git(root, "commit", "-qm", "commit portable retirement archive")
            self.assertEqual(run_git(root, "status", "--porcelain"), "")

    def test_committed_retirement_verifies_in_original_and_fresh_clone_without_quarantine(self):
        with legacy_fixture() as root, tempfile.TemporaryDirectory(prefix="buildos-v116-fresh-clone-") as raw:
            prepare_and_retire(root)
            run_git(root, "add", "-A")
            run_git(root, "commit", "-qm", "commit durable retirement")
            code, original = invoke(root, "verify", "--transition-id", TRANSITION, "--require-clean")
            self.assertEqual(code, 0, original)
            clone = Path(raw) / "clone"
            run_git(root, "clone", "-q", str(root), str(clone))
            run_git(clone, "remote", "set-url", "origin", "https://example.invalid/legacy-fixture.git")
            common = Path(run_git(clone, "rev-parse", "--git-common-dir"))
            if not common.is_absolute():
                common = clone / common
            self.assertFalse((common / "buildos-legacy-bridge" / TRANSITION / "retired-ai").exists())
            code, copied = invoke(clone, "verify", "--transition-id", TRANSITION, "--require-clean")
            self.assertEqual(code, 0, copied)
            self.assertEqual(copied["receipt_sha256"], original["receipt_sha256"])

    def test_blocked_goal_authorization_evidence_is_durable_in_fresh_clone(self):
        with legacy_fixture(goal_status="BLOCKED", node_status="BLOCKED") as root, tempfile.TemporaryDirectory(prefix="buildos-v116-auth-clone-") as raw:
            prepare_and_retire(root, blocked=True)
            authorization = root / ".buildos-legacy" / "archives" / TRANSITION / "terminal-disposition-authorization.json"
            self.assertTrue(authorization.is_file())
            run_git(root, "add", "-A")
            run_git(root, "commit", "-qm", "commit authorized durable retirement")
            clone = Path(raw) / "clone"
            run_git(root, "clone", "-q", str(root), str(clone))
            run_git(clone, "remote", "set-url", "origin", "https://example.invalid/legacy-fixture.git")
            code, value = invoke(clone, "verify", "--transition-id", TRANSITION, "--require-clean")
            self.assertEqual(code, 0, value)
            copied = clone / authorization.relative_to(root)
            self.assertEqual(copied.read_bytes(), authorization.read_bytes())

    def test_fresh_clone_still_requires_tracked_archive_and_exact_members(self):
        with legacy_fixture() as root, tempfile.TemporaryDirectory(prefix="buildos-v116-fresh-clone-") as raw:
            prepare_and_retire(root)
            run_git(root, "add", "-A")
            run_git(root, "commit", "-qm", "commit durable retirement")
            clone = Path(raw) / "clone"
            run_git(root, "clone", "-q", str(root), str(clone))
            run_git(clone, "remote", "set-url", "origin", "https://example.invalid/legacy-fixture.git")
            archive = clone / ".buildos-legacy" / "archives" / TRANSITION / "legacy-ai.zip"
            archive.unlink()
            code, missing = invoke(clone, "verify", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertEqual(missing["error"], "ARCHIVED_AI_STATE_MISSING")
        with legacy_fixture() as root, tempfile.TemporaryDirectory(prefix="buildos-v116-fresh-clone-") as raw:
            prepare_and_retire(root)
            run_git(root, "add", "-A")
            run_git(root, "commit", "-qm", "commit durable retirement")
            clone = Path(raw) / "clone"
            run_git(root, "clone", "-q", str(root), str(clone))
            run_git(clone, "remote", "set-url", "origin", "https://example.invalid/legacy-fixture.git")
            archive = clone / ".buildos-legacy" / "archives" / TRANSITION / "legacy-ai.zip"
            with zipfile.ZipFile(archive, "a", compression=zipfile.ZIP_STORED) as stored:
                stored.writestr(".ai/extra-forged-state.json", b"{}\n")
            code, tampered = invoke(clone, "verify", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertIn("ARCHIVED_AI_FILE_SET_MISMATCH", tampered["error"])

    def test_incomplete_retirement_cannot_verify_or_recover_without_quarantine(self):
        with legacy_fixture() as root:
            self.assertEqual(invoke(root, "prepare", *prepare_args())[0], 0)
            environment = os.environ.copy()
            environment["BUILDOS_LEGACY_BRIDGE_FAIL_AFTER"] = "ai_quarantine"
            self.assertEqual(invoke(root, "retire", "--transition-id", TRANSITION, env=environment)[0], 2)
            common = Path(run_git(root, "rev-parse", "--git-common-dir"))
            if not common.is_absolute():
                common = root / common
            quarantine = common / "buildos-legacy-bridge" / TRANSITION / "retired-ai"
            shutil.rmtree(quarantine)
            code, recovered = invoke(root, "recover", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertIn("QUARANTINED_AI_STATE", recovered["error"])
            self.assertFalse((root / ".buildos-legacy" / "archives" / TRANSITION / "receipt.json").exists())

    def test_legitimate_product_executor_basenames_survive_byte_identically(self):
        with legacy_fixture() as root:
            product_files = {
                "src/ai.py": b"def choose_move(board):\n    return 'product-ai'\n",
                "src/product/buildos.py": b"class ProductBuildOS:\n    pass\n",
            }
            for relative, content in product_files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            run_git(root, "add", "src")
            run_git(root, "commit", "-qm", "add legitimate product modules")
            prepare_and_retire(root)
            for relative, content in product_files.items():
                self.assertEqual((root / relative).read_bytes(), content)

    def test_spoofed_canonical_or_renamed_legacy_executor_is_refused_without_retirement(self):
        with legacy_fixture() as root:
            (root / "scripts" / "ai.py").write_text("def product_ai(): return True\n", encoding="utf-8")
            run_git(root, "add", "scripts/ai.py")
            run_git(root, "commit", "-qm", "spoof canonical executor basename")
            code, value = invoke(root, "prepare", *prepare_args())
            self.assertEqual(code, 2)
            self.assertIn("AMBIGUOUS_LEGACY_EXECUTOR_CANDIDATE", value["error"])
            self.assertTrue((root / "scripts" / "ai.py").is_file())
        with legacy_fixture() as root:
            renamed = root / "tools" / "renamed_lifecycle.py"
            renamed.parent.mkdir()
            renamed.write_text(LEGACY_KERNEL, encoding="utf-8")
            run_git(root, "add", "tools/renamed_lifecycle.py")
            run_git(root, "commit", "-qm", "add renamed legacy executor")
            code, value = invoke(root, "prepare", *prepare_args())
            self.assertEqual(code, 2)
            self.assertIn("AMBIGUOUS_LEGACY_EXECUTOR_CANDIDATE", value["error"])
            self.assertTrue(renamed.is_file())

    def test_require_clean_requires_tracked_transition_evidence(self):
        with legacy_fixture() as root:
            prepare_and_retire(root)
            info_exclude = Path(run_git(root, "rev-parse", "--git-path", "info/exclude"))
            if not info_exclude.is_absolute():
                info_exclude = root / info_exclude
            with info_exclude.open("a", encoding="utf-8") as handle:
                handle.write("\n.buildos-legacy/\n")
            run_git(root, "add", "-u")
            run_git(root, "commit", "-qm", "retire live legacy paths only")
            self.assertEqual(run_git(root, "status", "--porcelain"), "")
            self.assertEqual(run_git(root, "ls-files", ".buildos-legacy"), "")
            code, value = invoke(root, "verify", "--transition-id", TRANSITION, "--require-clean")
            self.assertEqual(code, 2)
            self.assertIn("TRANSITION_EVIDENCE_NOT_TRACKED", value["error"])

    def test_historical_bridge_package_identity_survives_compatible_package_upgrade(self):
        with legacy_fixture() as root, tempfile.TemporaryDirectory(prefix="buildos-future-package-") as raw:
            prepare_and_retire(root)
            run_git(root, "add", ".")
            run_git(root, "commit", "-qm", "retire legacy authority")
            future = Path(raw)
            manifest = json.loads((PACKAGE / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
            manifest["package_id"] = manifest["package_id"] + "-compatible-upgrade"
            manifest["package_version"] = "1.25-rc6"
            (future / "PACKAGE_MANIFEST.json").write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
            )
            code, value = invoke(
                root, "verify", "--transition-id", TRANSITION, "--require-clean",
                package_root=future,
            )
            self.assertEqual(code, 0, value)
            self.assertEqual(value["state"], "LEGACY_RETIRED")

    def test_interrupted_retirement_recovers_same_transaction(self):
        for fail_after in ("first_executor", "workers", "ai_quarantine", "legacy_state", "receipt"):
            with self.subTest(fail_after=fail_after), legacy_fixture() as root:
                self.assertEqual(invoke(root, "prepare", *prepare_args())[0], 0)
                environment = os.environ.copy()
                environment["BUILDOS_LEGACY_BRIDGE_FAIL_AFTER"] = fail_after
                code, value = invoke(
                    root, "retire", "--transition-id", TRANSITION, env=environment,
                )
                self.assertEqual(code, 2)
                self.assertIn(f"INJECTED_FAILURE:{fail_after}", value["error"])
                code, recovered = invoke(root, "recover", "--transition-id", TRANSITION)
                self.assertEqual(code, 0, recovered)
                self.assertEqual(recovered["state"], "LEGACY_RETIRED")
                self.assertFalse((root / "scripts" / "ai.py").exists())
                self.assertFalse((root / "scripts" / "ai_os.py").exists())

    def test_quarantined_ai_race_is_preserved_and_fails_closed(self):
        with legacy_fixture() as root:
            self.assertEqual(invoke(root, "prepare", *prepare_args())[0], 0)
            environment = os.environ.copy()
            environment["BUILDOS_LEGACY_BRIDGE_FAIL_AFTER"] = "ai_quarantine"
            code, value = invoke(root, "retire", "--transition-id", TRANSITION, env=environment)
            self.assertEqual(code, 2)
            self.assertIn("INJECTED_FAILURE:ai_quarantine", value["error"])
            common = Path(run_git(root, "rev-parse", "--git-common-dir"))
            if not common.is_absolute():
                common = root / common
            quarantine = common / "buildos-legacy-bridge" / TRANSITION / "retired-ai"
            late = quarantine / "late-writer-state.json"
            late.write_text('{"late":true}\n', encoding="utf-8")
            code, value = invoke(root, "recover", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertIn("QUARANTINED_AI_UNEXPECTED_FILE", value["error"])
            self.assertTrue(late.is_file())
            self.assertFalse((root / ".ai").exists())
        with legacy_fixture() as root:
            prepare_and_retire(root)
            common = Path(run_git(root, "rev-parse", "--git-common-dir"))
            if not common.is_absolute():
                common = root / common
            quarantine = common / "buildos-legacy-bridge" / TRANSITION / "retired-ai"
            late = quarantine / "post-archive-late-state.json"
            late.write_text('{"late_after_archive":true}\n', encoding="utf-8")
            code, value = invoke(root, "verify", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertIn("QUARANTINED_AI_UNEXPECTED_FILE", value["error"])
            self.assertTrue(late.is_file())

    def test_unrelated_dirty_path_during_recovery_fails_closed(self):
        with legacy_fixture() as root:
            self.assertEqual(invoke(root, "prepare", *prepare_args())[0], 0)
            environment = os.environ.copy()
            environment["BUILDOS_LEGACY_BRIDGE_FAIL_AFTER"] = "first_executor"
            self.assertEqual(invoke(root, "retire", "--transition-id", TRANSITION, env=environment)[0], 2)
            (root / "app.txt").write_text("unrelated owner drift\n", encoding="utf-8")
            code, value = invoke(root, "recover", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertIn("UNRELATED_DIRTY_PATHS_DURING_RECOVERY", value["error"])

    def test_archive_or_receipt_tampering_is_detected(self):
        with legacy_fixture() as root:
            prepare_and_retire(root)
            archived = root / ".buildos-legacy" / "archives" / TRANSITION / "encoded-executors" / "scripts" / "ai.py.base64"
            archived.write_text("tampered\n", encoding="utf-8")
            code, value = invoke(root, "verify", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertIn("ENCODED_EXECUTOR_ARCHIVE", value["error"])
        with legacy_fixture() as root:
            prepare_and_retire(root)
            receipt = root / ".buildos-legacy" / "archives" / TRANSITION / "receipt.json"
            value = json.loads(receipt.read_text(encoding="utf-8"))
            value["repository"]["head"] = "0" * 40
            receipt.write_text(json.dumps(value), encoding="utf-8")
            code, failed = invoke(root, "verify", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertEqual(failed["error"], "TRANSITION_RECEIPT_HASH_INVALID")
        with legacy_fixture() as root:
            prepare_and_retire(root)
            archived = root / ".buildos-legacy" / "archives" / TRANSITION / "legacy-ai.zip"
            with zipfile.ZipFile(archived, "r") as source:
                members = [(info.filename, source.read(info)) for info in source.infolist()]
            with zipfile.ZipFile(archived, "w", compression=zipfile.ZIP_STORED) as repacked:
                for name, content in reversed(members):
                    info = zipfile.ZipInfo(name, date_time=(2001, 2, 3, 4, 5, 6))
                    repacked.writestr(info, content)
            code, value = invoke(root, "verify", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertIn("ARCHIVED_AI_CONTAINER_HASH_MISMATCH", value["error"])

    def test_receipt_copied_to_another_repository_is_refused(self):
        with legacy_fixture() as source, legacy_fixture() as target:
            prepare_and_retire(source)
            run_git(target, "remote", "set-url", "origin", "https://example.invalid/different-repository.git")
            shutil.rmtree(target / ".ai")
            (target / "scripts" / "ai.py").unlink()
            (target / "scripts" / "ai_os.py").unlink()
            shutil.copy2(source / "AGENTS.md", target / "AGENTS.md")
            shutil.copytree(source / ".buildos-legacy", target / ".buildos-legacy")
            code, value = invoke(target, "verify", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertIn("RECEIPT_COPIED_OR_REPOSITORY_MISMATCH", value["error"])

    def test_symlinked_legacy_executor_is_refused(self):
        with legacy_fixture() as root:
            outside = root.parent / f"outside-{root.name}.py"
            outside.write_text("outside\n", encoding="utf-8")
            (root / "scripts" / "ai.py").unlink()
            try:
                (root / "scripts" / "ai.py").symlink_to(outside)
            except OSError:
                outside.unlink(missing_ok=True)
                self.skipTest("symlink creation unavailable")
            try:
                run_git(root, "add", "scripts/ai.py")
                run_git(root, "commit", "-qm", "symlink executor")
                code, value = invoke(root, "prepare", *prepare_args())
                self.assertEqual(code, 2)
                self.assertIn("REPARSE_POINT_FORBIDDEN", value["error"])
            finally:
                outside.unlink(missing_ok=True)

    def test_windows_reparse_point_legacy_state_is_refused(self):
        if os.name != "nt":
            self.skipTest("Windows reparse-point regression")
        with legacy_fixture() as root:
            outside = root.parent / f"outside-ai-{root.name}"
            shutil.copytree(root / ".ai", outside)
            shutil.rmtree(root / ".ai")
            created = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(root / ".ai"), str(outside)],
                text=True, encoding="utf-8", errors="replace", capture_output=True,
                timeout=30,
            )
            if created.returncode:
                shutil.rmtree(outside)
                self.skipTest("junction creation unavailable")
            try:
                code, value = invoke(root, "prepare", *prepare_args())
                self.assertEqual(code, 2)
                self.assertEqual(value["error"], "LEGACY_AI_STATE_PATH_INVALID")
            finally:
                os.rmdir(root / ".ai")
                shutil.rmtree(outside)

    def test_replay_after_new_commit_and_new_dual_executor_are_refused(self):
        with legacy_fixture() as root:
            prepare_and_retire(root)
            run_git(root, "add", ".")
            run_git(root, "commit", "-qm", "retire legacy")
            (root / "app.txt").write_text("legitimate descendant\n", encoding="utf-8")
            run_git(root, "add", "app.txt")
            run_git(root, "commit", "-qm", "post transition descendant")
            code, verified = invoke(root, "verify", "--transition-id", TRANSITION, "--require-clean")
            self.assertEqual(code, 0, verified)
            code, replay = invoke(root, "prepare", "--transition-id", "second-transition")
            self.assertEqual(code, 2)
            self.assertEqual(replay["error"], "LEGACY_BRIDGE_ALREADY_PRESENT")
            (root / "other").mkdir()
            (root / "other" / "ai.py").write_text(LEGACY_FACADE, encoding="utf-8")
            code, dual = invoke(root, "verify", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertIn("AMBIGUOUS_LEGACY_EXECUTOR_CANDIDATE", dual["error"])


class LegacyAdoptionBindingTests(unittest.TestCase):
    def _retired_commit(self, root: Path) -> None:
        prepare_and_retire(root)
        run_git(root, "add", ".")
        run_git(root, "commit", "-qm", "retire legacy authority")

    def test_authority_record_is_bound_to_transition_receipt(self):
        with legacy_fixture() as root:
            self._retired_commit(root)
            code, written = authority(root, "write-record")
            self.assertEqual(code, 0, written)
            record = json.loads((root / ".buildos-authority.json").read_text(encoding="utf-8"))
            self.assertEqual(record["legacy_transition"]["transition_id"], TRANSITION)
            self.assertEqual(record["legacy_transition"]["schema"], "buildos.legacy-authority-transition.v1")
            code, checked = authority(root, "check")
            self.assertEqual(code, 0, checked)

    def test_post_transition_authority_ignores_legitimate_product_modules(self):
        with legacy_fixture() as root:
            for relative in ("src/ai.py", "src/product/buildos.py"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("def product_behavior(): return True\n", encoding="utf-8")
            run_git(root, "add", "src")
            run_git(root, "commit", "-qm", "add product modules with historical basenames")
            self._retired_commit(root)
            self.assertEqual(authority(root, "write-record")[0], 0)
            code, checked = authority(root, "check")
            self.assertEqual(code, 0, checked)
            self.assertTrue((root / "src" / "ai.py").is_file())
            self.assertTrue((root / "src" / "product" / "buildos.py").is_file())

    def test_bound_authority_fails_if_transition_archive_disappears(self):
        with legacy_fixture() as root:
            self._retired_commit(root)
            self.assertEqual(authority(root, "write-record")[0], 0)
            code, checked = authority(root, "check")
            self.assertEqual(code, 0, checked)
            shutil.rmtree(root / ".buildos-legacy")
            code, checked = authority(root, "check")
            self.assertEqual(code, 2)
            self.assertIn("AUTHORITY_RECORD_FIELD_SET_MISMATCH", checked["errors"])

    def test_current_without_activation_receipt_blocks_then_finalize_unblocks(self):
        with legacy_fixture() as root:
            self._retired_commit(root)
            self.assertEqual(authority(root, "write-record")[0], 0)
            run_git(root, "add", ".buildos-authority.json")
            run_git(root, "commit", "-qm", "enroll portable authority")
            check_command = f'"{sys.executable}" -c "print(\'bridge proof\')"'
            boot = subprocess.run(
                [
                    sys.executable, str(AI), "--root", str(root), "bootstrap",
                    "--task-id", "BRIDGE-PROOF", "--outcome", "prove activation binding",
                    "--allow", "app.txt", "--check", check_command,
                ],
                text=True, encoding="utf-8", errors="replace", capture_output=True,
                timeout=90,
            )
            self.assertEqual(boot.returncode, 0, boot.stdout + boot.stderr)
            code, blocked = authority(root, "check")
            self.assertEqual(code, 2)
            self.assertIn("ACTIVATION", " ".join(blocked["errors"]))
            kernel_receipts = list((root / ".buildos" / "control" / "receipts").glob("p*.json"))
            self.assertEqual(len(kernel_receipts), 1)
            kernel_receipt_bytes = kernel_receipts[0].read_bytes()
            kernel_receipts[0].unlink()
            code, incomplete = invoke(root, "finalize", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertIn("KERNEL_COMMIT_RECEIPT_MISSING", incomplete["error"])
            kernel_receipts[0].write_bytes(kernel_receipt_bytes)
            code, finalized = invoke(root, "finalize", "--transition-id", TRANSITION)
            self.assertEqual(code, 0, finalized)
            self.assertEqual(finalized["state"], "V125_ACTIVE")
            code, checked = authority(root, "check")
            self.assertEqual(code, 0, checked)

    def test_finalize_rejects_self_hashed_noncanonical_generation(self):
        with legacy_fixture() as root:
            self._retired_commit(root)
            self.assertEqual(authority(root, "write-record")[0], 0)
            run_git(root, "add", ".buildos-authority.json")
            run_git(root, "commit", "-qm", "enroll portable authority")
            info_exclude = Path(run_git(root, "rev-parse", "--git-path", "info/exclude"))
            if not info_exclude.is_absolute():
                info_exclude = root / info_exclude
            with info_exclude.open("a", encoding="utf-8") as handle:
                handle.write("\n.buildos/\n")
            generation = {
                "schema": "buildos.generation.v1", "generation": 1,
                "state": {}, "event": {}, "operation_id": "forged-generation",
                "intent_hash": "0" * 64,
            }
            payload = json.dumps(generation, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            generation["generation_hash"] = __import__("hashlib").sha256(payload.encode("utf-8")).hexdigest()
            filename = "forged.json"
            current = {
                "schema": "buildos.current.v1", "generation": 1,
                "generation_hash": generation["generation_hash"], "file": filename,
            }
            control = root / ".buildos" / "control"
            (control / "generations").mkdir(parents=True)
            (control / "receipts").mkdir()
            (control / "generations" / filename).write_text(
                json.dumps(generation, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            (control / "CURRENT").write_text(json.dumps(current) + "\n", encoding="utf-8")
            receipt = {**current, "schema": "buildos.commit_receipt.v1"}
            (control / "receipts" / f"p00000001-{generation['generation_hash'][:16]}.json").write_text(
                json.dumps(receipt) + "\n", encoding="utf-8",
            )
            code, value = invoke(root, "finalize", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertIn("CURRENT_REJECTED_BY_FROZEN_KERNEL", value["error"])
            self.assertFalse((control / "legacy-bridge-receipts" / f"{TRANSITION}.json").exists())

    def test_activation_receipt_reparse_path_is_refused(self):
        with legacy_fixture() as root:
            self._retired_commit(root)
            self.assertEqual(authority(root, "write-record")[0], 0)
            run_git(root, "add", ".buildos-authority.json")
            run_git(root, "commit", "-qm", "enroll portable authority")
            check_command = f'"{sys.executable}" -c "print(\'bridge reparse proof\')"'
            boot = subprocess.run(
                [
                    sys.executable, str(AI), "--root", str(root), "bootstrap",
                    "--task-id", "BRIDGE-REPARSE", "--outcome", "prove receipt path safety",
                    "--allow", "app.txt", "--check", check_command,
                ],
                text=True, encoding="utf-8", errors="replace", capture_output=True,
                timeout=90,
            )
            self.assertEqual(boot.returncode, 0, boot.stdout + boot.stderr)
            link = root / ".buildos" / "control" / "legacy-bridge-receipts"
            outside = root.parent / f"outside-activation-{root.name}"
            outside.mkdir()
            if os.name == "nt":
                created = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                    text=True, encoding="utf-8", errors="replace", capture_output=True,
                    timeout=30,
                )
                if created.returncode:
                    shutil.rmtree(outside)
                    self.skipTest("activation receipt junction creation unavailable")
            else:
                try:
                    link.symlink_to(outside, target_is_directory=True)
                except OSError:
                    shutil.rmtree(outside)
                    self.skipTest("activation receipt symlink creation unavailable")
            try:
                code, value = invoke(root, "finalize", "--transition-id", TRANSITION)
                self.assertEqual(code, 2)
                self.assertIn("REPARSE_POINT_FORBIDDEN", value["error"])
                self.assertEqual(list(outside.iterdir()), [])
            finally:
                if os.name == "nt":
                    os.rmdir(link)
                else:
                    link.unlink()
                shutil.rmtree(outside)

    @unittest.skipUnless(shutil.which("powershell"), "PowerShell unavailable")
    def test_initializer_rejects_invalid_transition_before_any_adoption_write(self):
        with legacy_fixture() as root:
            self._retired_commit(root)
            receipt = root / ".buildos-legacy" / "archives" / TRANSITION / "receipt.json"
            value = json.loads(receipt.read_text(encoding="utf-8"))
            value["receipt_sha256"] = "0" * 64
            receipt.write_text(json.dumps(value) + "\n", encoding="utf-8")
            run_git(root, "add", str(receipt.relative_to(root)))
            run_git(root, "commit", "-qm", "tamper transition receipt")
            quality_gate = json.dumps([sys.executable, "-c", "print('isolated gate')"])
            initialized = subprocess.run(
                [
                    "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                    str(PACKAGE / "adoption" / "initialize.ps1"),
                    "-Root", str(root), "-AcceptedRef", "HEAD",
                    "-ProjectName", "Fixture", "-Purpose", "Bridge preflight",
                    "-IntendedUse", "Tests", "-SuccessDefinition", "Preflight passes",
                    "-NonGoals", "No production", "-Constraints", "Local only",
                    "-QualityGateArgvJson", quality_gate, "-Mode", "existing",
                    "-PackageRoot", str(PACKAGE),
                ],
                text=True, encoding="utf-8", errors="replace", capture_output=True,
                timeout=90,
            )
            self.assertNotEqual(initialized.returncode, 0)
            self.assertIn("Legacy authority transition preflight failed", initialized.stdout + initialized.stderr)
            self.assertFalse((root / ".buildos-policy.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
