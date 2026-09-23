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

**Outcome:** For the selected Story Audio book and chapter range, the Owner can move through speaker review, voice assignment, save, and approval as one clear journey, with a truthful status and next action at each step.

**Acceptance:**

- While speaker decisions remain, show the remaining work and an action that reaches it. Once review is complete, show completion and a clear path into voice configuration; historical unresolved counts must not appear as a current blocker.
- Voice configuration shows the selected scope and any actual missing, unavailable, or conflicting voices. A blocker points to the action needed to clear it. The journey remains usable when there are no Gemini voice suggestions.
- After saving voice changes, show what was saved and whether voice-map approval is still required. After approval, show the next production action in the same scope without a dead end or a misleading “ready” state.
- Speaker approval, voice save, and voice-map approval do not silently PREPARE a Job or start render. PREPARE and START_RENDER remain separate explicit Owner actions.
- Verify the connected journey with isolated, offline evidence, including an incomplete review, completed review, a voice blocker, and successful voice approval. Preserve unrelated Story Audio behavior.

OWNER_INPUT_REQUIRED: no

Your previous completion report:
**Changed:** [ui/app.js](/D:/CADS-Benchmark/XP-003-AUTO-V2/arms/N1/ui/app.js) now shows a post-save status explaining that the final voice map still needs to be created and approved when the registry says creation is required. Otherwise, it directs the Owner to check production status for approval and the next action.

**Checks:** `node --check ui/app.js` and `git diff --check` passed. Of 22 registry and voice-map tests run, all passed. The speaker-review API test could not run because FastAPI is unavailable.

**Limits:** I did not run the connected browser journey: the available browser test creates temporary files outside this clone, which the brief forbids. So incomplete and completed review, blocker recovery, successful voice approval, and the absence of implicit PREPARE/render were not verified together in a browser. The post-save message also relies on the registry’s `requires_casting_plan_creation` flag; otherwise, it directs the Owner to production status rather than asserting approval is complete.

