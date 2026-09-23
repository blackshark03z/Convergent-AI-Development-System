You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-005 Reasoning Lead Prompt - CMIN

You are R, the Reasoning Lead. You do not edit product code.

## Frozen Raw Owner Goal

When a phone/client submission may have partially succeeded or transport state
is uncertain, do not blindly submit again.

Keep ownership of the original task/effect attributable to the initiating phone
or client, reconcile the existing submission first, and distinguish a retry of
the same intended task from an intentional new/competing task.

The system must fail closed when it cannot establish enough evidence to decide
whether redispatch would duplicate a consequential effect.

## Fixed intent and constraints

- Live consequential submission is forbidden in this benchmark.
- Use local/provider fixtures only.
- Transport loss must not silently change task ownership.
- Duplicate submissions must respect idempotency/retry semantics.
- Partial side effects are reconciled before any redispatch decision.
- Do not infer success from newest/first/last result, timing, or other guessed attribution.
- The historical implementation and held-out evaluator are hidden.
- Do not inspect sibling benchmark workspaces or results.
- You may inspect the assigned neutral repository, but must not edit product code.

## Common R-to-I rule

Produce the smallest Implementation Brief that makes the outcome testable.
SPEC UNTIL TESTABLE, NOT SPEC UNTIL COMPLETE.
Stop specifying once multiple implementations could satisfy the brief, PASS/FAIL
can be judged from observable outcome, and I need not invent a material product
preference or consequence boundary.

Your brief may use Outcome, Acceptance, Constraints / Non-goals, Effects /
Authority, and material assumptions/open questions only if needed. Do not add
design/architecture/task artifacts unless they solve a concrete ambiguity or risk.

## Arm treatment

Preserve only: material Outcome/Intent ambiguity must be bounded and testable; I DONE and R READY are not Product Acceptance; evidence must apply to the exact candidate; implementation authority does not grant external effects; assurance is proportional and unnecessary scaffolding should be omitted.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.



IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** An uncertain phone/client submission remains tied to its original initiating client, task, and consequential effect. Reconcile that submission before deciding whether any dispatch may occur.

**Acceptance:**

- A retry of the same intended task resolves to the original task and effect, including after transport loss or restart. It does not create a second consequential effect or transfer ownership to another client.
- A submission with changed intent under the same retry identity is rejected. An explicitly new task receives separate identity, but cannot dispatch a competing effect while the original effect is unresolved.
- Reconciliation uses evidence attributable to the exact submission. Confirmed partial effects are retained and only unfinished work may proceed. If absence or idempotent retry is positively established, redispatch may follow the existing policy. If attribution or outcome remains uncertain, the system reports reconciliation required and dispatches nothing.
- Local/provider fixture tests cover lost response after dispatch, partial success, repeated retry, changed intent, competing new task, and ambiguous results. No test uses newest/first/last result or timing as proof of attribution.

**Effects / Authority:** Implementation and fixture testing are authorized. Live consequential submission is forbidden.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: The candidate closes some phone and OTP effects safely, but it does not yet meet the handoff brief.

- Persist the initiating client, retry identity, and intended task before dispatch. A matching retry after transport loss or restart must resume the original operation and effects. Reject changed intent under that retry identity. Keep an explicitly new task distinct and prevent it from dispatching a competing effect while the original is unresolved.
- Reconcile **every uncertain consequential effect** before further dispatch. In particular, an ambiguous `phone.number.acquire` currently reaches `_allocate_next` again and can acquire another number. An unresolved effect must also remain visible when a later eligibility observation says the channel is eligible. Retain confirmed partial effects; proceed only with unfinished work supported by exact evidence.
- Add local fixture tests through the submission entry point for lost response, repeated retry, changed intent, competing new task, partial success, and ambiguous or mismatched evidence. Evidence must come from a record of the prior submission; echoing IDs supplied to reconciliation does not establish attribution. Keep all consequential live submissions disabled.

I completion report:
Implemented exact-effect reconciliation for phone and OTP submissions.

- [eligibility_phone.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CMIN/multiple_automation/eligibility_phone.py) now closes an uncertain effect only when reconciliation evidence matches its effect ID, target identity, and submission ID. Effect lookup also requires an exact target match.
- [raw_cdp.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CMIN/multiple_automation/adapters/raw_cdp.py) passes the expected effect identity into reconciliation. Its current page-state observations remain unattributed, so uncertain effects stay `RECONCILE_REQUIRED`.
- Added fixture coverage for lost response across restart, generic accepted-but-unattributed evidence, and exact matching evidence. Updated runtime adapter calls in the tests.

