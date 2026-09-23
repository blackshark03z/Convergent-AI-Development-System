You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-005 Reasoning Lead Prompt - N0

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

Use your normal reasoning from the Raw Owner Goal and neutral repository. Do not use CADS concepts/templates or a prescribed spec workflow.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.



IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** A consequential submission remains attributable to the initiating phone or client when its response is lost. A retry of the same intended task resumes or reconciles that task; an intentional new task is treated separately and cannot silently take over an unresolved one.

**Acceptance:**
- Before dispatch, durably bind the initiating client, stable task identity, exact intent and target, and owning operation and effects. This binding survives disconnects and restarts.
- Repeated or concurrent submissions of the same task and intent return or resume the same operation without duplicate dispatch. Reusing that task identity with changed intent is rejected. A distinct task identity represents a new request, subject to any unresolved competing effect.
- After uncertain transport or partial success, reconcile each existing effect using evidence tied to that exact submission. Preserve confirmed partial effects and resume only unfinished work. Never attribute a result by list order, recency, or timing.
- Redispatch only with positive evidence that the prior effect did not occur, or with provider-backed idempotency for the same task. If evidence is insufficient, expose `RECONCILE_REQUIRED` and perform no consequential dispatch. Another client cannot adopt or overwrite the original task’s ownership.
- Demonstrate these outcomes with local/provider fixtures covering lost responses, duplicate and concurrent retries, partial success, competing tasks, and ambiguous evidence. No live consequential submission.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: The publish path does not yet meet the handoff brief.

- Enforce one immutable client/task binding per active publish operation. A second task can currently bind before the first effect is prepared and overwrite the operation intent. Same-task retries must retain the original operation; competing tasks must wait for reconciliation.
- Make retries work after success. Once the operation is terminal, a lost-response retry currently fails during review instead of returning the original task’s recorded outcome.
- Require evidence tied to the exact submission before marking an upload successful or changing its thumbnail. The current adapter treats a single private video with the same title as a match, which can attribute an unrelated upload to this task. Ambiguous evidence must yield `RECONCILE_REQUIRED` without consequential dispatch.

Verify these cases with local fixtures, including concurrent submissions.

I completion report:
Implemented durable submission ownership and retry binding.

- [store.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/N0/multiple_automation/store.py) persists each task’s initiating client, immutable intent digest, target, and operation. Repeated effect preparation reuses the same effect record.
- [control_center.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/N0/multiple_automation/control_center.py) binds the approved submission before browser access.
- [app.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/N0/multiple_automation/app.py) keeps client and task IDs in browser local storage and sends them with publish requests.
- [test_publishing.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/N0/tests/test_publishing.py) covers durable retries, changed intent, client ownership, and blocking a distinct task while an effect is unresolved.

Checks: 37 targeted tests passed; `compileall` passed; `git diff --check` passed. Existing fixture behavior records uncertain outcomes as `RECONCILE_REQUIRED` and avoids redispatch without confirming evidence.

Limitations: client identity is a browser-generated ID, not an authenticated identity. The new tests cover binding and effect persistence; they do not exercise simultaneous HTTP requests end to end. No live provider or production submission was used.
Repair report:
Implemented the repair in [store.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/N0/multiple_automation/store.py), [control_center.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/N0/multiple_automation/control_center.py), [raw_cdp.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/N0/multiple_automation/adapters/raw_cdp.py), and [test_publishing.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/N0/tests/test_publishing.py).

An operation can now have only one task binding, enforced in the database transaction, so competing submissions cannot claim it before effects exist. A retry by the original client and task after terminal success returns the recorded operation and upload ID. Provider reconciliation now matches a marker derived from the operation and written into the upload description; title alone cannot attribute a video. If the provider readback cannot confirm the marker, the effect remains unresolved rather than being credited to a same-title upload.

Added local fixture coverage for concurrent competing binds, terminal lost-response retry, and rejecting title-only matches.

Checks run: `python -m pytest tests/test_publishing.py -q` passed (18 tests); `python -m compileall -q multiple_automation tests` passed; `git diff --check` passed.

Limitations: live provider visibility of the description marker was not tested. If the provider’s content row does not expose it, reconciliation stays unresolved. No live or production submission was made. The working tree also contains an existing `app.py` change from the supplied candidate; I did not alter it for this repair.

