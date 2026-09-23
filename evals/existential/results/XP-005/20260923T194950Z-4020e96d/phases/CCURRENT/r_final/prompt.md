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

**Outcome:** A repeated client request remains tied to the initiating client, its original task, and its exact intended effect. An uncertain transport result triggers reconciliation before any consequential redispatch. Use the repository’s existing operation and effect lineage where possible.

**Acceptance:**

- A fixture simulates a submission that creates a partial provider or remote effect, then loses its response. A retry with the same client and request identity resumes or reports the original task; it does not create a second task or repeat the unresolved effect. This remains true after restart and for concurrent duplicate requests.
- Reconciliation attributes outcomes using exact persisted request, effect, and remote identities. Fixtures with multiple plausible results in different orders cannot cause a result to be assigned by recency, position, or timing. Confirmed partial effects are retained, and only unfinished steps may proceed.
- Redispatch occurs only with evidence that the prior effect did not happen or with a proven idempotent retry of that same effect. If evidence is insufficient, the task stays visibly unresolved and no consequential dispatch occurs.
- Reusing a request identity with changed intent, or from another client, cannot take ownership of the original task. An explicitly new task receives separate lineage; if it competes with an unresolved effect, it cannot dispatch until the conflict is resolved. A delayed retry of a completed task returns that task’s result.
- Representative evidence exercises the product submission path with local/provider fixtures and shows persisted ownership, reconciliation decisions, and dispatch counts. No live consequential submission.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: The atomic dispatch claim closes one race, but concurrent callers can still create separate `PREPARING` effects and each dispatch. The candidate also lacks persisted client/request ownership and evidence that an observed remote result belongs to the original effect.

- At the product submission boundary, persist the initiating client, request identity, intended task, and effect lineage. A retry must resolve to that task after restart or completion. Reject changed intent or a different client using the same request identity; keep an intentional new task separate and block it while a competing effect is unresolved.
- Make effect preparation and dispatch claiming safe under concurrent duplicate requests. Reconcile a partial or uncertain effect using exact persisted identities. Ambiguous observations must leave it unresolved without redispatch; confirmed partial effects must be retained.
- Provide local/provider fixture evidence through the product submission path for response loss after a partial effect, restart, concurrent duplicates, reordered plausible results, delayed completed-task retry, and changed or competing intent. Assert persisted ownership and consequential dispatch counts. No live submission.

I completion report:
Implemented an atomic dispatch claim for upload and thumbnail effects in [publishing.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CCURRENT/multiple_automation/publishing.py). If a concurrent request has already claimed an effect, the stale caller now returns `RECONCILE_REQUIRED` without dispatching it.

Checks run: `python -m pytest tests/test_publishing.py -q` passed (13 tests); `git diff --check` passed.

This is a partial candidate, not a complete implementation of the brief. The existing submit path has no persisted client/request identity, and provider observations are not shown here to prove exact request-to-remote attribution across ambiguous matches. I did not add those behaviors or a new fixture, so ownership, changed-intent protection, delayed retries, and the requested concurrent duplicate product-path evidence remain unverified. No live submission or external provider was used.
Repair report:
Implemented a partial repair candidate.

- Added durable `client_id`/`request_id` ownership in [store.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CCURRENT/multiple_automation/store.py). Reusing a request ID from another client raises an identity conflict; changed intent is also rejected.
- Added request identity parameters to the publish API and controller. A delayed retry of a completed task returns its original operation and result.
- Made effect preparation reuse existing lineage for the same operation, effect type, and target.
- Added a fixture test covering successful submission, reopening the store, delayed retry, and rejection of a different client.

Checks run: `python -m pytest tests/test_publishing.py -q` passed (14 tests); `git diff --check` passed.

The fixture observed one upload dispatch across the restart and retry, and the original operation remained associated with the request. No live submission or external provider was used.

Remaining gaps: the browser UI does not yet create and resend a stable request ID; separate tasks competing for an unresolved effect are not blocked by workspace-wide lineage; and fixtures do not cover partial remote effects, ambiguous reordered observations, concurrent product submissions, or competing intent. Exact remote attribution under those cases remains unverified. This is not a complete implementation of the repair brief, and I make no Product Acceptance claim.

