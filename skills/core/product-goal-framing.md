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

The Owner is not expected to supply missing engineering or product-system
expertise. The AI Tech Lead first inspects current reality and performs targeted
research when needed, then resolves low-consequence reversible choices within
established intent and authority. Ordinary targeted research is the default. If
that investigation finds a reusable external specialist Agent Skill materially
preferable to ordinary research, use `external-skill-acquisition.md` before
persistent use; stack or framework detection alone is not sufficient relevance
evidence.

Ask the Owner only for missing product facts, genuinely subjective preference,
material product/business trade-offs, or non-delegable/consequential authority.
When Owner input is genuinely required, construct the smallest useful decision
surface instead of dumping an open technical question on the Owner: proportionally
show concrete options or a recommended default, the observable product consequence
of each material option, and the consequence of deferring when relevant. Do not
freeze a mandatory option count or question count into this method. Translate
technical choices into observable consequences; do not ask the Owner to act as
architect or certify a technical fact.

### Research durability for material knowledge gaps

When targeted research can materially shape a durable product/system direction,
do more than snapshot today's tool landscape. At depth proportional to consequence
and replacement cost:

- establish current reality and the evidence date/context;
- examine credible industry and technology trajectory over the decision-relevant
  horizon rather than assuming today's implementation landscape is stable;
- separate durable capabilities/invariants from volatile models, providers,
  frameworks, APIs or products;
- assess replacement/portability cost and avoid unnecessary lock-in; and
- state concrete evidence/context changes that should trigger reconsideration.

Prefer durable decisions phrased in terms of required capability, property or
invariant, with current technology treated as a replaceable realization unless
that dependency itself is intentionally material. Treat forecasts as uncertain
evidence, not future truth. Do not add trajectory analysis to cheap, local,
reversible questions whose late correction remains bounded.

## Adaptive Intent Boundary and Risk Envelope

Treat Product / Design Framing as an **Intent Boundary**, not a permanent
specification compiler. If the Owner request, current Product Contract and
repository reality already make the material outcome/authority clear and late
correction is cheap, use a pass-through framing and proceed. Spend reasoning
before execution only on uncertainty that could materially change accepted
outcome, authority/external target, persistent-state semantics, or a
hard-to-recover consequence.

For a material Goal, assess a qualitative **Risk Envelope** using only the
dimensions that matter:

- **uncertainty** — how plausible is a materially different interpretation?
- **consequence** — what is the cost if the interpretation/action is wrong?
- **reversibility / recoverability** — how cheaply and reliably can reality be restored?
- **observability** — will failure be detected quickly and causally?
- **blast radius** — how much state, how many users/actors, or which external systems can be affected?

Do not calculate a universal numeric risk score. A credential/security boundary,
destructive persistent-state mutation, materially hard-to-recover external
effect, silent corruption risk or wide blast radius is a pre-execution assurance
trigger even if no prior real failure has occurred.

The boundary is complete when remaining ambiguity cannot materially alter the
accepted outcome, execution authority, external target, persistent-state
semantics or hard-to-recover consequence for the current Goal. It does not imply
complete implementation design.

## Design Compilation when material

The Intent Boundary is not a permanent compiler subsystem, but material Goals
should not force the execution Worker to rediscover accepted product semantics
while coding. When unresolved ambiguity, coupling, state/authority semantics or
cost of rework is material, compile current reality and accepted direction into a
**worker-ready Design Baseline** before execution.

Use `templates/project/DESIGN_BASELINE.md`, a goal-specific OpenSpec/Spec Kit
representation, or an equivalent structured form. The representation is
replaceable; CADS depends on its semantics rather than one tool. One logical
baseline may span several physical files when progressive disclosure helps.

At proportionate depth make explicit only what materially constrains execution:
user-observable outcome/non-goals, material journeys/actions, domain/state
semantics, required behavior/failure recovery, source-of-truth/authority/effect
boundaries, architecture invariants, acceptance/oracles and implementation
ordering where dependency requires it. Do not pre-design classes, functions or
other cheap implementation detail.

Before handoff, attack the baseline for dangling obligations: an unreachable
journey/action, state with unclear persist/reset/re-entry semantics, action with no
result/failure behavior, persistent entity with unclear identity/owner/source of
truth, consequential effect with unclear target/identity, requirement without an
oracle, or accepted output the intended user cannot actually obtain. Apply only
the checks material to the Goal.