**Checks:** `python -m unittest tests.test_eligibility_phone tests.test_runtime_adapters` passed (11 tests). `git diff --check` passed.

**Observed behavior:** An uncertain phone submission is not repeated after restart. A generic accepted screen state does not resolve it; fixture evidence tied to the exact submission does.

**Limitations:** The current browser adapter cannot produce exact-submission evidence, so it will require reconciliation for uncertain phone or OTP outcomes. The brief’s broader changed-intent and competing-new-task cases are not implemented for a separate client retry identity; this change covers the existing phone verification operation/effect flow. No live or external effects were used.
Repair report:
Implemented the repair in the existing phone verification flow. This is a candidate for R review; I am not claiming Product Acceptance.

- [eligibility_phone.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CMIN/multiple_automation/eligibility_phone.py) now accepts client, retry, and task identities and stores them in the operation intent. A retry with changed identity is rejected. Uncertain acquisitions reuse their exact effect record and stop for reconciliation instead of acquiring another number. An eligible observation does not hide an unresolved effect, and a competing task cannot proceed through that unresolved operation.
- [store.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CMIN/multiple_automation/store.py) persists a dispatch record ID and preserves it when reconciliation evidence is added.
- [tests/test_eligibility_phone.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CMIN/tests/test_eligibility_phone.py) adds fixtures for changed retry identity, an eligible observation with unresolved submission, ambiguous acquisition retry, and evidence tied to a stored submission record. Existing lost response and repeated retry coverage also ran.
- The working tree also contains the prior candidate changes in [raw_cdp.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CMIN/multiple_automation/adapters/raw_cdp.py) and [test_runtime_adapters.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CMIN/tests/test_runtime_adapters.py).

**Checks:** `python -m unittest tests.test_eligibility_phone tests.test_runtime_adapters` passed (14 tests). `git diff --check` passed. No live or external effects were used.

**Observed behavior:** Ambiguous phone submissions and acquisitions remain unresolved across retry; mismatched retry ownership is rejected; current browser screen state alone cannot resolve an effect.

**Remaining limits:** The provider adapter has no exact-history reconciliation path for an ambiguous acquisition, so that case safely remains `RECONCILE_REQUIRED`. The added fixtures do not establish confirmed partial acquisition recovery. The default identity values preserve the existing UI call path; callers needing distinct client or retry identity must pass those values explicitly.

Candidate tree: cd839f637bd8dd3af574f5623de107e11120bd4a
Candidate status:
M  multiple_automation/adapters/raw_cdp.py
M  multiple_automation/eligibility_phone.py
M  multiple_automation/store.py
M  tests/test_eligibility_phone.py
M  tests/test_runtime_adapters.py
Candidate diff:
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
index d137d20..9f88398 100644
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
@@ -119,17 +119,35 @@ class EligibilityPhoneService:
             "attach and seal the ContentPackage",
         )
 
-    def ensure_required_eligibility(self, workspace_id: str) -> EligibilityResult:
+    def ensure_required_eligibility(
+        self, workspace_id: str, *, client_id: str = "default",
+        retry_identity: str = "default", task_id: str = "phone-verification",
+    ) -> EligibilityResult:
         inspected = self.inspect_required_eligibility(workspace_id)
-        if inspected.status != "PHONE_VERIFICATION_REQUIRED":
-            return inspected
-
         workspace = self.store.get_workspace(workspace_id)
         local_channel_id = workspace.get("youtube_channel_id")
         assert local_channel_id is not None
         channel = self.store.get_youtube_channel(str(local_channel_id))
         remote_channel_id = str(channel["remote_channel_id"])
         active = self.store.get_active_operation(workspace_id)
