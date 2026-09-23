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

Candidate tree: 2d571089b068b5c7c0bc81f4540d876bf3903cb5
Candidate status:
M  ui/app.js
Candidate diff:
diff --git a/ui/app.js b/ui/app.js
index 6838334..92498d1 100644
--- a/ui/app.js
+++ b/ui/app.js
@@ -1617,7 +1617,7 @@ function renderBookVoiceRegistryPage(context,registryState){
   const unresolvedNotice=speakerStatus==='ANALYSIS_REQUIRED'?`<div class="assignment-unresolved-notice"><div><strong>Bản hiện tại cần tạo lại phân tích người nói.</strong><span>Không dùng Draft hoặc đề xuất duyệt cũ cho Revision ${esc(speakerState.current_revision_id)}.</span></div></div>`:reviewCount?`<div class="assignment-unresolved-notice"><div><strong>Còn ${reviewCount} câu chưa xác định người nói.</strong><span>Những câu này chỉ xuất hiện trong hàng đợi duyệt, không có bộ chọn giọng riêng.</span></div><button type="button" class="secondary" data-jump-to-speaker-review>Xem trong hàng đợi duyệt</button></div>`:'';
   const bookCharacterCount=Array.isArray(registry.characters)?registry.characters.length:0,narratorCount=voiceRows.filter(row=>row.role==='narrator').length,voiceSummary=`<div class="assignment-section-summary"><span><strong>${characterRows.length}</strong> nhân vật/nhóm có lời</span><span><strong>${narratorCount}</strong> người kể chuyện</span><span><strong>${voiceReady}</strong> vai có giọng</span><span><strong>${bookCharacterCount}</strong> nhân vật trong sách</span><span><strong>${voiceUnassigned.length}</strong> chưa có giọng</span><span><strong>${voiceBlockers.length}</strong> xung đột/không khả dụng</span></div>`;
   const rangeOverrideRecovery=renderRegistryRangeOverrideRecovery(context,registry),voiceBatch=renderGeminiVoiceBatch(context,registry),voiceTable=voiceRows.length?`<div class="assignment-registry-table-wrap" data-registry-scroll-region><table class="assignment-registry-table"><thead><tr><th colspan="4">Nhân vật, phạm vi và đoạn thoại để xác nhận</th><th>Thay đổi giọng</th></tr></thead><tbody>${[...voiceRows].sort((a,b)=>Number(registryVoiceNeedsAttention(b))-Number(registryVoiceNeedsAttention(a))).map(row=>renderRegistryTableRow(row,context)).join('')}</tbody></table></div>`:'<div class="assignment-empty-state"><strong>Chưa có Character hoặc nhóm đã xác định</strong><span>Hoàn tất bước duyệt người nói để tạo thư viện giọng cho phạm vi này.</span></div>',voiceSaveBar=renderRegistryBatchSave(context,registry);
-  const reviewNext=speakerStatus==='ANALYSIS_REQUIRED'?`Chuẩn bị phân tích ${reviewCount} câu`:reviewCount?`Tiếp tục xử lý ${reviewCount} câu còn lại`:'Tiếp tục cấu hình giọng',preflightLabel=repairReturn?'Quay lại chuẩn bị bản thay thế':'Tiếp tục: kiểm tra & chuẩn bị audio',voiceBlockerText=voiceBlockers.length?`<div class="issue warning"><strong>Giọng cần xử lý</strong>${voiceBlockers.map(row=>`<button type="button" class="text-action" data-voice-blocker-link="${esc(row.speaker_key)}">${esc(row.display_name)} · ${esc(registryStatusLabel(row.status))}</button>`).join('')}</div>`:'',repairBlockerText=repairContextBlockers.length?`<div class="issue warning"><strong>Điều kiện bản thay thế chưa hoàn tất</strong>${repairContextBlockers.map(item=>item.action_label?`<button type="button" class="text-action" data-assignment-repair-focus="${esc(item.assignment_focus||'review')}">${esc(item.title)}</button>`:`<span>${esc(item.title)}</span>`).join('')}</div>`:'';
+  const reviewNext=speakerStatus==='ANALYSIS_REQUIRED'?`Chuẩn bị phân tích ${reviewCount} câu`:reviewCount?`Tiếp tục xử lý ${reviewCount} câu còn lại`:'Tiếp tục cấu hình giọng',preflightLabel=repairReturn?'Quay lại chuẩn bị bản thay thế':'Tiếp tục: mở bước sản xuất',voiceBlockerText=voiceBlockers.length?`<div class="issue warning"><strong>Giọng cần xử lý</strong>${voiceBlockers.map(row=>`<button type="button" class="text-action" data-voice-blocker-link="${esc(row.speaker_key)}">${esc(row.display_name)} · ${esc(registryStatusLabel(row.status))}</button>`).join('')}</div>`:'',repairBlockerText=repairContextBlockers.length?`<div class="issue warning"><strong>Điều kiện bản thay thế chưa hoàn tất</strong>${repairContextBlockers.map(item=>item.action_label?`<button type="button" class="text-action" data-assignment-repair-focus="${esc(item.assignment_focus||'review')}">${esc(item.title)}</button>`:`<span>${esc(item.title)}</span>`).join('')}</div>`:'';
   const voiceSection=reviewBlocked?`<section class="assignment-workflow-section voice-section is-locked" data-assignment-section="voices" aria-disabled="true"><div class="assignment-locked-step"><span class="assignment-lock-icon" aria-hidden="true">2</span><div><strong>2. Cấu hình giọng</strong><small>${esc(voiceStatus)}</small><p>Còn <strong>${reviewCount}</strong> ${speakerStatus==='ANALYSIS_REQUIRED'?'câu cần phân tích hoặc xác định người nói':'quyết định người nói cần hoàn tất'}. Sau đó hệ thống sẽ tự mở danh sách Người kể chuyện và tất cả vai có lời để bạn cấu hình giọng một lần tại đây.</p></div><button type="button" class="secondary" data-jump-to-speaker-review>Tiếp tục Bước 1</button></div></section>`:`<details class="assignment-workflow-section voice-section ${voiceStepCurrent?'is-current':'is-complete'}" data-assignment-section="voices" ${voicesOpen?'open':''}><summary><span><strong>2. Vai có lời trong phạm vi và cấu hình giọng</strong><small>${esc(voiceStatus)}</small></span>${voiceSummary}</summary><div class="assignment-section-body"><p class="section-guide">Duyệt đề xuất giọng của Gemini tại đây, rồi chỉnh riêng từng vai nếu cần. Mỗi vai hiển thị nơi xuất hiện trong toàn bộ phạm vi đã chọn và phần còn thực sự được xử lý.</p>${voiceSummary}${rangeOverrideRecovery}${voiceBatch}${voiceTable}${voiceSaveBar}${voiceBlockerText}<div class="assignment-section-next ${preflightReady?'is-ready':'is-blocked'}">${preflightReady?`<button type="button" class="primary" data-open-production-preflight>${esc(preflightLabel)}</button>`:''}<span>${preflightReady?'Tất cả vai đang dùng giọng khả dụng.':pendingVoiceChanges.length?`Cần lưu ${pendingVoiceChanges.length} thay đổi đang chờ trước khi tiếp tục.`:castingCreationRows.length?'Cần lưu cấu hình giọng để tạo bản đồ giọng cuối cùng.':'Các điều kiện bản thay thế chưa hoàn tất.'}</span></div></div></details>`;
   rowsRoot.innerHTML=`<details class="assignment-workflow-section review-section ${reviewBlocked?'is-current':'is-complete'}" data-assignment-section="review" ${reviewOpen?'open':''}><summary><span><strong>1. Duyệt người nói</strong><small>${esc(reviewStatus)}</small></span></summary><div class="assignment-section-body"><p class="section-guide">Xác định ai đang nói từng câu. Gemini chỉ đề xuất danh tính; bạn có thể chấp nhận, chỉnh sửa, nhóm quần chúng hoặc để lại xử lý sau.</p>${reviewBody}<div class="assignment-section-next"><button type="button" class="secondary" data-assignment-review-next>${esc(reviewNext)}</button></div></div></details>${voiceSection}<section class="assignment-preflight-step ${preflightReady?'is-ready':'is-blocked'}" data-assignment-preflight-step><div><strong>3. Kiểm tra sẵn sàng</strong><span>${preflightReady?(repairReturn?`Các điều kiện cho Chương ${context.fromChapter} đã hoàn tất.`:'Phạm vi đã sẵn sàng để mở kiểm tra sản xuất.'):'Bước này sẽ mở khi các blocker bắt buộc đã được xử lý.'}</span>${repairBlockerText}</div><button type="button" class="secondary" data-open-production-preflight ${preflightReady?'':'disabled'}>${esc(preflightLabel)}</button></section>`;
   blocked.classList.add('hidden');blocked.textContent='';

Return exactly READY or REPAIR: followed by one bounded repair brief. If no safe repair is possible, return NOT_READY with a reason.
