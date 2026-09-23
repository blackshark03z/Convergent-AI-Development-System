# XP-001 Common Implementer Prompt

You are the implementation role (I) for a controlled benchmark.

You receive:
1. a disposable neutral Story Audio repository snapshot; and
2. an Implementation Brief prepared by a Reasoning Lead.

Implement the brief using the cheapest coherent technical path you judge
appropriate.

Rules:
- inspect the repository as needed;
- own implementation details;
- keep changes scoped to the brief;
- run relevant existing deterministic/product/browser checks;
- do not search for historical/reference implementations;
- do not inspect sibling benchmark workspaces or results;
- do not try to discover hidden benchmark tests;
- do not weaken tests/acceptance surfaces merely to make the candidate pass;
- do not cross external/irreversible effect boundaries absent from the brief;
- do not ask for implementation preferences you can safely decide yourself;
- if a material product preference or authority decision is genuinely missing,
  stop and report the ambiguity rather than inventing it.

When finished, report:
- exact files/behavior changed;
- checks actually run and their results;
- product-level evidence you observed;
- known limitations/untested surfaces;
- any material assumption you had to make.

Do not claim Product Acceptance. Your output is a candidate for R review and
later hidden evaluation.


Original IMPLEMENTATION_BRIEF:
IMPLEMENTATION_BRIEF

**Outcome:** On Production, the current primary action is visible and reachable on a supported desktop layout, including a constrained-height viewport, without scrolling to find it.

**Acceptance:** In isolated browser fixtures at 1366×768 and 1366×600, load Production at the top of the page with a current task whose content is long, such as voice review or preflight. When the task has a primary action, its full button must be visible, unobscured, and clickable. It must remain easy to reach while reviewing the task content. Verify that the button still shows and performs the action for the current task, and that the layout has no horizontal overflow. Run the affected Production browser behavior against the exact candidate delivered.

**Constraints / authority:** Preserve the existing workflow, action gates, and behavior outside this layout correction. Use an isolated runtime and fixtures; do not invoke providers, the canonical runtime, PREPARE, START_RENDER, or Human QA. Implementation completion and reasoning review are not Owner product acceptance.

OWNER_INPUT_REQUIRED: no

Your previous completion report:
Implemented the Production layout correction in [ui/index.html](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-001/20260923T203651Z-bfe50ba6/arms/CMIN/ui/index.html), [ui/styles.css](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-001/20260923T203651Z-bfe50ba6/arms/CMIN/ui/styles.css), and [browser_production_task_workbench_smoke.mjs](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-001/20260923T203651Z-bfe50ba6/arms/CMIN/scripts/browser_production_task_workbench_smoke.mjs).

The current task’s primary action now appears before its variable review content and stays fixed in view on desktop, with space reserved below it. Existing button identity and workflow gates are preserved; compact layouts keep the action in the normal flow. The browser fixture covers a long voice task at 1366×768 and 1366×600.

**Checks:** the Production browser workflow passed; 34 task workbench and projection tests passed; `git diff --check` passed.

The browser fixture confirmed the action remained visible and unobscured at page top and while scrolling, with no horizontal overflow, and its click dispatched for the current `ASSIGN_VOICE` task. The constrained fixture stubs the action handler, so it does not perform a backend mutation. No provider, canonical runtime, PREPARE, START_RENDER, or Human QA action was invoked. This is implementation evidence, not Product Acceptance.

