# XP-005 Common Implementer Prompt

You are the implementation role (I) for a controlled benchmark. You receive a
disposable neutral Multiple Automation snapshot and an Implementation Brief from
R. Implement the brief using the cheapest coherent technical path you judge
appropriate.

Rules:
- inspect the assigned repository as needed and own implementation details;
- keep changes scoped to the brief and run relevant deterministic local checks;
- never call live consequential submission, paid/external providers or production runtime;
- use only local/provider fixtures for effects;
- do not search for historical/reference implementations, sibling workspaces,
  results or hidden benchmark tests;
- do not weaken tests/acceptance surfaces to make the candidate pass;
- do not cross external or irreversible effect boundaries absent from the brief;
- decide ordinary implementation choices yourself; report a genuinely missing
  material product preference or authority decision rather than inventing it.

When finished, report exact files/behavior changed, checks actually run and
their results, product-level evidence observed, known limitations/untested
surfaces, and material assumptions. Do not claim Product Acceptance. Your output
is a candidate for R review and later hidden evaluation.



Original IMPLEMENTATION_BRIEF:
IMPLEMENTATION_BRIEF

**Outcome:** An uncertain phone/client submission remains tied to its original initiating client, task, and consequential effect. Reconcile that submission before deciding whether any dispatch may occur.

**Acceptance:**

- A retry of the same intended task resolves to the original task and effect, including after transport loss or restart. It does not create a second consequential effect or transfer ownership to another client.
- A submission with changed intent under the same retry identity is rejected. An explicitly new task receives separate identity, but cannot dispatch a competing effect while the original effect is unresolved.
- Reconciliation uses evidence attributable to the exact submission. Confirmed partial effects are retained and only unfinished work may proceed. If absence or idempotent retry is positively established, redispatch may follow the existing policy. If attribution or outcome remains uncertain, the system reports reconciliation required and dispatches nothing.
- Local/provider fixture tests cover lost response after dispatch, partial success, repeated retry, changed intent, competing new task, and ambiguous results. No test uses newest/first/last result or timing as proof of attribution.

**Effects / Authority:** Implementation and fixture testing are authorized. Live consequential submission is forbidden.

OWNER_INPUT_REQUIRED: no

Your previous completion report:
Implemented exact-effect reconciliation for phone and OTP submissions.

- [eligibility_phone.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CMIN/multiple_automation/eligibility_phone.py) now closes an uncertain effect only when reconciliation evidence matches its effect ID, target identity, and submission ID. Effect lookup also requires an exact target match.
- [raw_cdp.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CMIN/multiple_automation/adapters/raw_cdp.py) passes the expected effect identity into reconciliation. Its current page-state observations remain unattributed, so uncertain effects stay `RECONCILE_REQUIRED`.
- Added fixture coverage for lost response across restart, generic accepted-but-unattributed evidence, and exact matching evidence. Updated runtime adapter calls in the tests.

**Checks:** `python -m unittest tests.test_eligibility_phone tests.test_runtime_adapters` passed (11 tests). `git diff --check` passed.

**Observed behavior:** An uncertain phone submission is not repeated after restart. A generic accepted screen state does not resolve it; fixture evidence tied to the exact submission does.

**Limitations:** The current browser adapter cannot produce exact-submission evidence, so it will require reconciliation for uncertain phone or OTP outcomes. The brief’s broader changed-intent and competing-new-task cases are not implemented for a separate client retry identity; this change covers the existing phone verification operation/effect flow. No live or external effects were used.

Current candidate tree: 2204788e113292172b2d2298cec16e013182e355
Current diff:
diff --git a/multiple_automation/adapters/raw_cdp.py b/multiple_automation/adapters/raw_cdp.py
index 2b12e7f..721b13e 100644
--- a/multiple_automation/adapters/raw_cdp.py
+++ b/multiple_automation/adapters/raw_cdp.py
@@ -520,7 +520,9 @@ class RawCDPPhoneUIAdapter:
         result = self.runner.run("VERIFY_SUBMIT_PHONE", PHONE_NUMBER=phone_number, CHANNEL_ID=getattr(self, "remote_channel_id", ""))
         return str(result.get("state") or "UNKNOWN")
 
-    def reconcile_phone_submission(self) -> str:
+    def reconcile_phone_submission(self, effect_id: str, target_identity: str) -> str:
+        # The visible form state carries no submission identity. The orchestration
+        # layer treats this legacy state as unattributed and keeps the effect open.
         result = self.runner.run("VERIFY_RECONCILE_PHONE", CHANNEL_ID=getattr(self, "remote_channel_id", ""))
         return str(result.get("state") or "UNKNOWN")
 
@@ -528,7 +530,8 @@ class RawCDPPhoneUIAdapter:
         result = self.runner.run("VERIFY_SUBMIT_OTP", OTP_CODE=code, CHANNEL_ID=getattr(self, "remote_channel_id", ""))
         return str(result.get("state") or "UNKNOWN")
 