Current candidate tree: e506c861ba70c51cd734e14db555f161d4617136
Current diff:
diff --git a/ui/app.js b/ui/app.js
index 6838334..5bd22ef 100644
--- a/ui/app.js
+++ b/ui/app.js
@@ -1536,7 +1536,7 @@ function registryVoiceFieldId(row){return row?.role==='narrator'?'registry-voice
 function registryPersistedVoiceForScope(row,scopeChoice){if(scopeChoice==='book')return row.current_book_default_voice?.id||'';if(scopeChoice==='chapter')return row.chapter_override_voice?.id||row.effective_voice?.id||row.current_book_default_voice?.id||'';return row.range_override_voice?.id||row.effective_voice?.id||row.current_book_default_voice?.id||''}
 function registryDraftPending(row,context,draft=registryDraftForKey(row.speaker_key)){if(!draft||!Object.prototype.hasOwnProperty.call(draft,'voice'))return false;const scopeChoice=registryScopeChoice(context,row,draft);if(scopeChoice==='range'&&(row.conflict_voices||[]).length>1&&String(draft.voice||''))return true;return String(draft.voice||'')!==String(registryPersistedVoiceForScope(row,scopeChoice)||'')}
 function registryPendingVoiceChanges(context,registry=state.bookVoiceRegistry.result){return (registry?.rows||[]).filter(row=>row.role==='narrator'||row.character_id).map(row=>{const draft=registryDraftForKey(row.speaker_key),scope=registryScopeChoice(context,row,draft);return{row,draft,scope,voice:String(draft.voice||''),fromVoice:String(registryPersistedVoiceForScope(row,scope)||'')}}).filter(item=>registryDraftPending(item.row,context,item.draft))}
-function renderRegistryBatchSave(context,registry){const pending=registryPendingVoiceChanges(context,registry),busy=productionCommandBusy()||state.bookVoiceRegistry.batchSaving,invalid=pending.some(item=>!item.voice||!voiceSelectableForSave(item.voice)||(item.scope==='book'?!item.row.actions?.can_save_book_default:!item.row.actions?.can_create_range_or_chapter_override)),summary=pending.map(item=>`${item.row.display_name}: ${registryVoiceName(voiceCatalogItem(item.fromVoice)||{display_name:item.fromVoice||'Kế thừa'})} → ${registryVoiceName(voiceCatalogItem(item.voice)||{display_name:item.voice||'Chưa chọn'})} · ${item.scope==='book'?'Mặc định sách':item.scope==='chapter'?`Chương ${context.fromChapter}`:`Chương ${context.fromChapter}-${context.toChapter}`}`).join(' · ');return `<div class="assignment-batch-save ${pending.length?'has-changes':'is-clean'}" data-registry-batch-save role="status"><div><strong>${pending.length?`Có ${pending.length} thay đổi chưa lưu`:'Không có thay đổi chưa lưu'}</strong><span>${pending.length?esc(summary):'Các vai đang hiển thị đúng cấu hình đã lưu.'}</span>${state.bookVoiceRegistry.batchResult?`<small>${esc(state.bookVoiceRegistry.batchResult)}</small>`:''}</div><div class="assignment-row-actions"><button type="button" class="ghost" data-cancel-voice-batch ${pending.length&&!busy?'':'disabled'}>Hoàn tác tất cả</button><button type="button" class="primary" data-save-voice-batch ${pending.length&&!invalid&&runtimeAllowsMutation()&&!busy?'':'disabled'}>${state.bookVoiceRegistry.batchSaving?'Đang lưu nguyên khối…':`Lưu cấu hình cho ${pending.length} vai`}</button></div></div>`}
+function renderRegistryBatchSave(context,registry){const pending=registryPendingVoiceChanges(context,registry),busy=productionCommandBusy()||state.bookVoiceRegistry.batchSaving,invalid=pending.some(item=>!item.voice||!voiceSelectableForSave(item.voice)||(item.scope==='book'?!item.row.actions?.can_save_book_default:!item.row.actions?.can_create_range_or_chapter_override)),summary=pending.map(item=>`${item.row.display_name}: ${registryVoiceName(voiceCatalogItem(item.fromVoice)||{display_name:item.fromVoice||'Kế thừa'})} → ${registryVoiceName(voiceCatalogItem(item.voice)||{display_name:item.voice||'Chưa chọn'})} · ${item.scope==='book'?'Mặc định sách':item.scope==='chapter'?`Chương ${context.fromChapter}`:`Chương ${context.fromChapter}-${context.toChapter}`}`).join(' · ');const voiceMapApprovalRequired=(registry?.rows||[]).some(row=>(row.role==='narrator'||row.character_id)&&!!row.actions?.requires_casting_plan_creation),savedApprovalStatus=state.bookVoiceRegistry.batchResult&&!pending.length?`<small>${voiceMapApprovalRequired?'The final voice map still needs to be created and approved before PREPARE.':'Voice settings are saved. Check the production status for the final voice map approval and next action.'}</small>`:'';return `<div class="assignment-batch-save ${pending.length?'has-changes':'is-clean'}" data-registry-batch-save role="status"><div><strong>${pending.length?`Có ${pending.length} thay đổi chưa lưu`:'Không có thay đổi chưa lưu'}</strong><span>${pending.length?esc(summary):'Các vai đang hiển thị đúng cấu hình đã lưu.'}</span>${state.bookVoiceRegistry.batchResult?`<small>${esc(state.bookVoiceRegistry.batchResult)}</small>`:''}${savedApprovalStatus}</div><div class="assignment-row-actions"><button type="button" class="ghost" data-cancel-voice-batch ${pending.length&&!busy?'':'disabled'}>Hoàn tác tất cả</button><button type="button" class="primary" data-save-voice-batch ${pending.length&&!invalid&&runtimeAllowsMutation()&&!busy?'':'disabled'}>${state.bookVoiceRegistry.batchSaving?'Đang lưu nguyên khối…':`Lưu cấu hình cho ${pending.length} vai`}</button></div></div>`}
 function renderRegistryActionCell(row,context){const draft=registryDraftForKey(row.speaker_key),scopeChoice=registryScopeChoice(context,row,draft),scopeVoice=registryPersistedVoiceForScope(row,scopeChoice),selected=draft.voice??scopeVoice??'',busy=productionCommandBusy()||state.bookVoiceRegistry.batchSaving,scopedReady=!!row.actions?.can_create_range_or_chapter_override,bookReady=!!row.actions?.can_save_book_default,scopeReady=scopeChoice==='book'?bookReady:scopedReady,error=state.bookVoiceRegistry.rowErrors?.[row.speaker_key]||'',temporary=registryDraftPending(row,context,draft),guard=scopeChoice!=='book'&&!scopedReady?`<div class="assignment-voice-dependency" data-voice-save-guard="${esc(row.speaker_key)}"><strong>Chưa thể lưu giọng riêng vì bản xác định người nói chưa được duyệt.</strong><span>Duyệt người nói trước; sau đó thay đổi sẽ được gom vào một lần lưu ở cuối danh sách.</span></div>`:'',blockedAction=`<button type="button" class="primary small" data-registry-review-first="${esc(row.speaker_key)}" ${busy?'disabled':''}>Duyệt người nói trước</button>`;return `<div class="assignment-action-editor" data-registry-editor="${esc(row.speaker_key)}"><label>Phạm vi áp dụng<select data-registry-scope-key="${esc(row.speaker_key)}" ${busy?'disabled':''}>${registryScopeOptions(context,row,scopeChoice)}</select></label><label>Giọng sẽ dùng<select id="${esc(registryVoiceFieldId(row))}" data-registry-voice-key="${esc(row.speaker_key)}" ${busy?'disabled':''}>${registrySelectableVoiceOptions(selected)}</select></label><div class="assignment-voice-library-action"><button type="button" class="ghost small" data-registry-add-custom="${esc(row.speaker_key)}" ${busy?'disabled':''}>Thêm giọng custom</button><small>Tạo cho sách này rồi quay lại đúng vai; chưa tự lưu cấu hình.</small></div><strong class="assignment-unsaved-choice${temporary?'':' hidden'}">Chưa lưu — sẽ được gom vào lần lưu cuối</strong><div class="assignment-impact-summary" data-registry-impact="${esc(row.speaker_key)}">${esc(registryImpactSummary(row,context,draft))}</div>${guard}<div class="assignment-row-actions">${scopeReady?'':blockedAction}<button type="button" class="ghost small" data-registry-cancel="${esc(row.speaker_key)}" ${temporary&&!busy?'':'disabled'}>Hoàn tác lựa chọn</button></div>${scopeReady?'<small class="assignment-saving">Không lưu riêng từng vai; kiểm tra bảng tổng hợp ở cuối danh sách.</small>':''}${error?`<small class="assignment-row-error">${esc(error)}</small>`:''}${row.effective_voice?.preview_url?`<a class="text-action" href="${esc(row.effective_voice.preview_url)}" target="_blank" rel="noreferrer">Nghe thử giọng</a>`:''}</div>`}
 function openRegistryVoiceDetour(speakerKey){
   const context=currentProductionWorkingContext(),row=registryRowByKey(speakerKey),fieldId=registryVoiceFieldId(row);if(!context||!row||!window.StoryAudioVoiceDetour?.beginDetour)return;

R repair brief:
REPAIR: Complete the handoff for the selected Story Audio scope. The added message uses `requires_casting_plan_creation` to infer next steps, but that flag does not establish whether an existing voice map still needs approval, and the message gives no direct action. Show the authoritative blocker and an action that reaches voice-map creation or approval; show PREPARE as an explicit next action only after approval. Verify the connected journey offline for incomplete and completed speaker review, a voice blocker and its recovery, voice save, and approval. Confirm that review, save, and approval trigger neither PREPARE nor START_RENDER.

This is the sole repair. Work only in this disposable clone. No external or production effects. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report checks actually run and remaining limits.
