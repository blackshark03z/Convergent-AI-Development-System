from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1]
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))

from buildos.facade import BuildOS
from buildos.governor import decide
from buildos.model import KernelError
from buildos.store import InjectedFailure, RECEIPT_SCHEMA, RecoveryRequired, paths, read_current, scan_generations
from buildos.telemetry import TelemetryError, ingest, summarize


def run_git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, timeout=30, check=False)
    if proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed\nOUT={proc.stdout}\nERR={proc.stderr}")
    return proc.stdout.strip()


@contextmanager
def generic_repo(name: str = "generic"):
    with tempfile.TemporaryDirectory(prefix=f"buildos-{name}-") as td:
        root = Path(td)
        run_git(root, "init", "-q")
        run_git(root, "config", "user.email", "generic@example.invalid")
        run_git(root, "config", "user.name", "Generic Fixture")
        (root / "app.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
        (root / "README.md").write_text("# Unrelated calculator fixture\n", encoding="utf-8")
        run_git(root, "add", "app.py", "README.md")
        run_git(root, "commit", "-qm", "generic baseline")
        yield root


def request(task_id: str = "GENERIC-LOW", risk: str = "R1", **extra):
    value = {
        "task_id": task_id,
        "outcome": "calculator change is correct",
        "acceptance": ["the focused calculator check passes"],
        "allowed_paths": ["app.py"],
        "risk": risk,
        "side_effect": "WRITE",
        "worker_id": "worker-a",
    }
    value.update(extra)
    return value


def check_command() -> str:
    return f'"{sys.executable}" -c "import pathlib; assert pathlib.Path(\'app.py\').is_file()"'


def rollback_command() -> str:
    return f'"{sys.executable}" -c "import pathlib; assert pathlib.Path(\'.git\').is_dir()"'


def product_commit(root: Path, marker: str = "# product change\n") -> str:
    with (root / "app.py").open("a", encoding="utf-8") as handle:
        handle.write(marker)
    run_git(root, "add", "app.py")
    run_git(root, "commit", "-qm", marker.strip("# \n") or "product change")
    return run_git(root, "rev-parse", "HEAD")


class LifecycleTests(unittest.TestCase):
    def test_low_risk_product_commit_validation_and_descendant_close(self):
        with generic_repo("low-risk") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            started = osys.bootstrap(request())
            self.assertEqual(started.snapshot.state["phase"], "ACTIVE")
            self.assertTrue((root / ".buildos/control/CURRENT").is_file())
            c1 = product_commit(root)
            status = osys.status()
            self.assertTrue(status["unadopted_product_commit"])
            recorded = osys.record_commit()
            self.assertEqual(recorded.snapshot.state["product_commit"]["sha"], c1)
            validated = osys.validate(checks=[check_command()], inspected_by="agent:worker-a")
            self.assertEqual(validated.snapshot.state["phase"], "ASSURANCE_READY")
            target = validated.snapshot.state["assurance"]["target_sha"]
            self.assertEqual(target, c1)
            evidence = root / validated.snapshot.state["evidence"][0]["path"]
            evidence_hash = hashlib.sha256(evidence.read_bytes()).hexdigest()
            # A legitimate tree-equivalent descendant is not stale lifecycle
            # state and never requires destructive reopen.
            run_git(root, "commit", "--allow-empty", "-qm", "integration metadata")
            closed = osys.close()
            self.assertEqual(closed.snapshot.state["phase"], "CLOSED")
            self.assertEqual(closed.snapshot.state["assurance"]["head_refresh"], "LEGITIMATE_DESCENDANT")
            self.assertEqual(hashlib.sha256(evidence.read_bytes()).hexdigest(), evidence_hash)

    def test_product_change_after_validation_requires_fresh_revision(self):
        with generic_repo("late-change") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            product_commit(root)
            osys.record_commit()
            ready = osys.validate(checks=[check_command()], inspected_by="agent:worker-a")
            evidence = root / ready.snapshot.state["evidence"][0]["path"]
            before = evidence.read_bytes()
            product_commit(root, "# unvalidated late change\n")
            with self.assertRaisesRegex(KernelError, "changed after validation"):
                osys.close()
            self.assertEqual(read_current(root).state["phase"], "ASSURANCE_READY")
            self.assertEqual(evidence.read_bytes(), before)
            revised = osys.revise(reason="late product scope requires fresh proof")
            self.assertEqual(revised.snapshot.state["revision"], 2)
            self.assertTrue(evidence.is_file())
            self.assertEqual(hashlib.sha256(evidence.read_bytes()).hexdigest(), hashlib.sha256(before).hexdigest())

    def test_r3_authorization_and_assurance_fail_closed(self):
        with generic_repo("r3") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            with self.assertRaisesRegex(KernelError, "R3 requires"):
                osys.bootstrap(request("GENERIC-R3", "R3"))
            self.assertFalse((root / ".buildos/control/CURRENT").exists())
            with self.assertRaisesRegex(KernelError, "self-approve"):
                osys.bootstrap(request(
                    "GENERIC-R3", "R3",
                    owner_authorization="APPROVED",
                    authorization_reference="owner-ticket-42",
                    authorization_actor="worker-a",
                ))
            self.assertFalse((root / ".buildos/control/CURRENT").exists())
            osys.bootstrap(request(
                "GENERIC-R3", "R3",
                owner_authorization="APPROVED",
                authorization_reference="owner-ticket-42",
                authorization_actor="owner",
            ))
            product_commit(root)
            osys.record_commit()
            with self.assertRaisesRegex(KernelError, "independent reviewer"):
                osys.validate(checks=[check_command()], inspected_by="worker-a")
            self.assertEqual(read_current(root).state["phase"], "PRODUCT_COMMITTED")
            with self.assertRaisesRegex(KernelError, "rollback"):
                osys.validate(
                    checks=[check_command()], inspected_by="worker-a",
                    reviewer="reviewer-b", review_reference="review-42",
                )
            ready = osys.validate(
                checks=[check_command()], inspected_by="worker-a",
                reviewer="reviewer-b", review_reference="review-42",
                rollback_check=rollback_command(),
            )
            self.assertEqual(ready.snapshot.state["phase"], "ASSURANCE_READY")
            evidence_path = root / ready.snapshot.state["evidence"][0]["path"]
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            self.assertEqual(evidence["checks"][0]["role"], "ACCEPTANCE")
            self.assertEqual(evidence["rollback_check"]["role"], "ROLLBACK_RECOVERY")

    def test_explicit_skill_is_guidance_only_and_no_skill_is_valid(self):
        with generic_repo("skill") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            started = osys.bootstrap(request(skill="python-change-v122"))
            packet = json.loads((root / ".buildos/runtime/WORK_PACKET.json").read_text(encoding="utf-8"))
            self.assertEqual(packet["skill"]["authority"], "GUIDANCE_ONLY")
            self.assertEqual(packet["skill"]["id"], "python-change-v122")
            self.assertEqual(started.snapshot.state["risk"], "R1")
        with generic_repo("no-skill") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            self.assertIsNone(json.loads((root / ".buildos/runtime/WORK_PACKET.json").read_text(encoding="utf-8"))["skill"])


class GovernorTelemetryTests(unittest.TestCase):
    def test_field_thresholds_and_rollover_identity(self):
        base = {"model_context_window": 258_400}
        self.assertEqual(decide({**base, "projected_prompt_tokens": 129_199})["action"], "CONTINUE")
        self.assertEqual(decide({**base, "projected_prompt_tokens": 129_200})["action"], "HEADROOM_WARNING")
        self.assertEqual(decide({**base, "projected_prompt_tokens": 180_879})["action"], "HEADROOM_WARNING")
        self.assertEqual(decide({**base, "projected_prompt_tokens": 180_880})["action"], "COMPACT_REQUIRED")
        self.assertEqual(decide({**base, "projected_prompt_tokens": 206_720})["action"], "COMPACT_REQUIRED")
        rollover = decide({
            **base,
            "projected_prompt_tokens": 206_720,
            "compaction_status": "UNAVAILABLE",
            "compaction_evidence": "desktop/no-compact-capability",
        })
        self.assertEqual(rollover["action"], "ROLLOVER_REQUIRED")
        self.assertTrue(rollover["rollover_fallback_eligible"])
        self.assertEqual(decide({**base, "projected_prompt_tokens": 232_559})["action"], "COMPACT_REQUIRED")
        hard = decide({**base, "projected_prompt_tokens": 232_560})
        self.assertEqual(hard["action"], "HARD_STOP")
        self.assertFalse(hard["hard_interception_guaranteed"])
        self.assertEqual(decide({})["measurement"], "UNMEASURED")
        self.assertEqual(decide({})["context_window_source"], "CONSERVATIVE_FALLBACK")
        # Request count is evidence only, including the two recovered traces.
        self.assertEqual(decide({**base, "projected_prompt_tokens": 95_985, "requests_in_epoch": 59})["action"], "CONTINUE")
        # A different runtime W proves proportional rather than model-specific thresholds.
        other = decide({"model_context_window": 200_000, "projected_prompt_tokens": 140_000})
        self.assertEqual(other["action"], "COMPACT_REQUIRED")
        self.assertEqual(other["thresholds"], {"warning": 100_000, "compact": 140_000, "rollover": 160_000, "hard_stop": 175_000})
        reserve = decide({
            **base,
            "projected_prompt_tokens": 208_400,
            "known_payload_output_reserve_tokens": 50_000,
        })
        self.assertEqual(reserve["thresholds"]["hard_stop"], 208_400)
        self.assertEqual(reserve["action"], "HARD_STOP")
        self.assertEqual(decide({"runtime_overflow": True})["action"], "HARD_STOP")
        with self.assertRaisesRegex(KernelError, "evidence reference"):
            decide({**base, "projected_prompt_tokens": 206_720, "compaction_status": "UNAVAILABLE"})
        quality = decide({
            **base,
            "projected_prompt_tokens": 10_000,
            "persistent_post_compaction_loss": "DEMONSTRABLE_STATE_LOSS",
            "compaction_evidence": "review/state-loss-after-compact",
        })
        self.assertEqual(quality["action"], "ROLLOVER_REQUIRED")
        with generic_repo("rollover") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            first = osys.bootstrap(request()).snapshot
            with self.assertRaisesRegex(KernelError, "rollover requires a governor signal"):
                osys.rollover(
                    projected_prompt_tokens=180_880,
                    model_context_window=258_400,
                    thread_id="premature-thread",
                )
            with self.assertRaisesRegex(KernelError, "rollover requires a governor signal"):
                osys.rollover(
                    projected_prompt_tokens=232_560,
                    model_context_window=258_400,
                    thread_id="hard-stop-without-compact-evidence",
                )
            rolled = osys.rollover(
                projected_prompt_tokens=206_720,
                model_context_window=258_400,
                compaction_status="ATTEMPTED_INEFFECTIVE",
                compaction_evidence="trace/compact-attempt-1",
                thread_id="thread-b",
            ).snapshot
            self.assertEqual((rolled.state["task_id"], rolled.state["revision"]), (first.state["task_id"], first.state["revision"]))
            self.assertEqual(rolled.state["context"]["epoch"], 2)
            self.assertNotEqual(rolled.state["context"]["epoch_id"], first.state["context"]["epoch_id"])

    def test_telemetry_available_unavailable_and_identity_binding(self):
        with generic_repo("telemetry") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            state = osys.bootstrap(request()).snapshot.state
            absent = summarize(root, state)
            self.assertEqual(absent["status"], "UNMEASURED")
            self.assertEqual(absent["measurement_coverage"], "UNMEASURED")
            absent_status = osys.status()
            self.assertEqual(absent_status["governor"]["cache_economics"], {
                "role": "ADVISORY_ONLY",
                "cached_input_tokens": None,
                "noncached_input_tokens": None,
                "cache_write_input_tokens": None,
            })
            count = ingest(root, state, [
                {"role": "PRODUCTIVE", "raw_input_tokens": 1000, "cached_input_tokens": 700, "model_requests": 2, "tool_actions": 3, "projected_prompt_tokens": 41000},
                {"role": "CONTROL", "raw_input_tokens": 30, "model_requests": 1, "tool_actions": 2},
            ], source="TEST")
            self.assertEqual(count, 2)
            self.assertEqual(ingest(root, state, [
                {"role": "PRODUCTIVE", "raw_input_tokens": 1000, "cached_input_tokens": 700, "model_requests": 2, "tool_actions": 3, "projected_prompt_tokens": 41000},
            ], source="TEST"), 0)
            measured = summarize(root, state)
            self.assertEqual(measured["productive_model_requests"], 2)
            self.assertEqual(measured["productive_noncached_input_tokens"], 300)
            self.assertEqual(measured["control_tool_actions"], 2)
            self.assertEqual(measured["max_projected_prompt_tokens"], 41000)
            economics = osys.status()["governor"]["cache_economics"]
            self.assertEqual(economics["cached_input_tokens"], 700)
            self.assertEqual(economics["noncached_input_tokens"], 300)
            self.assertIsNone(economics["cache_write_input_tokens"])
            with self.assertRaises(TelemetryError):
                ingest(root, state, [{"task_id": "OTHER", "revision": 1}], source="TEST")
            before_hash = read_current(root).generation_hash
            with (root / ".buildos/runtime/telemetry.jsonl").open("ab") as handle:
                handle.write(b'{"partial":')
            partial = summarize(root, state)
            self.assertEqual(partial["status"], "PARTIAL")
            self.assertEqual(read_current(root).generation_hash, before_hash)

    def test_compaction_rebaseline_keeps_peak_as_evidence_only(self):
        with generic_repo("compact-rebaseline") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            state = osys.bootstrap(request()).snapshot.state
            ingest(root, state, [{
                "role": "PRODUCTIVE",
                "projected_prompt_tokens": 185_000,
                "model_context_window": 258_400,
                "model_requests": 1,
            }], source="COMPACTION_REPLAY")
            self.assertEqual(osys.status()["governor"]["action"], "COMPACT_REQUIRED")
            ingest(root, state, [{
                "role": "PRODUCTIVE",
                "projected_prompt_tokens": 53_000,
                "peak_prompt_tokens": 185_000,
                "model_context_window": 258_400,
                "model_requests": 1,
            }], source="COMPACTION_REPLAY")
            status = osys.status()
            self.assertEqual(status["telemetry"]["current_epoch_latest_projected_prompt_tokens"], 53_000)
            self.assertEqual(status["telemetry"]["current_epoch_max_projected_prompt_tokens"], 185_000)
            self.assertEqual(status["governor"]["projected_prompt_tokens"], 53_000)
            self.assertEqual(status["governor"]["peak_prompt_tokens"], 185_000)
            self.assertEqual(status["governor"]["action"], "CONTINUE")
            economic_variant = decide({
                "projected_prompt_tokens": 53_000,
                "model_context_window": 258_400,
                "cached_input_tokens": 9_000_000,
                "noncached_input_tokens": 1,
                "cache_write_input_tokens": 7_000_000,
            })
            self.assertEqual(economic_variant["action"], "CONTINUE")
            self.assertEqual(economic_variant["cache_economics"]["role"], "ADVISORY_ONLY")


class TransactionTests(unittest.TestCase):
    STORE_POINTS = [
        "before_lock", "after_lock", "before_prepare", "after_prepare",
        "before_generation_write", "after_generation_write", "after_generation_publish",
        "before_pointer_swap", "after_pointer_swap", "before_commit_receipt", "after_commit_receipt",
        "after_verify", "after_projection",
    ]

    def _prepare(self, root: Path, kind: str):
        osys = BuildOS(root, package_root=PACKAGE)
        if kind == "bootstrap":
            return osys, lambda point: osys.bootstrap(request(), op_id="op-bootstrap", configured_failures=point), None, "ACTIVE"
        osys.bootstrap(request())
        if kind == "rollover":
            return osys, lambda point: osys.rollover(force=True, thread_id="thread-rollover", op_id="op-rollover", configured_failures=point), "ACTIVE", "ACTIVE"
        if kind == "abort":
            return osys, lambda point: osys.abort(reason="bounded stop", op_id="op-abort", configured_failures=point), "ACTIVE", "ABORTED"
        product_commit(root)
        if kind == "record-commit":
            return osys, lambda point: osys.record_commit(op_id="op-record", configured_failures=point), "ACTIVE", "PRODUCT_COMMITTED"
        osys.record_commit()
        if kind == "validate":
            return osys, lambda point: osys.validate(checks=[check_command()], inspected_by="worker-a", op_id="op-validate", configured_failures=point), "PRODUCT_COMMITTED", "ASSURANCE_READY"
        osys.validate(checks=[check_command()], inspected_by="worker-a")
        if kind == "close":
            return osys, lambda point: osys.close(op_id="op-close", configured_failures=point), "ASSURANCE_READY", "CLOSED"
        osys.close()
        if kind == "new-revision":
            return osys, lambda point: osys.revise(reason="new accepted scope", op_id="op-revise", configured_failures=point), "CLOSED", "ACTIVE"
        raise AssertionError(kind)

    def test_shared_store_failure_at_every_boundary(self):
        precommit = {
            "before_lock", "after_lock", "before_prepare", "after_prepare",
            "before_generation_write", "after_generation_write", "after_generation_publish", "before_pointer_swap",
        }
        for point in self.STORE_POINTS:
            with self.subTest(point=point), generic_repo(f"boundary-{point}") as root:
                osys = BuildOS(root, package_root=PACKAGE)
                first = osys.bootstrap(request()).snapshot
                with self.assertRaises(InjectedFailure):
                    osys.rollover(force=True, thread_id=f"thread-{point}", op_id=f"roll-{point}", configured_failures=point)
                current = read_current(root)
                if point in precommit:
                    self.assertEqual(current.generation_hash, first.generation_hash)
                else:
                    self.assertEqual(current.generation, first.generation + 1)
                    self.assertEqual(current.state["context"]["epoch"], 2)
                retry = osys.rollover(force=True, thread_id=f"thread-{point}", op_id=f"roll-{point}")
                self.assertEqual(retry.snapshot.state["context"]["epoch"], 2)
                self.assertLessEqual(retry.snapshot.generation, first.generation + 1)
                self.assertEqual(len(list(paths(root).receipts.glob(f"p{retry.snapshot.generation:08d}-*.json"))), 1)

    def test_every_mutating_command_at_each_meaningful_boundary_and_retry(self):
        kinds = ["bootstrap", "rollover", "record-commit", "validate", "close", "new-revision", "abort"]
        points = (
            "before_prepare", "after_generation_publish", "before_pointer_swap",
            "after_pointer_swap", "before_commit_receipt", "after_projection",
        )
        precommit = {"before_prepare", "after_generation_publish", "before_pointer_swap"}
        for kind in kinds:
            for point in points:
                with self.subTest(kind=kind, point=point), generic_repo(f"{kind}-{point}") as root:
                    osys, invoke, prior_phase, expected_phase = self._prepare(root, kind)
                    prior = read_current(root, allow_uninitialized=True)
                    prior_generation = prior.generation if prior else 0
                    with self.assertRaises(InjectedFailure):
                        invoke(point)
                    current = read_current(root, allow_uninitialized=True)
                    if point in precommit:
                        self.assertEqual(current.state["phase"] if current else None, prior_phase)
                        self.assertEqual(current.generation if current else 0, prior_generation)
                    else:
                        self.assertEqual(current.state["phase"], expected_phase)
                        self.assertEqual(current.generation, prior_generation + 1)
                    retry = invoke(None)
                    self.assertEqual(retry.snapshot.state["phase"], expected_phase)
                    self.assertEqual(retry.snapshot.generation, prior_generation + 1)
                    self.assertEqual(len(list(paths(root).receipts.glob(f"p{retry.snapshot.generation:08d}-*.json"))), 1)

    def test_evidence_boundaries_never_mutate_state_or_delete_proof(self):
        for point in ("before_evidence_prepare", "after_evidence_prepare", "before_evidence_publish", "after_evidence_publish"):
            with self.subTest(point=point), generic_repo(f"evidence-{point}") as root:
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                product_commit(root)
                before = osys.record_commit().snapshot
                with self.assertRaises(InjectedFailure):
                    osys.validate(
                        checks=[check_command()], inspected_by="worker-a",
                        op_id=f"evidence-{point}", configured_failures=point,
                    )
                self.assertEqual(read_current(root).generation_hash, before.generation_hash)
                published = list((root / ".buildos/evidence").rglob("validation-*.json"))
                published_bytes = published[0].read_bytes() if published else None
                ready = osys.validate(checks=[check_command()], inspected_by="worker-a", op_id=f"evidence-{point}")
                self.assertEqual(ready.snapshot.state["phase"], "ASSURANCE_READY")
                if published_bytes is not None:
                    self.assertEqual(published[0].read_bytes(), published_bytes)

    def test_partial_runtime_recovery_and_ambiguous_fork_fail_closed(self):
        with generic_repo("partial") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            first = osys.bootstrap(request()).snapshot
            packet = root / ".buildos/runtime/WORK_PACKET.json"
            packet.write_bytes(b'{"partial":')
            status = osys.status()
            self.assertEqual(status["generation_hash"], first.generation_hash)
            self.assertEqual(json.loads(packet.read_text(encoding="utf-8"))["state_hash"], first.generation_hash)
            bogus = paths(root).generations / "g99999999-deadbeefdeadbeef.json"
            bogus.write_bytes(b'{"partial":')
            recovery = osys.recover()
            self.assertEqual(recovery["status"], "OK")
            self.assertIn(bogus.name, recovery["invalid_generations"])
            # Unique missing pointer recovery is deterministic.
            paths(root).current.unlink()
            recovered = osys.recover()
            self.assertEqual(recovered["status"], "RECOVERED")
            self.assertEqual(read_current(root).generation_hash, first.generation_hash)
        with generic_repo("fork") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request())
            for key in ("fork-a", "fork-b"):
                with self.assertRaises(InjectedFailure):
                    osys.rollover(force=True, thread_id=f"thread-{key}", op_id=key, configured_failures="before_pointer_swap")
            # Recovery never promotes these prepared orphans.  Even if an
            # external actor forges two competing receipts, it fails closed.
            for item in [value for value in scan_generations(root)[0] if value.generation == 2]:
                receipt = {
                    "schema": RECEIPT_SCHEMA,
                    "generation": item.generation,
                    "generation_hash": item.generation_hash,
                    "file": item.filename,
                }
                target = paths(root).receipts / f"p-forged-{item.generation_hash[:16]}.json"
                target.write_text(json.dumps(receipt), encoding="utf-8")
            paths(root).current.unlink()
            with self.assertRaisesRegex(RecoveryRequired, "ambiguous commit receipts"):
                osys.recover()


