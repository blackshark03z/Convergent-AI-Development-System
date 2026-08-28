from __future__ import annotations

import hashlib
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from buildos import effect_store
from buildos.effect_safety import (
    EffectSafetyError,
    mark_dispatch_uncertain,
    prepare,
    reconcile,
    retry_safety,
)
from buildos.external_effect import (
    effect_retry_safety,
    execute_external_effect,
    inspect_effect,
    list_effects,
    reconcile_effect,
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


class EffectSafetyModelTests(unittest.TestCase):
    def test_ambiguous_dispatch_is_not_retry_safe_without_positive_proof(self):
        record = mark_dispatch_uncertain(prepare(intent()))
        self.assertEqual(record["state"], "DISPATCH_UNCERTAIN")
        self.assertEqual(
            retry_safety(record),
            {"safe": False, "reason_code": "AMBIGUOUS_DISPATCH_NO_RETRY_PROOF"},
        )

    def test_exact_provider_idempotency_makes_ambiguous_retry_considerable(self):
        record = mark_dispatch_uncertain(prepare(intent(idempotent=True)))
        self.assertEqual(
            retry_safety(record),
            {"safe": True, "reason_code": "EXACT_PROVIDER_IDEMPOTENCY"},
        )

    def test_positive_no_effect_reconciliation_makes_retry_considerable(self):
        record = mark_dispatch_uncertain(prepare(intent()))
        resolved = reconcile(
            record,
            outcome="NO_EFFECT_CONFIRMED",
            evidence="canonical provider lookup proves target absent",
        )
        self.assertEqual(resolved["state"], "NO_EFFECT_CONFIRMED")
        self.assertEqual(
            retry_safety(resolved),
            {"safe": True, "reason_code": "POSITIVE_NO_EFFECT_PROOF"},
        )

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

            self.assertEqual(result["reason_codes"], ["BLIND_RETRY_BLOCKED"])
            self.assertEqual(result["effect_state"], "DISPATCH_UNCERTAIN")
            self.assertEqual(len(list_effects(root)), 1)
            dispatcher.assert_not_called()

    def test_positive_no_effect_reconciliation_survives_reload(self):
        with repository() as (root, base):
            self.execute(root, base, Mock(side_effect=RuntimeError("ambiguous")))

            reconciled = reconcile_effect(
                root,
                "publish-release",
                outcome="NO_EFFECT_CONFIRMED",
                evidence="canonical provider search proves release absent",
            )

            self.assertEqual(reconciled["state"], "NO_EFFECT_CONFIRMED")
            self.assertEqual(
                effect_retry_safety(root, "publish-release"),
                {"safe": True, "reason_code": "POSITIVE_NO_EFFECT_PROOF"},
            )

    def test_exact_idempotent_ambiguity_is_reported_safe_but_not_auto_retried(self):
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
                {"safe": True, "reason_code": "EXACT_PROVIDER_IDEMPOTENCY"},
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
