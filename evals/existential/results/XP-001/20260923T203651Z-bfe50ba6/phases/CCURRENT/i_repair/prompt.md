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

**Outcome:** On Production, the current primary action stays fully visible and operable in the initial viewport when a selected scope has long task content.

**Acceptance:**
- In an isolated browser fixture, check the Production surface at 1366×768 and a constrained-height 1366×600 desktop viewport. After the task renders, the current primary button is fully within the viewport, unobscured, and reachable by keyboard and pointer without scrolling to find it.
- Repeat after a task transition or refresh that changes the current action. The visible action still matches the authoritative task; states with no primary action do not gain one.
- Long content remains readable and reachable, with no horizontal overflow or action covering content. Existing focus, scroll, and production behavior remain intact.

**Constraints / authority:** Make the smallest coherent Production layout change. Preserve the existing task flow and separate PREPARE and START_RENDER actions. Verify against disposable fixture data without provider calls or the canonical runtime. Bind browser evidence to the candidate before READY; Owner product acceptance remains separate.

OWNER_INPUT_REQUIRED: no

Your previous completion report:
Implemented the Production desktop layout change in [ui/styles.css](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-001/20260923T203651Z-bfe50ba6/arms/CCURRENT/ui/styles.css): the current task’s action bar stays fixed at the bottom of desktop viewports, and the task card reserves space so its final content can scroll clear of it. The existing task still determines which action appears; this change adds no action to states without one. First-use and smaller-screen layouts retain their existing behavior.

**Checks run:** `git diff --check` passed. The Production browser test suite ran, but both tests failed before completing the requested viewport checks: one reported a missing narrator option; the other failed its primary-action/context assertion and showed corrupted text in the browser output.

**Evidence and limitations:** No rendered evidence was obtained at 1366×768 or 1366×600, and keyboard/pointer reachability, task transitions, no-action states, and content clearance remain unverified. No provider calls or canonical runtime were used. No material product assumptions were needed.

Current candidate tree: dd54926e07b4fc67a611432738d81ecd8f72cd55
Current diff:
diff --git a/ui/styles.css b/ui/styles.css
index 28693e4..7200d7b 100644
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
+  #productionView:not(.production-first-use) .production-primary-actions{position:fixed;left:max(292px,calc((100vw - 1200px)/2 + 276px));right:24px;bottom:0;z-index:45;margin:0;padding:10px 16px calc(10px + env(safe-area-inset-bottom));border:1px solid var(--color-border);border-bottom:0;background:rgba(255,255,255,.98);box-shadow:0 -5px 18px rgba(30,42,56,.08);backdrop-filter:blur(8px)}
+}
 .upload-target-display,.preview-test-status{background:var(--color-primary-soft)}.preferred-badge{background:var(--color-success)!important;color:#fff!important}.attempt-card.active{border-left-color:var(--color-primary);background:var(--color-primary-soft)}.attempt-card.candidate{border-left-color:var(--color-warning);background:var(--color-warning-soft)}
 .settings-provider-editor{margin-top:18px;padding:18px;border:1px solid var(--color-border);background:var(--color-surface-subtle)}.settings-provider-editor h3{margin:0}.settings-provider-editor label{display:block;font-weight:700;margin:14px 0 6px}.settings-provider-editor textarea{width:100%;min-height:132px;resize:vertical;font:13px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace}.settings-provider-actions{display:flex;align-items:center;gap:12px;margin-top:12px;flex-wrap:wrap}.settings-provider-actions [role="status"]{color:var(--color-text-muted)}

R repair brief:
REPAIR: Keep the current Production action visible at 1366×768 and 1366×600, but correct the desktop bar’s placement. At 1366px, its fixed left edge is about 359px while the task canvas begins about 488px, so it can cover the chapter queue and technical details. Keep the bar within the task area and ensure long content remains reachable without obstruction.

Before READY, obtain browser evidence from an isolated fixture for both viewports, including a changed current action, a no-action state, keyboard and pointer reachability, content clearance, and no horizontal overflow. The reported test failures occurred before those checks, so they do not establish acceptance.

This is the sole repair. Work only in this disposable clone. No external or production effects. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report checks actually run and remaining limits.
