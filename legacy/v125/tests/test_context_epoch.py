from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


PACKAGE = Path(__file__).resolve().parents[1]
SCRIPT = PACKAGE / "skills" / "project-lifecycle-bootstrap" / "scripts" / "context_epoch.py"
SPEC = importlib.util.spec_from_file_location("context_epoch", SCRIPT)
assert SPEC and SPEC.loader
epoch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(epoch)

from buildos.governor import decide


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, text=True, capture_output=True)


def status(root: Path, *, epoch_no: int, thread: str, generation: str) -> dict:
    return {
        "status": "PASS", "task_id": "EPOCH-1", "revision": 1, "phase": "PRODUCT_COMMITTED",
        "generation_hash": generation,
        "state": {"task_id": "EPOCH-1", "revision": 1, "phase": "PRODUCT_COMMITTED", "accepted_ref": "HEAD",
                  "context": {"epoch": epoch_no, "epoch_id": f"epoch-{epoch_no}", "thread_id": thread},
                  "lease": {"holder": "WORKER"}},
    }


class FakeRpc:
    calls: list[tuple[str, dict]] = []

    def __enter__(self): return self
    def __exit__(self, *_): return None
    def call(self, method: str, params: dict):
        self.calls.append((method, params))
        if method == "thread/resume": return {"model": "gpt-5.4"}
        if method == "thread/goal/get": return {"goal": {"objective": "preserve this exact product objective", "status": "active"}}
        if method == "thread/read": return {"thread": {"turns": []}}
        if method == "thread/start": return {"thread": {"id": "successor-1", "turns": []}}
        return {}


