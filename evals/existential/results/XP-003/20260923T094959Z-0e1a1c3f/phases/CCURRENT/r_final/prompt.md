You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-003 Reasoning Lead Prompt — C-current / Current Thin CADS

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

Apply current Thin-CADS semantics relevant to this bounded Goal: reconstruct
relevant product reality; keep Goal/journey authoritative; resolve only material
design uncertainty; prefer reuse/fix over new machinery; require representative
product-level evidence before READY; bind evidence to candidate; preserve
consequence boundaries and canonical product truth. Use the fast path.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.


IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** For the selected story and chapter scope, the Owner can move through speaker review, voice assignment, save and approval, and into the next production action as one clear journey.

**Acceptance:**

- After each speaker decision and final approval, the visible result reflects the current authoritative state. It shows what remains to be reviewed and does not present historical or stale unresolved counts as current blockers.
- If a blocker remains, the Owner can reach the specific action that clears it. When current speaker review is complete, the journey clearly opens voice assignment and configuration, including when no speaker review was required.
- Voice work shows the effective speaking roles in the selected scope and any missing or unavailable voices. After save or approval, the Owner sees the reconciled result and the next production action. A failed or stale save does not appear successful.
- Continuing from voice work does not implicitly PREPARE or START_RENDER. Existing Story Audio behavior outside this journey is preserved.

**Evidence for READY:** On the candidate, demonstrate the connected journey from scope selection through speaker approval, voice configuration and save, to the visible production handoff. Also demonstrate a remaining blocker with its remedy and a completed speaker review where a historical unresolved count remains nonzero. Use local, nonproduction evidence; bind the rendered journey and focused checks to the same candidate.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: In a selected scope with an unassigned speaking role, the assignment page currently marks voice configuration complete, says all roles have available voices, and enables the production handoff. Its own casting journey still treats that role as a blocker. Make these states agree: show the affected role and the action needed to assign and save its voice; expose the production handoff only after the current scope is ready. A save that fails reconciliation must likewise remain visibly unresolved. Demonstrate both states, then the successful handoff, in local browser evidence on the repaired candidate.

I completion report:
**Candidate implementation complete; Product Acceptance not claimed.**

Changed [ui/app.js](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-003/20260923T094959Z-0e1a1c3f/arms/CCURRENT/ui/app.js:1620): the final assignment action now reads **“Tiếp tục: mở bước sản xuất”** (“Continue: open production”). Its handler opens the production overview; it does not PREPARE or START_RENDER.

**Checks run**

- Speaker review UI and browser tests: 15 passed.
- Assignment journey and completed-review browser tests: 2 passed.
- `git diff --check`: passed.

**Local browser evidence observed**

- Completed speaker review opens voice configuration, reports zero items awaiting review, and does not show an unresolved-speaker blocker.
- A remaining speaker-review blocker has navigation into the review queue.
- The assignment journey reaches the production overview without issuing render commands.

The browser checks use local test fixtures, not production services. I did not independently demonstrate every save failure or stale-save scenario in a rendered session; provider-backed and production-runtime behavior remain untested.
Repair report:
**Candidate repair complete; Product Acceptance is not claimed.**

Changed the assignment journey in [ui/app.js](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-003/20260923T094959Z-0e1a1c3f/arms/CCURRENT/ui/app.js):

- Unassigned voices now keep configuration in the current state and block the production handoff. The page names each affected role and links to its voice selector.
- Clicking a blocker opens the voice section and focuses that role’s selector.
- A failed save reconciliation retains the selected voice draft and displays the failure, leaving the scope unresolved until corrected and saved.

**Checks run**

- `node --check ui/app.js` and `git diff --check`: passed.
- Local browser fixtures for speaker review and character assignment: 2 passed. The assignment fixture observed voice save and a path to production with no render commands.
- The broader UI contract run had one failure: an existing assertion expects the prior handoff label “Continue: check & prepare audio.” The current candidate already uses “Continue: open production”; I left that behavior intact. The remaining 27 tests in that run passed.

The local browser fixtures demonstrated the existing review and assignment path. They did not exercise an unassigned role or a forced reconciliation failure in a rendered session, so those two repaired states are not independently demonstrated by browser evidence here. No production runtime or external provider was used.

