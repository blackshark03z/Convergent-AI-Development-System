You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-005 Reasoning Lead Prompt - CCURRENT

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

Apply current Thin-CADS semantics relevant to this bounded Goal: reconstruct relevant product reality; keep Goal/journey authoritative; resolve only material design uncertainty; prefer reuse/fix over new machinery; require representative product-level evidence before READY; bind evidence to candidate; preserve consequence boundaries and exact ownership. Use the fast path.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.



IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** A consequential submission remains owned by the initiating phone or client and its original intended task when the response is lost or partial effects may have occurred. Recovery reconciles that submission before deciding whether any further dispatch is safe.

**Acceptance:**

- Persist the initiating client, stable task intent, owning operation, and effect lineage before dispatch. A retry of the same intended task resumes that lineage and cannot create a duplicate consequential effect.
- A changed intent presented as the same retry is rejected. An intentional new or competing task has distinct identity and cannot take over or bypass an unresolved submission.
- Reconcile each possibly completed side effect using evidence tied to the exact task and target. Do not attribute an unrelated result by recency or ordering. If evidence cannot establish the outcome or prove a retry safe, retain a visible unresolved state and do not redispatch.
- Demonstrate these outcomes through the product submission path with local/provider fixtures covering lost responses, partial success, restart, duplicate and competing submissions, and unrelated or reordered provider results. Bind the evidence to the candidate revision. No live consequential submission.

OWNER_INPUT_REQUIRED: no

I completion report:
Implemented exact-task reconciliation in [publishing.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/CCURRENT/multiple_automation/publishing.py) and added unrelated-result coverage in [test_publishing.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/CCURRENT/tests/test_publishing.py).

A provider match now counts only when it identifies the sealed package digest and exact channel/package target. Uncertain or mismatched observations leave the effect visibly unresolved and block dispatch. The local fixture suite passed: `14 passed`; `git diff --check` passed. The tested candidate is based on revision `191739c0efbf9f3086043fa9bcae71bbf1ee3f1f`.

The added fixture covers an unrelated, reordered provider result. Existing publishing fixtures cover success, preexisting matches, dispatch loss/restart, and thumbnail recovery. I did not verify initiating-client identity persistence, competing-client submissions, or a live provider’s ability to return exact task evidence; no live submission was attempted. I do not claim Product Acceptance.

Candidate tree: 5938296fa038ee2ad1452e9db70652303a4a91e7
Candidate status:
M  multiple_automation/publishing.py
M  tests/test_publishing.py
Candidate diff:
diff --git a/multiple_automation/publishing.py b/multiple_automation/publishing.py
index 11c520b..ae57c1e 100644
--- a/multiple_automation/publishing.py
+++ b/multiple_automation/publishing.py
@@ -15,6 +15,8 @@ class PublishObservation:
     remote_video_id: str | None = None
     visibility: str | None = None
     evidence: dict[str, Any] | None = None
+    task_digest: str | None = None
+    target_identity: str | None = None
 
     @property
     def confirmed_private(self) -> bool:
@@ -160,6 +162,17 @@ class PrivatePublishService:
     EFFECT_TYPE = "youtube.video.upload"
     THUMBNAIL_EFFECT_TYPE = "youtube.video.thumbnail"
 
+    @staticmethod
+    def _is_exact_match(observation: PublishObservation, package: SealedContentPackage,
+                        remote_channel_id: str) -> bool:
+        """Require provider evidence to name this sealed task and exact target."""
+        expected_target = f"youtube-channel:{remote_channel_id}:package:{package.package_digest}"
+        return (
+            observation.confirmed_private
+            and observation.task_digest == package.package_digest
+            and observation.target_identity == expected_target
+        )
+
     def __init__(self, store: SQLiteProductStore, adapter: PublishAdapter):
         self.store = store
         self.adapter = adapter
@@ -213,7 +226,7 @@ class PrivatePublishService:
             succeeded_remote_video_id = str(effect.remote_id or "").strip()
             if not succeeded_remote_video_id:
                 raise InvalidTransitionError("succeeded upload effect is missing its exact remote video identity")