Candidate tree: f7b81b7885f65be363169dcf9d4026cfdf6567ea
Candidate status:
M  multiple_automation/app.py
M  multiple_automation/control_center.py
M  multiple_automation/publishing.py
M  multiple_automation/store.py
M  tests/test_publishing.py
Candidate diff:
diff --git a/multiple_automation/app.py b/multiple_automation/app.py
index 45e5d4a..1848e40 100644
--- a/multiple_automation/app.py
+++ b/multiple_automation/app.py
@@ -214,6 +214,8 @@ class ControlCenterHandler(BaseHTTPRequestHandler):
                 "publish": lambda: self.controller.publish_private(
                     workspace_id,
                     str(body.get("review_digest") or ""),
+                    client_id=str(body.get("client_id") or "control-center"),
+                    request_id=str(body.get("request_id") or "") or None,
                 ),
             }
             if action not in routes:
diff --git a/multiple_automation/control_center.py b/multiple_automation/control_center.py
index d0ce43c..90892c2 100644
--- a/multiple_automation/control_center.py
+++ b/multiple_automation/control_center.py
@@ -694,7 +694,7 @@ class ProductController:
         review = PublishReviewService(self.store).review(workspace_id)
         return {"publish_review": asdict(review), "workspace": self.workspace_overview(workspace_id)}
 
-    def publish_private(self, workspace_id: str, review_digest: str) -> dict[str, Any]:
+    def publish_private(self, workspace_id: str, review_digest: str, *, client_id: str = "control-center", request_id: str | None = None) -> dict[str, Any]:
         review = PublishReviewService(self.store).approve(workspace_id, review_digest)
         runner = self._runner_for_workspace(workspace_id)
         result = PrivatePublishService(self.store, HybridPublishAdapter(runner)).publish(
@@ -702,6 +702,8 @@ class ProductController:
             review.content_package_id,
             expected_remote_channel_id=review.remote_channel_id,
             expected_package_digest=review.package_digest,
+            client_id=client_id,
+            request_id=request_id,
         )
         return {"result": asdict(result), "workspace": self.workspace_overview(workspace_id)}
 
diff --git a/multiple_automation/publishing.py b/multiple_automation/publishing.py
index 11c520b..771bf17 100644
--- a/multiple_automation/publishing.py
+++ b/multiple_automation/publishing.py
@@ -171,6 +171,8 @@ class PrivatePublishService:
         *,
         expected_remote_channel_id: str | None = None,
         expected_package_digest: str | None = None,
+        client_id: str = "control-center",
+        request_id: str | None = None,
     ) -> PublishResult:
         workspace = self.store.get_workspace(workspace_id)
         local_channel_id = workspace.get("youtube_channel_id")
@@ -192,6 +194,23 @@ class PrivatePublishService:
             )
 
         operation = self.store.get_operation(package.operation_id)
+        if request_id:
+            operation = self.store.bind_submission_request(
+                client_id, request_id, operation.operation_id,
+                {"workspace_id": workspace_id, "content_package_id": content_package_id,
+                 "package_digest": package.package_digest, "remote_channel_id": remote_channel_id},
+            )
+            if operation.terminal_at:
+                effects = self.store.list_effects(operation.operation_id)
+                remote = next((item.remote_id for item in effects if item.effect_type == self.EFFECT_TYPE), None)
+                return PublishResult(operation.state, operation.operation_id, workspace_id, remote,
+                                     "return original completed task result")
+            if operation.operation_id != package.operation_id:
+                original = self.store.get_operation_content_package(operation.operation_id)
+                if not original:
+                    raise InvalidTransitionError("owned request task has no sealed package")
+                content_package_id = str(original["content_package_id"])
+                package = verify_sealed_content_package(self.store, content_package_id)
         active = self.store.get_active_operation(workspace_id)
         if active is None or active.operation_id != operation.operation_id:
             raise InvalidTransitionError("sealed ContentPackage must belong to the active publish operation")
@@ -296,7 +315,21 @@ class PrivatePublishService:
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
@@ -462,7 +495,19 @@ class PrivatePublishService:
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
diff --git a/multiple_automation/store.py b/multiple_automation/store.py
index e0df09f..966283d 100644
--- a/multiple_automation/store.py
+++ b/multiple_automation/store.py
@@ -187,6 +187,18 @@ class SQLiteProductStore:
                     updated_at TEXT NOT NULL
                 );
 
