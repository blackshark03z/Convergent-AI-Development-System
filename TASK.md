# Goal

Close the CADS semantic-drift gap exposed when an implementation and its local tests can become internally consistent while silently losing previously accepted/frozen product behavior. Add Accepted Product Contract Continuity as a lightweight execution/acceptance invariant: affected accepted behavior is `MUST-PRESERVE` unless an explicit legitimate Intent/Design change supersedes it.

Preserve the canonical five-control model:

`Reality -> Intent / Design -> Change -> Acceptance -> Consequence`

# Critical User Journey

Tech Lead/Worker begins a material change -> reconstructs current implementation reality and the materially affected accepted product behavior -> identifies only affected must-preserve obligations -> implements/refactors the smallest coherent path -> verifies local component behavior plus required product-level composition -> blocks semantic drift when current code/tests no longer satisfy the accepted journey -> continues without reopening unrelated accepted behavior or adding a new process layer.

# Acceptance

- `skills/core/goal-execution.md` states that accepted/frozen behavior implicated by a change is `MUST-PRESERVE` absent an explicit accepted Intent/Design change.
- Goal Execution distinguishes current implementation reality from accepted product obligation and uses bounded `PRESERVED` / `INTENTIONALLY_CHANGED` / `UNVERIFIED` dispositions.
- Component-level terminal/handoff behavior cannot silently replace a product-level accepted automation/composition contract; the responsible consumer/orchestrator must be identified and verified when the journey requires continuation.
- Accepted configuration semantics cannot silently disappear merely because a surviving subset has green tests.
- `skills/core/product-acceptance.md` treats divergence between internally consistent current code/tests and durable accepted product behavior as regression unless legitimately superseded.
- Product Acceptance requires composition-level evidence for materially affected accepted behavior and does not infer Journey PASS from component PASS.
- No sixth CADS control, phase, lifecycle, state machine, contract registry, traceability matrix, mandatory full E2E run per commit, generic new skill or artifact family.
- `evals/autonomy/cases.json` adds one representative accepted-contract-drift case derived from the real failure archetype while remaining product-agnostic.
- Eval validator/tests require that failure class and continue to fail closed on forbidden lifecycle/runtime state.
- `docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md` remains unchanged.
- Focused regression and full `python scripts/self_test.py` pass with `SIMPLIFIED_ACTIVE_SUITE=PASS`; `git diff --check` passes.

# Non-goals

Do not patch Multiple Automation in this task; do not redesign CADS architecture; do not create a product-contract database; do not require all prior acceptance to be re-proven after every change; do not require real external-provider E2E on every commit; do not add new controls/phases/states; do not change the frozen canonical Standard; no unrelated cleanup.

# Constraints

Current source/runtime/tests remain authoritative for what the implementation does now, not for silently redefining what the accepted product should do. Durable accepted Goal/Intent/Design/CUJ/acceptance remain normative for materially affected behavior until legitimately superseded. Verification depth scales with impact: focused deterministic composition checks during execution, real supported journey at meaningful acceptance convergence points where required.

# Material Decisions

- Fix the gap inside existing Goal Execution + Product Acceptance rather than adding another control or lifecycle.
- Treat semantic preservation as an impact-bounded obligation, not a project-wide traceability exercise.
- A narrower component contract may remain correct; missing product-level composition is fixed at the responsible orchestration layer rather than by bloating the component.
- Do not let implementation-coupled tests self-authorize a reduced product contract.
- Preserve unaffected accepted behavior/evidence when impact analysis supports reuse.

# Progress / Discoveries / Next

- Start HEAD: `62cf2aa4909d1953a94c1c519e497e3c369e80c5`.
- Branch: `codex/product-contract-continuity`.
- Triggering failure archetype: frozen product automation remained durable in SoT while later implementation + local tests converged on manual handoff states and dropped part of accepted configuration semantics.
- Patch scope intentionally limited to existing execution/acceptance guidance plus one representative autonomy eval and regression coverage.
- Autonomy validator: 26 cases PASS; accepted-contract-drift is required coverage.
- Focused autonomy regression: 7/7 PASS.
- Full CADS regression: 112/112 PASS with `SIMPLIFIED_ACTIVE_SUITE=PASS`.
- `git diff --check`: PASS; frozen Standard diff: empty; exactly 7 existing files changed and no new file/artifact family introduced.
- MAR runtime qualification: release `local-3b2dfda71164` detected registered project `cads` as artifact capability and admitted it through recommended `research-artifacts` verification.

Next: use this invariant when reconciling affected product implementations; reopen the CADS mechanism only if evidence shows it misses semantic drift or adds disproportionate ceremony.