-    def reconcile_otp_submission(self) -> str:
+    def reconcile_otp_submission(self, effect_id: str, target_identity: str) -> str:
+        # A verified page state alone cannot prove which OTP submission caused it.
         result = self.runner.run("VERIFY_RECONCILE_OTP", CHANNEL_ID=getattr(self, "remote_channel_id", ""))
         return str(result.get("state") or "UNKNOWN")
 
diff --git a/multiple_automation/eligibility_phone.py b/multiple_automation/eligibility_phone.py
index d137d20..6897103 100644
--- a/multiple_automation/eligibility_phone.py
+++ b/multiple_automation/eligibility_phone.py
@@ -45,9 +45,9 @@ class PhoneProviderAdapter(Protocol):
 class PhoneVerificationUIAdapter(Protocol):
     def observe_eligibility(self, remote_channel_id: str) -> EligibilityObservation: ...
     def submit_phone(self, phone_number: str) -> str: ...
-    def reconcile_phone_submission(self) -> str: ...
+    def reconcile_phone_submission(self, effect_id: str, target_identity: str) -> Any: ...
     def submit_otp(self, code: str) -> str: ...
-    def reconcile_otp_submission(self) -> str: ...
+    def reconcile_otp_submission(self, effect_id: str, target_identity: str) -> Any: ...
 
 
 @dataclass(frozen=True)
@@ -352,9 +352,9 @@ class EligibilityPhoneService:
         if effect.state == EffectState.SUCCEEDED.value:
             return None
         if effect.state != EffectState.PREPARING.value:
-            reconciled = self.ui.reconcile_phone_submission()
-            if reconciled == "ACCEPTED":
-                self.store.mark_effect_succeeded(effect.effect_id, evidence={"reconciled": True})
+            reconciled = self.ui.reconcile_phone_submission(effect.effect_id, effect.target_identity)
+            if self._attributed_reconciliation(reconciled, effect, "ACCEPTED"):
+                self.store.mark_effect_succeeded(effect.effect_id, evidence=reconciled)
                 self.store.update_phone_lease_state(lease_ref, "WAITING_FOR_OTP")
                 return None
             if reconciled == "NEEDS_OPERATOR":
@@ -414,9 +414,9 @@ class EligibilityPhoneService:
         if effect.state == EffectState.SUCCEEDED.value:
             return None
         if effect.state != EffectState.PREPARING.value:
-            reconciled = self.ui.reconcile_otp_submission()
-            if reconciled == "VERIFIED":
-                self.store.mark_effect_succeeded(effect.effect_id, evidence={"reconciled": True})
+            reconciled = self.ui.reconcile_otp_submission(effect.effect_id, effect.target_identity)
+            if self._attributed_reconciliation(reconciled, effect, "VERIFIED"):
+                self.store.mark_effect_succeeded(effect.effect_id, evidence=reconciled)
                 return None
             if reconciled == "NEEDS_OPERATOR":
                 self.store.mark_effect_needs_operator(effect.effect_id, evidence={"reconciled": True})
@@ -451,11 +451,31 @@ class EligibilityPhoneService:
         )
 
     def _effect_for(self, operation_id: str, effect_type: str, lease_ref: str):
+        target = (
+            f"google-phone-submit:{lease_ref}"
+            if effect_type == "google.phone.submit"
+            else f"google-otp-submit:{lease_ref}"
+        )
         return next(
             (
                 effect
                 for effect in self.store.list_effects(operation_id)
-                if effect.effect_type == effect_type and lease_ref in effect.target_identity
+                if effect.effect_type == effect_type and effect.target_identity == target
             ),
             None,
         )
+
+    @staticmethod
+    def _attributed_reconciliation(result: Any, effect: Any, state: str) -> bool:
+        """Only accept a positive result cryptographically/structurally bound to this effect.
+
+        Legacy adapters return a bare state string from the current browser screen. That
+        state is not attributable to a particular submission and must not close an effect.
+        """
+        return (
+            isinstance(result, dict)
+            and result.get("state") == state
+            and result.get("effect_id") == effect.effect_id
+            and result.get("target_identity") == effect.target_identity
+            and result.get("submission_id") == effect.effect_id
+        )
diff --git a/tests/test_eligibility_phone.py b/tests/test_eligibility_phone.py
index ee545ce..5d0f297 100644
--- a/tests/test_eligibility_phone.py
+++ b/tests/test_eligibility_phone.py
@@ -76,6 +76,7 @@ class FakeUI:
         self.otp_outcome = "VERIFIED"
         self.phone_submits = 0
         self.otp_submits = 0
+        self.phone_reconcile_result = "UNKNOWN"
 
     def observe_eligibility(self, remote_channel_id: str) -> EligibilityObservation:
         return EligibilityObservation(self.required, not self.required, f"token-{self.required}")
@@ -84,8 +85,10 @@ class FakeUI:
         self.phone_submits += 1
         return self.phone_outcome
 
