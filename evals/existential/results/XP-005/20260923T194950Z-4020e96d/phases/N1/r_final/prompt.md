You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-005 Reasoning Lead Prompt - N1

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

Use ordinary product/developer documentation, existing tests and normal engineering conventions available in the neutral repository. Do not create a custom process/framework.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.



IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** A lost response or uncertain transport state leaves the original consequential task attributable to the initiating phone or client. The system reconciles that task before deciding whether any effect can be dispatched again.

**Acceptance:**

- A retry of the same request, including after restart or concurrent delivery, resumes or reports the same durable task and effect lineage. It does not create a second consequential effect.
- Reusing a request identity with a different material intent or target is rejected. A distinct, intentional task has separate lineage; it cannot take over an unresolved task or inherit its partial effects.
- If a submission may have produced a partial effect, reconciliation uses evidence tied to the exact task and remote or provider identity. Confirmed effects are retained and only unfinished steps may proceed.
- An uncertain outcome remains `RECONCILE_REQUIRED` or equivalent until there is positive evidence that redispatch is safe. Result ordering, timing, and absence of a local response are insufficient evidence.
- Local/provider fixture tests cover response loss, restart, duplicate delivery, partial success, and a competing request. No live consequential submission is used.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: The terminal-state change does not satisfy the handoff. At the consequential submission entry point, persist an initiating client’s stable request identity with its material intent and owning operation. Repeated delivery, including after restart and concurrently, must return or resume that lineage without a second dispatch; reuse of the identity for different intent or target must fail. A distinct request must not take over unresolved effects.

Reconcile partial or uncertain effects using evidence attributable to that exact operation and remote identity. Title matches, result order, timing, or a missing response cannot establish success or justify redispatch; leave the effect `RECONCILE_REQUIRED` when attribution is insufficient. Add local fixture tests for response loss, restart, concurrent duplicates, partial success, and a competing request. No live submission.

I completion report:
**Implemented:** `finish_operation` now treats a repeated request to finish an operation in the same terminal state as idempotent. It returns the existing operation record, allowing duplicate completion after response loss without reactivating the task. A request to change an already terminal operation to a different state still fails.

**Checks:** `python -m pytest tests/test_publishing.py -q` passed: 13 tests.

**Evidence and limits:** The fixture suite covers upload response loss across restart, ambiguous thumbnail outcomes across restart, and reconciliation of an observed existing upload without redispatch. I did not add coverage for stable client request identities or concurrent duplicate delivery. A concurrent fixture attempt exposed an unresolved race while calls reconcile the thumbnail effect; I removed that test rather than claim concurrent delivery is handled. The service currently relies on the persisted operation and package/channel identity, not an explicit client-supplied request ID. No live submission or external provider was used.
Repair report:
I added durable publish request binding and an atomic guard against duplicate upload dispatch. I have **not** finished the repair: exact-task evidence checks, competing-request and partial-success fixture coverage, and the requested deterministic checks remain incomplete. The candidate is not ready for review; I can continue the implementation if you want.

Candidate tree: ca64d16d8f469e8c563ea03bddbfdfa3352ba080
Candidate status:
M  multiple_automation/publishing.py
M  multiple_automation/store.py
Candidate diff:
diff --git a/multiple_automation/publishing.py b/multiple_automation/publishing.py
index 11c520b..1b9548b 100644
--- a/multiple_automation/publishing.py
+++ b/multiple_automation/publishing.py
@@ -171,6 +171,7 @@ class PrivatePublishService:
         *,
         expected_remote_channel_id: str | None = None,
         expected_package_digest: str | None = None,
+        request_id: str | None = None,
     ) -> PublishResult:
         workspace = self.store.get_workspace(workspace_id)
         local_channel_id = workspace.get("youtube_channel_id")
@@ -199,6 +200,19 @@ class PrivatePublishService:
             raise InvalidTransitionError("sealed ContentPackage operation is not PUBLISH_PRIVATE")
 
         target = f"youtube-channel:{remote_channel_id}:package:{package.package_digest}"
