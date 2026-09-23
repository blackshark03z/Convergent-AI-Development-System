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

**Outcome:** The Owner can select a story, prepare and review its speakers, configure and save voices, and see the next production action as one continuous journey.

**Acceptance:**

- For the selected chapter or range, the visible speaker status reflects work still required on the current text. Pending review leads to the review action. Completed review, including when historical unresolved items remain, is shown as complete; stale approval does not clear a current blocker.
- Completing speaker review or approval shows a clear result and a direct way into voice configuration for the same scope.
- Voice configuration identifies the narrator and speaking roles in scope. Unsaved choices and remaining blockers are visible. Each blocker leads to the action that can clear it, including missing or unavailable voices and any required final voice map review or approval. The journey must not present a disabled or ineffective action as its only way forward.
- After a successful voice save or approval, the refreshed status shows what was saved and the next available production action. An unsuccessful or uncertain result is not shown as complete. Saving or approving does not start PREPARE or render.
- Existing Story Audio behavior outside this journey remains intact. Verification uses local fixtures only; it does not call external providers or the canonical production runtime.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: An approved speaker draft with no Final Voice Map is presented as “Review Casting Plan,” but that action calls approval without a plan ID. Make the next action lead to creating the map, then offer map review and approval once it exists. The new success message and continuation button also persist when another draft is selected; show them only for the current approved draft and text revision. Verify both paths with local fixtures, including that approval exposes PREPARE without starting it.

I completion report:
Implemented the chapter-level handoff: speaker review approval is now reported separately from Final Voice Map creation, and the result includes a direct action to the matching voice setup or map review step. Saving/approval still does not start PREPARE or render.

Changed [ui/app.js](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-003/20260923T094959Z-0e1a1c3f/arms/N0/ui/app.js:1196), [ui/index.html](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-003/20260923T094959Z-0e1a1c3f/arms/N0/ui/index.html:1124), and [test_speaker_review_ui.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-003/20260923T094959Z-0e1a1c3f/arms/N0/tests/test_speaker_review_ui.py:176).

Checks: 61 focused tests passed; `node --check ui\app.js` and `git diff --check` passed. The fixture-backed browser run had 3 passes and 1 failure in an existing speaker correction result assertion (`correctionEvidence.result`); that assertion concerns a different handoff and was not changed here. The API test could not collect because FastAPI is not installed.

Product evidence is from the existing journey code and fixture-backed browser checks; I did not perform a visual preview of this specific new result state. Product acceptance is not claimed.
Repair report:
Implemented the repair in [ui/app.js](</C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-003/20260923T094959Z-0e1a1c3f/arms/N0/ui/app.js>) and added a regression assertion in [test_speaker_review_ui.py](</C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-003/20260923T094959Z-0e1a1c3f/arms/N0/tests/test_speaker_review_ui.py>).

“Review Casting Plan” now opens the voice-map workspace, where its review and approval controls are available. Speaker-review success messages and continuation buttons appear only when the selected draft ID and text revision match the approval result. An approved speaker draft can therefore continue to map creation; after the map exists, the journey offers map review and approval.

Checks passed: `python -m unittest tests.test_speaker_review_ui tests.test_production_workflow_browser` (18 tests), `node --check ui/app.js`, and `git diff --check`. The local browser fixtures cover the review and PREPARE-ready journey; PREPARE was not started. The route and stale-result behavior also have a regression assertion. This did not exercise both new branches end to end in a browser. No external providers or production runtime were used. Product acceptance is not claimed.

