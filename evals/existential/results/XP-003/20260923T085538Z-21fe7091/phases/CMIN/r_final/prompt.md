You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-003 Reasoning Lead Prompt — C-min / Minimum CADS residue

You are R, the Reasoning Lead. You do not edit product code.

## Frozen Raw Owner Goal

Make the Story Audio assignment/review journey usable as one coherent user flow,
not merely a set of individually working controls. After speaker review/approval,
the Owner must see a clear result/status, know the next action, and be able to
continue into voice assignment/configuration without a hidden blocker or dead end.

## Fixed intent

- The affected journey is: select story -> prepare/review speakers -> assign voices -> save -> continue.
- Visible state must truthfully reflect remaining blockers.
- If a blocker remains, direct the Owner to the actual action required to clear it.
- Completing speaker review must expose a clear continuation into voice assignment/configuration.
- Saving/approving voice work must expose the next production action without silently starting render.
- Preserve unrelated Story Audio behavior.
- Do not prescribe the implementation method.

## Fixed constraints

- Do not call paid/external providers or the canonical production runtime.
- Keep the historical/reference implementation and held-out evaluator hidden.
- Do not inspect sibling benchmark workspaces or results.
- You may inspect the assigned neutral repository, but must not edit product code.

## Common R→I rule

Produce the smallest Implementation Brief that makes the outcome testable.
SPEC UNTIL TESTABLE, NOT SPEC UNTIL COMPLETE.
Stop specifying once multiple implementations could satisfy the brief, PASS/FAIL
can be judged from observable outcome, and I need not invent a material product
preference or consequence boundary.

Your brief may use Outcome, Acceptance, Constraints / Non-goals, Effects /
Authority, and material assumptions/open questions only if needed. Do not add
design/architecture/task artifacts unless they solve a concrete ambiguity or risk.

## Arm treatment

Preserve only: material Outcome/Intent ambiguity must be bounded and testable;
I DONE and R READY are not Product Acceptance; evidence must apply to the exact
candidate; implementation authority does not grant external effects; assurance
is proportional and unnecessary scaffolding should be omitted.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.


IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** The Owner can move through the selected Story Audio scope from speaker review to voice configuration, save and approval, then the next production action without a dead end.

**Acceptance:**
- After speaker review or approval, the visible result reflects the current state. If review is complete, the Owner has a clear way into voice configuration, even when a historical unresolved count remains nonzero.
- At each step, any remaining blocker is shown truthfully and directs the Owner to the action that clears it. A completed step is not presented as blocked by stale status.
- After voice changes are saved or a voice map is approved, refreshed status shows what happened and exposes the next required action. No save or approval silently starts rendering.
- A representative journey through these transitions is verified against the exact candidate. Focused checks may support that evidence; I DONE and R READY are not Product Acceptance.

**Constraints / authority:** Preserve unrelated Story Audio behavior. Do not call paid or external providers, the canonical production runtime, or trigger production effects as part of verification. Implementation authority does not authorize external effects.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: Verify the new button on this exact candidate with speaker review complete, voice changes saved, and final voice map creation still required. Show that it opens an actionable map creation and review step, then that approval refreshes status and exposes the next production action without starting render. The reported browser test marks the map ready during voice save, so it bypasses the new button. Fix any dead end or misleading status found in that journey.

I completion report:
Implemented the missing next step in [ui/app.js](/D:/CADS-Benchmark/XP-003-AUTO-V2/arms/CMIN/ui/app.js:1619). When speaker review is complete, voice changes are saved, and a final voice map still needs creation, the voice section now offers **“Tạo bản đồ giọng cuối cùng”** and explains that it opens the production task. It does not start rendering.

Checks run: `node --check ui/app.js`, `git diff --check`, and `python -m unittest tests.test_assignment_completed_review_browser tests.test_assignment_workflow_browser tests.test_casting_voice_map_ui` — all passed; 9 tests ran.

The browser checks observed completed speaker review advancing to voice configuration, refreshed save status, and no render commands during the verified journey. They do not specifically exercise the newly added map creation button. No external or production services were called. This is a candidate for review, not Product Acceptance.
Repair report:
**The repair verified the candidate’s final voice-map path; I found no UI defect requiring a code change.** The existing button opens the production workbench, whose actions advance from map creation to review and then preparation.

I updated [browser_assignment_flow_smoke.mjs](/D:/CADS-Benchmark/XP-003-AUTO-V2/arms/CMIN/scripts/browser_assignment_flow_smoke.mjs:325) and [test_assignment_workflow_browser.py](/D:/CADS-Benchmark/XP-003-AUTO-V2/arms/CMIN/tests/test_assignment_workflow_browser.py:237) to exercise and assert that journey. The fixture presents saved voice settings with final map creation still required; the browser check confirms the actionable button and the create → review → prepare transitions. No render command was issued. The voice-map mutation responses are simulated in the test, not sent to a backend.

