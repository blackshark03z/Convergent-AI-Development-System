You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-001 Reasoning Lead Prompt — N1 / Existing-minimal stack

You are R, the Reasoning Lead. You do not edit product code.

## Frozen Raw Owner Goal

On the Production surface, keep the current primary action visible and reachable
without requiring the Owner to scroll just to find that action on the supported
desktop layout, including a constrained-height desktop viewport.

Preserve the existing production workflow and behavior. Make the smallest
coherent product change needed and verify the affected browser behavior.

## Fixed constraints

- Do not redesign unrelated Story Audio flows.
- Do not call paid/external providers or the canonical production runtime.
- Preserve existing user-facing behavior outside the affected layout.
- The historical/reference implementation and held-out evaluator are hidden.
- Do not inspect sibling benchmark workspaces or results.
- You may inspect the assigned neutral repository.
- You must not edit product code.

## Common R→I rule

Produce the smallest Implementation Brief that makes the outcome testable.

SPEC UNTIL TESTABLE, NOT SPEC UNTIL COMPLETE.

Stop specifying once:
1. multiple implementations could validly satisfy the brief;
2. PASS/FAIL can be judged from observable outcome without reference-patch
   knowledge; and
3. I no longer needs to invent a material product preference or consequence
   boundary.

Your brief may use:
- Outcome
- Acceptance
- Constraints / Non-goals
- Effects / Authority
- material assumptions/open questions only if needed

Do not add design/architecture/task artifacts unless they solve a concrete
ambiguity or risk in this Goal.

## Arm treatment

Use ordinary product/developer documentation, existing tests, browser tooling and
normal engineering conventions available in the neutral repository. Do not
create a custom process/framework.

## Output for phase 1

Return only:
- `IMPLEMENTATION_BRIEF`
- `OWNER_INPUT_REQUIRED: yes|no`
- if yes, the minimum material question that blocks a safe/testable handoff.

After I returns a candidate, you will receive its diff/evidence separately and
may respond READY or one REPAIR brief.


IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** On Production, the current primary action is visible and operable without scrolling to find it on the supported desktop layout, including a constrained-height viewport.

**Acceptance:** In an isolated browser fixture, verify at 1366×768 and 1366×600 that the primary action is within the visible viewport, unobscured, and keyboard and pointer operable at page scroll position 0. Cover both the no-scope state and a selected-scope task with content taller than the viewport. After the task changes, the action must still show the correct current label and invoke its existing behavior. Preserve access to task content and check for horizontal overflow.

**Constraints / authority:** Keep the change local to Production layout. Preserve the existing workflow, projection-driven action, command boundaries, and behavior on other surfaces. Use disposable fixtures only; do not contact providers or the canonical runtime.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: The no-scope state uses `production-first-use`, whose later CSS rule sets the action area to `position: static` and overrides the new fixed rule. Make the primary action visible at page scroll position 0 in that state while keeping the change local to Production.

Extend the isolated browser check at 1366×768 and 1366×600 for both no scope and a selected scope with content taller than the viewport. Assert that the current action is fully visible, unobscured, pointer and keyboard operable, and still invokes its existing behavior after a task change. Also verify that the task content remains reachable and there is no horizontal overflow. The current check does not assert its `primaryViewport` result or exercise activation.

I completion report:
Changed the Production action area in [ui/styles.css](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-001/20260923T203651Z-bfe50ba6/arms/N1/ui/styles.css) to stay pinned at the bottom of the viewport while task content scrolls, with extra page padding so content remains reachable. Updated the existing browser check in [browser_production_task_workbench_smoke.mjs](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-001/20260923T203651Z-bfe50ba6/arms/N1/scripts/browser_production_task_workbench_smoke.mjs) to check the pinned action’s visibility.

Checks run: seven workbench unit tests passed; the isolated Production workbench browser journey passed; `node --check` passed for both JavaScript files; `git diff --check` passed. An initial broader browser run also hit unrelated fixture failures; the focused workbench browser check passed afterward.

The browser check exercised changing task states and verified their current action labels. I did not verify pointer and keyboard activation or inspect the action at both requested heights (1366×768 and 1366×600), so those acceptance details remain unverified. I cannot claim Product Acceptance.
Repair report:
**Changed**

- Added a more specific first-use Production CSS rule so the primary action stays fixed and visible when the later `position: static` rule applies.
- Extended the isolated browser check to measure the action at 1366×768 and 1366×600, with and without the first-use class. It checks visibility, hit testing, task-content reachability, horizontal overflow, pointer clicks, and Enter activation against the current task type.

