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

I completion report:
Changed the Production action area in [ui/styles.css](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-001/20260923T203651Z-bfe50ba6/arms/N1/ui/styles.css) to stay pinned at the bottom of the viewport while task content scrolls, with extra page padding so content remains reachable. Updated the existing browser check in [browser_production_task_workbench_smoke.mjs](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-001/20260923T203651Z-bfe50ba6/arms/N1/scripts/browser_production_task_workbench_smoke.mjs) to check the pinned action’s visibility.

Checks run: seven workbench unit tests passed; the isolated Production workbench browser journey passed; `node --check` passed for both JavaScript files; `git diff --check` passed. An initial broader browser run also hit unrelated fixture failures; the focused workbench browser check passed afterward.

The browser check exercised changing task states and verified their current action labels. I did not verify pointer and keyboard activation or inspect the action at both requested heights (1366×768 and 1366×600), so those acceptance details remain unverified. I cannot claim Product Acceptance.

Candidate tree: 39095f372823cf57434fe62b789bacb5eb7b827c
Candidate status:
M  scripts/browser_production_task_workbench_smoke.mjs
M  ui/styles.css
Candidate diff:
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

Return exactly READY or REPAIR: followed by one bounded repair brief. If no safe repair is possible, return NOT_READY with a reason.
