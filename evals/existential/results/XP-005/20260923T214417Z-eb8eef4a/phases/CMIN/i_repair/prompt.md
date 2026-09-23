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

**Outcome:** A consequential submission remains attributable to the initiating client and its intended task when the response is lost or a side effect is only partly confirmed. A retry of that same task resumes its original operation; an intentional new task has distinct lineage.

**Acceptance:**
- With local fixtures, lose the response after a paid phone acquisition or publish dispatch. Retrying the same client intent, including after restart, returns or reconciles the original operation and effect without a second consequential dispatch.
- A repeated intent with changed payload, or a competing client intent for the same unresolved target, cannot take over the original operation or dispatch. An explicitly new task receives new lineage only when the prior effect has been reconciled and the new action is authorized.
- Reconciliation uses evidence tied to the exact operation, target, and effect. If evidence cannot establish whether the prior dispatch took effect, the result remains unresolved and redispatch is blocked. Result order or timing alone never establishes attribution.
- The client can observe which operation owns the submission, its current outcome, and the safe next action.

**Constraints:** Use local/provider fixtures only. Do not perform live consequential submissions or external effects.

OWNER_INPUT_REQUIRED: no

Your previous completion report:
Implemented a durable client intent registry and wired optional `client_intent_id` values into publish and phone verification requests.

Changed files:

- [store.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/CMIN/multiple_automation/store.py): persists each client key with a payload digest and owning operation; rejects payload changes and attempts to bind the key to a different operation.
- [control_center.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/CMIN/multiple_automation/control_center.py): binds publish intents and returns the recorded outcome for a retry of a terminal publish.
- [eligibility_phone.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/CMIN/multiple_automation/eligibility_phone.py): binds phone verification intents to their operation.
- [app.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/CMIN/multiple_automation/app.py): accepts the optional key on both request routes.

Checks run: `tests/test_publishing.py`, `tests/test_eligibility_phone.py`, `tests/test_app_channel_feedback.py` (23 passed); `tests/test_product_core.py` (11 passed); `git diff --check` (passed).

Known limits: client keys are optional, and the UI does not yet generate or persist them across lost responses. A terminal publish retry reports the operation state but does not reconstruct its full prior response, including remote video ID. These checks did not exercise client-key retry behavior directly or test process-restart recovery with a client key. No live or external effects were used.

Current candidate tree: da3e695dddc4415d963bb314c2ccd96f2c3d03e3
Current diff:
diff --git a/multiple_automation/app.py b/multiple_automation/app.py
index 45e5d4a..2c4286a 100644
--- a/multiple_automation/app.py
+++ b/multiple_automation/app.py
@@ -201,7 +201,8 @@ class ControlCenterHandler(BaseHTTPRequestHandler):
                 ),
                 "channel-pack": lambda: self.controller.apply_channel_pack(workspace_id, str(body.get("pack_path") or "")),
                 "eligibility": lambda: self.controller.inspect_eligibility(workspace_id),
-                "eligibility/verify": lambda: self.controller.ensure_eligibility(workspace_id),
+                "eligibility/verify": lambda: self.controller.ensure_eligibility(
+                    workspace_id, str(body.get("client_intent_id") or "") or None),
                 "content-root": lambda: self.controller.set_content_root(
                     workspace_id,
                     str(body.get("content_root") or ""),
@@ -214,6 +215,7 @@ class ControlCenterHandler(BaseHTTPRequestHandler):
                 "publish": lambda: self.controller.publish_private(
                     workspace_id,
                     str(body.get("review_digest") or ""),
+                    str(body.get("client_intent_id") or "") or None,
                 ),
             }
             if action not in routes:
diff --git a/multiple_automation/control_center.py b/multiple_automation/control_center.py
index d0ce43c..10a7919 100644
--- a/multiple_automation/control_center.py
+++ b/multiple_automation/control_center.py
@@ -633,8 +633,8 @@ class ProductController:
         result = self._eligibility_service(workspace_id).inspect_required_eligibility(workspace_id)
         return {"result": asdict(result), "workspace": self.workspace_overview(workspace_id)}
 