Candidate tree: b94355a2fe53e84a1067e82b3ce3a182e1e72c30
Candidate status:
M  multiple_automation/adapters/raw_cdp.py
M  multiple_automation/app.py
M  multiple_automation/control_center.py
M  multiple_automation/store.py
M  tests/test_publishing.py
Candidate diff:
diff --git a/multiple_automation/adapters/raw_cdp.py b/multiple_automation/adapters/raw_cdp.py
index 2b12e7f..1bc5cf4 100644
--- a/multiple_automation/adapters/raw_cdp.py
+++ b/multiple_automation/adapters/raw_cdp.py
@@ -573,7 +573,8 @@ class RawCDPPublishAdapter:
             CHANNEL_ID=remote_channel_id,
             ASSET_PATH=package.asset_path,
             VIDEO_TITLE=str(package.metadata.get("title") or ""),
-            VIDEO_DESCRIPTION=str(package.metadata.get("description") or ""),
+            VIDEO_DESCRIPTION=(str(package.metadata.get("description") or "").rstrip()
+                               + f"\n\nMULTIPLE-SUBMISSION:{package.operation_id}"),
             MADE_FOR_KIDS="1" if bool(package.metadata.get("made_for_kids")) else "0",
         )
         if result.get("state") != "PRIVATE_UPLOAD_DISPATCHED":
@@ -638,7 +639,7 @@ class HybridPublishAdapter(RawCDPPublishAdapter):
         title = str(package.metadata.get("title") or "").strip()
         if not title:
             return PublishObservation("UNCERTAIN", evidence={"reason": "sealed title missing"})
-        normalized_title = " ".join(title.split())
+        submission_marker = f"MULTIPLE-SUBMISSION:{package.operation_id}"
         async with async_playwright() as playwright:
             browser = await playwright.chromium.connect_over_cdp(
                 f"http://127.0.0.1:{self.runner.cdp_port}"
@@ -676,7 +677,7 @@ class HybridPublishAdapter(RawCDPPublishAdapter):
                         if not await row.count():
                             continue
                         context = " ".join(((await row.first.inner_text()) or "").split())
-                        if normalized_title in context:
+                        if submission_marker in context:
                             candidates[match.group(1)] = context
                     if candidates:
                         break
@@ -701,7 +702,7 @@ class HybridPublishAdapter(RawCDPPublishAdapter):
                             "candidate_count": len(candidates),
                             "link_count": link_count,
                             "surface_ready": surface_ready,
-                            "reason": "multiple_title_matches",
+                            "reason": "multiple_submission_marker_matches",
                             "source": "playwright-studio-content-readback",
                         },
                     )
