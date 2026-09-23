# CADS R→I Benchmark Protocol v1 — 2026-09

Status: frozen benchmark protocol candidate

## Purpose

Measure whether CADS semantics improve the handoff from a strong reasoning AI
(R) to a cheaper implementation AI (I), without conflating the result with model
quality, implementation topology, or evaluator quality.

## Fixed topology

```text
Owner Raw Goal
    ↓
R — strong reasoning model
    ↓
Implementation Brief
    ↓
I — cost-efficient coding model
    ↓
candidate + self-check evidence
    ↓
same R
    ↓
READY or one REPAIR brief
    ↓
freeze candidate
    ↓
held-out evaluator
```

R and I are roles, not model names. The same R model/profile and the same I
model/profile must be used for every arm in one comparison batch.

## R responsibilities

R may:
- inspect the neutral repository and product reality;
- clarify material ambiguity;
- produce the smallest sufficient product/implementation contract;
- review the candidate, diff and visible verification evidence;
- issue at most one repair brief;
- declare READY when the candidate is ready for independent evaluation.

R must not:
- edit product code in this benchmark;
- see the reference implementation or held-out oracle;
- treat its own READY judgment as Product Acceptance;
- invent Owner preferences or consequence authority.

## Spec Sufficiency rule

**SPEC UNTIL TESTABLE, NOT SPEC UNTIL COMPLETE.**

The contract is sufficient when all are true:

1. Multiple implementations could legitimately satisfy it.
2. An evaluator can distinguish PASS from FAIL from observable outcome without
   knowing the historical/reference patch.
3. No material product preference, irreversible choice, or consequence boundary
   is left for I to silently invent.

Once these conditions hold, R should stop specifying and hand off execution.

### Minimal default contract

For ordinary material work the brief should contain only what is needed from:

- Outcome
- Acceptance
- Constraints / Non-goals
- Effects / Authority
- material assumptions or open questions, only if needed

Technical design, file-level plans, task decomposition, state diagrams, migration
plans, or architecture detail are added only when they reduce a triggered
ambiguity/risk. They are not mandatory artifacts.

## I responsibilities

I receives only:
- the neutral product workspace;
- R's Implementation Brief;
- common execution rules.

I owns implementation method, code edits, local tests, product/browser checks and
repair within the brief.

I must not see:
- arm identity unless it is inherently present in the brief;
- historical/reference patch;
- held-out oracle;
- sibling-arm results.

## Review / repair

After I stops, R receives:
- candidate diff/revision;
- checks actually run and their output/evidence;
- I's completion report.

R returns exactly one of:
- `READY`
- `REPAIR: <bounded repair brief>`

Maximum: one repair cycle for the initial pilot.

After READY, candidate mutation stops before held-out evaluation.

## Independent acceptance

R READY and I DONE are claims, not Product Acceptance.

Only after candidate freeze does the evaluator materialize the pre-frozen
held-out oracle and score the exact candidate.

A run is FALSE-DONE when the candidate is declared READY but the held-out oracle
fails on an acceptance condition the candidate was expected to satisfy.

## Arm isolation

All arms share:
- same frozen Raw Owner Goal;
- same neutral product snapshot;
- same R model/profile;
- same I model/profile;
- same environment and authority;
- same implementation/review-cycle budget;
- same hidden evaluator.

Only R's semantic treatment differs by arm.

## Metrics

Primary:
- verified accepted Goals / Owner active-attention minute

Also record:
- first-pass and final acceptance;
- false-DONE;
- R tokens/cost/time;
- I tokens/cost/time;
- number of R→I handoffs;
- repair count;
- Owner intervention/re-explanation;
- brief length;
- material assumptions invented by I;
- scope escape;
- product-level evidence coverage;
- candidate/source/artifact/runtime identity where material;
- consequence failure;
- total inference cost;
- cost / accepted change.

## Interpretation

The benchmark is not trying to prove that more specification is better.

If N1 produces equally accepted outcomes with less brief/coordination cost than
C-min, the CADS spec semantics should shrink or disappear.

If C-min prevents wrong-product implementation, false-DONE, identity drift or
unauthorized effects at low additional cost, only that measured residue earns a
place in CADS.
