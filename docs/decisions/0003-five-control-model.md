# DR-0003: Consolidate CADS around five engineering controls

Status: Accepted
Date: 2026-09-08
Scope: Process architecture

## Context

Real project failures improved CADS in useful ways: Story Audio exposed journey
composition gaps; Multiple Automation exposed domain/cardinality discovery gaps;
and Story Audio later exposed repeat-cycle state lifetime/re-entry leakage. The
individual corrections were defensible, but they also revealed an accretion
pattern: each new failure class could tempt CADS to add another standalone
procedure.

An independent senior-review gate classified CADS as `EARLY_PROCESS_ACCRETION`
and returned `REFACTOR_WITH_CORRECTIONS`. It supported a smaller universal mental
model only if the concrete trigger-questions learned from real failures survived
the consolidation.

## Decision

Organize CADS conceptually around five reasoning controls:

1. Reality — reconstruct trustworthy current source/runtime/workspace/decision truth.
2. Intent / Design — frame Goal/CUJ/acceptance and surface only material,
   expensive-to-get-wrong design drivers and assumptions.
3. Change — make the smallest coherent change and verify it.
4. Acceptance — prove the real supported outcome, not isolated feature success.
5. Consequence — guard applicable destructive/external/privileged/high-cost effects.

Merge standalone Concern Coverage Review into Product / Design Framing while
preserving its useful lenses and assumption attack. Keep the existing
`product-goal-framing.md` filename to minimize activation/package churn, but its
role becomes Product / Design Framing. Remove the standalone
`concern-coverage-review.md` playbook.

Systematic Debugging and Workspace Hygiene remain valuable conditional methods,
not universal control stages. User-Facing Workflow, Frontend Design and UI
Quality Review remain conditional product/UI methods.

State Lifecycle & Ownership does not become a new skill. Repeatable/persistent/
asynchronous workflows receive an explicit design lens covering scope, owner,
lifetime, snapshot/freeze, terminal behavior, reset/persist, re-entry and stale-
state isolation, plus a repeat-cycle Product Acceptance oracle.

Concurrency/fencing, external-effect ambiguity/idempotency, security, migration,
performance and similar disciplines remain conditional design lenses or targeted
research, not new universal procedures.

## Why

CADS should control engineering uncertainty and consequence, not become an
encyclopedia of software disciplines. AI can pull specialist knowledge on demand
once a material concern is identified. A small stable control model reduces
routing/cognitive load while explicit lenses preserve failure coverage that was
paid for through real project evidence.

The same primitives scale by depth: a tiny reversible local tool uses almost no
ceremony; Story Audio needs journey/state-cycle evidence; Multiple Automation
needs deeper domain/ownership/external-effect reasoning; MAR-like infrastructure
needs concurrency/fencing/recovery/authority reasoning.

## Anti-bloat rule

When a new failure appears:

1. handle project-specific specialist knowledge locally;
2. if an existing control should have caught it, fix that control;
3. if one existing lens/question is missing, refine it;
4. create a new procedure only for genuinely different recurring behavior that
   cannot fit current controls and is justified by repeated evidence or serious
   consequence.

Every proposed ADD must include the symmetric question: what can now be MERGED or
DELETED? One anecdote can justify a lens refinement, not a new universal
procedure, unless the consequence is serious enough to satisfy the Standard's
existing Class A Freeze Rule.

## Consequences

The standalone Concern Coverage Review is removed but its material coverage is
not. The universal mental model becomes smaller. Debugging/hygiene/UI methods
remain available without dominating project entry. No process lifecycle, review
state, approval board, database, runtime or new authority is introduced.

## Revisit When

Revisit CADS only when a real project demonstrates either a Class A serious
failure or a repeated systemic failure that current controls/lenses do not
handle. Any amendment must include a consolidation check so CADS can shrink as
well as grow. Do not reopen CADS for hypothetical completeness, new terminology,
or specialist knowledge that can be researched on demand.