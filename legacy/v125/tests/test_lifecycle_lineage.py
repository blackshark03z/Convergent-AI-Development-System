from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import subprocess
import tempfile
import unittest

from buildos.facade import BuildOS
from buildos.cli import parser
from buildos.model import KernelError
from buildos.store import InjectedFailure, find_task_revision, task_snapshots


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, timeout=30)
    if proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


@contextmanager
def repository(name: str):
    with tempfile.TemporaryDirectory(prefix=f"buildos-lineage-{name}-") as raw:
        root = Path(raw)
        git(root, "init", "-q")
        git(root, "config", "user.name", "Build OS Test")
        git(root, "config", "user.email", "buildos@example.invalid")
        (root / "app.py").write_text("value = 1\n", encoding="utf-8")
        git(root, "add", "app.py")
        git(root, "commit", "-qm", "base")
        yield root


def request(task_id: str, *, allowed: list[str] | None = None) -> dict:
    return {
        "task_id": task_id,
        "outcome": f"{task_id} outcome",
        "acceptance": [f"{task_id} acceptance"],
        "acceptance_commands": [],
        "risk": "R1",
        "side_effect": "WRITE",
        "allowed_paths": allowed or ["app.py"],
        "prohibited_paths": ["secrets/**"],
        "worker_id": "WORKER",
        "owner_authorization": "NONE",
        "authorization_reference": None,
        "authorization_actor": "NONE",
        "enforcement": "SUPERVISORY",
        "skill": None,
    }


def complete(root: Path, osys: BuildOS, task_id: str, value: int) -> None:
    osys.bootstrap(request(task_id))
    (root / "app.py").write_text(f"value = {value}\n", encoding="utf-8")
    git(root, "add", "app.py")
    git(root, "commit", "-qm", task_id)
    osys.record_commit()
    osys.validate(checks=["git diff --quiet HEAD"], inspected_by="TEST")
    osys.close()


class ContinuationLineageTests(unittest.TestCase):
    def test_worker_and_admin_command_boundaries_are_explicit(self) -> None:
        worker_choices = next(action.choices for action in parser()._actions if getattr(action, "choices", None))
        admin_choices = next(action.choices for action in parser(admin=True)._actions if getattr(action, "choices", None))
        self.assertIn("block-for-source-fix", worker_choices)
        self.assertIn("continue-task", worker_choices)
        self.assertNotIn("adopt-existing-change", worker_choices)
        self.assertIn("adopt-existing-change", admin_choices)

    def test_continuation_preserves_terminal_source_across_intervening_task(self) -> None:
        with repository("continuation") as root:
            osys = BuildOS(root)
            complete(root, osys, "RUNTIME-1", 2)
            source = find_task_revision(root, "RUNTIME-1", 1)
            complete(root, osys, "REPAIR-1", 3)

            result = osys.continue_task(
                request("RUNTIME-2"),
                source_task_id="RUNTIME-1",
                source_revision=1,
                reason="resume after bounded source repair",
            )

            self.assertEqual(result.snapshot.state["phase"], "ACTIVE")
            self.assertEqual(result.snapshot.state["task_id"], "RUNTIME-2")
            self.assertEqual(result.snapshot.state["lineage"], {
                "kind": "CONTINUATION",
                "source_task_id": "RUNTIME-1",
                "source_revision": 1,
                "source_phase": "CLOSED",
                "source_generation": source.generation,
                "source_generation_hash": source.generation_hash,
                "reason": "resume after bounded source repair",
                "resolution_reference": None,
            })
            self.assertEqual(task_snapshots(root, "RUNTIME-1")[-1].state["phase"], "CLOSED")
            retry = osys.continue_task(
                request("RUNTIME-2"), source_task_id="RUNTIME-1", source_revision=1,
                reason="resume after bounded source repair",
            )
            self.assertTrue(retry.idempotent)

    def test_continuation_rejects_live_source_and_reused_identity(self) -> None:
        with repository("continuation-reject") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("LIVE-1"))
            with self.assertRaisesRegex(KernelError, "released lease"):
                osys.continue_task(request("NEXT-1"), source_task_id="LIVE-1", source_revision=1, reason="invalid")

            osys.abort(reason="bounded stop")
            result = osys.continue_task(request("NEXT-1"), source_task_id="LIVE-1", source_revision=1, reason="valid")
            self.assertEqual(result.snapshot.state["lineage"]["source_phase"], "ABORTED")
            osys.abort(reason="finish continuation")
            with self.assertRaisesRegex(KernelError, "fresh task_id"):
                osys.continue_task(request("LIVE-1"), source_task_id="NEXT-1", source_revision=1, reason="reuse")

    def test_continuation_retry_after_pointer_swap_is_idempotent(self) -> None:
        with repository("continuation-crash") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("OLD-1"))
            osys.abort(reason="source terminal")
            kwargs = dict(source_task_id="OLD-1", source_revision=1, reason="recover", op_id="continue-crash")
            with self.assertRaises(InjectedFailure):
                osys.continue_task(request("NEW-1"), configured_failures="after_pointer_swap", **kwargs)
            retry = osys.continue_task(request("NEW-1"), **kwargs)
            self.assertTrue(retry.idempotent)
            self.assertEqual(retry.snapshot.state["task_id"], "NEW-1")

    def test_public_source_fix_block_releases_lease_and_requires_resolution_proof(self) -> None:
        with repository("source-fix-block") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("RUNTIME-BLOCKED"))
            blocked = osys.block_for_source_fix(
                reason="validator semantic drift",
                defect_reference="evidence/source-defect-1",
            )
            self.assertEqual(blocked.snapshot.state["phase"], "BLOCKED_SOURCE_FIX")
            self.assertEqual(blocked.snapshot.state["lease"]["status"], "RELEASED")
            self.assertEqual(blocked.snapshot.state["source_defect"]["reference"], "evidence/source-defect-1")

            complete(root, osys, "SOURCE-REPAIR", 2)
            with self.assertRaisesRegex(KernelError, "resolution reference"):
                osys.continue_task(
                    request("RUNTIME-CONTINUED"), source_task_id="RUNTIME-BLOCKED",
                    source_revision=1, reason="resume after repair",
                )
            continued = osys.continue_task(
                request("RUNTIME-CONTINUED"), source_task_id="RUNTIME-BLOCKED",
                source_revision=1, reason="resume after repair",
                resolution_reference="SOURCE-REPAIR@r001:CLOSED",
            )
            self.assertEqual(continued.snapshot.state["lineage"]["source_phase"], "BLOCKED_SOURCE_FIX")
            self.assertEqual(continued.snapshot.state["lineage"]["resolution_reference"], "SOURCE-REPAIR@r001:CLOSED")

    def test_source_fix_block_accepts_assurance_ready_but_not_released_state(self) -> None:
        with repository("source-fix-assurance") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("ASSURED-BUT-DEFECTIVE"))
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py")
            git(root, "commit", "-qm", "candidate")
            osys.record_commit()
            osys.validate(checks=["git diff --quiet HEAD"], inspected_by="TEST")
            self.assertEqual(
                osys.block_for_source_fix(reason="late semantic defect", defect_reference="evidence/late").snapshot.state["phase"],
                "BLOCKED_SOURCE_FIX",
            )
            with self.assertRaisesRegex(KernelError, "live task state"):
                osys.block_for_source_fix(reason="again", defect_reference="evidence/again")


