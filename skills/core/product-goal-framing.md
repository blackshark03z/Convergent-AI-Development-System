# Product / Design Framing

An advisory procedure for turning Owner intent into one bounded Product Goal and
surfacing only the material design drivers that would be expensive or unsafe to
get wrong. It creates no lifecycle phase, review database, architecture
authority, or project state.

Use the canonical development semantics in
`docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`. This playbook combines Goal framing
with proportionate concern coverage; specialist knowledge is pulled on demand
only when a material driver is found.

## When to use

Use when:

- starting a new product or materially new Product Goal;
- Owner requirements or acceptance materially change;
- implementation is about to begin without a clear real-user path;
- a new/changed architecture, domain, source-of-truth, ownership, or authority
  decision is about to become expensive to reverse; or
- new evidence invalidates a material assumption behind an earlier decision.

Do not rerun the full framing after every tiny reversible edit. If project
context is unknown or stale, run `project-cold-start.md` first.

## Knowledge-gap responsibility

The Owner is not expected to supply missing engineering expertise. The AI Tech
Lead investigates material engineering concerns using the Goal, repository,
runtime evidence, supported operating context, and targeted research when
needed. Resolve ordinary engineering choices within established intent and
authority. Ask the Owner only for missing product facts, material trade-offs, or
consequential choices that change Owner-controlled outcomes and cannot
reasonably be recovered or inferred. Translate technical choices into observable
consequences; do not ask the Owner to certify a technical fact.

## Frame the Goal

1. State one bounded Owner outcome in user-observable terms.
2. Define the shortest representative Critical User Journey (CUJ) that proves
   the outcome. For a multi-step user-facing Goal, use the composed journey, not
   merely a feature list.
3. Select one representative real acceptance fixture / golden input when the
   product has meaningful input or state.
4. Define observable acceptance before implementation. Include the useful final
   result, not merely tests, commits, builds, or subsystem success.
5. State non-goals and constraints that prevent adjacent work from silently
   becoming part of the Goal.
6. Identify only the source/runtime/config/data/external-effect authority
   boundaries material to this Goal.
7. Apply the Decision Continuity materiality test to accepted direction that
   must survive chat/agent turnover.
8. Choose rigor proportional to consequence, irreversibility, complexity and
   cost of being wrong. A small local tool should collapse to very little ceremony;
   a coupled or high-consequence system should receive deeper design
   evidence.

## Material design drivers

Ask one question first:

> What assumption or concern, if wrong, could materially change product
> behavior, acceptance, architecture, authority/source-of-truth, failure safety,
> or a meaningful cost/risk trade-off?

Use the following lenses only as a compact reference surface. Do not produce
paperwork for obviously inapplicable items.

When a material concern can shape durable system structure, identify the small
set of architecture drivers (quality attributes/constraints) that actually drive
the choice. Route to `architecture-description.md` only when system boundary,
building blocks, technology/framework, runtime/data/state/deployment/trust
boundaries or architecture fitness need durable description/evaluation.

### Product / domain / state

When applicable, establish the actors/external systems, domain objects and
identities, relationships/cardinality, ownership, business rules/invariants
versus configurable policy, and material exceptions.

For repeatable, persistent, asynchronous, or historical workflows, also resolve
only the state-lifecycle facts that constrain design: state scope, owning entity,
lifetime, mutable versus frozen data, snapshot point, terminal behavior, what
persists versus resets, how the next cycle re-enters, and how stale state from a
completed cycle is prevented from becoming active context. Domain semantics
constrain architecture; they do not prescribe schemas, classes, services, BPMN,
or deployment topology.

### User / journey

Check the primary job/CUJ, discoverability and next-action clarity, context
retention, failure/recovery, and accessibility/assisted-use needs when material.
Feature/subsystem PASS does not establish Journey/Product PASS.

### Architecture / structure

When architecture is material, check system boundary, major building-block
ownership, critical runtime flows, deployment/runtime topology and the few
quality attributes/constraints that drive the design. Treat frontend/backend,
framework, database, provider or service choices as architecturally significant
only when they materially affect boundaries, quality, interfaces, deployment or
maintainability. Use scenario/evidence reasoning rather than a mandatory diagram
or architecture framework.

### Data / authority

Check identity, source of truth, persistence/state ownership, consistency, and
retention/deletion, migration/upgrade, backup/recovery only when they could
materially change the design or consequence.

### External / security / safety

Check authentication/authorization, secrets/untrusted input, privacy/compliance
or physical-world safety when applicable. For consequential external effects,
make ambiguity, effect identity, idempotency, retry safety and authorization
explicit rather than assuming a successful call or retry is harmless.

### Runtime / operations

Check concurrency and resource ownership, fencing/authority when concurrent or
replaceable actors can mutate shared state, failure/restart/recovery behavior,
runtime/config identity and observability, and material performance/latency/
scale/resource-envelope constraints.

### Quality / economy

Check acceptance oracle and representative fixture, integration/regression/
journey evidence, Owner real-use when subjective experience is the oracle,
duplicate authoritative paths, speculative abstraction, deferred material debt,
and whether a cheaper safe path satisfies the Goal.

## Assumption attack

Before treating a material design decision as stable, ask:

1. What must be true for this design to work?
2. If an important assumption is false, what breaks or becomes unsafe?
3. Imagine happy-path and isolated tests PASS but the product still fails in
   real use. What plausible condition caused the failure?
4. What new evidence or context change would require this decision to be
   revisited?

Use concrete scenarios or small probes when they cheaply resolve a material
uncertainty. Scan broadly enough to find material drivers; work narrowly on only
those that matter.

## Acceptance rules

Acceptance must be independently observable and must not be weakened post hoc
merely to make an implementation pass. Tests are verification evidence, not the
acceptance oracle unless the Goal itself is explicitly test-only.

For user-facing work, the CUJ should express what the intended user actually
does from entry to useful result. Hidden, unreachable, or technically present
capability does not satisfy user-visible acceptance. For multi-step Goals,
isolated feature/subsystem PASS results do not compose into Journey PASS.

Do not invent detailed architecture before current source has been inspected.
The Goal and material design drivers constrain implementation; they do not
justify speculative subsystems.

## Context update

When authorized, keep only the minimum current Goal context in `TASK.md`: Goal,
CUJ, acceptance, representative fixture when applicable, non-goals, constraints,
and material accepted decisions. Update `ARCHITECTURE.md` only when durable
current system truth changes; use `architecture-description.md` for the bounded
profile/fitness reasoning when material. Durable rationale/direction that must
survive Goal/chat turnover belongs in an accepted Decision Record.

Do not add task IDs, lifecycle stages, schemas, persisted concern status, or a
planning database around this procedure.

## Result contract

Return one concise result:

- `GOAL_READY`: Goal/acceptance and applicable material design drivers are clear
  enough for bounded implementation or for the affected design decision to be
  treated as stable under current evidence;
- `MATERIAL_GAPS_FOUND`: list only the highest-impact material gaps/assumptions,
  their consequence, and the targeted evidence or specialist reasoning needed;
  or
- `OWNER_INPUT_REQUIRED`: a material Owner-controlled product fact, trade-off,
  or consequential choice cannot reasonably be recovered or inferred.

A clear framing is not proof that every unknown unknown was found. New evidence
reopens only the affected decision, not a CADS lifecycle.