from __future__ import annotations

from contextlib import contextmanager
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from buildos.facade import BuildOS
from buildos.model import KernelError
from buildos.store import InjectedFailure


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, timeout=30)
    if proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


@contextmanager
def repository(name: str):
    with tempfile.TemporaryDirectory(prefix=f"buildos-execution-{name}-") as raw:
        root = Path(raw)
        git(root, "init", "-q")
        git(root, "config", "user.name", "Execution Test")
        git(root, "config", "user.email", "execution@example.invalid")
        (root / "app.py").write_text("value = 1\n", encoding="utf-8")
        (root / "other.py").write_text("other = 1\n", encoding="utf-8")
        git(root, "add", ".")
        git(root, "commit", "-qm", "base")
        yield root


def request(task_id: str, *, execution_class: str = "LOCAL_HIGH_COST", no_source: bool = False) -> dict:
    return {
        "task_id": task_id,
        "outcome": "safe admitted outcome",
        "acceptance": ["behavior is correct"],
        "acceptance_commands": [],
        "risk": "R1",
        "side_effect": "WRITE",
        "execution_class": execution_class,
        "product_change_mode": "NO_SOURCE_DELTA" if no_source else "PRODUCT_DELTA",
        "allowed_paths": [] if no_source else ["app.py", "other.py"],
        "prohibited_paths": ["secrets/**"],
        "worker_id": "WORKER",
        "owner_authorization": "NONE",
        "authorization_reference": None,
        "authorization_actor": "NONE",
        "enforcement": "SUPERVISORY",
        "skill": None,
    }


def spec(*, external: bool = False, plan_id: str = "plan_one", idempotent: bool = True) -> dict:
    commands = [
        {"id": "focused", "argv": [sys.executable, "-c", "print('focused')"], "provenance": "OWNER_AUTHORED"},
        {"id": "final", "argv": [sys.executable, "-c", "print('final')"], "provenance": "OWNER_AUTHORED"},
    ]
    capabilities = [
        {"id": "local_python", "status": "AVAILABLE", "source": "DETERMINISTIC_PROBE", "evidence": "python-version", "constraints": {"major": 3}},
    ]
    authorities = [
        {"field": "canonical_input", "owner": "product", "owner_kind": "PRODUCT", "mode": "CANONICAL", "evidence": "app.py"},
        {"field": "derived_output", "owner": "compiler", "owner_kind": "DETERMINISTIC_COMPILER", "mode": "DERIVED", "evidence": "compiler-v1"},
    ]
    effects = []
    steps = [{
        "id": "implement", "kind": "LOCAL", "after": [],
        "requires_assumptions": ["input_complete"], "requires_capabilities": ["local_python"],
        "capability_constraints": {"local_python": {"major": 3}},
        "reads": ["canonical_input"], "writes": ["derived_output"], "effect_id": None,
        "failure_families": ["local_defect", "scope_surprise"],
    }]
    recovery = [
        {"family": "local_defect", "disposition": "BOUNDED_FIX", "max_bounded_occurrences": 1, "evidence_required": True},
        {"family": "scope_surprise", "disposition": "BOUNDED_FIX", "max_bounded_occurrences": 1, "evidence_required": True},
    ]
    if external:
        capabilities.append({
            "id": "provider_api", "status": "RESTRICTED", "source": "PROVIDER_CONTRACT",
            "evidence": "provider-discovery", "constraints": {"max_refs": 2, "idempotency": idempotent},
        })
        authorities.append({
            "field": "provider_output", "owner": "adapter", "owner_kind": "PROVIDER",
            "mode": "EXECUTOR", "evidence": "adapter-contract",
        })
        effects.append({
            "id": "submit_job", "idempotency": "IDEMPOTENT_WITH_KEY" if idempotent else "NON_IDEMPOTENT",
            "idempotency_key": "stable-key" if idempotent else None,
            "no_effect_predicate": "canonical_no_effect", "provider_capability": "provider_api",
            "deadline_seconds": 60, "required": True,
        })
        steps.append({
            "id": "dispatch", "kind": "EXTERNAL_EFFECT", "after": ["implement"],
            "requires_assumptions": ["input_complete"], "requires_capabilities": ["provider_api"],
            "capability_constraints": {"provider_api": {"max_refs": 2, "idempotency": idempotent}},
            "reads": ["derived_output"], "writes": ["provider_output"], "effect_id": "submit_job",
            "failure_families": ["provider_uncertain"],
        })
        recovery.append({
            "family": "provider_uncertain", "disposition": "RECONCILE",
            "max_bounded_occurrences": 1, "evidence_required": True,
        })
    return {
        "schema": "buildos.execution-spec.v1", "plan_id": plan_id,
        "cost_class": "EXTERNAL" if external else "HIGH",
        "assumptions": [{
            "id": "input_complete", "statement": "input is complete", "status": "PROVEN",
            "critical": True, "evidence": "input-schema-check", "fallback": None,
        }],
        "capabilities": capabilities, "authorities": authorities, "commands": commands,
        "claims": [
            {
                "id": "focused_behavior", "description": "focused behavior", "command_id": "focused",
                "dependencies": ["app.py"], "mode": "AFFECTED", "role": "ACCEPTANCE",
                "acceptance": ["behavior is correct"],
            },
            {
                "id": "final_assurance", "description": "final integration", "command_id": "final",
                "dependencies": ["*"], "mode": "FINAL", "role": "ACCEPTANCE",
                "acceptance": ["behavior is correct"],
            },
        ],
        "effects": effects, "steps": steps, "recovery": recovery,
    }


