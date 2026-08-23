from __future__ import annotations

from contextlib import contextmanager
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from buildos.facade import BuildOS
from buildos.model import KernelError, sha256_json
from buildos.store import InjectedFailure


COMMAND_REGISTRY_PATH = ".buildos-command-registry.json"
COMMAND_ROWS = [
    {"id": "focused", "argv": [sys.executable, "-c", "print('focused')"]},
    {"id": "final", "argv": [sys.executable, "-c", "print('final')"]},
]
COMMAND_REGISTRY_BYTES = (
    json.dumps(
        {"schema": "buildos.command-registry.v1", "commands": COMMAND_ROWS},
        ensure_ascii=False, sort_keys=True, indent=2,
    ) + "\n"
).encode("utf-8")
COMMAND_REGISTRY_SHA256 = hashlib.sha256(COMMAND_REGISTRY_BYTES).hexdigest()
COMMAND_APPROVAL_REGISTRY_PATH = ".buildos-command-approvals.json"
FOCUSED_COMMAND_SHA256 = sha256_json(COMMAND_ROWS[0])
COMMAND_APPROVAL_REGISTRY_BYTES = (
    json.dumps({
        "schema": "buildos.command-approval-registry.v1",
        "approvals": [{
            "reference": "owner/approval-7", "command_sha256": FOCUSED_COMMAND_SHA256,
        }],
    }, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
).encode("utf-8")
COMMAND_APPROVAL_REGISTRY_SHA256 = hashlib.sha256(COMMAND_APPROVAL_REGISTRY_BYTES).hexdigest()
CANONICAL_INPUT_PATH = "provider-input.json"
CANONICAL_INPUT_BYTES = (
    json.dumps({"prompt": "baseline"}, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
).encode("utf-8")
CANONICAL_INPUT_SHA256 = hashlib.sha256(CANONICAL_INPUT_BYTES).hexdigest()
EFFECT_INPUT_PATH = "effect-input.json"
EFFECT_INPUT_BYTES = (
    json.dumps({
        "schema": "buildos.effect-input.v1",
        "action_id": "submit_job",
        "provider_capability": "provider_api",
        "payload": {"prompt": "baseline"},
        "canonical_inputs": [{"path": CANONICAL_INPUT_PATH, "sha256": CANONICAL_INPUT_SHA256}],
    }, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
).encode("utf-8")
EFFECT_INPUT_SHA256 = hashlib.sha256(EFFECT_INPUT_BYTES).hexdigest()
ALT_EFFECT_INPUT_PATH = "effect-input-alt.json"
ALT_EFFECT_INPUT_BYTES = (
    json.dumps({
        "schema": "buildos.effect-input.v1",
        "action_id": "submit_job",
        "provider_capability": "provider_api",
        "payload": {"prompt": "materially changed"},
        "canonical_inputs": [{"path": CANONICAL_INPUT_PATH, "sha256": CANONICAL_INPUT_SHA256}],
    }, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
).encode("utf-8")
ALT_EFFECT_INPUT_SHA256 = hashlib.sha256(ALT_EFFECT_INPUT_BYTES).hexdigest()
ADAPTER_IMPLEMENTATION_PATH = "provider_adapter.py"
ADAPTER_IMPLEMENTATION_BYTES = b"def submit(payload):\n    return payload\n"
ADAPTER_IMPLEMENTATION_SHA256 = hashlib.sha256(ADAPTER_IMPLEMENTATION_BYTES).hexdigest()
ADAPTER_RULES_PATH = "provider-adapter-rules.json"
ADAPTER_RULES_BYTES = b'{"endpoint":"fixture-v1","mode":"submit"}\n'
ADAPTER_RULES_SHA256 = hashlib.sha256(ADAPTER_RULES_BYTES).hexdigest()
ADAPTER_CONTRACT_PATH = "effect-adapter-contract.json"
ADAPTER_CONTRACT_BYTES = (
    json.dumps({
        "schema": "buildos.effect-adapter-contract.v1",
        "adapter_id": "provider_adapter",
        "provider_capability": "provider_api",
        "implementation": [{
            "path": ADAPTER_IMPLEMENTATION_PATH,
            "sha256": ADAPTER_IMPLEMENTATION_SHA256,
        }, {
            "path": ADAPTER_RULES_PATH,
            "sha256": ADAPTER_RULES_SHA256,
        }],
    }, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
).encode("utf-8")
ADAPTER_CONTRACT_SHA256 = hashlib.sha256(ADAPTER_CONTRACT_BYTES).hexdigest()


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, timeout=30)
    if proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


def install_command_registry(root: Path, rows: list[dict]) -> str:
    data = (
        json.dumps(
            {"schema": "buildos.command-registry.v1", "commands": rows},
            ensure_ascii=False, sort_keys=True, indent=2,
        ) + "\n"
    ).encode("utf-8")
    (root / COMMAND_REGISTRY_PATH).write_bytes(data)
    git(root, "add", COMMAND_REGISTRY_PATH)
    git(root, "commit", "-qm", "install adversarial trusted commands")
    return hashlib.sha256(data).hexdigest()


def trusted_command(row: dict, registry_sha256: str) -> dict:
    return {
        "id": row["id"], "argv": list(row["argv"]),
        "provenance": "PROJECT_POLICY_TRUSTED",
        "source": {
            "kind": "PROJECT_BASELINE", "path": COMMAND_REGISTRY_PATH,
            "sha256": registry_sha256,
        },
    }


def spec_with_commands(root: Path, rows: list[dict], claims: list[dict]) -> dict:
    registry_sha = install_command_registry(root, rows)
    value = spec()
    value["commands"] = [trusted_command(row, registry_sha) for row in rows]
    value["claims"] = claims
    return value


@contextmanager
def repository(name: str):
    with tempfile.TemporaryDirectory(prefix=f"buildos-execution-{name}-") as raw:
        root = Path(raw)
        git(root, "init", "-q")
        git(root, "config", "user.name", "Execution Test")
        git(root, "config", "user.email", "execution@example.invalid")
        (root / "app.py").write_text("value = 1\n", encoding="utf-8")
        (root / "other.py").write_text("other = 1\n", encoding="utf-8")
        (root / COMMAND_REGISTRY_PATH).write_bytes(COMMAND_REGISTRY_BYTES)
        (root / COMMAND_APPROVAL_REGISTRY_PATH).write_bytes(COMMAND_APPROVAL_REGISTRY_BYTES)
        (root / CANONICAL_INPUT_PATH).write_bytes(CANONICAL_INPUT_BYTES)
        (root / EFFECT_INPUT_PATH).write_bytes(EFFECT_INPUT_BYTES)
        (root / ALT_EFFECT_INPUT_PATH).write_bytes(ALT_EFFECT_INPUT_BYTES)
        (root / ADAPTER_IMPLEMENTATION_PATH).write_bytes(ADAPTER_IMPLEMENTATION_BYTES)
        (root / ADAPTER_RULES_PATH).write_bytes(ADAPTER_RULES_BYTES)
        (root / ADAPTER_CONTRACT_PATH).write_bytes(ADAPTER_CONTRACT_BYTES)
        git(root, "add", ".")
        git(root, "commit", "-qm", "base")
        yield root


def request(
    task_id: str, *, execution_class: str = "LOCAL_HIGH_COST", no_source: bool = False,
    authorization: str = "NONE", authorization_reference: str | None = None,
) -> dict:
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
        "owner_authorization": authorization,
        "authorization_reference": authorization_reference,
        "authorization_actor": "OWNER" if authorization == "APPROVED" else "NONE",
        "enforcement": "SUPERVISORY",
        "skill": None,
    }


def spec(*, external: bool = False, plan_id: str = "plan_one", idempotent: bool = True) -> dict:
    commands = [
        {
            "id": COMMAND_ROWS[0]["id"], "argv": list(COMMAND_ROWS[0]["argv"]),
            "provenance": "PROJECT_POLICY_TRUSTED",
            "source": {"kind": "PROJECT_BASELINE", "path": COMMAND_REGISTRY_PATH, "sha256": COMMAND_REGISTRY_SHA256},
        },
        {
            "id": COMMAND_ROWS[1]["id"], "argv": list(COMMAND_ROWS[1]["argv"]),
            "provenance": "PROJECT_POLICY_TRUSTED",
            "source": {"kind": "PROJECT_BASELINE", "path": COMMAND_REGISTRY_PATH, "sha256": COMMAND_REGISTRY_SHA256},
        },
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
            "effect_input": {
                "kind": "PROJECT_ARTIFACT", "path": EFFECT_INPUT_PATH,
                "sha256": EFFECT_INPUT_SHA256,
            },
            "adapter_contract": {
                "kind": "PROJECT_BASELINE", "path": ADAPTER_CONTRACT_PATH,
                "sha256": ADAPTER_CONTRACT_SHA256,
            },
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

    def test_trusted_command_provenance_cannot_be_self_labelled(self):
        with repository("self-labelled-owner") as root:
            value = spec()
            value["commands"][0]["source"] = {
                "kind": "OWNER_APPROVAL", "reference": "owner/chat",
                "command_sha256": sha256_json({"id": "focused", "argv": value["commands"][0]["argv"]}),
            }
            with self.assertRaisesRegex(KernelError, "registry path/hash binding"):
                BuildOS(root).admit(request("PROVENANCE-OWNER"), execution_spec=value)

        with repository("registry-mismatch") as root:
            value = spec()
            value["commands"][0]["argv"][-1] = "print('agent changed argv')"
            with self.assertRaisesRegex(KernelError, "trusted registry entry"):
                BuildOS(root).admit(request("PROVENANCE-ARGV"), execution_spec=value)

        with repository("self-labelled-package") as root:
            value = spec()
            value["commands"][0].update({
                "provenance": "PACKAGE_OWNED",
                "source": {
                    "kind": "PACKAGE_MANIFEST", "path": "templates/execution/COMMAND_REGISTRY.json.tmpl",
                    "sha256": "0" * 64,
                },
            })
            with self.assertRaisesRegex(KernelError, "not bound by the package manifest"):
                BuildOS(root).admit(request("PROVENANCE-PACKAGE"), execution_spec=value)

    def test_legacy_owner_authored_is_only_a_compatibility_alias(self):
        with repository("legacy-owner-vocabulary") as root:
            value = spec()
            value["commands"][0]["provenance"] = "OWNER_AUTHORED"
            admitted = BuildOS(root).admit(request("PROVENANCE-LEGACY"), execution_spec=value)
            compiled = admitted["runtime"]["envelope"]["commands"]["focused"]
            self.assertEqual(compiled["provenance"], "PROJECT_POLICY_TRUSTED")
            self.assertEqual(compiled["compatibility_provenance"], "OWNER_AUTHORED")

    def test_model_proposed_command_requires_exact_owner_approval_binding(self):
        with repository("model-approval") as root:
            value = spec()
            command = value["commands"][0]
            digest = sha256_json({"id": command["id"], "argv": command["argv"]})
            command.update({
                "provenance": "MODEL_PROPOSED_APPROVED",
                "source": {
                    "kind": "OWNER_APPROVAL", "path": COMMAND_APPROVAL_REGISTRY_PATH,
                    "sha256": COMMAND_APPROVAL_REGISTRY_SHA256,
                    "reference": "owner/approval-7", "command_sha256": digest,
                },
            })
            with self.assertRaisesRegex(KernelError, "not bound to explicit owner approval"):
                BuildOS(root).admit(request("MODEL-DENIED"), execution_spec=value)
            admitted = BuildOS(root).admit(
                request(
                    "MODEL-APPROVED", authorization="APPROVED",
                    authorization_reference="owner/approval-7",
                ),
                execution_spec=value,
            )
            self.assertEqual(admitted["status"], "READY")

            changed = copy.deepcopy(value)
            changed["commands"][0]["argv"][-1] = "print('changed after approval')"
            with self.assertRaisesRegex(KernelError, "exact argv hash"):
                BuildOS(root).admit(
                    request(
                        "MODEL-CHANGED", authorization="APPROVED",
                        authorization_reference="owner/approval-7",
                    ),
                    execution_spec=changed,
                )

            forged = copy.deepcopy(value)
            forged["commands"][0]["source"]["reference"] = "owner/self-labelled"
            with self.assertRaisesRegex(KernelError, "baseline owner approval"):
                BuildOS(root).admit(
                    request(
                        "MODEL-FORGED", authorization="APPROVED",
                        authorization_reference="owner/self-labelled",
                    ),
                    execution_spec=forged,
                )

    def test_package_owned_command_requires_manifest_bound_registry(self):
        with repository("package-registry") as root, tempfile.TemporaryDirectory() as raw_package:
            package_root = Path(raw_package)
            registry_path = "trusted-commands.json"
            (package_root / registry_path).write_bytes(COMMAND_REGISTRY_BYTES)
            (package_root / "PACKAGE_MANIFEST.json").write_text(json.dumps({
                "trusted_command_registries": {registry_path: COMMAND_REGISTRY_SHA256},
            }), encoding="utf-8")
            value = spec()
            value["commands"][0].update({
                "provenance": "PACKAGE_OWNED",
                "source": {
                    "kind": "PACKAGE_MANIFEST", "path": registry_path,
                    "sha256": COMMAND_REGISTRY_SHA256,
                },
            })
            admitted = BuildOS(root, package_root=package_root).admit(
                request("PACKAGE-TRUSTED"), execution_spec=value,
            )
            self.assertEqual(admitted["status"], "READY")


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

    def test_replan_preserves_dirty_allowed_work_without_adopting_it(self):
        with repository("replan-dirty-wip") as root:
            osys = BuildOS(root)
            bootstrapped = osys.bootstrap(request("REPLAN-DIRTY"), execution_spec=spec()).snapshot
            base = bootstrapped.state["base_git"]["head"]
            osys.report_blocker(
                family="local_defect", evidence="evidence/critical",
                assumption_id="input_complete",
            )
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            replaced = osys.replan(execution_spec=spec(plan_id="plan_two")).snapshot
            binding = replaced.state["execution"]["product_state_binding"]
            self.assertEqual((root / "app.py").read_text(encoding="utf-8"), "value = 2\n")
            self.assertEqual(replaced.state["base_git"]["head"], base)
            self.assertIsNone(replaced.state["product_commit"])
            self.assertEqual(binding["status"], "IN_PROGRESS_UNADOPTED")
            self.assertEqual(binding["trust_baseline_head"], base)
            self.assertEqual(binding["dirty_paths"], ["app.py"])

    def test_replan_preserves_partially_committed_work_without_using_it_as_trust(self):
        with repository("replan-committed-wip") as root:
            osys = BuildOS(root)
            bootstrapped = osys.bootstrap(request("REPLAN-COMMITTED"), execution_spec=spec()).snapshot
            base = bootstrapped.state["base_git"]["head"]
            osys.report_blocker(
                family="local_defect", evidence="evidence/critical",
                assumption_id="input_complete",
            )
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py")
            git(root, "commit", "-qm", "unadopted product change")
            wip_head = git(root, "rev-parse", "HEAD")
            replaced = osys.replan(execution_spec=spec(plan_id="plan_two")).snapshot
            binding = replaced.state["execution"]["product_state_binding"]
            self.assertEqual(git(root, "rev-parse", "HEAD"), wip_head)
            self.assertEqual(replaced.state["base_git"]["head"], base)
            self.assertIsNone(replaced.state["product_commit"])
            self.assertEqual(binding["observed_head"], wip_head)
            self.assertEqual(binding["committed_paths"], ["app.py"])
            self.assertEqual(replaced.state["execution"]["trust_baseline"]["head"], base)

    def test_replan_rejects_dirty_or_committed_trust_registry_mutation(self):
        for committed in (False, True):
            with self.subTest(committed=committed), repository("replan-registry") as root:
                req = request("REPLAN-REGISTRY")
                req["allowed_paths"].append(COMMAND_REGISTRY_PATH)
                osys = BuildOS(root)
                osys.bootstrap(req, execution_spec=spec())
                osys.report_blocker(
                    family="local_defect", evidence="evidence/critical",
                    assumption_id="input_complete",
                )
                changed = json.loads(COMMAND_REGISTRY_BYTES)
                changed["commands"][0]["argv"][-1] = "print('mutated registry')"
                (root / COMMAND_REGISTRY_PATH).write_text(
                    json.dumps(changed, sort_keys=True, indent=2) + "\n", encoding="utf-8",
                )
                if committed:
                    git(root, "add", COMMAND_REGISTRY_PATH)
                    git(root, "commit", "-qm", "untrusted registry mutation")
                with self.assertRaisesRegex(KernelError, "differs from the current Git baseline"):
                    osys.replan(execution_spec=spec(plan_id="plan_two"))

    def test_replan_rejects_prohibited_deleted_and_type_changed_wip(self):
        with repository("replan-prohibited") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("REPLAN-PROHIBITED"), execution_spec=spec())
            osys.report_blocker(
                family="local_defect", evidence="evidence/critical", assumption_id="input_complete",
            )
            (root / "secrets").mkdir()
            (root / "secrets" / "key.txt").write_text("not-a-secret-fixture\n", encoding="utf-8")
            with self.assertRaisesRegex(KernelError, "prohibited paths"):
                osys.replan(execution_spec=spec(plan_id="plan_two"))

        with repository("replan-deleted") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("REPLAN-DELETED"), execution_spec=spec())
            osys.report_blocker(
                family="local_defect", evidence="evidence/critical", assumption_id="input_complete",
            )
            (root / "app.py").unlink()
            with self.assertRaisesRegex(KernelError, "deletion requires"):
                osys.replan(execution_spec=spec(plan_id="plan_two"))

        with repository("replan-type-change") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("REPLAN-TYPE"), execution_spec=spec())
            osys.report_blocker(
                family="local_defect", evidence="evidence/critical", assumption_id="input_complete",
            )
            target = root / "link-target.txt"
            target.write_text("other.py\n", encoding="utf-8")
            blob = git(root, "hash-object", "-w", "link-target.txt")
            target.unlink()
            git(root, "update-index", "--cacheinfo", f"120000,{blob},app.py")
            git(root, "commit", "-qm", "unadopted type change")
            with self.assertRaisesRegex(KernelError, "file type changes require"):
                osys.replan(execution_spec=spec(plan_id="plan_two"))


class ExternalEffectTests(unittest.TestCase):
    @staticmethod
    def _commit_provider_effect(osys: BuildOS):
        osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
        osys.effect(transition="DISPATCH", effect_id="attempt_one")
        osys.effect(transition="ACK", effect_id="attempt_one", reference="provider/request-1")
        osys.effect(transition="RESULT", effect_id="attempt_one", reference="artifact/result", sha256="a" * 64)
        return osys.effect(transition="COMMIT", effect_id="attempt_one", reference="manifest/result-1").snapshot

    def test_effect_request_canonical_input_and_adapter_are_real_source_bindings(self):
        with repository("effect-input-stale") as root:
            changed = json.loads(EFFECT_INPUT_BYTES)
            changed["payload"]["prompt"] = "changed without rebinding"
            (root / EFFECT_INPUT_PATH).write_text(
                json.dumps(changed, sort_keys=True, indent=2) + "\n", encoding="utf-8",
            )
            with self.assertRaisesRegex(KernelError, "content-addressed SHA-256"):
                BuildOS(root).admit(
                    request("EFFECT-INPUT-STALE", execution_class="EXTERNAL_EFFECT", no_source=True),
                    execution_spec=spec(external=True),
                )

        with repository("canonical-input-stale") as root:
            (root / CANONICAL_INPUT_PATH).write_text('{"prompt":"changed"}\n', encoding="utf-8")
            with self.assertRaisesRegex(KernelError, "canonical input.*content-addressed SHA-256"):
                BuildOS(root).admit(
                    request("CANONICAL-INPUT-STALE", execution_class="EXTERNAL_EFFECT", no_source=True),
                    execution_spec=spec(external=True),
                )

        with repository("adapter-behavior-dependency-stale") as root:
            (root / ADAPTER_RULES_PATH).write_text(
                '{"endpoint":"fixture-v2","mode":"submit"}\n', encoding="utf-8",
            )
            with self.assertRaisesRegex(KernelError, "differs from the current Git baseline"):
                BuildOS(root).admit(
                    request("ADAPTER-STALE", execution_class="EXTERNAL_EFFECT", no_source=True),
                    execution_spec=spec(external=True),
                )

    def test_effect_sources_are_reverified_at_prepare_and_dispatch(self):
        with repository("effect-source-recheck") as root:
            req = request("EFFECT-RECHECK", execution_class="EXTERNAL_EFFECT")
            req["allowed_paths"].extend([
                EFFECT_INPUT_PATH, CANONICAL_INPUT_PATH, ADAPTER_RULES_PATH,
            ])
            osys = BuildOS(root)
            osys.bootstrap(req, execution_spec=spec(external=True))

            changed_request = json.loads(EFFECT_INPUT_BYTES)
            changed_request["payload"]["prompt"] = "changed after admission"
            (root / EFFECT_INPUT_PATH).write_text(
                json.dumps(changed_request, sort_keys=True, indent=2) + "\n", encoding="utf-8",
            )
            with self.assertRaisesRegex(KernelError, "content-addressed SHA-256"):
                osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
            (root / EFFECT_INPUT_PATH).write_bytes(EFFECT_INPUT_BYTES)
            osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")

            (root / CANONICAL_INPUT_PATH).write_text('{"prompt":"changed"}\n', encoding="utf-8")
            with self.assertRaisesRegex(KernelError, "canonical input.*content-addressed SHA-256"):
                osys.effect(transition="DISPATCH", effect_id="attempt_one")
            (root / CANONICAL_INPUT_PATH).write_bytes(CANONICAL_INPUT_BYTES)

            (root / ADAPTER_RULES_PATH).write_text(
                '{"endpoint":"fixture-v2","mode":"submit"}\n', encoding="utf-8",
            )
            with self.assertRaisesRegex(KernelError, "differs from the current Git baseline"):
                osys.effect(transition="DISPATCH", effect_id="attempt_one")
            (root / ADAPTER_RULES_PATH).write_bytes(ADAPTER_RULES_BYTES)
            dispatched = osys.effect(transition="DISPATCH", effect_id="attempt_one").snapshot
            self.assertEqual(
                dispatched.state["execution"]["effect_ledger"]["attempt_one"]["state"],
                "DISPATCH_UNCONFIRMED",
            )

    def test_package_adapter_requires_manifest_and_implementation_hashes(self):
        with repository("package-adapter") as root, tempfile.TemporaryDirectory() as raw_package:
            package_root = Path(raw_package)
            (package_root / ADAPTER_IMPLEMENTATION_PATH).write_bytes(ADAPTER_IMPLEMENTATION_BYTES)
            (package_root / ADAPTER_RULES_PATH).write_bytes(ADAPTER_RULES_BYTES)
            (package_root / ADAPTER_CONTRACT_PATH).write_bytes(ADAPTER_CONTRACT_BYTES)
            (package_root / "PACKAGE_MANIFEST.json").write_text(json.dumps({
                "trusted_effect_adapter_contracts": {
                    ADAPTER_CONTRACT_PATH: ADAPTER_CONTRACT_SHA256,
                },
            }), encoding="utf-8")
            value = spec(external=True)
            value["effects"][0]["adapter_contract"]["kind"] = "PACKAGE_MANIFEST"
            admitted = BuildOS(root, package_root=package_root).admit(
                request("PACKAGE-ADAPTER", execution_class="EXTERNAL_EFFECT", no_source=True),
                execution_spec=value,
            )
            self.assertEqual(admitted["status"], "READY")

            (package_root / ADAPTER_RULES_PATH).write_text(
                '{"endpoint":"fixture-v2","mode":"submit"}\n', encoding="utf-8",
            )
            with self.assertRaisesRegex(KernelError, "content-addressed SHA-256"):
                BuildOS(root, package_root=package_root).admit(
                    request("PACKAGE-ADAPTER-STALE", execution_class="EXTERNAL_EFFECT", no_source=True),
                    execution_spec=value,
                )

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

    def test_product_committed_flow_can_still_prepare_and_dispatch(self):
        with repository("effect-product-committed") as root:
            osys = BuildOS(root)
            osys.bootstrap(
                request("EFFECT-COMMITTED", execution_class="EXTERNAL_EFFECT"),
                execution_spec=spec(external=True),
            )
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py")
            git(root, "commit", "-qm", "product implementation")
            osys.record_commit()
            osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
            dispatched = osys.effect(transition="DISPATCH", effect_id="attempt_one").snapshot
            self.assertEqual(dispatched.state["phase"], "PRODUCT_COMMITTED")
            self.assertEqual(
                dispatched.state["execution"]["effect_ledger"]["attempt_one"]["state"],
                "DISPATCH_UNCONFIRMED",
            )

    def test_pre_provider_timeout_cannot_promote_to_dispatch(self):
        with repository("pre-provider-timeout") as root:
            value = spec(external=True)
            value["effects"][0]["deadline_seconds"] = 2
            osys = BuildOS(root)
            osys.bootstrap(request("EFFECT-TIME", execution_class="EXTERNAL_EFFECT", no_source=True), execution_spec=value)
            class FixedDateTime(datetime):
                current = datetime(2030, 1, 1, tzinfo=timezone.utc)

                @classmethod
                def now(cls, tz=None):
                    return cls.current

            with patch("buildos.execution.datetime", FixedDateTime):
                osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
                with self.assertRaisesRegex(KernelError, "deadline has not expired"):
                    osys.effect(
                        transition="TIMEOUT_NO_DISPATCH", effect_id="attempt_one",
                        reference="preflight/timeout",
                    )
                FixedDateTime.current += timedelta(seconds=3)
                resolved = osys.effect(
                    transition="TIMEOUT_NO_DISPATCH", effect_id="attempt_one",
                    reference="preflight/timeout",
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

    def test_replan_carries_only_an_identical_committed_effect_contract(self):
        with repository("effect-replan-identical") as root:
            osys = BuildOS(root)
            osys.bootstrap(
                request("EFFECT-SAME", execution_class="EXTERNAL_EFFECT", no_source=True),
                execution_spec=spec(external=True),
            )
            self._commit_provider_effect(osys)
            osys.report_blocker(
                family="local_defect", evidence="evidence/plan-a-invalid",
                assumption_id="input_complete",
            )
            replaced = osys.replan(execution_spec=spec(external=True, plan_id="plan_two")).snapshot
            runtime = replaced.state["execution"]
            self.assertEqual(replaced.event["effects_carried"], ["attempt_one"])
            self.assertEqual(replaced.event["effects_retired"], [])
            self.assertEqual(runtime["effect_ledger"]["attempt_one"]["state"], "COMMITTED")
            self.assertEqual(
                runtime["effect_ledger"]["attempt_one"]["effect_contract_hash"],
                runtime["envelope"]["effects"]["submit_job"]["effect_contract_hash"],
            )
            self.assertEqual(
                runtime["effect_ledger"]["attempt_one"]["effect_input"],
                runtime["envelope"]["effects"]["submit_job"]["effect_input"],
            )
            self.assertEqual(
                runtime["effect_ledger"]["attempt_one"]["adapter_contract"],
                runtime["envelope"]["effects"]["submit_job"]["adapter_contract"],
            )
            with self.assertRaisesRegex(KernelError, "stable effect identity"):
                osys.effect(transition="PREPARE", effect_id="attempt_two", action_id="submit_job")
            assured = osys.validate(
                checks=[], inspected_by="TEST", runtime_acceptance_reference="runtime/identical-replan",
            ).snapshot
            self.assertEqual(assured.state["phase"], "ASSURANCE_READY")

    def test_replan_retires_same_action_id_when_semantics_change(self):
        with repository("effect-replan-changed") as root:
            osys = BuildOS(root)
            osys.bootstrap(
                request("EFFECT-CHANGED", execution_class="EXTERNAL_EFFECT", no_source=True),
                execution_spec=spec(external=True),
            )
            committed = self._commit_provider_effect(osys)
            prior_hash = committed.state["execution"]["effect_ledger"]["attempt_one"]["effect_contract_hash"]
            osys.report_blocker(
                family="local_defect", evidence="evidence/plan-a-invalid",
                assumption_id="input_complete",
            )
            changed = spec(external=True, plan_id="plan_two")
            changed["capabilities"][1]["constraints"]["max_refs"] = 3
            changed["steps"][1]["capability_constraints"]["provider_api"]["max_refs"] = 3
            replaced = osys.replan(execution_spec=changed).snapshot
            runtime = replaced.state["execution"]
            self.assertEqual(replaced.event["effects_carried"], [])
            self.assertEqual(replaced.event["effects_retired"], ["attempt_one"])
            self.assertEqual(runtime["effect_ledger"], {})
            self.assertEqual(runtime["effect_history"][-1]["effect_contract_hash"], prior_hash)
            self.assertNotEqual(
                prior_hash, runtime["envelope"]["effects"]["submit_job"]["effect_contract_hash"],
            )
            with self.assertRaisesRegex(KernelError, "required external effect"):
                osys.validate(
                    checks=[], inspected_by="TEST", runtime_acceptance_reference="runtime/changed-replan",
                )
            with self.assertRaisesRegex(KernelError, "immutable historical lineage"):
                osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
            prepared = osys.effect(
                transition="PREPARE", effect_id="attempt_two", action_id="submit_job",
            ).snapshot
            self.assertEqual(prepared.state["execution"]["effect_ledger"]["attempt_two"]["state"], "INTENT_RECORDED")

    def test_committed_effect_does_not_satisfy_same_action_id_with_changed_request_payload(self):
        with repository("effect-replan-changed-request") as root:
            osys = BuildOS(root)
            osys.bootstrap(
                request("EFFECT-REQUEST-CHANGED", execution_class="EXTERNAL_EFFECT", no_source=True),
                execution_spec=spec(external=True),
            )
            self._commit_provider_effect(osys)
            osys.report_blocker(
                family="local_defect", evidence="evidence/plan-a-invalid",
                assumption_id="input_complete",
            )
            changed = spec(external=True, plan_id="plan_two")
            changed["effects"][0]["effect_input"] = {
                "kind": "PROJECT_ARTIFACT", "path": ALT_EFFECT_INPUT_PATH,
                "sha256": ALT_EFFECT_INPUT_SHA256,
            }
            replaced = osys.replan(execution_spec=changed).snapshot
            self.assertEqual(replaced.event["effects_carried"], [])
            self.assertEqual(replaced.event["effects_retired"], ["attempt_one"])
            self.assertEqual(replaced.state["execution"]["effect_ledger"], {})
            with self.assertRaisesRegex(KernelError, "required external effect"):
                osys.validate(
                    checks=[], inspected_by="TEST",
                    runtime_acceptance_reference="runtime/changed-request",
                )

    def test_resolved_no_effect_carries_retry_authority_but_unresolved_effect_blocks_replan(self):
        with repository("effect-replan-no-effect") as root:
            osys = BuildOS(root)
            osys.bootstrap(
                request("EFFECT-NONE", execution_class="EXTERNAL_EFFECT", no_source=True),
                execution_spec=spec(external=True, idempotent=False),
            )
            osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
            osys.effect(
                transition="FAIL_BEFORE_DISPATCH", effect_id="attempt_one",
                reference="preflight/provider-not-called",
            )
            osys.report_blocker(
                family="local_defect", evidence="evidence/plan-a-invalid",
                assumption_id="input_complete",
            )
            replaced = osys.replan(
                execution_spec=spec(external=True, idempotent=False, plan_id="plan_two"),
            ).snapshot
            self.assertEqual(replaced.event["effects_carried"], ["attempt_one"])
            retried = osys.effect(transition="AUTHORIZE_RETRY", effect_id="attempt_one").snapshot
            self.assertEqual(
                retried.state["execution"]["effect_ledger"]["attempt_one"]["retry_basis"],
                "POSITIVE_NO_EFFECT_PROOF",
            )

        with repository("effect-replan-changed-no-effect") as root:
            osys = BuildOS(root)
            osys.bootstrap(
                request("EFFECT-NONE-CHANGED", execution_class="EXTERNAL_EFFECT", no_source=True),
                execution_spec=spec(external=True, idempotent=False),
            )
            osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
            osys.effect(
                transition="FAIL_BEFORE_DISPATCH", effect_id="attempt_one",
                reference="preflight/provider-not-called",
            )
            osys.report_blocker(
                family="local_defect", evidence="evidence/plan-a-invalid",
                assumption_id="input_complete",
            )
            changed = spec(external=True, idempotent=False, plan_id="plan_two")
            changed["effects"][0]["effect_input"] = {
                "kind": "PROJECT_ARTIFACT", "path": ALT_EFFECT_INPUT_PATH,
                "sha256": ALT_EFFECT_INPUT_SHA256,
            }
            replaced = osys.replan(execution_spec=changed).snapshot
            self.assertEqual(replaced.event["effects_carried"], [])
            self.assertEqual(replaced.event["effects_retired"], ["attempt_one"])
            with self.assertRaisesRegex(KernelError, "effect intent is not recorded"):
                osys.effect(transition="AUTHORIZE_RETRY", effect_id="attempt_one")
            prepared = osys.effect(
                transition="PREPARE", effect_id="attempt_two", action_id="submit_job",
            ).snapshot
            self.assertEqual(
                prepared.state["execution"]["effect_ledger"]["attempt_two"]["state"],
                "INTENT_RECORDED",
            )

        with repository("effect-replan-unresolved") as root:
            osys = BuildOS(root)
            osys.bootstrap(
                request("EFFECT-UNRESOLVED", execution_class="EXTERNAL_EFFECT", no_source=True),
                execution_spec=spec(external=True, idempotent=False),
            )
            osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
            osys.effect(transition="DISPATCH", effect_id="attempt_one")
            osys.report_blocker(
                family="local_defect", evidence="evidence/plan-a-invalid",
                assumption_id="input_complete",
            )
            with self.assertRaisesRegex(KernelError, "cannot bypass an unresolved external effect"):
                osys.replan(
                    execution_spec=spec(external=True, idempotent=False, plan_id="plan_two"),
                )

    def test_uncertain_effect_blocks_wip_replan_then_positive_no_effect_proof_preserves_wip(self):
        with repository("effect-wip-uncertain") as root:
            osys = BuildOS(root)
            osys.bootstrap(
                request("EFFECT-WIP", execution_class="EXTERNAL_EFFECT"),
                execution_spec=spec(external=True, idempotent=False),
            )
            osys.effect(transition="PREPARE", effect_id="attempt_one", action_id="submit_job")
            osys.effect(transition="DISPATCH", effect_id="attempt_one")
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            osys.report_blocker(
                family="local_defect", evidence="evidence/critical", assumption_id="input_complete",
            )
            with self.assertRaisesRegex(KernelError, "cannot bypass an unresolved external effect"):
                osys.replan(
                    execution_spec=spec(external=True, idempotent=False, plan_id="plan_two"),
                )
            osys.effect(
                transition="RECONCILE_NO_EFFECT", effect_id="attempt_one",
                reference="provider/positive-no-effect", predicate="canonical_no_effect",
            )
            replaced = osys.replan(
                execution_spec=spec(external=True, idempotent=False, plan_id="plan_two"),
            ).snapshot
            self.assertEqual((root / "app.py").read_text(encoding="utf-8"), "value = 2\n")
            self.assertEqual(replaced.event["effects_carried"], ["attempt_one"])
            retried = osys.effect(transition="AUTHORIZE_RETRY", effect_id="attempt_one").snapshot
            self.assertEqual(
                retried.state["execution"]["effect_ledger"]["attempt_one"]["retry_basis"],
                "POSITIVE_NO_EFFECT_PROOF",
            )


class ProportionalAssuranceTests(unittest.TestCase):
    def test_validation_cannot_assure_descendant_committed_by_a_claim(self):
        with repository("claim-mutates-head") as root:
            mutating = {
                "id": "mutating_final",
                "argv": [
                    sys.executable, "-c",
                    "from pathlib import Path; import subprocess; "
                    "p=Path('app.py'); assert p.read_text(encoding='utf-8') == 'value = 2\\n'; "
                    "p.write_text('value = 999\\n', encoding='utf-8'); "
                    "subprocess.run(['git','add','app.py'], check=True); "
                    "subprocess.run(['git','commit','-qm','unvalidated descendant'], check=True)",
                ],
            }
            registry_sha = install_command_registry(root, [mutating])
            value = spec()
            value["commands"] = [trusted_command(mutating, registry_sha)]
            value["claims"] = [{
                "id": "final_assurance", "description": "assert then mutate",
                "command_id": "mutating_final", "dependencies": ["app.py"],
                "mode": "FINAL", "role": "ACCEPTANCE",
                "acceptance": ["behavior is correct"],
            }]
            osys = BuildOS(root)
            osys.bootstrap(request("CLAIM-MUTATES-HEAD"), execution_spec=value)
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py"); git(root, "commit", "-qm", "recorded candidate")
            recorded = osys.record_commit().snapshot.state["product_commit"]["sha"]
            with self.assertRaisesRegex(KernelError, "validation command changed product identity"):
                osys.validate(checks=[], inspected_by="TEST")
            self.assertNotEqual(git(root, "rev-parse", "HEAD"), recorded)

    def test_validation_rejects_every_product_identity_mutation_family(self):
        mutations = {
            "tracked_edit": (
                "from pathlib import Path; Path('app.py').write_text('dirty edit\\n', encoding='utf-8')"
            ),
            "tracked_delete": "from pathlib import Path; Path('app.py').unlink()",
            "type_change": (
                "import subprocess; "
                "b=subprocess.run(['git','hash-object','-w','--stdin'],input='other.py\\n',text=True,capture_output=True,check=True).stdout.strip(); "
                "subprocess.run(['git','update-index','--cacheinfo',f'120000,{b},app.py'],check=True); "
                "subprocess.run(['git','commit','-qm','validation type change'],check=True)"
            ),
            "tree_equivalent_head_move": (
                "import subprocess; subprocess.run(['git','commit','--allow-empty','-qm','validation empty commit'],check=True)"
            ),
        }
        for name, code in mutations.items():
            with self.subTest(name=name), repository(f"validation-{name}") as root:
                command = {"id": "mutator", "argv": [sys.executable, "-c", code]}
                value = spec_with_commands(root, [command], [{
                    "id": "final_assurance", "description": name,
                    "command_id": "mutator", "dependencies": ["app.py"],
                    "mode": "FINAL", "role": "ACCEPTANCE",
                    "acceptance": ["behavior is correct"],
                }])
                osys = BuildOS(root)
                osys.bootstrap(request(f"VALIDATION-{name.upper()}"), execution_spec=value)
                (root / "app.py").write_text("value = 2\n", encoding="utf-8")
                git(root, "add", "app.py"); git(root, "commit", "-qm", "recorded candidate")
                osys.record_commit()
                with self.assertRaisesRegex(KernelError, "validation command changed product identity"):
                    osys.validate(checks=[], inspected_by="TEST")

    def test_validation_allows_ignored_output_and_binds_one_exact_target(self):
        with repository("validation-ignored-output") as root:
            command = {
                "id": "ignored_output",
                "argv": [
                    sys.executable, "-c",
                    "from pathlib import Path; Path('.buildos/validation-output.tmp').write_text('ok')",
                ],
            }
            value = spec_with_commands(root, [command], [{
                "id": "final_assurance", "description": "ignored temporary output",
                "command_id": "ignored_output", "dependencies": ["app.py"],
                "mode": "FINAL", "role": "ACCEPTANCE",
                "acceptance": ["behavior is correct"],
            }])
            osys = BuildOS(root)
            osys.bootstrap(request("VALIDATION-IGNORED"), execution_spec=value)
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py"); git(root, "commit", "-qm", "recorded candidate")
            recorded = osys.record_commit().snapshot.state["product_commit"]
            assured = osys.validate(checks=[], inspected_by="TEST").snapshot
            evidence_ref = assured.state["evidence"][-1]
            evidence = json.loads((root / evidence_ref["path"]).read_text(encoding="utf-8"))
            plan = assured.state["execution"]["last_assurance_plan"]
            self.assertEqual(
                (recorded["sha"], recorded["tree"]),
                (plan["target_sha"], plan["target_tree"]),
            )
            self.assertEqual(
                (plan["target_sha"], plan["target_tree"]),
                (evidence["target_sha"], evidence["target_tree"]),
            )
            self.assertEqual(
                (evidence["target_sha"], evidence["target_tree"]),
                (assured.state["assurance"]["target_sha"], assured.state["assurance"]["validated_tree"]),
            )
            self.assertTrue((root / ".buildos" / "validation-output.tmp").is_file())

    def test_early_mutating_claim_stops_before_later_claim(self):
        with repository("validation-multi-claim") as root:
            early = {
                "id": "early_mutator",
                "argv": [sys.executable, "-c", "from pathlib import Path; Path('app.py').write_text('mutated\\n')"],
            }
            later = {
                "id": "later_claim",
                "argv": [sys.executable, "-c", "from pathlib import Path; Path('.buildos/later-ran').write_text('yes')"],
            }
            value = spec_with_commands(root, [early, later], [
                {
                    "id": "a_early", "description": "early mutation", "command_id": "early_mutator",
                    "dependencies": ["app.py"], "mode": "FINAL", "role": "ACCEPTANCE",
                    "acceptance": ["behavior is correct"],
                },
                {
                    "id": "z_later", "description": "later claim", "command_id": "later_claim",
                    "dependencies": ["app.py"], "mode": "FINAL", "role": "SECURITY",
                    "acceptance": ["behavior is correct"],
                },
            ])
            osys = BuildOS(root)
            osys.bootstrap(request("VALIDATION-MULTI"), execution_spec=value)
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py"); git(root, "commit", "-qm", "recorded candidate")
            osys.record_commit()
            with self.assertRaisesRegex(KernelError, "validation command changed product identity"):
                osys.validate(checks=[], inspected_by="TEST")
            self.assertFalse((root / ".buildos" / "later-ran").exists())

    def test_enhanced_validation_retry_after_evidence_publication_keeps_target_identity(self):
        with repository("validation-evidence-retry") as root:
            osys = BuildOS(root)
            osys.bootstrap(request("VALIDATION-EVIDENCE-RETRY"), execution_spec=spec())
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py"); git(root, "commit", "-qm", "recorded candidate")
            recorded = osys.record_commit().snapshot.state["product_commit"]
            kwargs = {"checks": [], "inspected_by": "TEST", "op_id": "validation-evidence-retry"}
            with self.assertRaises(InjectedFailure):
                osys.validate(configured_failures="after_evidence_publish", **kwargs)
            retried = osys.validate(**kwargs)
            self.assertEqual(retried.snapshot.state["phase"], "ASSURANCE_READY")
            plan = retried.snapshot.state["execution"]["last_assurance_plan"]
            self.assertEqual((plan["target_sha"], plan["target_tree"]), (recorded["sha"], recorded["tree"]))

    def test_r3_rollback_recovery_claim_executes_fresh_in_each_revision(self):
        with repository("r3-rollback-fresh") as root:
            rollback = {
                "id": "rollback",
                "argv": [
                    sys.executable, "-c",
                    "from pathlib import Path; p=Path('.buildos/rollback-count.txt'); "
                    "n=int(p.read_text() if p.exists() else '0')+1; "
                    "p.write_text(str(n)); print(n)",
                ],
            }
            rows = [*COMMAND_ROWS, rollback]
            registry_sha = install_command_registry(root, rows)
            value = spec()
            value["commands"] = [trusted_command(row, registry_sha) for row in rows]
            value["claims"].append({
                "id": "rollback_current", "description": "current rollback proof",
                "command_id": "rollback", "dependencies": ["app.py"],
                "mode": "AFFECTED", "role": "ROLLBACK_RECOVERY",
                "acceptance": ["behavior is correct"],
            })
            value["claims"].extend([
                {
                    "id": "security_affected", "description": "security evidence",
                    "command_id": "focused", "dependencies": ["app.py"],
                    "mode": "AFFECTED", "role": "SECURITY",
                    "acceptance": ["behavior is correct"],
                },
                {
                    "id": "qc_affected", "description": "QC evidence",
                    "command_id": "focused", "dependencies": ["app.py"],
                    "mode": "AFFECTED", "role": "QC",
                    "acceptance": ["behavior is correct"],
                },
            ])
            req = request(
                "R3-ROLLBACK-FRESH", authorization="APPROVED",
                authorization_reference="owner/r3-rollback-fresh",
            )
            req["risk"] = "R3"
            req["authorization_actor"] = "OWNER"
            osys = BuildOS(root)
            osys.bootstrap(req, execution_spec=value)
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py"); git(root, "commit", "-qm", "revision one")
            osys.record_commit()
            osys.validate(
                checks=[], inspected_by="TEST", reviewer="REVIEWER-ONE",
                review_reference="review/r1",
            )
            osys.close()
            osys.revise(reason="unrelated revision")
            (root / "other.py").write_text("other = 2\n", encoding="utf-8")
            git(root, "add", "other.py"); git(root, "commit", "-qm", "revision two")
            osys.record_commit()
            plan = osys.assurance_plan()
            self.assertIn("focused_behavior", plan["reuse"])
            self.assertIn("security_affected", plan["reuse"])
            self.assertIn("qc_affected", plan["reuse"])
            self.assertIn("rollback_current", plan["execute"])
            second = osys.validate(
                checks=[], inspected_by="TEST", reviewer="REVIEWER-TWO",
                review_reference="review/r2",
            ).snapshot
            self.assertEqual((root / ".buildos" / "rollback-count.txt").read_text(), "2")
            self.assertIn("rollback_current", second.state["execution"]["last_assurance_plan"]["executed"])
            self.assertFalse(second.state["execution"]["claim_results"]["rollback_current"]["reused"])
            osys.close()
            osys.revise(reason="rollback dependency changed")
            (root / "app.py").write_text("value = 3\n", encoding="utf-8")
            git(root, "add", "app.py"); git(root, "commit", "-qm", "revision three")
            osys.record_commit()
            third_plan = osys.assurance_plan()
            self.assertIn("rollback_current", third_plan["execute"])
            osys.validate(
                checks=[], inspected_by="TEST", reviewer="REVIEWER-THREE",
                review_reference="review/r3",
            )
            self.assertEqual((root / ".buildos" / "rollback-count.txt").read_text(), "3")

    def test_r3_reused_rollback_marker_cannot_satisfy_current_evidence(self):
        with repository("r3-forged-reuse") as root:
            req = request(
                "R3-FORGED-REUSE", authorization="APPROVED",
                authorization_reference="owner/r3-forged-reuse",
            )
            req["risk"] = "R3"; req["authorization_actor"] = "OWNER"
            value = spec()
            value["claims"].append({
                "id": "rollback_current", "description": "rollback",
                "command_id": "focused", "dependencies": ["app.py"],
                "mode": "AFFECTED", "role": "ROLLBACK_RECOVERY",
                "acceptance": ["behavior is correct"],
            })
            osys = BuildOS(root)
            osys.bootstrap(req, execution_spec=value)
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py"); git(root, "commit", "-qm", "candidate")
            osys.record_commit()
            real_plan = osys.assurance_plan()
            forged = copy.deepcopy(real_plan)
            rollback_row = next(row for row in forged["claims"] if row["claim_id"] == "rollback_current")
            rollback_row["disposition"] = "REUSE"
            rollback_row["previous_evidence"] = {"path": ".buildos/forged.json", "sha256": "0" * 64}
            forged["execute"] = [item for item in forged["execute"] if item != "rollback_current"]
            forged["reuse"] = [*forged["reuse"], "rollback_current"]
            with patch("buildos.facade.execution.claim_plan", return_value=forged):
                with self.assertRaisesRegex(KernelError, "R3 validation requires a rollback/recovery check"):
                    osys.validate(
                        checks=[], inspected_by="TEST", reviewer="REVIEWER",
                        review_reference="review/forged",
                    )

    def test_r1_and_r2_unchanged_claim_is_reused_while_final_claim_runs(self):
        for risk in ("R1", "R2"):
            with self.subTest(risk=risk), repository(f"claims-{risk.lower()}") as root:
                osys = BuildOS(root)
                req = request(f"CLAIMS-{risk}")
                req["risk"] = risk
                osys.bootstrap(req, execution_spec=spec())
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
            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            kwargs = {"execution_spec": spec(plan_id="plan_two"), "op_id": "crash-replan"}
            with self.assertRaises(InjectedFailure):
                osys.replan(configured_failures="after_pointer_swap", **kwargs)
            retried = osys.replan(**kwargs)
            self.assertTrue(retried.idempotent)
            self.assertEqual((root / "app.py").read_text(encoding="utf-8"), "value = 2\n")
            self.assertEqual(
                retried.snapshot.state["execution"]["product_state_binding"]["dirty_paths"],
                ["app.py"],
            )

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
