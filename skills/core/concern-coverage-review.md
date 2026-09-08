# Concern Coverage Review

An advisory, bounded cross-concern review for exposing material gaps and unsafe
assumptions before a hard-to-reverse design decision. It creates no lifecycle
phase, persisted review status, compliance database, or architecture authority.

Use the canonical development semantics in
`docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`. This playbook operationalizes the
AI Tech Lead's Knowledge-Gap Responsibility; it is not a claim that all unknown
unknowns can be eliminated.

## When to use

Use when:

- a new or materially changed architecture, domain model, source-of-truth model,
  ownership boundary, or authority boundary is about to be treated as stable;
- the Goal has multiple actors, domain objects, providers, external effects,
  persistent data authorities, concurrency/resource ownership, or other coupled
  concerns whose assumptions can materially change the design; or
- new evidence changes a material assumption, risk profile, supported context,
  or external contract behind an earlier design decision.

Do not use for a tiny reversible docs/internal-code edit that does not change or
depend on a material design assumption. Rerun only when a relevant material gap
is resolved or a trigger above changes current reality; do not run it after every
small edit.

If the Goal, CUJ, acceptance, or relevant domain semantics are unclear, use
`product-goal-framing.md` first.

## Review broadly, work narrowly

Review the concern surface proportionally to Goal consequence and complexity.
For each area, determine whether current evidence makes it resolved, clearly not
applicable, or leaves a material gap. These are ephemeral reasoning findings,
not persisted project states.

### 1. Product / business / domain

- actors, stakeholders, external participants and intended outcomes;
- domain objects, identity, ownership and relationships/cardinality;
- business rules/invariants versus configurable policy; and
- material exceptions and off-nominal cases.

### 2. User / workflow

- primary jobs and representative Critical User Journey;
- discoverability, next-action clarity, context retention and recovery; and
- accessibility or assisted-use needs when relevant.

### 3. Data / state

- source of truth, persistence and state ownership;
- material state transitions and consistency expectations; and
- retention/deletion, migration/upgrade, backup/recovery when applicable.

### 4. Architecture / integration

- component and authority boundaries;
- single authoritative paths versus parallel implementations;
- external/provider integration contracts; and
- coupling, replaceability and material compatibility constraints.

### 5. Security / privacy / consequential effects

- authentication, authorization, secrets and untrusted input;
- privacy/compliance and safety/physical-world obligations when applicable; and
- destructive/external effects, ambiguity, idempotency and retry safety.

### 6. Runtime / operations

- concurrency and resource ownership;
- failure, restart, retry and recovery behavior;
- runtime/configuration identity and observability; and
- material performance/latency/scale and capacity/resource-envelope constraints.

### 7. Delivery / environment

- supported platforms and dependency assumptions;
- install/configuration/update/rollback path; and
- external availability or compatibility constraints that can block use.

### 8. Quality / evidence

- acceptance oracle and representative fixture;
- integration/regression/journey evidence required by the Goal; and
- Owner real-use evidence where subjective experience is the oracle.

### 9. Economy / maintainability

- avoidable abstraction or speculative extensibility;
- duplicate authority or competing implementation;
- cheaper safe path consistent with the Goal; and
- material deferred debt whose risk must survive handoff.

Do not produce paperwork for obviously inapplicable items. Report only gaps or
assumptions material enough to change product behavior, domain semantics,
architecture, authority/source-of-truth, failure safety, acceptance, or a
meaningful cost/risk trade-off.

## Assumption attack

Before concluding the review, ask:

1. What must be true for the proposed design to work?
2. If each important assumption is false, what breaks or becomes unsafe?
3. Imagine the happy path and isolated tests PASS but the product still fails in
   real use. What plausible domain, user, data, provider, runtime, security, or
   operational condition caused that failure?
4. What new evidence or context change would require this decision to be
   revisited?

Use concrete scenarios or small probes when they can cheaply resolve a material
uncertainty. Do not ask the Owner to choose implementation mechanisms or certify
technical facts.

## Result contract

Return one concise result:

- `CONCERN_REVIEW_CLEAR`: no material gap was found that blocks treating the
  proposed design decision as stable under the current Goal and evidence; this
  is not proof of exhaustive completeness; or
- `MATERIAL_GAPS_FOUND`: list only the highest-impact material gaps, normally
  1-7, with the current evidence/assumption, consequence, and the existing
  playbook or targeted specialist analysis needed to resolve each one.

Do not freeze the affected design decision while a `MATERIAL_GAP` remains. Do
not create a new Product Goal merely because the review found a gap; resolve it
within the same Goal unless Owner intent materially changes.