class AdmissionTests(unittest.TestCase):
    def test_admit_is_read_only_and_reports_compiled_readiness(self):
        with repository("admit") as root:
            result = BuildOS(root).admit(request("ADMIT-1"), execution_spec=spec())
            self.assertEqual(result["status"], "READY")
            self.assertEqual(result["runtime"]["mode"], "ENHANCED")
            self.assertFalse((root / ".buildos").exists())

    def test_external_or_high_cost_class_requires_spec(self):
        with repository("required") as root:
            osys = BuildOS(root)
            with self.assertRaisesRegex(KernelError, "requires an admitted"):
                osys.bootstrap(request("HIGH-1"))
            legacy = request("LEGACY-1", execution_class="LOCAL_REVERSIBLE")
            self.assertEqual(osys.bootstrap(legacy).snapshot.state["execution"]["mode"], "LEGACY_LOCAL")

    def test_unknown_capability_authority_and_constraint_fail_before_state(self):
        cases = []
        unknown = spec(); unknown["capabilities"][0]["status"] = "UNKNOWN"; unknown["capabilities"][0]["evidence"] = None
        cases.append((unknown, "REQUIRED_CAPABILITY_NOT_READY"))
        llm = spec(); llm["authorities"][0]["owner_kind"] = "LLM"
        cases.append((llm, "LLM_CANNOT_BE_CANONICAL_AUTHORITY"))
        mismatch = spec(); mismatch["steps"][0]["capability_constraints"]["local_python"]["major"] = 4
        cases.append((mismatch, "CAPABILITY_CONSTRAINT_UNSATISFIED"))
        for value, expected in cases:
            with self.subTest(expected=expected), repository("blocked") as root:
                osys = BuildOS(root)
                with self.assertRaisesRegex(KernelError, expected):
                    osys.bootstrap(request("BLOCKED-1"), execution_spec=value)
                self.assertFalse((root / ".buildos" / "control" / "CURRENT").exists())

    def test_acceptance_must_be_operationally_bound(self):
        with repository("acceptance") as root:
            value = spec()
            value["claims"][0]["acceptance"] = ["not the task criterion"]
            with self.assertRaisesRegex(KernelError, "unknown acceptance"):
                BuildOS(root).bootstrap(request("ACCEPT-1"), execution_spec=value)

    def test_external_work_cannot_hide_in_a_local_execution_class(self):
        with repository("underdeclared") as root:
            with self.assertRaisesRegex(KernelError, "EXECUTION_CLASS_UNDERDECLARED"):
                BuildOS(root).bootstrap(
                    request("UNDER-1", execution_class="LOCAL_HIGH_COST"),
                    execution_spec=spec(external=True),
                )


