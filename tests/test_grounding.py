from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from buildos import git_adapter
from buildos.grounding import (
    GroundingError,
    derive_action_rights,
    grounding_projection,
    task_request_from_work_loop,
    validate_grounding_report,
)
from buildos.work_contract import validate_contract
from tests.test_work_contract import contract


PACKAGE = Path(__file__).resolve().parents[1]
AI = PACKAGE / "scripts" / "ai.py"


def run_git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=root, text=True, encoding="utf-8",
        errors="replace", capture_output=True, timeout=30,
    )
    if completed.returncode:
        raise AssertionError(completed.stdout + completed.stderr)
    return completed.stdout.strip()


def repository(root: Path) -> dict:
    root.mkdir()
    run_git(root, "init")
    run_git(root, "config", "user.name", "Build OS Test")
    run_git(root, "config", "user.email", "buildos@example.invalid")
    (root / "scripts").mkdir()
    (root / "scripts" / "ai.py").write_text("print('facade')\n", encoding="utf-8")
    run_git(root, "add", "scripts/ai.py")
    run_git(root, "commit", "-m", "baseline")
    return git_adapter.snapshot(root)


def report(root: Path, observed: dict, contract_hash: str, *, claim_id: str = "repo.current_cli", outcome: str = "VERIFIED") -> dict:
    digest = hashlib.sha256((root / "scripts" / "ai.py").read_bytes()).hexdigest()
    return {
        "schema": "buildos.grounding-report.v1",
        "contract_hash": contract_hash,
        "worker": {"id": "worker-role", "observed_at": "2026-08-24T00:00:00Z"},
        "repository": {
            "root": str(root.resolve()), "head": observed["head"], "tree": observed["tree"],
            "product_state_digest": observed["product_state_digest"],
        },
        "scope_claim_ids": [claim_id],
        "execution_request": {
            "requested_action": "LOCAL_MUTATION", "product_change_mode": "PRODUCT_DELTA",
            "risk": "AUTO", "allowed_paths": ["scripts/**"],
            "prohibited_paths": [".buildos/**"], "acceptance_commands": ["python -m unittest"],
        },
        "evidence": [{
            "id": "evidence.cli", "kind": "REPO_FILE", "locator": "scripts/ai.py",
            "digest": digest, "observed_at": "2026-08-24T00:00:00Z",
        }],
        "results": [{
            "claim_id": claim_id, "outcome": outcome,
            "summary": "Repository inspection result.", "evidence_refs": ["evidence.cli"],
        }],
        "discoveries": [],
    }