class ContextEpochTests(unittest.TestCase):
    def test_objective_hash_is_normalized_and_bounded(self):
        self.assertEqual(epoch.objective_hash("goal\n"), epoch.objective_hash("goal"))
        with self.assertRaises(epoch.ContextEpochError): epoch.objective_hash("x" * 4097)

    def test_dirty_binding_reuses_the_continuity_algorithm(self):
        with tempfile.TemporaryDirectory(prefix="context-epoch-dirty-") as raw:
            root = Path(raw); git(root, "init"); git(root, "config", "user.email", "test@example.invalid"); git(root, "config", "user.name", "Test")
            (root / "app.py").write_text("ok\n", encoding="utf-8"); git(root, "add", "app.py"); git(root, "commit", "-m", "base")
            fingerprint = epoch._continuity_dirty_fingerprint(PACKAGE, root)
            self.assertRegex(fingerprint, r"^[0-9a-f]{64}$")

    def test_handoff_reuses_rollover_and_fences_predecessor(self):
        with tempfile.TemporaryDirectory(prefix="context-epoch-") as raw:
            root = Path(raw); git(root, "init"); git(root, "config", "user.email", "test@example.invalid"); git(root, "config", "user.name", "Test")
            (root / "app.py").write_text("ok\n", encoding="utf-8"); git(root, "add", "app.py"); git(root, "commit", "-m", "base")
            sidecar = root / "sidecar.json"; sidecar.write_text(json.dumps({"accepted_ref": "HEAD", "resolved_accepted_sha": epoch._git(root, "rev-parse", "HEAD"), "git": {"dirty": {"fingerprint": "clean"}}}), encoding="utf-8")
            first, second = status(root, epoch_no=1, thread="predecessor-1", generation="before-hash"), status(root, epoch_no=2, thread="successor-1", generation="after-hash")
            capsule = {"status": "SAFE_TO_CONTINUE", "sidecar": str(sidecar), "sidecar_hash": "initial", "capsule": "schema=buildos.working-state-capsule.v1\nstatus=SAFE_TO_CONTINUE"}
            args = epoch.parser().parse_args([
                "--root", str(root), "handoff", "--compaction-status", "ATTEMPTED_INEFFECTIVE",
                "--compaction-evidence", "proof/compact", "--post-compaction-evidence", "proof/real-request",
                "--projected-prompt-tokens", "180000", "--model-context-window", "200000",
                "--material-work-remains", "YES", "--atomic-operation-complete", "YES",
            ])
            FakeRpc.calls = []
            rollover_commands: list[list[str]] = []
            def rollover_json(command, **_):
                rollover_commands.append(command)
                return {"status": "PASS", "generation_hash": "after-hash"}
            with mock.patch.object(epoch, "Rpc", FakeRpc), \
                 mock.patch.object(epoch, "_state", side_effect=[first, second]), \
                 mock.patch.object(epoch, "_sidecar_capsule", return_value=capsule), \
                 mock.patch.object(epoch, "_checkpoint", return_value={"status": "PASS", "sidecar_hash": "checkpoint"}), \
                 mock.patch.object(epoch, "_continuity_dirty_fingerprint", return_value="clean"), \
                 mock.patch.object(epoch, "_post_compaction_observation", return_value={"action": "COMPACT_REQUIRED", "latest_prompt_tokens": 180000}), \
                 mock.patch.object(epoch, "_json_output", side_effect=rollover_json):
                result = epoch.command_handoff(args)
            receipt = json.loads(Path(result["receipt"]).read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(receipt["predecessor"]["thread_id"], "predecessor-1")
            self.assertEqual(receipt["successor"]["thread_id"], "successor-1")
            self.assertEqual(receipt["successor"]["generation_hash"], "after-hash")
            self.assertEqual(receipt["goal"]["objective_sha256"], epoch.objective_hash("preserve this exact product objective"))
            self.assertEqual(receipt["worker"], "WORKER")
            self.assertEqual(receipt["git"]["accepted_ref"], "HEAD")
            self.assertIn("--force", rollover_commands[0])
            self.assertIn(("thread/archive", {"threadId": "predecessor-1"}), FakeRpc.calls)
            injected = [call for call in FakeRpc.calls if call[0] == "thread/inject_items"]
            self.assertEqual(len(injected), 1)
            self.assertIn("CONTEXT_EPOCH_SUCCESSOR_BOOTSTRAP_V1", injected[0][1]["items"][0]["content"][0]["text"])
            activated = [call for call in FakeRpc.calls if call[0] == "thread/goal/set" and call[1]["threadId"] == "successor-1"]
            self.assertEqual(activated[-1][1]["status"], "active")

    def test_post_compaction_requires_a_real_measurement_and_existing_governor_cut_signal(self):
        args = epoch.parser().parse_args([
            "--root", ".", "handoff", "--compaction-status", "ATTEMPTED_INEFFECTIVE",
            "--compaction-evidence", "proof/compact", "--post-compaction-evidence", "proof/real",
            "--projected-prompt-tokens", "160000", "--model-context-window", "200000",
            "--material-work-remains", "YES", "--atomic-operation-complete", "YES",
        ])
        with mock.patch.object(epoch, "_json_output", return_value={"status": "OK", "governor": {
            "action": "COMPACT_REQUIRED", "reason": "SAME_CHAT_COMPACTION_THRESHOLD", "measurement": "MEASURED",
            "latest_prompt_tokens": 160000, "model_context_window": 200000, "compaction_status": "ATTEMPTED_INEFFECTIVE",
        }}):
            observed = epoch._post_compaction_observation(PACKAGE, Path.cwd(), args)
        self.assertEqual(observed["action"], "COMPACT_REQUIRED")
        args.projected_prompt_tokens = 0
        with self.assertRaisesRegex(epoch.ContextEpochError, "non-zero real"):
            epoch._post_compaction_observation(PACKAGE, Path.cwd(), args)

    def test_cut_safety_keeps_safe_closeout_in_context_and_allows_only_the_unsafe_fallback(self):
        args = epoch.parser().parse_args([
            "--root", ".", "handoff", "--compaction-status", "UNAVAILABLE", "--compaction-evidence", "proof/compact",
            "--post-compaction-evidence", "proof/real", "--projected-prompt-tokens", "160000", "--model-context-window", "200000",
            "--material-work-remains", "YES", "--atomic-operation-complete", "NO",
        ])
        with self.assertRaisesRegex(epoch.ContextEpochError, "atomic operation"):
            epoch._assert_cut_safety(args)
        # Ordinary material work retains the pre-existing context-epoch path.
        args.atomic_operation_complete = "YES"
        self.assertEqual(epoch._assert_cut_safety(args), "CONTEXT_EPOCH_ELIGIBLE_FOR_MATERIAL_WORK")
        # Closeout does not create an epoch while its current context is safe.
        args.material_work_remains = "NO"; args.closeout_only = "YES"
        with self.assertRaisesRegex(epoch.ContextEpochError, "same-context continuation is safe"):
            epoch._assert_cut_safety(args)
        # Nor does a declared unavailable runtime turn into an unsafe fallback.
        args.would_continuing_same_context_violate_headroom_safety = "YES"; args.context_epoch_available = "NO"
        with self.assertRaisesRegex(epoch.ContextEpochError, "capability is unavailable"):
            epoch._assert_cut_safety(args)
        args.context_epoch_available = "YES"
        self.assertEqual(epoch._assert_cut_safety(args), epoch.SAFE_CLOSEOUT_ELIGIBILITY)

    def test_exact_field_fixture_is_eligible_for_safe_closeout_epoch(self):
        # Exact regression: 199742 / 258400 is COMPACT_REQUIRED, not a normal
        # 80-percent rollover. The existing compact-first adapter may cut only
        # after failed/unavailable compaction and an unsafe continuation.
        args = epoch.parser().parse_args([
            "--root", ".", "handoff", "--compaction-status", "UNAVAILABLE", "--compaction-evidence", "field/no-native-compaction",
            "--post-compaction-evidence", "field/prompt-199742", "--projected-prompt-tokens", "199742", "--model-context-window", "258400",
            "--material-work-remains", "NO", "--atomic-operation-complete", "YES", "--closeout-only", "YES",
            "--would-continuing-same-context-violate-headroom-safety", "YES", "--context-epoch-available", "YES",
        ])
        self.assertEqual(epoch._assert_cut_safety(args), "CONTEXT_EPOCH_ELIGIBLE_FOR_SAFE_CLOSEOUT")
        with mock.patch.object(epoch, "_json_output", return_value={"status": "PASS", "governor": {
            "action": "COMPACT_REQUIRED", "reason": "SAME_CHAT_COMPACTION_THRESHOLD", "measurement": "MEASURED",
            "latest_prompt_tokens": 199742, "model_context_window": 258400, "compaction_status": "UNAVAILABLE",
        }}):
            observed = epoch._post_compaction_observation(PACKAGE, Path.cwd(), args)
        self.assertEqual(observed["action"], "COMPACT_REQUIRED")

    def test_closeout_compaction_first_and_hard_stop_decision_matrix(self):
        base = {"model_context_window": 258400}
        # Effective compaction is represented by the real post-compaction
        # footprint: it stays in one chat and never needs this adapter.
        self.assertEqual(decide({**base, "projected_prompt_tokens": 53_000})["action"], "CONTINUE")
        safe_closeout = epoch.parser().parse_args([
            "--root", ".", "handoff", "--compaction-status", "UNAVAILABLE", "--compaction-evidence", "proof/unavailable",
            "--post-compaction-evidence", "proof/current", "--projected-prompt-tokens", "199742", "--model-context-window", "258400",
            "--material-work-remains", "NO", "--atomic-operation-complete", "YES", "--closeout-only", "YES",
        ])
        # Unavailable compaction alone is not enough when the current context
        # is still safe.
        with self.assertRaisesRegex(epoch.ContextEpochError, "same-context continuation is safe"):
            epoch._assert_cut_safety(safe_closeout)
        safe_closeout.would_continuing_same_context_violate_headroom_safety = "YES"
        self.assertEqual(epoch._assert_cut_safety(safe_closeout), epoch.SAFE_CLOSEOUT_ELIGIBILITY)
        safe_closeout.compaction_status = "ATTEMPTED_INEFFECTIVE"
        self.assertEqual(epoch._assert_cut_safety(safe_closeout), epoch.SAFE_CLOSEOUT_ELIGIBILITY)
        # HARD_STOP is still a legal fresh-epoch cut only through this bounded
        # fallback, never an instruction to continue the oversized context.
        self.assertEqual(decide({**base, "projected_prompt_tokens": 232560})["action"], "HARD_STOP")

    def test_closeout_successor_preserves_committed_identity_and_is_zero_history(self):
        with tempfile.TemporaryDirectory(prefix="context-epoch-closeout-") as raw:
            root = Path(raw); git(root, "init"); git(root, "config", "user.email", "test@example.invalid"); git(root, "config", "user.name", "Test")
            (root / "app.py").write_text("ok\n", encoding="utf-8"); git(root, "add", "app.py"); git(root, "commit", "-m", "base")
            sidecar = root / "sidecar.json"; sidecar.write_text(json.dumps({"accepted_ref": "HEAD", "resolved_accepted_sha": epoch._git(root, "rev-parse", "HEAD"), "git": {"dirty": {"fingerprint": "clean"}}}), encoding="utf-8")
            first, second = status(root, epoch_no=1, thread="predecessor-1", generation="before-hash"), status(root, epoch_no=2, thread="successor-1", generation="after-hash")
            capsule = {"status": "SAFE_TO_CONTINUE", "sidecar": str(sidecar), "sidecar_hash": "initial", "capsule": "schema=buildos.working-state-capsule.v1\ntargeted_reads=immutable-evidence"}
            args = epoch.parser().parse_args([
                "--root", str(root), "handoff", "--compaction-status", "UNAVAILABLE", "--compaction-evidence", "field/no-native-compaction",
                "--post-compaction-evidence", "field/prompt-199742", "--projected-prompt-tokens", "199742", "--model-context-window", "258400",
                "--material-work-remains", "NO", "--atomic-operation-complete", "YES", "--closeout-only", "YES",
                "--would-continuing-same-context-violate-headroom-safety", "YES",
            ])
            FakeRpc.calls = []
            with mock.patch.object(epoch, "Rpc", FakeRpc), \
                 mock.patch.object(epoch, "_state", side_effect=[first, second]), \
                 mock.patch.object(epoch, "_sidecar_capsule", return_value=capsule), \
                 mock.patch.object(epoch, "_checkpoint", return_value={"status": "PASS", "sidecar_hash": "checkpoint"}), \
                 mock.patch.object(epoch, "_continuity_dirty_fingerprint", return_value="clean"), \
                 mock.patch.object(epoch, "_post_compaction_observation", return_value={"action": "COMPACT_REQUIRED", "latest_prompt_tokens": 199742}), \
                 mock.patch.object(epoch, "_json_output", return_value={"status": "PASS", "generation_hash": "after-hash"}):
                result = epoch.command_handoff(args)
            receipt = json.loads(Path(result["receipt"]).read_text(encoding="utf-8"))
            self.assertEqual((receipt["task_id"], receipt["revision"], receipt["lifecycle_phase"]), ("EPOCH-1", 1, "PRODUCT_COMMITTED"))
            self.assertTrue(receipt["cut_safety"]["closeout_only"])
            self.assertEqual(receipt["cut_safety"]["eligibility"], epoch.SAFE_CLOSEOUT_ELIGIBILITY)
            self.assertIn("validation, assurance, and close", receipt["next_action"])
            injected = [call for call in FakeRpc.calls if call[0] == "thread/inject_items"]
            self.assertEqual(len(injected), 1)
            payload = injected[0][1]["items"][0]["content"][0]["text"]
            self.assertIn("Do not request or replay predecessor conversation, tool output", payload)
            self.assertNotIn("predecessor-1", payload)

    def test_second_closeout_epoch_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="context-epoch-one-closeout-") as raw:
            root = Path(raw)
            receipt = {"cut_safety": {"closeout_only": True}}
            path = epoch._receipt_path(root, "EPOCH-1", 1, 2, "prior")
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(receipt), encoding="utf-8")
            self.assertTrue(epoch._prior_closeout_epoch_exists(root, "EPOCH-1", 1))

    def test_duplicate_successor_race_never_reactivates_the_stale_predecessor(self):
        with tempfile.TemporaryDirectory(prefix="context-epoch-race-") as raw:
            root = Path(raw); git(root, "init"); git(root, "config", "user.email", "test@example.invalid"); git(root, "config", "user.name", "Test")
            (root / "app.py").write_text("ok\n", encoding="utf-8"); git(root, "add", "app.py"); git(root, "commit", "-m", "base")
            args = epoch.parser().parse_args([
                "--root", str(root), "handoff", "--compaction-status", "UNAVAILABLE", "--compaction-evidence", "proof/compact",
                "--post-compaction-evidence", "proof/real", "--projected-prompt-tokens", "160000", "--model-context-window", "200000",
                "--material-work-remains", "YES", "--atomic-operation-complete", "YES",
            ])
            first = status(root, epoch_no=1, thread="predecessor-1", generation="before")
            winning = status(root, epoch_no=2, thread="competing-successor", generation="winner")
            FakeRpc.calls = []
            with mock.patch.object(epoch, "Rpc", FakeRpc), \
                 mock.patch.object(epoch, "_state", side_effect=[first, winning]), \
                 mock.patch.object(epoch, "_sidecar_capsule", return_value={"sidecar_hash": "before", "capsule": "capsule"}), \
                 mock.patch.object(epoch, "_post_compaction_observation", return_value={"action": "ROLLOVER_REQUIRED"}), \
                 mock.patch.object(epoch, "_json_output", side_effect=epoch.ContextEpochError("CAS lost")):
                with self.assertRaisesRegex(epoch.ContextEpochError, "CAS lost"):
                    epoch.command_handoff(args)
            stale_reactivations = [call for call in FakeRpc.calls if call[0] == "thread/goal/set" and call[1]["threadId"] == "predecessor-1" and call[1]["status"] == "active"]
            self.assertEqual(stale_reactivations, [])
            self.assertIn(("thread/archive", {"threadId": "successor-1"}), FakeRpc.calls)

    def test_preflight_rejects_wrong_thread_and_tampered_receipt(self):
        with tempfile.TemporaryDirectory(prefix="context-epoch-preflight-") as raw:
            root = Path(raw); git(root, "init"); git(root, "config", "user.email", "test@example.invalid"); git(root, "config", "user.name", "Test")
            (root / "app.py").write_text("ok\n", encoding="utf-8"); git(root, "add", "app.py"); git(root, "commit", "-m", "base")
            sidecar = root / "sidecar.json"; sidecar.write_text("{}", encoding="utf-8")
            observed = status(root, epoch_no=2, thread="successor-1", generation="after-hash")
            receipt = {"schema": epoch.SCHEMA, "capability": epoch.RUNTIME_CAPABILITY, "self_hash": "", "task_id": "EPOCH-1", "revision": 1,
                       "operation_id": "op", "lifecycle_phase": "PRODUCT_COMMITTED", "worker": "WORKER",
                       "predecessor": {"epoch": 1, "epoch_id": "epoch-1", "thread_id": "old", "generation_hash": "before"},
                       "successor": {"epoch": 2, "epoch_id": "epoch-2", "thread_id": "successor-1", "generation_hash": "after-hash"},
                       "goal": {"objective_sha256": epoch.objective_hash("goal")}, "continuity": {"path": str(sidecar), "sha256": epoch.digest(sidecar.read_bytes()), "checkpoint_hash": "x"},
                       "capsule": {"sha256": epoch.digest(b"capsule"), "bytes": 7},
                       "git": {"worktree": epoch._worktree(root), "accepted_ref": "HEAD", "resolved_accepted_sha": epoch._git(root, "rev-parse", "HEAD"), "head": epoch._git(root, "rev-parse", "HEAD"), "tree": epoch._git(root, "rev-parse", "HEAD^{tree}"), "dirty_fingerprint": "clean"}}
            target = epoch._receipt_path(root, "EPOCH-1", 1, 2, "op"); epoch._publish_receipt(target, receipt)
            with self.assertRaisesRegex(epoch.ContextEpochError, "bound context-epoch successor"):
                epoch._preflight_receipt(root, observed, "wrong-thread")
            with mock.patch.object(epoch, "_runtime_goal_hash", return_value=epoch.objective_hash("different goal")):
                with self.assertRaisesRegex(epoch.ContextEpochError, "Goal-objective hash"):
                    epoch._preflight_receipt(root, observed, "successor-1", verify_runtime_goal=True)
            target.write_text("{}", encoding="utf-8")
            with self.assertRaises(epoch.ContextEpochError): epoch._preflight_receipt(root, observed, "successor-1")

    def test_preflight_rejects_live_capsule_mismatch(self):
        with tempfile.TemporaryDirectory(prefix="context-epoch-capsule-") as raw:
            root = Path(raw); git(root, "init"); git(root, "config", "user.email", "test@example.invalid"); git(root, "config", "user.name", "Test")
            (root / "app.py").write_text("ok\n", encoding="utf-8"); git(root, "add", "app.py"); git(root, "commit", "-m", "base")
            sidecar = root / "sidecar.json"; sidecar.write_text("{}", encoding="utf-8")
            observed = status(root, epoch_no=2, thread="successor-1", generation="after-hash")
            receipt = {"schema": epoch.SCHEMA, "capability": epoch.RUNTIME_CAPABILITY, "self_hash": "", "task_id": "EPOCH-1", "revision": 1,
                       "operation_id": "op", "lifecycle_phase": "PRODUCT_COMMITTED", "next_action": "read", "worker": "WORKER",
                       "predecessor": {"epoch": 1, "epoch_id": "epoch-1", "thread_id": "old", "generation_hash": "before"},
                       "successor": {"epoch": 2, "epoch_id": "epoch-2", "thread_id": "successor-1", "generation_hash": "after-hash"},
                       "goal": {"objective_sha256": epoch.objective_hash("goal")}, "continuity": {"path": str(sidecar), "sha256": epoch.digest(sidecar.read_bytes()), "checkpoint_hash": "x"},
                       "capsule": {"sha256": epoch.digest(b"capsule"), "bytes": 7},
                       "git": {"worktree": epoch._worktree(root), "accepted_ref": "HEAD", "resolved_accepted_sha": epoch._git(root, "rev-parse", "HEAD"), "head": epoch._git(root, "rev-parse", "HEAD"), "tree": epoch._git(root, "rev-parse", "HEAD^{tree}"), "dirty_fingerprint": "clean"}}
            epoch._publish_receipt(epoch._receipt_path(root, "EPOCH-1", 1, 2, "op"), receipt)
            with mock.patch.object(epoch, "_sidecar_capsule", return_value={"capsule": "capsule"}), \
                 mock.patch.object(epoch, "_continuity_dirty_fingerprint", return_value="clean"):
                epoch._preflight_receipt(root, observed, "successor-1", package=PACKAGE)
            with mock.patch.object(epoch, "_sidecar_capsule", return_value={"capsule": "changed"}), \
                 mock.patch.object(epoch, "_continuity_dirty_fingerprint", return_value="clean"):
                with self.assertRaisesRegex(epoch.ContextEpochError, "Capsule hash"):
                    epoch._preflight_receipt(root, observed, "successor-1", package=PACKAGE)

    def test_recover_classifies_all_handoff_crash_boundaries_without_split_brain(self):
        args = epoch.parser().parse_args(["--root", ".", "recover"])
        predecessor = status(Path.cwd(), epoch_no=1, thread="predecessor-1", generation="before")
        successor = status(Path.cwd(), epoch_no=2, thread="successor-1", generation="after")
        # Before CAS (including predecessor pause and fresh successor creation),
        # CURRENT still declares the predecessor.  After CAS, receipt absence or
        # mismatch stays fail-closed; a verified receipt names only successor.
        boundaries = {
            "before_predecessor_pause": (predecessor, None, "PREDECESSOR_CANONICAL"),
            "after_predecessor_pause": (predecessor, None, "PREDECESSOR_CANONICAL"),
            "after_successor_created": (predecessor, None, "PREDECESSOR_CANONICAL"),
            "after_rollover_cas": (successor, epoch.ContextEpochError("missing receipt"), "RECOVERY_REQUIRED"),
            "after_sidecar_checkpoint": (successor, epoch.ContextEpochError("missing receipt"), "RECOVERY_REQUIRED"),
            "after_receipt_publish": (successor, {"self_hash": "receipt"}, "SUCCESSOR_CANONICAL"),
            "during_successor_verification": (successor, {"self_hash": "receipt"}, "SUCCESSOR_CANONICAL"),
            "after_successor_activation": (successor, {"self_hash": "receipt"}, "SUCCESSOR_CANONICAL"),
        }
        for boundary, (observed, result, expected) in boundaries.items():
            with self.subTest(boundary=boundary), mock.patch.object(epoch, "_state", return_value=observed):
                if isinstance(result, Exception):
                    with mock.patch.object(epoch, "_preflight_receipt", side_effect=result):
                        self.assertEqual(epoch.command_recover(args)["status"], expected)
                else:
                    with mock.patch.object(epoch, "_preflight_receipt", return_value=result):
                        self.assertEqual(epoch.command_recover(args)["status"], expected)


if __name__ == "__main__": unittest.main()