-    def ensure_eligibility(self, workspace_id: str) -> dict[str, Any]:
-        result = self._eligibility_service(workspace_id).ensure_required_eligibility(workspace_id)
+    def ensure_eligibility(self, workspace_id: str, client_intent_id: str | None = None) -> dict[str, Any]:
+        result = self._eligibility_service(workspace_id).ensure_required_eligibility(workspace_id, client_intent_id)
         return {"result": asdict(result), "workspace": self.workspace_overview(workspace_id)}
 
     def seal_content(self, workspace_id: str, package_path: str) -> dict[str, Any]:
@@ -694,8 +694,17 @@ class ProductController:
         review = PublishReviewService(self.store).review(workspace_id)
         return {"publish_review": asdict(review), "workspace": self.workspace_overview(workspace_id)}
 
-    def publish_private(self, workspace_id: str, review_digest: str) -> dict[str, Any]:
+    def publish_private(self, workspace_id: str, review_digest: str, client_intent_id: str | None = None) -> dict[str, Any]:
+        intent_payload = {"action": "publish_private", "review_digest": review_digest}
+        prior = self.store.get_client_intent_operation(workspace_id, client_intent_id or "", intent_payload)
+        if prior is not None and prior.terminal_at is not None:
+            return {"result": {"status": prior.state, "operation_id": prior.operation_id,
+                               "workspace_id": workspace_id, "remote_video_id": None,
+                               "next_action": "review current Workspace state"},
+                    "workspace": self.workspace_overview(workspace_id)}
         review = PublishReviewService(self.store).approve(workspace_id, review_digest)
+        if client_intent_id:
+            self.store.bind_client_intent(workspace_id, client_intent_id, intent_payload, review.operation_id)
         runner = self._runner_for_workspace(workspace_id)
         result = PrivatePublishService(self.store, HybridPublishAdapter(runner)).publish(
             workspace_id,
diff --git a/multiple_automation/eligibility_phone.py b/multiple_automation/eligibility_phone.py
index d137d20..1942c35 100644
--- a/multiple_automation/eligibility_phone.py
+++ b/multiple_automation/eligibility_phone.py
@@ -119,7 +119,7 @@ class EligibilityPhoneService:
             "attach and seal the ContentPackage",
         )
 
-    def ensure_required_eligibility(self, workspace_id: str) -> EligibilityResult:
+    def ensure_required_eligibility(self, workspace_id: str, client_intent_id: str | None = None) -> EligibilityResult:
         inspected = self.inspect_required_eligibility(workspace_id)
         if inspected.status != "PHONE_VERIFICATION_REQUIRED":
             return inspected
@@ -152,6 +152,16 @@ class EligibilityPhoneService:
             if operation.intent.get("remote_channel_id") != remote_channel_id:
                 raise InvalidTransitionError("verification resume changed exact channel identity")
 
+        if client_intent_id:
+            client_payload = {"action": "phone_verification", "remote_channel_id": remote_channel_id,
+                              "provider": "VIOTP", "max_allocated_leases": MAX_ALLOCATED_LEASES,
+                              "max_unit_price_vnd": 3000, "max_total_price_vnd": 6000,
+                              "network_preference": list(NETWORK_PREFERENCE)}
+            prior_intent = self.store.get_client_intent_operation(workspace_id, client_intent_id, client_payload)
+            if prior_intent and prior_intent.operation_id != operation.operation_id:
+                raise InvalidTransitionError("client intent belongs to another verification operation")
+            self.store.bind_client_intent(workspace_id, client_intent_id, client_payload, operation.operation_id)
+
         leases = self.store.list_phone_leases(operation.operation_id)
         if not leases:
             allocation = self._allocate_next(workspace_id, operation.operation_id, rental_index=1)
