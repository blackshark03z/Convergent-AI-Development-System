from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[1]
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))

from buildos.facade import BuildOS
from buildos.governor import decide, load_policy
from buildos.model import KernelError, validate_task_request
from buildos.store import (
    CURRENT_SCHEMA,
    InjectedFailure,
    RecoveryRequired,
    atomic_json,
    paths,
    read_current,
    scan_generations,
    writer_lock,
)
from buildos.telemetry import TelemetryError, ingest, summarize
from tests.test_candidate import (
    check_command,
    generic_repo,
    product_commit,
    request,
    rollback_command,
    run_git,
)


class StoreRecoveryAdversarialTests(unittest.TestCase):
    def test_hard_process_death_releases_writer_guard(self):
        with generic_repo("hard-lock") as root:
            code = (
                "import os,sys\n"
                "from pathlib import Path\n"
                "from buildos.store import writer_lock\n"
                "with writer_lock(Path(sys.argv[1])):\n"
                "    os._exit(17)\n"
            )
            child = subprocess.run(
                [sys.executable, "-c", code, str(root)],
                cwd=PACKAGE,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(child.returncode, 17, child.stdout + child.stderr)
            self.assertTrue(paths(root).lock.is_file())
            with writer_lock(root):
                self.assertTrue(paths(root).lock.is_file())
            self.assertFalse(paths(root).lock.exists())
            self.assertTrue(any((paths(root).control / "stale-locks").glob("LOCK-*.json")))

    def test_missing_current_cannot_bootstrap_competing_task(self):
        with generic_repo("missing-current") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            old = osys.bootstrap(request("TASK-OLD")).snapshot
            paths(root).current.unlink()
            with self.assertRaisesRegex(RecoveryRequired, "run recover"):
                osys.status()
            with self.assertRaisesRegex(RecoveryRequired, "CURRENT is missing"):
                osys.bootstrap(request("TASK-NEW"))
            self.assertFalse(paths(root).current.exists())
            recovered = osys.recover()
            self.assertEqual(recovered["status"], "RECOVERED")
            self.assertEqual(read_current(root).generation_hash, old.generation_hash)
            self.assertEqual(read_current(root).state["task_id"], "TASK-OLD")

    def test_prepared_bootstrap_never_adopts_a_stale_git_anchor(self):
        with generic_repo("bootstrap-anchor") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            with self.assertRaises(InjectedFailure):
                osys.bootstrap(request(), configured_failures="before_pointer_swap")
            new_base = product_commit(root, "# pre-task external commit\n")
            started = osys.bootstrap(request()).snapshot
            self.assertEqual(started.state["base_git"]["head"], new_base)
            self.assertFalse(started.state["product_commit"])
            self.assertFalse(osys.status()["unadopted_product_commit"])

    def test_wrong_shape_files_are_reported_and_pointer_recovers_from_receipt(self):
        with generic_repo("wrong-shape") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            first = osys.bootstrap(request()).snapshot
            malformed = paths(root).generations / "g99999999-deadbeefdeadbeef.json"
            malformed.write_text("[]\n", encoding="utf-8")
            checked = osys.recover()
            self.assertIn(malformed.name, checked["invalid_generations"])
            paths(root).current.write_text("{}\n", encoding="utf-8")
            recovered = osys.recover()
            self.assertEqual(recovered["status"], "RECOVERED")
            self.assertEqual(read_current(root).generation_hash, first.generation_hash)

    def test_recover_quarantines_invalid_receipt_when_current_is_valid(self):
        with generic_repo("bad-receipt") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            bad = paths(root).receipts / "pbad.json"
            bad.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(RecoveryRequired, "invalid commit receipts"):
                osys.rollover(force=True, thread_id="thread-2")
            repaired = osys.recover()
            self.assertEqual(repaired["status"], "RECOVERED")
            self.assertIn("pbad.json", repaired["invalid_receipts"])
            self.assertTrue(repaired["quarantined_receipts"])
            self.assertFalse(bad.exists())
            self.assertEqual(osys.rollover(force=True, thread_id="thread-2").snapshot.state["context"]["epoch"], 2)

    def test_recover_repairs_valid_pointer_rollback_to_latest_receipt(self):
        with generic_repo("stale-pointer") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            first = osys.bootstrap(request()).snapshot
            second = osys.rollover(force=True, thread_id="thread-2").snapshot
            atomic_json(paths(root).current, {
                "schema": CURRENT_SCHEMA,
                "generation": first.generation,
                "generation_hash": first.generation_hash,
                "file": first.filename,
            })
            self.assertEqual(read_current(root).generation, 1)
            recovered = osys.recover()
            self.assertTrue(recovered["pointer_repaired"])
            self.assertEqual(read_current(root).generation_hash, second.generation_hash)

    def test_writer_refuses_stale_pointer_before_creating_competing_generation(self):
        with generic_repo("stale-writer") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            first = osys.bootstrap(request()).snapshot
            second = osys.rollover(force=True, thread_id="thread-2").snapshot
            atomic_json(paths(root).current, {
                "schema": CURRENT_SCHEMA,
                "generation": first.generation,
                "generation_hash": first.generation_hash,
                "file": first.filename,
            })
            before_records = {item.generation_hash for item in scan_generations(root)[0]}
            with self.assertRaisesRegex(RecoveryRequired, "older than the committed receipt frontier"):
                osys.rollover(force=True, thread_id="competing-thread")
            self.assertEqual({item.generation_hash for item in scan_generations(root)[0]}, before_records)
            self.assertEqual(read_current(root).generation_hash, first.generation_hash)
            osys.recover()
            self.assertEqual(read_current(root).generation_hash, second.generation_hash)
            third = osys.rollover(force=True, thread_id="thread-3").snapshot
            self.assertEqual(third.generation, 3)

    def test_recovery_mutation_boundaries_are_retry_safe(self):
        points = (
            "before_recovery_pointer_swap", "after_recovery_pointer_swap",
            "before_recovery_receipt", "after_recovery_receipt",
            "before_recovery_projection", "after_recovery_projection",
        )
        for point in points:
            with self.subTest(point=point), generic_repo(f"recover-{point}") as root:
                osys = BuildOS(root, package_root=PACKAGE)
                first = osys.bootstrap(request()).snapshot
                paths(root).current.unlink()
                with self.assertRaises(InjectedFailure):
                    osys.recover(configured_failures=point)
                if point == "before_recovery_pointer_swap":
                    self.assertFalse(paths(root).current.exists())
                else:
                    self.assertEqual(read_current(root).generation_hash, first.generation_hash)
                recovered = osys.recover()
                self.assertIn(recovered["status"], {"OK", "RECOVERED"})
                self.assertEqual(read_current(root).generation_hash, first.generation_hash)
                packet = json.loads((paths(root).runtime / "WORK_PACKET.json").read_text(encoding="utf-8"))
                self.assertEqual(packet["state_hash"], first.generation_hash)

    def test_operation_id_is_bound_across_prepared_and_committed_transitions(self):
        with generic_repo("op-collision") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            first = osys.bootstrap(request()).snapshot
            with self.assertRaises(InjectedFailure):
                osys.rollover(force=True, thread_id="thread-2", op_id="shared-op", configured_failures="before_pointer_swap")
            with self.assertRaisesRegex(KernelError, "different transition intent"):
                osys.abort(reason="not a rollover", op_id="shared-op")
            self.assertEqual(read_current(root).generation_hash, first.generation_hash)
            rolled = osys.rollover(force=True, thread_id="thread-2", op_id="shared-op")
            self.assertEqual(rolled.snapshot.state["context"]["epoch"], 2)
            with self.assertRaisesRegex(KernelError, "different transition intent"):
                osys.abort(reason="still not a rollover", op_id="shared-op")
            self.assertEqual(read_current(root).generation, 2)
        with generic_repo("op-global-binding") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            with self.assertRaises(InjectedFailure):
                osys.abort(reason="prepared abort", op_id="reused-global-op", configured_failures="before_pointer_swap")
            osys.rollover(force=True, thread_id="thread-2", op_id="different-op")
            with self.assertRaisesRegex(KernelError, "different transition intent"):
                osys.rollover(force=True, thread_id="thread-3", op_id="reused-global-op")
            self.assertEqual(read_current(root).generation, 2)

    def test_default_rollover_retry_after_linearization_advances_once(self):
        with generic_repo("rollover-default-retry") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            first = osys.bootstrap(request()).snapshot
            with self.assertRaises(InjectedFailure):
                osys.rollover(force=True, thread_id="thread-2", configured_failures="after_pointer_swap")
            retry = osys.rollover(force=True, thread_id="thread-2")
            self.assertTrue(retry.idempotent)
            self.assertEqual(retry.snapshot.generation, first.generation + 1)
            self.assertEqual(retry.snapshot.state["context"]["epoch"], 2)
            self.assertEqual(len(list(paths(root).receipts.glob("p00000002-*.json"))), 1)

    def test_explicit_rollover_retry_survives_a_fresher_governor_observation(self):
        with generic_repo("rollover-signal-retry") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            state = osys.bootstrap(request()).snapshot.state
            with self.assertRaises(InjectedFailure):
                osys.rollover(
                    force=True,
                    thread_id="thread-2",
                    op_id="stable-rollover",
                    configured_failures="before_pointer_swap",
                )
            ingest(root, state, [{
                "thread_id": "thread-original",
                "role": "PRODUCTIVE",
                "projected_prompt_tokens": 64_000,
                "model_requests": 5,
            }], source="FRESHER_SIGNAL")
            retried = osys.rollover(force=True, thread_id="thread-2", op_id="stable-rollover")
            self.assertTrue(retried.recovered_orphan)
            self.assertEqual(retried.snapshot.state["context"]["epoch"], 2)

    def test_stale_snapshot_cannot_overwrite_newer_work_packet(self):
        with generic_repo("packet-monotonic") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            first = osys.bootstrap(request()).snapshot
            second = osys.rollover(force=True, thread_id="thread-2").snapshot
            packet = osys.project(first)
            persisted = json.loads((paths(root).runtime / "WORK_PACKET.json").read_text(encoding="utf-8"))
            self.assertEqual(packet["state_hash"], second.generation_hash)
            self.assertEqual(persisted["state_hash"], second.generation_hash)
            self.assertEqual(persisted["epoch"], 2)

    def test_git_aware_status_cannot_overwrite_a_newer_packet(self):
        with generic_repo("status-packet-monotonic") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            from buildos import facade as facade_module
            original_atomic = facade_module.atomic_json
            advanced = False

            def advance_then_write(path, value):
                nonlocal advanced
                if not advanced and Path(path).name == "WORK_PACKET.json":
                    advanced = True
                    osys.rollover(force=True, thread_id="status-race-thread")
                return original_atomic(path, value)

            with patch("buildos.facade.atomic_json", side_effect=advance_then_write):
                status = osys.status()
            self.assertEqual(status["work_packet"]["epoch"], 2)
            self.assertEqual(status["work_packet"]["state_hash"], read_current(root).generation_hash)
            persisted = json.loads((paths(root).runtime / "WORK_PACKET.json").read_text(encoding="utf-8"))
            self.assertEqual(persisted["state_hash"], read_current(root).generation_hash)


class LifecycleScopeAdversarialTests(unittest.TestCase):
    def test_sequential_tasks_and_changed_bootstrap_contract(self):
        with generic_repo("sequential") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request("TASK-A"))
            product_commit(root)
            osys.record_commit()
            osys.validate(checks=[check_command()], inspected_by="worker-a")
            closed = osys.close().snapshot
            second = osys.bootstrap(request("TASK-B")).snapshot
            self.assertEqual(second.state["task_id"], "TASK-B")
            self.assertEqual(second.state["phase"], "ACTIVE")
            self.assertEqual(second.generation, closed.generation + 1)
        with generic_repo("contract-change") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            first = osys.bootstrap(request("SAME-TASK", "R1")).snapshot
            with self.assertRaisesRegex(KernelError, "different live canonical task"):
                osys.bootstrap(request(
                    "SAME-TASK", "R3",
                    owner_authorization="APPROVED",
                    authorization_reference="owner/ref/change",
                    authorization_actor="owner",
                ))
            self.assertEqual(read_current(root).generation_hash, first.generation_hash)
            self.assertEqual(read_current(root).state["risk"], "R1")

    def test_revision_can_change_scope_but_r3_escalation_still_requires_owner(self):
        with generic_repo("revision-contract") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            product_commit(root)
            osys.record_commit()
            osys.validate(checks=[check_command()], inspected_by="worker-a")
            closed = osys.close().snapshot
            with self.assertRaisesRegex(KernelError, "R3 revision requires"):
                osys.revise(reason="authorized expanded scope", risk="R3", allowed_paths=["app.py", "security.py"])
            self.assertEqual(read_current(root).generation_hash, closed.generation_hash)
            revised = osys.revise(
                reason="authorized expanded scope",
                risk="R3",
                allowed_paths=["app.py", "security.py"],
                owner_authorization="APPROVED",
                authorization_reference="owner/ref/revision",
                authorization_actor="owner",
            ).snapshot
            self.assertEqual(revised.state["risk"], "R3")
            self.assertEqual(revised.state["allowed_paths"], ["app.py", "security.py"])
            self.assertEqual(revised.state["authorization"]["reference"], "owner/ref/revision")

    def test_dirty_and_non_git_bootstrap_fail_before_canonical_state(self):
        with generic_repo("dirty-bootstrap") as root:
            (root / "app.py").write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(KernelError, "clean product baseline"):
                BuildOS(root, package_root=PACKAGE).bootstrap(request())
            self.assertFalse(paths(root).current.exists())
        with tempfile.TemporaryDirectory(prefix="buildos-nongit-") as td:
            root = Path(td)
            (root / "app.py").write_text("x = 1\n", encoding="utf-8")
            with self.assertRaisesRegex(KernelError, "requires a Git repository"):
                BuildOS(root, package_root=PACKAGE).bootstrap(request())
            self.assertFalse(paths(root).current.exists())
        with generic_repo("tracked-control") as root:
            (root / ".buildos").mkdir()
            (root / ".buildos" / "user-owned.txt").write_text("collision\n", encoding="utf-8")
            run_git(root, "add", "-f", ".buildos/user-owned.txt")
            run_git(root, "commit", "-qm", "tracked reserved path")
            with self.assertRaisesRegex(KernelError, "tracked .buildos control path"):
                BuildOS(root, package_root=PACKAGE).bootstrap(request())
            self.assertFalse(paths(root).current.exists())
        with generic_repo("subdir-root") as root:
            nested = root / "src"
            nested.mkdir()
            with self.assertRaisesRegex(KernelError, "Git worktree top-level"):
                BuildOS(nested, package_root=PACKAGE).bootstrap(request())
            self.assertFalse(paths(nested).current.exists())

    def test_bootstrap_git_exclude_boundary_leaves_no_canonical_partial_state(self):
        for point in ("before_git_exclude", "after_git_exclude"):
            with self.subTest(point=point), generic_repo(f"exclude-{point}") as root:
                osys = BuildOS(root, package_root=PACKAGE)
                with self.assertRaises(InjectedFailure):
                    osys.bootstrap(request(), configured_failures=point)
                self.assertFalse(paths(root).current.exists())
                started = osys.bootstrap(request()).snapshot
                self.assertEqual(started.state["phase"], "ACTIVE")

    def test_risk_floor_scope_and_dotfile_normalization_fail_closed(self):
        resolved = validate_task_request(request(risk="R0", side_effect="DELETE", owner_authorization="APPROVED", authorization_reference="owner/delete", authorization_actor="owner"))
        self.assertEqual(resolved["risk"], "R3")
        with generic_repo("dotfile") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request(allowed_paths=["env"]))
            (root / ".env").write_text("SECRET=not-a-real-secret\n", encoding="utf-8")
            run_git(root, "add", ".env")
            run_git(root, "commit", "-qm", "add dotfile")
            with self.assertRaisesRegex(KernelError, "exceeds allowed paths"):
                osys.record_commit()
            self.assertEqual(read_current(root).state["phase"], "ACTIVE")
        with generic_repo("casefold-scope") as root:
            (root / "Secret.txt").write_text("baseline\n", encoding="utf-8")
            run_git(root, "add", "Secret.txt")
            run_git(root, "commit", "-qm", "case-sensitive fixture")
            run_git(root, "config", "core.ignorecase", "false")
            if os.name != "nt":
                run_git(root, "config", "core.ignorecase", "true")
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request(allowed_paths=["*"], prohibited_paths=["secret.txt"]))
            (root / "Secret.txt").write_text("changed\n", encoding="utf-8")
            run_git(root, "add", "Secret.txt")
            run_git(root, "commit", "-qm", "change prohibited case variant")
            with self.assertRaisesRegex(KernelError, "prohibited paths"):
                osys.record_commit()

    def test_read_only_and_deletion_risk_cannot_be_underdeclared(self):
        with generic_repo("read-only") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request("READ-ONLY", "R0", side_effect="READ_ONLY", allowed_paths=[]))
            ready = osys.validate(checks=[check_command()], inspected_by="auditor").snapshot
            self.assertEqual(ready.state["phase"], "ASSURANCE_READY")
            self.assertEqual(osys.close().snapshot.state["phase"], "CLOSED")
        with generic_repo("read-only-write") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request("READ-ONLY", "R0", side_effect="READ_ONLY", allowed_paths=[]))
            product_commit(root)
            status = osys.status()
            self.assertTrue(status["read_only_baseline_violation"])
            self.assertIn("READ_ONLY baseline changed", status["work_packet"]["next_action"])
            with self.assertRaisesRegex(KernelError, "READ_ONLY tasks cannot record"):
                osys.record_commit()
            self.assertEqual(read_current(root).state["phase"], "ACTIVE")
        with generic_repo("undeclared-delete") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request("DELETE-UNDER-R1", "R1", side_effect="WRITE", allowed_paths=["app.py"]))
            run_git(root, "rm", "app.py")
            run_git(root, "commit", "-qm", "delete underdeclared")
            with self.assertRaisesRegex(KernelError, "authorized R3 DELETE"):
                osys.record_commit()
            self.assertEqual(read_current(root).state["phase"], "ACTIVE")
        with generic_repo("empty-write") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            run_git(root, "commit", "--allow-empty", "-qm", "no product delta")
            with self.assertRaisesRegex(KernelError, "at least one committed product path"):
                osys.record_commit()

    def test_late_prohibited_change_cannot_be_laundered_by_revision(self):
        with generic_repo("scope-launder") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request(allowed_paths=["app.py", "secret.txt"], prohibited_paths=["secret.txt"]))
            product_commit(root, "# accepted c1\n")
            osys.record_commit()
            ready = osys.validate(checks=[check_command()], inspected_by="worker-a")
            evidence = root / ready.snapshot.state["evidence"][0]["path"]
            original = evidence.read_bytes()
            (root / "secret.txt").write_text("prohibited product delta\n", encoding="utf-8")
            run_git(root, "add", "secret.txt")
            run_git(root, "commit", "-qm", "late prohibited delta")
            with self.assertRaisesRegex(KernelError, "changed after validation"):
                osys.close()
            osys.revise(reason="fresh proof without rebasing away old delta")
            product_commit(root, "# accepted c3\n")
            with self.assertRaisesRegex(KernelError, "prohibited paths"):
                osys.record_commit()
            self.assertEqual(evidence.read_bytes(), original)

    def test_git_unavailable_or_observation_error_cannot_close_or_record(self):
        with generic_repo("git-disappears") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            product_commit(root)
            osys.record_commit()
            ready = osys.validate(checks=[check_command()], inspected_by="worker-a")
            evidence = root / ready.snapshot.state["evidence"][0]["path"]
            original = evidence.read_bytes()
            git_dir = root / ".git"
            hidden = root / ".git-away"
            git_dir.rename(hidden)
            try:
                with self.assertRaisesRegex(KernelError, "observable Git ancestry"):
                    osys.close()
                self.assertEqual(read_current(root).state["phase"], "ASSURANCE_READY")
                self.assertEqual(evidence.read_bytes(), original)
            finally:
                hidden.rename(git_dir)
        with generic_repo("git-observation-error") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            product_commit(root)
            before = read_current(root)
            with patch("buildos.git_adapter.changed_paths", side_effect=RuntimeError("injected git diff failure")):
                with self.assertRaisesRegex(RuntimeError, "injected git diff failure"):
                    osys.record_commit()
            self.assertEqual(read_current(root).generation_hash, before.generation_hash)

    def test_git_change_between_snapshot_and_pointer_swap_blocks_close(self):
        with generic_repo("close-git-toctou") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            product_commit(root)
            osys.record_commit()
            ready = osys.validate(checks=[check_command()], inspected_by="worker-a").snapshot
            evidence = root / ready.state["evidence"][0]["path"]
            before = evidence.read_bytes()
            from buildos import facade as facade_module
            original_guard = facade_module._assert_git_unchanged
            advanced = False

            def advance_then_check(*args, **kwargs):
                nonlocal advanced
                if not advanced:
                    advanced = True
                    product_commit(root, "# concurrent product advance\n")
                return original_guard(*args, **kwargs)

            with patch("buildos.facade._assert_git_unchanged", side_effect=advance_then_check):
                with self.assertRaisesRegex(KernelError, "changed before canonical commit"):
                    osys.close()
            self.assertEqual(read_current(root).generation_hash, ready.generation_hash)
            self.assertEqual(read_current(root).state["phase"], "ASSURANCE_READY")
            self.assertEqual(evidence.read_bytes(), before)
            with self.assertRaisesRegex(KernelError, "changed after validation"):
                osys.close()

    def test_closed_retry_rechecks_product_state_instead_of_returning_blind_pass(self):
        with generic_repo("closed-retry") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            product_commit(root)
            osys.record_commit()
            osys.validate(checks=[check_command()], inspected_by="worker-a")
            closed = osys.close().snapshot
            product_commit(root, "# post-close product change\n")
            with self.assertRaisesRegex(KernelError, "closed proof does not cover"):
                osys.close()
            self.assertEqual(read_current(root).generation_hash, closed.generation_hash)
            status = osys.status()
            self.assertTrue(status["unvalidated_product_change"])
            self.assertIn("new revision", status["work_packet"]["next_action"])


