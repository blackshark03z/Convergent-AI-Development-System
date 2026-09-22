# DR-0014: Require an existential challenge before durable CADS expansion

Status: Accepted
Date: 2026-09-23
Scope: Research / Architecture / Evaluation / Build-vs-Borrow

## Context

Recent CADS iterations repeatedly improved only after comparing proposed machinery
against simpler existing approaches. OpenSpec/spec workflows, direct coding
harnesses and MAR-vs-direct execution exposed a recurring research-order defect:
CADS could design a complete mechanism before proving that the missing capability
was not already available more cheaply in the ecosystem or in a stronger model
or harness.

Multiple reviewers sharing the same proposal/context are not sufficiently
independent for this purpose. They can disagree while remaining anchored to the
same architecture, assumptions and search space. The relevant independence is
independence of search objective and initial context before synthesis.

CADS already requires adaptive controls, replaceable spec substrates, direct
execution by default, representative autonomy evals and removal of stale
capability scaffolding. This decision adds a falsification rule for durable CADS
architecture; it does not add a sixth CADS control or a research runtime.

## Decision

Before adding or materially expanding a durable CADS mechanism, perform an
**Existential Challenge** when the change is load-bearing, hard to reverse,
cross-cutting, or triggered by a material step-change in model/harness capability.

The challenge must start from the null hypothesis:

> CADS should not own this mechanism unless simpler existing systems, stronger
> agents/harnesses and a minimal assembled stack fail to provide the required
> semantic guarantee at lower total cost.

Research lanes are isolated until they submit their findings. At minimum use the
following search objectives when relevant:

- **A — Solution-blind search:** see only the problem/Goal; derive the strongest
  solution without seeing the current CADS proposal.
- **B — Existing-system search:** identify products, standards, frameworks and
  ordinary engineering mechanisms that already solve all or part of the problem;
  do not see proposal A.
- **C — Practitioner search:** investigate how strong practitioners/teams
  actually solve the problem in current production work, including where their
  practice differs from published frameworks.
- **D — Failure search:** look for failed, abandoned, over-engineered or
  non-scaling approaches and the conditions that caused failure.
- **E — Adjacent-field search:** inspect analogous problems in other engineering
  disciplines for transferable mechanisms.
- **F — Kill-CADS search:** deliberately design the smallest viable system that
  removes as much CADS-specific machinery as possible while preserving the
  accepted Goal and safety/authority semantics.

A synthesis agent/reviewer sees lane outputs **only after the lanes are
complete**. It may reconcile evidence but must not rewrite lane results to create
consensus.

## Counterfactual benchmark

Research argument alone is insufficient when the disputed mechanism can be
tested. Compare equivalent Goals/oracles across, at minimum:

1. **No-CADS baseline** — Owner + capable coding/research harness + repository +
   normal tests/CI, with no CADS-specific mechanism under evaluation.
2. **Existing/minimal assembled stack** — commodity tools/standards composed with
   the smallest glue required, still without the disputed CADS mechanism.
3. **Current/Candidate Thin CADS** — only the CADS semantics/mechanisms actually
   under evaluation.

Keep Goal meaning, authority and acceptance strength equivalent. Do not weaken a
baseline or make a CADS arm win by giving it better problem information,
stronger oracles or materially different tools without recording that difference.

Measure the existing autonomy north-star and guards: accepted Goals per Owner
attention, re-explanation/intervention load, wall-clock time, model/tool cost,
repair loops, false-DONE/escaped defects, recovery quality, evidence coverage and
ceremony/maintenance burden.

The valid outcomes are:

- **KEEP** — representative evidence shows the CADS-specific mechanism closes a
  real semantic gap at acceptable cost.
- **SHRINK** — keep only the irreducible guarantee; delete replaceable mechanics.
- **REPLACE** — use an existing/commodity mechanism and retain only required
  integration semantics.
- **DELETE** — remove the CADS-specific mechanism because a simpler baseline
  preserves the accepted guarantees.

DELETE is a successful research outcome, not a failed review.

## Trigger discipline

Do not run a full Existential Challenge for every feature or reversible local
change. Trigger it for material architecture decisions, new persistent
state/lifecycle/router/runtime/scaffolding, substantial Owner burden/ceremony, a
major new external tool that may replace CADS machinery, or a material
model/harness capability jump.

A small targeted ecosystem scan and deletion test is sufficient for lower-cost
decisions.

## Relationship to CADS controls

The Existential Challenge is a research/decision method around the Five Controls,
not a sixth control and not a workflow state machine.

It grants no mutation, Git, runtime or consequence authority. Its artifacts are
advisory evidence until an accepted Decision Record changes canonical direction.

Existing autonomy cases for capability obstruction, harness semantic lock-in,
stale capability scaffolding, owner-burden stagnation and correlated verifier
blind spots remain the executable pressure tests. Do not duplicate those
semantics into a new lifecycle.

## Consequences

- Build-vs-borrow becomes a falsifiable architectural question rather than a
  preference.
- CADS is expected to get smaller as commodity agents/harnesses absorb mechanics
  that CADS once needed.
- Independent research means independent search objectives/context before
  synthesis, not merely multiple agents debating one shared proposal.
- Major capability releases such as a new frontier coding model become triggers
  to re-test existing scaffolding instead of reasons to immediately add model-
  specific architecture.
- Model/harness benchmark evidence can inform the challenge without becoming a
  CADS-owned model router.

## Explicitly rejected

Do not add:

- a permanent multi-agent debate council;
- a mandatory six-lane ceremony for routine work;
- a research workflow database or lifecycle;
- a requirement that CADS must survive the challenge;
- an evaluation score that automatically preserves existing CADS machinery;
- a named tool/model dependency in CADS Core; or
- architecture whose justification is only that it is more comprehensive.

## Revisit

Revisit this decision if independent counterfactual evidence shows the challenge
costs more Owner attention than the architecture churn it prevents, or if a
future harness can natively provide equivalent blind research, counterfactual
evaluation and decision provenance at lower cost.

CADS has no architectural entitlement beyond the smallest semantic guarantees
that simpler existing systems and stronger future agents fail to provide.