Current candidate tree: d8cc99f56a800d753de5ca151c34274ac9f275ab
Current diff:
diff --git a/scripts/browser_production_task_workbench_smoke.mjs b/scripts/browser_production_task_workbench_smoke.mjs
index 295d6a1..3f6fda9 100644
--- a/scripts/browser_production_task_workbench_smoke.mjs
+++ b/scripts/browser_production_task_workbench_smoke.mjs
@@ -157,7 +157,7 @@ try {
     const workspace=document.querySelector("#productionTaskWorkspace").getBoundingClientRect();
     const nested=[...document.querySelectorAll("#productionWorkbench *")].filter(element=>{const style=getComputedStyle(element);return /(auto|scroll)/.test(style.overflowY)&&element.scrollHeight>element.clientHeight+2}).map(element=>element.id||element.className);
     const primaryButton=document.querySelector("#productionPrimaryAction"),primaryRect=primaryButton.getBoundingClientRect(),contextRect=document.querySelector("#productionTaskContent").getBoundingClientRect();
-    return {state:document.querySelector("#productionStateCard").dataset.productionState,title:document.querySelector("#productionCurrentStepHeading").textContent,primary,primaryViewport:!primary.includes(primaryButton.textContent.trim())||primaryRect.top>=0&&primaryRect.bottom<=innerHeight,primaryAfterContext:primaryRect.top>=contextRect.bottom,body:document.querySelector("#productionTaskContent").innerText,queue:document.querySelectorAll(".production-queue-item").length,workspaceVisible:workspace.top>=0&&workspace.top<innerHeight,nested};
+    return {state:document.querySelector("#productionStateCard").dataset.productionState,title:document.querySelector("#productionCurrentStepHeading").textContent,primary,primaryViewport:!primary.includes(primaryButton.textContent.trim())||primaryRect.top>=0&&primaryRect.bottom<=innerHeight,primaryBeforeTaskContent:!!(document.querySelector("#productionPrimaryActions").compareDocumentPosition(document.querySelector("#productionTaskContent"))&Node.DOCUMENT_POSITION_FOLLOWING),body:document.querySelector("#productionTaskContent").innerText,queue:document.querySelectorAll(".production-queue-item").length,workspaceVisible:workspace.top>=0&&workspace.top<innerHeight,nested};
   })()`);
 
   const journeyA = await show({ rangeState: "CASTING_REVIEW" });
@@ -241,7 +241,7 @@ try {
   ];
   for (const [journey, label] of expected) {
     if (journey.primary.length !== 1 || journey.primary[0] !== label) throw new Error(`Primary action mismatch for ${label}: ${JSON.stringify(journey)}`);
-    if (!journey.primaryAfterContext) throw new Error(`Primary action did not follow its decision context: ${JSON.stringify(journey)}`);
+    if (!journey.primaryBeforeTaskContent) throw new Error(`Primary action did not precede variable task content: ${JSON.stringify(journey)}`);
     if (journey.nested.length) throw new Error(`Nested operational scroll found: ${JSON.stringify(journey.nested)}`);
   }
   if (prepareSkipCompleted.calls !== 1 || prepareSkipCompleted.scope?.skip_completed !== true || prepareSkipCompleted.scope?.from_chapter !== 6 || prepareSkipCompleted.scope?.to_chapter !== 8 || !prepareSkipCompleted.label?.includes('2 chương')) throw new Error(`Skip-completed PREPARE did not preserve owner scope: ${JSON.stringify(prepareSkipCompleted)}`);
@@ -281,13 +281,22 @@ try {
   await send("Emulation.setDeviceMetricsOverride", { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });
   const desktop = await evaluate(`(() => ({horizontal:document.documentElement.scrollWidth>innerWidth+1,primaryVisible:document.querySelector("#productionPrimaryAction").getBoundingClientRect().top<innerHeight}))()`);
   if (desktop.horizontal || !desktop.primaryVisible) throw new Error(`1920 layout failed: ${JSON.stringify(desktop)}`);
+  await show({ rangeState: "VOICE_BLOCKED" });
+  await evaluate(`(()=>{const content=document.querySelector('#productionTaskContent');window.__longTaskBody=content.innerHTML;window.__primaryActionFn=runProductionPrimaryAction;window.__primaryTask=currentProductionViewModel()?.task_type||currentProductionViewModel()?.journey_state||null;content.innerHTML='<div style="height:1800px">'+Array.from({length:30},(_,i)=>'<p>Long voice review and preflight fixture content '+i+'</p>').join('')+'</div>';runProductionPrimaryAction=async current=>{window.__primaryInvoked=current?.task_type||current?.journey_state||null};return true})()`);
+  const constrainedPrimary=[];
+  for (const height of [768, 600]) {
+    await send("Emulation.setDeviceMetricsOverride", { width: 1366, height, deviceScaleFactor: 1, mobile: false });
+    constrainedPrimary.push(await evaluate(`(async()=>{await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));const button=document.querySelector('#productionPrimaryAction'),content=document.querySelector('#productionTaskContent'),initial=button.getBoundingClientRect(),initialVisible=initial.top>=0&&initial.bottom<=innerHeight;window.scrollTo(0,content.getBoundingClientRect().top+300);await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));const rect=button.getBoundingClientRect(),center=document.elementFromPoint(rect.left+rect.width/2,rect.top+rect.height/2),layout={height:${height},initialVisible,reviewVisible:rect.top>=0&&rect.bottom<=innerHeight,unobscured:center===button||button.contains(center),horizontal:document.documentElement.scrollWidth>innerWidth+1,task:window.__primaryTask,rect:{top:Math.round(rect.top),bottom:Math.round(rect.bottom)}};button.click();layout.invoked=window.__primaryInvoked===layout.task;window.scrollTo(0,0);return layout})()`));
+  }
+  await evaluate(`(()=>{runProductionPrimaryAction=window.__primaryActionFn;document.querySelector('#productionTaskContent').innerHTML=window.__longTaskBody;return true})()`);
+  if (constrainedPrimary.some(layout=>layout.task!=="ASSIGN_VOICE"||!layout.initialVisible||!layout.reviewVisible||!layout.unobscured||layout.horizontal||!layout.invoked)) throw new Error(`Constrained Production primary action failed: ${JSON.stringify(constrainedPrimary)}`);
   await evaluate(`(()=>{loadProductionTaskProjection=window.__v2dProductionProjectionLoader;const savedApi=api,counts={projection:0,preflight:0};api=async(path,options)=>{const value=String(path);if(value.startsWith('/api/production/task-projection'))counts.projection+=1;if(value.startsWith('/api/production/preflight'))counts.preflight+=1;return savedApi(path,options)};state.book={id:91,title:'Sách kiểm thử cô lập'};state.productionRange={bookId:91,fromChapter:401,toChapter:401,chapterId:9101,skipCompleted:false};setAppRoute('assignment');window.__v2dInactivePolling={counts,savedApi};return true})()`);
   await evaluate(`loadJobs()`);
   const inactiveProjectionPolling = await evaluate(`(()=>{const audit=window.__v2dInactivePolling,result={...audit.counts,route:state.currentRoute};api=audit.savedApi;return result})()`);
   if (inactiveProjectionPolling.route !== "assignment" || inactiveProjectionPolling.projection !== 0 || inactiveProjectionPolling.preflight !== 0) throw new Error(`Inactive view requested Production state: ${JSON.stringify(inactiveProjectionPolling)}`);
   if (browserErrors.length) throw new Error(`Browser errors: ${browserErrors.join(" | ")}`);
 
-  process.stdout.write(JSON.stringify({ ok: true, journeyA, journeyB, journeyC, pollingStability, journeyDEdit, journeyDReview, journeyEPrepare, journeyInfrastructure, voiceReturnLayout1366, voiceReturnLayout520, voiceReturn, journeyEStart, preparedEditCancel, journeyEStartBlocked, journeyERunning, monitorJobsNavigation, jobsRecoveryActions, jobsRecoveryVariants, journeyF, journeyG, qaHandoff, journeyH, commandLifecycle, qaCommandReconcile, rangeCommandContinuity, inspectionBC, prepareSkipCompleted, nullPrimaryMappings, malformedSafe, scopeAction1366, scopeAction820, desktop, inactiveProjectionPolling, returnToProduction }));
+  process.stdout.write(JSON.stringify({ ok: true, journeyA, journeyB, journeyC, pollingStability, journeyDEdit, journeyDReview, journeyEPrepare, journeyInfrastructure, voiceReturnLayout1366, voiceReturnLayout520, voiceReturn, journeyEStart, preparedEditCancel, journeyEStartBlocked, journeyERunning, monitorJobsNavigation, jobsRecoveryActions, jobsRecoveryVariants, journeyF, journeyG, qaHandoff, journeyH, commandLifecycle, qaCommandReconcile, rangeCommandContinuity, inspectionBC, prepareSkipCompleted, nullPrimaryMappings, malformedSafe, scopeAction1366, scopeAction820, desktop, constrainedPrimary, inactiveProjectionPolling, returnToProduction }));
 } finally {
   try { socket?.close(); } catch {}
   const browserExited = new Promise(resolve => {
diff --git a/ui/index.html b/ui/index.html
index 97c96b8..0b3585a 100644
--- a/ui/index.html
+++ b/ui/index.html
@@ -173,11 +173,11 @@
               <p id="productionStateExplanation" class="production-task-summary">Hãy chọn sách và chương để xem việc cần làm tiếp theo.</p>
               <p id="productionBlockerReason" class="issue warning hidden"></p>
               <section id="productionCommandStatus" class="production-command-status hidden" aria-live="polite"></section>
-              <section id="productionTaskContent" class="production-task-content" aria-label="Nội dung việc hiện tại"></section>
               <div id="productionPrimaryActions" class="production-primary-actions">
                 <button id="productionBackToVoices" class="secondary hidden" type="button">Quay lại cấu hình giọng</button>
                 <button id="productionPrimaryAction" class="primary dominant-production-action" type="button" aria-label="Chọn chương">Chọn chương</button>
               </div>
+              <section id="productionTaskContent" class="production-task-content" aria-label="Nội dung việc hiện tại"></section>
               <section id="productionPhaseWorkspace" class="production-phase-workspace hidden" aria-label="Công cụ của việc hiện tại"></section>
               <div id="productionQaActions" class="production-qa-actions hidden" aria-label="Kết luận nghe duyệt">
                 <button id="productionQaNeedsFixes" class="secondary" type="button">Cần sửa</button>
diff --git a/ui/styles.css b/ui/styles.css
index 28693e4..38514eb 100644
--- a/ui/styles.css
+++ b/ui/styles.css
@@ -158,9 +158,9 @@ main{max-width:1240px;margin:18px auto;padding:0 20px 50px}.app-view{animation:n
 .production-progress-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.production-progress-summary>div{display:grid;gap:2px;padding:11px;background:#f5f9f6;border-radius:9px}.production-progress-summary strong{font-size:19px}.production-progress-summary span{font-size:11px;color:var(--muted)}.production-qa-player{padding:10px;background:#f5f9f6;border-radius:9px}.production-qa-player audio{width:100%}.production-qa-note-label{display:grid;gap:5px;font-size:13px;font-weight:800}.production-qa-actions,.production-primary-actions,.production-secondary-links{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:16px}.production-primary-actions{justify-content:flex-end;margin:0 0 16px}.production-primary-actions .dominant-production-action{min-width:210px}.production-secondary-links{font-size:13px}.production-next-hint{margin:13px 0 0;font-size:12px;color:var(--muted)}.production-technical-details{margin-top:12px;border-top:1px solid #e4e9e4;padding-top:10px}.production-technical-details summary{cursor:pointer;font-size:12px;color:#527060;font-weight:800}.production-technical-details>div{margin-top:8px;font-size:12px}.production-task-workspace .production-stage-summaries{display:none}.production-task-workspace .production-phase-workspace,.production-task-workspace .production-stage-isolation{display:none!important}.production-workbench-shell #productionChangeScope{white-space:nowrap}.production-queue-collapsed .production-task-queue{display:none}.production-queue-collapsed .production-workbench{grid-template-columns:1fr}
 .production-render-progress{display:grid;gap:10px;padding:14px;border:1px solid #d9e4dc;border-radius:12px;background:#fbfdfb}.production-render-progress.is-stalled{border-color:#c58a2e;background:#fff8e8}.production-render-phase{margin:0;font-weight:800;color:#235a40}.production-render-progress>strong{font-size:16px}.production-render-progress .progress{margin:0}.production-render-progress button{justify-self:start}
 .production-operator-key{display:grid;gap:5px;max-width:420px;font-size:13px;font-weight:800}
-.production-primary-actions{position:sticky;top:8px;z-index:3;padding:6px 0;background:linear-gradient(90deg,#fff 78%,rgba(255,255,255,.92))}
+.production-primary-actions{position:fixed;right:max(22px,calc((100vw - 1380px)/2 + 22px));bottom:12px;z-index:8;justify-content:flex-end;min-height:58px;margin:0;padding:8px 12px;border:1px solid #dce5de;border-radius:12px;background:rgba(255,255,255,.97);box-shadow:0 8px 28px rgba(23,59,44,.18);backdrop-filter:blur(8px)}.production-task-card{padding-bottom:82px}
 @media(max-width:1100px){.production-stage-strip{grid-template-columns:repeat(6,minmax(120px,1fr));overflow:auto}.production-stage-strip li{min-width:150px}.production-workbench{grid-template-columns:260px minmax(0,1fr)}}
-@media(max-width:900px){.production-range-context{grid-template-columns:1fr auto}.production-range-progress{grid-column:1/-1;grid-row:2}.production-workbench{grid-template-columns:1fr}.production-task-queue{order:2}.production-task-workspace{order:1}.production-stage-strip{display:flex;overflow-x:auto}.production-stage-strip li{flex:1 0 155px}.production-primary-actions .dominant-production-action{width:100%}}
+@media(max-width:900px){.production-range-context{grid-template-columns:1fr auto}.production-range-progress{grid-column:1/-1;grid-row:2}.production-workbench{grid-template-columns:1fr}.production-task-queue{order:2}.production-task-workspace{order:1}.production-stage-strip{display:flex;overflow-x:auto}.production-stage-strip li{flex:1 0 155px}.production-primary-actions{position:static;min-height:0;padding:0;border:0;border-radius:0;background:transparent;box-shadow:none;backdrop-filter:none}.production-primary-actions .dominant-production-action{width:100%}.production-task-card{padding-bottom:20px}}
 @media(max-width:560px){.production-workbench-shell{padding:14px}.production-range-context{grid-template-columns:1fr}.production-workbench-shell #productionChangeScope{justify-self:start}.production-progress-summary{grid-template-columns:repeat(2,minmax(0,1fr))}.production-voice-row{grid-template-columns:1fr}.production-task-heading h2{font-size:22px}}
 @media(max-width:620px){
   .topbar{align-items:stretch;flex-direction:column}.system-diagnostics>summary{width:100%}.system-diagnostics-panel{position:fixed;top:84px;right:8px;left:8px;width:auto}
@@ -451,8 +451,9 @@ input,select,textarea{border:1px solid #c7d0c9!important;border-radius:4px!impor
 .production-workbench{display:grid;grid-template-columns:minmax(220px,270px) minmax(0,1fr);gap:0;margin-top:14px;border:1px solid var(--studio-rule);background:#fff}.production-task-queue{position:sticky;top:58px;align-self:start;max-height:calc(100vh - 78px);padding:0;border:0;border-right:1px solid var(--studio-rule);border-radius:0;background:#f8faf8;overflow:hidden}.production-queue-head{margin:0;padding:13px 14px 10px;border-bottom:1px solid var(--studio-rule)}.production-queue-head h2{font-size:15px}.production-chapter-queue{display:grid;gap:0;max-height:calc(100vh - 146px);overflow:auto;padding:0;scrollbar-gutter:stable}.production-queue-item{grid-template-columns:30px minmax(0,1fr) 14px;gap:7px;margin:0;padding:9px 12px;border:0;border-bottom:1px solid #e6ebe7;border-radius:0;background:transparent}.production-queue-item:hover{background:#f0f4f1}.production-queue-item.selected{background:#e9f1ec;box-shadow:inset 3px 0 0 var(--studio-pine)}.production-queue-item.blocked{box-shadow:inset 3px 0 0 var(--studio-oxide)}.production-queue-item.error{box-shadow:inset 3px 0 0 var(--studio-danger)}.production-queue-item.complete{opacity:.66}.production-queue-copy strong{font-size:12.5px}.production-queue-copy small{font-size:10.5px}.production-queue-number{color:#65756b}
 .production-task-workspace{min-width:0;padding:22px 24px 28px;outline:none}.production-task-card{padding:0;border:0;border-radius:0;background:#fff;box-shadow:none}.production-task-heading{padding-bottom:12px;border-bottom:1px solid var(--studio-rule)}.production-task-heading h2{font-size:28px;font-weight:650;line-height:1.14}.production-task-summary{max-width:70ch;margin:10px 0 18px;color:#536159;font-size:15px}.production-chapter-context{text-transform:none;letter-spacing:0;color:#64746a}.production-task-content{gap:14px}.production-result-note,.owner-decision-note{padding:11px 13px;border-left:3px solid #769885;border-radius:0;background:#f1f5f2}.production-speaker-card{border:1px solid var(--studio-rule);border-radius:3px;background:#fafbf9}.production-speaker-card blockquote{border-radius:0;border-left:3px solid var(--studio-pine);background:#fff;font:16px/1.62 Georgia,"Times New Roman",serif}.production-context-list p{border-radius:0;background:#f8f9f7}.production-voice-row{border:0;border-top:1px solid #e1e7e2;border-radius:0;background:transparent}.production-voice-row:last-child{border-bottom:1px solid #e1e7e2}
 .production-range-metrics,.production-progress-summary{gap:0;border:1px solid var(--studio-rule)}.production-range-metrics>div,.production-progress-summary>div{padding:10px 12px;border-radius:0;background:#f7f9f7;border-right:1px solid var(--studio-rule)}.production-range-metrics>div:last-child,.production-progress-summary>div:last-child{border-right:0}.production-range-metrics strong{color:var(--studio-pine)}
-.production-primary-actions{position:sticky;top:auto;bottom:0;z-index:4;justify-content:flex-end;gap:10px;margin:18px -24px -28px;padding:12px 24px;border-top:1px solid var(--studio-rule);background:rgba(255,255,255,.96);backdrop-filter:blur(8px)}.production-primary-actions .dominant-production-action{min-width:220px;min-height:42px;border-radius:4px;box-shadow:none}.production-secondary-links{margin-top:14px}.production-technical-details{margin-top:16px;padding-top:10px;border-top:1px solid var(--studio-rule)}.production-technical-details summary{color:#6b7870;font-weight:600}
+.production-primary-actions{position:fixed;right:max(22px,calc((100vw - 1380px)/2 + 22px));bottom:12px;z-index:8;justify-content:flex-end;gap:10px;min-height:58px;margin:0;padding:8px 12px;border:1px solid var(--studio-rule);border-radius:12px;background:rgba(255,255,255,.97);box-shadow:0 8px 28px rgba(23,59,44,.18);backdrop-filter:blur(8px)}.production-primary-actions .dominant-production-action{min-width:220px;min-height:42px;border-radius:4px;box-shadow:none}.production-task-card{padding-bottom:82px}.production-secondary-links{margin-top:14px}.production-technical-details{margin-top:16px;padding-top:10px;border-top:1px solid var(--studio-rule)}.production-technical-details summary{color:#6b7870;font-weight:600}
 .production-command-status{border-radius:0}.production-inspection-summary{border-radius:0}.production-render-progress{border-radius:3px}.production-preflight-verdict,.production-preflight-check,.production-preflight-table,.production-execution-preview,.owner-prepared-hero,.owner-complete-hero{border-radius:3px}.production-preflight-checklist{gap:4px}.production-preflight-table-head{text-transform:none;letter-spacing:0}.production-execution-preview{background:var(--studio-pine-deep)}
+@media(max-width:900px){.production-primary-actions{position:static;min-height:0;margin:0;padding:0;border:0;border-radius:0;background:transparent;box-shadow:none;backdrop-filter:none}.production-task-card{padding-bottom:20px}}
 #productionView.production-first-use .production-workbench{display:block;border:0;background:transparent}#productionView.production-first-use .production-task-workspace{max-width:800px;margin:52px auto;padding:0 24px}#productionView.production-first-use .production-task-card{padding:0}#productionView.production-first-use .production-task-heading{border-bottom:0}#productionView.production-first-use .production-task-heading h2{font-size:34px}#productionView.production-first-use .production-task-summary{font-size:16px}#productionView.production-first-use .production-primary-actions{position:static;margin:22px 0 0;padding:0;border:0;background:transparent}
 
 /* Books: import bay first, then a quiet library list. */

R repair brief:
REPAIR: Keep `#productionTaskContent` before `#productionPrimaryActions` in the document. The candidate moves the action ahead of the review content on compact layouts, where the action returns to normal flow; that changes the existing decision order outside the requested desktop correction. Retain the desktop visibility fix, then rerun the affected browser check on the exact repaired candidate. At 1366×768 and 1366×600, verify the button is fully visible and can be activated by a pointer at page top and while reviewing long content, with no horizontal overflow.

This is the sole repair. Work only in this disposable clone. No external or production effects. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report checks actually run and remaining limits.