class AssuranceAdversarialTests(unittest.TestCase):
    def _r3_ready_for_validation(self, root: Path) -> BuildOS:
        osys = BuildOS(root, package_root=PACKAGE)
        osys.bootstrap(request(
            "R3-EVIDENCE", "R3",
            owner_authorization="APPROVED",
            authorization_reference="owner/ref/evidence",
            authorization_actor="owner",
        ))
        product_commit(root)
        osys.record_commit()
        return osys

    def test_operation_id_cannot_escape_evidence_directory_or_forge_proof(self):
        with generic_repo("unsafe-op") as root:
            osys = self._r3_ready_for_validation(root)
            with self.assertRaisesRegex(KernelError, "filename-safe"):
                osys.validate(
                    checks=[check_command()], inspected_by="worker-a",
                    reviewer="reviewer-b", review_reference="review/ref",
                    rollback_check=rollback_command(), op_id="../forged",
                )
            self.assertFalse((root.parent / "forged").exists())
        with generic_repo("forged-proof") as root:
            osys = self._r3_ready_for_validation(root)
            op_id = "forged"
            key = hashlib.sha256(op_id.encode("utf-8")).hexdigest()[:24]
            final = root / ".buildos" / "evidence" / "R3-EVIDENCE" / "r001" / f"validation-{key}.json"
            final.parent.mkdir(parents=True, exist_ok=True)
            final.write_text(json.dumps({
                "operation_id": op_id,
                "task_id": "R3-EVIDENCE",
                "revision": 1,
                "target_sha": run_git(root, "rev-parse", "HEAD"),
            }), encoding="utf-8")
            forged = final.read_bytes()
            with self.assertRaisesRegex(KernelError, "another transition"):
                osys.validate(
                    checks=[check_command()], inspected_by="worker-a",
                    reviewer="reviewer-b", review_reference="review/ref",
                    rollback_check=rollback_command(), op_id=op_id,
                )
            self.assertEqual(read_current(root).state["phase"], "PRODUCT_COMMITTED")
            self.assertEqual(final.read_bytes(), forged)

    def test_r3_rollback_is_distinct_and_validation_retry_cannot_change_checks(self):
        with generic_repo("distinct-rollback") as root:
            osys = self._r3_ready_for_validation(root)
            with self.assertRaisesRegex(KernelError, "non-empty"):
                osys.validate(
                    checks=[" "], inspected_by="worker-a",
                    reviewer="reviewer-b", review_reference="review/ref",
                    rollback_check=rollback_command(),
                )
            with self.assertRaisesRegex(KernelError, "independent reviewer"):
                osys.validate(
                    checks=[check_command()], inspected_by="worker-a",
                    reviewer=" ", review_reference=" ", rollback_check=rollback_command(),
                )
            with self.assertRaisesRegex(KernelError, "cannot be WORKER, AUTO, or SELF"):
                osys.validate(
                    checks=[check_command()], inspected_by="worker-a",
                    reviewer="AUTO", review_reference="review/ref", rollback_check=rollback_command(),
                )
            with self.assertRaisesRegex(KernelError, "rollback/recovery check"):
                osys.validate(
                    checks=[check_command()], inspected_by="worker-a",
                    reviewer="reviewer-b", review_reference="review/ref", rollback_check=" ",
                )
            with self.assertRaisesRegex(KernelError, "must be distinct"):
                osys.validate(
                    checks=[check_command()], inspected_by="worker-a",
                    reviewer="reviewer-b", review_reference="review/ref",
                    rollback_check=check_command(),
                )
            ready = osys.validate(
                checks=[check_command()], inspected_by="worker-a",
                reviewer="reviewer-b", review_reference="review/ref",
                rollback_check=rollback_command(),
            )
            evidence = root / ready.snapshot.state["evidence"][0]["path"]
            before = evidence.read_bytes()
            changed = f'"{sys.executable}" -c "import pathlib; pathlib.Path(\'should-not-run\').write_text(\'x\')"'
            with self.assertRaisesRegex(KernelError, "another transition"):
                osys.validate(
                    checks=[changed], inspected_by="worker-a",
                    reviewer="reviewer-b", review_reference="review/ref",
                    rollback_check=rollback_command(),
                )
            self.assertFalse((root / "should-not-run").exists())
            self.assertEqual(evidence.read_bytes(), before)

    def test_concurrent_same_operation_validation_never_mismatches_evidence_hash(self):
        with generic_repo("concurrent-evidence") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            product_commit(root)
            osys.record_commit()
            barrier = threading.Barrier(2)
            from buildos import facade as facade_module
            original_run = facade_module._run_check

            def synchronized_check(*args, **kwargs):
                barrier.wait(timeout=10)
                return original_run(*args, **kwargs)

            def validate_once():
                try:
                    value = osys.validate(
                        checks=[check_command()],
                        inspected_by="worker-a",
                        op_id="concurrent-validation",
                    )
                    return ("PASS", value.snapshot.generation_hash)
                except Exception as exc:  # The losing publisher must fail closed, never corrupt proof.
                    return ("ERROR", exc)

            with patch("buildos.facade._run_check", side_effect=synchronized_check):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    outcomes = [future.result(timeout=30) for future in [pool.submit(validate_once), pool.submit(validate_once)]]
            self.assertTrue(any(kind == "PASS" for kind, _ in outcomes), outcomes)
            errors = [value for kind, value in outcomes if kind == "ERROR"]
            self.assertTrue(all(isinstance(value, KernelError) for value in errors), outcomes)
            current = read_current(root)
            self.assertEqual(current.state["phase"], "ASSURANCE_READY")
            reference = current.state["evidence"][-1]
            evidence = root / reference["path"]
            actual = hashlib.sha256(evidence.read_bytes()).hexdigest()
            self.assertEqual(reference["sha256"], actual)
            self.assertEqual(current.state["assurance"]["evidence_sha"], actual)