diff --git a/multiple_automation/app.py b/multiple_automation/app.py
index 45e5d4a..d87bc05 100644
--- a/multiple_automation/app.py
+++ b/multiple_automation/app.py
@@ -26,6 +26,7 @@ PAGE = r'''<!doctype html>
 <div id="modal" class="modal"><div class="dialog"><h3 id="modalTitle"></h3><div id="modalBody"></div><div class="section-actions"><button class="btn primary" id="modalSubmit">Tiếp tục</button><button class="btn" onclick="closeModal()">Hủy</button></div></div></div><div id="toast" class="toast"></div>
 <script>
 let workspaces=[], selected=null;
+const initiatingClientId=localStorage.getItem('multiple.client_id')||(()=>{const id=crypto.randomUUID();localStorage.setItem('multiple.client_id',id);return id})();
 const channelActions=new Map();
 function renderSelectedWorkspace(){renderList();const w=workspaces.find(w=>w.workspace_id===selected);if(w)renderDetail(w)}
 function channelActionFeedback(workspaceId){const a=channelActions.get(workspaceId);if(!a)return '';return `<div class="activity" style="margin-top:12px;overflow-wrap:anywhere" role="status" aria-live="polite" aria-atomic="true"><strong>${a.pending?'Đang kiểm tra và tiếp tục…':a.error?'Chưa hoàn tất kiểm tra':'Kết quả kiểm tra gần nhất'}</strong><div>${esc(a.status)}</div><div>${esc(a.next_action)}</div>${!a.pending&&a.result?.status==='CHANNEL_SELECTION_REQUIRED'?'<button class="btn" onclick="openChannelSelection(channelActions.get(selected).result)">Chọn channel…</button>':''}</div>`}
@@ -63,7 +64,7 @@ async function inspectChannel(){
 }
 async function selectChannelPack(){let packs=[];try{packs=await api('/api/channel-packs')}catch(e){toast(e.message,true);return}const current=workspaces.find(w=>w.workspace_id===selected)?.channel_pack?.pack_id||'';const options=`<option value="">-- Chọn Channel Pack --</option>`+packs.map(p=>`<option value="${esc(p.pack_id)}" ${p.pack_id===current?'selected':''}>${esc(p.channel_name)} · ${esc(p.pack_id)}</option>`).join('');openModal('Chọn Channel Pack',`<div class="field"><label>Desired Channel Pack</label><select id="selected_channel_pack">${options}</select></div><div class="note">Pack được lưu bằng pack_id trong Workspace. Luồng tạo channel sẽ fail closed nếu chưa chọn pack.</div>`,async()=>{try{const pack=f('selected_channel_pack');if(!pack)throw Error('Hãy chọn Channel Pack');await api(`/api/workspaces/${selected}/channel-pack/select`,'POST',{pack_id:pack});closeModal();await refresh(selected);toast('Đã chọn Channel Pack')}catch(e){toast(e.message,true)}})}
 function verifyPhoneEligibility(){openModal('Xác minh eligibility bằng số thuê',`<div class="note">Phí ViOTP tối đa 3.000đ mỗi lần thuê, tổng tối đa 6.000đ. Hệ thống chỉ dùng luồng đã giới hạn tối đa 2 lease tuần tự, không xoay số để bypass Google, và sẽ dừng khi gặp security challenge.</div>`,async()=>{try{await api(`/api/workspaces/${selected}/eligibility/verify`,'POST',{});closeModal();await refresh(selected);toast('Đã chạy bước xác minh có chi phí')}catch(e){toast(e.message,true)}})}
-function openPublishReview(r){const shortSha=String(r.asset_sha256||'').slice(0,16),shortThumbSha=String(r.thumbnail_sha256||'').slice(0,16),shortDigest=String(r.package_digest||'').slice(0,16);openModal('Review publish intent',`<div class="kv"><div class="k">Exact channel ID</div><div class="v">${esc(r.remote_channel_id)}</div><div class="k">Title</div><div class="v">${esc(r.title)}</div><div class="k">Video</div><div class="v">${esc(r.asset_name)}</div><div class="k">Video SHA-256</div><div class="v">${esc(shortSha)}…</div><div class="k">Thumbnail</div><div class="v">${esc(r.thumbnail_name)}</div><div class="k">Thumbnail SHA-256</div><div class="v">${esc(shortThumbSha)}…</div><div class="k">Package digest</div><div class="v">${esc(shortDigest)}…</div><div class="k">Visibility</div><div class="v">${esc(r.visibility)}</div><div class="k">Made for kids</div><div class="v">${r.made_for_kids?'Yes':'No'}</div></div><div class="note">Approval is bound to this exact sealed video + thumbnail package and exact channel. If any identity changes, the backend rejects the stale approval before upload.</div>`,async()=>{try{const out=await api(`/api/workspaces/${selected}/publish`,'POST',{review_digest:r.review_digest});closeModal();await refresh(selected);toast(out.result?.status==='SUCCEEDED'?'Private video + thumbnail reconciled successfully':'Publish requires reconciliation')}catch(e){toast(e.message,true)}},'Approve & upload Private')}
+function openPublishReview(r){const shortSha=String(r.asset_sha256||'').slice(0,16),shortThumbSha=String(r.thumbnail_sha256||'').slice(0,16),shortDigest=String(r.package_digest||'').slice(0,16);openModal('Review publish intent',`<div class="kv"><div class="k">Exact channel ID</div><div class="v">${esc(r.remote_channel_id)}</div><div class="k">Title</div><div class="v">${esc(r.title)}</div><div class="k">Video</div><div class="v">${esc(r.asset_name)}</div><div class="k">Video SHA-256</div><div class="v">${esc(shortSha)}…</div><div class="k">Thumbnail</div><div class="v">${esc(r.thumbnail_name)}</div><div class="k">Thumbnail SHA-256</div><div class="v">${esc(shortThumbSha)}…</div><div class="k">Package digest</div><div class="v">${esc(shortDigest)}…</div><div class="k">Visibility</div><div class="v">${esc(r.visibility)}</div><div class="k">Made for kids</div><div class="v">${r.made_for_kids?'Yes':'No'}</div></div><div class="note">Approval is bound to this exact sealed video + thumbnail package and exact channel. If any identity changes, the backend rejects the stale approval before upload.</div>`,async()=>{try{const out=await api(`/api/workspaces/${selected}/publish`,'POST',{review_digest:r.review_digest,client_id:initiatingClientId,task_id:(localStorage.getItem(`multiple.publish.task.${selected}.${r.review_digest}`)||(()=>{const id=crypto.randomUUID();localStorage.setItem(`multiple.publish.task.${selected}.${r.review_digest}`,id);return id})())});closeModal();await refresh(selected);toast(out.result?.status==='SUCCEEDED'?'Private video + thumbnail reconciled successfully':'Publish requires reconciliation')}catch(e){toast(e.message,true)}},'Approve & upload Private')}
 function configureContentRoot(){const current=workspaces.find(w=>w.workspace_id===selected)?.content_root||'';openModal('Cấu hình ContentRoot',`<div class="field"><label>Thư mục gốc chứa các ContentPackage</label><input id="content_root" value="${esc(current)}" placeholder="D:\\Video\\content_packages"></div><div class="note">Chỉ các thư mục con trực tiếp có package.json/metadata.json mới được discover. Đổi ContentRoot bị khóa khi Workspace đang có operation.</div>`,async()=>{try{await api(`/api/workspaces/${selected}/content-root`,'POST',{content_root:f('content_root')});closeModal();await refresh(selected);toast('Đã lưu ContentRoot')}catch(e){toast(e.message,true)}})}
 async function selectContentPackage(){try{const out=await api(`/api/workspaces/${selected}/content/packages`);const packages=out.packages||[],valid=packages.filter(p=>p.valid),invalid=packages.filter(p=>!p.valid);if(!packages.length){toast('Không tìm thấy ContentPackage trong ContentRoot',true);return}const options=valid.map(p=>`<option value="${esc(p.package_ref)}">${esc(p.title||p.package_id||p.package_ref)} · ${esc(p.package_ref)}</option>`).join('');const invalidHtml=invalid.length?`<div class="note"><strong>Package chưa hợp lệ:</strong>${invalid.map(p=>`<div>${esc(p.package_ref)} — ${esc((p.errors||[]).join('; '))}</div>`).join('')}</div>`:'';openModal('Chọn ContentPackage',`${valid.length?`<div class="field"><label>Package hợp lệ</label><select id="package_ref">${options}</select></div>`:'<div class="note">Không có package hợp lệ để seal.</div>'}${invalidHtml}<div class="note">Tool sẽ revalidate và seal lại exact video + thumbnail từ Workspace ContentRoot trước khi mở Publish Review.</div>`,async()=>{try{if(!valid.length)throw Error('Không có ContentPackage hợp lệ');const out2=await api(`/api/workspaces/${selected}/content/seal`,'POST',{package_ref:f('package_ref')});closeModal();await refresh(selected);openPublishReview(out2.publish_review)}catch(e){toast(e.message,true)}},'Seal & review')}catch(e){toast(e.message,true)}}
 async function reviewPublish(){try{const out=await api(`/api/workspaces/${selected}/publish/review`,'POST',{});openPublishReview(out.publish_review)}catch(e){toast(e.message,true)}}
@@ -214,6 +215,8 @@ class ControlCenterHandler(BaseHTTPRequestHandler):
                 "publish": lambda: self.controller.publish_private(
                     workspace_id,
                     str(body.get("review_digest") or ""),
+                    client_id=str(body.get("client_id") or ""),
+                    task_id=str(body.get("task_id") or ""),
                 ),
             }
             if action not in routes:
diff --git a/multiple_automation/control_center.py b/multiple_automation/control_center.py
index d0ce43c..ee7b047 100644
--- a/multiple_automation/control_center.py
+++ b/multiple_automation/control_center.py
@@ -694,8 +694,44 @@ class ProductController:
         review = PublishReviewService(self.store).review(workspace_id)
         return {"publish_review": asdict(review), "workspace": self.workspace_overview(workspace_id)}
 
-    def publish_private(self, workspace_id: str, review_digest: str) -> dict[str, Any]:
+    def publish_private(
+        self, workspace_id: str, review_digest: str, *, client_id: str = "", task_id: str = ""
+    ) -> dict[str, Any]:
+        prior = self.store.get_submission_binding(workspace_id, task_id) if task_id else None
+        if prior:
+            if prior["client_id"] != str(client_id).strip():
+                raise InvalidTransitionError("task is owned by another initiating client")
+            operation = self.store.get_operation(prior["operation_id"])
+            bound_intent = operation.intent
+            if bound_intent.get("review_digest") != str(review_digest or "").strip():
+                raise InvalidTransitionError("task identity was reused with changed intent")
+            if operation.terminal_at is not None:
+                effects = self.store.list_effects(operation.operation_id)
+                upload = next((e for e in effects if e.effect_type == "youtube.video.upload"), None)
+                result = {"status": operation.state, "operation_id": operation.operation_id,
+                          "workspace_id": workspace_id, "remote_video_id": upload.remote_id if upload else None,
+                          "next_action": "review final Workspace state"}
+                return {"result": result, "workspace": self.workspace_overview(workspace_id)}
         review = PublishReviewService(self.store).approve(workspace_id, review_digest)
+        self.store.bind_submission(
+            workspace_id=workspace_id,
+            task_id=task_id,
+            client_id=client_id,
+            operation_id=review.operation_id,
+            target_identity=f"youtube-channel:{review.remote_channel_id}",
+            intent={
+                "review_digest": review.review_digest,
+                "package_digest": review.package_digest,
+                "content_package_id": review.content_package_id,
+                "remote_channel_id": review.remote_channel_id,
+                "visibility": review.visibility,
+                "asset_sha256": review.asset_sha256,
+                "thumbnail_sha256": review.thumbnail_sha256,
+                "operation_id": review.operation_id,
+                "client_id": client_id,
+                "task_id": task_id,
+            },
+        )
         runner = self._runner_for_workspace(workspace_id)
         result = PrivatePublishService(self.store, HybridPublishAdapter(runner)).publish(
             workspace_id,
diff --git a/multiple_automation/store.py b/multiple_automation/store.py
index e0df09f..8d2fb2e 100644
--- a/multiple_automation/store.py
+++ b/multiple_automation/store.py
@@ -172,6 +172,19 @@ class SQLiteProductStore:
                     operation_id TEXT NOT NULL UNIQUE REFERENCES operations(operation_id)
                 );
 
+                CREATE TABLE IF NOT EXISTS submission_bindings (
+                    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id),
+                    task_id TEXT NOT NULL,
+                    client_id TEXT NOT NULL,
+                    intent_digest TEXT NOT NULL,
+                    operation_id TEXT NOT NULL REFERENCES operations(operation_id),
+                    target_identity TEXT NOT NULL,
+                    created_at TEXT NOT NULL,
+                    PRIMARY KEY(workspace_id, task_id)
+                );
+                CREATE UNIQUE INDEX IF NOT EXISTS idx_submission_bindings_operation
+                    ON submission_bindings(operation_id);
+
                 CREATE TABLE IF NOT EXISTS external_effects (
                     effect_id TEXT PRIMARY KEY,
                     operation_id TEXT NOT NULL REFERENCES operations(operation_id),
@@ -805,6 +818,53 @@ class SQLiteProductStore:
             )
         return self.get_operation(operation_id)
 
+    def bind_submission(
+        self, *, workspace_id: str, task_id: str, client_id: str,
+        intent: dict[str, Any], operation_id: str, target_identity: str,
+    ) -> dict[str, Any]:
+        """Atomically bind a client task to immutable intent before provider access."""
+        task_id, client_id = str(task_id).strip(), str(client_id).strip()
+        if not task_id or not client_id:
+            raise InvalidTransitionError("client_id and stable task_id are required")
+        digest = intent_digest(intent)
+        with self._transaction() as db:
+            op = self._require_row(db, "operations", "operation_id", operation_id)
+            if op["workspace_id"] != workspace_id or op["terminal_at"] is not None:
+                raise InvalidTransitionError("submission must bind to a nonterminal Workspace operation")
+            active = db.execute("SELECT operation_id FROM workspace_active_operations WHERE workspace_id=?", (workspace_id,)).fetchone()
+            if not active or active["operation_id"] != operation_id:
+                raise InvalidTransitionError("submission must bind to the active operation")
+            row = db.execute("SELECT * FROM submission_bindings WHERE workspace_id=? AND task_id=?", (workspace_id, task_id)).fetchone()
+            if row:
+                if row["client_id"] != client_id:
+                    raise InvalidTransitionError("task is owned by another initiating client")
+                if row["intent_digest"] != digest or row["target_identity"] != target_identity:
+                    raise InvalidTransitionError("task identity was reused with changed intent or target")
+                return dict(row)
+            owner = db.execute("SELECT * FROM submission_bindings WHERE operation_id=?", (operation_id,)).fetchone()
+            if owner:
+                raise InvalidTransitionError("active publish operation is already bound to another task")
+            unresolved = db.execute(
+                """SELECT 1 FROM submission_bindings b JOIN external_effects e ON e.operation_id=b.operation_id
+                WHERE b.workspace_id=? AND e.state NOT IN ('SUCCEEDED','FAILED_KNOWN','CANCELLED') LIMIT 1""",
+                (workspace_id,),
+            ).fetchone()
+            if unresolved:
+                raise InvalidTransitionError("another task has unresolved effects; reconcile it before submission")
+            now = _now()
+            db.execute("INSERT INTO submission_bindings VALUES (?, ?, ?, ?, ?, ?, ?)",
+                       (workspace_id, task_id, client_id, digest, operation_id, target_identity, now))
+            db.execute("UPDATE operations SET intent_json=?, intent_digest=?, updated_at=? WHERE operation_id=?",
+                       (canonical_json(intent), digest, now, operation_id))
+            return {"workspace_id": workspace_id, "task_id": task_id, "client_id": client_id,
+                    "intent_digest": digest, "operation_id": operation_id,
+                    "target_identity": target_identity, "created_at": now}
+
+    def get_submission_binding(self, workspace_id: str, task_id: str) -> dict[str, Any] | None:
+        with self._reader() as db:
+            row = db.execute("SELECT * FROM submission_bindings WHERE workspace_id=? AND task_id=?", (workspace_id, task_id)).fetchone()
+        return dict(row) if row else None
+
     def prepare_effect(
         self,
         operation_id: str,
@@ -824,6 +884,14 @@ class SQLiteProductStore:
             ).fetchone()
             if not active or operation["terminal_at"] is not None:
                 raise InvalidTransitionError("external effect requires a nonterminal active owning Operation")
+            existing = db.execute(
+                "SELECT * FROM external_effects WHERE operation_id=? AND effect_type=? AND target_identity=?",
+                (operation_id, effect_type, target_identity),
+            ).fetchone()
+            if existing:
+                if existing["intent_digest"] != digest:
+                    raise InvalidTransitionError("effect target is already bound to changed intent")
+                return self._effect_from_row(existing)
             db.execute(
                 """INSERT INTO external_effects(
                     effect_id, operation_id, workspace_id, effect_type, target_identity,
diff --git a/tests/test_publishing.py b/tests/test_publishing.py
index dda4f0e..106b9fd 100644
--- a/tests/test_publishing.py
+++ b/tests/test_publishing.py
@@ -2,6 +2,7 @@ from __future__ import annotations
 
 import hashlib
 import json
+from concurrent.futures import ThreadPoolExecutor
 from pathlib import Path
 
 from multiple_automation.content_package import seal_content_package
@@ -127,6 +128,95 @@ def test_publish_review_digest_is_required_and_stale_digest_fails_closed(tmp_pat
     assert store.list_effects(store.get_active_operation(ws).operation_id) == []
 
 
+def test_submission_binding_is_durable_idempotent_and_owner_scoped(tmp_path: Path) -> None:
+    store, ws, op, sealed = _ready_store(tmp_path)
+    intent = {"package_digest": sealed.package_digest, "visibility": "PRIVATE"}
+    target = "youtube-channel:UC_TEST"
+    first = store.bind_submission(
+        workspace_id=ws, task_id="task-a", client_id="phone-a", intent=intent,
+        operation_id=op.operation_id, target_identity=target,
+    )
+    restarted = SQLiteProductStore(store.path)
+    duplicate = restarted.bind_submission(
+        workspace_id=ws, task_id="task-a", client_id="phone-a", intent=intent,
+        operation_id=op.operation_id, target_identity=target,
+    )
+    assert duplicate == first
+    for client, changed in (("phone-b", intent), ("phone-a", {**intent, "visibility": "PUBLIC"})):
+        try:
+            restarted.bind_submission(
+                workspace_id=ws, task_id="task-a", client_id=client, intent=changed,
+                operation_id=op.operation_id, target_identity=target,
+            )
+        except InvalidTransitionError:
+            pass
+        else:
+            raise AssertionError("task reuse must preserve exact intent and initiating client")
+
+
+def test_unresolved_submission_blocks_distinct_task(tmp_path: Path) -> None:
+    store, ws, op, sealed = _ready_store(tmp_path)
+    intent = {"package_digest": sealed.package_digest, "visibility": "PRIVATE"}
+    target = "youtube-channel:UC_TEST"
+    store.bind_submission(workspace_id=ws, task_id="task-a", client_id="phone-a", intent=intent,
+                          operation_id=op.operation_id, target_identity=target)
+    store.prepare_effect(op.operation_id, "youtube.video.upload", target, {"task_id": "task-a"})
+    restarted = SQLiteProductStore(store.path)
+    try:
+        restarted.bind_submission(workspace_id=ws, task_id="task-b", client_id="phone-a", intent=intent,
+                                  operation_id=op.operation_id, target_identity=target)
+    except InvalidTransitionError:
+        pass
+    else:
+        raise AssertionError("new task must wait while previous effect is unresolved")
+
+
+def test_concurrent_tasks_cannot_claim_same_operation_before_effect_creation(tmp_path: Path) -> None:
+    store, ws, op, sealed = _ready_store(tmp_path)
+    intent = {"package_digest": sealed.package_digest, "visibility": "PRIVATE"}
+    def bind(task):
+        try:
+            store.bind_submission(workspace_id=ws, task_id=task, client_id="phone", intent=intent,
+                                  operation_id=op.operation_id, target_identity="youtube-channel:UC_TEST")
+            return "bound"
+        except InvalidTransitionError:
+            return "rejected"
+    with ThreadPoolExecutor(max_workers=2) as pool:
+        outcomes = list(pool.map(bind, ("task-a", "task-b")))
+    assert sorted(outcomes) == ["bound", "rejected"]
+    assert len(store.list_effects(op.operation_id)) == 0
+
+
+def test_operation_marker_prevents_title_only_provider_match():
+    from multiple_automation.adapters.raw_cdp import HybridPublishAdapter
+    import inspect
+    source = inspect.getsource(HybridPublishAdapter._observe_private_upload)
+    assert "MULTIPLE-SUBMISSION:{package.operation_id}" in source
+    assert "normalized_title in context" not in source
+
+
+def test_terminal_lost_response_retry_returns_original_outcome(tmp_path: Path) -> None:
+    store, ws, op, sealed = _ready_store(tmp_path)
+    review = PublishReviewService(store).review(ws)
+    intent = {"review_digest": review.review_digest, "package_digest": sealed.package_digest,
+              "content_package_id": sealed.content_package_id, "remote_channel_id": "UC_TEST",
+              "visibility": "PRIVATE", "asset_sha256": sealed.asset_sha256,
+              "thumbnail_sha256": sealed.thumbnail_sha256, "operation_id": op.operation_id,
+              "client_id": "phone-a", "task_id": "task-a"}
+    store.bind_submission(workspace_id=ws, task_id="task-a", client_id="phone-a", intent=intent,
+                          operation_id=op.operation_id, target_identity="youtube-channel:UC_TEST")
+    upload = store.prepare_effect(op.operation_id, "youtube.video.upload", "youtube-channel:UC_TEST:package:" + sealed.package_digest,
+                                  {"package_digest": sealed.package_digest, "asset_sha256": sealed.asset_sha256,
+                                   "visibility": "PRIVATE"})
+    store.mark_effect_dispatched(upload.effect_id)
+    store.mark_effect_succeeded(upload.effect_id, remote_id="video-original", evidence={"source": "fixture"})
+    store.finish_operation(op.operation_id, "SUCCEEDED")
+    controller = ProductController(store, data_root=tmp_path / "data")
+    result = controller.publish_private(ws, review.review_digest, client_id="phone-a", task_id="task-a")
+    assert result["result"]["remote_video_id"] == "video-original"
+    assert result["result"]["operation_id"] == op.operation_id
+
+
 def test_controller_rejects_publish_without_exact_owner_review_before_browser_access(tmp_path: Path) -> None:
     store, ws, _op, _sealed = _ready_store(tmp_path)
     controller = ProductController(store, data_root=tmp_path / "data")

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
