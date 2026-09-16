# Goal

Implement the independently reviewed **SHRINK** outcome for CADS Intent / Design vNext: strengthen the existing `Intent / Design` control so vague Owner intent and machine-heavy workflows are handled with proportionate design sufficiency, without adding another control, lifecycle, phase, artifact family, role or skill.

Preserve the canonical five-control model:

`Reality -> Intent / Design -> Change -> Acceptance -> Consequence`

# Critical User Journey

Owner provides a bounded but possibly vague product outcome -> AI Tech Lead inspects/researches current reality and resolves cheap reversible choices autonomously -> consequential unresolved design decisions are surfaced only when they are load-bearing -> machine-heavy behavior is described through a conditional behavioral/system-flow view when CUJ alone is insufficient -> implementation proceeds once load-bearing decisions are resolved, empirically reduced, or cheaply deferred with bounded impact -> later intent changes propagate through affected behavior/state/architecture/acceptance before local patching -> unaffected evidence remains reusable when supported.

# Acceptance

- No new CADS control, skill, lifecycle, persisted design state machine, mandatory artifact family, universal design-review phase or product-designer role.
- `docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md` remains unchanged.
- `product-goal-framing.md` makes AI responsible for closing engineering/product-system knowledge gaps as far as practical, builds an Owner decision surface only when needed, and defines explicit Design Sufficiency rather than design completeness.
- `GOAL_READY` requires unresolved load-bearing decisions to be resolved, empirically reduced, or explicitly/cheaply deferred with bounded downstream impact.
- Behavioral/System Flow is conditional, triggered only by observable workflow conditions, and distinguishes user CUJ, required system behavior and architecture realization.
- Brownfield behavioral views are reconciled against current source/runtime reality before constraining additions.
- Representative-user/context evidence is conditional on acceptance impact and Owner representativeness; personal tools do not inherit mandatory UX research.
- Unresolved load-bearing design questions, when any remain, use only the minimum working set in existing `TASK.md`; no new ledger/schema/database is introduced.
- `goal-execution.md` propagates clarified/revised intent across affected CUJ, behavior flow, state/data/authority, architecture contract and acceptance before patching; only affected scope/evidence is reopened.
- `evals/autonomy/cases.json` contains exactly 25 cases with AE-022 through AE-025 covering intent ambiguity, machine-workflow behavior, intent-change impact and the simple-task ceremony floor.
- `scripts/validate_autonomy_evals.py` requires those four new failure classes while keeping schema version unchanged and max case count at 25.
- `docs/CADS_AUTONOMY_EVAL_SUITE.md` reports 25 cases and names the new Intent/Design failure coverage concisely.
- `python scripts/validate_autonomy_evals.py`, `python scripts/self_test.py` and `git diff --check` pass; full regression retains `SIMPLIFIED_ACTIVE_SUITE=PASS`.
- Final diff contains only the bounded paths in this task, with no Standard diff and no unrelated cleanup.

# Non-goals

No sixth CADS control; no new `intent-design.md` or `functional-decomposition.md` skill; no persisted design workflow/state machine; no mandatory PRD/UML/BPMN/C4/requirements matrix; no mandatory prototypes or fixed N-alternatives; no universal design-review phase; no product-designer role; no orchestration/runtime machinery; no evidence-envelope/oracle-integrity/safety-floor work; no repo-wide rewrite of requirements language; no unrelated cleanup.

# Constraints

Implement as refinement of existing skills only. Design completeness is not required. Simple reversible tasks must retain a fast path with very little ceremony. Behavioral/system-flow modeling remains conditional and must describe required/existing behavior rather than proposed components. New acceptance wording should be singular and independently verifiable when practical, but existing requirements are not being rewritten repo-wide.

# Material Decisions

- Implement the independent-review verdict `SHRINK`, not the original broad A?G proposal.
- Keep design sufficiency inside the existing `Intent / Design` control; no new lifecycle, skill or artifact family.
- Make Behavioral/System Flow conditional and separate from CUJ and architecture realization.
- Preserve the simple reversible-task fast path and reopen only scope affected by later intent changes.

# Progress / Discoveries / Next

- Start HEAD: `3dab33a621c2b25db14a09219a836c628c0a0a83`.
- Isolated worktree/branch: `codex/intent-design-vnext-shrink`.
- Autonomy eval validator: PASS with 25 cases and all four new required failure classes covered.
- Focused regression for eval/cold-start/architecture/bootstrap behavior: 30/30 PASS.
- Full CADS regression: 110/110 PASS with `SIMPLIFIED_ACTIVE_SUITE=PASS`.
- `git diff --check`: PASS.
- Frozen Standard diff: empty.
- One directly related stale regression expectation was updated from 21 to 25 cases; no unrelated test or runtime machinery was added.

Next: final anti-accretion review, then commit and push the isolated branch.