Candidate tree: 22a79696585edfabc343765a31f7c1855bb2815e
Candidate status:
M  tests/test_speaker_review_ui.py
M  ui/app.js
M  ui/index.html
Candidate diff:
diff --git a/tests/test_speaker_review_ui.py b/tests/test_speaker_review_ui.py
index 72e5d45..ad8112c 100644
--- a/tests/test_speaker_review_ui.py
+++ b/tests/test_speaker_review_ui.py
@@ -173,6 +173,18 @@ console.log(JSON.stringify({
         ):
             self.assertIn(value, self.html + self.js + self.css)
 
+    def test_speaker_review_result_distinguishes_approval_from_map_creation(self) -> None:
+        self.assertIn("kind:'speaker-review'", self.js)
+        self.assertIn("kind:'casting-plan'", self.js)
+        self.assertIn("The voice map has not been created yet.", self.js)
+        self.assertIn("speakerReviewContinueToVoice", self.html + self.js)
+        self.assertIn("?'confirm-casting':'voices'", self.js)
+
+    def test_voice_map_review_action_opens_review_and_hides_stale_speaker_result(self) -> None:
+        self.assertIn("if(action==='REVIEW_VOICE_MAP'||action==='REVIEW_CASTING_PLAN'){await openCasting();return}", self.js)
+        self.assertIn("approval.draft_id===draft.id&&approval.text_revision_id===draft.text_revision_id", self.js)
+        self.assertIn("$('#speakerReviewContinueToVoice').classList.add('hidden')", self.js)
+
     def test_voice_map_and_render_sections_remain_separate(self) -> None:
         for value in (
             "flowStepReviewVoiceMap",
diff --git a/ui/app.js b/ui/app.js
index 6838334..e78c1e3 100644
--- a/ui/app.js
+++ b/ui/app.js
@@ -538,7 +538,7 @@ async function runProductionPrimaryAction(vm=currentProductionViewModel()){
   if(action==='EDIT_VOICE_ASSIGNMENTS'||action==='ASSIGN_VOICE'){if(!state.casting)await openCasting();await saveProductionVoiceAssignments();return}
   if(action==='REVIEW_RANGE_VOICE_EXCEPTIONS'||action==='RESOLVE_VOICE_EXCEPTION'){await saveRangeVoiceException(vm);return}
   if(action==='APPROVE_RANGE_CASTING_PLANS'){await approveRangeCastingPlans(vm);return}
-  if(action==='REVIEW_VOICE_MAP'||action==='REVIEW_CASTING_PLAN'){await approveCastingPlan();return}
+  if(action==='REVIEW_VOICE_MAP'||action==='REVIEW_CASTING_PLAN'){await openCasting();return}
   if(action==='PREPARE_RANGE'){await prepareProductionScopeTask();return}
   if(action==='OPEN_JOB_RANGE'){const owner=vm?.render||{},bookId=Number(owner.book_id||state.productionRange?.bookId||0),from=Number(owner.from_chapter||0),to=Number(owner.to_chapter||0);if(!bookId||!from||!to){toast('Kh\u00f4ng x\u00e1c \u0111\u1ecbnh \u0111\u01b0\u1ee3c ph\u1ea1m vi c\u1ee7a Job hi\u1ec7n t\u1ea1i.',true);return}await restoreProductionRangeScope({bookId,fromChapter:from,toChapter:to,skipCompleted:false});return}
   if(action==='START_RENDER_RANGE'){await startProductionRangeRender();return}
@@ -1193,7 +1193,7 @@ function reviewChoiceValue(row,decision){if(!decision)return 'skip';if(decision.
 function reviewFilterMatch(row){const filter=$('#speakerReviewFilter').value,decision=state.speakerReview.decisions[row.utterance_id],level=row.invalid_item?'invalid':row.suggestion?.confidence_level;if(filter==='all')return true;if(filter==='unreviewed')return !row.reviewed&&!decision;if(filter==='invalid')return !!row.invalid_item;if(filter==='needs_review')return !!row.suggestion?.needs_review||!!row.invalid_item;return level===filter}
 function reviewRowElement(row){const s=row.suggestion,level=row.invalid_item?'invalid':s?.confidence_level||'invalid',current=row.current_assignment?speakerName(row.current_assignment.speaker_type,row.current_assignment.character_id):'None',suggestion=s?speakerName(s.speaker_type,s.character_id):'Unavailable',reason=s?.reason||row.invalid_item?.error_code||'No reason provided.',alternatives=(s?.alternatives||[]).map(item=>`${speakerName(item.speaker_type,item.character_id)} ${Math.round(item.confidence*100)}%`).join(' · ')||'None',root=document.createElement('div'),pending=!row.reviewed&&!state.speakerReview.decisions[row.utterance_id];root.className=`speaker-review-row${reviewFilterMatch(row)?'':' hidden-filter'}${row.reviewed?' reviewed':''}`;root.dataset.reviewRow=row.utterance_id;root.dataset.reviewPending=pending?'true':'false';const check=document.createElement('input');check.className='review-check';check.type='checkbox';check.dataset.reviewCheck=row.utterance_id;check.checked=!!state.speakerReview.selected?.[row.utterance_id];check.onchange=()=>setReviewSelection(row.utterance_id,check.checked);const seq=document.createElement('span');seq.className='utterance-seq';seq.textContent=row.sequence;const textBox=document.createElement('div'),id=document.createElement('strong'),text=document.createElement('p'),currentText=document.createElement('small'),reviewText=document.createElement('small');id.textContent=row.utterance_id;text.className='speaker-review-text';text.textContent=row.text;currentText.textContent=`Current: ${current}`;reviewText.textContent=row.human_review?`Reviewed: ${speakerName(row.human_review.speaker_type,row.human_review.character_id)}`:'Reviewed: no';textBox.append(id,text,currentText,reviewText);const suggestionBox=document.createElement('div'),suggestionName=document.createElement('strong'),confidence=document.createElement('span'),reasonText=document.createElement('span'),alternativesText=document.createElement('small');suggestionBox.className='speaker-review-suggestion';suggestionName.textContent=suggestion;confidence.className=`confidence-${level}`;confidence.textContent=`${level.toUpperCase()}${s?` · ${Math.round(s.confidence*100)}%`:''}`;reasonText.textContent=reason;alternativesText.textContent=`Alternatives: ${alternatives}`;suggestionBox.append(suggestionName,confidence,reasonText,alternativesText);const decisionBox=document.createElement('div'),label=document.createElement('label'),select=document.createElement('select'),save=document.createElement('button'),preview=document.createElement('button'),voice=document.createElement('span');decisionBox.className='speaker-review-decision';label.append('Review decision');select.dataset.reviewChoice=row.utterance_id;const selected=reviewChoiceValue(row,state.speakerReview.decisions[row.utterance_id]||row.human_review),choices=[['skip','Skip for now'],['narrator','Mark Narrator'],['unknown','Keep Unknown']];(state.speakerReview.draft.characters||[]).forEach(c=>choices.push([`character:${c.id}`,`Map to character: ${c.display_name}`]));choices.forEach(([value,name])=>select.add(new Option(name,value,false,value===selected)));select.onchange=()=>setSpeakerReviewChoice(row.utterance_id,select.value);label.append(select);save.className='secondary';save.textContent='Save row review';save.disabled=!runtimeAllowsMutation();save.onclick=()=>saveSpeakerReviewRow(row.utterance_id);preview.className='ghost';preview.textContent='Preview effective voice';preview.onclick=()=>previewReviewVoice(row.utterance_id);voice.id=`review-voice-${row.utterance_id}`;voice.className='review-voice-result';decisionBox.append(label,save,preview,voice);const details=document.createElement('details'),summary=document.createElement('summary'),contextList=document.createElement('div');details.className='speaker-context';summary.textContent='Context';contextList.className='speaker-context-list';(row.context||[]).forEach(item=>{const context=document.createElement('div');context.className=`speaker-context-item${item.is_target?' target':''}`;context.textContent=item.text;
     if(item.confirmed_assignment){const known=document.createElement('small');known.textContent=` · ${speakerName(item.confirmed_assignment.speaker_type,item.confirmed_assignment.character_id)}`;context.append(known)}contextList.append(context)});details.append(summary,contextList);root.append(check,seq,textBox,suggestionBox,decisionBox,details);return root}
-function renderSpeakerReview(){const review=state.speakerReview||{},draft=review.draft,items=review.drafts||[],existingPlan=!!state.casting?.casting?.id;$('#speakerDraftSelect').innerHTML=items.length?items.map(item=>`<option value="${item.id}" ${draft?.id===item.id?'selected':''}>Draft #${item.id}${item.stale?' · Outdated':''} · ${esc(item.status||'invalid')}</option>`).join(''):'<option value="">Chưa có draft</option>';$('#speakerReviewEmpty').classList.toggle('hidden',items.length>0);$('#speakerReviewWorkspace').classList.toggle('hidden',!draft);$('#speakerReviewPanel').classList.toggle('has-existing-plan',existingPlan);$('#speakerDraftExistingPlanWarning').classList.toggle('hidden',!existingPlan);$('#approveSpeakerReview').textContent=speakerDraftApprovalLabel();$('#regenerateSpeakerDraft').disabled=!runtimeAllowsMutation()||!draft||review.busy;$('#generateSpeakerDraft').disabled=!runtimeAllowsMutation()||!!review.busy;$('#refreshSpeakerDrafts').disabled=!!review.busy;if(!draft){$('#speakerReviewStatus').textContent='Chưa có draft';$('#speakerReviewMeta').innerHTML='';$('#speakerReviewRows').replaceChildren();$('#speakerReviewStale').classList.add('hidden');$('#speakerReviewApprovalResult').textContent='';return}$('#speakerReviewStatus').textContent=draft.stale?'Draft đã cũ':`${draft.status} · còn ${localRemainingUnreviewedCount(review)} mục`;const counts={high:0,medium:0,low:0,invalid:0};draft.review_rows.forEach(row=>{counts[row.invalid_item?'invalid':row.suggestion?.confidence_level||'invalid']++});$('#speakerReviewMeta').innerHTML=`<div><strong>#${draft.id}</strong><span>Draft</span></div><div><strong>${esc(draft.model_id)}</strong><span>${esc(draft.prompt_version)}</span></div><div><strong>${draft.target_count} / ${draft.valid_count} / ${draft.invalid_count}</strong><span>Target / valid / invalid</span></div><div><strong>${counts.high} / ${counts.medium} / ${counts.low} / ${counts.invalid}</strong><span>High / medium / low / invalid</span></div><div><strong>${esc(draft.input_fingerprint.slice(0,12))}</strong><span>Input fingerprint</span></div><div><strong>#${draft.text_revision_id}</strong><span>Text revision</span></div>${review.generation?`<div><strong>${review.generation.reused?'Reused':'Generated'}</strong><span>Cache ${review.generation.cache?.hit_count||0} hit / ${review.generation.cache?.miss_count||0} miss</span></div>`:''}`;$('#speakerReviewStale').textContent=(draft.stale_reasons||[]).join(' ');$('#speakerReviewStale').classList.toggle('hidden',!draft.stale);$('#speakerReviewApprovalResult').textContent=review.lastApproval?`Đã tạo Final Voice Map draft v${review.lastApproval.casting_plan_revision}. Hãy chuyển sang phần Bản đồ giọng cuối để kiểm tra và duyệt riêng.`:'';const rows=draft.review_rows.map(reviewRowElement);if(rows.length)$('#speakerReviewRows').replaceChildren(...rows);else{const empty=document.createElement('p');empty.className='muted';empty.textContent='Draft này không có mục nào cần rà soát.';$('#speakerReviewRows').replaceChildren(empty)}updateSpeakerReviewApproval()}
+function renderSpeakerReview(){const review=state.speakerReview||{},draft=review.draft,items=review.drafts||[],existingPlan=!!state.casting?.casting?.id;$('#speakerDraftSelect').innerHTML=items.length?items.map(item=>`<option value="${item.id}" ${draft?.id===item.id?'selected':''}>Draft #${item.id}${item.stale?' · Outdated':''} · ${esc(item.status||'invalid')}</option>`).join(''):'<option value="">Chưa có draft</option>';$('#speakerReviewEmpty').classList.toggle('hidden',items.length>0);$('#speakerReviewWorkspace').classList.toggle('hidden',!draft);$('#speakerReviewPanel').classList.toggle('has-existing-plan',existingPlan);$('#speakerDraftExistingPlanWarning').classList.toggle('hidden',!existingPlan);$('#approveSpeakerReview').textContent=speakerDraftApprovalLabel();$('#regenerateSpeakerDraft').disabled=!runtimeAllowsMutation()||!draft||review.busy;$('#generateSpeakerDraft').disabled=!runtimeAllowsMutation()||!!review.busy;$('#refreshSpeakerDrafts').disabled=!!review.busy;if(!draft){$('#speakerReviewStatus').textContent='Chưa có draft';$('#speakerReviewMeta').innerHTML='';$('#speakerReviewRows').replaceChildren();$('#speakerReviewStale').classList.add('hidden');$('#speakerReviewApprovalResult').textContent='';$('#speakerReviewContinueToVoice').classList.add('hidden');return}$('#speakerReviewStatus').textContent=draft.stale?'Draft đã cũ':`${draft.status} · còn ${localRemainingUnreviewedCount(review)} mục`;const counts={high:0,medium:0,low:0,invalid:0};draft.review_rows.forEach(row=>{counts[row.invalid_item?'invalid':row.suggestion?.confidence_level||'invalid']++});$('#speakerReviewMeta').innerHTML=`<div><strong>#${draft.id}</strong><span>Draft</span></div><div><strong>${esc(draft.model_id)}</strong><span>${esc(draft.prompt_version)}</span></div><div><strong>${draft.target_count} / ${draft.valid_count} / ${draft.invalid_count}</strong><span>Target / valid / invalid</span></div><div><strong>${counts.high} / ${counts.medium} / ${counts.low} / ${counts.invalid}</strong><span>High / medium / low / invalid</span></div><div><strong>${esc(draft.input_fingerprint.slice(0,12))}</strong><span>Input fingerprint</span></div><div><strong>#${draft.text_revision_id}</strong><span>Text revision</span></div>${review.generation?`<div><strong>${review.generation.reused?'Reused':'Generated'}</strong><span>Cache ${review.generation.cache?.hit_count||0} hit / ${review.generation.cache?.miss_count||0} miss</span></div>`:''}`;$('#speakerReviewStale').textContent=(draft.stale_reasons||[]).join(' ');$('#speakerReviewStale').classList.toggle('hidden',!draft.stale);const approval=review.lastApproval,approvalMatches=!!approval&&approval.draft_id===draft.id&&approval.text_revision_id===draft.text_revision_id,approvalResult=$('#speakerReviewApprovalResult'),continueToVoice=$('#speakerReviewContinueToVoice');if(approvalResult)approvalResult.textContent=approvalMatches&&approval.kind==='speaker-review'?'Speaker review approved for this chapter. The voice map has not been created yet.':approvalMatches&&approval.kind==='casting-plan'?`Final Voice Map draft v${approval.casting_plan_revision} created for this chapter.`:'';if(continueToVoice){continueToVoice.classList.toggle('hidden',!approvalMatches);continueToVoice.textContent=approval?.kind==='casting-plan'?'Review the Final Voice Map':'Continue to voice configuration'};const rows=draft.review_rows.map(reviewRowElement);if(rows.length)$('#speakerReviewRows').replaceChildren(...rows);else{const empty=document.createElement('p');empty.className='muted';empty.textContent='Draft này không có mục nào cần rà soát.';$('#speakerReviewRows').replaceChildren(empty)}updateSpeakerReviewApproval()}
 async function loadSpeakerDrafts(preferredId=null){const review=state.speakerReview;review.busy=true;renderSpeakerReview();try{const data=await api(`/api/chapters/${review.chapterId}/speaker-assignment/drafts`);review.drafts=data.items;const usable=data.items.find(item=>item.id===+preferredId)||data.items.find(item=>!item.stale&&!item.load_error)||data.items[0];if(usable&&!usable.load_error){review.draft=await api(`/api/chapters/${review.chapterId}/speaker-assignment/drafts/${usable.id}`);review.decisions={};review.selected={}}else review.draft=null}finally{review.busy=false;renderSpeakerReview();renderProductionShell()}}
 async function openSpeakerDraft(id){if(!id)return;try{state.speakerReview.draft=await api(`/api/chapters/${state.speakerReview.chapterId}/speaker-assignment/drafts/${id}`);state.speakerReview.decisions={};state.speakerReview.selected={};renderSpeakerReview()}catch(e){toast(e.message,true)}}
 async function generateSpeakerDraft(force=false){if(!runtimeAllowsMutation()){toast('Runtime identity must be resolved before mutating actions.',true);return}const review=state.speakerReview,mode=force?'reanalyze':'unassigned_only',envelope=await runProductionCommand({commandType:'CREATE_SPEAKER_PROPOSAL',scope:chapterProductionCommandScope(review.chapterId),payload:{chapter_id:Number(review.chapterId),mode,utterance_ids:null,force_refresh:force},label:'Đang tạo đề xuất người nói…'}),item=envelope?.applied_items?.[0];if(item?.draft_id)await loadSpeakerDrafts(item.draft_id)}
@@ -1208,8 +1208,8 @@ async function reviewIdempotencyKey(draft,decisions){const stable=JSON.stringify
 function rowReviewPayload(decision){if(!decision)return null;if(decision.speaker_type==='narrator')return {decision:'MARK_NARRATOR'};if(decision.speaker_type==='unknown')return {decision:'KEEP_UNKNOWN'};if(decision.speaker_type==='character')return {decision:'MAP_TO_EXISTING_CHARACTER',character_id:decision.character_id};return null}
 function savedReviewDecisions(draft){return (draft.row_reviews||[]).map(item=>({utterance_id:item.utterance_id,speaker_type:item.speaker_type,character_id:item.character_id,decision_source:item.decision_source}))}
 async function saveSpeakerReviewRow(utteranceId){if(!runtimeAllowsMutation()){toast('Runtime identity must be resolved before mutating actions.',true);return}const review=state.speakerReview,draft=review.draft,decision=review.decisions[utteranceId],payload=rowReviewPayload(decision);if(!payload){toast('Row review supports Narrator, Keep Unknown, or map to an existing character.',true);return}const envelope=await runProductionCommand({commandType:'SAVE_SPEAKER_DECISION',scope:chapterProductionCommandScope(review.chapterId),payload:{chapter_id:Number(review.chapterId),draft_id:Number(draft.id),target_id:utteranceId,...payload},label:'Đang lưu xác nhận người nói…'});if(envelope?.outcome==='APPLIED'){delete review.decisions[utteranceId];await openSpeakerDraft(draft.id)}}
-async function approveSpeakerReview(){if(!runtimeAllowsMutation()){toast('Runtime identity must be resolved before mutating actions.',true);return}const review=state.speakerReview,draft=review.draft;if(!draft||draft.stale||!draftOnlyApprovalReady(review))return;const envelope=await runProductionCommand({commandType:'APPROVE_SPEAKER_DRAFT',scope:chapterProductionCommandScope(review.chapterId),payload:{chapter_id:Number(review.chapterId),draft_id:Number(draft.id)},label:'Đang duyệt người nói…'});if(envelope?.outcome==='APPLIED'){review.lastApproval=envelope;review.decisions={};await openSpeakerDraft(draft.id)}}
-async function createSpeakerReviewCastingPlan(){if(!runtimeAllowsMutation()){toast('Runtime identity must be resolved before mutating actions.',true);return}const review=state.speakerReview,draft=review.draft;if(!draft||draft.stale||!reviewReadyForCastingPlan(review))return;const decisions=savedReviewDecisions(draft),idempotency_key=await reviewIdempotencyKey(draft,decisions),payload={chapter_id:Number(review.chapterId),speaker_draft_id:draft.id,base_casting_plan_revision_id:draft.base_casting_plan_id,expected_draft_fingerprint:draft.input_fingerprint,expected_text_revision_id:draft.text_revision_id,decisions,idempotency_key},envelope=await runProductionCommand({commandType:'CREATE_CASTING_PLAN_DRAFT',scope:chapterProductionCommandScope(review.chapterId),payload,label:'Đang tạo bản nháp gán giọng…'});if(envelope?.outcome==='APPLIED'){review.lastApproval=envelope;await openCasting()}}
+async function approveSpeakerReview(){if(!runtimeAllowsMutation()){toast('Runtime identity must be resolved before mutating actions.',true);return}const review=state.speakerReview,draft=review.draft;if(!draft||draft.stale||!draftOnlyApprovalReady(review))return;const envelope=await runProductionCommand({commandType:'APPROVE_SPEAKER_DRAFT',scope:chapterProductionCommandScope(review.chapterId),payload:{chapter_id:Number(review.chapterId),draft_id:Number(draft.id)},label:'Đang duyệt người nói…'});if(envelope?.outcome==='APPLIED'){review.lastApproval={...envelope,kind:'speaker-review',draft_id:draft.id,text_revision_id:draft.text_revision_id};review.decisions={};await openSpeakerDraft(draft.id)}}
+async function createSpeakerReviewCastingPlan(){if(!runtimeAllowsMutation()){toast('Runtime identity must be resolved before mutating actions.',true);return}const review=state.speakerReview,draft=review.draft;if(!draft||draft.stale||!reviewReadyForCastingPlan(review))return;const decisions=savedReviewDecisions(draft),idempotency_key=await reviewIdempotencyKey(draft,decisions),payload={chapter_id:Number(review.chapterId),speaker_draft_id:draft.id,base_casting_plan_revision_id:draft.base_casting_plan_id,expected_draft_fingerprint:draft.input_fingerprint,expected_text_revision_id:draft.text_revision_id,decisions,idempotency_key},envelope=await runProductionCommand({commandType:'CREATE_CASTING_PLAN_DRAFT',scope:chapterProductionCommandScope(review.chapterId),payload,label:'Đang tạo bản nháp gán giọng…'});if(envelope?.outcome==='APPLIED'){review.lastApproval={...envelope,kind:'casting-plan',draft_id:draft.id,text_revision_id:draft.text_revision_id};await openCasting()}}
 function utteranceResolution(u){if(u.resolution_source)return {resolved_voice_id:u.resolved_voice_id,resolution_source:u.resolution_source,gender:u.resolved_gender,needs_review:u.needs_review};if(u.role==='character')return state.casting.characters.find(c=>c.id===u.character_id)?.effective_resolution||null;if(u.role==='unknown')return state.casting.voice_profile?.unknown_resolution||null;return state.casting.voice_profile?.narrator_resolution||null}
 function optionSet(values,selected){return values.map(v=>`<option value="${esc(v)}" ${v===selected?'selected':''}>${esc(v||'none')}</option>`).join('')}
 function characterAliases(c){return (c.aliases||[]).length?`<div class="alias-list">${c.aliases.map(a=>`<span class="alias-chip" title="${esc(a)}">${esc(a)}</span>`).join('')}</div>`:'<div class="muted small">No aliases</div>'}
@@ -2051,7 +2051,7 @@ $('#reviewClearSelection').onclick=clearSelectedReviewRows;
 $('#jumpToPendingReview').onclick=jumpToPendingReview;
 $('#jumpToApprovalControls').onclick=jumpToApprovalControls;
 $('#approveSpeakerReview').onclick=approveSpeakerReview;
-$('#createSpeakerReviewCastingPlan').onclick=createSpeakerReviewCastingPlan;
+$('#createSpeakerReviewCastingPlan').onclick=createSpeakerReviewCastingPlan;$('#speakerReviewContinueToVoice').onclick=()=>navigateJourneyStage(state.speakerReview?.lastApproval?.kind==='casting-plan'?'confirm-casting':'voices');
 $('#loadTextDiff').onclick=loadTextDiff;
 document.querySelectorAll('[data-diff-preset]').forEach(button=>button.onclick=()=>setDiffPreset(...button.dataset.diffPreset.split(',')));
 $('#diffInlineMode').onclick=()=>{state.diffMode='inline';renderTextDiff()};
diff --git a/ui/index.html b/ui/index.html
index cd6990c..5298fd7 100644
--- a/ui/index.html
+++ b/ui/index.html
@@ -1121,7 +1121,8 @@
                   <button id="approveSpeakerReview" class="primary" disabled data-runtime-mutation-control>Duyệt Speaker Draft</button>
                   <button id="createSpeakerReviewCastingPlan" class="secondary" disabled data-runtime-mutation-control>Tạo Final Voice Map draft</button>
                 </div>
-                <div id="speakerReviewApprovalResult" class="muted"></div>
+                <div id="speakerReviewApprovalResult" class="muted" role="status" aria-live="polite"></div>
+                <button id="speakerReviewContinueToVoice" class="secondary hidden" type="button">Continue to voice configuration</button>
               </div>
             </section>
           </details>

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
