# Goal

Add a thin event-routed core playbook layer so recurring AI-development failure
modes are handled at the right moment without turning CADS into a lifecycle or
workflow engine.

# Critical User Journey

Fresh Tech Lead/Worker enters a project -> reconstructs current reality -> frames
one bounded Goal and acceptance -> implements in small coherent changes -> uses
systematic debugging on the first blocker -> resumes the same real journey ->
proves the canonical runtime/output -> requests Owner acceptance when required ->
performs only bounded workspace closure.

# Acceptance

- Root/project `AGENTS.md` route current events to six core advisory playbooks.
- Four new core skills cover Product Goal Framing, Goal Execution, Systematic
  Debugging and Product Acceptance while existing Cold-Start and Workspace
  Hygiene remain authoritative for their concerns.
- `TASK.md` template carries Critical User Journey and Acceptance Fixture /
  Golden Input without adding schema/lifecycle state.
- `ARCHITECTURE.md` template can state code/data/config/runtime/effect authority
  boundaries when relevant.
- Testing/runtime/observability/UX are not promoted into mandatory core
  subsystems; Thin Guard and the canonical Standard remain semantically
  unchanged.
- Bootstrap/candidate tests prove procedure wiring and all six skills are
  packaged; the full active source-checkout suite passes.
- One clean local task commit is produced; no push, merge or deployment.

# Acceptance Fixture / Golden Input

Bootstrap a temporary empty project from the current package and verify the
resulting canonical project files plus a simplified candidate package built from
the exact source revision.

# Non-goals

No Thin Guard redesign, Standard v2, task/lifecycle engine, persisted skill
state, testing framework, observability platform, UX framework, provider system,
legacy rewrite, remote push, merge or deployment.

# Constraints

- Preserve the simplified native-development architecture.
- Keep procedure routing advisory and current-reality-driven.
- Do not modify `buildos/**`, legacy lifecycle sources, or the canonical
  Convergent AI Development Standard for this Goal.
- Reuse existing bootstrap/package mechanisms rather than adding a new loader or
  registry.

# Material Decisions

- Core remains exactly six playbooks: Project Cold-Start, Product Goal Framing,
  Goal Execution, Systematic Debugging, Product Acceptance, Workspace Hygiene.
- `AGENTS.md` is the event router; skills are procedures; project templates hold
  context; scripts/tests verify mechanical wiring only; Thin Guard retains only
  consequential-action safety.
- Stable Goal + small coherent implementation batches is the execution model.
- A removed blocker returns immediately to the original journey; non-blocking
  anomalies become deferred debt.
- The simplified thin-guard lineage remains rooted in baseline `8970dc8`; this
  Goal does not reopen or reinterpret that architecture decision.

# Progress / Discoveries / Next

- Final architecture review completed before implementation.
- Local branch `task/cads-event-routed-core-playbooks` created from clean
  `origin/master` baseline `199a7768c5f909f62d3fd83c1252a095ae6c10de`.
- Existing Standard already contains most durable invariants; the missing layer
  is event-triggered procedure routing, not another Standard revision.
- Existing bootstrap is intentionally non-destructive and project templates are
  the correct place for CUJ/golden-input and authority-boundary context.
- Focused bootstrap/candidate tests pass 18/18.
- Full suite exposed one compatibility-only failure: root `TASK.md` must retain
  the historical `# Progress / Discoveries / Next` heading used by the E2E
  cold-start contract. The root task now preserves that contract without
  weakening the new project template.
- The affected E2E cold-start test passes after the compatibility fix.
- Full active source-checkout suite passes 67/67 with
  `SIMPLIFIED_ACTIVE_SUITE=PASS`.

Next: review final diff/scope, rerun verification on the exact final bytes, then
capture one clean local task commit. No push, merge or deployment.