class BlockerAndReplanTests(unittest.TestCase):
    def test_second_same_family_or_second_distinct_family_requires_replan(self):
        with repository("blockers") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("BLOCKER-1"), execution_spec=spec())
            first = osys.report_blocker(family="local_defect", evidence="evidence/one").snapshot
            self.assertEqual(first.event["decision"], "BOUNDED_CORRECTION_ALLOWED")
            second = osys.report_blocker(family="local_defect", evidence="evidence/two").snapshot
            self.assertEqual(second.state["execution"]["plan_validity"], "REPLAN_REQUIRED")
            with self.assertRaisesRegex(KernelError, "plan validity"):
                osys.record_commit()

        with repository("families") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("BLOCKER-2"), execution_spec=spec())
            osys.report_blocker(family="local_defect", evidence="evidence/one")
            result = osys.report_blocker(family="scope_surprise", evidence="evidence/two").snapshot
            self.assertEqual(result.state["execution"]["plan_validity"], "REPLAN_REQUIRED")

    def test_critical_assumption_failure_replans_immediately_and_replacement_is_atomic(self):
        with repository("replan") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("REPLAN-1"), execution_spec=spec())
            blocked = osys.report_blocker(
                family="local_defect", evidence="evidence/assumption-false", assumption_id="input_complete",
            ).snapshot
            self.assertEqual(blocked.state["execution"]["plan_validity"], "REPLAN_REQUIRED")
            replaced = osys.replan(execution_spec=spec(plan_id="plan_two")).snapshot
            self.assertEqual(replaced.state["execution"]["plan_validity"], "VALID")
            self.assertEqual(replaced.state["execution"]["plan_revision"], 2)
            self.assertEqual(len(replaced.state["execution"]["envelope_history"]), 1)


class ExternalEffectTests(unittest.TestCase):
    def test_pre_provider_failure_is_bounded_no_effect_and_effect_identity_is_unique(self):
        with repository("pre-provider") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("EFFECT-0", execution_class="EXTERNAL_EFFECT", no_source=True), execution_spec=spec(external=True))
            osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
            with self.assertRaisesRegex(KernelError, "stable effect identity"):
                osys.effect(transition="PREPARE", effect_id="attempt_two", action_id="submit_job")
            resolved = osys.effect(
                transition="FAIL_BEFORE_DISPATCH", effect_id="attempt_one", reference="preflight/capability-rejected",
            ).snapshot
            record = resolved.state["execution"]["effect_ledger"]["attempt_one"]
            self.assertEqual(record["state"], "RESOLVED_NO_EFFECT")
            self.assertEqual(record["reconciliation"]["outcome"], "PRE_PROVIDER_FAILURE")

    def test_pre_provider_timeout_cannot_promote_to_dispatch(self):
        with repository("pre-provider-timeout") as root:
            value = spec(external=True)
            value["effects"][0]["deadline_seconds"] = 2
            osys = BuildOS(root)
            osys.bootstrap(request("EFFECT-TIME", execution_class="EXTERNAL_EFFECT", no_source=True), execution_spec=value)
            osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
            with self.assertRaisesRegex(KernelError, "deadline has not expired"):
                osys.effect(transition="TIMEOUT_NO_DISPATCH", effect_id="attempt_one", reference="preflight/timeout")
            time.sleep(2.1)
            resolved = osys.effect(
                transition="TIMEOUT_NO_DISPATCH", effect_id="attempt_one", reference="preflight/timeout",
            ).snapshot
            self.assertEqual(resolved.state["execution"]["effect_ledger"]["attempt_one"]["state"], "RESOLVED_NO_EFFECT")

    def test_uncertain_non_idempotent_effect_needs_positive_no_effect_proof(self):
        with repository("non-idempotent") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("EFFECT-1", execution_class="EXTERNAL_EFFECT", no_source=True), execution_spec=spec(external=True, idempotent=False))
            osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
            osys.effect(transition="DISPATCH", effect_id="attempt_one")
            with self.assertRaisesRegex(KernelError, "provider-enforced idempotency"):
                osys.effect(transition="AUTHORIZE_RETRY", effect_id="attempt_one")
            with self.assertRaisesRegex(KernelError, "canonical predicate"):
                osys.effect(
                    transition="RECONCILE_NO_EFFECT", effect_id="attempt_one",
                    reference="provider/no-effect-proof", predicate="wrong_predicate",
                )
            osys.effect(
                transition="RECONCILE_NO_EFFECT", effect_id="attempt_one",
                reference="provider/no-effect-proof", predicate="canonical_no_effect",
            )
            retried = osys.effect(transition="AUTHORIZE_RETRY", effect_id="attempt_one").snapshot
            self.assertEqual(retried.state["execution"]["effect_ledger"]["attempt_one"]["retry_basis"], "POSITIVE_NO_EFFECT_PROOF")

    def test_idempotent_same_key_retry_and_durable_effect_completion(self):
        with repository("idempotent") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("EFFECT-2", execution_class="EXTERNAL_EFFECT", no_source=True), execution_spec=spec(external=True))
            osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
            osys.effect(transition="DISPATCH", effect_id="attempt_one")
            retried = osys.effect(transition="AUTHORIZE_RETRY", effect_id="attempt_one").snapshot
            self.assertEqual(retried.state["execution"]["effect_ledger"]["attempt_one"]["retry_basis"], "SAME_IDEMPOTENCY_KEY")
            osys.effect(transition="DISPATCH", effect_id="attempt_one")
            osys.effect(transition="ACK", effect_id="attempt_one", reference="provider/request-1")
            osys.effect(transition="RESULT", effect_id="attempt_one", reference="artifact/result", sha256="a" * 64)
            with self.assertRaisesRegex(KernelError, "reconciliation before assurance"):
                osys.validate(checks=[], inspected_by="TEST", runtime_acceptance_reference="runtime/evidence")
            committed = osys.effect(transition="COMMIT", effect_id="attempt_one", reference="manifest/result-1").snapshot
            self.assertEqual(committed.state["execution"]["effect_ledger"]["attempt_one"]["state"], "COMMITTED")
            assured = osys.validate(checks=[], inspected_by="TEST", runtime_acceptance_reference="runtime/evidence").snapshot
            self.assertEqual(assured.state["phase"], "ASSURANCE_READY")
            self.assertEqual(osys.close().snapshot.state["phase"], "CLOSED")

    def test_new_product_revision_cannot_reuse_a_prior_required_effect(self):
        with repository("effect-revision") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("EFFECT-REV", execution_class="EXTERNAL_EFFECT", no_source=True), execution_spec=spec(external=True))
            osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
            osys.effect(transition="DISPATCH", effect_id="attempt_one")
            osys.effect(transition="ACK", effect_id="attempt_one", reference="provider/request-1")
            osys.effect(transition="RESULT", effect_id="attempt_one", reference="artifact/result", sha256="a" * 64)
            osys.effect(transition="COMMIT", effect_id="attempt_one", reference="manifest/result-1")
            osys.validate(checks=[], inspected_by="TEST", runtime_acceptance_reference="runtime/evidence")
            osys.close()
            revised = osys.revise(reason="fresh provider execution").snapshot
            self.assertEqual(revised.state["execution"]["effect_ledger"], {})
            with self.assertRaisesRegex(KernelError, "required external effect"):
                osys.validate(checks=[], inspected_by="TEST", runtime_acceptance_reference="runtime/evidence-2")


