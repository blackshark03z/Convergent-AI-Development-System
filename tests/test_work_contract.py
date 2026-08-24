from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from buildos.work_contract import (
    MAX_CAPSULE_BYTES,
    WorkContractError,
    load_contract,
    validate_contract,
    validation_projection,
    worker_capsule,
)


PACKAGE = Path(__file__).resolve().parents[1]
AI = PACKAGE / "scripts" / "ai.py"
TEMPLATE = PACKAGE / "templates" / "work-contract" / "WORK_CONTRACT.json.tmpl"


def contract() -> dict:
    return {
        "schema": "buildos.work-contract.v1",
        "contract_id": "BUILD-OS-VNEXT",
        "revision": 1,
        "issuer": {
            "role": "TECH_LEAD",
            "identity": "tech-lead-role",
            "authority_reference": "decision:build-os-vnext",
            "issued_at": "2026-08-24T00:00:00Z",
        },
        "target": {
            "repository": "D:/Buil OS/Senior-AI-Build-OS-v1.22",
            "ref": "agent/vnext-evidence-work-loop",
            "head": None,
            "tree": None,
        },
        "objective": "Deliver an evidence-carrying Work Loop.",
        "non_goals": ["Do not build an AI product manager."],
        "claims": [
            {
                "id": "intent.outcome",
                "kind": "INTENT",
                "statement": "Build OS preserves authority while reducing duplicated reasoning.",
                "authority": "TECH_LEAD",
                "binding": "CANONICAL",
                "status": "DECIDED",
                "source_refs": [],
                "repo_binding": None,
                "observed_at": None,
                "invalidators": [],
                "verification_owner": "NONE",
            },
            {
                "id": "acceptance.contract",
                "kind": "ACCEPTANCE",
                "statement": "A structured contract can be validated without repository mutation.",
                "authority": "TECH_LEAD",
                "binding": "CANONICAL",
                "status": "DECIDED",
                "source_refs": [],
                "repo_binding": None,
                "observed_at": None,
                "invalidators": [],
                "verification_owner": "WORKER",
            },
            {
                "id": "repo.current_cli",
                "kind": "REPO_CLAIM",
                "statement": "scripts/ai.py is the normal Worker facade.",
                "authority": "TECH_LEAD",
                "binding": "VERIFY_IN_REPO",
                "status": "SUPPORTED",
                "source_refs": [],
                "repo_binding": None,
                "observed_at": None,
                "invalidators": ["The target repository HEAD changes."],
                "verification_owner": "WORKER",
            },
        ],
        "acceptance_ids": ["acceptance.contract"],
        "open_question_ids": [],
        "ship": {"mode": "HANDOFF_ONLY", "authority_reference": None},
        "metadata": {"parent_contract_hash": None, "source_context_refs": []},
    }


class WorkContractTests(unittest.TestCase):
    def test_template_and_contract_validate_deterministically(self):
        value = validate_contract(contract())
        self.assertEqual(value["contract_id"], "BUILD-OS-VNEXT")
        with tempfile.TemporaryDirectory(prefix="work-contract-") as raw:
            path = Path(raw) / "contract.json"
            path.write_text(json.dumps(contract(), indent=2), encoding="utf-8")
            first, first_hash = load_contract(path)
            second, second_hash = load_contract(path)
        self.assertEqual(first, second)
        self.assertEqual(first_hash, second_hash)
        template_value = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        validate_contract(template_value)

    def test_validation_projection_exposes_pending_repo_claims_without_authority(self):
        value = validate_contract(contract())
        with tempfile.TemporaryDirectory(prefix="work-contract-") as raw:
            path = Path(raw) / "contract.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            normalized, digest = load_contract(path)
        projection = validation_projection(normalized, digest)
        self.assertEqual(projection["status"], "PASS")
        self.assertEqual(projection["repo_verification_pending"], ["repo.current_cli"])
        self.assertEqual(projection["mutation_authority"], "NONE_READ_ONLY_INTAKE")

    def test_worker_capsule_is_bounded_and_does_not_copy_evidence_bodies(self):
        value = contract()
        for index in range(20):
            value["claims"].append({
                "id": f"repo.claim.{index}",
                "kind": "REPO_CLAIM",
                "statement": "Repository-sensitive claim " + ("x" * 900),
                "authority": "TECH_LEAD",
                "binding": "VERIFY_IN_REPO",
                "status": "SUPPORTED",
                "source_refs": [{
                    "id": f"source.{index}", "kind": "FILE",
                    "locator": f"evidence/{index}.json", "sha256": "a" * 64,
                    "observed_at": "2026-08-24T00:00:00Z",
                }],
                "repo_binding": None,
                "observed_at": "2026-08-24T00:00:00Z",
                "invalidators": ["HEAD changes"],
                "verification_owner": "WORKER",
            })
        normalized = validate_contract(value)
        capsule = worker_capsule(normalized, "b" * 64)
        encoded = json.dumps(capsule, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.assertLessEqual(len(encoded), MAX_CAPSULE_BYTES)
        self.assertEqual(capsule["current_action_right"], "READ_AND_VERIFY")
        self.assertEqual(capsule["mutation_authority"], "NONE_READ_ONLY_INTAKE")
        self.assertGreater(capsule["repo_verification_overflow"], 0)
        self.assertNotIn("evidence/0.json", encoded.decode("utf-8"))

    def test_advisory_model_cannot_claim_canonical_authority(self):
        value = contract()
        value["claims"][0]["authority"] = "ADVISORY_MODEL"
        with self.assertRaisesRegex(WorkContractError, "advisory model cannot own canonical"):
            validate_contract(value)

    def test_repo_claim_cannot_self_declare_verified_without_bound_evidence(self):
        value = contract()
        value["claims"][2]["status"] = "VERIFIED"
        with self.assertRaisesRegex(WorkContractError, "verified repository claim needs bound evidence"):
            validate_contract(value)

    def test_acceptance_and_open_question_references_are_typed(self):
        value = contract()
        value["acceptance_ids"] = ["repo.current_cli"]
        with self.assertRaisesRegex(WorkContractError, "non-acceptance"):
            validate_contract(value)
        value = contract()
        value["claims"].append({
            "id": "question.ship",
            "kind": "OPEN_QUESTION",
            "statement": "Which ship mode is authorized?",
            "authority": "TECH_LEAD",
            "binding": "ADVISORY",
            "status": "UNKNOWN",
            "source_refs": [],
            "repo_binding": None,
            "observed_at": None,
            "invalidators": [],
            "verification_owner": "OWNER",
        })
        with self.assertRaisesRegex(WorkContractError, "missing from open_question_ids"):
            validate_contract(value)

    def test_read_only_cli_creates_no_buildos_or_telemetry_state(self):
        with tempfile.TemporaryDirectory(prefix="work-contract-cli-") as raw:
            root = Path(raw) / "product"
            root.mkdir()
            source = Path(raw) / "contract.json"
            source.write_text(json.dumps(contract()), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable, str(AI), "--root", str(root), "contract",
                    "--file", str(source), "--view", "worker-capsule",
                ],
                text=True, encoding="utf-8", errors="replace", capture_output=True,
                timeout=30,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["projection"], "READ_ONLY_DERIVED")
            self.assertFalse((root / ".buildos").exists())

    def test_unexpected_fields_fail_closed(self):
        value = copy.deepcopy(contract())
        value["semantic_plan"] = {"pretend": "kernel reasoning"}
        with self.assertRaisesRegex(WorkContractError, "unexpected"):
            validate_contract(value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