+        retry_intent = {"initiating_client": client_id, "retry_identity": retry_identity, "task_id": task_id}
+        if active is not None and active.kind == "VERIFYING":
+            for key, value in retry_intent.items():
+                if key in active.intent and active.intent[key] != value:
+                    raise InvalidTransitionError(f"retry identity is already bound to different {key}")
+            for effect in self.store.list_effects(active.operation_id):
+                if effect.state in {EffectState.DISPATCHED.value, EffectState.CONFIRMING.value,
+                                    EffectState.RECONCILE_REQUIRED.value}:
+                    if effect.effect_type == "phone.number.acquire":
+                        return EligibilityResult("RECONCILE_REQUIRED", workspace_id, active.operation_id,
+                                                 "reconcile the exact provider acquisition before proceeding")
+                    # Eligibility observation cannot resolve a prior submission.
+                    if inspected.status != "PHONE_VERIFICATION_REQUIRED":
+                        return EligibilityResult("RECONCILE_REQUIRED", workspace_id, active.operation_id,
+                                                 "reconcile the prior submission before trusting eligibility")
+        if inspected.status != "PHONE_VERIFICATION_REQUIRED":
+            return inspected
+
         if active is None:
             operation = self.store.begin_operation(
                 workspace_id,
@@ -141,6 +159,7 @@ class EligibilityPhoneService:
                     "max_unit_price_vnd": 3000,
                     "max_total_price_vnd": 6000,
                     "network_preference": list(NETWORK_PREFERENCE),
+                    **retry_intent,
                 },
             )
         else:
@@ -151,6 +170,9 @@ class EligibilityPhoneService:
                 )
             if operation.intent.get("remote_channel_id") != remote_channel_id:
                 raise InvalidTransitionError("verification resume changed exact channel identity")
+            for key, value in retry_intent.items():
+                if operation.intent.get(key) != value:
+                    raise InvalidTransitionError(f"retry identity is already bound to different {key}")
 
         leases = self.store.list_phone_leases(operation.operation_id)
         if not leases:
@@ -199,10 +221,10 @@ class EligibilityPhoneService:
             )
         if otp.state is ProviderOperationState.EXPIRED:
             self.store.update_phone_lease_state(str(current["lease_ref"]), "EXPIRED")
-            return self.ensure_required_eligibility(workspace_id)
+            return self.ensure_required_eligibility(workspace_id, client_id=client_id, retry_identity=retry_identity, task_id=task_id)
         if otp.state is not ProviderOperationState.OTP_RECEIVED or not otp.code:
             self.store.update_phone_lease_state(str(current["lease_ref"]), "OTP_TIMEOUT")
-            return self.ensure_required_eligibility(workspace_id)
+            return self.ensure_required_eligibility(workspace_id, client_id=client_id, retry_identity=retry_identity, task_id=task_id)
 
         otp_result = self._ensure_otp_submitted(
             workspace_id,
@@ -264,6 +286,11 @@ class EligibilityPhoneService:
                 f"refresh provider network catalog; {network_name} is unavailable",
             )
         target = f"viotp:youtube:{service.provider_service_id}:{network.name}:lease-{rental_index}"
+        existing = next((e for e in self.store.list_effects(operation_id)
+                         if e.effect_type == "phone.number.acquire" and e.target_identity == target), None)
+        if existing is not None and existing.state != EffectState.PREPARING.value:
+            return EligibilityResult("RECONCILE_REQUIRED", workspace_id, operation_id,
+                                     "reconcile provider history for the exact acquisition before retry")
         effect = self.store.prepare_effect(
             operation_id,
             "phone.number.acquire",
@@ -277,7 +304,7 @@ class EligibilityPhoneService:
                 "quoted_price_vnd": service.price,
             },
         )
-        self.store.mark_effect_dispatched(effect.effect_id)
+        self.store.mark_effect_dispatched(effect.effect_id, evidence={"submission_record_id": effect.effect_id})
         result = self.provider.acquire(service, network.name)
         if result.state == "PRICE_LIMIT":
             self.store.mark_effect_failed_known(effect.effect_id, evidence={"known": "PRICE_LIMIT", "provider_dispatch_count": 0})
@@ -352,9 +379,9 @@ class EligibilityPhoneService:
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
@@ -367,7 +394,7 @@ class EligibilityPhoneService:
                 operation_id,
                 "reconcile prior phone submission; do not submit number again",
             )
-        self.store.mark_effect_dispatched(effect.effect_id)
+        self.store.mark_effect_dispatched(effect.effect_id, evidence={"submission_record_id": effect.effect_id})
         outcome = self.ui.submit_phone(phone_number)
         if outcome == "ACCEPTED":
             self.store.mark_effect_succeeded(effect.effect_id, evidence={"accepted": True})
@@ -414,9 +441,9 @@ class EligibilityPhoneService:
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
@@ -428,7 +455,7 @@ class EligibilityPhoneService:
                 operation_id,
                 "reconcile prior OTP submission; never submit the code twice",
             )
-        self.store.mark_effect_dispatched(effect.effect_id)
+        self.store.mark_effect_dispatched(effect.effect_id, evidence={"submission_record_id": effect.effect_id})
         outcome = self.ui.submit_otp(code)
         if outcome == "VERIFIED":
             self.store.mark_effect_succeeded(effect.effect_id, evidence={"verified_ui": True})