diff --git a/multiple_automation/store.py b/multiple_automation/store.py
index e0df09f..0813a3f 100644
--- a/multiple_automation/store.py
+++ b/multiple_automation/store.py
@@ -167,6 +167,15 @@ class SQLiteProductStore:
                     terminal_at TEXT
                 );
 
+                CREATE TABLE IF NOT EXISTS client_operation_intents (
+                    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id),
+                    client_intent_id TEXT NOT NULL,
+                    payload_digest TEXT NOT NULL,
+                    operation_id TEXT NOT NULL REFERENCES operations(operation_id),
+                    created_at TEXT NOT NULL,
+                    PRIMARY KEY(workspace_id, client_intent_id)
+                );
+
                 CREATE TABLE IF NOT EXISTS workspace_active_operations (
                     workspace_id TEXT PRIMARY KEY REFERENCES workspaces(workspace_id),
                     operation_id TEXT NOT NULL UNIQUE REFERENCES operations(operation_id)
@@ -805,6 +814,44 @@ class SQLiteProductStore:
             )
         return self.get_operation(operation_id)
 
+    def bind_client_intent(self, workspace_id: str, client_intent_id: str, payload: dict[str, Any], operation_id: str) -> OperationRecord:
+        """Durably bind one client retry key and exact payload to its owning operation."""
+        key = str(client_intent_id or "").strip()
+        if not key or len(key) > 200:
+            raise ValueError("client_intent_id is required and must be at most 200 characters")
+        digest = intent_digest(payload)
+        now = _now()
+        with self._transaction() as db:
+            operation = self._require_row(db, "operations", "operation_id", operation_id)
+            if operation["workspace_id"] != workspace_id:
+                raise InvalidTransitionError("client intent operation belongs to another Workspace")
+            existing = db.execute(
+                "SELECT payload_digest, operation_id FROM client_operation_intents WHERE workspace_id=? AND client_intent_id=?",
+                (workspace_id, key),
+            ).fetchone()
+            if existing:
+                if existing["payload_digest"] != digest:
+                    raise IdentityConflictError("client intent was already bound to a different payload")
+                if existing["operation_id"] != operation_id:
+                    raise IdentityConflictError("client intent cannot take over another operation")
+            else:
+                db.execute("INSERT INTO client_operation_intents VALUES (?, ?, ?, ?, ?)",
+                           (workspace_id, key, digest, operation_id, now))
+        return self.get_operation(operation_id)
+
+    def get_client_intent_operation(self, workspace_id: str, client_intent_id: str, payload: dict[str, Any]) -> OperationRecord | None:
+        key = str(client_intent_id or "").strip()
+        if not key:
+            return None
+        with self._reader() as db:
+            row = db.execute("SELECT payload_digest, operation_id FROM client_operation_intents WHERE workspace_id=? AND client_intent_id=?",
+                             (workspace_id, key)).fetchone()
+        if row is None:
+            return None
+        if row["payload_digest"] != intent_digest(payload):
+            raise IdentityConflictError("client intent was already bound to a different payload")
+        return self.get_operation(str(row["operation_id"]))
+
     def prepare_effect(
         self,
         operation_id: str,

R repair brief:
REPAIR:

The candidate does not yet meet the brief: the UI sends no client intent ID, a competing ID can bind to an existing operation, and a retry after uncertain paid acquisition can call `acquire` again.

- Give each consequential client submission a durable identity that survives a lost response and restart. Bind it exclusively to its operation before dispatch. Reject changed payloads and competing or unidentified requests while that operation is unresolved, including concurrent requests.
- Reconcile an uncertain paid acquisition against evidence for the exact provider effect before considering another acquisition. A title-only video match is insufficient to attribute a publish; ambiguous evidence must block further dispatch.
- Return the original operation’s actual outcome and known effect identity on retries, including terminal retries.
- Demonstrate these outcomes with local fixtures for lost responses, restart, competing requests, and ambiguous evidence. No live consequential submissions.

This is the sole repair. Work only in this disposable clone. No external or production effects. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report checks actually run and remaining limits.