+        self.store.bind_publish_request(
+            request_id or operation.operation_id,
+            workspace_id,
+            operation.operation_id,
+            {
+                "workspace_id": workspace_id,
+                "operation_id": operation.operation_id,
+                "remote_channel_id": remote_channel_id,
+                "content_package_id": package.content_package_id,
+                "package_digest": package.package_digest,
+                "target_identity": target,
+            },
+        )
         effect = next(
             (
                 item
@@ -296,7 +310,16 @@ class PrivatePublishService:
             )
 
         # Persist dispatch-uncertain lineage before crossing the external boundary.
-        self.store.mark_effect_dispatched(effect.effect_id)
+        try:
+            self.store.mark_effect_dispatched(effect.effect_id)
+        except InvalidTransitionError:
+            return PublishResult(
+                "RECONCILE_REQUIRED",
+                operation.operation_id,
+                workspace_id,
+                effect.remote_id,
+                "another delivery owns or has dispatched this upload; reconcile before retry",
+            )
         try:
             self.adapter.dispatch_private_upload(remote_channel_id, package)
         except Exception:
diff --git a/multiple_automation/store.py b/multiple_automation/store.py
index e0df09f..ccd52ab 100644
--- a/multiple_automation/store.py
+++ b/multiple_automation/store.py
@@ -172,6 +172,14 @@ class SQLiteProductStore:
                     operation_id TEXT NOT NULL UNIQUE REFERENCES operations(operation_id)
                 );
 
+                CREATE TABLE IF NOT EXISTS publish_requests (
+                    request_id TEXT PRIMARY KEY,
+                    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id),
+                    operation_id TEXT NOT NULL REFERENCES operations(operation_id),
+                    intent_digest TEXT NOT NULL,
+                    created_at TEXT NOT NULL
+                );
+
                 CREATE TABLE IF NOT EXISTS external_effects (
                     effect_id TEXT PRIMARY KEY,
                     operation_id TEXT NOT NULL REFERENCES operations(operation_id),
@@ -805,6 +813,28 @@ class SQLiteProductStore:
             )
         return self.get_operation(operation_id)
 
+    def bind_publish_request(self, request_id: str, workspace_id: str, operation_id: str, intent: dict[str, Any]) -> OperationRecord:
+        request_id = str(request_id or "").strip()
+        if not request_id:
+            raise InvalidTransitionError("stable client request_id is required for publish")
+        digest = intent_digest(intent)
+        with self._transaction() as db:
+            operation = self._require_row(db, "operations", "operation_id", operation_id)
+            if operation["workspace_id"] != workspace_id:
+                raise InvalidTransitionError("publish request operation belongs to another Workspace")
+            existing = db.execute("SELECT * FROM publish_requests WHERE request_id=?", (request_id,)).fetchone()
+            if existing:
+                if existing["intent_digest"] != digest:
+                    raise InvalidTransitionError("request identity was reused for a different publish intent or target")
+                if existing["operation_id"] != operation_id:
+                    return self._operation_from_row(self._require_row(db, "operations", "operation_id", existing["operation_id"]))
+                return self._operation_from_row(operation)
+            owner = db.execute("SELECT request_id, intent_digest FROM publish_requests WHERE operation_id=?", (operation_id,)).fetchone()
+            if owner:
+                raise InvalidTransitionError("active publish operation is already owned by another client request")
+            db.execute("INSERT INTO publish_requests VALUES (?, ?, ?, ?, ?)", (request_id, workspace_id, operation_id, digest, _now()))
+        return self.get_operation(operation_id)
+
     def prepare_effect(
         self,
         operation_id: str,
@@ -824,6 +854,14 @@ class SQLiteProductStore:
             ).fetchone()
             if not active or operation["terminal_at"] is not None:
                 raise InvalidTransitionError("external effect requires a nonterminal active owning Operation")
+            existing = db.execute(
+                "SELECT * FROM external_effects WHERE operation_id=? AND effect_type=? AND target_identity=?",
+                (operation_id, effect_type, target_identity),
+            ).fetchone()
+            if existing:
+                if existing["intent_digest"] != digest:
+                    raise InvalidTransitionError("effect target was reused with different material intent")
+                return self._effect_from_row(existing)
             db.execute(
                 """INSERT INTO external_effects(
                     effect_id, operation_id, workspace_id, effect_type, target_identity,
@@ -1115,6 +1153,8 @@ class SQLiteProductStore:
         with self._transaction() as db:
             operation = self._require_row(db, "operations", "operation_id", operation_id)
             if operation["terminal_at"] is not None:
+                if operation["state"] == target:
+                    return self._operation_from_row(operation)
                 raise InvalidTransitionError("terminal Operation is historical and cannot reactivate")
             active = db.execute(
                 "SELECT workspace_id FROM workspace_active_operations WHERE operation_id=?",

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