class AdoptionAndCliTests(unittest.TestCase):
    def test_clean_unrelated_repo_adoption_low_risk_and_r3(self):
        # No YouTube files, schema, service, port, or package-local product
        # assumptions are present in either fixture.
        with generic_repo("adopt-low") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request("UNRELATED-LOW", "R1"))
            product_commit(root)
            osys.record_commit()
            osys.rollover(force=True, thread_id="fresh-thread")
            osys.validate(checks=[check_command()], inspected_by="generic-worker")
            closed = osys.close()
            self.assertEqual(closed.snapshot.state["phase"], "CLOSED")
            self.assertEqual(summarize(root, closed.snapshot.state)["status"], "UNMEASURED")
        with generic_repo("adopt-r3") as root:
            osys = BuildOS(root, package_root=PACKAGE)
            osys.bootstrap(request(
                "UNRELATED-R3", "R3",
                owner_authorization="APPROVED", authorization_reference="owner/ref/7", authorization_actor="owner",
            ))
            product_commit(root)
            osys.record_commit()
            osys.validate(
                checks=[check_command()], inspected_by="generic-worker",
                reviewer="independent-reviewer", review_reference="review/ref/7", rollback_check=rollback_command(),
            )
            self.assertEqual(osys.close().snapshot.state["phase"], "CLOSED")

    def test_compact_facade_passes_r3_authorization(self):
        script = PACKAGE / "scripts" / "ai.py"
        with generic_repo("cli-missing") as root:
            missing = subprocess.run([
                sys.executable, str(script), "--root", str(root), "bootstrap",
                "--task-id", "CLI-R3", "--outcome", "authorized change", "--risk", "R3", "--allow", "app.py",
            ], text=True, capture_output=True, timeout=30, check=False)
            self.assertEqual(missing.returncode, 2)
            self.assertFalse((root / ".buildos/control/CURRENT").exists())
            passed = subprocess.run([
                sys.executable, str(script), "--root", str(root), "bootstrap",
                "--task-id", "CLI-R3", "--outcome", "authorized change", "--risk", "R3", "--allow", "app.py",
                "--worker-id", "cli-worker", "--owner-authorization", "APPROVED",
                "--authorization-reference", "owner/ref/cli", "--authorization-actor", "owner",
            ], text=True, capture_output=True, timeout=30, check=False)
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
            self.assertEqual(json.loads(passed.stdout)["phase"], "ACTIVE")
            product_commit(root)
            recorded = subprocess.run([
                sys.executable, str(script), "--root", str(root), "record-commit",
            ], text=True, capture_output=True, timeout=30, check=False)
            self.assertEqual(recorded.returncode, 0, recorded.stdout + recorded.stderr)
            validated = subprocess.run([
                sys.executable, str(script), "--root", str(root), "validate",
                "--check", check_command(), "--inspected-by", "cli-worker",
                "--reviewer", "cli-reviewer", "--review-reference", "review/ref/cli",
                "--rollback-check", rollback_command(),
            ], text=True, capture_output=True, timeout=30, check=False)
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            closed = subprocess.run([
                sys.executable, str(script), "--root", str(root), "close",
            ], text=True, capture_output=True, timeout=30, check=False)
            self.assertEqual(closed.returncode, 0, closed.stdout + closed.stderr)
            self.assertEqual(json.loads(closed.stdout)["phase"], "CLOSED")
        help_text = subprocess.run([sys.executable, str(script), "--help"], text=True, capture_output=True, timeout=30, check=True).stdout
        self.assertNotIn("reopen", help_text)
        for command in ("bootstrap", "status", "next", "record-commit", "validate", "rollover", "close", "recover"):
            self.assertIn(command, help_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