Checks passed: `python -m unittest tests.test_assignment_workflow_browser` (1 test), `node --check scripts/browser_assignment_flow_smoke.mjs`, and `git diff --check`.

The existing candidate change in `ui/app.js` remains present and unmodified by this repair. This verifies the UI route and action dispatch with fixture state; it does not verify backend map creation or approval. No external or production services were called. This is a candidate for R review, not Product Acceptance.

Candidate tree: 938b58edbd861d2e54d136b2c3c1ca39038fccf5
Candidate status:
M  scripts/browser_assignment_flow_smoke.mjs
M  tests/test_assignment_workflow_browser.py
M  ui/app.js
Candidate diff:
diff --git a/scripts/browser_assignment_flow_smoke.mjs b/scripts/browser_assignment_flow_smoke.mjs
index f67e7b8..d878b5f 100644
--- a/scripts/browser_assignment_flow_smoke.mjs
+++ b/scripts/browser_assignment_flow_smoke.mjs
@@ -325,8 +325,15 @@ try {
     commands: null,
   })`);
   voiceSaveState.commands = await evaluate(`fetch('/api/fixture/commands').then(response => response.json())`);
-  if (!voiceSaveState.preflightEnabled) {
-    throw new Error(`Voice save did not unlock preflight: ${JSON.stringify(voiceSaveState)}`);
+  const mapCreationButton = await evaluate(`(() => {
+    const registry=window.storyAudioAppState.bookVoiceRegistry.result;
+    registry.rows.filter(row=>row.role==='narrator'||row.character_id).forEach(row=>{row.actions={...(row.actions||{}),requires_casting_plan_creation:true};});
+    renderAssignmentPage();
+    const button=document.querySelector('[data-assignment-section="voices"] [data-open-production-preflight]');
+    return {label:button?.textContent.trim()||'',disabled:button?.disabled||false,message:document.querySelector('[data-assignment-section="voices"] .assignment-section-next span')?.textContent.trim()||''};
+  })()`);
+  if (!mapCreationButton.label.includes('Tạo bản đồ giọng cuối cùng') || mapCreationButton.disabled) {
+    throw new Error(`Saved voice configuration did not expose final map creation: ${JSON.stringify(mapCreationButton)}`);
   }
 
   const commandsBeforePreflight = await evaluate(`fetch('/api/fixture/commands').then(response => response.json())`);
@@ -338,6 +345,42 @@ try {
   })`);
   const commandsAfterPreflight = await evaluate(`fetch('/api/fixture/commands').then(response => response.json())`);
 