**Checks run:** `node --check scripts/browser_production_task_workbench_smoke.mjs` and `git diff --check` passed. I did not run the browser journey: this checkout has no isolated server command available, and the documented app launcher uses the canonical runtime, which the brief prohibits contacting.

The new browser assertions are therefore unverified in a live browser. The “no scope” case is simulated by toggling the first-use class on the selected-scope fixture; it does not exercise the application’s actual no-scope setup path. No product acceptance is claimed.

Candidate tree: 0e3dc2e78e10d488d1b7430c79b23e7505f5e6ab
Candidate status:
M  scripts/browser_production_task_workbench_smoke.mjs
M  ui/styles.css
Candidate diff:
diff --git a/scripts/browser_production_task_workbench_smoke.mjs b/scripts/browser_production_task_workbench_smoke.mjs
index 295d6a1..3500053 100644
--- a/scripts/browser_production_task_workbench_smoke.mjs
+++ b/scripts/browser_production_task_workbench_smoke.mjs
@@ -157,10 +157,27 @@ try {
     const workspace=document.querySelector("#productionTaskWorkspace").getBoundingClientRect();
     const nested=[...document.querySelectorAll("#productionWorkbench *")].filter(element=>{const style=getComputedStyle(element);return /(auto|scroll)/.test(style.overflowY)&&element.scrollHeight>element.clientHeight+2}).map(element=>element.id||element.className);
     const primaryButton=document.querySelector("#productionPrimaryAction"),primaryRect=primaryButton.getBoundingClientRect(),contextRect=document.querySelector("#productionTaskContent").getBoundingClientRect();
-    return {state:document.querySelector("#productionStateCard").dataset.productionState,title:document.querySelector("#productionCurrentStepHeading").textContent,primary,primaryViewport:!primary.includes(primaryButton.textContent.trim())||primaryRect.top>=0&&primaryRect.bottom<=innerHeight,primaryAfterContext:primaryRect.top>=contextRect.bottom,body:document.querySelector("#productionTaskContent").innerText,queue:document.querySelectorAll(".production-queue-item").length,workspaceVisible:workspace.top>=0&&workspace.top<innerHeight,nested};
+    return {state:document.querySelector("#productionStateCard").dataset.productionState,title:document.querySelector("#productionCurrentStepHeading").textContent,primary,primaryViewport:!primary.includes(primaryButton.textContent.trim())||primaryRect.top>=0&&primaryRect.bottom<=innerHeight,primaryAfterContext:getComputedStyle(primaryButton.parentElement).position==="fixed"&&primaryRect.top>=0&&primaryRect.bottom<=innerHeight,body:document.querySelector("#productionTaskContent").innerText,queue:document.querySelectorAll(".production-queue-item").length,workspaceVisible:workspace.top>=0&&workspace.top<innerHeight,nested};
   })()`);
 
   const journeyA = await show({ rangeState: "CASTING_REVIEW" });
+  const productionActionLayouts = [];
+  for (const firstUse of [true, false]) {
+    const view = await evaluate(`(()=>{const root=document.querySelector('#productionView');root.classList.toggle('production-first-use',${firstUse});const content=document.querySelector('#productionTaskContent');content.insertAdjacentHTML('beforeend','<div data-layout-fixture style="height:1200px">Tall task fixture</div>');return true})()`);
+    for (const height of [768, 600]) {
+      await send("Emulation.setDeviceMetricsOverride", { width: 1366, height, deviceScaleFactor: 1, mobile: false });
+      const layout = await evaluate(`(()=>{const button=document.querySelector('#productionPrimaryAction'),rect=button.getBoundingClientRect(),actions=button.parentElement,hit=document.elementFromPoint(rect.left+rect.width/2,rect.top+rect.height/2),content=document.querySelector('#productionTaskContent'),saved=runProductionPrimaryAction;window.__actionCalls=[];window.__savedAction=saved;runProductionPrimaryAction=async vm=>{window.__actionCalls.push(vm.task_type)};button.focus();return{height:${height},firstUse:${firstUse},label:button.textContent.trim(),task:currentProductionViewModel().task_type,x:rect.left+rect.width/2,y:rect.top+rect.height/2,visible:rect.top>=0&&rect.bottom<=innerHeight&&rect.left>=0&&rect.right<=innerWidth,unobscured:hit===button||button.contains(hit),focused:document.activeElement===button,position:getComputedStyle(actions).position,contentReachable:content.scrollHeight>innerHeight&&content.lastElementChild.getBoundingClientRect().bottom>innerHeight,horizontal:document.documentElement.scrollWidth>innerWidth+1}})()`);
+      await send("Input.dispatchMouseEvent", { type: "mousePressed", x: layout.x, y: layout.y, button: "left", clickCount: 1 });
+      await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: layout.x, y: layout.y, button: "left", clickCount: 1 });
+      await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
+      await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
+      Object.assign(layout, await evaluate(`(()=>{const result={focused:document.activeElement===document.querySelector('#productionPrimaryAction'),calls:window.__actionCalls.slice()};runProductionPrimaryAction=window.__savedAction;return result})()`));
+      productionActionLayouts.push(layout);
+      if (!layout.visible || !layout.unobscured || layout.position !== "fixed" || !layout.contentReachable || layout.horizontal || layout.calls.length !== 2 || layout.calls.some(task => task !== layout.task)) throw new Error(`Production action layout/activation failed: ${JSON.stringify(layout)}`);
+    }
+    await evaluate(`document.querySelector('[data-layout-fixture]')?.remove();document.querySelector('#productionView').classList.remove('production-first-use')`);
+  }
+  await send("Emulation.setDeviceMetricsOverride", { width: 1366, height: 768, deviceScaleFactor: 1, mobile: false });
   const noDraftCasting = structuredClone(fixture.casting); noDraftCasting.casting = {};
   const journeyB = await show({ casting: noDraftCasting, draft: null, rangeState: "SPEAKER_EXCEPTIONS" });
   const unresolvedDraft = { id: 602, status: "draft", stale: false, remaining_unreviewed_count: 1, invalid_count: 0, characters: [{ id: 7001, display_name: "Nhân vật A" }], review_rows: [{ utterance_id: "u2", sequence: 2, text: "Ai đang nói?", reviewed: false, context: [{ text: "Ngữ cảnh trước" }, { text: "Ai đang nói?", is_target: true }, { text: "Ngữ cảnh sau" }], suggestion: { speaker_type: "character", character_id: 7001, confidence_level: "medium", confidence: 0.7, reason: "Có tên nhân vật gần câu thoại." } }] };
@@ -287,7 +304,7 @@ try {
   if (inactiveProjectionPolling.route !== "assignment" || inactiveProjectionPolling.projection !== 0 || inactiveProjectionPolling.preflight !== 0) throw new Error(`Inactive view requested Production state: ${JSON.stringify(inactiveProjectionPolling)}`);
   if (browserErrors.length) throw new Error(`Browser errors: ${browserErrors.join(" | ")}`);
 
-  process.stdout.write(JSON.stringify({ ok: true, journeyA, journeyB, journeyC, pollingStability, journeyDEdit, journeyDReview, journeyEPrepare, journeyInfrastructure, voiceReturnLayout1366, voiceReturnLayout520, voiceReturn, journeyEStart, preparedEditCancel, journeyEStartBlocked, journeyERunning, monitorJobsNavigation, jobsRecoveryActions, jobsRecoveryVariants, journeyF, journeyG, qaHandoff, journeyH, commandLifecycle, qaCommandReconcile, rangeCommandContinuity, inspectionBC, prepareSkipCompleted, nullPrimaryMappings, malformedSafe, scopeAction1366, scopeAction820, desktop, inactiveProjectionPolling, returnToProduction }));
+  process.stdout.write(JSON.stringify({ ok: true, journeyA, productionActionLayouts, journeyB, journeyC, pollingStability, journeyDEdit, journeyDReview, journeyEPrepare, journeyInfrastructure, voiceReturnLayout1366, voiceReturnLayout520, voiceReturn, journeyEStart, preparedEditCancel, journeyEStartBlocked, journeyERunning, monitorJobsNavigation, jobsRecoveryActions, jobsRecoveryVariants, journeyF, journeyG, qaHandoff, journeyH, commandLifecycle, qaCommandReconcile, rangeCommandContinuity, inspectionBC, prepareSkipCompleted, nullPrimaryMappings, malformedSafe, scopeAction1366, scopeAction820, desktop, inactiveProjectionPolling, returnToProduction }));
 } finally {
   try { socket?.close(); } catch {}
   const browserExited = new Promise(resolve => {
diff --git a/ui/styles.css b/ui/styles.css
index 28693e4..910ffd6 100644
--- a/ui/styles.css
+++ b/ui/styles.css
@@ -235,6 +235,11 @@ main{max-width:1240px;margin:18px auto;padding:0 20px 50px}.app-view{animation:n
 /* OWNER_PRODUCT_UX_CONVERGENCE_V1 */
 .production-primary-actions{position:static;z-index:auto;margin:18px 0 0;padding:0;background:none;justify-content:flex-end}
 .production-primary-actions .dominant-production-action{width:auto;min-width:230px}
+/* Keep the current Production action reachable while task content scrolls. */
+#productionView{padding-bottom:112px}
+#productionView .production-primary-actions{position:fixed;right:max(22px,calc((100vw - 1380px)/2 + 22px));bottom:max(16px,env(safe-area-inset-bottom));z-index:8;display:flex;align-items:center;justify-content:flex-end;gap:10px;width:min(1380px,calc(100vw - 44px));margin:0;padding:12px 14px;border:1px solid #dce5de;border-radius:14px;background:rgba(255,255,255,.97);box-shadow:0 8px 28px rgba(23,59,44,.16);backdrop-filter:blur(10px)}
+#productionView .production-primary-actions .dominant-production-action{min-height:46px}
+@media(max-width:560px){#productionView{padding-bottom:104px}#productionView .production-primary-actions{right:12px;width:calc(100vw - 24px);padding:10px}}
 .owner-section-heading{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;margin-bottom:14px}
 .owner-section-heading h3,.owner-section-heading p{margin:0}
 .owner-voice-tools{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
@@ -454,6 +459,7 @@ input,select,textarea{border:1px solid #c7d0c9!important;border-radius:4px!impor
 .production-primary-actions{position:sticky;top:auto;bottom:0;z-index:4;justify-content:flex-end;gap:10px;margin:18px -24px -28px;padding:12px 24px;border-top:1px solid var(--studio-rule);background:rgba(255,255,255,.96);backdrop-filter:blur(8px)}.production-primary-actions .dominant-production-action{min-width:220px;min-height:42px;border-radius:4px;box-shadow:none}.production-secondary-links{margin-top:14px}.production-technical-details{margin-top:16px;padding-top:10px;border-top:1px solid var(--studio-rule)}.production-technical-details summary{color:#6b7870;font-weight:600}
 .production-command-status{border-radius:0}.production-inspection-summary{border-radius:0}.production-render-progress{border-radius:3px}.production-preflight-verdict,.production-preflight-check,.production-preflight-table,.production-execution-preview,.owner-prepared-hero,.owner-complete-hero{border-radius:3px}.production-preflight-checklist{gap:4px}.production-preflight-table-head{text-transform:none;letter-spacing:0}.production-execution-preview{background:var(--studio-pine-deep)}
 #productionView.production-first-use .production-workbench{display:block;border:0;background:transparent}#productionView.production-first-use .production-task-workspace{max-width:800px;margin:52px auto;padding:0 24px}#productionView.production-first-use .production-task-card{padding:0}#productionView.production-first-use .production-task-heading{border-bottom:0}#productionView.production-first-use .production-task-heading h2{font-size:34px}#productionView.production-first-use .production-task-summary{font-size:16px}#productionView.production-first-use .production-primary-actions{position:static;margin:22px 0 0;padding:0;border:0;background:transparent}
+#productionView.production-first-use .production-primary-actions{position:fixed;right:max(22px,calc((100vw - 1380px)/2 + 22px));bottom:max(16px,env(safe-area-inset-bottom));z-index:8;width:min(1380px,calc(100vw - 44px));margin:0;padding:12px 14px;border:1px solid #dce5de;border-radius:14px;background:rgba(255,255,255,.97);box-shadow:0 8px 28px rgba(23,59,44,.16);backdrop-filter:blur(10px)}
 
 /* Books: import bay first, then a quiet library list. */
 #booksView .panel{box-shadow:none}.import-panel{grid-template-columns:minmax(0,1fr);gap:14px}.import-row{display:grid;grid-template-columns:minmax(280px,1.2fr) minmax(220px,.8fr) auto auto;gap:10px;align-items:end;padding:14px 0;border-top:1px solid var(--studio-rule);border-bottom:1px solid var(--studio-rule)}.epub-upload-field,.epub-existing-source{display:grid;gap:5px;font-size:12px;font-weight:650}.epub-upload-field input{padding:7px}.epub-existing-source select{min-width:0}.book-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:0;border-top:1px solid var(--studio-rule)}.book-card{min-width:0;padding:13px 12px;border:0;border-bottom:1px solid var(--studio-rule);border-radius:0;background:transparent}.book-card:hover{background:#f0f4f1}.book-card.active{background:#e9f1ec;box-shadow:inset 3px 0 0 var(--studio-pine)}.book-card strong{font-family:Bahnschrift,"Segoe UI Variable",sans-serif;font-size:15px}.book-card span{font-size:12px}

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
