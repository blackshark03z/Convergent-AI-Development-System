# DR-0011: Adopt adaptive control boundaries for progressive AI delivery

Status: Accepted
Date: 2026-09-21
Scope: Intent / Risk / Acceptance / Integration

## Context

Real project evidence and independent review exposed a gap between two desirable
properties: very fast AI implementation and durable product convergence. A
convergence-only interpretation can react too late when a fast Worker implements
an ambiguous product intent incorrectly. Conversely, front-loading a complete
design or assurance process slows cheap, reversible work and competes with
improving model capability.

Existing CADS already requires bounded Goal/CUJ/acceptance, verification
independence, consequence-proportional rigor, architecture fitness when material,
trusted evidence, and one canonical integration authority. This decision
clarifies how those existing semantics compose for progressive delivery; it does
not amend the frozen Convergent AI Development Standard or add a lifecycle
engine.

## Decision

Adopt five adaptive control boundaries:

1. **Intent Boundary** — before material execution, unresolved uncertainty that
   can materially change accepted outcome, authority, external target,
   persistent-state semantics, or a hard-to-recover consequence must be reduced,
   resolved, or explicitly bounded. If the request is already clear and cheap to
   reverse, this boundary collapses to near-zero ceremony.
2. **Risk Envelope** — scale assurance using the material dimensions of
   uncertainty, consequence, reversibility/recoverability, observability and
   blast radius. Do not turn these dimensions into a universal numeric score.
   Credential/security boundaries, destructive persistent-state mutation,
   materially hard-to-recover external effects, silent corruption and wide
   blast radius are pre-execution triggers rather than "fail once, then harden"
   candidates.
3. **Execution Authority** — Workers receive maximum implementation freedom
   inside explicit mutation/effect authority and existing project invariants.
   CADS constrains outcomes and consequences, not the Worker thought process,
   model family, planner, framework, subagent topology or coding method.
4. **Versioned Acceptance** — the acceptance/oracle used for a completion claim
   must be identifiable with the candidate it evaluates. Identification may be
   a Git-bound Goal/TASK revision, content digest, decision record or equivalent;
   no universal numeric oracle registry is required. A Worker may propose an
   oracle change but may not silently weaken/redefine the oracle and use the
   replacement to approve the same implementation.
5. **Canonical Promotion** — parallel experimentation is allowed, but one
   authority advances canonical product truth. Before promotion, evidence must
   correspond to the candidate actually being promoted and include the affected
   product oracle plus applicable system-fitness invariants.

## System-fitness trigger

Local CUJ success does not imply global system health. Run proportionate
system-fitness reasoning/checks when a change materially alters or introduces:

- state ownership or a source of truth;
- dependency direction or a durable architecture boundary;
- persistent schema/state evolution;
- external-effect identity, uniqueness, retry/idempotency or target semantics;
- concurrency/fencing semantics; or
- another cross-cutting invariant whose local success could hide a system-level
  failure.

Prefer executable architecture/contract checks once a stable invariant can be
expressed mechanically. Do not require a full architecture review for every
small change.

## Accepted outcome versus continuity commitment

Acceptance for present use does not automatically freeze every observable detail
of the first usable implementation as a permanent compatibility contract.
Preserve only material accepted behavior explicitly required by the active or
durable Product Contract. The canonical requirement is one identifiable product
lineage, not permanent loyalty to the first implementation architecture.

A targeted rewrite/replacement is valid when accepted behavior is preserved or
explicitly superseded, material state has a deliberate transition when needed,
the replacement is accepted against the current oracle/system invariants, it is
promoted canonically, and the obsolete competing path is retired.

## Deferred assurance

Cheap-to-correct guarantees may be deliberately deferred when current risk is
bounded. Record a deferred guarantee only when it is material enough to retain,
and prefer a concrete trigger that makes the guarantee required, for example
render duration, provider cost, failure frequency, user count or state value.
This is a lightweight memory aid, not a mandatory backlog, phase, database or
global CADS registry.

Catastrophic or materially hard-to-recover risk classes are not eligible for
"observe the first failure" deferral merely because recovery work has not yet
been justified by production evidence.

## Consequences

- Product / Design Framing becomes an adaptive Intent Boundary plus Risk Envelope,
  not a permanent "Intent Compiler" subsystem.
- Tiny reversible tools can pass through CADS with almost no ceremony.
- Product Acceptance binds claims to an identifiable oracle/candidate and checks
  only affected system-fitness invariants.
- "Usable" is scope-bound acceptance, not a promise that every current behavior
  is permanent or that all assurance dimensions are mature.
- Parallel execution can scale while canonical promotion remains a serialization
  point for product truth.
- Model/harness specialization remains operational and replaceable; no named
  model role becomes CADS architecture.
- Recovery remains evidence-driven for bounded recoverable failures, while
  catastrophic/hard-to-recover classes receive anticipatory protection.
- Existing Five Controls remain the mental model. No sixth control, task runtime,
  workflow state machine, mandatory reviewer topology or universal release
  schema is introduced.

## Explicitly rejected

Do not adopt as CADS invariants:

- first usable implementation must remain the permanent architecture;
- every accepted-for-use behavior becomes a permanent compatibility contract;
- real failure must happen before protection is justified;
- one branch strategy, model topology or reviewer count for all projects;
- a universal numeric risk score;
- stable-before-first-use; or
- enterprise-grade assurance by default.

## Revisit

Revisit this decision only when representative project evidence shows one of the
following:

- the Intent/Risk boundary repeatedly costs more than the rework it prevents;
- scope-bound acceptance repeatedly produces material architecture decay despite
  the system-fitness trigger;
- canonical promotion becomes a throughput bottleneck whose guarantee can be
  replaced by a cheaper equally trustworthy mechanism;
- a stronger execution environment makes one of these mechanisms redundant; or
- a serious/repeated failure class is not expressible through the existing Five
  Controls plus these adaptive boundaries.

Any replacement should preserve the durable semantics while allowing obsolete
scaffolding to disappear.