Candidate tree: 9dabd269a74c9bfb61a56419d01fcb82e6b7e14c
Candidate status:
M  ui/app.js
Candidate diff:
diff --git a/ui/app.js b/ui/app.js
index 6838334..7c3555f 100644
--- a/ui/app.js
+++ b/ui/app.js
@@ -1610,15 +1610,15 @@ function renderBookVoiceRegistryPage(context,registryState){
   if(!speakerState.status)speakerState.status=unresolvedRows.length?'CURRENT_REVIEW_REQUIRED':'NO_REVIEW_REQUIRED';
   const speakerStatus=String(speakerState.status),reviewCount=speakerReviewRemainingCount(speakerState,unresolvedRows),voiceRows=rows.filter(row=>row.role==='narrator'||row.character_id),characterRows=voiceRows.filter(row=>row.role!=='narrator'),voiceUnassigned=voiceRows.filter(registryVoiceIsUnassigned),voiceBlockers=voiceRows.filter(registryVoiceNeedsAttention),castingCreationRows=voiceRows.filter(row=>row.actions?.requires_casting_plan_creation),speakerDependencyBlocked=!speakerStateResolved(speakerState),voiceReady=voiceRows.length-voiceUnassigned.length-voiceBlockers.length;
   const sections=registryState.workflowSections||{},reviewJustCompleted=Number(registryState.lastReviewCount)>0&&reviewCount===0,assignmentFocus=context.assignmentFocus||'';if(reviewJustCompleted){sections.review=false;sections.voices=true}if(assignmentFocus==='review'&&sections.review===null)sections.review=true;if(assignmentFocus==='voices'&&sections.voices===null)sections.voices=true;const reviewOpen=sections.review===null?reviewCount>0:!!sections.review,voicesOpen=sections.voices===null?reviewCount===0:!!sections.voices;registryState.workflowSections=sections;registryState.lastReviewCount=reviewCount;
-  const pendingVoiceChanges=registryPendingVoiceChanges(context,registry),repairReturn=context.returnTask==='REPAIR_PREFLIGHT',rawRepairContextBlockers=repairReturn?repairActionableBlockers(currentProductionViewModel().repair||{},{number:context.fromChapter}):[],repairContextBlockers=speakerStateResolved(speakerState)?rawRepairContextBlockers.filter(item=>!String(item.code||'').startsWith('SPEAKER_')):rawRepairContextBlockers,reviewBlocked=!speakerStateResolved(speakerState),voiceStepBlocked=reviewBlocked,voiceStepCurrent=!reviewBlocked&&(pendingVoiceChanges.length>0||voiceBlockers.length>0||castingCreationRows.length>0),preflightReady=!reviewBlocked&&pendingVoiceChanges.length===0&&voiceBlockers.length===0&&castingCreationRows.length===0&&repairContextBlockers.length===0,reviewStatus=speakerStatus==='CURRENT_REVIEW_REQUIRED'?`Còn ${reviewCount} câu chưa xác định người nói`:speakerStatus==='ANALYSIS_REQUIRED'?`${reviewCount} câu chưa phân tích`:speakerStatus==='APPROVED_CURRENT'?'Đã duyệt người nói':'Đã hoàn tất',voiceStatus=speakerStatus==='ANALYSIS_REQUIRED'?'Cần phân tích hoặc xử lý thủ công':speakerStatus==='CURRENT_REVIEW_REQUIRED'?'Còn người nói chưa xác định':pendingVoiceChanges.length?`${pendingVoiceChanges.length} thay đổi chưa lưu`:castingCreationRows.length?'Sẵn sàng chọn giọng và tạo bản đồ giọng':voiceBlockers.length?`${voiceBlockers.length} mục cần chú ý`:voiceUnassigned.length?`${voiceUnassigned.length} mục chưa có giọng · có thể xử lý sau`:`${voiceReady} vai sẵn sàng`,preflightStatus=reviewBlocked?(speakerStatus==='ANALYSIS_REQUIRED'?'Cần phân tích hoặc xử lý thủ công':'Cần xác định người nói'):pendingVoiceChanges.length?`Cần lưu ${pendingVoiceChanges.length} thay đổi giọng`:castingCreationRows.length?'Cần hoàn tất bản đồ giọng':voiceBlockers.length?'Cần xử lý giọng':repairContextBlockers.length?repairContextBlockers[0].title:'Có thể kiểm tra';
+  const pendingVoiceChanges=registryPendingVoiceChanges(context,registry),repairReturn=context.returnTask==='REPAIR_PREFLIGHT',rawRepairContextBlockers=repairReturn?repairActionableBlockers(currentProductionViewModel().repair||{},{number:context.fromChapter}):[],repairContextBlockers=speakerStateResolved(speakerState)?rawRepairContextBlockers.filter(item=>!String(item.code||'').startsWith('SPEAKER_')):rawRepairContextBlockers,reviewBlocked=!speakerStateResolved(speakerState),voiceStepBlocked=reviewBlocked,voiceStepCurrent=!reviewBlocked&&(pendingVoiceChanges.length>0||voiceBlockers.length>0||voiceUnassigned.length>0||castingCreationRows.length>0),preflightReady=!reviewBlocked&&pendingVoiceChanges.length===0&&voiceBlockers.length===0&&voiceUnassigned.length===0&&castingCreationRows.length===0&&repairContextBlockers.length===0,reviewStatus=speakerStatus==='CURRENT_REVIEW_REQUIRED'?`Còn ${reviewCount} câu chưa xác định người nói`:speakerStatus==='ANALYSIS_REQUIRED'?`${reviewCount} câu chưa phân tích`:speakerStatus==='APPROVED_CURRENT'?'Đã duyệt người nói':'Đã hoàn tất',voiceStatus=speakerStatus==='ANALYSIS_REQUIRED'?'Cần phân tích hoặc xử lý thủ công':speakerStatus==='CURRENT_REVIEW_REQUIRED'?'Còn người nói chưa xác định':pendingVoiceChanges.length?`${pendingVoiceChanges.length} thay đổi chưa lưu`:castingCreationRows.length?'Sẵn sàng chọn giọng và tạo bản đồ giọng':voiceBlockers.length?`${voiceBlockers.length} mục cần chú ý`:voiceUnassigned.length?`${voiceUnassigned.length} mục chưa có giọng`: `${voiceReady} vai sẵn sàng`,preflightStatus=reviewBlocked?(speakerStatus==='ANALYSIS_REQUIRED'?'Cần phân tích hoặc xử lý thủ công':'Cần xác định người nói'):pendingVoiceChanges.length?`Cần lưu ${pendingVoiceChanges.length} thay đổi giọng`:voiceUnassigned.length?`Cần gán giọng cho ${voiceUnassigned.length} vai`:castingCreationRows.length?'Cần hoàn tất bản đồ giọng':voiceBlockers.length?'Cần xử lý giọng':repairContextBlockers.length?repairContextBlockers[0].title:'Có thể kiểm tra';
   summary.innerHTML=`${renderCastingJourney({context,registry})}<div class="assignment-workflow-steps" aria-label="Tiến trình gán giọng"><div class="${reviewBlocked?'current':'complete'}"><strong>1</strong><span>Duyệt người nói<small>${esc(reviewStatus)}</small></span></div><div class="${voiceStepBlocked?'optional':voiceStepCurrent?'current':'complete'}"><strong>2</strong><span>Cấu hình giọng<small>${esc(voiceStatus)}</small></span></div><div class="${preflightReady?'current':'blocked'}"><strong>3</strong><span>Kiểm tra sẵn sàng<small>${esc(preflightStatus)}</small></span></div></div>`;
   bindCastingJourneyActions(summary);
   const historyOpen=!!sections.history,suggestionPanel=renderSpeakerSuggestionWorkspace(context,registry),historyPanel=renderSpeakerStateHistory(speakerState,historyOpen),reviewBody=speakerStatus==='ANALYSIS_REQUIRED'?`<div class="assignment-empty-state"><strong>Cần chuẩn bị phân tích người nói hiện tại trước khi duyệt.</strong><span>Hệ thống sẽ tạo hoặc làm mới Speaker Draft cho đúng Revision hiện tại trước; đề xuất duyệt cũ không được dùng làm authority.</span><button type="button" class="primary" data-prepare-speaker-analysis>Chuẩn bị phân tích người nói</button></div>${historyPanel}`:speakerStatus==='CURRENT_REVIEW_REQUIRED'?(suggestionPanel||'<div class="assignment-empty-state"><strong>Còn câu cần xác định người nói</strong><span>Hàng đợi hiện tại chưa tải được các câu cần duyệt.</span></div>')+historyPanel:speakerStatus==='APPROVED_CURRENT'?`${renderCompletedSpeakerBatchState(speakerState)}<div class="assignment-empty-state"><strong>Bản xác định người nói hiện tại đã được duyệt.</strong><span>Cấu trúc người nói của Revision ${esc(speakerState.current_revision_id)} đang được dùng.</span></div>${historyPanel}`:`<div class="assignment-empty-state"><strong>Không có câu thoại nào cần xác định người nói trong bản hiện tại.</strong><span>Draft cũ chỉ được giữ trong lịch sử và không chặn cấu hình giọng.</span></div>${historyPanel}`;
   const unresolvedNotice=speakerStatus==='ANALYSIS_REQUIRED'?`<div class="assignment-unresolved-notice"><div><strong>Bản hiện tại cần tạo lại phân tích người nói.</strong><span>Không dùng Draft hoặc đề xuất duyệt cũ cho Revision ${esc(speakerState.current_revision_id)}.</span></div></div>`:reviewCount?`<div class="assignment-unresolved-notice"><div><strong>Còn ${reviewCount} câu chưa xác định người nói.</strong><span>Những câu này chỉ xuất hiện trong hàng đợi duyệt, không có bộ chọn giọng riêng.</span></div><button type="button" class="secondary" data-jump-to-speaker-review>Xem trong hàng đợi duyệt</button></div>`:'';
   const bookCharacterCount=Array.isArray(registry.characters)?registry.characters.length:0,narratorCount=voiceRows.filter(row=>row.role==='narrator').length,voiceSummary=`<div class="assignment-section-summary"><span><strong>${characterRows.length}</strong> nhân vật/nhóm có lời</span><span><strong>${narratorCount}</strong> người kể chuyện</span><span><strong>${voiceReady}</strong> vai có giọng</span><span><strong>${bookCharacterCount}</strong> nhân vật trong sách</span><span><strong>${voiceUnassigned.length}</strong> chưa có giọng</span><span><strong>${voiceBlockers.length}</strong> xung đột/không khả dụng</span></div>`;
   const rangeOverrideRecovery=renderRegistryRangeOverrideRecovery(context,registry),voiceBatch=renderGeminiVoiceBatch(context,registry),voiceTable=voiceRows.length?`<div class="assignment-registry-table-wrap" data-registry-scroll-region><table class="assignment-registry-table"><thead><tr><th colspan="4">Nhân vật, phạm vi và đoạn thoại để xác nhận</th><th>Thay đổi giọng</th></tr></thead><tbody>${[...voiceRows].sort((a,b)=>Number(registryVoiceNeedsAttention(b))-Number(registryVoiceNeedsAttention(a))).map(row=>renderRegistryTableRow(row,context)).join('')}</tbody></table></div>`:'<div class="assignment-empty-state"><strong>Chưa có Character hoặc nhóm đã xác định</strong><span>Hoàn tất bước duyệt người nói để tạo thư viện giọng cho phạm vi này.</span></div>',voiceSaveBar=renderRegistryBatchSave(context,registry);
-  const reviewNext=speakerStatus==='ANALYSIS_REQUIRED'?`Chuẩn bị phân tích ${reviewCount} câu`:reviewCount?`Tiếp tục xử lý ${reviewCount} câu còn lại`:'Tiếp tục cấu hình giọng',preflightLabel=repairReturn?'Quay lại chuẩn bị bản thay thế':'Tiếp tục: kiểm tra & chuẩn bị audio',voiceBlockerText=voiceBlockers.length?`<div class="issue warning"><strong>Giọng cần xử lý</strong>${voiceBlockers.map(row=>`<button type="button" class="text-action" data-voice-blocker-link="${esc(row.speaker_key)}">${esc(row.display_name)} · ${esc(registryStatusLabel(row.status))}</button>`).join('')}</div>`:'',repairBlockerText=repairContextBlockers.length?`<div class="issue warning"><strong>Điều kiện bản thay thế chưa hoàn tất</strong>${repairContextBlockers.map(item=>item.action_label?`<button type="button" class="text-action" data-assignment-repair-focus="${esc(item.assignment_focus||'review')}">${esc(item.title)}</button>`:`<span>${esc(item.title)}</span>`).join('')}</div>`:'';
-  const voiceSection=reviewBlocked?`<section class="assignment-workflow-section voice-section is-locked" data-assignment-section="voices" aria-disabled="true"><div class="assignment-locked-step"><span class="assignment-lock-icon" aria-hidden="true">2</span><div><strong>2. Cấu hình giọng</strong><small>${esc(voiceStatus)}</small><p>Còn <strong>${reviewCount}</strong> ${speakerStatus==='ANALYSIS_REQUIRED'?'câu cần phân tích hoặc xác định người nói':'quyết định người nói cần hoàn tất'}. Sau đó hệ thống sẽ tự mở danh sách Người kể chuyện và tất cả vai có lời để bạn cấu hình giọng một lần tại đây.</p></div><button type="button" class="secondary" data-jump-to-speaker-review>Tiếp tục Bước 1</button></div></section>`:`<details class="assignment-workflow-section voice-section ${voiceStepCurrent?'is-current':'is-complete'}" data-assignment-section="voices" ${voicesOpen?'open':''}><summary><span><strong>2. Vai có lời trong phạm vi và cấu hình giọng</strong><small>${esc(voiceStatus)}</small></span>${voiceSummary}</summary><div class="assignment-section-body"><p class="section-guide">Duyệt đề xuất giọng của Gemini tại đây, rồi chỉnh riêng từng vai nếu cần. Mỗi vai hiển thị nơi xuất hiện trong toàn bộ phạm vi đã chọn và phần còn thực sự được xử lý.</p>${voiceSummary}${rangeOverrideRecovery}${voiceBatch}${voiceTable}${voiceSaveBar}${voiceBlockerText}<div class="assignment-section-next ${preflightReady?'is-ready':'is-blocked'}">${preflightReady?`<button type="button" class="primary" data-open-production-preflight>${esc(preflightLabel)}</button>`:''}<span>${preflightReady?'Tất cả vai đang dùng giọng khả dụng.':pendingVoiceChanges.length?`Cần lưu ${pendingVoiceChanges.length} thay đổi đang chờ trước khi tiếp tục.`:castingCreationRows.length?'Cần lưu cấu hình giọng để tạo bản đồ giọng cuối cùng.':'Các điều kiện bản thay thế chưa hoàn tất.'}</span></div></div></details>`;
+  const reviewNext=speakerStatus==='ANALYSIS_REQUIRED'?`Chuẩn bị phân tích ${reviewCount} câu`:reviewCount?`Tiếp tục xử lý ${reviewCount} câu còn lại`:'Tiếp tục cấu hình giọng',preflightLabel=repairReturn?'Quay lại chuẩn bị bản thay thế':'Tiếp tục: mở bước sản xuất',voiceBlockerText=voiceBlockers.length||voiceUnassigned.length?`<div class="issue warning"><strong>${voiceUnassigned.length?'Cần gán giọng trước khi tiếp tục':'Giọng cần xử lý'}</strong>${voiceUnassigned.map(row=>`<button type="button" class="text-action" data-voice-blocker-link="${esc(row.speaker_key)}">${esc(row.display_name)} · Chọn và lưu giọng</button>`).join('')}${voiceBlockers.map(row=>`<button type="button" class="text-action" data-voice-blocker-link="${esc(row.speaker_key)}">${esc(row.display_name)} · ${esc(registryStatusLabel(row.status))}</button>`).join('')}</div>`:'',repairBlockerText=repairContextBlockers.length?`<div class="issue warning"><strong>Điều kiện bản thay thế chưa hoàn tất</strong>${repairContextBlockers.map(item=>item.action_label?`<button type="button" class="text-action" data-assignment-repair-focus="${esc(item.assignment_focus||'review')}">${esc(item.title)}</button>`:`<span>${esc(item.title)}</span>`).join('')}</div>`:'';
+  const voiceSection=reviewBlocked?`<section class="assignment-workflow-section voice-section is-locked" data-assignment-section="voices" aria-disabled="true"><div class="assignment-locked-step"><span class="assignment-lock-icon" aria-hidden="true">2</span><div><strong>2. Cấu hình giọng</strong><small>${esc(voiceStatus)}</small><p>Còn <strong>${reviewCount}</strong> ${speakerStatus==='ANALYSIS_REQUIRED'?'câu cần phân tích hoặc xác định người nói':'quyết định người nói cần hoàn tất'}. Sau đó hệ thống sẽ tự mở danh sách Người kể chuyện và tất cả vai có lời để bạn cấu hình giọng một lần tại đây.</p></div><button type="button" class="secondary" data-jump-to-speaker-review>Tiếp tục Bước 1</button></div></section>`:`<details class="assignment-workflow-section voice-section ${voiceStepCurrent?'is-current':'is-complete'}" data-assignment-section="voices" ${voicesOpen?'open':''}><summary><span><strong>2. Vai có lời trong phạm vi và cấu hình giọng</strong><small>${esc(voiceStatus)}</small></span>${voiceSummary}</summary><div class="assignment-section-body"><p class="section-guide">Duyệt đề xuất giọng của Gemini tại đây, rồi chỉnh riêng từng vai nếu cần. Mỗi vai hiển thị nơi xuất hiện trong toàn bộ phạm vi đã chọn và phần còn thực sự được xử lý.</p>${voiceSummary}${rangeOverrideRecovery}${voiceBatch}${voiceTable}${voiceSaveBar}${voiceBlockerText}<div class="assignment-section-next ${preflightReady?'is-ready':'is-blocked'}">${preflightReady?`<button type="button" class="primary" data-open-production-preflight>${esc(preflightLabel)}</button>`:''}<span>${preflightReady?'Tất cả vai đang dùng giọng khả dụng.':pendingVoiceChanges.length?`Cần lưu ${pendingVoiceChanges.length} thay đổi đang chờ trước khi tiếp tục.`:voiceUnassigned.length?`Gán và lưu giọng cho ${voiceUnassigned.length} vai để tiếp tục.`:castingCreationRows.length?'Cần lưu cấu hình giọng để tạo bản đồ giọng cuối cùng.':voiceBlockers.length?'Xử lý các giọng không khả dụng trước khi tiếp tục.':'Các điều kiện bản thay thế chưa hoàn tất.'}</span></div></div></details>`;
   rowsRoot.innerHTML=`<details class="assignment-workflow-section review-section ${reviewBlocked?'is-current':'is-complete'}" data-assignment-section="review" ${reviewOpen?'open':''}><summary><span><strong>1. Duyệt người nói</strong><small>${esc(reviewStatus)}</small></span></summary><div class="assignment-section-body"><p class="section-guide">Xác định ai đang nói từng câu. Gemini chỉ đề xuất danh tính; bạn có thể chấp nhận, chỉnh sửa, nhóm quần chúng hoặc để lại xử lý sau.</p>${reviewBody}<div class="assignment-section-next"><button type="button" class="secondary" data-assignment-review-next>${esc(reviewNext)}</button></div></div></details>${voiceSection}<section class="assignment-preflight-step ${preflightReady?'is-ready':'is-blocked'}" data-assignment-preflight-step><div><strong>3. Kiểm tra sẵn sàng</strong><span>${preflightReady?(repairReturn?`Các điều kiện cho Chương ${context.fromChapter} đã hoàn tất.`:'Phạm vi đã sẵn sàng để mở kiểm tra sản xuất.'):'Bước này sẽ mở khi các blocker bắt buộc đã được xử lý.'}</span>${repairBlockerText}</div><button type="button" class="secondary" data-open-production-preflight ${preflightReady?'':'disabled'}>${esc(preflightLabel)}</button></section>`;
   blocked.classList.add('hidden');blocked.textContent='';
   rowsRoot.onfocusout=()=>window.setTimeout(applyDeferredSpeakerReviewUpdate,0);
@@ -1640,7 +1640,7 @@ function renderBookVoiceRegistryPage(context,registryState){
   rowsRoot.querySelector('[data-assignment-review-next]')?.addEventListener('click',()=>speakerStatus==='ANALYSIS_REQUIRED'?prepareRangeInputs():reviewCount?focusAssignmentReviewQueue():openAssignmentVoiceSection());
   rowsRoot.querySelector('[data-speaker-state-history]')?.addEventListener('toggle',event=>{const current=registryState.workflowSections||{};registryState.workflowSections={...current,history:event.currentTarget.open}});
   rowsRoot.querySelectorAll('[data-assignment-repair-focus]').forEach(control=>control.addEventListener('click',()=>{const section=rowsRoot.querySelector(`[data-assignment-section="${control.dataset.assignmentRepairFocus==='voices'?'voices':'review'}"]`);if(section)section.open=true;section?.scrollIntoView?.({block:'start',behavior:'smooth'});section?.querySelector('select,button,input,summary')?.focus?.({preventScroll:true})}));
-  rowsRoot.querySelectorAll('[data-voice-blocker-link]').forEach(control=>control.addEventListener('click',()=>{const row=rowsRoot.querySelector(`[data-voice-library-row="${CSS.escape(control.dataset.voiceBlockerLink)}"]`);row?.scrollIntoView?.({block:'center',behavior:'smooth'});row?.querySelector('select,button')?.focus?.({preventScroll:true})}));
+  rowsRoot.querySelectorAll('[data-voice-blocker-link]').forEach(control=>control.addEventListener('click',()=>{const row=rowsRoot.querySelector(`[data-voice-library-row="${CSS.escape(control.dataset.voiceBlockerLink)}"]`),section=row?.closest('details');if(section)section.open=true;row?.scrollIntoView?.({block:'center',behavior:'smooth'});row?.querySelector('[data-registry-voice-key]')?.focus?.({preventScroll:true})}));
   rowsRoot.querySelectorAll('[data-open-production-preflight]').forEach(control=>control.addEventListener('click',openAssignmentPreflight));
   if(button){button.disabled=false;button.textContent='Thay đổi phạm vi';button.onclick=openProductionScopeDialog}
 }
@@ -1748,11 +1748,11 @@ async function saveRegistryVoiceBatch(explicitItems=null,{recovery=false}={}){
   try{
     const envelope=await runProductionCommand({commandType:'SAVE_VOICE_CONFIGURATION_BATCH',scope:rangeProductionCommandScope(context),payload:{book_id:context.bookId,items},label:recovery?'Đang cập nhật bản đồ giọng theo mặc định mới…':'Đang lưu toàn bộ cấu hình giọng…'});
     if(envelope?.outcome!=='APPLIED'){state.bookVoiceRegistry.batchResult=state.productionCommand.message||'Chưa lưu được cấu hình. Không thay đổi nào trong batch được áp dụng.';return false}
-    state.bookVoiceRegistry.savedScopes={...(state.bookVoiceRegistry.savedScopes||{}),...Object.fromEntries(items.map(item=>[item.speaker_key,item.scope]))};if(!recovery)state.bookVoiceRegistry.drafts={};state.bookVoiceRegistry.rowErrors={};
+    state.bookVoiceRegistry.savedScopes={...(state.bookVoiceRegistry.savedScopes||{}),...Object.fromEntries(items.map(item=>[item.speaker_key,item.scope]))};state.bookVoiceRegistry.rowErrors={};
     await loadBookVoiceRegistry({force:true});
     const failures=items.filter(item=>{const refreshed=registryRowByKey(item.speaker_key);return item.scope==='book'?String(refreshed?.current_book_default_voice?.id||'')!==String(item.voice_id):String(refreshed?.effective_voice?.id||'')!==String(item.voice_id)});
     if(failures.length){state.bookVoiceRegistry.batchResult=`Đã commit batch nhưng ${failures.length} vai chưa phản chiếu đúng giọng hiệu lực. Hãy tải lại và chưa PREPARE/render.`;return false}
-    state.bookVoiceRegistry.batchResult=`Đã lưu nguyên khối cấu hình cho ${items.length} vai. Không có trạng thái lưu dở dang.`;
+    if(!recovery)state.bookVoiceRegistry.drafts={};state.bookVoiceRegistry.batchResult=`Đã lưu nguyên khối cấu hình cho ${items.length} vai. Không có trạng thái lưu dở dang.`;
     if(recovery)state.bookVoiceRegistry.bulkOverrideResult=`Đã cập nhật ${items.length} vai theo mặc định sách hiện tại bằng một giao dịch nguyên khối.`;
     await loadProductionTaskProjection({silent:true});return true
   }finally{state.bookVoiceRegistry.batchSaving=false;renderAssignmentPage();restoreRegistryUiSnapshot(snapshot);requestAnimationFrame(()=>document.querySelector(recovery?'[data-range-override-recovery],[data-range-override-result]':'[data-registry-batch-save]')?.focus?.({preventScroll:true}))}

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