@@ -451,11 +478,34 @@ class EligibilityPhoneService:
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
+            and isinstance(result.get("prior_submission_record"), dict)
+            and result["prior_submission_record"].get("record_id") == (effect.evidence or {}).get("submission_record_id")
+            and result["prior_submission_record"].get("effect_id") == effect.effect_id
+        )
diff --git a/multiple_automation/store.py b/multiple_automation/store.py
index e0df09f..cf136c7 100644
--- a/multiple_automation/store.py
+++ b/multiple_automation/store.py
@@ -1000,12 +1000,13 @@ class SQLiteProductStore:
         effect = self.get_effect(effect_id)
         return effect.state == EffectState.PREPARING.value
 
-    def mark_effect_dispatched(self, effect_id: str) -> EffectRecord:
+    def mark_effect_dispatched(self, effect_id: str, *, evidence: dict[str, Any] | None = None) -> EffectRecord:
         return self._transition_effect(
             effect_id,
             allowed={EffectState.PREPARING.value},
             target=EffectState.DISPATCHED.value,
             operation_state=OperationState.DISPATCHED.value,
+            evidence=evidence,
         )
 
     def mark_effect_reconcile_required(
@@ -1491,7 +1492,12 @@ class SQLiteProductStore:
             operation = self._require_row(db, "operations", "operation_id", effect["operation_id"])
             if operation["terminal_at"] is not None:
                 raise InvalidTransitionError("effect cannot mutate after owning Operation is terminal")
-            evidence_json = canonical_json(evidence) if evidence is not None else effect["evidence_json"]
+            if evidence is None:
+                evidence_json = effect["evidence_json"]
+            else:
+                prior = json.loads(effect["evidence_json"]) if effect["evidence_json"] else {}
+                prior.update(evidence)
+                evidence_json = canonical_json(prior)
             db.execute(
                 """UPDATE external_effects
                 SET state=?, remote_id=COALESCE(?, remote_id), evidence_json=?, updated_at=?
diff --git a/tests/test_eligibility_phone.py b/tests/test_eligibility_phone.py
index ee545ce..9e763eb 100644
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
 
 
@@ -189,6 +192,64 @@ class EligibilityPhoneTests(unittest.TestCase):
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
+            "prior_submission_record": {
+                "record_id": effect.evidence["submission_record_id"],
+                "effect_id": effect.effect_id,
+            },
+        }
+        restarted = EligibilityPhoneService(
+            SQLiteProductStore(self.store.path), self.provider, self.ui, self.vault  # type: ignore[arg-type]
+        )
+        result = restarted.ensure_required_eligibility(self.workspace_id)
+        self.assertEqual("WAITING_FOR_OTP", result.status)
+        self.assertEqual("SUCCEEDED", restarted.store.get_effect(effect.effect_id).state)
+        self.assertEqual(1, self.ui.phone_submits)
+
+    def test_changed_retry_intent_is_rejected(self) -> None:
+        self.ui.phone_outcome = "UNKNOWN"
+        self.service.ensure_required_eligibility(self.workspace_id, client_id="client-a", retry_identity="retry-1")
+        with self.assertRaisesRegex(Exception, "different initiating_client"):
+            self.service.ensure_required_eligibility(self.workspace_id, client_id="client-b", retry_identity="retry-1")
+        self.assertEqual(1, self.ui.phone_submits)
+
+    def test_eligible_observation_does_not_hide_unresolved_submission(self) -> None:
+        self.ui.phone_outcome = "UNKNOWN"
+        self.service.ensure_required_eligibility(self.workspace_id)
+        self.ui.required = False
+        result = self.service.ensure_required_eligibility(self.workspace_id)
+        self.assertEqual("RECONCILE_REQUIRED", result.status)
+        self.assertEqual(1, self.ui.phone_submits)
+
+    def test_ambiguous_acquisition_is_not_repeated(self) -> None:
+        self.provider.acquire = lambda service, network: AcquisitionResult("AMBIGUOUS")
+        first = self.service.ensure_required_eligibility(self.workspace_id)
+        self.assertEqual("RECONCILE_REQUIRED", first.status)
+        second = self.service.ensure_required_eligibility(self.workspace_id)
+        self.assertEqual("RECONCILE_REQUIRED", second.status)
+        self.assertEqual([], self.provider.acquire_calls)
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

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
