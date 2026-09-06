# Goal

Add a thin conditional UI/UX procedure layer so AI-built user-facing products
converge on discoverable workflows, deliberate frontend implementation, and
real rendered usability without turning CADS into a design OS.

# Critical User Journey

A Tech Lead/Worker with a user-facing Goal -> frames the Product Goal -> shapes
the user journey/navigation around operator intent -> implements the interface
with complete relevant states/accessibility -> exercises the real rendered flow
-> reviews only high-impact UX findings -> fixes blockers -> proceeds to Product
Acceptance.

# Acceptance

- Add exactly three conditional product/UI skills: User-Facing Workflow,
  Frontend Design, and UI Quality Review.
- Root/project `AGENTS.md` route user-facing triggers into those skills while the
  existing six core playbooks remain universal and unchanged in role.
- Workflow/information architecture precedes visual implementation when both are
  material; Systematic Debugging remains the path for concrete defects; UI
  Quality Review precedes user-facing Product Acceptance.
- Frontend Design embeds relevant interaction states, responsive verification,
  accessibility basics, reuse-first visual discipline, and actual rendered UI
  verification.
- UI Quality Review returns only high-impact `BLOCKER`, `HIGH`, or
  `DEFERRED_POLISH` findings and does not create an open-ended redesign chain.
- No mandatory design system, `DESIGN.md`, Figma workflow, accessibility
  subsystem, visual scoring engine, or persisted UX lifecycle is introduced.
- Candidate packaging/tests prove all three product/UI skills and router wiring;
  the full active source-checkout suite passes.
- One clean local task commit is produced before any promotion decision.

# Acceptance Fixture / Golden Input

Use the CADS project bootstrap/template and candidate-package tests as the
mechanical fixture, plus current root `AGENTS.md` routing as the procedure
contract. The skills themselves must remain self-contained advisory procedures.

# Non-goals

No Thin Guard redesign, Standard v2, design-system framework, component library,
CSS/token runtime, screenshot scoring service, browser automation framework,
legacy rewrite, provider integration, or product-specific UI redesign.

# Constraints

- Preserve the simplified native-development architecture and existing six core
  playbooks.
- Do not modify `buildos/**`, legacy lifecycle sources, or the canonical
  Convergent AI Development Standard.
- Product/UI skills are conditional; non-user-facing projects must not pay their
  process cost.
- Accessibility uses established semantic/native and WCAG/WAI-ARIA-aligned
  practice inside the relevant skills rather than a new subsystem.

# Material Decisions

- `skills/core/` remains exactly the six universal procedures already promoted.
- UI/UX procedures live under `skills/product/` because they are conditional on
  user-facing work.
- User-Facing Workflow owns task flow/navigation/discoverability reasoning;
  Frontend Design owns implementation craft and rendered-state verification; UI
  Quality Review owns bounded usability/accessibility review before acceptance.
- A design-system skill is deferred until repeated evidence across projects
  proves a shared-rule problem that cannot be handled locally.
- The simplified thin-guard lineage remains rooted in baseline `8970dc8`; this
  Goal does not reopen or reinterpret that architecture decision.

# Progress / Discoveries / Next

- Researched current UX/service/accessibility standards and representative
  GitHub agent skills before implementation.
- Chosen minimum sufficient layer: three conditional product/UI skills, not a
  broad UI/UX framework.
- Started from clean `master` synchronized with `origin/master` and created
  branch `task/cads-uiux-product-skills`.
- Implemented the three conditional product/UI skills plus router/docs/test
  wiring without modifying `buildos/**`, legacy sources, or the canonical
  Standard.
- `git diff --check` passes and the changed-file scope matches the Goal.
- Focused bootstrap/candidate tests pass 19/19.
- Full active source-checkout suite passes 68/68 with
  `SIMPLIFIED_ACTIVE_SUITE=PASS`.

Next: verify the final documentation-only checkpoint still satisfies the E2E
cold-start contract, review/stage the exact Goal scope, then capture one clean
local commit. No push, merge or deployment is part of this checkpoint.
