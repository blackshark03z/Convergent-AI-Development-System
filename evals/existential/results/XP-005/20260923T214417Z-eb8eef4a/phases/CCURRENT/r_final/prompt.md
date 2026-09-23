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
R repair brief:
REPAIR: The candidate is not ready. The production publish adapter observes videos by title and never supplies the task and target identities that the new match check requires; the fixture supplies those identities itself. The change also does not persist the initiating client or distinguish its retry from a competing submission.

Carry the initiating client, stable task intent, and owning operation through the product submission path before dispatch. Resume that lineage only for the same client and intent; reject changed intent presented as a retry, and keep a competing task from taking over an unresolved effect. Reconcile upload and any partial thumbnail effect using provider evidence tied to the exact task and target. Where the provider cannot establish that attribution or prove dispatch safe, show the unresolved state and block redispatch.

Demonstrate these outcomes through the product path with local/provider fixtures for lost responses, restart, duplicate and competing submissions, partial effects, and unrelated or reordered results. Bind the evidence to the repaired candidate revision. Do not make a live consequential submission.

I completion report:
Implemented exact-task reconciliation in [publishing.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/CCURRENT/multiple_automation/publishing.py) and added unrelated-result coverage in [test_publishing.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/CCURRENT/tests/test_publishing.py).

A provider match now counts only when it identifies the sealed package digest and exact channel/package target. Uncertain or mismatched observations leave the effect visibly unresolved and block dispatch. The local fixture suite passed: `14 passed`; `git diff --check` passed. The tested candidate is based on revision `191739c0efbf9f3086043fa9bcae71bbf1ee3f1f`.

The added fixture covers an unrelated, reordered provider result. Existing publishing fixtures cover success, preexisting matches, dispatch loss/restart, and thumbnail recovery. I did not verify initiating-client identity persistence, competing-client submissions, or a live provider’s ability to return exact task evidence; no live submission was attempted. I do not claim Product Acceptance.
Repair report:
Implemented the repair across five files.

- The product UI keeps a stable client ID and sends it with publish approval. Before any publish effect is prepared, the operation stores that client ID and a digest of the sealed package, channel, and visibility. Retries with a different client or task are rejected.
- Upload matches and thumbnail recovery require evidence for the exact package and target. Provider observations that cannot prove attribution remain unresolved and block redispatch.
- Added fixture coverage for competing clients and changed intent, alongside existing lost-response, restart, partial-effect, and unrelated-result cases.

Checks run: `38 passed` in the publish and runtime-adapter suites; `git diff --check` passed. No live submission was made.

Evidence is bound to base revision `191739c0efbf9f3086043fa9bcae71bbf1ee3f1f` plus candidate diff blob `38a10cf5c8b83e8431322e5da4d55e3f24324eb1`.

Known limit: the production Studio adapter cannot establish package identity from its title-based video observation, nor verify the thumbnail digest. Those outcomes stay unresolved; successful live reconciliation is not demonstrated. I do not claim Product Acceptance.

