from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from buildos.evidence_envelope import EvidenceEnvelopeError, evaluate_envelope
from tests.test_thin_guard import AI, snapshot_files


def envelope() -> dict:
    return {
        "goal_ref": "TASK.md#Acceptance",
        "candidate": {
            "base_revision": "a" * 40,
            "candidate_revision": "b" * 40,
        },
        "criteria": [
            {
                "criterion_id": "journey",
                "oracle_type": "runtime",
                "oracle_identity": "journey-v1",
                "verifier_identity": "browser-check",
                "verifier_version": "1",
                "result": "PASS",
                "evidence_refs": ["artifact://journey/1"],
            },
        ],
        "invariants": [
            {
                "invariant_id": "canonical-state",
                "result": "PASS",
                "evidence_refs": ["git://candidate/tree"],
            },
        ],
        "authority": {"required": False, "status": "NOT_REQUIRED"},
        "review": {"required": False, "result": "NOT_REQUIRED", "blocking_findings": []},
        "provenance": {
            "execution_environment": "fixture://local",
            "evidence_producer": "tests/test_evidence_envelope.py",
        },
    }


def cli(root: Path, input_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(AI),
            "--root",
            str(root),
            "verify-envelope",
            "--input",
            str(input_path),
        ],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )


class EvidenceEnvelopeTests(unittest.TestCase):
    def test_complete_objective_evidence_is_verified(self):
        result = evaluate_envelope(envelope())
        self.assertEqual(result["verdict"], "VERIFIED")
        self.assertTrue(result["read_only"])

    def test_pass_without_evidence_is_unknown(self):
        value = envelope()
        value["criteria"][0]["evidence_refs"] = []
        result = evaluate_envelope(value)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertIn("CRITERION_EVIDENCE_MISSING", result["reason_codes"])

    def test_failed_criterion_with_evidence_is_not_verified(self):
        value = envelope()
        value["criteria"][0]["result"] = "FAIL"
        result = evaluate_envelope(value)
        self.assertEqual(result["verdict"], "NOT_VERIFIED")
        self.assertIn("CRITERION_FAILED:journey", result["reason_codes"])

    def test_weakened_or_implementation_coupled_oracle_cannot_self_prove(self):
        for kind in ("WEAKENED", "IMPLEMENTATION_COUPLED"):
            with self.subTest(kind=kind):
                value = envelope()
                value["criteria"][0].update({
                    "oracle_changed": True,
                    "oracle_change_kind": kind,
                    "oracle_change_authorized": True,
                    "independent_evidence_refs": ["artifact://independent/1"],
                })
                result = evaluate_envelope(value)
                self.assertEqual(result["verdict"], "UNKNOWN")
                self.assertIn("ORACLE_INTEGRITY_UNPROVEN", result["reason_codes"])

    def test_authorized_clarification_with_independent_evidence_can_verify(self):
        value = envelope()
        value["criteria"][0].update({
            "oracle_changed": True,
            "oracle_change_kind": "CLARIFICATION",
            "oracle_change_authorized": True,
            "independent_evidence_refs": ["artifact://independent/1"],
        })
        self.assertEqual(evaluate_envelope(value)["verdict"], "VERIFIED")

    def test_regression_coverage_alone_is_unknown(self):
        value = envelope()
        value["criteria"][0].update({
            "oracle_changed": True,
            "oracle_change_kind": "REGRESSION_COVERAGE",
            "oracle_change_authorized": False,
        })
        result = evaluate_envelope(value)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertIn("REGRESSION_SELF_PROOF_ONLY", result["reason_codes"])

    def test_required_authority_missing_or_denied(self):
        missing = envelope()
        missing["authority"] = {"required": True, "status": "MISSING"}
        denied = envelope()
        denied["authority"] = {"required": True, "status": "DENIED"}
        self.assertEqual(evaluate_envelope(missing)["verdict"], "UNKNOWN")
        self.assertEqual(evaluate_envelope(denied)["verdict"], "NOT_VERIFIED")

    def test_required_review_incomplete_or_blocking(self):
        incomplete = envelope()
        incomplete["review"] = {"required": True, "result": "UNKNOWN", "blocking_findings": []}
        blocked = envelope()
        blocked["review"] = {
            "required": True,
            "result": "BLOCK",
            "blocking_findings": ["contract mismatch"],
        }
        self.assertEqual(evaluate_envelope(incomplete)["verdict"], "UNKNOWN")
        self.assertEqual(evaluate_envelope(blocked)["verdict"], "NOT_VERIFIED")

    def test_failed_invariant_with_evidence_is_not_verified(self):
        value = envelope()
        value["invariants"][0]["result"] = "FAIL"
        result = evaluate_envelope(value)
        self.assertEqual(result["verdict"], "NOT_VERIFIED")
        self.assertIn("INVARIANT_FAILED:canonical-state", result["reason_codes"])

    def test_lifecycle_state_is_rejected(self):
        value = envelope()
        value["phase"] = "VERIFYING"
        with self.assertRaises(EvidenceEnvelopeError):
            evaluate_envelope(value)

    def test_nested_schema_cannot_accumulate_execution_state(self):
        value = envelope()
        value["criteria"][0]["retry_count"] = 4
        with self.assertRaises(EvidenceEnvelopeError):
            evaluate_envelope(value)

    def test_cli_is_read_only_and_returns_zero_only_for_verified(self):
        with tempfile.TemporaryDirectory(prefix="cads-envelope-") as raw:
            root = Path(raw)
            input_path = root / "evidence.json"
            input_path.write_text(json.dumps(envelope()), encoding="utf-8")
            before = snapshot_files(root)
            verified = cli(root, Path("evidence.json"))
            after = snapshot_files(root)

            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
            self.assertEqual(json.loads(verified.stdout)["verdict"], "VERIFIED")
            self.assertEqual(before, after)

            unknown_value = envelope()
            unknown_value["criteria"][0]["evidence_refs"] = []
            input_path.write_text(json.dumps(unknown_value), encoding="utf-8")
            unknown = cli(root, Path("evidence.json"))
            self.assertEqual(unknown.returncode, 2, unknown.stdout + unknown.stderr)
            self.assertEqual(json.loads(unknown.stdout)["verdict"], "UNKNOWN")

    def test_cli_rejects_input_outside_root(self):
        with tempfile.TemporaryDirectory(prefix="cads-envelope-root-") as raw_root:
            with tempfile.TemporaryDirectory(prefix="cads-envelope-outside-") as raw_outside:
                root = Path(raw_root)
                outside = Path(raw_outside) / "evidence.json"
                outside.write_text(json.dumps(envelope()), encoding="utf-8")
                result = cli(root, outside)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["result"], "BLOCK")
                self.assertIn("inside repository root", payload["message"])


if __name__ == "__main__":
    unittest.main()
