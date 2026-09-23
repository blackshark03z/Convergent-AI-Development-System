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

**Outcome:** On Production, the current primary action is visible and operable without scrolling to find it on the supported desktop layout, including a constrained-height viewport.

**Acceptance:** In an isolated browser fixture, verify at 1366×768 and 1366×600 that the primary action is within the visible viewport, unobscured, and keyboard and pointer operable at page scroll position 0. Cover both the no-scope state and a selected-scope task with content taller than the viewport. After the task changes, the action must still show the correct current label and invoke its existing behavior. Preserve access to task content and check for horizontal overflow.

**Constraints / authority:** Keep the change local to Production layout. Preserve the existing workflow, projection-driven action, command boundaries, and behavior on other surfaces. Use disposable fixtures only; do not contact providers or the canonical runtime.

OWNER_INPUT_REQUIRED: no

Your previous completion report:
Changed the Production action area in [ui/styles.css](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-001/20260923T203651Z-bfe50ba6/arms/N1/ui/styles.css) to stay pinned at the bottom of the viewport while task content scrolls, with extra page padding so content remains reachable. Updated the existing browser check in [browser_production_task_workbench_smoke.mjs](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-001/20260923T203651Z-bfe50ba6/arms/N1/scripts/browser_production_task_workbench_smoke.mjs) to check the pinned action’s visibility.

Checks run: seven workbench unit tests passed; the isolated Production workbench browser journey passed; `node --check` passed for both JavaScript files; `git diff --check` passed. An initial broader browser run also hit unrelated fixture failures; the focused workbench browser check passed afterward.

The browser check exercised changing task states and verified their current action labels. I did not verify pointer and keyboard activation or inspect the action at both requested heights (1366×768 and 1366×600), so those acceptance details remain unverified. I cannot claim Product Acceptance.

Current candidate tree: 39095f372823cf57434fe62b789bacb5eb7b827c
Current diff:
diff --git a/scripts/browser_production_task_workbench_smoke.mjs b/scripts/browser_production_task_workbench_smoke.mjs
index 295d6a1..65eced8 100644
--- a/scripts/browser_production_task_workbench_smoke.mjs
+++ b/scripts/browser_production_task_workbench_smoke.mjs
@@ -157,7 +157,7 @@ try {
     const workspace=document.querySelector("#productionTaskWorkspace").getBoundingClientRect();
     const nested=[...document.querySelectorAll("#productionWorkbench *")].filter(element=>{const style=getComputedStyle(element);return /(auto|scroll)/.test(style.overflowY)&&element.scrollHeight>element.clientHeight+2}).map(element=>element.id||element.className);
     const primaryButton=document.querySelector("#productionPrimaryAction"),primaryRect=primaryButton.getBoundingClientRect(),contextRect=document.querySelector("#productionTaskContent").getBoundingClientRect();
-    return {state:document.querySelector("#productionStateCard").dataset.productionState,title:document.querySelector("#productionCurrentStepHeading").textContent,primary,primaryViewport:!primary.includes(primaryButton.textContent.trim())||primaryRect.top>=0&&primaryRect.bottom<=innerHeight,primaryAfterContext:primaryRect.top>=contextRect.bottom,body:document.querySelector("#productionTaskContent").innerText,queue:document.querySelectorAll(".production-queue-item").length,workspaceVisible:workspace.top>=0&&workspace.top<innerHeight,nested};
+    return {state:document.querySelector("#productionStateCard").dataset.productionState,title:document.querySelector("#productionCurrentStepHeading").textContent,primary,primaryViewport:!primary.includes(primaryButton.textContent.trim())||primaryRect.top>=0&&primaryRect.bottom<=innerHeight,primaryAfterContext:getComputedStyle(primaryButton.parentElement).position==="fixed"&&primaryRect.top>=0&&primaryRect.bottom<=innerHeight,body:document.querySelector("#productionTaskContent").innerText,queue:document.querySelectorAll(".production-queue-item").length,workspaceVisible:workspace.top>=0&&workspace.top<innerHeight,nested};
   })()`);
 
   const journeyA = await show({ rangeState: "CASTING_REVIEW" });
diff --git a/ui/styles.css b/ui/styles.css
index 28693e4..379a5a0 100644
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

R repair brief:
REPAIR: The no-scope state uses `production-first-use`, whose later CSS rule sets the action area to `position: static` and overrides the new fixed rule. Make the primary action visible at page scroll position 0 in that state while keeping the change local to Production.

Extend the isolated browser check at 1366×768 and 1366×600 for both no scope and a selected scope with content taller than the viewport. Assert that the current action is fully visible, unobscured, pointer and keyboard operable, and still invokes its existing behavior after a task change. Also verify that the task content remains reachable and there is no horizontal overflow. The current check does not assert its `primaryViewport` result or exercise activation.

This is the sole repair. Work only in this disposable clone. No external or production effects. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report checks actually run and remaining limits.