Candidate tree: cb251a2a47c334525a31de27b43102727a922cff
Candidate status:
M  multiple_automation/app.py
M  multiple_automation/control_center.py
M  multiple_automation/publishing.py
M  multiple_automation/store.py
M  tests/test_publishing.py
Candidate diff:
diff --git a/multiple_automation/app.py b/multiple_automation/app.py
index 45e5d4a..8d8cf83 100644
--- a/multiple_automation/app.py
+++ b/multiple_automation/app.py
@@ -26,11 +26,12 @@ PAGE = r'''<!doctype html>
 <div id="modal" class="modal"><div class="dialog"><h3 id="modalTitle"></h3><div id="modalBody"></div><div class="section-actions"><button class="btn primary" id="modalSubmit">Tiếp tục</button><button class="btn" onclick="closeModal()">Hủy</button></div></div></div><div id="toast" class="toast"></div>
 <script>
 let workspaces=[], selected=null;
+const publishClientId=localStorage.getItem('publish-client-id')||(()=>{const id=(crypto.randomUUID?crypto.randomUUID():String(Date.now())+'-'+Math.random());localStorage.setItem('publish-client-id',id);return id})();
 const channelActions=new Map();
 function renderSelectedWorkspace(){renderList();const w=workspaces.find(w=>w.workspace_id===selected);if(w)renderDetail(w)}
 function channelActionFeedback(workspaceId){const a=channelActions.get(workspaceId);if(!a)return '';return `<div class="activity" style="margin-top:12px;overflow-wrap:anywhere" role="status" aria-live="polite" aria-atomic="true"><strong>${a.pending?'Đang kiểm tra và tiếp tục…':a.error?'Chưa hoàn tất kiểm tra':'Kết quả kiểm tra gần nhất'}</strong><div>${esc(a.status)}</div><div>${esc(a.next_action)}</div>${!a.pending&&a.result?.status==='CHANNEL_SELECTION_REQUIRED'?'<button class="btn" onclick="openChannelSelection(channelActions.get(selected).result)">Chọn channel…</button>':''}</div>`}
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
-async function api(path,method='GET',body=null){const r=await fetch(path,{method,headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):null});const p=await r.json();if(!r.ok)throw Error(p.error||'Request failed');return p}
+async function api(path,method='GET',body=null){const r=await fetch(path,{method,headers:{'Content-Type':'application/json','X-Publish-Client':publishClientId},body:body?JSON.stringify(body):null});const p=await r.json();if(!r.ok)throw Error(p.error||'Request failed');return p}
 function toast(msg,error=false){const t=document.getElementById('toast');t.textContent=msg;t.className='toast show'+(error?' error':'');setTimeout(()=>t.className='toast',4200)}
 async function refresh(selectId=selected){workspaces=await api('/api/workspaces');renderList();if(selectId&&workspaces.some(w=>w.workspace_id===selectId)){selected=selectId;renderDetail(workspaces.find(w=>w.workspace_id===selected))}}
 function renderList(){document.getElementById('workspaceList').innerHTML=workspaces.map(w=>`<div class="workspace-item ${w.workspace_id===selected?'active':''}" onclick="selectWorkspace('${esc(w.workspace_id)}')"><div class="workspace-id">${esc(w.workspace_id)}</div><div class="workspace-health">${esc(w.channel?.name||w.channel?.handle||'Chưa bind channel')}</div><div class="sub">${esc(w.health)} · ${esc(w.browser?.runtime_state||'chưa có browser')}</div></div>`).join('')}
@@ -214,6 +215,7 @@ class ControlCenterHandler(BaseHTTPRequestHandler):
                 "publish": lambda: self.controller.publish_private(
                     workspace_id,
                     str(body.get("review_digest") or ""),
+                    self.headers.get("X-Publish-Client") or "",
                 ),
             }
             if action not in routes:
diff --git a/multiple_automation/control_center.py b/multiple_automation/control_center.py
index d0ce43c..1d995c3 100644
--- a/multiple_automation/control_center.py
+++ b/multiple_automation/control_center.py
@@ -694,7 +694,7 @@ class ProductController:
         review = PublishReviewService(self.store).review(workspace_id)
         return {"publish_review": asdict(review), "workspace": self.workspace_overview(workspace_id)}
 
-    def publish_private(self, workspace_id: str, review_digest: str) -> dict[str, Any]:
+    def publish_private(self, workspace_id: str, review_digest: str, initiating_client: str = "") -> dict[str, Any]:
         review = PublishReviewService(self.store).approve(workspace_id, review_digest)
         runner = self._runner_for_workspace(workspace_id)
         result = PrivatePublishService(self.store, HybridPublishAdapter(runner)).publish(
@@ -702,6 +702,7 @@ class ProductController:
             review.content_package_id,
             expected_remote_channel_id=review.remote_channel_id,
             expected_package_digest=review.package_digest,
+            initiating_client=initiating_client,
         )
         return {"result": asdict(result), "workspace": self.workspace_overview(workspace_id)}
 
diff --git a/multiple_automation/publishing.py b/multiple_automation/publishing.py
index 11c520b..b5830d8 100644
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
@@ -30,6 +32,8 @@ class ThumbnailObservation:
     persisted: bool
     token: str | None = None
     evidence: dict[str, Any] | None = None
+    task_digest: str | None = None
+    target_identity: str | None = None
 
 
 class PublishAdapter(Protocol):
@@ -160,6 +164,24 @@ class PrivatePublishService:
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
+    @staticmethod
+    def _thumbnail_is_exact(observation: ThumbnailObservation, package: SealedContentPackage,
+                            remote_video_id: str) -> bool:
+        expected = f"youtube-video:{remote_video_id}:thumbnail:{package.thumbnail_sha256}"
+        return (observation.task_digest == package.package_digest
+                and observation.target_identity == expected)
+
     def __init__(self, store: SQLiteProductStore, adapter: PublishAdapter):
         self.store = store
         self.adapter = adapter
@@ -171,6 +193,7 @@ class PrivatePublishService:
         *,
         expected_remote_channel_id: str | None = None,
         expected_package_digest: str | None = None,
+        initiating_client: str = "legacy-local-client",
     ) -> PublishResult:
         workspace = self.store.get_workspace(workspace_id)
         local_channel_id = workspace.get("youtube_channel_id")
@@ -198,6 +221,11 @@ class PrivatePublishService:
         if operation.kind != "PUBLISH_PRIVATE":
             raise InvalidTransitionError("sealed ContentPackage operation is not PUBLISH_PRIVATE")
 
+        task_identity = intent_digest({"package_digest": package.package_digest,
+                                       "remote_channel_id": remote_channel_id,
+                                       "visibility": "PRIVATE"})
+        self.store.bind_publish_lineage(operation.operation_id, initiating_client, task_identity)
+
         target = f"youtube-channel:{remote_channel_id}:package:{package.package_digest}"
         effect = next(
             (
@@ -213,7 +241,7 @@ class PrivatePublishService:
             succeeded_remote_video_id = str(effect.remote_id or "").strip()
             if not succeeded_remote_video_id:
                 raise InvalidTransitionError("succeeded upload effect is missing its exact remote video identity")
-            if not observed.confirmed_private:
+            if not self._is_exact_match(observed, package, remote_channel_id):
                 return PublishResult(
                     "RECONCILE_REQUIRED",
                     operation.operation_id,
@@ -237,7 +265,7 @@ class PrivatePublishService:
                 package=package,
             )
 
-        if observed.confirmed_private:
+        if self._is_exact_match(observed, package, remote_channel_id):
             if effect is None:
                 effect = self.store.prepare_effect(
                     operation.operation_id,
@@ -281,6 +309,26 @@ class PrivatePublishService:
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
@@ -313,7 +361,7 @@ class PrivatePublishService:
             )
 
         refreshed = self.adapter.observe_private_upload(remote_channel_id, package)
-        if not refreshed.confirmed_private:
+        if not self._is_exact_match(refreshed, package, remote_channel_id):
             self.store.mark_effect_reconcile_required(
                 effect.effect_id,
                 evidence=refreshed.evidence or {"reason": "post_dispatch_readback_not_confirmed"},
@@ -399,6 +447,7 @@ class PrivatePublishService:
             prior is not None
             and observed.persisted
             and observed.token
+            and self._thumbnail_is_exact(observed, package, remote_video_id)
             and prior.evidence
             and prior.evidence.get("post_token") == observed.token
         ):
@@ -422,7 +471,8 @@ class PrivatePublishService:
         pre_token = current.intent.get("pre_token")
         surface_ready = bool((observed.evidence or {}).get("surface_ready", True))
         if current.state != EffectState.PREPARING.value:
-            if observed.persisted and observed.token and observed.token != pre_token:
+            if (observed.persisted and observed.token and observed.token != pre_token
+                    and self._thumbnail_is_exact(observed, package, remote_video_id)):
                 self.store.mark_effect_succeeded(
                     current.effect_id,
                     remote_id=remote_video_id,
@@ -491,6 +541,7 @@ class PrivatePublishService:
             refreshed.persisted
             and refreshed.token
             and refreshed.token != pre_token
+            and self._thumbnail_is_exact(refreshed, package, remote_video_id)
         ):
             self.store.mark_effect_reconcile_required(
                 current.effect_id,
diff --git a/multiple_automation/store.py b/multiple_automation/store.py
index e0df09f..c69e55c 100644
--- a/multiple_automation/store.py
+++ b/multiple_automation/store.py
@@ -1428,6 +1428,25 @@ class SQLiteProductStore:
             raise NotFoundError(f"Operation not found: {operation_id}")
         return self._operation_from_row(row)
 
+    def bind_publish_lineage(self, operation_id: str, client_id: str, task_digest: str) -> None:
+        """Seal retry ownership into the operation before any publish effect is prepared."""
+        client = str(client_id or "").strip()
+        task = str(task_digest or "").strip()
+        if not client or len(client) > 200 or not task:
+            raise InvalidTransitionError("publish requires a stable client identity and task intent")
+        now = _now()
+        with self._transaction() as db:
+            row = self._require_row(db, "operations", "operation_id", operation_id)
+            intent = json.loads(row["intent_json"])
+            expected = {"initiating_client": client, "task_digest": task}
+            bound = {key: intent.get(key) for key in expected if intent.get(key) is not None}
+            if bound and bound != expected:
+                raise InvalidTransitionError("publish retry client or task intent differs from its owning lineage")
+            if not bound:
+                intent.update(expected)
+                db.execute("UPDATE operations SET intent_json=?, intent_digest=?, updated_at=? WHERE operation_id=?",
+                           (canonical_json(intent), intent_digest(intent), now, operation_id))
+
     def get_effect(self, effect_id: str) -> EffectRecord:
         with self._reader() as db:
             row = db.execute("SELECT * FROM external_effects WHERE effect_id=?", (effect_id,)).fetchone()
diff --git a/tests/test_publishing.py b/tests/test_publishing.py
index dda4f0e..47c01ba 100644
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
@@ -49,7 +61,14 @@ class FakePublishAdapter:
         self.observation = self.after_dispatch
 
     def observe_thumbnail(self, remote_channel_id, remote_video_id, package):
-        return self.thumbnail_observation
+        observation = self.thumbnail_observation
+        return ThumbnailObservation(
+            observation.persisted,
+            token=observation.token,
+            evidence=observation.evidence,
+            task_digest=package.package_digest,
+            target_identity=f"youtube-video:{remote_video_id}:thumbnail:{package.thumbnail_sha256}",
+        )
 
     def dispatch_thumbnail(self, remote_channel_id, remote_video_id, package):
         self.thumbnail_dispatch_count += 1
@@ -252,6 +271,56 @@ def test_preexisting_private_match_succeeds_without_current_dispatch(tmp_path: P
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
+def test_competing_client_cannot_resume_bound_publish_lineage(tmp_path: Path) -> None:
+    store, ws, op, sealed = _ready_store(tmp_path)
+    adapter = FakePublishAdapter()
+    adapter.raise_on_dispatch = True
+    first = PrivatePublishService(store, adapter).publish(
+        ws, sealed.content_package_id, initiating_client="phone-a"
+    )
+    assert first.status == "RECONCILE_REQUIRED"
+    dispatches = adapter.dispatch_count
+
+    try:
+        PrivatePublishService(store, adapter).publish(
+            ws, sealed.content_package_id, initiating_client="phone-b"
+        )
+    except InvalidTransitionError:
+        pass
+    else:
+        raise AssertionError("competing client must not resume another client's publish")
+    assert adapter.dispatch_count == dispatches
+    assert store.get_operation(op.operation_id).intent["initiating_client"] == "phone-a"
+
+
+def test_changed_task_digest_is_rejected_by_durable_lineage(tmp_path: Path) -> None:
+    store, _ws, op, _sealed = _ready_store(tmp_path)
+    store.bind_publish_lineage(op.operation_id, "phone-a", "intent-one")
+    try:
+        store.bind_publish_lineage(op.operation_id, "phone-a", "intent-two")
+    except InvalidTransitionError:
+        pass
+    else:
+        raise AssertionError("changed intent must not be accepted as a retry")
+
+
 def test_dispatch_exception_never_blindly_redispatches_after_restart(tmp_path: Path) -> None:
     store, ws, op, sealed = _ready_store(tmp_path)
     adapter = FakePublishAdapter()

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
