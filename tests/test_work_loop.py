from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from buildos import git_adapter
from buildos.facade import BuildOS
from buildos.grounding import GroundingError, verify_work_loop_evidence
from buildos.model import KernelError
from buildos.store import read_current
from buildos.work_contract import TRUSTED_CONTRACT_SHA256_ENV, validate_contract
from tests.test_grounding import report, repository, run_git
from tests.test_work_contract import contract


PACKAGE = Path(__file__).resolve().parents[1]
AI = PACKAGE / "scripts" / "ai.py"


def canonical_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


class WorkLoopBootstrapTests(unittest.TestCase):
    def _inputs(self, base: Path, *, contradicted_claim: str | None = None) -> tuple[Path, Path, Path]:
        root = base / "repo"
        observed = repository(root)
        value = contract()
        value["target"]["repository"] = str(root.resolve())
        value["target"]["ref"] = observed["branch"]
        normalized = validate_contract(value)
        digest = canonical_hash(normalized)
        grounding = report(
            root, observed, digest,
            claim_id=contradicted_claim or "repo.current_cli",
            outcome="CONTRADICTED" if contradicted_claim else "VERIFIED",
        )
        contract_path = base / "work-contract.json"
        grounding_path = base / "grounding.json"
        contract_path.write_text(json.dumps(normalized), encoding="utf-8")
        grounding_path.write_text(json.dumps(grounding), encoding="utf-8")
        return root, contract_path, grounding_path

    def _trusted_env(self, contract_path: Path) -> dict[str, str]:
        environment = os.environ.copy()
        environment[TRUSTED_CONTRACT_SHA256_ENV] = canonical_hash(
            json.loads(contract_path.read_text(encoding="utf-8")),
        )
        return environment

    def _bootstrap(
        self, root: Path, contract_path: Path, grounding_path: Path, *, trusted: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable, str(AI), "--root", str(root), "bootstrap",
                "--work-contract", str(contract_path), "--grounding", str(grounding_path),
            ],
            text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=60,
            env=self._trusted_env(contract_path) if trusted else {
                key: value for key, value in os.environ.items()
                if key != TRUSTED_CONTRACT_SHA256_ENV
            },
        )

    def _work(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        if "--work-contract" in args:
            contract_path = Path(args[args.index("--work-contract") + 1])
            environment = self._trusted_env(contract_path)
        return subprocess.run(
            [sys.executable, str(AI), "--root", str(root), "work", *args],
            text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=120,
            env=environment,
        )

    def test_initial_contract_requires_exact_trusted_launcher_binding_before_any_write(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(Path(raw))
            missing = self._bootstrap(root, contract_path, grounding_path, trusted=False)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("trusted launcher binding", missing.stdout + missing.stderr)
            self.assertFalse((root / ".buildos").exists())

            wrong_environment = os.environ.copy()
            wrong_environment[TRUSTED_CONTRACT_SHA256_ENV] = "0" * 64
            mismatch = subprocess.run(
                [
                    sys.executable, str(AI), "--root", str(root), "bootstrap",
                    "--work-contract", str(contract_path), "--grounding", str(grounding_path),
                ],
                text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=60,
                env=wrong_environment,
            )
            self.assertNotEqual(mismatch.returncode, 0)
            self.assertIn("does not match validated handoff", mismatch.stdout + mismatch.stderr)
            self.assertFalse((root / ".buildos").exists())

    def test_contract_and_grounding_compile_one_canonical_task_without_relay_args(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(Path(raw))
            completed = self._bootstrap(root, contract_path, grounding_path)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["task_id"], "BUILD-OS-VNEXT-r1")
            current = read_current(root)
            assert current is not None
            state = current.state
            self.assertEqual(state["outcome"], "Deliver an evidence-carrying Work Loop.")
            self.assertEqual(state["allowed_paths"], ["scripts/**"])
            self.assertEqual(state["enforcement"], "BOUNDARY")
            self.assertEqual(state["work_loop"]["action_rights"]["requested_action_status"], "GRANTED")
            self.assertEqual(
                state["work_loop"]["work_contract"]["hash"], canonical_hash(validate_contract(contract() | {
                    "target": {
                        **contract()["target"], "repository": str(root.resolve()),
                        "ref": git_adapter.snapshot(root)["branch"],
                    },
                })),
            )
            for section in ("work_contract", "grounding"):
                reference = state["work_loop"][section]["evidence"]
                artifact = root / reference["path"]
                self.assertTrue(artifact.is_file())
                self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(), reference["sha256"])
            packet = json.loads((root / ".buildos" / "runtime" / "WORK_PACKET.json").read_text(encoding="utf-8"))
            self.assertEqual(packet["state_hash"], current.generation_hash)
            self.assertEqual(
                packet["work_loop"]["work_contract_hash"],
                state["work_loop"]["work_contract"]["hash"],
            )
            self.assertEqual(packet["work_loop"]["repository"]["head"], state["base_git"]["head"])
            plan = BuildOS(root).assurance_plan()
            self.assertEqual(plan["work_loop"]["profile"], "WORKER_PROPORTIONAL")
            self.assertEqual(plan["work_loop"]["grounding_claims_reused"], ["repo.current_cli"])
            self.assertEqual(plan["work_loop"]["grounding_claims_reexecuted"], [])

    def test_identical_bootstrap_retry_is_idempotent(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(Path(raw))
            first = self._bootstrap(root, contract_path, grounding_path)
            second = self._bootstrap(root, contract_path, grounding_path)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertTrue(json.loads(second.stdout)["idempotent"])

    def test_bootstrap_retry_cannot_acknowledge_different_grounding_as_idempotent(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            base = Path(raw)
            root, contract_path, grounding_path = self._inputs(base)
            first = self._bootstrap(root, contract_path, grounding_path)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            before = read_current(root)
            assert before is not None
            changed = report(
                root, git_adapter.snapshot(root),
                before.state["work_loop"]["work_contract"]["hash"],
                outcome="CONTRADICTED",
            )
            grounding_path.write_text(json.dumps(changed), encoding="utf-8")
            second = self._bootstrap(root, contract_path, grounding_path)
            self.assertEqual(second.returncode, 2, second.stdout + second.stderr)
            self.assertIn("different grounding", second.stdout)
            after = read_current(root)
            assert after is not None
            self.assertEqual(after.generation_hash, before.generation_hash)

    def test_material_decision_blocks_before_control_state_or_product_mutation(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(
                Path(raw), contradicted_claim="acceptance.contract",
            )
            completed = self._bootstrap(root, contract_path, grounding_path)
            self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
            self.assertIn("decision_requests=decision-", completed.stdout)
            self.assertFalse((root / ".buildos").exists())

    def test_changed_handoff_evidence_fails_closed_on_next_operation(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(Path(raw))
            completed = self._bootstrap(root, contract_path, grounding_path)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            current = read_current(root)
            assert current is not None
            reference = current.state["work_loop"]["grounding"]["evidence"]
            (root / reference["path"]).write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(GroundingError, "missing or changed"):
                BuildOS(root).status()

    def test_canonical_binding_must_semantically_replay_from_immutable_evidence(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(Path(raw))
            completed = self._bootstrap(root, contract_path, grounding_path)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            current = read_current(root)
            assert current is not None

            forged_repository = deepcopy(current.state["work_loop"])
            forged_repository["grounding"]["repository"]["head"] = "f" * 40
            with self.assertRaisesRegex(GroundingError, "immutable evidence replay"):
                verify_work_loop_evidence(root, forged_repository)

            forged_rights = deepcopy(current.state["work_loop"])
            forged_rights["grounding"]["outcomes"]["repo.current_cli"] = "UNKNOWN"
            forged_rights["grounding"]["decision_requests"] = []
            with self.assertRaisesRegex(GroundingError, "action rights do not match"):
                verify_work_loop_evidence(root, forged_rights)

    def test_compiled_scope_reaches_existing_commit_boundary(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(Path(raw))
            completed = self._bootstrap(root, contract_path, grounding_path)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            (root / "scripts" / "ai.py").write_text("print('implemented')\n", encoding="utf-8")
            run_git(root, "add", "scripts/ai.py")
            run_git(root, "commit", "-m", "implement grounded scope")
            current = read_current(root)
            assert current is not None
            fresh = report(
                root, git_adapter.snapshot(root),
                current.state["work_loop"]["work_contract"]["hash"],
            )
            fresh_path = Path(raw) / "fresh-grounding.json"
            fresh_path.write_text(json.dumps(fresh), encoding="utf-8")
            result = BuildOS(root).advance(
                work_contract=contract_path, grounding_report=fresh_path,
            )
            self.assertEqual(
                [row["kind"] for row in result["transitions"]],
                ["GROUNDING_REFRESH", "PRODUCT_COMMIT"],
            )
            after = read_current(root)
            assert after is not None
            self.assertEqual(after.state["phase"], "PRODUCT_COMMITTED")
            self.assertEqual(after.state["work_loop"]["action_rights"]["requested_action_status"], "GRANTED")

    def test_work_loop_cannot_silently_revise_outside_new_contract(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(Path(raw))
            completed = self._bootstrap(root, contract_path, grounding_path)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            with self.assertRaisesRegex(ValueError, "fresh Work Contract"):
                BuildOS(root).revise(reason="silently change product intent")

    def test_inspect_is_strictly_read_only_for_buildos_state(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(Path(raw))
            completed = self._bootstrap(root, contract_path, grounding_path)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

            def snapshot_files() -> dict[str, tuple[int, int, str]]:
                return {
                    path.relative_to(root).as_posix(): (
                        path.stat().st_size,
                        path.stat().st_mtime_ns,
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                    )
                    for path in (root / ".buildos").rglob("*") if path.is_file()
                }

            before = snapshot_files()
            value = BuildOS(root).inspect()
            after = snapshot_files()
            self.assertTrue(value["read_only"])
            self.assertEqual(before, after)

    def test_inspect_cli_is_strictly_read_only_for_entire_repository(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(Path(raw))
            completed = self._bootstrap(root, contract_path, grounding_path)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

            def snapshot_files() -> dict[str, tuple[int, int, str]]:
                return {
                    path.relative_to(root).as_posix(): (
                        path.stat().st_size,
                        path.stat().st_mtime_ns,
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                    )
                    for path in root.rglob("*") if path.is_file()
                }

            before = snapshot_files()
            inspected = subprocess.run(
                [sys.executable, str(AI), "--root", str(root), "inspect"],
                text=True, encoding="utf-8", errors="replace",
                capture_output=True, timeout=30,
            )
            after = snapshot_files()
            self.assertEqual(inspected.returncode, 0, inspected.stdout + inspected.stderr)
            self.assertTrue(json.loads(inspected.stdout)["read_only"])
            self.assertEqual(before, after)

    def test_one_normal_work_facade_bootstraps_then_assures_and_closes(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(Path(raw))
            started = self._work(
                root, "--work-contract", str(contract_path), "--grounding", str(grounding_path),
            )
            self.assertEqual(started.returncode, 0, started.stdout + started.stderr)
            started_value = json.loads(started.stdout)
            self.assertEqual(started_value["status"], "READY_FOR_WORK")
            self.assertEqual([row["kind"] for row in started_value["transitions"]], ["BOOTSTRAP"])

            (root / "scripts" / "ai.py").write_text("print('implemented by normal work loop')\n", encoding="utf-8")
            run_git(root, "add", "scripts/ai.py")
            run_git(root, "commit", "-m", "implement")
            current = read_current(root)
            assert current is not None
            refreshed = report(
                root, git_adapter.snapshot(root),
                current.state["work_loop"]["work_contract"]["hash"],
            )
            grounding_path.write_text(json.dumps(refreshed), encoding="utf-8")
            finished = self._work(
                root, "--work-contract", str(contract_path),
                "--grounding", str(grounding_path), "--assure",
            )
            self.assertEqual(finished.returncode, 0, finished.stdout + finished.stderr)
            finished_value = json.loads(finished.stdout)
            self.assertEqual(finished_value["status"], "COMPLETE")
            self.assertEqual(
                [row["kind"] for row in finished_value["transitions"]],
                ["GROUNDING_REFRESH", "PRODUCT_COMMIT", "VALIDATION", "CLOSE"],
            )
            self.assertEqual(finished_value["current"]["phase"], "CLOSED")
            packet = finished_value["current"]["work_packet"]
            self.assertEqual(packet["work_loop"]["ship_readiness"], "READY_FOR_DECLARED_MODE")
            self.assertEqual(len(packet["evidence_index"]["handoff"]), 2)
            self.assertEqual(len(packet["evidence_index"]["assurance"]), 1)

    def test_work_facade_does_not_adopt_dirty_or_uncommitted_product_state(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(Path(raw))
            started = self._work(
                root, "--work-contract", str(contract_path), "--grounding", str(grounding_path),
            )
            self.assertEqual(started.returncode, 0, started.stdout + started.stderr)
            (root / "scripts" / "ai.py").write_text("print('dirty')\n", encoding="utf-8")
            observed = self._work(root, "--assure")
            self.assertEqual(observed.returncode, 0, observed.stdout + observed.stderr)
            value = json.loads(observed.stdout)
            self.assertEqual(value["status"], "GROUNDING_REFRESH_REQUIRED")
            self.assertEqual(value["transitions"], [])
            self.assertTrue(value["current"]["git"]["product_dirty"])

    def test_work_facade_cannot_validate_then_discard_changed_grounding(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            base = Path(raw)
            root, contract_path, grounding_path = self._inputs(base)
            started = self._work(
                root, "--work-contract", str(contract_path), "--grounding", str(grounding_path),
            )
            self.assertEqual(started.returncode, 0, started.stdout + started.stderr)
            before = read_current(root)
            assert before is not None

            (root / "scripts" / "other.py").write_text("print('unrelated committed change')\n", encoding="utf-8")
            run_git(root, "add", "scripts/other.py")
            run_git(root, "commit", "-m", "candidate implementation")
            observed = git_adapter.snapshot(root)
            fresh = report(
                root, observed, before.state["work_loop"]["work_contract"]["hash"],
                claim_id="acceptance.contract", outcome="CONTRADICTED",
            )
            fresh_path = base / "fresh-grounding.json"
            fresh_path.write_text(json.dumps(fresh), encoding="utf-8")

            result = BuildOS(root).advance(
                {}, work_contract=contract_path, grounding_report=fresh_path,
                run_assurance=True,
            )
            self.assertEqual(result["status"], "DECISION_REQUIRED")
            self.assertEqual([row["kind"] for row in result["transitions"]], ["GROUNDING_REFRESH"])
            after = read_current(root)
            assert after is not None
            self.assertNotEqual(after.generation_hash, before.generation_hash)
            self.assertEqual(after.state["phase"], "ACTIVE")
            self.assertEqual(
                after.state["work_loop"]["action_rights"]["requested_action_status"],
                "BLOCKED",
            )
            repeated = BuildOS(root).advance(run_assurance=True)
            self.assertEqual(repeated["status"], "DECISION_REQUIRED")
            self.assertEqual(repeated["transitions"], [])

    def test_changed_grounding_dependency_blocks_assurance_until_regrounded(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(Path(raw))
            started = self._work(
                root, "--work-contract", str(contract_path), "--grounding", str(grounding_path),
            )
            self.assertEqual(started.returncode, 0, started.stdout + started.stderr)
            (root / "scripts" / "ai.py").write_text("print('changed dependency')\n", encoding="utf-8")
            run_git(root, "add", "scripts/ai.py")
            run_git(root, "commit", "-m", "change grounded dependency")

            plan = BuildOS(root).assurance_plan()["work_loop"]
            self.assertEqual(plan["grounding_claims_reused"], [])
            self.assertEqual(plan["grounding_claims_reexecuted"], ["repo.current_cli"])
            blocked = BuildOS(root).advance(run_assurance=True)
            self.assertEqual(blocked["status"], "GROUNDING_REFRESH_REQUIRED")
            self.assertEqual(blocked["transitions"], [])
            with self.assertRaisesRegex(KernelError, "fresh Worker grounding"):
                BuildOS(root).validate(checks=[], inspected_by="WORKER")

    def test_worker_can_monotonically_adapt_local_action_boundary_from_fresh_grounding(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            base = Path(raw)
            root, contract_path, grounding_path = self._inputs(base)
            started = self._work(
                root, "--work-contract", str(contract_path), "--grounding", str(grounding_path),
            )
            self.assertEqual(started.returncode, 0, started.stdout + started.stderr)
            before = read_current(root)
            assert before is not None

            observed = git_adapter.snapshot(root)
            fresh = report(
                root, observed, before.state["work_loop"]["work_contract"]["hash"],
            )
            fresh["execution_request"]["allowed_paths"] = ["scripts/**", "tests/**"]
            fresh["execution_request"]["prohibited_paths"] = [".buildos/**", "secrets/**"]
            fresh["execution_request"]["acceptance_commands"] = [
                "python -m unittest", "python -m unittest tests.test_work_loop",
            ]
            fresh_path = base / "adapted-grounding.json"
            fresh_path.write_text(json.dumps(fresh), encoding="utf-8")

            result = BuildOS(root).advance(
                work_contract=contract_path, grounding_report=fresh_path,
            )
            self.assertEqual(result["status"], "READY_FOR_WORK")
            self.assertEqual([row["kind"] for row in result["transitions"]], ["GROUNDING_REFRESH"])
            after = read_current(root)
            assert after is not None
            self.assertEqual(after.state["allowed_paths"], ["scripts/**", "tests/**"])
            self.assertEqual(after.state["prohibited_paths"], [".buildos/**", "secrets/**"])
            self.assertEqual(
                after.state["work_loop"]["work_contract"]["hash"],
                before.state["work_loop"]["work_contract"]["hash"],
            )

    def test_worker_grounding_refresh_cannot_weaken_an_admitted_boundary(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            base = Path(raw)
            root, contract_path, grounding_path = self._inputs(base)
            started = self._work(
                root, "--work-contract", str(contract_path), "--grounding", str(grounding_path),
            )
            self.assertEqual(started.returncode, 0, started.stdout + started.stderr)
            before = read_current(root)
            assert before is not None

            weakened = report(
                root, git_adapter.snapshot(root),
                before.state["work_loop"]["work_contract"]["hash"],
            )
            weakened["execution_request"]["prohibited_paths"] = []
            weakened_path = base / "weakened-grounding.json"
            weakened_path.write_text(json.dumps(weakened), encoding="utf-8")

            with self.assertRaisesRegex(KernelError, "cannot remove a prohibited product path"):
                BuildOS(root).advance(
                    work_contract=contract_path, grounding_report=weakened_path,
                )
            after = read_current(root)
            assert after is not None
            self.assertEqual(after.generation_hash, before.generation_hash)

    def test_worker_cannot_retroactively_widen_scope_to_adopt_existing_commit(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            base = Path(raw)
            root, contract_path, grounding_path = self._inputs(base)
            started = self._work(
                root, "--work-contract", str(contract_path), "--grounding", str(grounding_path),
            )
            self.assertEqual(started.returncode, 0, started.stdout + started.stderr)
            before = read_current(root)
            assert before is not None

            (root / "outside.txt").write_text("already outside admitted scope\n", encoding="utf-8")
            run_git(root, "add", "outside.txt")
            run_git(root, "commit", "-m", "out-of-scope change before authorization")
            expanded = report(
                root, git_adapter.snapshot(root),
                before.state["work_loop"]["work_contract"]["hash"],
            )
            expanded["execution_request"]["allowed_paths"] = ["scripts/**", "outside.txt"]
            expanded_path = base / "late-expanded-grounding.json"
            expanded_path.write_text(json.dumps(expanded), encoding="utf-8")

            with self.assertRaisesRegex(KernelError, "late scope widening cannot authorize"):
                BuildOS(root).advance(
                    work_contract=contract_path, grounding_report=expanded_path,
                )
            after = read_current(root)
            assert after is not None
            self.assertEqual(after.generation_hash, before.generation_hash)
            self.assertEqual(after.state["phase"], "ACTIVE")
            self.assertEqual(after.state["allowed_paths"], ["scripts/**"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
