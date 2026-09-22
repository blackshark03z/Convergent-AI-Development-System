# DR-0012: Compile material design before execution using a replaceable spec substrate

Status: Accepted
Date: 2026-09-22
Scope: Intent / Design / Execution / Acceptance

## Context

CADS intentionally does not own a development lifecycle. DR-0011 established an
adaptive Intent Boundary: clear reversible work should pass through with almost no
ceremony, while material uncertainty must be reduced before expensive execution.

Representative project evidence exposed a different bottleneck. A Worker given a
broad Goal plus repository reality can spend substantial cognition rediscovering
product semantics while coding. That increases rework and allows locally correct
features to miss composed user actions, state transitions or configuration
semantics. Loading more CADS prose into the Worker is not a scalable remedy.

A direct ChatCode pilot on Story Auto removed MAR/runtime lifecycle noise and
compared a Raw arm with a goal-specific spec-driven arm. The Raw candidate required
repair and still missed hidden product obligations after focused tests passed. The
spec-driven candidate passed the same focused checks and hidden product obligations
without a repair round. This is directional evidence only: the spec arm ran later
in the same model context and therefore was not statistically independent. It is
sufficient to justify the mechanism for further use, not to freeze one tool or
claim a universal performance factor.

The same pilot also exposed an invalid earlier comparison: merely installing an
OpenSpec skeleton/configuration is not Spec-Driven Development. A treatment counts
only when the current Goal has an accepted, goal-specific design/spec baseline.

## Decision

For a Goal whose Intent Boundary does not collapse to pass-through, use
**Design Compilation** inside the existing Intent / Design control:

Owner intent + current reality + targeted research
-> accepted worker-ready Design Baseline
-> bounded execution package
-> Worker implementation
-> independent Product Acceptance.

Design Compilation is a mechanism, not a sixth CADS control, phase engine, task
state machine or mandatory document ceremony.

### Worker-ready Design Baseline

A material Design Baseline makes the decisions that materially constrain product
semantics explicit enough that execution no longer has to rediscover them while
coding. At proportionate depth it may cover:

- desired user-observable outcome and non-goals;
- complete material journeys, actions and reachable next steps;
- domain identity, ownership and state lifetime/reset/re-entry semantics;
- required system behavior and material failure/recovery behavior;
- source-of-truth, authority, external-effect and architecture boundaries;
- acceptance/oracle obligations; and
- a small ordered implementation decomposition when execution ordering matters.

The baseline describes **what must be true and which boundaries must hold**. It
does not freeze classes, functions, file layout or other implementation detail
that the Worker can choose safely from current code reality.

One logical baseline may be represented physically as one small Markdown file,
an OpenSpec change, Spec Kit artifacts, a structured graph or another equivalent
form. The representation is replaceable. CADS Core depends on the semantics, not
on OpenSpec, Spec Kit, Markdown, a named vendor or a named model.

### Proportionality

Do not create a Design Baseline when the request is already precise, correction is
cheap and local, and material product/state/authority ambiguity is absent. A tiny
reversible edit may go directly from Goal to implementation.

As ambiguity, coupling, consequence or cost of rework increases, spend more
reasoning before execution. Optimize total time/cost to accepted product rather
than minimizing planning tokens in isolation.

### Design completeness attack

Before handing a material baseline to execution, attack only the obligations that
can create expensive rework:

- each material Goal has a reachable journey or observable system outcome;
- each material journey step has required behavior and a clear next action;
- material states have entry/exit/reset/persist semantics;
- each consequential action has result/failure/recovery semantics;
- persistent entities have identity, owner and source of truth;
- external effects have target/identity/idempotency semantics where relevant;
- material requirements map to an acceptance oracle; and
- accepted output is actually obtainable by the intended user/operator.

Do not expand this into a universal checklist for trivial work.

### Execution contract

The Worker should receive the smallest execution input that preserves the accepted
design: active Goal, relevant baseline obligations, acceptance/oracle, mutation/
effect authority, current repository reality and necessary implementation
dependencies. Do not require every Worker to reconstruct the whole CADS corpus.

Implementation-detail uncertainty remains the Worker's responsibility. A
contradiction or missing material product/design decision is a **DESIGN_GAP**:
pause only the affected implementation slice, return the concrete unresolved
decision to Design Authority, amend/supersede the affected baseline, then resume.
Do not silently invent material product semantics and do not route ordinary code
choices back to the Owner.

### Execution substrate boundary

CADS does not mandate MAR, ChatCode, one agent runtime or one orchestration model.
Use the simplest execution substrate that preserves the required authority,
isolation, evidence and consequence guarantees.

A durable runtime such as MAR is justified when the task needs properties such as
isolated mutation, crash/retry recovery, concurrency/fencing, durable authority,
resource governance or crash-safe canonical integration. Those runtime lifecycle
states belong to the execution substrate, not to CADS product/design semantics.

Direct repository execution is valid for bounded local work when its authority and
evidence are sufficient. Product architecture experiments should not use a more
complex execution substrate when that substrate would confound the property being
measured.

## Consequences

- CADS development optimizes for **front-loaded intelligence, streamlined
  execution** on material Goals.
- Design Authority is a capability role, not a permanent model/vendor assignment.
  One sufficiently capable model may perform design and execution.
- Workers are expected to reason deeply about implementation, but not repeatedly
  reconstruct already accepted product semantics.
- Goal-specific specs become first-class execution inputs when useful, while the
  spec framework remains replaceable.
- Hidden/independent product acceptance remains necessary because a detailed design
  can still be wrong and focused implementation tests can still miss product
  composition.
- Existing Five Controls and DR-0011 remain authoritative; no lifecycle is added.

## Explicitly rejected

Do not make any of the following CADS Core requirements:

- a Design Baseline for every trivial edit;
- OpenSpec, Spec Kit or Markdown as the permanent canonical representation;
- a fixed strong-model/cheap-model vendor mapping;
- detailed class/function implementation plans before coding;
- a giant-bang implementation merely because design was done deeply;
- MAR or another durable runtime for every development task;
- loading the entire CADS documentation corpus into every execution Worker; or
- weakening independent acceptance because a strong Design Authority produced the
  baseline.

## Revisit

Revisit this mechanism when representative evidence shows that:

- Design Compilation costs more than the rework/product defects it prevents for
  the class of Goals where it is applied;
- execution Workers repeatedly require material redesign despite accepted
  baselines;
- a stronger model makes the compiled baseline redundant while preserving the
  same product/authority/acceptance guarantees;
- a structured representation materially outperforms current text/spec substrates;
  or
- independent acceptance exposes a systematic failure class that the current
  baseline semantics cannot express.
