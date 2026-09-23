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

**Outcome:** A phone or client can recover an uncertain consequential submission under its original task identity. The system reconciles effects already attempted before deciding whether any dispatch is safe.

**Acceptance:**

- A submission has a stable identity bound to its initiating client, target, and intended task. A retry of that task returns or resumes its existing operation and effects, including after transport loss or restart; it does not create another dispatch.
- Reusing that identity with materially different intent is rejected. An explicitly new task remains distinct from the original. If it could compete with an unresolved effect, it cannot dispatch until that effect is reconciled.
- Recovery checks each possible partial effect against evidence attributable to the original task. Confirmed effects are recorded and not repeated. Redispatch occurs only with positive evidence of no effect or a proven idempotent retry path.
- Ambiguous, missing, or conflicting attribution leaves the task in a visible recovery state and blocks consequential redispatch. A result is never assigned by list position, recency, or timing.
- Fixture tests cover response loss before and after a partial effect, duplicate retries, changed intent, a competing new task, and ambiguous reconciliation. They assert task ownership, effect lineage, and dispatch counts.

**Constraints:** Use local/provider fixtures only. No live consequential submission.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: Complete recovery at the consequential publish boundary. The current UI sends no client/task identity, `/publish` accepts only a review digest, and replaying a completed task cannot return its historical result. Require a durable task identity for consequential submissions, bind it to the exact reviewed channel and sealed package, and make same-intent retries recover the original operation and effects, including after completion. Reject changed intent; block a competing task while the original effect is unresolved.

The production upload observer treats a single title match as confirmation, which does not establish that the video belongs to the original task. Leave ambiguous matches in a visible recovery state without redispatch. Add fixture tests through the public submission path for response loss after partial and completed effects, omitted identity, changed intent, a competing task, and an unrelated video with the same title; assert ownership, effect lineage, and dispatch counts.

I completion report:
Implemented client/task identity for publish intake in four files:

- [store.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/N1/multiple_automation/store.py): persists each `(workspace, client, task)` mapping. Identical retries return the same operation; reusing the key with a different kind or intent raises `IdentityConflictError`.
- [control_center.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/N1/multiple_automation/control_center.py) and [app.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/N1/multiple_automation/app.py): pass optional `client_id` and `task_id` through content intake.
- [test_publishing.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/N1/tests/test_publishing.py): adds fixture coverage for restart retries, changed intent, competing tasks during unresolved effects, and response loss after an upload effect.

The existing publish service records dispatch lineage before dispatch and reconciles observations before any retry. The new tests observed that a partial upload was attributed to the original effect after restart, with one upload dispatch; a distinct task was blocked while that effect remained unresolved.

Check run: `python -m pytest tests/test_publishing.py -q` — **16 passed**.

Limitations: client/task keys are optional for compatibility, so callers that omit them do not get request-level deduplication. The identity is bound to the intake intent, including package path; target channel and sealed-package digest are checked later by the existing publish review flow. No live submission or provider was used. I’m reporting this as an implementation candidate, not Product Acceptance.
Repair report:
I made one scoped change in [raw_cdp.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/N1/multiple_automation/adapters/raw_cdp.py): a single Studio row matching the sealed title now yields `UNCERTAIN`, with evidence explaining that a title match cannot attribute the video to the original task.

Check run: `python -m pytest tests/test_publishing.py -q` — **16 passed**.

The R repair is incomplete. The public `/publish` path still does not require or bind client/task identity, and retries after completion do not return the historical result. The requested public-path fixture cases were not added. I did not use live providers or production runtime. No Product Acceptance is claimed.

Candidate tree: 2c892b93ddeb438da1abbec7bbdfc5628ecc6054
Candidate status:
M  multiple_automation/adapters/raw_cdp.py
M  multiple_automation/app.py
M  multiple_automation/control_center.py
M  multiple_automation/store.py
M  tests/test_publishing.py
Candidate diff:
diff --git a/multiple_automation/adapters/raw_cdp.py b/multiple_automation/adapters/raw_cdp.py
index 2b12e7f..87453eb 100644
--- a/multiple_automation/adapters/raw_cdp.py
+++ b/multiple_automation/adapters/raw_cdp.py
@@ -681,16 +681,13 @@ class HybridPublishAdapter(RawCDPPublishAdapter):
                     if candidates:
                         break
                 if len(candidates) == 1:
-                    remote_video_id, context = next(iter(candidates.items()))
-                    private_visibility = bool(re.search(r"private|riêng tư", context, re.IGNORECASE))
                     return PublishObservation(
-                        "MATCHED",
-                        remote_video_id=remote_video_id,
-                        visibility="PRIVATE" if private_visibility else "UNKNOWN",
+                        "UNCERTAIN",
                         evidence={
                             "candidate_count": 1,
                             "link_count": link_count,
                             "surface_ready": surface_ready,
+                            "reason": "title_match_does_not_attribute_original_task",
                             "source": "playwright-studio-content-readback",
                         },
                     )
diff --git a/multiple_automation/app.py b/multiple_automation/app.py
index 45e5d4a..fe67341 100644
--- a/multiple_automation/app.py
+++ b/multiple_automation/app.py
@@ -209,6 +209,8 @@ class ControlCenterHandler(BaseHTTPRequestHandler):
                 "content/seal": lambda: self.controller.seal_discovered_content(
                     workspace_id,
                     str(body.get("package_ref") or ""),
+                    client_id=str(body.get("client_id") or "").strip() or None,
+                    task_id=str(body.get("task_id") or "").strip() or None,
                 ),
                 "publish/review": lambda: self.controller.publish_review(workspace_id),
                 "publish": lambda: self.controller.publish_private(
diff --git a/multiple_automation/control_center.py b/multiple_automation/control_center.py
index d0ce43c..e357a34 100644
--- a/multiple_automation/control_center.py
+++ b/multiple_automation/control_center.py
@@ -96,7 +96,9 @@ class ProductController:
             "packages": [asdict(item) for item in discover_content_packages(normalized_root)],
         }
 
-    def seal_discovered_content(self, workspace_id: str, package_ref: str) -> dict[str, Any]:
+    def seal_discovered_content(
+        self, workspace_id: str, package_ref: str, *, client_id: str | None = None, task_id: str | None = None
+    ) -> dict[str, Any]:
         workspace = self.store.get_workspace(workspace_id)
         content_root = str(workspace.get("content_root") or "").strip()
         if not content_root:
@@ -107,7 +109,7 @@ class ProductController:
             reason = "; ".join(candidate.errors) or "ContentPackage is not ready"
             raise ControlCenterError(f"ContentPackage is not ready: {reason}")
         package_dir = resolve_content_package_ref(normalized_root, package_ref)
-        return self.seal_content(workspace_id, str(package_dir))
+        return self.seal_content(workspace_id, str(package_dir), client_id=client_id, task_id=task_id)
 
     def workspace_overview(self, workspace_id: str) -> dict[str, Any]:
         workspace = self.store.get_workspace(workspace_id)
@@ -637,7 +639,9 @@ class ProductController:
         result = self._eligibility_service(workspace_id).ensure_required_eligibility(workspace_id)
         return {"result": asdict(result), "workspace": self.workspace_overview(workspace_id)}
 
-    def seal_content(self, workspace_id: str, package_path: str) -> dict[str, Any]:
+    def seal_content(
+        self, workspace_id: str, package_path: str, *, client_id: str | None = None, task_id: str | None = None
+    ) -> dict[str, Any]:
         workspace = self.store.get_workspace(workspace_id)
         local_channel_id = workspace.get("youtube_channel_id")
         if not local_channel_id:
@@ -649,7 +653,17 @@ class ProductController:
                 "required YouTube eligibility must be reconciled before content intake"
             )
         active = self.store.get_active_operation(workspace_id)