class GovernorTelemetryAdversarialTests(unittest.TestCase):
    def test_measured_usage_cannot_be_overridden_down_and_rollover_resets_epoch(self):
        with generic_repo("measured-governor") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            state = osys.bootstrap(request()).snapshot.state
            ingest(root, state, [{
                "role": "PRODUCTIVE",
                "raw_input_tokens": 70_000,
                "model_requests": 5,
                "projected_prompt_tokens": 64_000,
            }], source="TEST")
            status = osys.status(usage={"projected_prompt_tokens": 1, "requests_in_epoch": 0})
            self.assertEqual(status["governor"]["action"], "ROLLOVER_REQUIRED")
            self.assertEqual(status["governor"]["projected_prompt_tokens"], 64_000)
            self.assertEqual(status["governor"]["requests_in_epoch"], 5)
            self.assertEqual(status["work_packet"]["next_action"], "run rollover before further model work")
            rolled = osys.rollover(thread_id="fresh-thread")
            self.assertEqual(rolled.snapshot.state["context"]["epoch"], 2)
            after = osys.status()
            self.assertEqual(after["governor"]["action"], "CONTINUE_UNMEASURED")
            self.assertEqual(after["telemetry"]["current_epoch_max_projected_prompt_tokens"], 0)

    def test_cumulative_snapshots_use_latest_not_sum(self):
        with generic_repo("cumulative") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            state = osys.bootstrap(request()).snapshot.state
            ingest(root, state, [
                {"thread_id": "t", "role": "PRODUCTIVE", "raw_input_tokens": 100, "model_requests": 1, "cumulative": True},
                {"thread_id": "t", "role": "PRODUCTIVE", "raw_input_tokens": 200, "model_requests": 2, "cumulative": True},
            ], source="CUMULATIVE_TEST")
            measured = summarize(root, state)
            self.assertEqual(measured["productive_raw_input_tokens"], 200)
            self.assertEqual(measured["productive_model_requests"], 2)

    def test_missing_prompt_stays_unmeasured_and_record_ids_are_task_scoped(self):
        with generic_repo("telemetry-truth") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            first = osys.bootstrap(request("TELEMETRY-A")).snapshot.state
            ingest(root, first, [{"record_id": "1", "role": "PRODUCTIVE", "raw_input_tokens": 1_000}], source="SOURCE")
            status = osys.status()
            self.assertEqual(status["telemetry"]["current_epoch_measurement"], "UNMEASURED")
            self.assertEqual(status["governor"]["measurement"], "UNMEASURED")
            osys.abort(reason="first telemetry fixture complete")
            second = osys.bootstrap(request("TELEMETRY-B")).snapshot.state
            count = ingest(root, second, [{
                "record_id": "1",
                "role": "PRODUCTIVE",
                "projected_prompt_tokens": 64_000,
                "model_requests": 1,
            }], source="SOURCE")
            self.assertEqual(count, 1)
            measured = summarize(root, second)
            self.assertEqual(measured["records"], 1)
            self.assertEqual(measured["current_epoch_max_projected_prompt_tokens"], 64_000)

    def test_control_overhead_is_automatic_and_epoch_binding_is_strict(self):
        with generic_repo("control-telemetry") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            self.assertTrue(osys.record_control_action("bootstrap", "PASS"))
            control_only = summarize(root, read_current(root).state)
            self.assertEqual(control_only["control_tool_actions"], 1)
            self.assertEqual(control_only["status"], "UNMEASURED")
            self.assertEqual(control_only["measurement_coverage"], "PRODUCTIVE_UNMEASURED_CONTROL_MEASURED")
            rolled = osys.rollover(force=True, thread_id="bound-thread").snapshot
            with self.assertRaisesRegex(TelemetryError, "thread"):
                ingest(root, rolled.state, [{"role": "PRODUCTIVE", "model_requests": 1}], source="MISSING_THREAD")
            with self.assertRaisesRegex(TelemetryError, "epoch identity"):
                ingest(root, rolled.state, [{
                    "role": "PRODUCTIVE",
                    "model_requests": 1,
                    "thread_id": "bound-thread",
                    "epoch_id": "wrong-epoch",
                }], source="WRONG_EPOCH")
            with self.assertRaisesRegex(TelemetryError, "epoch number"):
                ingest(root, rolled.state, [{
                    "role": "PRODUCTIVE",
                    "model_requests": 1,
                    "thread_id": "bound-thread",
                    "epoch": 1,
                }], source="OLD_EPOCH")

    def test_initial_epoch_telemetry_cannot_mix_multiple_threads(self):
        with generic_repo("initial-thread-binding") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            state = osys.bootstrap(request()).snapshot.state
            ingest(root, state, [{
                "thread_id": "thread-a",
                "role": "PRODUCTIVE",
                "projected_prompt_tokens": 1_000,
                "model_requests": 1,
            }], source="THREAD_SOURCE")
            with self.assertRaisesRegex(TelemetryError, "multiple productive threads"):
                ingest(root, state, [{
                    "thread_id": "thread-b",
                    "role": "PRODUCTIVE",
                    "projected_prompt_tokens": 2_000,
                    "model_requests": 1,
                }], source="THREAD_SOURCE")

    def test_real_codex_turns_are_counted_from_task_epoch_baseline(self):
        def notification(turn: int, total_input: int) -> dict:
            return {
                "method": "thread/tokenUsage/updated",
                "params": {
                    "threadId": "thread-real",
                    "turnId": f"turn-{turn}",
                    "tokenUsage": {
                        "total": {"inputTokens": total_input, "cachedInputTokens": total_input // 2, "outputTokens": turn * 10},
                        "last": {"inputTokens": 1_000 + turn},
                    },
                },
            }

        with generic_repo("codex-baseline") as root:
            source = root / ".buildos" / "runtime" / "codex-source.jsonl"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("".join(json.dumps(notification(i, i * 1_000)) + "\n" for i in range(1, 3)), encoding="utf-8")
            env = {
                "BUILDOS_TELEMETRY_FILE": "",
                "AI_BUILD_OS_CODEX_APP_SERVER_USAGE_FILE": str(source),
                "AI_BUILD_OS_USAGE_FILE": "",
                "BUILDOS_THREAD_ID": "thread-real",
                "AI_BUILD_OS_CODEX_THREAD_ID": "",
            }
            with patch.dict(os.environ, env, clear=False):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                with source.open("a", encoding="utf-8") as handle:
                    for i in range(3, 8):
                        handle.write(json.dumps(notification(i, i * 1_000)) + "\n")
                status = osys.status()
                self.assertEqual(status["telemetry"]["current_epoch_model_requests"], 5)
                self.assertEqual(status["telemetry"]["current_epoch_requests_measurement"], "MEASURED")
                self.assertEqual(status["governor"]["action"], "ROLLOVER_REQUIRED")
                osys.rollover(thread_id="thread-next")
                after = osys.status()
                self.assertNotEqual(after["governor"]["action"], "ROLLOVER_REQUIRED")

    def test_project_policy_cannot_claim_hard_or_weaken_field_limits(self):
        with self.assertRaisesRegex(KernelError, "SUPERVISORY or BOUNDARY"):
            decide({"projected_prompt_tokens": 1}, {"enforcement": "HARD"})
        with tempfile.TemporaryDirectory(prefix="buildos-policy-") as td:
            root = Path(td)
            (root / ".buildos-policy.json").write_text(json.dumps({
                "context_governor": {
                    "compact_prompt_tokens": 40_000,
                    "rollover_prompt_tokens": 64_000,
                    "requests_per_epoch": 6,
                    "absolute_prompt_cap": 128_000,
                    "enforcement": "SUPERVISORY",
                }
            }), encoding="utf-8")
            with self.assertRaisesRegex(KernelError, "exceeds the kernel safety maximum"):
                load_policy(root)
        with self.assertRaisesRegex(KernelError, "non-negative integer"):
            decide({"projected_prompt_tokens": "not-a-number"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
