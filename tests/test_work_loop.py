from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from buildos.facade import BuildOS
from buildos.grounding import GroundingError
from buildos.store import read_current
from buildos.work_contract import validate_contract
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

    def _bootstrap(self, root: Path, contract_path: Path, grounding_path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable, str(AI), "--root", str(root), "bootstrap",
                "--work-contract", str(contract_path), "--grounding", str(grounding_path),
            ],
            text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=60,
        )

    def _work(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(AI), "--root", str(root), "work", *args],
            text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=120,
        )

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
                    "target": {**contract()["target"], "repository": str(root.resolve())},
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

    def test_compiled_scope_reaches_existing_commit_boundary(self):
        with tempfile.TemporaryDirectory(prefix="work-loop-") as raw:
            root, contract_path, grounding_path = self._inputs(Path(raw))
            completed = self._bootstrap(root, contract_path, grounding_path)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            (root / "scripts" / "ai.py").write_text("print('implemented')\n", encoding="utf-8")
            run_git(root, "add", "scripts/ai.py")
            run_git(root, "commit", "-m", "implement grounded scope")
            result = BuildOS(root).record_commit()
            self.assertEqual(result.snapshot.state["phase"], "PRODUCT_COMMITTED")
            self.assertEqual(result.snapshot.state["work_loop"]["action_rights"]["requested_action_status"], "GRANTED")

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
            finished = self._work(root, "--assure")
            self.assertEqual(finished.returncode, 0, finished.stdout + finished.stderr)
            finished_value = json.loads(finished.stdout)
            self.assertEqual(finished_value["status"], "COMPLETE")
            self.assertEqual(
                [row["kind"] for row in finished_value["transitions"]],
                ["PRODUCT_COMMIT", "VALIDATION", "CLOSE"],
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
            self.assertEqual(value["status"], "READY_FOR_WORK")
            self.assertEqual(value["transitions"], [])
            self.assertTrue(value["current"]["git"]["product_dirty"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
