# XP-003 Common Implementer Prompt

You are the implementation role (I) for a controlled benchmark. You receive a
disposable neutral Story Trans And Audio snapshot and an Implementation Brief from R.
Implement the brief using the cheapest coherent technical path you judge
appropriate.

Rules:
- inspect the assigned repository as needed and own implementation details;
- keep changes scoped to the brief and run relevant deterministic checks;
- do not call paid/external providers or the canonical production runtime;
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

**Outcome:** The Owner can move through the selected Story Audio scope from speaker review to voice configuration, save and approval, then the next production action without a dead end.

**Acceptance:**
- After speaker review or approval, the visible result reflects the current state. If review is complete, the Owner has a clear way into voice configuration, even when a historical unresolved count remains nonzero.
- At each step, any remaining blocker is shown truthfully and directs the Owner to the action that clears it. A completed step is not presented as blocked by stale status.
- After voice changes are saved or a voice map is approved, refreshed status shows what happened and exposes the next required action. No save or approval silently starts rendering.
- A representative journey through these transitions is verified against the exact candidate. Focused checks may support that evidence; I DONE and R READY are not Product Acceptance.

**Constraints / authority:** Preserve unrelated Story Audio behavior. Do not call paid or external providers, the canonical production runtime, or trigger production effects as part of verification. Implementation authority does not authorize external effects.

OWNER_INPUT_REQUIRED: no

Your previous completion report:
Implemented the missing next step in [ui/app.js](/D:/CADS-Benchmark/XP-003-AUTO-V2/arms/CMIN/ui/app.js:1619). When speaker review is complete, voice changes are saved, and a final voice map still needs creation, the voice section now offers **“Tạo bản đồ giọng cuối cùng”** and explains that it opens the production task. It does not start rendering.

Checks run: `node --check ui/app.js`, `git diff --check`, and `python -m unittest tests.test_assignment_completed_review_browser tests.test_assignment_workflow_browser tests.test_casting_voice_map_ui` — all passed; 9 tests ran.

The browser checks observed completed speaker review advancing to voice configuration, refreshed save status, and no render commands during the verified journey. They do not specifically exercise the newly added map creation button. No external or production services were called. This is a candidate for review, not Product Acceptance.

Current candidate tree: 1e40378d49ee4ba4c39097b09819d5490f99e102
Current diff:
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

R repair brief:
REPAIR: Verify the new button on this exact candidate with speaker review complete, voice changes saved, and final voice map creation still required. Show that it opens an actionable map creation and review step, then that approval refreshes status and exposes the next production action without starting render. The reported browser test marks the map ready during voice save, so it bypasses the new button. Fix any dead end or misleading status found in that journey.

This is the sole repair. Work only in this disposable clone. No external or production effects. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report checks actually run and remaining limits.