+                CREATE TABLE IF NOT EXISTS submission_requests (
+                    client_id TEXT NOT NULL,
+                    request_id TEXT NOT NULL,
+                    operation_id TEXT NOT NULL REFERENCES operations(operation_id),
+                    intent_digest TEXT NOT NULL,
+                    created_at TEXT NOT NULL,
+                    PRIMARY KEY(client_id, request_id)
+                );
+
+                CREATE UNIQUE INDEX IF NOT EXISTS idx_effect_lineage_unique
+                    ON external_effects(operation_id, effect_type, target_identity);
+
                 CREATE TABLE IF NOT EXISTS effect_supersessions (
                     predecessor_effect_id TEXT PRIMARY KEY REFERENCES external_effects(effect_id),
                     successor_effect_id TEXT NOT NULL UNIQUE REFERENCES external_effects(effect_id),
@@ -817,6 +829,12 @@ class SQLiteProductStore:
         snapshot = canonical_json(intent)
         digest = intent_digest(intent)
         with self._transaction() as db:
+            existing = db.execute(
+                "SELECT effect_id FROM external_effects WHERE operation_id=? AND effect_type=? AND target_identity=?",
+                (operation_id, effect_type, target_identity),
+            ).fetchone()
+            if existing:
+                return self.get_effect(existing["effect_id"])
             operation = self._require_row(db, "operations", "operation_id", operation_id)
             active = db.execute(
                 "SELECT 1 FROM workspace_active_operations WHERE operation_id=?",
@@ -848,6 +866,23 @@ class SQLiteProductStore:
             )
         return self.get_effect(effect_id)
 
+    def bind_submission_request(self, client_id: str, request_id: str, operation_id: str, intent: dict[str, Any]) -> OperationRecord:
+        client_id, request_id = str(client_id).strip(), str(request_id).strip()
+        if not client_id or not request_id:
+            raise InvalidTransitionError("client_id and request_id are required")
+        digest = intent_digest(intent)
+        now = _now()
+        with self._transaction() as db:
+            row = db.execute("SELECT * FROM submission_requests WHERE request_id=?", (request_id,)).fetchone()
+            if row:
+                if row["client_id"] != client_id or row["intent_digest"] != digest:
+                    raise IdentityConflictError("request identity is owned by another client or changed intent")
+                return self.get_operation(row["operation_id"])
+            operation = self._require_row(db, "operations", "operation_id", operation_id)
+            db.execute("INSERT INTO submission_requests VALUES (?, ?, ?, ?, ?)",
+                       (client_id, request_id, operation_id, digest, now))
+        return self.get_operation(operation_id)
+
     def prepare_approved_effect_supersession(
         self,
         *,
diff --git a/tests/test_publishing.py b/tests/test_publishing.py
index dda4f0e..af7b5a2 100644
--- a/tests/test_publishing.py
+++ b/tests/test_publishing.py
@@ -229,6 +229,31 @@ def test_success_is_independently_reconciled_before_terminal(tmp_path: Path) ->
     assert latest.state == "SUCCEEDED"
 
 
+def test_submission_request_ownership_survives_restart_and_completed_retry(tmp_path: Path) -> None:
+    store, ws, op, sealed = _ready_store(tmp_path)
+    adapter = FakePublishAdapter()
+    first = PrivatePublishService(store, adapter).publish(
+        ws, sealed.content_package_id, client_id="browser-A", request_id="req-1"
+    )
+    assert first.status == "SUCCEEDED"
+    # A fresh store instance models process restart; completion remains owned.
+    reopened = SQLiteProductStore(tmp_path / "product.db")
+    delayed = PrivatePublishService(reopened, adapter).publish(
+        ws, sealed.content_package_id, client_id="browser-A", request_id="req-1"
+    )
+    assert delayed.operation_id == op.operation_id
+    assert delayed.status == "SUCCEEDED"
+    assert adapter.dispatch_count == 1
+    try:
+        PrivatePublishService(reopened, adapter).publish(
+            ws, sealed.content_package_id, client_id="browser-B", request_id="req-1"
+        )
+    except Exception as exc:
+        assert "request identity" in str(exc)
+    else:
+        raise AssertionError("another client must not claim a persisted request")
+
+
 def test_preexisting_private_match_succeeds_without_current_dispatch(tmp_path: Path) -> None:
     store, ws, op, sealed = _ready_store(tmp_path)
     adapter = FakePublishAdapter()

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
