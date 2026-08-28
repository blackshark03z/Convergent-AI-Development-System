from __future__ import annotations

import hashlib
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from buildos import effect_store
from buildos.effect_safety import (
    EffectSafetyError,
    apply_verified_retry_proof,
    mark_dispatch_uncertain,
    prepare,
    reconcile,
    retry_safety,
    verify_retry_proof,
)
from buildos.external_effect import (
    effect_retry_safety,
    execute_external_effect,
    inspect_effect,
    list_effects,
    reconcile_effect,
    verify_effect_retry_proof,
)
from buildos.git_adapter import boundary_snapshot
from tests.test_thin_guard import append, repository, run_git


def intent(effect_id: str = "publish-release", *, idempotent: bool = False) -> dict:
    value = {
        "effect_id": effect_id,
        "operation": "publish",
        "target": "provider://account/release",
        "request_digest": hashlib.sha256(b"exact provider request").hexdigest(),
    }
    if idempotent:
        value.update({
            "idempotency_key": "release-request-001",
            "provider_idempotency_enforced": True,
            "idempotency_evidence": "provider contract section idempotency-keys",
        })
    return value


def trusted_response(challenge: dict, **changes: object) -> dict:
    value = {
        **challenge,
        "evidence": "verified provider read-back",
        "reference": "provider-query-42",
    }
    value.update(changes)
    return value


