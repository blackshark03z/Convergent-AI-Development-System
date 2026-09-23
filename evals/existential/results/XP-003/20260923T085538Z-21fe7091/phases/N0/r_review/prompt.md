You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-003 Reasoning Lead Prompt — N0 / No CADS

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

Use your normal reasoning from the Raw Owner Goal and neutral repository. Do not
use CADS concepts/templates or a prescribed spec workflow.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.


IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** The Owner can move through the selected story and chapter scope from speaker review to voice configuration, saving, and the next production action as one clear flow.

**Acceptance:**

- After individual or batch speaker review, show the saved result and any remaining speaker decisions. Deferred, failed, or unanalyzed items must remain visible as blockers with a way to reach the action that clears them.
- Once speaker review is complete, provide a clear continuation into voice assignment for the same scope, with the current saved state shown.
- Voice status must reflect the actual remaining work, including unsaved choices, unusable or missing voices, and any casting plan creation or approval still required. A required step must remain actionable even when there are no voice changes to save.
- After voice work is saved or approved, show the result and the next valid production action for that scope. Failed or partial saves must not appear complete. Neither saving nor approval starts rendering automatically.
- Preserve unrelated Story Audio behavior.

**Constraints:** Use only the assigned repository for implementation and verification; do not call paid or external providers or the canonical production runtime.

OWNER_INPUT_REQUIRED: no

I completion report:
Implemented the selected scope’s speaker-to-voice continuation in [ui/app.js](/D:/CADS-Benchmark/XP-003-AUTO-V2/arms/N0/ui/app.js:1613).

Voice status now shows unsaved choices, unusable voices, missing voices, and when a Casting Plan still needs creation or approval. If voices are already saved and usable but the plan step remains, **Mở bước Casting Plan** opens that action without requiring a save. Missing voices remain visible while the existing production readiness flow decides whether work can continue.

**Checks:** `node --check ui/app.js` passed; 55 focused UI tests passed; the assignment workflow browser smoke test passed after I adjusted the readiness display to preserve its existing fallback behavior. That browser test reported that saving voice configuration unlocked preflight.

Only `ui/app.js` changed. I did not verify every partial-save or approval scenario in a browser, and this candidate is not Product Acceptance.

