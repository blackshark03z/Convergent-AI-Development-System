from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
SCRIPT = PACKAGE / "skills" / "project-lifecycle-bootstrap" / "scripts" / "side_effect_contract.py"
TEMPLATE = PACKAGE / "templates" / "project-lifecycle" / "SIDE_EFFECT_CONTRACT.json.tmpl"
SPEC = importlib.util.spec_from_file_location("side_effect_contract", SCRIPT)
assert SPEC and SPEC.loader
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)


def example() -> dict:
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


class SideEffectContractTests(unittest.TestCase):
    def test_portable_template_is_valid(self):
        result = contract.validate_contract(example())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["invariant"], "SIDE_EFFECT_AUTHORITY_AND_RECOVERY_FORMALIZED")
        self.assertEqual(result["dangerous_actions"], 1)

    def test_unknown_must_be_a_queue_barrier(self):
        value = example()
        value["dangerous_actions"][0]["unknown_is_barrier"] = False
        with self.assertRaisesRegex(contract.ContractError, "unknown a queue barrier"):
            contract.validate_contract(value)

    def test_non_idempotent_retry_requires_positive_no_effect_proof(self):
        value = example()
        value["dangerous_actions"][0]["positive_no_effect_proof"] = ""
        with self.assertRaisesRegex(contract.ContractError, "positive_no_effect_proof"):
            contract.validate_contract(value)

        unsafe = example()
        unsafe["dangerous_actions"][0]["retry_policy"] = "SAFE_IDEMPOTENT"
        with self.assertRaisesRegex(contract.ContractError, "non-idempotent"):
            contract.validate_contract(unsafe)

    def test_retry_and_replay_share_one_canonical_predicate(self):
        value = example()
        value["canonical_predicates"].append({
            "id": "different_no_effect", "semantics": "A weaker unrelated proof.",
            "verifier": "different verifier",
        })
        value["crash_recovery"][0]["proof_predicate"] = "different_no_effect"
        with self.assertRaisesRegex(contract.ContractError, "canonical no-effect predicate"):
            contract.validate_contract(value)

        unknown = example()
        unknown["semantic_consumers"][2]["predicate_id"] = "missing_predicate"
        with self.assertRaisesRegex(contract.ContractError, "unknown canonical predicate"):
            contract.validate_contract(unknown)

    def test_every_retry_replay_and_recovery_consumer_uses_the_action_proof(self):
        for role in ("RETRY", "REPLAY", "RECOVERY"):
            with self.subTest(role=role):
                value = example()
                value["canonical_predicates"].append({
                    "id": "weak_no_effect",
                    "semantics": "A weaker proof that must not authorize another attempt.",
                    "verifier": "weak verifier",
                })
                if role == "RECOVERY":
                    value["semantic_consumers"].append({
                        "id": "recovery_no_effect_gate",
                        "action_id": "submit_external_effect",
                        "role": role,
                        "predicate_id": "weak_no_effect",
                        "purpose": "Permit recovery after possible execution.",
                    })
                else:
                    target = next(
                        row for row in value["semantic_consumers"] if row["role"] == role
                    )
                    target["predicate_id"] = "weak_no_effect"
                with self.assertRaisesRegex(contract.ContractError, "canonical no-effect predicate"):
                    contract.validate_contract(value)

    def test_missing_canonical_retry_or_replay_binding_is_rejected(self):
        for role in ("RETRY", "REPLAY"):
            with self.subTest(role=role):
                value = example()
                value["semantic_consumers"] = [
                    row for row in value["semantic_consumers"] if row["role"] != role
                ]
                with self.assertRaisesRegex(contract.ContractError, "missing canonical no-effect"):
                    contract.validate_contract(value)

    def test_legacy_single_action_consumer_shape_remains_compatible(self):
        value = example()
        for row in value["semantic_consumers"]:
            row.pop("action_id")
            row.pop("role")
        self.assertEqual(contract.validate_contract(value)["status"], "PASS")

    def test_possible_or_confirmed_effect_never_authorizes_retry(self):
        for effect_state in ("POSSIBLE", "CONFIRMED"):
            with self.subTest(effect_state=effect_state):
                value = example()
                value["crash_recovery"][1]["effect_state"] = effect_state
                value["crash_recovery"][1]["retry_authority"] = "IDEMPOTENT"
                with self.assertRaisesRegex(contract.ContractError, "forbid retry"):
                    contract.validate_contract(value)

    def test_legacy_equivalence_requires_explicit_verifier(self):
        value = example()
        value["schema_compatibility"][1]["verifier"] = ""
        with self.assertRaisesRegex(contract.ContractError, "explicit verifier"):
            contract.validate_contract(value)

    def test_exactly_one_current_schema_is_required(self):
        missing = example()
        missing["schema_compatibility"][0]["policy"] = "UNMIGRATABLE"
        with self.assertRaisesRegex(contract.ContractError, "exactly one CURRENT_SCHEMA"):
            contract.validate_contract(missing)

        duplicate = copy.deepcopy(example())
        duplicate["schema_compatibility"][1]["policy"] = "CURRENT_SCHEMA"
        with self.assertRaisesRegex(contract.ContractError, "exactly one CURRENT_SCHEMA"):
            contract.validate_contract(duplicate)


if __name__ == "__main__":
    unittest.main(verbosity=2)
