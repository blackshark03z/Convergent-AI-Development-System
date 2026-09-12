# DR-0005: Adopt a lean project architecture description profile

Status: Accepted
Date: 2026-09-12
Scope: Architecture / Process

## Context

CADS already performs proportionate concern coverage before material design freeze, but the project `ARCHITECTURE.md` template did not reliably expose architecture drivers, technology/framework rationale, runtime/deployment views or scenario-based architecture fitness to a fresh AI. This created a legibility gap without proving a need for a new lifecycle/control.

## Decision

Keep the existing Five Controls and frozen Standard. Strengthen project-level architecture through:

- a lean `ARCHITECTURE.md` profile centered on current durable architecture truth;
- explicit material architecture drivers;
- architecturally significant technology/framework choices recorded by role, choice, rationale/trade-off and revisit trigger;
- concern-driven optional views for context, building blocks, runtime, data/state/authority, deployment and trust boundaries;
- a lightweight architecture fitness relation from driver to decision to scenario/evidence/risk;
- one conditional Architecture Description skill under Intent / Design;
- Decision Records for material accepted rationale that must survive turnover.

CADS does not prescribe a universal frontend/backend/database stack or mandatory diagram notation.

## Consequences

- New/fresh AI sessions can reconstruct system shape and critical architecture assumptions more reliably.
- Small/reversible projects may omit irrelevant views and ceremony.
- Architecture description remains subordinate to Git/runtime truth and cannot become a competing implementation authority.
- Product / Design Framing discovers material drivers; Architecture Description records/evaluates durable system shape only when those drivers justify it.
- No new lifecycle, persisted phase, runtime authority or Standard amendment is introduced.

## Revisit

Revisit if representative projects show the profile adds recurring maintenance cost without reducing architecture drift, state/ownership errors, Owner re-explanation or context-reconstruction time; or if a repeated failure class requires a missing viewpoint/evaluation primitive.
