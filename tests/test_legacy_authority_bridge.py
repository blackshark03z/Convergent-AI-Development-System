from __future__ import annotations

from contextlib import contextmanager
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
BRIDGE = PACKAGE / "skills" / "project-lifecycle-bootstrap" / "scripts" / "legacy_authority_bridge.py"
AUTHORITY = PACKAGE / "skills" / "project-lifecycle-bootstrap" / "scripts" / "execution_authority.py"
AI = PACKAGE / "scripts" / "ai.py"
TRANSITION = "legacy-v116-fixture"


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
        (root / "scripts" / "ai.py").write_text("print('legacy worker')\n", encoding="utf-8")
        (root / "scripts" / "ai_os.py").write_text("print('legacy admin')\n", encoding="utf-8")
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


def prepare_args(*, blocked: bool = False) -> list[str]:
    rows = ["--transition-id", TRANSITION]
    if blocked:
        rows.extend([
            "--terminalize-blocked-goal", "--authorization-reference",
            "OWNER-AUTH-LEGACY-GOAL-TERMINAL-DISPOSITION",
        ])
    return rows


def prepare_and_retire(root: Path, *, blocked: bool = False) -> dict:
    code, prepared = invoke(root, "prepare", *prepare_args(blocked=blocked))
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

    def test_blocked_goal_requires_specific_authorization(self):
        with legacy_fixture(goal_status="BLOCKED", node_status="BLOCKED") as root:
            code, value = invoke(root, "prepare", *prepare_args())
            self.assertEqual(code, 2)
            self.assertIn("REQUIRES_TERMINAL_DISPOSITION_AUTHORIZATION", value["error"])
            code, value = invoke(root, "prepare", *prepare_args(blocked=True))
            self.assertEqual(code, 0, value)
            self.assertEqual(value["state"], "TRANSITION_PREPARED")

    def test_blocked_goal_authorization_never_overrides_active_node(self):
        with legacy_fixture(goal_status="BLOCKED", node_status="ACTIVE") as root:
            code, value = invoke(root, "prepare", *prepare_args(blocked=True))
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
            self.assertEqual(code, 0, value)

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
            encoded = root / ".buildos-legacy" / "archives" / TRANSITION / "encoded-executors" / "scripts" / "ai.py.base64"
            self.assertEqual(base64.b64decode(encoded.read_bytes(), validate=True), old_ai)
            self.assertEqual((archive / "AGENTS.md").read_bytes(), old_agents)
            self.assertEqual((archive / ".ai" / "history" / "task.json").read_bytes(), old_history)
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
        for fail_after in ("first_executor", "workers", "legacy_state", "receipt"):
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
            (root / "other" / "ai.py").write_text("print('dual')\n", encoding="utf-8")
            code, dual = invoke(root, "verify", "--transition-id", TRANSITION)
            self.assertEqual(code, 2)
            self.assertIn("LEGACY_EXECUTOR_CALLABLE", dual["error"])


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