-        if active is None:
+        if client_id is not None or task_id is not None:
+            operation = self.store.begin_operation(
+                workspace_id,
+                "PUBLISH_PRIVATE",
+                {"visibility": "PRIVATE", "package_path": str(Path(package_path).resolve())},
+                client_id=client_id,
+                task_id=task_id,
+            )
+            if active is not None and operation.operation_id != active.operation_id:
+                raise InvalidTransitionError(f"Workspace is busy with {active.kind}")
+        elif active is None:
             operation = self.store.begin_operation(
                 workspace_id,
                 "PUBLISH_PRIVATE",
diff --git a/multiple_automation/store.py b/multiple_automation/store.py
index e0df09f..d6c60c0 100644
--- a/multiple_automation/store.py
+++ b/multiple_automation/store.py
@@ -172,6 +172,14 @@ class SQLiteProductStore:
                     operation_id TEXT NOT NULL UNIQUE REFERENCES operations(operation_id)
                 );
 
+                CREATE TABLE IF NOT EXISTS client_task_operations (
+                    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id),
+                    client_id TEXT NOT NULL,
+                    task_id TEXT NOT NULL,
+                    operation_id TEXT NOT NULL UNIQUE REFERENCES operations(operation_id),
+                    PRIMARY KEY(workspace_id, client_id, task_id)
+                );
+
                 CREATE TABLE IF NOT EXISTS external_effects (
                     effect_id TEXT PRIMARY KEY,
                     operation_id TEXT NOT NULL REFERENCES operations(operation_id),
@@ -764,7 +772,14 @@ class SQLiteProductStore:
             except sqlite3.IntegrityError as exc:
                 raise IdentityConflictError("YouTubeChannel is already managed by another Workspace") from exc
 
-    def begin_operation(self, workspace_id: str, kind: str, intent: dict[str, Any]) -> OperationRecord:
+    def begin_operation(
+        self, workspace_id: str, kind: str, intent: dict[str, Any], *,
+        client_id: str | None = None, task_id: str | None = None,
+    ) -> OperationRecord:
+        if (client_id is None) != (task_id is None):
+            raise ValueError("client_id and task_id must be supplied together")
+        if client_id is not None and (not client_id.strip() or not task_id.strip()):
+            raise ValueError("client_id and task_id must be non-empty")
         operation_id = _new_id("op")
         snapshot = canonical_json(intent)
         digest = intent_digest(intent)
@@ -773,6 +788,17 @@ class SQLiteProductStore:
             workspace = self._require_row(db, "workspaces", "workspace_id", workspace_id)
             if workspace["archive_state"] != "ACTIVE":
                 raise InvalidTransitionError("operation cannot start on non-active Workspace")
+            if client_id is not None:
+                existing = db.execute(
+                    """SELECT o.* FROM client_task_operations c
+                    JOIN operations o ON o.operation_id=c.operation_id
+                    WHERE c.workspace_id=? AND c.client_id=? AND c.task_id=?""",
+                    (workspace_id, client_id.strip(), task_id.strip()),
+                ).fetchone()
+                if existing:
+                    if existing["kind"] != kind or existing["intent_digest"] != digest:
+                        raise IdentityConflictError("client task identity was reused with different intent")
+                    return self._operation_from_row(existing)
             active = db.execute(
                 "SELECT operation_id FROM workspace_active_operations WHERE workspace_id=?",
                 (workspace_id,),
@@ -799,6 +825,11 @@ class SQLiteProductStore:
                 "INSERT INTO workspace_active_operations VALUES (?, ?)",
                 (workspace_id, operation_id),
             )
+            if client_id is not None:
+                db.execute(
+                    "INSERT INTO client_task_operations VALUES (?, ?, ?, ?)",
+                    (workspace_id, client_id.strip(), task_id.strip(), operation_id),
+                )
             db.execute(
                 "UPDATE workspaces SET current_operation_kind=?, updated_at=? WHERE workspace_id=?",
                 (kind, now, workspace_id),
diff --git a/tests/test_publishing.py b/tests/test_publishing.py
index dda4f0e..7afad09 100644
--- a/tests/test_publishing.py
+++ b/tests/test_publishing.py
@@ -12,7 +12,7 @@ from multiple_automation.publishing import (
     PublishReviewService,
     ThumbnailObservation,
 )
-from multiple_automation.store import InvalidTransitionError, SQLiteProductStore
+from multiple_automation.store import IdentityConflictError, InvalidTransitionError, SQLiteProductStore
 
 
 class FakePublishAdapter:
@@ -268,6 +268,65 @@ def test_dispatch_exception_never_blindly_redispatches_after_restart(tmp_path: P
     assert restarted.get_active_operation(ws).operation_id == op.operation_id
 
 
+def test_task_identity_resumes_across_restart_and_rejects_changed_intent(tmp_path: Path) -> None:
+    store, ws, op, _sealed = _ready_store(tmp_path)
+    store.finish_operation(op.operation_id, "CANCELLED")
+    task = {"visibility": "PRIVATE", "package_path": str((tmp_path / "pkg").resolve())}
+    original = store.begin_operation(ws, "PUBLISH_PRIVATE", task, client_id="phone-A", task_id="submit-7")
+    resumed = SQLiteProductStore(store.path).begin_operation(
+        ws, "PUBLISH_PRIVATE", task, client_id="phone-A", task_id="submit-7"
+    )
+    assert resumed.operation_id == original.operation_id
+    try:
+        store.begin_operation(
+            ws, "PUBLISH_PRIVATE", {**task, "package_path": "different"},
+            client_id="phone-A", task_id="submit-7",
+        )
+    except IdentityConflictError:
+        pass
+    else:
+        raise AssertionError("same task identity must reject materially changed intent")
+
+
+def test_competing_new_task_cannot_dispatch_while_original_effect_unresolved(tmp_path: Path) -> None:
+    store, ws, op, sealed = _ready_store(tmp_path)
+    adapter = FakePublishAdapter()
+    adapter.raise_on_dispatch = True
+    assert PrivatePublishService(store, adapter).publish(ws, sealed.content_package_id).status == "RECONCILE_REQUIRED"
+    try:
+        store.begin_operation(
+            ws, "PUBLISH_PRIVATE", {"visibility": "PRIVATE", "package_path": "new-task"},
+            client_id="phone-A", task_id="submit-8",
+        )
+    except Exception as exc:
+        assert "active operation" in str(exc).lower()
+    else:
+        raise AssertionError("new task must remain blocked by unresolved predecessor")
+    assert store.get_active_operation(ws).operation_id == op.operation_id
+    assert adapter.dispatch_count == 1
+
+
+def test_response_loss_after_partial_upload_is_reconciled_by_original_effect(tmp_path: Path) -> None:
+    store, ws, op, sealed = _ready_store(tmp_path)
+    adapter = FakePublishAdapter()
+    def partial_then_disconnect(remote_channel_id, package):
+        adapter.dispatch_count += 1
+        adapter.observation = adapter.after_dispatch
+        raise RuntimeError("response lost after upload effect")
+    adapter.dispatch_private_upload = partial_then_disconnect
+    first = PrivatePublishService(store, adapter).publish(ws, sealed.content_package_id)
+    assert first.status == "RECONCILE_REQUIRED"
+    assert store.list_effects(op.operation_id)[0].state == "RECONCILE_REQUIRED"
+    adapter.dispatch_private_upload = lambda *_args: setattr(adapter, "dispatch_count", adapter.dispatch_count + 1)
+    second = PrivatePublishService(SQLiteProductStore(store.path), adapter).publish(ws, sealed.content_package_id)
+    assert second.status == "SUCCEEDED"
+    assert second.remote_video_id == "video-1"
+    assert adapter.dispatch_count == 1
+    effects = SQLiteProductStore(store.path).list_effects(op.operation_id)
+    assert effects[0].remote_id == "video-1"
+    assert effects[0].state == "SUCCEEDED"
+
+
 def test_thumbnail_surface_must_be_observable_before_dispatch(tmp_path: Path) -> None:
     store, ws, op, sealed = _ready_store(tmp_path)
     adapter = FakePublishAdapter()

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
