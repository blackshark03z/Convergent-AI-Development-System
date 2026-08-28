from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from buildos.cli import parser
from buildos.facade import BuildOS
from buildos.model import KernelError, validate_state
from buildos.store import find_task_revision, read_current, task_snapshots


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, timeout=30)
    if proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


@contextmanager
def repository(name: str):
    with tempfile.TemporaryDirectory(prefix=f"buildos-no-source-{name}-") as raw:
        root = Path(raw)
        git(root, "init", "-q")
        git(root, "config", "user.name", "Build OS Test")
        git(root, "config", "user.email", "buildos@example.invalid")
        (root / "app.py").write_text("value = 1\n", encoding="utf-8")
        git(root, "add", "app.py")
        git(root, "commit", "-qm", "base")
        yield root


def product_request(task_id: str) -> dict:
    return {
        "task_id": task_id,
        "outcome": "product source is updated",
        "acceptance": ["product acceptance passes"],
        "side_effect": "WRITE",
        "allowed_paths": ["app.py"],
        "worker_id": "WORKER",
    }


def runtime_request(task_id: str, *, risk: str = "R2") -> dict:
    value = {
        "task_id": task_id,
        "outcome": "runtime acceptance is recorded without a product delta",
        "acceptance": ["runtime acceptance evidence is valid"],
        "side_effect": "MUTATE_IN_PLACE",
        "product_change_mode": "NO_SOURCE_DELTA",
        "worker_id": "WORKER",
        "risk": risk,
    }
    if risk == "R3":
        value.update({
            "owner_authorization": "APPROVED",
            "authorization_reference": "owner/runtime-r3",
            "authorization_actor": "OWNER",
        })
    return value


CHECK = "git diff --quiet HEAD"
RUNTIME_ACCEPTANCE = "STORY-AUTO-TRIAL-A-ACCEPTED-2026-08-22"