class ProportionalAssuranceTests(unittest.TestCase):
    def test_unchanged_claim_is_reused_while_final_claim_runs(self):
        with repository("claims") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("CLAIMS-1"), execution_spec=spec())
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py"); git(root, "commit", "-qm", "first")
            osys.record_commit()
            first = osys.validate(checks=[], inspected_by="TEST").snapshot
            self.assertEqual(first.state["execution"]["last_assurance_plan"]["executed"], ["final_assurance", "focused_behavior"])
            osys.close()

            osys.revise(reason="small unrelated correction")
            (root / "other.py").write_text("other = 2\n", encoding="utf-8")
            git(root, "add", "other.py"); git(root, "commit", "-qm", "second")
            osys.record_commit()
            plan = osys.assurance_plan()
            self.assertEqual(plan["reuse"], ["focused_behavior"])
            self.assertEqual(plan["execute"], ["final_assurance"])
            second = osys.validate(checks=[], inspected_by="TEST").snapshot
            self.assertTrue(second.state["execution"]["claim_results"]["focused_behavior"]["reused"])
            self.assertFalse(second.state["execution"]["claim_results"]["final_assurance"]["reused"])

    def test_missing_prior_evidence_forces_execution_instead_of_unsafe_reuse(self):
        with repository("claim-proof") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("CLAIMS-PROOF"), execution_spec=spec())
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py"); git(root, "commit", "-qm", "first")
            osys.record_commit(); first = osys.validate(checks=[], inspected_by="TEST").snapshot; osys.close()
            evidence = root / first.state["execution"]["claim_results"]["focused_behavior"]["evidence"]["path"]
            evidence.unlink()
            osys.revise(reason="unrelated correction")
            (root / "other.py").write_text("other = 2\n", encoding="utf-8")
            git(root, "add", "other.py"); git(root, "commit", "-qm", "second")
            osys.record_commit()
            self.assertIn("focused_behavior", osys.assurance_plan()["execute"])

    def test_review_supersession_binds_same_asset_and_content(self):
        with repository("review") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("REVIEW-1"), execution_spec=spec())
            osys.review(
                review_id="review_one", asset_id="asset_one", content_sha256="b" * 64,
                outcome="REJECT", evidence="qc/reject",
            )
            passed = osys.review(
                review_id="review_two", asset_id="asset_one", content_sha256="b" * 64,
                outcome="PASS", evidence="qc/correction", supersedes="review_one",
            ).snapshot
            self.assertEqual(passed.state["execution"]["reviews"][-1]["epoch"], 2)
            with self.assertRaisesRegex(KernelError, "same asset identity"):
                osys.review(
                    review_id="review_three", asset_id="asset_one", content_sha256="c" * 64,
                    outcome="PASS", evidence="qc/wrong", supersedes="review_two",
                )

    def test_salvage_creates_new_content_bound_asset_lineage(self):
        with repository("salvage") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("SALVAGE-1"), execution_spec=spec())
            osys.review(
                review_id="review_source", asset_id="asset_source", content_sha256="a" * 64,
                outcome="SALVAGEABLE", evidence="qc/duration-window",
            )
            repaired = osys.review(
                review_id="review_repaired", asset_id="asset_repaired", content_sha256="b" * 64,
                outcome="PASS", evidence="qc/review-repaired", derived_from_review="review_source",
                transformation_reference="salvage/ffmpeg-trim-proof",
            ).snapshot.state["execution"]["reviews"][-1]
            self.assertEqual(repaired["derived_from_review"], "review_source")
            with self.assertRaisesRegex(KernelError, "new asset bytes/identity"):
                osys.review(
                    review_id="review_bad", asset_id="asset_source", content_sha256="a" * 64,
                    outcome="PASS", evidence="qc/bad", derived_from_review="review_source",
                    transformation_reference="salvage/not-new",
                )