-            if not observed.confirmed_private:
+            if not self._is_exact_match(observed, package, remote_channel_id):
                 return PublishResult(
                     "RECONCILE_REQUIRED",
                     operation.operation_id,
@@ -237,7 +250,7 @@ class PrivatePublishService:
                 package=package,
             )
 
-        if observed.confirmed_private:
+        if self._is_exact_match(observed, package, remote_channel_id):
             if effect is None:
                 effect = self.store.prepare_effect(
                     operation.operation_id,
@@ -281,6 +294,26 @@ class PrivatePublishService:
                 },
             )
 
+        # Only an affirmative, exact absence permits a first dispatch. A title
+        # match for another task (or an inconclusive provider read) is not proof
+        # that this task is absent, even when no effect row existed yet.
+        if observed.state != "ABSENT":
+            if effect.state == EffectState.PREPARING.value:
+                effect = self.store.mark_effect_reconcile_required(
+                    effect.effect_id,
+                    evidence={
+                        "reason": "provider observation did not prove exact task absence",
+                        "observation": observed.evidence or {},
+                    },
+                )
+            return PublishResult(
+                "RECONCILE_REQUIRED",
+                operation.operation_id,
+                workspace_id,
+                effect.remote_id,
+                "provider evidence is not exact; keep unresolved and do not dispatch",
+            )
+
         if effect.state != EffectState.PREPARING.value:
             if effect.state != EffectState.RECONCILE_REQUIRED.value:
                 effect = self.store.mark_effect_reconcile_required(
@@ -313,7 +346,7 @@ class PrivatePublishService:
             )
 
         refreshed = self.adapter.observe_private_upload(remote_channel_id, package)
-        if not refreshed.confirmed_private:
+        if not self._is_exact_match(refreshed, package, remote_channel_id):
             self.store.mark_effect_reconcile_required(
                 effect.effect_id,
                 evidence=refreshed.evidence or {"reason": "post_dispatch_readback_not_confirmed"},
diff --git a/tests/test_publishing.py b/tests/test_publishing.py
index dda4f0e..fd58299 100644
--- a/tests/test_publishing.py
+++ b/tests/test_publishing.py
@@ -40,7 +40,19 @@ class FakePublishAdapter:
         self.raise_on_thumbnail_dispatch = False
 
     def observe_private_upload(self, remote_channel_id, package):
-        return self.observation
+        observation = self.observation
+        if observation.state == "MATCHED" and observation.task_digest is None:
+            return PublishObservation(
+                observation.state,
+                remote_video_id=observation.remote_video_id,
+                visibility=observation.visibility,
+                evidence=observation.evidence,
+                task_digest=package.package_digest,
+                target_identity=(
+                    f"youtube-channel:{remote_channel_id}:package:{package.package_digest}"
+                ),
+            )
+        return observation
 
     def dispatch_private_upload(self, remote_channel_id, package):
         self.dispatch_count += 1
@@ -252,6 +264,23 @@ def test_preexisting_private_match_succeeds_without_current_dispatch(tmp_path: P
     assert store.get_operation(op.operation_id).terminal_at is not None
 
 
+def test_unrelated_or_reordered_provider_match_cannot_be_attributed(tmp_path: Path) -> None:
+    store, ws, op, sealed = _ready_store(tmp_path)
+    adapter = FakePublishAdapter()
+    adapter.observation = PublishObservation(
+        "MATCHED", remote_video_id="newest-unrelated-video", visibility="PRIVATE",
+        evidence={"source": "provider-list", "position": 0},
+        task_digest="different-task-digest",
+        target_identity="youtube-channel:UC_OTHER:package:other-package",
+    )
+
+    result = PrivatePublishService(store, adapter).publish(ws, sealed.content_package_id)
+
+    assert result.status == "RECONCILE_REQUIRED"
+    assert adapter.dispatch_count == 0
+    assert store.list_effects(op.operation_id)[0].state == "RECONCILE_REQUIRED"
+
+
 def test_dispatch_exception_never_blindly_redispatches_after_restart(tmp_path: Path) -> None:
     store, ws, op, sealed = _ready_store(tmp_path)
     adapter = FakePublishAdapter()

Return exactly READY or REPAIR: followed by one bounded repair brief. If no safe repair is possible, return NOT_READY with a reason.