If the request is already precise and correction is cheap/local, skip this
artifact entirely. Optimize total time/cost to accepted product, not planning
tokens in isolation.

### Execution substrate requirements

After material design is clear, name only the runtime properties that execution
must actually supply. With no such property, prefer the normal direct coding
harness path. Escalate to a governed substrate only when the Goal requires
isolated mutation, durable recovery, concurrent-writer fencing, durable execution
authority across client/session loss, enforced resource governance, or crash-safe
canonical integration. These are capability requirements, not lifecycle phases
or a mandate for MAR.

`python scripts/ai.py route --require <property>` is an optional read-only helper
that derives `DIRECT`/`GOVERNED` from those explicit properties. It does not infer
risk, grant authority, select a vendor or prove that the chosen substrate satisfies
the requirement. Consequential external effects still use the existing Consequence
boundary regardless of route.

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
   a coupled or high-consequence system should receive deeper design evidence.

## Design sufficiency

Design completeness is not required. Before implementation materially commits
the product/system to a hard-to-reverse direction, identify unresolved decisions
whose plausible alternatives could materially change user-visible behavior,
persistent state/data ownership, authority/external effects, hard-to-reverse
architecture boundaries, or the acceptance oracle.

For each such unresolved decision, choose the cheapest valid treatment:

1. resolve it from current reality and available domain knowledge;
2. reduce uncertainty with a focused probe/prototype when the uncertainty is
   empirical or preference-forming; or
3. deliberately defer it only when reversal is cheap and downstream impact is
   bounded.

Do not delay implementation for unknowns whose late discovery remains cheap and
local. `GOAL_READY` means unresolved load-bearing decisions are resolved,
empirically reduced, or explicitly and cheaply deferred with bounded impact; it
does not mean every design detail is complete.

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
Feature/subsystem PASS does not establish Journey/Product PASS. When intended-user
characteristics, workflow or context materially affect acceptance and the Owner
is not a representative user, require proportionate user/context evidence. Do
not turn that condition into mandatory UX research for personal tools or cases
where the Owner is representative.

### Behavioral / system flow when CUJ is insufficient

Do not create this view universally. Use it when any one observable trigger is
present: the primary flow has no meaningful human actor; two or more actors or
external systems participate; a step is asynchronous, retryable or scheduled;
or an entity has an explicit state lifecycle whose handoffs affect the Goal.

At the depth needed for the Goal, make required/existing behavior clear through
inputs and source of truth, ordered transformations, handoff postconditions,
terminal states, and failure/recovery behavior. Keep the boundaries explicit:
CUJ describes what the user/operator does; Behavioral/System Flow describes what
the system must do; Architecture describes where/how responsibilities are
realized. The behavioral view describes required and existing behavior, not
proposed components. On brownfield work, reconcile it against current source and
runtime reality before it constrains additions.

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
and material accepted decisions. If unresolved load-bearing design decisions
remain, keep only the minimum working set in the existing `TASK.md`, for example:
Question, Why load-bearing, Current working assumption, Cost if wrong, and
Status. These are suggested fields, not a new schema or registry. Remove resolved
items, or promote them to existing Decision Continuity only when rationale must
survive Goal/chat turnover.

Update `ARCHITECTURE.md` only when durable current system truth changes; use
`architecture-description.md` for the bounded profile/fitness reasoning when
material. Durable rationale/direction that must survive Goal/chat turnover
belongs in an accepted Decision Record.

Do not add task IDs, lifecycle stages, schemas, persisted concern status, or a
planning database around this procedure.

## Result contract

Return one concise result:

- `GOAL_READY`: Goal/acceptance and applicable material design drivers are clear
  enough for bounded implementation, with unresolved load-bearing decisions
  resolved, empirically reduced, or explicitly/cheaply deferred with bounded
  downstream impact;
- `MATERIAL_GAPS_FOUND`: list only the highest-impact material gaps/assumptions,
  their consequence, and the targeted evidence or specialist reasoning needed;
  or
- `OWNER_INPUT_REQUIRED`: a material Owner-controlled product fact, trade-off,
  or consequential choice cannot reasonably be recovered or inferred.

A clear framing is not proof that every unknown unknown was found. New evidence
reopens only the affected decision, not a CADS lifecycle.