Candidate tree: 1e6237a5bc93bf5a297415b43298244e1570c925
Candidate status:
M  ui/app.js
Candidate diff:
diff --git a/ui/app.js b/ui/app.js
index 6838334..9dd823c 100644
--- a/ui/app.js
+++ b/ui/app.js
@@ -1610,7 +1610,7 @@ function renderBookVoiceRegistryPage(context,registryState){
   if(!speakerState.status)speakerState.status=unresolvedRows.length?'CURRENT_REVIEW_REQUIRED':'NO_REVIEW_REQUIRED';
   const speakerStatus=String(speakerState.status),reviewCount=speakerReviewRemainingCount(speakerState,unresolvedRows),voiceRows=rows.filter(row=>row.role==='narrator'||row.character_id),characterRows=voiceRows.filter(row=>row.role!=='narrator'),voiceUnassigned=voiceRows.filter(registryVoiceIsUnassigned),voiceBlockers=voiceRows.filter(registryVoiceNeedsAttention),castingCreationRows=voiceRows.filter(row=>row.actions?.requires_casting_plan_creation),speakerDependencyBlocked=!speakerStateResolved(speakerState),voiceReady=voiceRows.length-voiceUnassigned.length-voiceBlockers.length;
   const sections=registryState.workflowSections||{},reviewJustCompleted=Number(registryState.lastReviewCount)>0&&reviewCount===0,assignmentFocus=context.assignmentFocus||'';if(reviewJustCompleted){sections.review=false;sections.voices=true}if(assignmentFocus==='review'&&sections.review===null)sections.review=true;if(assignmentFocus==='voices'&&sections.voices===null)sections.voices=true;const reviewOpen=sections.review===null?reviewCount>0:!!sections.review,voicesOpen=sections.voices===null?reviewCount===0:!!sections.voices;registryState.workflowSections=sections;registryState.lastReviewCount=reviewCount;
-  const pendingVoiceChanges=registryPendingVoiceChanges(context,registry),repairReturn=context.returnTask==='REPAIR_PREFLIGHT',rawRepairContextBlockers=repairReturn?repairActionableBlockers(currentProductionViewModel().repair||{},{number:context.fromChapter}):[],repairContextBlockers=speakerStateResolved(speakerState)?rawRepairContextBlockers.filter(item=>!String(item.code||'').startsWith('SPEAKER_')):rawRepairContextBlockers,reviewBlocked=!speakerStateResolved(speakerState),voiceStepBlocked=reviewBlocked,voiceStepCurrent=!reviewBlocked&&(pendingVoiceChanges.length>0||voiceBlockers.length>0||castingCreationRows.length>0),preflightReady=!reviewBlocked&&pendingVoiceChanges.length===0&&voiceBlockers.length===0&&castingCreationRows.length===0&&repairContextBlockers.length===0,reviewStatus=speakerStatus==='CURRENT_REVIEW_REQUIRED'?`Còn ${reviewCount} câu chưa xác định người nói`:speakerStatus==='ANALYSIS_REQUIRED'?`${reviewCount} câu chưa phân tích`:speakerStatus==='APPROVED_CURRENT'?'Đã duyệt người nói':'Đã hoàn tất',voiceStatus=speakerStatus==='ANALYSIS_REQUIRED'?'Cần phân tích hoặc xử lý thủ công':speakerStatus==='CURRENT_REVIEW_REQUIRED'?'Còn người nói chưa xác định':pendingVoiceChanges.length?`${pendingVoiceChanges.length} thay đổi chưa lưu`:castingCreationRows.length?'Sẵn sàng chọn giọng và tạo bản đồ giọng':voiceBlockers.length?`${voiceBlockers.length} mục cần chú ý`:voiceUnassigned.length?`${voiceUnassigned.length} mục chưa có giọng · có thể xử lý sau`:`${voiceReady} vai sẵn sàng`,preflightStatus=reviewBlocked?(speakerStatus==='ANALYSIS_REQUIRED'?'Cần phân tích hoặc xử lý thủ công':'Cần xác định người nói'):pendingVoiceChanges.length?`Cần lưu ${pendingVoiceChanges.length} thay đổi giọng`:castingCreationRows.length?'Cần hoàn tất bản đồ giọng':voiceBlockers.length?'Cần xử lý giọng':repairContextBlockers.length?repairContextBlockers[0].title:'Có thể kiểm tra';
+  const pendingVoiceChanges=registryPendingVoiceChanges(context,registry),repairReturn=context.returnTask==='REPAIR_PREFLIGHT',rawRepairContextBlockers=repairReturn?repairActionableBlockers(currentProductionViewModel().repair||{},{number:context.fromChapter}):[],repairContextBlockers=speakerStateResolved(speakerState)?rawRepairContextBlockers.filter(item=>!String(item.code||'').startsWith('SPEAKER_')):rawRepairContextBlockers,reviewBlocked=!speakerStateResolved(speakerState),voiceStepBlocked=reviewBlocked,voiceStepCurrent=!reviewBlocked&&(pendingVoiceChanges.length>0||voiceBlockers.length>0||voiceUnassigned.length>0||castingCreationRows.length>0),preflightReady=!reviewBlocked&&pendingVoiceChanges.length===0&&voiceBlockers.length===0&&castingCreationRows.length===0&&repairContextBlockers.length===0,reviewStatus=speakerStatus==='CURRENT_REVIEW_REQUIRED'?`Còn ${reviewCount} câu chưa xác định người nói`:speakerStatus==='ANALYSIS_REQUIRED'?`${reviewCount} câu chưa phân tích`:speakerStatus==='APPROVED_CURRENT'?'Đã duyệt người nói':'Đã hoàn tất',voiceStatus=[pendingVoiceChanges.length?`${pendingVoiceChanges.length} thay đổi chưa lưu`:'',voiceBlockers.length?`${voiceBlockers.length} giọng không khả dụng hoặc xung đột`:'',voiceUnassigned.length?`${voiceUnassigned.length} vai thiếu giọng`:'',castingCreationRows.length?'Cần tạo hoặc duyệt Casting Plan':''].filter(Boolean).join(' · ')||(speakerStatus==='ANALYSIS_REQUIRED'?'Cần phân tích hoặc xử lý thủ công':speakerStatus==='CURRENT_REVIEW_REQUIRED'?'Còn người nói chưa xác định':`${voiceReady} vai có giọng khả dụng`),preflightStatus=reviewBlocked?(speakerStatus==='ANALYSIS_REQUIRED'?'Cần phân tích hoặc xử lý thủ công':'Cần xác định người nói'):pendingVoiceChanges.length?`Cần lưu ${pendingVoiceChanges.length} thay đổi giọng`:castingCreationRows.length?'Cần hoàn tất bản đồ giọng':voiceBlockers.length?'Cần xử lý giọng':repairContextBlockers.length?repairContextBlockers[0].title:'Có thể kiểm tra';
   summary.innerHTML=`${renderCastingJourney({context,registry})}<div class="assignment-workflow-steps" aria-label="Tiến trình gán giọng"><div class="${reviewBlocked?'current':'complete'}"><strong>1</strong><span>Duyệt người nói<small>${esc(reviewStatus)}</small></span></div><div class="${voiceStepBlocked?'optional':voiceStepCurrent?'current':'complete'}"><strong>2</strong><span>Cấu hình giọng<small>${esc(voiceStatus)}</small></span></div><div class="${preflightReady?'current':'blocked'}"><strong>3</strong><span>Kiểm tra sẵn sàng<small>${esc(preflightStatus)}</small></span></div></div>`;
   bindCastingJourneyActions(summary);
   const historyOpen=!!sections.history,suggestionPanel=renderSpeakerSuggestionWorkspace(context,registry),historyPanel=renderSpeakerStateHistory(speakerState,historyOpen),reviewBody=speakerStatus==='ANALYSIS_REQUIRED'?`<div class="assignment-empty-state"><strong>Cần chuẩn bị phân tích người nói hiện tại trước khi duyệt.</strong><span>Hệ thống sẽ tạo hoặc làm mới Speaker Draft cho đúng Revision hiện tại trước; đề xuất duyệt cũ không được dùng làm authority.</span><button type="button" class="primary" data-prepare-speaker-analysis>Chuẩn bị phân tích người nói</button></div>${historyPanel}`:speakerStatus==='CURRENT_REVIEW_REQUIRED'?(suggestionPanel||'<div class="assignment-empty-state"><strong>Còn câu cần xác định người nói</strong><span>Hàng đợi hiện tại chưa tải được các câu cần duyệt.</span></div>')+historyPanel:speakerStatus==='APPROVED_CURRENT'?`${renderCompletedSpeakerBatchState(speakerState)}<div class="assignment-empty-state"><strong>Bản xác định người nói hiện tại đã được duyệt.</strong><span>Cấu trúc người nói của Revision ${esc(speakerState.current_revision_id)} đang được dùng.</span></div>${historyPanel}`:`<div class="assignment-empty-state"><strong>Không có câu thoại nào cần xác định người nói trong bản hiện tại.</strong><span>Draft cũ chỉ được giữ trong lịch sử và không chặn cấu hình giọng.</span></div>${historyPanel}`;
@@ -1618,7 +1618,7 @@ function renderBookVoiceRegistryPage(context,registryState){
   const bookCharacterCount=Array.isArray(registry.characters)?registry.characters.length:0,narratorCount=voiceRows.filter(row=>row.role==='narrator').length,voiceSummary=`<div class="assignment-section-summary"><span><strong>${characterRows.length}</strong> nhân vật/nhóm có lời</span><span><strong>${narratorCount}</strong> người kể chuyện</span><span><strong>${voiceReady}</strong> vai có giọng</span><span><strong>${bookCharacterCount}</strong> nhân vật trong sách</span><span><strong>${voiceUnassigned.length}</strong> chưa có giọng</span><span><strong>${voiceBlockers.length}</strong> xung đột/không khả dụng</span></div>`;
   const rangeOverrideRecovery=renderRegistryRangeOverrideRecovery(context,registry),voiceBatch=renderGeminiVoiceBatch(context,registry),voiceTable=voiceRows.length?`<div class="assignment-registry-table-wrap" data-registry-scroll-region><table class="assignment-registry-table"><thead><tr><th colspan="4">Nhân vật, phạm vi và đoạn thoại để xác nhận</th><th>Thay đổi giọng</th></tr></thead><tbody>${[...voiceRows].sort((a,b)=>Number(registryVoiceNeedsAttention(b))-Number(registryVoiceNeedsAttention(a))).map(row=>renderRegistryTableRow(row,context)).join('')}</tbody></table></div>`:'<div class="assignment-empty-state"><strong>Chưa có Character hoặc nhóm đã xác định</strong><span>Hoàn tất bước duyệt người nói để tạo thư viện giọng cho phạm vi này.</span></div>',voiceSaveBar=renderRegistryBatchSave(context,registry);
   const reviewNext=speakerStatus==='ANALYSIS_REQUIRED'?`Chuẩn bị phân tích ${reviewCount} câu`:reviewCount?`Tiếp tục xử lý ${reviewCount} câu còn lại`:'Tiếp tục cấu hình giọng',preflightLabel=repairReturn?'Quay lại chuẩn bị bản thay thế':'Tiếp tục: kiểm tra & chuẩn bị audio',voiceBlockerText=voiceBlockers.length?`<div class="issue warning"><strong>Giọng cần xử lý</strong>${voiceBlockers.map(row=>`<button type="button" class="text-action" data-voice-blocker-link="${esc(row.speaker_key)}">${esc(row.display_name)} · ${esc(registryStatusLabel(row.status))}</button>`).join('')}</div>`:'',repairBlockerText=repairContextBlockers.length?`<div class="issue warning"><strong>Điều kiện bản thay thế chưa hoàn tất</strong>${repairContextBlockers.map(item=>item.action_label?`<button type="button" class="text-action" data-assignment-repair-focus="${esc(item.assignment_focus||'review')}">${esc(item.title)}</button>`:`<span>${esc(item.title)}</span>`).join('')}</div>`:'';
-  const voiceSection=reviewBlocked?`<section class="assignment-workflow-section voice-section is-locked" data-assignment-section="voices" aria-disabled="true"><div class="assignment-locked-step"><span class="assignment-lock-icon" aria-hidden="true">2</span><div><strong>2. Cấu hình giọng</strong><small>${esc(voiceStatus)}</small><p>Còn <strong>${reviewCount}</strong> ${speakerStatus==='ANALYSIS_REQUIRED'?'câu cần phân tích hoặc xác định người nói':'quyết định người nói cần hoàn tất'}. Sau đó hệ thống sẽ tự mở danh sách Người kể chuyện và tất cả vai có lời để bạn cấu hình giọng một lần tại đây.</p></div><button type="button" class="secondary" data-jump-to-speaker-review>Tiếp tục Bước 1</button></div></section>`:`<details class="assignment-workflow-section voice-section ${voiceStepCurrent?'is-current':'is-complete'}" data-assignment-section="voices" ${voicesOpen?'open':''}><summary><span><strong>2. Vai có lời trong phạm vi và cấu hình giọng</strong><small>${esc(voiceStatus)}</small></span>${voiceSummary}</summary><div class="assignment-section-body"><p class="section-guide">Duyệt đề xuất giọng của Gemini tại đây, rồi chỉnh riêng từng vai nếu cần. Mỗi vai hiển thị nơi xuất hiện trong toàn bộ phạm vi đã chọn và phần còn thực sự được xử lý.</p>${voiceSummary}${rangeOverrideRecovery}${voiceBatch}${voiceTable}${voiceSaveBar}${voiceBlockerText}<div class="assignment-section-next ${preflightReady?'is-ready':'is-blocked'}">${preflightReady?`<button type="button" class="primary" data-open-production-preflight>${esc(preflightLabel)}</button>`:''}<span>${preflightReady?'Tất cả vai đang dùng giọng khả dụng.':pendingVoiceChanges.length?`Cần lưu ${pendingVoiceChanges.length} thay đổi đang chờ trước khi tiếp tục.`:castingCreationRows.length?'Cần lưu cấu hình giọng để tạo bản đồ giọng cuối cùng.':'Các điều kiện bản thay thế chưa hoàn tất.'}</span></div></div></details>`;
+  const voiceSection=reviewBlocked?`<section class="assignment-workflow-section voice-section is-locked" data-assignment-section="voices" aria-disabled="true"><div class="assignment-locked-step"><span class="assignment-lock-icon" aria-hidden="true">2</span><div><strong>2. Cấu hình giọng</strong><small>${esc(voiceStatus)}</small><p>Còn <strong>${reviewCount}</strong> ${speakerStatus==='ANALYSIS_REQUIRED'?'câu cần phân tích hoặc xác định người nói':'quyết định người nói cần hoàn tất'}. Sau đó hệ thống sẽ tự mở danh sách Người kể chuyện và tất cả vai có lời để bạn cấu hình giọng một lần tại đây.</p></div><button type="button" class="secondary" data-jump-to-speaker-review>Tiếp tục Bước 1</button></div></section>`:`<details class="assignment-workflow-section voice-section ${voiceStepCurrent?'is-current':'is-complete'}" data-assignment-section="voices" ${voicesOpen?'open':''}><summary><span><strong>2. Vai có lời trong phạm vi và cấu hình giọng</strong><small>${esc(voiceStatus)}</small></span>${voiceSummary}</summary><div class="assignment-section-body"><p class="section-guide">Duyệt đề xuất giọng của Gemini tại đây, rồi chỉnh riêng từng vai nếu cần. Mỗi vai hiển thị nơi xuất hiện trong toàn bộ phạm vi đã chọn và phần còn thực sự được xử lý.</p>${voiceSummary}${rangeOverrideRecovery}${voiceBatch}${voiceTable}${voiceSaveBar}${voiceBlockerText}<div class="assignment-section-next ${preflightReady?'is-ready':'is-blocked'}">${preflightReady?`<button type="button" class="primary" data-open-production-preflight>${esc(preflightLabel)}</button><span>${voiceUnassigned.length?`Có thể tiếp tục; ${voiceUnassigned.length} vai vẫn thiếu giọng và sẽ được kiểm tra ở bước sẵn sàng.`:'Tất cả vai đang dùng giọng khả dụng.'}</span>`:pendingVoiceChanges.length?`<span>Cần lưu ${pendingVoiceChanges.length} thay đổi đang chờ trước khi tiếp tục.</span>`:castingCreationRows.length&&!voiceUnassigned.length&&!voiceBlockers.length?`<span>Cấu hình đã lưu; bước Casting Plan vẫn cần hoàn tất.</span><button type="button" class="secondary" data-open-final-casting>Mở bước Casting Plan</button>`:voiceUnassigned.length?`<span>Cần chọn giọng cho ${voiceUnassigned.length} vai trước khi tiếp tục.</span>`:'<span>Các điều kiện bản thay thế chưa hoàn tất.</span>'}</div></div></details>`;
   rowsRoot.innerHTML=`<details class="assignment-workflow-section review-section ${reviewBlocked?'is-current':'is-complete'}" data-assignment-section="review" ${reviewOpen?'open':''}><summary><span><strong>1. Duyệt người nói</strong><small>${esc(reviewStatus)}</small></span></summary><div class="assignment-section-body"><p class="section-guide">Xác định ai đang nói từng câu. Gemini chỉ đề xuất danh tính; bạn có thể chấp nhận, chỉnh sửa, nhóm quần chúng hoặc để lại xử lý sau.</p>${reviewBody}<div class="assignment-section-next"><button type="button" class="secondary" data-assignment-review-next>${esc(reviewNext)}</button></div></div></details>${voiceSection}<section class="assignment-preflight-step ${preflightReady?'is-ready':'is-blocked'}" data-assignment-preflight-step><div><strong>3. Kiểm tra sẵn sàng</strong><span>${preflightReady?(repairReturn?`Các điều kiện cho Chương ${context.fromChapter} đã hoàn tất.`:'Phạm vi đã sẵn sàng để mở kiểm tra sản xuất.'):'Bước này sẽ mở khi các blocker bắt buộc đã được xử lý.'}</span>${repairBlockerText}</div><button type="button" class="secondary" data-open-production-preflight ${preflightReady?'':'disabled'}>${esc(preflightLabel)}</button></section>`;
   blocked.classList.add('hidden');blocked.textContent='';
   rowsRoot.onfocusout=()=>window.setTimeout(applyDeferredSpeakerReviewUpdate,0);
@@ -1638,6 +1638,7 @@ function renderBookVoiceRegistryPage(context,registryState){
   rowsRoot.querySelector('[data-jump-to-speaker-review]')?.addEventListener('click',focusAssignmentReviewQueue);
   rowsRoot.querySelector('[data-prepare-speaker-analysis]')?.addEventListener('click',prepareRangeInputs);
   rowsRoot.querySelector('[data-assignment-review-next]')?.addEventListener('click',()=>speakerStatus==='ANALYSIS_REQUIRED'?prepareRangeInputs():reviewCount?focusAssignmentReviewQueue():openAssignmentVoiceSection());
+  rowsRoot.querySelector('[data-open-final-casting]')?.addEventListener('click',()=>navigateJourneyStage('confirm-casting'));
   rowsRoot.querySelector('[data-speaker-state-history]')?.addEventListener('toggle',event=>{const current=registryState.workflowSections||{};registryState.workflowSections={...current,history:event.currentTarget.open}});
   rowsRoot.querySelectorAll('[data-assignment-repair-focus]').forEach(control=>control.addEventListener('click',()=>{const section=rowsRoot.querySelector(`[data-assignment-section="${control.dataset.assignmentRepairFocus==='voices'?'voices':'review'}"]`);if(section)section.open=true;section?.scrollIntoView?.({block:'start',behavior:'smooth'});section?.querySelector('select,button,input,summary')?.focus?.({preventScroll:true})}));
   rowsRoot.querySelectorAll('[data-voice-blocker-link]').forEach(control=>control.addEventListener('click',()=>{const row=rowsRoot.querySelector(`[data-voice-library-row="${CSS.escape(control.dataset.voiceBlockerLink)}"]`);row?.scrollIntoView?.({block:'center',behavior:'smooth'});row?.querySelector('select,button')?.focus?.({preventScroll:true})}));

Return exactly READY or REPAIR: followed by one bounded repair brief. If no safe repair is possible, return NOT_READY with a reason.
