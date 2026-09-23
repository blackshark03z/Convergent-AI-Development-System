You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-001 Reasoning Lead Prompt — C-current / Current Thin CADS

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

Apply current Thin-CADS semantics relevant to this bounded Goal: reconstruct
relevant product reality; keep Goal/journey authoritative; resolve only material
design uncertainty; prefer reuse/fix over new machinery; require representative
product-level evidence before READY; bind evidence to candidate; preserve
consequence boundaries and canonical product truth. Use the fast path.

## Output for phase 1

Return only:
- `IMPLEMENTATION_BRIEF`
- `OWNER_INPUT_REQUIRED: yes|no`
- if yes, the minimum material question that blocks a safe/testable handoff.

After I returns a candidate, you will receive its diff/evidence separately and
may respond READY or one REPAIR brief.


IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** On Production, the current primary action stays fully visible and operable in the initial viewport when a selected scope has long task content.

**Acceptance:**
- In an isolated browser fixture, check the Production surface at 1366×768 and a constrained-height 1366×600 desktop viewport. After the task renders, the current primary button is fully within the viewport, unobscured, and reachable by keyboard and pointer without scrolling to find it.
- Repeat after a task transition or refresh that changes the current action. The visible action still matches the authoritative task; states with no primary action do not gain one.
- Long content remains readable and reachable, with no horizontal overflow or action covering content. Existing focus, scroll, and production behavior remain intact.

**Constraints / authority:** Make the smallest coherent Production layout change. Preserve the existing task flow and separate PREPARE and START_RENDER actions. Verify against disposable fixture data without provider calls or the canonical runtime. Bind browser evidence to the candidate before READY; Owner product acceptance remains separate.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: Keep the current Production action visible at 1366×768 and 1366×600, but correct the desktop bar’s placement. At 1366px, its fixed left edge is about 359px while the task canvas begins about 488px, so it can cover the chapter queue and technical details. Keep the bar within the task area and ensure long content remains reachable without obstruction.

Before READY, obtain browser evidence from an isolated fixture for both viewports, including a changed current action, a no-action state, keyboard and pointer reachability, content clearance, and no horizontal overflow. The reported test failures occurred before those checks, so they do not establish acceptance.

I completion report:
Implemented the Production desktop layout change in [ui/styles.css](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-001/20260923T203651Z-bfe50ba6/arms/CCURRENT/ui/styles.css): the current task’s action bar stays fixed at the bottom of desktop viewports, and the task card reserves space so its final content can scroll clear of it. The existing task still determines which action appears; this change adds no action to states without one. First-use and smaller-screen layouts retain their existing behavior.

**Checks run:** `git diff --check` passed. The Production browser test suite ran, but both tests failed before completing the requested viewport checks: one reported a missing narrator option; the other failed its primary-action/context assertion and showed corrupted text in the browser output.

**Evidence and limitations:** No rendered evidence was obtained at 1366×768 or 1366×600, and keyboard/pointer reachability, task transitions, no-action states, and content clearance remain unverified. No provider calls or canonical runtime were used. No material product assumptions were needed.
Repair report:
**Implemented the layout repair** in [ui/styles.css](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-001/20260923T203651Z-bfe50ba6/arms/CCURRENT/ui/styles.css): the fixed Production action bar now aligns with the task card’s left and right edges, keeping it clear of the chapter queue and technical details.

**Checks run:** `git diff --check` passed. Seven Production task workbench unit tests passed. Two existing Production browser tests failed before reaching viewport checks: one hit the missing narrator option reported previously; the other failed its context assertion and showed corrupted browser text.

I did **not** obtain browser evidence at 1366×768 or 1366×600 for action transitions, no-action states, keyboard or pointer reachability, content clearance, or horizontal overflow. Those remain unverified, so this is not READY evidence. No provider calls or canonical runtime were used.

Candidate tree: d3d17cce95edf8ec9267f26d5f9f0789a26d5e0c
Candidate status:
M  ui/styles.css
Candidate diff:
diff --git a/ui/styles.css b/ui/styles.css
index 28693e4..bb4afa8 100644
--- a/ui/styles.css
+++ b/ui/styles.css
@@ -630,6 +630,12 @@ input,select,textarea{border-color:#c5ceda!important;color:var(--color-text)!imp
 .range-exception-card,.speaker-review-guide,.casting-step-banner,.recommended-action-banner{border-color:#e6c68d!important;background:var(--color-warning-soft)!important}.range-exception-card strong,.speaker-review-guide strong{color:#6f4a12}
 .status-dot.casting-approved,.badge.active-output,.status-dot.active-output,.voice-info-badge.badge-active,.confidence-high{background:var(--color-success-soft)!important;color:var(--color-success)!important}.status-dot.casting-review,.confidence-medium{background:var(--color-warning-soft)!important;color:#7d520f!important}.confidence-low,.confidence-invalid,.error-text,.needs-review{color:var(--color-danger)!important}.badge.historical,.status-dot.historical,.voice-info-badge.badge-inactive,.muted-chip{background:#eef1f4!important;color:#606d7d!important}
 .production-auth-status{background:var(--color-success-soft);color:var(--color-success)}.production-auth-status.blocked{background:var(--color-warning-soft);color:#7d520f}.production-preflight-verdict{background:var(--color-success-soft);border-left-color:var(--color-success)}.production-preflight-verdict.blocked{background:var(--color-warning-soft);border-left-color:var(--color-warning)}.production-preflight-check>span{background:var(--color-success-soft);color:var(--color-success)}.production-preflight-check.fail{border-color:#e6c68d;background:var(--color-warning-soft)}.production-preflight-check.fail>span{background:#f4ddb2;color:#7d520f}
+
+/* Keep the current Production decision reachable while long task guidance scrolls. */
+@media(min-width:901px){
+  #productionView:not(.production-first-use) .production-task-card{padding-bottom:84px}
+  #productionView:not(.production-first-use) .production-primary-actions{position:fixed;left:calc(var(--ux-nav-width) + 28px + 220px + 16px);right:calc(28px + 260px + 16px);bottom:0;z-index:45;margin:0;padding:10px 16px calc(10px + env(safe-area-inset-bottom));border:1px solid var(--color-border);border-bottom:0;background:rgba(255,255,255,.98);box-shadow:0 -5px 18px rgba(30,42,56,.08);backdrop-filter:blur(8px)}
+}
 .upload-target-display,.preview-test-status{background:var(--color-primary-soft)}.preferred-badge{background:var(--color-success)!important;color:#fff!important}.attempt-card.active{border-left-color:var(--color-primary);background:var(--color-primary-soft)}.attempt-card.candidate{border-left-color:var(--color-warning);background:var(--color-warning-soft)}
 .settings-provider-editor{margin-top:18px;padding:18px;border:1px solid var(--color-border);background:var(--color-surface-subtle)}.settings-provider-editor h3{margin:0}.settings-provider-editor label{display:block;font-weight:700;margin:14px 0 6px}.settings-provider-editor textarea{width:100%;min-height:132px;resize:vertical;font:13px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace}.settings-provider-actions{display:flex;align-items:center;gap:12px;margin-top:12px;flex-wrap:wrap}.settings-provider-actions [role="status"]{color:var(--color-text-muted)}

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
