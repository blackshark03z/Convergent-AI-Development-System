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

**Outcome:** A repeated client request remains tied to the initiating client, its original task, and its exact intended effect. An uncertain transport result triggers reconciliation before any consequential redispatch. Use the repository’s existing operation and effect lineage where possible.

**Acceptance:**

- A fixture simulates a submission that creates a partial provider or remote effect, then loses its response. A retry with the same client and request identity resumes or reports the original task; it does not create a second task or repeat the unresolved effect. This remains true after restart and for concurrent duplicate requests.
- Reconciliation attributes outcomes using exact persisted request, effect, and remote identities. Fixtures with multiple plausible results in different orders cannot cause a result to be assigned by recency, position, or timing. Confirmed partial effects are retained, and only unfinished steps may proceed.
- Redispatch occurs only with evidence that the prior effect did not happen or with a proven idempotent retry of that same effect. If evidence is insufficient, the task stays visibly unresolved and no consequential dispatch occurs.
- Reusing a request identity with changed intent, or from another client, cannot take ownership of the original task. An explicitly new task receives separate lineage; if it competes with an unresolved effect, it cannot dispatch until the conflict is resolved. A delayed retry of a completed task returns that task’s result.
- Representative evidence exercises the product submission path with local/provider fixtures and shows persisted ownership, reconciliation decisions, and dispatch counts. No live consequential submission.

OWNER_INPUT_REQUIRED: no

Your previous completion report:
Implemented an atomic dispatch claim for upload and thumbnail effects in [publishing.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CCURRENT/multiple_automation/publishing.py). If a concurrent request has already claimed an effect, the stale caller now returns `RECONCILE_REQUIRED` without dispatching it.

Checks run: `python -m pytest tests/test_publishing.py -q` passed (13 tests); `git diff --check` passed.

This is a partial candidate, not a complete implementation of the brief. The existing submit path has no persisted client/request identity, and provider observations are not shown here to prove exact request-to-remote attribution across ambiguous matches. I did not add those behaviors or a new fixture, so ownership, changed-intent protection, delayed retries, and the requested concurrent duplicate product-path evidence remain unverified. No live submission or external provider was used.

Current candidate tree: 939573cb6f3af61202981aa530d002fcb9649a4f
Current diff:
diff --git a/multiple_automation/publishing.py b/multiple_automation/publishing.py
index 11c520b..6bd3bd0 100644
--- a/multiple_automation/publishing.py
+++ b/multiple_automation/publishing.py
@@ -296,7 +296,21 @@ class PrivatePublishService:
             )
 
         # Persist dispatch-uncertain lineage before crossing the external boundary.
-        self.store.mark_effect_dispatched(effect.effect_id)
+        # The effect was read before the adapter observation. Another request may
+        # have claimed it while that observation was in flight. The SQLite
+        # transition is the dispatch claim: only the caller that atomically moves
+        # PREPARING -> DISPATCHED may cross the provider boundary.
+        try:
+            self.store.mark_effect_dispatched(effect.effect_id)
+        except InvalidTransitionError:
+            current = self.store.get_effect(effect.effect_id)
+            return PublishResult(
+                "RECONCILE_REQUIRED",
+                operation.operation_id,
+                workspace_id,
+                current.remote_id,
+                "another request claimed this upload; reconcile the original effect",
+            )
         try:
             self.adapter.dispatch_private_upload(remote_channel_id, package)
         except Exception:
@@ -462,7 +476,19 @@ class PrivatePublishService:
                 "re-observe exact video editor before thumbnail dispatch",
             )
 
-        self.store.mark_effect_dispatched(current.effect_id)
+        # Claim the thumbnail effect atomically for the same reason as upload:
+        # concurrent retries must not both act on a stale PREPARING snapshot.
+        try:
+            self.store.mark_effect_dispatched(current.effect_id)
+        except InvalidTransitionError:
+            latest = self.store.get_effect(current.effect_id)
+            return PublishResult(
+                "RECONCILE_REQUIRED",
+                operation_id,
+                workspace_id,
+                remote_video_id,
+                "another request claimed this thumbnail; reconcile the original effect",
+            )
         try:
             self.adapter.dispatch_thumbnail(
                 remote_channel_id,

R repair brief:
REPAIR: The atomic dispatch claim closes one race, but concurrent callers can still create separate `PREPARING` effects and each dispatch. The candidate also lacks persisted client/request ownership and evidence that an observed remote result belongs to the original effect.

- At the product submission boundary, persist the initiating client, request identity, intended task, and effect lineage. A retry must resolve to that task after restart or completion. Reject changed intent or a different client using the same request identity; keep an intentional new task separate and block it while a competing effect is unresolved.
- Make effect preparation and dispatch claiming safe under concurrent duplicate requests. Reconcile a partial or uncertain effect using exact persisted identities. Ambiguous observations must leave it unresolved without redispatch; confirmed partial effects must be retained.
- Provide local/provider fixture evidence through the product submission path for response loss after a partial effect, restart, concurrent duplicates, reordered plausible results, delayed completed-task retry, and changed or competing intent. Assert persisted ownership and consequential dispatch counts. No live submission.

This is the sole repair. Work only in this disposable clone. No external or production effects. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report checks actually run and remaining limits.
