# CADS Existential Challenge

Status: Canonical research method
Date: 2026-09-23
Decision: DR-0014

## Purpose

Attempt to falsify the need for a proposed or existing CADS-specific mechanism
before expanding or preserving it.

The question is not "How should CADS improve this?" The first question is:

> If CADS did not exist, what is the simplest credible way to achieve the same
> accepted product/development outcome?

## Inputs

Provide every lane with the same problem statement, user/Owner objective,
material constraints and evidence of the observed failure class.

Do **not** provide all lanes with the current CADS proposal. Proposal visibility
is lane-specific and should be minimized to preserve search independence.

## Independent lanes

### Lane A — Solution-blind search

Input: problem/Goal only.

Task: derive the strongest solution architecture from first principles and
current available capabilities. Do not optimize for compatibility with CADS.

### Lane B — Existing-system search

Input: problem/Goal only.

Task: find tools, standards, frameworks, protocols and ordinary engineering
practices that already solve all or part of the problem. Prefer adoption,
composition or thin adaptation over rebuilding equivalent machinery.

### Lane C — Practitioner search

Input: problem/Goal only.

Task: determine how capable practitioners and teams actually solve this class of
problem in production, including lightweight practices not represented by a
formal framework.

### Lane D — Failure search

Input: problem/Goal plus candidate approach families, but not other lanes'
conclusions.

Task: find where comparable approaches fail, become obsolete, create lock-in or
produce more coordination/maintenance cost than value.

### Lane E — Adjacent-field search

Input: abstracted problem/Goal.

Task: inspect analogous problems in adjacent engineering disciplines and identify
mechanisms whose semantics transfer without importing unnecessary domain
machinery.

### Lane F — Kill CADS

Input: current accepted CADS guarantees plus the problem/Goal.

Task: remove the disputed CADS mechanism. Construct the smallest alternative
stack that still preserves required Intent/Design, Acceptance, Evidence,
Authority and Consequence semantics. State exactly what cannot be removed and
why.

## Isolation rule

Lanes A-E must not read each other's drafts or a synthesized proposal before
submission. Lane F may see the current accepted CADS guarantees because its job
is adversarial deletion, but it must not see other lanes' conclusions.

Using five agents in one shared conversation does not satisfy this method.

## Synthesis

Only after all completed lane artifacts are frozen may synthesis compare them.

The synthesizer must produce:

- common facts supported across independent lanes;
- genuinely distinct candidate architectures;
- existing mechanisms that can replace CADS-owned mechanics;
- documented failure conditions;
- unresolved evidence gaps;
- the smallest claimed irreducible CADS semantic layer;
- counterfactual experiments needed to test that claim.

Do not choose a winner from rhetoric alone when a bounded benchmark is feasible.

## Counterfactual experiment

Prefer three arms:

- **N0 No CADS**
- **N1 Existing/minimal assembled stack**
- **C Thin CADS**

A benchmark may add a current-system control arm when needed to distinguish a
proposed shrunken residue from the current implementation. The 2026-09
Existential Pilot therefore uses `C-min` and `C-current` separately.

Keep Goal, acceptance meaning and authority equivalent. Record differences in
model/harness/tool access explicitly.

At minimum record:

- final accepted/not-accepted verdict;
- Owner active-attention minutes;
- Owner re-explanation/intervention count;
- wall-clock duration;
- token/model/tool cost when measurable;
- repair iterations;
- false-DONE / escaped-defect / reopen / rollback;
- evidence/oracle strength;
- ceremony and persistent maintenance introduced by the arm.

A mechanism must earn its existence through measurable semantic or operational
value, not through architectural completeness.

## Benchmark integrity

A No-CADS arm must not silently inherit the disputed CADS mechanism through the
benchmark repository, task prompt, hidden evaluator setup or stronger oracle.

When a historical CADS repository is already contaminated by the mechanism under
test, its replay may validate benchmark instrumentation but must not by itself
support an existential verdict.

Prefer product-derived or otherwise neutral baselines for the decisive
counterfactual.

## Decision output

Conclude with exactly one disposition per disputed mechanism:

- KEEP
- SHRINK
- REPLACE
- DELETE
- INCONCLUSIVE — evidence is insufficient; do not promote new durable machinery.

For KEEP/SHRINK, identify the guarantee that fails without the retained piece.
For REPLACE, identify the commodity replacement and only the necessary CADS glue.
For DELETE, identify the simpler baseline that preserves the guarantees.

## Trigger examples

Run the full method for:

- a proposed CADS runtime/lifecycle/router/state store;
- a new mandatory design/spec layer;
- a cross-project authority or evidence mechanism;
- a large increase in Owner ceremony;
- a major model/harness capability jump that may obsolete scaffolding.

Do not run it for routine implementation choices, small reversible refactors or
ordinary product features unless they imply one of the above architecture
changes.

## Current application

The independent A-F round completed on 2026-09-23 and produced a provisional
**SHRINK — benchmark-gated** synthesis. That is research evidence, not an
architecture promotion.

Canonical research artifacts:

- `docs/CADS_EXISTENTIAL_CHALLENGE_SYNTHESIS_2026-09-23.md`
- `docs/CADS_EXISTENTIAL_PILOT_2026-09.md`
- `evals/existential/cads_v1.json`

The pilot distinguishes:

- P0 historical CADS replay — instrumentation/oracle validation only;
- P1 product-derived counterfactual — eligible for existential disposition after
  fairness audit;
- full-project confirmation — required when controlled P1 materially
  differentiates the arms.

The 2026-09 GPT-6 model-routing replay remains evidence for an Existential
Challenge, not justification for GPT-specific CADS architecture. It asks whether
stronger models reduce or eliminate implementation/review scaffolding while CADS
semantic guarantees remain stable.

MAR-vs-DIRECT remains a separate counterfactual dimension so runtime coordination
overhead is not misattributed to CADS or model capability.