class GroundingTests(unittest.TestCase):
    def _contract(self, root: Path) -> tuple[dict, str]:
        raw = contract()
        raw["target"]["repository"] = str(root.resolve())
        normalized = validate_contract(raw)
        encoded = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return normalized, hashlib.sha256(encoded).hexdigest()

    def test_verified_targeted_claim_is_grounded_without_mutation_authority(self):
        with tempfile.TemporaryDirectory(prefix="grounding-") as raw:
            root = Path(raw) / "repo"
            observed = repository(root)
            work_contract, digest = self._contract(root)
            normalized = validate_grounding_report(
                work_contract, digest, report(root, observed, digest), root=root, observed_repository=observed,
            )
            projection = grounding_projection(normalized)
            self.assertEqual(projection["status"], "GROUNDED")
            self.assertEqual(projection["mutation_authority"], "NONE_READ_ONLY_GROUNDING")
            self.assertTrue(projection["unscoped_claims_remain_non_blocking"])
            self.assertEqual(projection["action_rights"]["requested_action_status"], "GRANTED")

    def test_repo_contradiction_is_local_adaptation_not_owner_escalation(self):
        with tempfile.TemporaryDirectory(prefix="grounding-") as raw:
            root = Path(raw) / "repo"
            observed = repository(root)
            work_contract, digest = self._contract(root)
            value = report(root, observed, digest, outcome="CONTRADICTED")
            projection = grounding_projection(validate_grounding_report(
                work_contract, digest, value, root=root, observed_repository=observed,
            ))
            self.assertEqual(projection["status"], "GROUNDED_WITH_LOCAL_ADAPTATION")
            self.assertEqual(projection["local_adaptation_claim_ids"], ["repo.current_cli"])
            self.assertEqual(projection["decision_requests"], [])

    def test_canonical_conflict_emits_deterministic_typed_decision_request(self):
        with tempfile.TemporaryDirectory(prefix="grounding-") as raw:
            root = Path(raw) / "repo"
            observed = repository(root)
            work_contract, digest = self._contract(root)
            value = report(root, observed, digest, claim_id="acceptance.contract", outcome="CONTRADICTED")
            first = grounding_projection(validate_grounding_report(
                work_contract, digest, value, root=root, observed_repository=observed,
            ))
            second = grounding_projection(validate_grounding_report(
                work_contract, digest, value, root=root, observed_repository=observed,
            ))
            self.assertEqual(first, second)
            self.assertEqual(first["status"], "DECISION_REQUIRED")
            request = first["decision_requests"][0]
            self.assertEqual(request["decision_type"], "PRODUCT_INTENT")
            self.assertEqual(request["requested_from"], "TECH_LEAD")
            self.assertEqual(request["blocking_scope"], "ACTIONS_DEPENDENT_ON_CLAIM")
            self.assertEqual(first["action_rights"]["requested_action_status"], "BLOCKED")

    def test_stale_repository_binding_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="grounding-") as raw:
            root = Path(raw) / "repo"
            observed = repository(root)
            work_contract, digest = self._contract(root)
            value = report(root, observed, digest)
            value["repository"]["product_state_digest"] = "0" * 64
            with self.assertRaisesRegex(GroundingError, "stale"):
                validate_grounding_report(work_contract, digest, value, root=root, observed_repository=observed)

    def test_repo_result_cannot_rely_only_on_external_reference(self):
        with tempfile.TemporaryDirectory(prefix="grounding-") as raw:
            root = Path(raw) / "repo"
            observed = repository(root)
            work_contract, digest = self._contract(root)
            value = report(root, observed, digest)
            value["evidence"] = [{
                "id": "evidence.cli", "kind": "EXTERNAL_REFERENCE",
                "locator": "https://example.invalid/claim", "digest": None,
                "observed_at": "2026-08-24T00:00:00Z",
            }]
            with self.assertRaisesRegex(GroundingError, "locally verified"):
                validate_grounding_report(work_contract, digest, value, root=root, observed_repository=observed)

    def test_repo_evidence_cannot_cite_buildos_control_state(self):
        with tempfile.TemporaryDirectory(prefix="grounding-") as raw:
            root = Path(raw) / "repo"
            repository(root)
            (root / ".buildos").mkdir()
            control = root / ".buildos" / "CURRENT"
            control.write_text("not product truth\n", encoding="utf-8")
            observed = git_adapter.snapshot(root)
            work_contract, digest = self._contract(root)
            value = report(root, observed, digest)
            value["evidence"][0].update({
                "locator": ".buildos/CURRENT",
                "digest": hashlib.sha256(control.read_bytes()).hexdigest(),
            })
            with self.assertRaisesRegex(GroundingError, "control state"):
                validate_grounding_report(
                    work_contract, digest, value,
                    root=root, observed_repository=observed,
                )

    def test_grounding_cli_is_read_only(self):
        with tempfile.TemporaryDirectory(prefix="grounding-cli-") as raw:
            base = Path(raw)
            root = base / "repo"
            observed = repository(root)
            work_contract, digest = self._contract(root)
            contract_path = base / "contract.json"
            grounding_path = base / "grounding.json"
            contract_path.write_text(json.dumps(work_contract), encoding="utf-8")
            grounding_path.write_text(json.dumps(report(root, observed, digest)), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(AI), "--root", str(root), "contract", "--file", str(contract_path),
                 "--grounding", str(grounding_path), "--view", "grounding"],
                text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=30,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["status"], "GROUNDED")
            self.assertFalse((root / ".buildos").exists())

    def test_discovery_against_canonical_claim_requires_decision(self):
        with tempfile.TemporaryDirectory(prefix="grounding-") as raw:
            root = Path(raw) / "repo"
            observed = repository(root)
            work_contract, digest = self._contract(root)
            value = report(root, observed, digest)
            value["discoveries"] = [{
                "id": "discovery.architecture", "statement": "Repository evidence conflicts with the canonical premise.",
                "status": "VERIFIED", "conflicts_with": ["intent.outcome"], "evidence_refs": ["evidence.cli"],
            }]
            projection = grounding_projection(validate_grounding_report(
                work_contract, digest, value, root=root, observed_repository=observed,
            ))
            self.assertEqual(projection["status"], "DECISION_REQUIRED")
            self.assertEqual(projection["decision_requests"][0]["decision_type"], "PRODUCT_INTENT")

    def test_target_drift_is_explicit_and_duplicate_decisions_coalesce(self):
        with tempfile.TemporaryDirectory(prefix="grounding-") as raw:
            root = Path(raw) / "repo"
            observed = repository(root)
            work_contract, digest = self._contract(root)
            work_contract["target"]["head"] = "0" * 40
            work_contract["target"]["tree"] = "1" * 40
            encoded = json.dumps(work_contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            digest = hashlib.sha256(encoded).hexdigest()
            value = report(root, observed, digest, claim_id="acceptance.contract", outcome="CONTRADICTED")
            value["discoveries"] = [{
                "id": "discovery.same", "statement": "A second observation conflicts with the same premise.",
                "status": "VERIFIED", "conflicts_with": ["acceptance.contract"],
                "evidence_refs": ["evidence.cli"],
            }]
            projection = grounding_projection(validate_grounding_report(
                work_contract, digest, value, root=root, observed_repository=observed,
            ))
            self.assertTrue(projection["contract_target_drift"])
            self.assertEqual(len(projection["decision_requests"]), 1)
            self.assertEqual(
                projection["decision_requests"][0]["trigger_sources"],
                ["DISCOVERY:discovery.same", "GROUNDING_RESULT"],
            )

    def test_unrelated_open_question_does_not_block_requested_action(self):
        with tempfile.TemporaryDirectory(prefix="grounding-") as raw:
            root = Path(raw) / "repo"
            observed = repository(root)
            base = contract()
            base["target"]["repository"] = str(root.resolve())
            base["claims"].append({
                "id": "question.unrelated", "kind": "OPEN_QUESTION",
                "statement": "A later product choice remains open.", "authority": "TECH_LEAD",
                "binding": "ADVISORY", "status": "UNKNOWN", "source_refs": [],
                "repo_binding": None, "observed_at": None, "invalidators": [],
                "verification_owner": "TECH_LEAD",
            })
            base["open_question_ids"] = ["question.unrelated"]
            work_contract = validate_contract(base)
            digest = hashlib.sha256(json.dumps(
                work_contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            ).encode("utf-8")).hexdigest()
            normalized = validate_grounding_report(
                work_contract, digest, report(root, observed, digest), root=root, observed_repository=observed,
            )
            self.assertEqual(derive_action_rights(normalized)["requested_action_status"], "GRANTED")

    def test_scoped_open_question_becomes_a_typed_material_decision(self):
        with tempfile.TemporaryDirectory(prefix="grounding-") as raw:
            root = Path(raw) / "repo"
            observed = repository(root)
            base = contract()
            base["target"]["repository"] = str(root.resolve())
            base["claims"].append({
                "id": "question.material", "kind": "OPEN_QUESTION",
                "statement": "Which canonical behavior applies?", "authority": "TECH_LEAD",
                "binding": "ADVISORY", "status": "UNKNOWN", "source_refs": [],
                "repo_binding": None, "observed_at": None, "invalidators": [],
                "verification_owner": "TECH_LEAD",
            })
            base["open_question_ids"] = ["question.material"]
            work_contract = validate_contract(base)
            digest = hashlib.sha256(json.dumps(
                work_contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            ).encode("utf-8")).hexdigest()
            value = report(root, observed, digest, claim_id="question.material", outcome="UNKNOWN")
            value["results"][0]["evidence_refs"] = []
            normalized = validate_grounding_report(
                work_contract, digest, value, root=root, observed_repository=observed,
            )
            self.assertEqual(normalized["decision_requests"][0]["decision_type"], "OPEN_QUESTION")
            self.assertEqual(normalized["decision_requests"][0]["requested_from"], "TECH_LEAD")
            self.assertEqual(derive_action_rights(normalized)["requested_action_status"], "BLOCKED")

    def test_lifecycle_request_is_compiled_from_contract_and_worker_grounding(self):
        with tempfile.TemporaryDirectory(prefix="grounding-") as raw:
            root = Path(raw) / "repo"
            observed = repository(root)
            work_contract, digest = self._contract(root)
            normalized = validate_grounding_report(
                work_contract, digest, report(root, observed, digest), root=root, observed_repository=observed,
            )
            request = task_request_from_work_loop(work_contract, normalized)
            self.assertEqual(request["task_id"], "BUILD-OS-VNEXT-r1")
            self.assertEqual(request["outcome"], work_contract["objective"])
            self.assertEqual(request["acceptance"], [work_contract["claims"][1]["statement"]])
            self.assertEqual(request["allowed_paths"], ["scripts/**"])
            self.assertEqual(request["enforcement"], "BOUNDARY")


if __name__ == "__main__":
    unittest.main(verbosity=2)
