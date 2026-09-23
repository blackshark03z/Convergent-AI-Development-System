# CADS Existential Pilot — 2026-09

Status: Frozen benchmark design; runs not yet started
Research basis: `docs/CADS_EXISTENTIAL_CHALLENGE_SYNTHESIS_2026-09-23.md`
Protocol: DR-0014

## Question

Does a minimum CADS semantic residue materially improve verified accepted
product outcomes, Owner attention, false-DONE/escaped-defect rate, identity
correctness, or consequence safety versus a credible existing-tool stack?

The benchmark is allowed to conclude that CADS should disappear as a named
system.

## P0 is instrumentation-only

Historical CADS changes are useful because they have pinned revisions and known
held-out reference tests. They are not a valid No-CADS product baseline because
the repository itself already contains CADS concepts.

P0 may validate:
- isolated candidate creation;
- reference-diff secrecy;
- held-out oracle materialization after candidate completion;
- result/identity capture;
- timing/token/Owner-attention accounting;
- harness failure vs model failure separation.

P0 results cannot determine CADS existential status.

## P1 — product-derived counterfactual

P1 uses five pre-existing product failure classes selected before any arm runs:

1. simple reversible fast path;
2. material intent ambiguity;
3. end-to-end journey composition;
4. evidence / source-artifact-runtime identity;
5. consequential or ambiguous external effect.

Pinned histories live in `evals/existential/cads_v1.json`.

## P1 neutral projection rule

Do not give N0 an accidentally CADS-enriched repository and call it No-CADS.

For each product base:

1. Create disposable isolated source copies/worktrees.
2. Audit repository artifacts as product-native truth, ordinary engineering
   configuration, or CADS/process-specific control artifacts.
3. Keep product code, product-native docs, build/test configuration and
   historical product facts equivalent.
4. Build one neutral product projection that does not expose CADS process
   artifacts by default.
5. Inject arm-specific instructions outside the candidate source tree where
   possible; otherwise record exact bytes as benchmark metadata.
6. Candidate never sees reference implementation diff or held-out reference
   tests before stopping.
7. Evaluator applies the same held-out oracle to every arm.

If neutral projection cannot be created without changing product behavior, mark
the case INCONCLUSIVE.

## Fixed R→I topology

P1 evaluates a two-role operating model:

```text
Owner Raw Goal
  -> R: strong reasoning model
  -> Implementation Brief
  -> I: cost-efficient implementation model
  -> candidate + evidence
  -> same R: READY or one REPAIR
  -> frozen candidate
  -> held-out evaluator
```

R and I are roles, not provider/model names. One comparison batch fixes the same
R model/profile and I model/profile across every arm.

R does not edit product code. I does not see the held-out oracle. R READY and I
DONE are not Product Acceptance.

The detailed contract is frozen in
`docs/CADS_RI_BENCHMARK_PROTOCOL_2026-09.md`.

### Spec Sufficiency

The benchmark uses:

> **SPEC UNTIL TESTABLE, NOT SPEC UNTIL COMPLETE.**

R should stop specifying when:
1. multiple implementations could validly satisfy the contract;
2. PASS/FAIL can be judged from observable outcome without a reference patch; and
3. I no longer needs to invent a material product preference or consequence
   boundary.

This rule applies to all arms. The treatment difference is whether and which
semantics R is explicitly required to preserve.

## Arms

### N0 — No CADS
Raw Owner Goal + neutral product snapshot. R uses its normal reasoning with no
CADS semantic pack or prescribed spec method.

### N1 — existing/minimal assembled stack
N0 plus ordinary repository documentation, tests, browser tooling and normal
engineering conventions. No CADS-specific process.

### C-min — minimum CADS residue
N1 plus only:
- Outcome/Intent boundary;
- Acceptance/Oracle-integrity boundary;
- Evidence/Identity boundary;
- Consequence/Authority boundary;
- proportional assurance;
- deletion/replaceability.

### C-current — current Thin CADS
R receives the current Thin-CADS semantics relevant to the task, still bounded by
the same Spec Sufficiency stop condition.

## Controls

Within one case:
- same raw Owner Goal;
- same R model/profile and reasoning effort;
- same I model/profile and reasoning effort;
- same product base and environmental preconditions;
- same tool/network/effect authority;
- same maximum one R-requested repair cycle;
- same hidden held-out oracle;
- same Owner-intervention policy.