+  const voiceMapJourney = await evaluate(`(() => {
+    const state = window.storyAudioAppState;
+    const task = (type, key, title, label, stage) => {
+      const primary_action={key,label,target:'voice_map'};
+      return {task_scope:'chapter',task_type:type,task_key:'fixture:'+type,user_stage:stage,
+        title,task_title:title,summary:title,task_summary:title,primary_action,
+        canonical_task:{task_scope:'chapter',task_type:type,task_key:'fixture:'+type,user_stage:stage,
+          current_stage_key:type==='PREPARE_RANGE'?'prepare':'voice_map',title,task_title:title,summary:title,task_summary:title,primary_action}};
+    };
+    const show = value => { state.productionProjection=value; renderProductionShell(currentProductionViewModel()); };
+    const creation = task('CREATE_VOICE_MAP_DRAFT','CREATE_VOICE_MAP_DRAFT','Tạo bản đồ giọng cuối cùng','Tạo Final Voice Map draft',3);
+    show(creation);
+    const creationUi = {heading:document.querySelector('#productionCurrentStepHeading')?.textContent,action:document.querySelector('#productionPrimaryAction')?.textContent,taskType:currentProductionViewModel().task_type};
+    const previousCreate = createSpeakerReviewCastingPlan;
+    const previousApprove = approveCastingPlan;
+    let createCount=0, approveCount=0;
+    createSpeakerReviewCastingPlan=async()=>{createCount++;show(task('REVIEW_VOICE_MAP','REVIEW_VOICE_MAP','Duyệt bản đồ giọng cuối cùng','Duyệt và tiếp tục',3));};
+    approveCastingPlan=async()=>{approveCount++;show(task('PREPARE_RANGE','PREPARE_RANGE','Chuẩn bị phạm vi','Chuẩn bị',4));};
+    document.querySelector('#productionPrimaryAction')?.click();
+    const reviewUi={heading:document.querySelector('#productionCurrentStepHeading')?.textContent,action:document.querySelector('#productionPrimaryAction')?.textContent,taskType:currentProductionViewModel().task_type};
+    document.querySelector('#productionPrimaryAction')?.click();
+    const nextUi={heading:document.querySelector('#productionCurrentStepHeading')?.textContent,action:document.querySelector('#productionPrimaryAction')?.textContent,taskType:currentProductionViewModel().task_type};
+    createSpeakerReviewCastingPlan=previousCreate;approveCastingPlan=previousApprove;
+    return {creationUi,reviewUi,nextUi,createCount,approveCount};
+  })()`);
+  if (voiceMapJourney.creationUi.taskType !== 'CREATE_VOICE_MAP_DRAFT'
+      || voiceMapJourney.reviewUi.taskType !== 'REVIEW_VOICE_MAP'
+      || voiceMapJourney.nextUi.taskType !== 'PREPARE_RANGE'
+      || voiceMapJourney.createCount !== 1 || voiceMapJourney.approveCount !== 1) {
+    throw new Error(`Final voice map journey did not advance: ${JSON.stringify(voiceMapJourney)}`);
+  }
+  const commandsAfterVoiceMapJourney = await evaluate(`fetch('/api/fixture/commands').then(response => response.json())`);
+  if (commandsAfterVoiceMapJourney.length !== commandsAfterPreflight.length) {
+    throw new Error(`Voice map navigation/transition issued an unexpected command: ${JSON.stringify(commandsAfterVoiceMapJourney.slice(commandsAfterPreflight.length))}`);
+  }
+
   const repairBlocked = await evaluate(`(() => {
     const chapter={id:1001,number:1,title:'Chapter 1'};
     const details=[
@@ -397,7 +440,10 @@ try {
     reviewCompletion,
     pollingStability,
     voiceSaveState,
+    mapCreationButton,
     readyNavigation,
+    voiceMapJourney,
+    commandsAfterVoiceMapJourney,
     commandsBeforePreflight,
     commandsAfterPreflight,
     repairBlocked,
diff --git a/tests/test_assignment_workflow_browser.py b/tests/test_assignment_workflow_browser.py
index c8b7dbc..fc87672 100644
--- a/tests/test_assignment_workflow_browser.py
+++ b/tests/test_assignment_workflow_browser.py
@@ -237,6 +237,15 @@ class AssignmentWorkflowBrowserTests(unittest.TestCase):
         self.assertIn("Commander Voice", polling["impact"])
         self.assertIn("Ghi đè đúng phạm vi", polling["impact"])
         self.assertIn("Tiếp tục", evidence["voiceSaveState"]["voiceNextAction"])
+        self.assertIn("Tạo bản đồ giọng cuối cùng", evidence["mapCreationButton"]["label"])
+        self.assertFalse(evidence["mapCreationButton"]["disabled"])
+        self.assertIn("tạo và duyệt bản đồ giọng cuối cùng", evidence["mapCreationButton"]["message"])
+        journey = evidence["voiceMapJourney"]
+        self.assertEqual(journey["creationUi"]["taskType"], "CREATE_VOICE_MAP_DRAFT")
+        self.assertEqual(journey["reviewUi"]["taskType"], "REVIEW_VOICE_MAP")
+        self.assertEqual(journey["nextUi"]["taskType"], "PREPARE_RANGE")
+        self.assertEqual(journey["createCount"], 1)
+        self.assertEqual(journey["approveCount"], 1)
         self.assertIn("book=1", evidence["readyNavigation"]["hash"])
         self.assertIn("from=1", evidence["readyNavigation"]["hash"])
         self.assertIn("to=10", evidence["readyNavigation"]["hash"])
diff --git a/ui/app.js b/ui/app.js
index 6838334..bad1ef7 100644
--- a/ui/app.js
+++ b/ui/app.js
@@ -1618,7 +1618,10 @@ function renderBookVoiceRegistryPage(context,registryState){
   const bookCharacterCount=Array.isArray(registry.characters)?registry.characters.length:0,narratorCount=voiceRows.filter(row=>row.role==='narrator').length,voiceSummary=`<div class="assignment-section-summary"><span><strong>${characterRows.length}</strong> nhân vật/nhóm có lời</span><span><strong>${narratorCount}</strong> người kể chuyện</span><span><strong>${voiceReady}</strong> vai có giọng</span><span><strong>${bookCharacterCount}</strong> nhân vật trong sách</span><span><strong>${voiceUnassigned.length}</strong> chưa có giọng</span><span><strong>${voiceBlockers.length}</strong> xung đột/không khả dụng</span></div>`;
   const rangeOverrideRecovery=renderRegistryRangeOverrideRecovery(context,registry),voiceBatch=renderGeminiVoiceBatch(context,registry),voiceTable=voiceRows.length?`<div class="assignment-registry-table-wrap" data-registry-scroll-region><table class="assignment-registry-table"><thead><tr><th colspan="4">Nhân vật, phạm vi và đoạn thoại để xác nhận</th><th>Thay đổi giọng</th></tr></thead><tbody>${[...voiceRows].sort((a,b)=>Number(registryVoiceNeedsAttention(b))-Number(registryVoiceNeedsAttention(a))).map(row=>renderRegistryTableRow(row,context)).join('')}</tbody></table></div>`:'<div class="assignment-empty-state"><strong>Chưa có Character hoặc nhóm đã xác định</strong><span>Hoàn tất bước duyệt người nói để tạo thư viện giọng cho phạm vi này.</span></div>',voiceSaveBar=renderRegistryBatchSave(context,registry);
   const reviewNext=speakerStatus==='ANALYSIS_REQUIRED'?`Chuẩn bị phân tích ${reviewCount} câu`:reviewCount?`Tiếp tục xử lý ${reviewCount} câu còn lại`:'Tiếp tục cấu hình giọng',preflightLabel=repairReturn?'Quay lại chuẩn bị bản thay thế':'Tiếp tục: kiểm tra & chuẩn bị audio',voiceBlockerText=voiceBlockers.length?`<div class="issue warning"><strong>Giọng cần xử lý</strong>${voiceBlockers.map(row=>`<button type="button" class="text-action" data-voice-blocker-link="${esc(row.speaker_key)}">${esc(row.display_name)} · ${esc(registryStatusLabel(row.status))}</button>`).join('')}</div>`:'',repairBlockerText=repairContextBlockers.length?`<div class="issue warning"><strong>Điều kiện bản thay thế chưa hoàn tất</strong>${repairContextBlockers.map(item=>item.action_label?`<button type="button" class="text-action" data-assignment-repair-focus="${esc(item.assignment_focus||'review')}">${esc(item.title)}</button>`:`<span>${esc(item.title)}</span>`).join('')}</div>`:'';
-  const voiceSection=reviewBlocked?`<section class="assignment-workflow-section voice-section is-locked" data-assignment-section="voices" aria-disabled="true"><div class="assignment-locked-step"><span class="assignment-lock-icon" aria-hidden="true">2</span><div><strong>2. Cấu hình giọng</strong><small>${esc(voiceStatus)}</small><p>Còn <strong>${reviewCount}</strong> ${speakerStatus==='ANALYSIS_REQUIRED'?'câu cần phân tích hoặc xác định người nói':'quyết định người nói cần hoàn tất'}. Sau đó hệ thống sẽ tự mở danh sách Người kể chuyện và tất cả vai có lời để bạn cấu hình giọng một lần tại đây.</p></div><button type="button" class="secondary" data-jump-to-speaker-review>Tiếp tục Bước 1</button></div></section>`:`<details class="assignment-workflow-section voice-section ${voiceStepCurrent?'is-current':'is-complete'}" data-assignment-section="voices" ${voicesOpen?'open':''}><summary><span><strong>2. Vai có lời trong phạm vi và cấu hình giọng</strong><small>${esc(voiceStatus)}</small></span>${voiceSummary}</summary><div class="assignment-section-body"><p class="section-guide">Duyệt đề xuất giọng của Gemini tại đây, rồi chỉnh riêng từng vai nếu cần. Mỗi vai hiển thị nơi xuất hiện trong toàn bộ phạm vi đã chọn và phần còn thực sự được xử lý.</p>${voiceSummary}${rangeOverrideRecovery}${voiceBatch}${voiceTable}${voiceSaveBar}${voiceBlockerText}<div class="assignment-section-next ${preflightReady?'is-ready':'is-blocked'}">${preflightReady?`<button type="button" class="primary" data-open-production-preflight>${esc(preflightLabel)}</button>`:''}<span>${preflightReady?'Tất cả vai đang dùng giọng khả dụng.':pendingVoiceChanges.length?`Cần lưu ${pendingVoiceChanges.length} thay đổi đang chờ trước khi tiếp tục.`:castingCreationRows.length?'Cần lưu cấu hình giọng để tạo bản đồ giọng cuối cùng.':'Các điều kiện bản thay thế chưa hoàn tất.'}</span></div></div></details>`;
+  const canCreateFinalVoiceMap=!reviewBlocked&&!pendingVoiceChanges.length&&!voiceBlockers.length&&castingCreationRows.length>0&&!repairContextBlockers.length;
+  const voiceNextAction=preflightReady?`<button type="button" class="primary" data-open-production-preflight>${esc(preflightLabel)}</button>`:canCreateFinalVoiceMap?'<button type="button" class="primary" data-open-production-preflight>Tạo bản đồ giọng cuối cùng</button>':'';
+  const voiceNextMessage=preflightReady?'Tất cả vai đang dùng giọng khả dụng.':pendingVoiceChanges.length?`Cần lưu ${pendingVoiceChanges.length} thay đổi đang chờ trước khi tiếp tục.`:canCreateFinalVoiceMap?'Cấu hình đã lưu. Mở bước sản xuất để tạo và duyệt bản đồ giọng cuối cùng.':castingCreationRows.length?'Cần lưu cấu hình giọng để tạo bản đồ giọng cuối cùng.':voiceBlockers.length?'Hãy xử lý các giọng cần chú ý ở trên trước khi tiếp tục.':'Các điều kiện bản thay thế chưa hoàn tất.';
+  const voiceSection=reviewBlocked?`<section class="assignment-workflow-section voice-section is-locked" data-assignment-section="voices" aria-disabled="true"><div class="assignment-locked-step"><span class="assignment-lock-icon" aria-hidden="true">2</span><div><strong>2. Cấu hình giọng</strong><small>${esc(voiceStatus)}</small><p>Còn <strong>${reviewCount}</strong> ${speakerStatus==='ANALYSIS_REQUIRED'?'câu cần phân tích hoặc xác định người nói':'quyết định người nói cần hoàn tất'}. Sau đó hệ thống sẽ tự mở danh sách Người kể chuyện và tất cả vai có lời để bạn cấu hình giọng một lần tại đây.</p></div><button type="button" class="secondary" data-jump-to-speaker-review>Tiếp tục Bước 1</button></div></section>`:`<details class="assignment-workflow-section voice-section ${voiceStepCurrent?'is-current':'is-complete'}" data-assignment-section="voices" ${voicesOpen?'open':''}><summary><span><strong>2. Vai có lời trong phạm vi và cấu hình giọng</strong><small>${esc(voiceStatus)}</small></span>${voiceSummary}</summary><div class="assignment-section-body"><p class="section-guide">Duyệt đề xuất giọng của Gemini tại đây, rồi chỉnh riêng từng vai nếu cần. Mỗi vai hiển thị nơi xuất hiện trong toàn bộ phạm vi đã chọn và phần còn thực sự được xử lý.</p>${voiceSummary}${rangeOverrideRecovery}${voiceBatch}${voiceTable}${voiceSaveBar}${voiceBlockerText}<div class="assignment-section-next ${preflightReady||canCreateFinalVoiceMap?'is-ready':'is-blocked'}">${voiceNextAction}<span>${voiceNextMessage}</span></div></div></details>`;
   rowsRoot.innerHTML=`<details class="assignment-workflow-section review-section ${reviewBlocked?'is-current':'is-complete'}" data-assignment-section="review" ${reviewOpen?'open':''}><summary><span><strong>1. Duyệt người nói</strong><small>${esc(reviewStatus)}</small></span></summary><div class="assignment-section-body"><p class="section-guide">Xác định ai đang nói từng câu. Gemini chỉ đề xuất danh tính; bạn có thể chấp nhận, chỉnh sửa, nhóm quần chúng hoặc để lại xử lý sau.</p>${reviewBody}<div class="assignment-section-next"><button type="button" class="secondary" data-assignment-review-next>${esc(reviewNext)}</button></div></div></details>${voiceSection}<section class="assignment-preflight-step ${preflightReady?'is-ready':'is-blocked'}" data-assignment-preflight-step><div><strong>3. Kiểm tra sẵn sàng</strong><span>${preflightReady?(repairReturn?`Các điều kiện cho Chương ${context.fromChapter} đã hoàn tất.`:'Phạm vi đã sẵn sàng để mở kiểm tra sản xuất.'):'Bước này sẽ mở khi các blocker bắt buộc đã được xử lý.'}</span>${repairBlockerText}</div><button type="button" class="secondary" data-open-production-preflight ${preflightReady?'':'disabled'}>${esc(preflightLabel)}</button></section>`;
   blocked.classList.add('hidden');blocked.textContent='';
   rowsRoot.onfocusout=()=>window.setTimeout(applyDeferredSpeakerReviewUpdate,0);

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