class RuntimeNoSourceDeltaTests(unittest.TestCase):
    def test_normal_source_goal_still_requires_product_committed(self) -> None:
        with repository("normal-product") as root:
            osys = BuildOS(root)
            osys.bootstrap(product_request("PRODUCT-1"))
            with self.assertRaisesRegex(KernelError, "requires PRODUCT_COMMITTED"):
                osys.validate(checks=[CHECK], inspected_by="TEST")
            self.assertEqual(read_current(root).state["phase"], "ACTIVE")

    def test_runtime_only_unchanged_head_reaches_assurance_without_fake_commit_and_closes(self) -> None:
        with repository("success") as root:
            baseline = git(root, "rev-parse", "HEAD")
            osys = BuildOS(root)
            started = osys.bootstrap(runtime_request("RUNTIME-1")).snapshot
            self.assertEqual(started.state["base_git"]["head"], baseline)
            self.assertEqual(started.state["product_change_mode"], "NO_SOURCE_DELTA")
            self.assertIsNone(started.state["product_commit"])
            ready = osys.validate(
                checks=[CHECK], inspected_by="runtime-inspector",
                runtime_acceptance_reference=RUNTIME_ACCEPTANCE,
            ).snapshot
            self.assertEqual(ready.state["phase"], "ASSURANCE_READY")
            self.assertIsNone(ready.state["product_commit"])
            self.assertEqual(ready.state["assurance"]["mode"], "NO_SOURCE_DELTA")
            self.assertEqual(ready.state["assurance"]["target_sha"], baseline)
            self.assertEqual(ready.state["assurance"]["runtime_acceptance_reference"], RUNTIME_ACCEPTANCE)
            evidence = json.loads((root / ready.state["evidence"][-1]["path"]).read_text(encoding="utf-8"))
            self.assertEqual(evidence["assurance_scope"], "NO_SOURCE_DELTA_RUNTIME_ASSURANCE")
            self.assertIsNone(evidence["review"])
            closed = osys.close().snapshot
            self.assertEqual(closed.state["phase"], "CLOSED")
            self.assertEqual(closed.state["lease"]["status"], "RELEASED")

    def test_runtime_only_dirty_tree_is_denied(self) -> None:
        with repository("dirty") as root:
            osys = BuildOS(root)
            osys.bootstrap(runtime_request("RUNTIME-DIRTY"))
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            self.assertTrue(osys.status()["no_source_delta_violation"])
            with self.assertRaisesRegex(KernelError, "clean product tree"):
                osys.validate(
                    checks=[CHECK], inspected_by="runtime-inspector",
                    runtime_acceptance_reference=RUNTIME_ACCEPTANCE,
                )
            self.assertEqual(read_current(root).state["phase"], "ACTIVE")

    def test_runtime_only_head_drift_is_denied_even_without_tree_delta(self) -> None:
        with repository("empty-head-drift") as root:
            osys = BuildOS(root)
            osys.bootstrap(runtime_request("RUNTIME-HEAD-DRIFT"))
            git(root, "commit", "--allow-empty", "-qm", "synthetic no-op")
            with self.assertRaisesRegex(KernelError, "unchanged bootstrap Git baseline"):
                osys.validate(
                    checks=[CHECK], inspected_by="runtime-inspector",
                    runtime_acceptance_reference=RUNTIME_ACCEPTANCE,
                )

    def test_runtime_only_product_delta_is_denied_and_cannot_be_recorded(self) -> None:
        with repository("product-delta") as root:
            osys = BuildOS(root)
            started = osys.bootstrap(runtime_request("RUNTIME-PRODUCT-DELTA")).snapshot
            self.assertIsNone(started.state["product_commit"])
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py")
            git(root, "commit", "-qm", "forbidden product delta")
            with self.assertRaisesRegex(KernelError, "NO_SOURCE_DELTA tasks cannot record"):
                osys.record_commit()
            with self.assertRaisesRegex(KernelError, "unchanged bootstrap Git baseline"):
                osys.validate(
                    checks=[CHECK], inspected_by="runtime-inspector",
                    runtime_acceptance_reference=RUNTIME_ACCEPTANCE,
                )
            self.assertIsNone(read_current(root).state["product_commit"])

    def test_runtime_acceptance_reference_is_mandatory(self) -> None:
        with repository("missing-acceptance") as root:
            osys = BuildOS(root)
            osys.bootstrap(runtime_request("RUNTIME-NO-ACCEPTANCE"))
            with self.assertRaisesRegex(KernelError, "runtime acceptance reference"):
                osys.validate(checks=[CHECK], inspected_by="runtime-inspector")
            self.assertEqual(read_current(root).state["phase"], "ACTIVE")

    def test_fake_product_commit_anchor_is_invalid_for_no_source_state(self) -> None:
        with repository("fake-product-anchor") as root:
            state = BuildOS(root).bootstrap(runtime_request("RUNTIME-NO-FAKE-COMMIT")).snapshot.state
            forged = deepcopy(state)
            forged["product_commit"] = {
                "sha": forged["base_git"]["head"],
                "tree": forged["base_git"]["tree"],
                "origin": "NATIVE",
            }
            with self.assertRaisesRegex(KernelError, "cannot contain a product commit anchor"):
                validate_state(forged)

    def test_runtime_r3_remains_independent_assurance_not_fake_delta_review(self) -> None:
        with repository("runtime-r3") as root:
            osys = BuildOS(root)
            osys.bootstrap(runtime_request("RUNTIME-R3", risk="R3"))
            with self.assertRaisesRegex(KernelError, "independent reviewer"):
                osys.validate(
                    checks=[CHECK], inspected_by="runtime-inspector",
                    runtime_acceptance_reference=RUNTIME_ACCEPTANCE,
                )
            ready = osys.validate(
                checks=[CHECK], inspected_by="runtime-inspector",
                reviewer="external-reviewer", review_reference="review/runtime-r3",
                rollback_check="git status --porcelain",
                runtime_acceptance_reference=RUNTIME_ACCEPTANCE,
            ).snapshot
            evidence = json.loads((root / ready.state["evidence"][-1]["path"]).read_text(encoding="utf-8"))
            self.assertEqual(evidence["review"]["scope"], "NO_SOURCE_DELTA_RUNTIME_ASSURANCE")
            self.assertIsNone(ready.state["product_commit"])

    def test_goal38_style_blocked_task_uses_fresh_linked_continuation(self) -> None:
        with repository("goal38-continuation") as root:
            osys = BuildOS(root)
            osys.bootstrap(product_request("STORY-AUTO-GOAL-38"))
            blocked = osys.block_for_source_fix(
                reason="BLOCK_SOURCE_DEFECT_RUNTIME_ONLY_MUTATE_IN_PLACE_CANNOT_REACH_ASSURANCE_READY_WITHOUT_FORBIDDEN_PRODUCT_COMMIT",
                defect_reference="GOAL38@revision=1:BLOCKED_SOURCE_FIX",
            ).snapshot
            blocked_hash = blocked.generation_hash
            continued = osys.continue_task(
                runtime_request("STORY-AUTO-GOAL-38-CONTINUATION-1"),
                source_task_id="STORY-AUTO-GOAL-38", source_revision=1,
                reason="resume runtime-only acceptance after Build OS repair",
                resolution_reference="BUILDOS-RUNTIME-ONLY-NO-SOURCE-DELTA-ASSURANCE-CLOSEOUT@PRODUCT_COMMITTED",
            ).snapshot
            self.assertEqual(continued.state["lineage"]["source_phase"], "BLOCKED_SOURCE_FIX")
            self.assertEqual(continued.state["lineage"]["source_generation_hash"], blocked_hash)
            self.assertEqual(find_task_revision(root, "STORY-AUTO-GOAL-38", 1).state["phase"], "BLOCKED_SOURCE_FIX")
            ready = osys.validate(
                checks=[CHECK], inspected_by="runtime-inspector",
                runtime_acceptance_reference=RUNTIME_ACCEPTANCE,
            ).snapshot
            self.assertEqual(ready.state["phase"], "ASSURANCE_READY")
            self.assertIsNone(ready.state["product_commit"])
            self.assertEqual(osys.close().snapshot.state["phase"], "CLOSED")
            self.assertEqual(task_snapshots(root, "STORY-AUTO-GOAL-38")[-1].state["phase"], "BLOCKED_SOURCE_FIX")

    def test_cli_requires_explicit_no_source_declaration_and_runtime_reference(self) -> None:
        args = parser().parse_args([
            "bootstrap", "--task-id", "RUNTIME-CLI", "--outcome", "runtime accepted",
            "--side-effect", "MUTATE_IN_PLACE", "--no-source-delta",
        ])
        self.assertTrue(args.no_source_delta)
        validate_args = parser().parse_args([
            "validate", "--inspected-by", "runtime-inspector",
            "--runtime-acceptance-reference", RUNTIME_ACCEPTANCE,
        ])
        self.assertEqual(validate_args.runtime_acceptance_reference, RUNTIME_ACCEPTANCE)


if __name__ == "__main__":
    unittest.main()