-    def reconcile_phone_submission(self) -> str:
-        return "UNKNOWN"
+    def reconcile_phone_submission(self, effect_id: str, target_identity: str) -> str:
+        if callable(self.phone_reconcile_result):
+            return self.phone_reconcile_result(effect_id, target_identity)
+        return self.phone_reconcile_result
 
     def submit_otp(self, code: str) -> str:
         self.otp_submits += 1
@@ -93,7 +96,7 @@ class FakeUI:
             self.required = False
         return self.otp_outcome
 
-    def reconcile_otp_submission(self) -> str:
+    def reconcile_otp_submission(self, effect_id: str, target_identity: str) -> str:
         return "UNKNOWN"
 
 
@@ -189,6 +192,37 @@ class EligibilityPhoneTests(unittest.TestCase):
         self.assertEqual("RECONCILE_REQUIRED", second.status)
         self.assertEqual(1, self.ui.phone_submits)
 
+    def test_unattributed_positive_screen_state_does_not_reconcile_phone_effect(self) -> None:
+        self.ui.phone_outcome = "UNKNOWN"
+        self.assertEqual("RECONCILE_REQUIRED", self.service.ensure_required_eligibility(self.workspace_id).status)
+        self.ui.reconcile_phone_submission = lambda effect_id, target: "ACCEPTED"
+        restarted = EligibilityPhoneService(
+            SQLiteProductStore(self.store.path), self.provider, self.ui, self.vault  # type: ignore[arg-type]
+        )
+        result = restarted.ensure_required_eligibility(self.workspace_id)
+        self.assertEqual("RECONCILE_REQUIRED", result.status)
+        self.assertEqual(1, self.ui.phone_submits)
+
+    def test_exact_submission_evidence_closes_only_its_phone_effect(self) -> None:
+        self.ui.phone_outcome = "UNKNOWN"
+        self.service.ensure_required_eligibility(self.workspace_id)
+        operation = self.store.get_active_operation(self.workspace_id)
+        effect = next(e for e in self.store.list_effects(operation.operation_id) if e.effect_type == "google.phone.submit")
+        self.ui.phone_reconcile_result = lambda effect_id, target: {
+            "state": "ACCEPTED",
+            "effect_id": effect_id,
+            "target_identity": target,
+            "submission_id": effect.effect_id,
+            "evidence_source": "fixture-exact-submission",
+        }
+        restarted = EligibilityPhoneService(
+            SQLiteProductStore(self.store.path), self.provider, self.ui, self.vault  # type: ignore[arg-type]
+        )
+        result = restarted.ensure_required_eligibility(self.workspace_id)
+        self.assertEqual("WAITING_FOR_OTP", result.status)
+        self.assertEqual("SUCCEEDED", restarted.store.get_effect(effect.effect_id).state)
+        self.assertEqual(1, self.ui.phone_submits)
+
     def test_timeout_uses_one_materially_different_sequential_replacement(self) -> None:
         first = self.service.ensure_required_eligibility(self.workspace_id)
         self.assertEqual("WAITING_FOR_OTP", first.status)
diff --git a/tests/test_runtime_adapters.py b/tests/test_runtime_adapters.py
index 80e4484..006500f 100644
--- a/tests/test_runtime_adapters.py
+++ b/tests/test_runtime_adapters.py
@@ -349,8 +349,8 @@ def test_phone_adapter_maps_operator_and_verified_states() -> None:
     second = adapter.observe_eligibility("UC_A")
     assert first.evidence_token == "NEEDS_OPERATOR"
     assert second.custom_thumbnail_enabled
-    assert adapter.reconcile_phone_submission() == "ACCEPTED"
-    assert adapter.reconcile_otp_submission() == "VERIFIED"
+    assert adapter.reconcile_phone_submission("effect-1", "target-1") == "ACCEPTED"
+    assert adapter.reconcile_otp_submission("effect-2", "target-2") == "VERIFIED"
 
 
 def test_publish_adapter_maps_exact_studio_readback() -> None:

R repair brief:
REPAIR: The candidate closes some phone and OTP effects safely, but it does not yet meet the handoff brief.

- Persist the initiating client, retry identity, and intended task before dispatch. A matching retry after transport loss or restart must resume the original operation and effects. Reject changed intent under that retry identity. Keep an explicitly new task distinct and prevent it from dispatching a competing effect while the original is unresolved.
- Reconcile **every uncertain consequential effect** before further dispatch. In particular, an ambiguous `phone.number.acquire` currently reaches `_allocate_next` again and can acquire another number. An unresolved effect must also remain visible when a later eligibility observation says the channel is eligible. Retain confirmed partial effects; proceed only with unfinished work supported by exact evidence.
- Add local fixture tests through the submission entry point for lost response, repeated retry, changed intent, competing new task, partial success, and ambiguous or mismatched evidence. Evidence must come from a record of the prior submission; echoing IDs supplied to reconciliation does not establish attribution. Keep all consequential live submissions disabled.

This is the sole repair. Work only in this disposable clone. No external or production effects. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report checks actually run and remaining limits.