class ExistingChangeAdoptionTests(unittest.TestCase):
    def test_adoption_marks_external_origin_then_uses_normal_assurance(self) -> None:
        with repository("adopt") as root:
            base = git(root, "rev-parse", "HEAD")
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py")
            git(root, "commit", "-qm", "pre-existing change")
            target = git(root, "rev-parse", "HEAD")
            osys = BuildOS(root)

            adopted = osys.adopt_existing_change(
                request("ADOPT-1"), base=base, target=target,
                reason="commit predates lifecycle enrollment",
            )

            commit = adopted.snapshot.state["product_commit"]
            self.assertEqual(adopted.snapshot.state["phase"], "PRODUCT_COMMITTED")
            self.assertEqual(commit["origin"], "EXTERNAL_PREEXISTING")
            self.assertEqual(commit["sha"], target)
            self.assertEqual(commit["adoption_reason"], "commit predates lifecycle enrollment")
            self.assertEqual(adopted.snapshot.event["kind"], "ADOPT_EXISTING_CHANGE")
            osys.validate(checks=["git diff --quiet HEAD"], inspected_by="TEST")
            self.assertEqual(osys.close().snapshot.state["phase"], "CLOSED")

    def test_adoption_rejects_non_head_target_and_scope_escape(self) -> None:
        with repository("adopt-reject") as root:
            base = git(root, "rev-parse", "HEAD")
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py")
            git(root, "commit", "-qm", "candidate")
            candidate = git(root, "rev-parse", "HEAD")
            (root / "other.txt").write_text("outside\n", encoding="utf-8")
            git(root, "add", "other.txt")
            git(root, "commit", "-qm", "later")
            head = git(root, "rev-parse", "HEAD")
            osys = BuildOS(root)
            with self.assertRaisesRegex(KernelError, "target must equal"):
                osys.adopt_existing_change(request("OLD-TARGET"), base=base, target=candidate, reason="not head")
            with self.assertRaisesRegex(KernelError, "exceeds allowed paths"):
                osys.adopt_existing_change(request("OUTSIDE"), base=base, target=head, reason="scope escape")

    def test_adoption_retry_after_pointer_swap_is_idempotent(self) -> None:
        with repository("adopt-crash") as root:
            base = git(root, "rev-parse", "HEAD")
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py")
            git(root, "commit", "-qm", "pre-existing")
            target = git(root, "rev-parse", "HEAD")
            osys = BuildOS(root)
            kwargs = dict(base=base, target=target, reason="recover adoption", op_id="adopt-crash")
            with self.assertRaises(InjectedFailure):
                osys.adopt_existing_change(request("ADOPT-CRASH"), configured_failures="after_pointer_swap", **kwargs)
            retry = osys.adopt_existing_change(request("ADOPT-CRASH"), **kwargs)
            self.assertTrue(retry.idempotent)
            self.assertEqual(retry.snapshot.state["product_commit"]["origin"], "EXTERNAL_PREEXISTING")


if __name__ == "__main__":
    unittest.main()