Changing R or I model/substrate creates a different comparison batch.

## Metrics

Primary: `verified accepted Goals / Owner active-attention minutes`.

Also record:
- first-pass and final acceptance;
- false-DONE;
- escaped defect/reopen/rollback;
- repair iterations;
- Owner active minutes/interventions/re-explanations;
- wall-clock;
- token and model/tool cost where measurable;
- scope escape;
- product-level evidence coverage;
- candidate identity;
- source/artifact/runtime identity when relevant;
- unauthorized/duplicated/ambiguous effects;
- persistent arm artifacts;
- follow-up maintenance burden.

A serious consequence failure cannot be averaged away.

## Held-out oracle rule

1. Candidate starts at pinned base.
2. Candidate sees raw Goal + its arm context only.
3. Candidate may use tests already present at base.
4. Candidate stops.
5. Evaluator materializes only pre-frozen outcome-oriented held-out checks.
6. Evaluator runs held-out checks plus active base-compatible product checks.
7. Exact patch equality is never required.

Reject reference tests that encode reference implementation shape instead of the
intended outcome.

## P1 cases

### XP-001 — Story Audio primary action remains visible
- failure class: AE-025
- project: Story Trans And Audio
- base: `b6a9efb1de053edccbf9541deaaf21a830d71727`
- reference: `dbef3b7`
- purpose: ceremony-floor fast path
- reference oracle candidates:
  - `tests/test_production_workflow_browser.py`
  - `scripts/browser_range_input_workflow_smoke.mjs`
  - `scripts/browser_production_task_workbench_smoke.mjs`

C-min/C-current must not impose material ceremony versus N0/N1.

### XP-002 — AutoVideoPipeline stock proposal intent
- failure class: AE-022
- project: AutoVideoPipeline
- base: `eb0a6480962612865a4974c960e6c6547b7b2009`
- reference: `9051238`
- historical oracle candidate: `tests/test_stock_proposal_plan.py`
- raw historical Owner Goal must be reconstructed and frozen before the run.

If the Goal cannot be reconstructed without reverse-engineering the reference
solution, this case is ineligible for the final verdict.

### XP-003 — Story Audio fresh Assignment journey
- failure class: AE-002
- project: Story Trans And Audio
- base: `e07820fcc43f1dbfb1de84feb32fee6cfd4329f2`
- reference: `25a09b4`
- oracle candidates:
  - `tests/test_assignment_workflow_browser.py`
  - `tests/test_character_assignment_browser.py`
  - `tests/test_speaker_review_suggestions.py`
  - `scripts/browser_assignment_flow_smoke.mjs`

The oracle must prove the complete affected journey/handoff, not isolated DOM
presence or unit success.

### XP-004 — AutoVideoPipeline verification/lineage gap
- failure class: AE-003
- project: AutoVideoPipeline
- base: `79ac228d14b1ac743ab760bc4c87f87adc433533`
- reference: `07ed3af`
- oracle candidates:
  - `tests/test_independent_repairs.py`
  - `tests/test_real_golden_cujs.py`
  - `tests/test_golden_cujs.py`

Pre-run evaluator must select outcome-oriented held-out checks and reject
reference-shape assertions.

### XP-005 — Multiple Automation uncertain phone submission
- failure classes: AE-004 + AE-015
- project: Multiple Automation
- base: `7683e2617f2aacb962c905bfe1eb67a749252f6d`
- reference: `36c954f`
- oracle candidates:
  - `tests/test_runtime_adapters.py`
  - `tests/verification_state.test.mjs`
- live consequential submission: FORBIDDEN.

Use local/provider fixtures and require correct reconciliation/no-blind-
redispatch behavior.

## Full-project confirmation

If controlled P1 materially differentiates N1, C-min and C-current, repeat at
least one low-risk and one high-consequence case in the full real product repo.

## Decision rule

- N1 >= C-min with equal/better guards and lower/equal burden:
  REPLACE/DELETE CADS residue.
- C-min > N1 and C-current adds no material value:
  SHRINK CADS to C-min.
- C-current closes a repeated material failure C-min cannot:
  retain only that demonstrated mechanism.
- evaluator/projection fairness insufficient:
  INCONCLUSIVE.

No promotion from rhetoric or lane consensus alone.