class TransactionBoundaryTests(unittest.TestCase):
    def test_new_runtime_mutations_retry_idempotently_after_pointer_swap(self):
        with repository("crash-blocker") as root:
            osys = BuildOS(root); osys.bootstrap(request("CRASH-BLOCK"), execution_spec=spec())
            kwargs = {"family": "local_defect", "evidence": "evidence/one", "op_id": "crash-blocker"}
            with self.assertRaises(InjectedFailure):
                osys.report_blocker(configured_failures="after_pointer_swap", **kwargs)
            self.assertTrue(osys.report_blocker(**kwargs).idempotent)

        with repository("crash-replan") as root:
            osys = BuildOS(root); osys.bootstrap(request("CRASH-REPLAN"), execution_spec=spec())
            osys.report_blocker(family="local_defect", evidence="evidence/critical", assumption_id="input_complete")
            kwargs = {"execution_spec": spec(plan_id="plan_two"), "op_id": "crash-replan"}
            with self.assertRaises(InjectedFailure):
                osys.replan(configured_failures="after_pointer_swap", **kwargs)
            self.assertTrue(osys.replan(**kwargs).idempotent)

        with repository("crash-review") as root:
            osys = BuildOS(root); osys.bootstrap(request("CRASH-REVIEW"), execution_spec=spec())
            kwargs = {
                "review_id": "review_one", "asset_id": "asset_one", "content_sha256": "b" * 64,
                "outcome": "PASS", "evidence": "qc/pass", "op_id": "crash-review",
            }
            with self.assertRaises(InjectedFailure):
                osys.review(configured_failures="after_pointer_swap", **kwargs)
            self.assertTrue(osys.review(**kwargs).idempotent)

        with repository("crash-effect") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("CRASH-EFFECT", execution_class="EXTERNAL_EFFECT", no_source=True), execution_spec=spec(external=True))
            prepare = {"transition": "PREPARE", "effect_id": "attempt_one", "action_id": "submit_job", "op_id": "crash-effect-prepare"}
            with self.assertRaises(InjectedFailure):
                osys.effect(configured_failures="after_pointer_swap", **prepare)
            self.assertTrue(osys.effect(**prepare).idempotent)
            dispatch = {"transition": "DISPATCH", "effect_id": "attempt_one", "op_id": "crash-effect-dispatch"}
            with self.assertRaises(InjectedFailure):
                osys.effect(configured_failures="after_pointer_swap", **dispatch)
            self.assertTrue(osys.effect(**dispatch).idempotent)


if __name__ == "__main__":
    unittest.main(verbosity=2)
