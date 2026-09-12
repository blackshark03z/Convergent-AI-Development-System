# CADS Autonomy Implementation Plan

Status: Candidate implementation plan
Date: 2026-09-12
Depends on: DR-0003, DR-0004, `docs/CADS_AI_AUTONOMY_RESEARCH_2026-09.md`

## Goal

Increase verified autonomous completion and reduce Owner attention without
adding a second CADS task runtime or duplicating model-harness capabilities.

This plan deliberately separates **accepted architecture direction** from
**mechanisms that still require evaluation**. The Standard remains frozen unless
its existing Freeze Rule is independently satisfied.

## North-star and guard metrics

Primary:

- Owner active-attention minutes per verified accepted Goal;
- time-to-verified-done.

Guard metrics:

- false-DONE / escaped-defect rate;
- reopen, rollback and post-integration repair rate;
- Owner re-explanation load;
- repair iterations, wall-clock and compute/token cost, stratified by risk;
- percentage of acceptance criteria backed by relevant identity-bound evidence;
- consequential incident rate;
- fresh-review incremental defect discovery when fresh review is used.

Do not optimize one metric in isolation. Compare similar task/risk classes so a
shift toward easier tasks or weaker oracles cannot look like autonomy progress.

## Workstream 0 — Correct current acceptance authority

### Change

Align `skills/core/product-acceptance.md` with the existing Standard:

- Owner remains the final oracle for subjective experience/product judgement and
  Owner-controlled material trade-offs;
- fully machine-observable acceptance, including a user-facing journey when its
  predefined criteria are objectively decidable, may be closed autonomously;
- mixed Goals close machine-observable criteria autonomously while unresolved
  subjective criteria remain Owner-controlled;
- engineering PASS/build/CI/browser evidence must not be substituted for an
  actually subjective Owner criterion.

Also make oracle mutation visible in acceptance reasoning: a materially changed
acceptance/test after implementation began must be shown to be a legitimate
clarification rather than a weakening made to obtain PASS.

### Acceptance

- no mandatory Owner ceremony exists solely because a product has a UI;
- no subjective Owner criterion can be silently converted into engineering PASS;
- no Standard amendment is required.

## Workstream 1 — Evidence Envelope / Oracle Integrity prototype

### Purpose

Test whether a small identity-bound evidence envelope materially reduces false
DONE/rework without creating process ceremony.

### Candidate minimum

Evaluate only the fields needed to establish:

- Goal/criterion identity;
- base and candidate revision/build identity;
- oracle/verifier identity and version where meaningful;
- PASS/FAIL/UNKNOWN result;
- evidence references;
- relevant runtime/environment identity;
- must-preserve invariant results;
- required consequential authorization status;
- material reviewer blocking findings when review is required;
- derived technical verdict.

Do not include task lifecycle, retry history, agent thoughts, planner state,
subagent graph or model-routing history.

### Oracle Integrity checks

For criteria where a test/oracle was modified by the implementation change,
record enough provenance to distinguish:

- accepted requirement/oracle clarification;
- legitimate new regression coverage;
- implementation-coupled self-proof or weakened acceptance.

Do not automatically block all test changes. The invariant is independent
validity, not immutability of tests.

### Verdict semantics

Prefer three values:

- `VERIFIED`: all required criteria/invariants have relevant trusted evidence;
- `NOT_VERIFIED`: at least one required criterion/invariant is contradicted or
  failed;
- `UNKNOWN`: required evidence is missing/ambiguous.

The Worker must not directly set the derived technical verdict.

### Kill/shrink criterion

After representative trials, shrink or remove the envelope if it adds material
latency/ceremony without reducing false-DONE, escaped defects, Owner QA or
re-explanation load.

## Workstream 2 — CADS Autonomy Eval Suite

### Purpose

Measure whether CADS changes improve the actual 1 Owner + AI operating model.

### Initial set

Build approximately 15–25 representative Goals from real failure classes rather
than synthetic prose-only tests. Include, where examples exist:

- state leakage across repeated workflows;
- feature PASS but end-to-end journey failure;
- runtime/source identity mismatch;
- provider ambiguity or external-effect retry uncertainty;
- missing/weak acceptance oracle;
- acceptance/test mutation during a fix;
- architecture/source-of-truth drift;
- repeated repair that stops converging;
- persistent-state/migration compatibility;
- UI discoverability/next-action failure;
- interacting isolated candidates with compatible and incompatible assumptions.

### Compare

At minimum compare current thin CADS behavior with the proposed B-prime
mechanisms on matched task classes.

Collect:

- Goal result and acceptance evidence;
- Owner active-attention minutes;
- Owner re-explanation count;
- wall-clock and model/tool cost;
- repair iterations;
- false-DONE/escaped defects;
- rollback/reopen;
- evidence coverage and oracle strength.

The eval suite is the gate for future autonomy claims. Do not promote a mechanism
because it sounds agentic.

## Workstream 3 — MAR authority-boundary audit

For each MAR capability, answer:

1. What invariant/guarantee is required by CADS/product safety?
2. Does the selected vendor/harness already provide that guarantee?
3. Is the guarantee inspectable/auditable enough to rely on?
4. Does MAR need to enforce the missing part, or only verify/bind it?
5. Would retaining the MAR implementation create duplicate authority or
   maintenance cost?

### Prefer to retain in MAR / integration authority

- canonical integration authority;
- exact candidate/source identity and evidence binding;
- consequential effect/mutation authority;
- stale-writer/process fencing where concurrent mutation can outlive logical
  authority;
- crash-safe integration/recovery guarantees;
- cross-provider telemetry/audit that is required to compare or govern
  autonomous execution.

### Prefer vendor/harness ownership when guarantees are adequate

- generic planning/task decomposition;
- generic subagent scheduling;
- model routing;
- context compaction;
- ordinary browser/computer control;
- ordinary self-repair loops;
- generic sandbox/worktree mechanisms that already meet the required isolation
  semantics.

Document gaps instead of automatically rebuilding provider capabilities.

## Workstream 4 — Conditional capabilities after the baseline is measured

Do not build these before Workstreams 1–3 produce evidence.

### Fresh Reviewer

Use a read-only fresh reviewer only when risk/oracle weakness/semantic novelty
justifies it. Candidate triggers:

- security/auth/permission/secrets;
- consequential external effects;
- persistence/migration/architecture-boundary changes;
- weak/non-deterministic oracle;
- repeated repair without convergence;
- interacting parallel-candidate assumptions;
- material acceptance/test change by the implementation Worker.

Reviewer may report blocking/non-blocking/unknown findings but may not mutate the
candidate, change Goal/acceptance or advance canonical state.

### Parallel isolated candidates

Permit multiple candidate writers only when decomposition is sufficiently
independent and each writer is isolated. Exactly one integration authority
advances canonical state. Measure wall-clock savings against semantic
reconciliation/merge cost.

### Eval-gated autonomy profiles

Define profiles by demonstrated capability against representative evals, not by
model/vendor name. Production telemetry may trigger re-evaluation but must not
silently raise authority online.

## Portable skill packaging

Keep one canonical CADS knowledge source. Agent Skills / `SKILL.md` compatible
projections may be added when they improve portability across supported
harnesses. Do not add a skill-sync daemon, knowledge database or duplicated
vendor-specific standards without evidence of need.

## Explicit non-goals

This plan does not authorize:

- a CADS task database, phase machine or new lifecycle;
- permanent planner/architect/coder/QA/reviewer organizations;
- global vector/knowledge/context databases;
- generic cross-vendor model routing;
- always-on LLM review;
- online self-modifying CADS policy;
- agent-authored final DONE as technical authority;
- multiple agents concurrently mutating canonical state;
- automatic weakening/suppression of tests or acceptance to obtain PASS.

## Promotion rule

A candidate mechanism becomes a durable CADS/MAR responsibility only when it
shows measurable benefit on representative Goals or closes a serious safety/
authority gap that existing controls cannot guarantee. When promoted, apply
DR-0003's symmetric consolidation question: what can now be removed, delegated
or kept advisory?