class EffectSafetyModelTests(unittest.TestCase):
    def test_ambiguous_dispatch_is_not_retry_safe_without_positive_proof(self):
        record = mark_dispatch_uncertain(prepare(intent()))
        self.assertEqual(record["state"], "DISPATCH_UNCERTAIN")
        self.assertEqual(
            retry_safety(record),
            {"safe": False, "reason_code": "AMBIGUOUS_DISPATCH_NO_RETRY_PROOF"},
        )

    def test_self_declared_provider_idempotency_is_not_retry_proof(self):
        record = mark_dispatch_uncertain(prepare(intent(idempotent=True)))
        self.assertEqual(
            retry_safety(record),
            {"safe": False, "reason_code": "AMBIGUOUS_DISPATCH_NO_RETRY_PROOF"},
        )

    def test_free_form_no_effect_evidence_cannot_make_retry_safe(self):
        record = mark_dispatch_uncertain(prepare(intent()))
        with self.assertRaisesRegex(EffectSafetyError, "trusted verifier"):
            reconcile(
                record,
                outcome="NO_EFFECT_CONFIRMED",
                evidence="trust me",
            )
        self.assertEqual(
            retry_safety(record),
            {"safe": False, "reason_code": "AMBIGUOUS_DISPATCH_NO_RETRY_PROOF"},
        )

    def test_only_exact_trusted_no_effect_proof_makes_retry_eligible(self):
        record = mark_dispatch_uncertain(prepare(intent()))
        proof = verify_retry_proof(
            record,
            kind="NO_EFFECT_CONFIRMED",
            verifier=lambda challenge: trusted_response(challenge),
        )
        resolved = apply_verified_retry_proof(record, proof)

        self.assertEqual(resolved["state"], "NO_EFFECT_CONFIRMED")
        self.assertEqual(
            retry_safety(resolved),
            {"safe": True, "reason_code": "POSITIVE_NO_EFFECT_PROOF"},
        )

    def test_only_exact_trusted_idempotency_proof_makes_retry_eligible(self):
        record = mark_dispatch_uncertain(prepare(intent(idempotent=True)))
        proof = verify_retry_proof(
            record,
            kind="PROVIDER_IDEMPOTENCY",
            verifier=lambda challenge: trusted_response(challenge),
        )
        resolved = apply_verified_retry_proof(record, proof)

        self.assertEqual(resolved["state"], "DISPATCH_UNCERTAIN")
        self.assertEqual(
            retry_safety(resolved),
            {"safe": True, "reason_code": "EXACT_PROVIDER_IDEMPOTENCY"},
        )

    def test_trusted_proof_must_match_exact_effect_binding(self):
        record = mark_dispatch_uncertain(prepare(intent(idempotent=True)))
        for field, value in (
            ("target", "provider://other/target"),
            ("operation", "delete"),
            ("request_digest", hashlib.sha256(b"other request").hexdigest()),
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(EffectSafetyError, f"exact {field}"):
                    verify_retry_proof(
                        record,
                        kind="PROVIDER_IDEMPOTENCY",
                        verifier=lambda challenge, field=field, value=value: trusted_response(
                            challenge, **{field: value},
                        ),
                    )
                self.assertFalse(retry_safety(record)["safe"])

    def test_claimed_provider_idempotency_requires_key_and_evidence(self):
        value = intent()
        value["provider_idempotency_enforced"] = True
        with self.assertRaisesRegex(EffectSafetyError, "exact key and canonical evidence"):
            prepare(value)


class ExternalEffectBoundaryTests(unittest.TestCase):
    def execute(self, root: Path, base: str, dispatcher, **values) -> dict:
        return execute_external_effect(
            root,
            base=base,
            intent=values.pop("intent", intent()),
            dispatcher=dispatcher,
            **values,
        )

    def test_known_success_records_intent_before_exactly_one_dispatch(self):
        with repository() as (root, base):
            calls: list[dict] = []

            def dispatcher(exact_intent: dict) -> dict:
                calls.append(exact_intent)
                durable = effect_store.load(root, exact_intent["effect_id"])
                self.assertEqual(durable["state"], "DISPATCH_UNCERTAIN")
                self.assertEqual(durable["dispatch_count"], 1)
                return {
                    "status": "CONFIRMED",
                    "reference": "provider-result-42",
                    "evidence": "provider acknowledged exact request digest",
                }

            result = self.execute(root, base, dispatcher)
            loaded = inspect_effect(root, "publish-release")

            self.assertEqual(len(calls), 1)
            self.assertTrue(result["dispatched"])
            self.assertEqual(result["effect_state"], "CONFIRMED")
            self.assertEqual(loaded["state"], "CONFIRMED")
            self.assertEqual(loaded["provider_reference"], "provider-result-42")
            self.assertFalse((root / ".buildos" / "effects").exists())
            self.assertEqual(run_git(root, "status", "--porcelain"), "")

    def test_dispatch_exception_preserves_ambiguity_across_reload(self):
        with repository() as (root, base):
            dispatcher = Mock(side_effect=RuntimeError("connection ended after send"))
            result = self.execute(root, base, dispatcher)

            self.assertEqual(result["effect_state"], "DISPATCH_UNCERTAIN")
            self.assertEqual(result["reason_codes"], ["DISPATCH_UNCERTAIN"])
            self.assertEqual(inspect_effect(root, "publish-release")["state"], "DISPATCH_UNCERTAIN")
            dispatcher.assert_called_once()

    def test_blind_retry_of_ambiguous_effect_is_rejected_without_dispatch(self):
        with repository() as (root, base):
            first = Mock(side_effect=RuntimeError("ambiguous"))
            self.execute(root, base, first)
            retry_dispatcher = Mock()

            result = self.execute(root, base, retry_dispatcher)

            self.assertEqual(result["guard_result"], "BLOCK")
            self.assertEqual(result["reason_codes"], ["BLIND_RETRY_BLOCKED"])
            self.assertFalse(result["retry_safety"]["safe"])
            retry_dispatcher.assert_not_called()

    def test_new_effect_id_cannot_bypass_ambiguous_exact_effect_identity(self):
        with repository() as (root, base):
            self.execute(root, base, Mock(side_effect=RuntimeError("ambiguous")))
            same_effect = intent(effect_id="renamed-attempt")
            dispatcher = Mock()

            result = self.execute(root, base, dispatcher, intent=same_effect)

            self.assertEqual(result["reason_codes"], ["EFFECT_INTENT_MISMATCH"])
            self.assertEqual(result["effect_state"], "DISPATCH_UNCERTAIN")
            self.assertEqual(len(list_effects(root)), 1)
            self.assertEqual(
                result["retry_safety"],
                {"safe": False, "reason_code": "EXACT_INTENT_MISMATCH"},
            )
            dispatcher.assert_not_called()

    def test_changed_idempotency_key_cannot_disguise_same_ambiguous_effect(self):
        with repository() as (root, base):
            first_intent = intent(effect_id="first-key", idempotent=True)
            self.execute(
                root, base, Mock(side_effect=RuntimeError("ambiguous")),
                intent=first_intent,
            )
            changed_key = intent(effect_id="changed-key", idempotent=True)
            changed_key["idempotency_key"] = "release-request-002"
            dispatcher = Mock()

            result = self.execute(root, base, dispatcher, intent=changed_key)

            self.assertEqual(result["reason_codes"], ["EFFECT_INTENT_MISMATCH"])
            self.assertEqual(len(list_effects(root)), 1)
            self.assertEqual(
                result["retry_safety"],
                {"safe": False, "reason_code": "EXACT_INTENT_MISMATCH"},
            )
            dispatcher.assert_not_called()

    def test_free_form_no_effect_reconciliation_fails_closed(self):
        with repository() as (root, base):
            self.execute(root, base, Mock(side_effect=RuntimeError("ambiguous")))

            with self.assertRaisesRegex(EffectSafetyError, "trusted verifier"):
                reconcile_effect(
                    root,
                    "publish-release",
                    outcome="NO_EFFECT_CONFIRMED",
                    evidence="trust me",
                )

            self.assertEqual(
                effect_retry_safety(root, "publish-release"),
                {"safe": False, "reason_code": "AMBIGUOUS_DISPATCH_NO_RETRY_PROOF"},
            )

    def test_verified_no_effect_reconciliation_survives_reload(self):
        with repository() as (root, base):
            self.execute(root, base, Mock(side_effect=RuntimeError("ambiguous")))

            reconciled = verify_effect_retry_proof(
                root,
                "publish-release",
                kind="NO_EFFECT_CONFIRMED",
                verifier=lambda challenge: trusted_response(challenge),
            )

            self.assertEqual(reconciled["state"], "NO_EFFECT_CONFIRMED")
            self.assertEqual(
                effect_retry_safety(root, "publish-release"),
                {"safe": True, "reason_code": "POSITIVE_NO_EFFECT_PROOF"},
            )

    def test_self_declared_idempotency_remains_unsafe_and_is_not_auto_retried(self):
        with repository() as (root, base):
            first = Mock(side_effect=RuntimeError("ambiguous"))
            self.execute(root, base, first, intent=intent(idempotent=True))
            retry_dispatcher = Mock()

            result = self.execute(
                root, base, retry_dispatcher, intent=intent(idempotent=True),
            )

            self.assertEqual(result["reason_codes"], ["BLIND_RETRY_BLOCKED"])
            self.assertEqual(
                result["retry_safety"],
                {"safe": False, "reason_code": "AMBIGUOUS_DISPATCH_NO_RETRY_PROOF"},
            )
            retry_dispatcher.assert_not_called()

    def test_scope_block_creates_no_effect_record_and_never_dispatches(self):
        with repository() as (root, base):
            append(root / "outside.txt")
            dispatcher = Mock()

            result = self.execute(
                root, base, dispatcher, strict_paths=["app.py"],
            )

            self.assertEqual(result["guard_result"], "BLOCK")
            self.assertFalse(result["dispatched"])
            self.assertEqual(list_effects(root), [])
            dispatcher.assert_not_called()

    def test_git_drift_after_intent_leaves_prepared_and_never_dispatches(self):
        with repository() as (root, base):
            real_observer = boundary_snapshot

            def drift(observed_root: Path | str, observed_base: str) -> dict:
                append(root / "app.py", "between-check drift\n")
                return real_observer(observed_root, observed_base)

            dispatcher = Mock()
            with patch("buildos.external_effect.boundary_snapshot", side_effect=drift):
                result = self.execute(
                    root, base, dispatcher, strict_paths=["app.py"],
                )

            self.assertEqual(result["reason_codes"], ["BLOCK_STALE_STATE"])
            self.assertEqual(inspect_effect(root, "publish-release")["state"], "PREPARED")
            dispatcher.assert_not_called()

    def test_exact_prepared_effect_dispatches_once_after_git_is_fixed(self):
        with repository() as (root, base):
            real_observer = boundary_snapshot

            def drift(observed_root: Path | str, observed_base: str) -> dict:
                append(root / "app.py", "between-check drift\n")
                return real_observer(observed_root, observed_base)

            first_dispatcher = Mock()
            with patch("buildos.external_effect.boundary_snapshot", side_effect=drift):
                first = self.execute(
                    root, base, first_dispatcher, strict_paths=["app.py"],
                )
            run_git(root, "restore", "app.py")
            second_dispatcher = Mock(return_value={
                "status": "CONFIRMED",
                "reference": "provider-result-43",
                "evidence": "provider acknowledged exact request",
            })

            second = self.execute(
                root, base, second_dispatcher, strict_paths=["app.py"],
            )
            loaded = inspect_effect(root, "publish-release")

            self.assertEqual(first["reason_codes"], ["BLOCK_STALE_STATE"])
            first_dispatcher.assert_not_called()
            second_dispatcher.assert_called_once()
            self.assertTrue(second["dispatched"])
            self.assertEqual(loaded["state"], "CONFIRMED")
            self.assertEqual(loaded["dispatch_count"], 1)

    def test_prepared_effect_with_changed_exact_intent_fails_closed(self):
        for field, value in (
            ("request_digest", hashlib.sha256(b"different request").hexdigest()),
            ("target", "provider://account/other-release"),
            ("operation", "delete"),
        ):
            with self.subTest(field=field), repository() as (root, base):
                real_observer = boundary_snapshot

                def drift(observed_root: Path | str, observed_base: str) -> dict:
                    append(root / "app.py", "between-check drift\n")
                    return real_observer(observed_root, observed_base)

                with patch("buildos.external_effect.boundary_snapshot", side_effect=drift):
                    self.execute(root, base, Mock(), strict_paths=["app.py"])
                run_git(root, "restore", "app.py")
                changed = intent()
                changed[field] = value
                dispatcher = Mock()

                result = self.execute(
                    root, base, dispatcher, intent=changed, strict_paths=["app.py"],
                )

                self.assertEqual(result["guard_result"], "BLOCK")
                self.assertEqual(result["reason_codes"], ["EFFECT_INTENT_MISMATCH"])
                dispatcher.assert_not_called()
                self.assertEqual(
                    inspect_effect(root, "publish-release")["state"], "PREPARED",
                )

    def test_provider_can_report_definite_non_dispatch(self):
        with repository() as (root, base):
            result = self.execute(
                root,
                base,
                lambda _: {
                    "status": "NOT_DISPATCHED",
                    "reference": None,
                    "evidence": "adapter failed before provider transport",
                },
            )

            self.assertEqual(result["effect_state"], "NOT_DISPATCHED")
            self.assertEqual(
                effect_retry_safety(root, "publish-release"),
                {"safe": True, "reason_code": "POSITIVE_NO_EFFECT_PROOF"},
            )


if __name__ == "__main__":
    unittest.main()
