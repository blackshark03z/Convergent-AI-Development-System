# Architecture Description

A conditional CADS method for making durable project architecture legible and testing material architecture choices against the concerns that caused them. It creates no lifecycle phase, design authority, approval gate, architecture database, mandatory diagram set or runtime state.

Use the canonical development semantics in `docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`, Product / Design Framing for Goal and concern discovery, and Decision Continuity for accepted rationale that must survive turnover.

## When to use

Use when one or more of these are material:

- a new project needs its durable system shape established;
- frontend/backend/service/data-store/runtime/deployment boundaries are introduced or materially changed;
- an architecturally significant framework/provider/technology choice is being made or replaced;
- state/source-of-truth/ownership/runtime topology/trust boundaries change;
- a fresh contributor cannot reconstruct the system shape and critical runtime behavior from current repository truth; or
- new evidence invalidates an assumption behind a material architecture decision.

Do not invoke this for tiny reversible implementation choices that do not change durable architecture.

## Source-of-truth discipline

Inspect current Git/source, runtime/configuration evidence, tests, active Decision Records and the current Goal before describing architecture. `ARCHITECTURE.md` is durable current architecture context, not implementation authority and not an aspirational roadmap. When docs conflict with identified Git/runtime reality, fix the description or affected implementation rather than treating prose as stronger evidence.

## Build the lean description

### 1. Establish purpose, boundary and material concerns

State the durable system purpose/scope and only the stakeholders/concerns that can change architecture. Avoid organization charts and exhaustive stakeholder paperwork for small tools.

### 2. Identify architecture drivers

Extract the small set of forces that materially shape design: product constraints and the most important quality attributes such as reliability, usability, recoverability, security, performance, maintainability, interoperability, operability, scale or cost. Do not copy a full quality checklist.

When useful, express a driver as an observable scenario:

`stimulus/context -> expected system response -> useful measure/evidence`.

### 3. Record solution strategy and significant technology choices

Choose the smallest architecture that satisfies current drivers and constraints. CADS does not prescribe React, Next.js, FastAPI, Go, PostgreSQL, microservices, containers or any other universal stack.

For each architecturally significant technology/framework role, record:

- role/problem it solves;
- actual chosen technology/framework/provider;
- why it fits current drivers/constraints;
- important trade-off;
- evidence or condition that should trigger reconsideration.

Escalate to the Owner only when the choice changes an Owner-controlled product outcome, material business trade-off or consequential authority boundary.

### 4. Select only views that answer current concerns

Use prose, tables or diagrams as convenient. Typical concern-driven views are:

- **System context** — users/external systems and boundary;
- **Building blocks / ownership** — frontend, backend/API, workers, stores, modules/services and responsibilities when those concepts exist;
- **Runtime** — critical request/job/event/recovery flows;
- **Data / state / authority** — source of truth, ownership, lifetime, snapshots, reset/persist and mutation authority;
- **Deployment / topology** — processes/hosts/cloud/queues/storage relationships;
- **Trust / external boundaries** — auth, secrets, untrusted input, providers and consequential effects.

No complete set is mandatory. If a view answers no material concern, omit it.

When Product Acceptance depends on an observed product surface and provenance
would otherwise be hard to reconstruct, record only the mechanisms material to
that proof: for example the relevant entrypoint/route, artifact or client-asset
provenance, configuration/data authority, activation/reload mechanism when one
actually exists, request-reachable replica/version behavior, and stale
process/cache replacement. These are examples, not a mandatory deployment
schema. The purpose is to make acceptance-surface provenance reconstructable,
not to create an activation phase or process manager.

### 5. State stable invariants and decision continuity

Record the architecture properties future changes must preserve. Put accepted rationale/direction that could materially change a later session's approach into `docs/decisions/`; keep `ARCHITECTURE.md` focused on current durable truth.

### 6. Run a lightweight architecture fitness check

For each material driver, ask:

`driver -> architecture decision -> expected property/scenario -> evidence/risk/trade-off`.

Attack important assumptions with plausible failure scenarios. Include runtime/recovery/state-transition scenarios when static structure can pass while the real product journey fails. Use targeted prototypes/tests/runtime observations when they cheaply resolve uncertainty.

This is not a mandatory ATAM workshop or review board. Depth scales with consequence, irreversibility, complexity and oracle weakness.

## Update rules

Update `ARCHITECTURE.md` when durable current system truth changes. Do not record transient task progress, session history, implementation todo lists or speculative future topology. Supersede durable rationale through Decision Records rather than silently rewriting history.

## Result contract

Return one concise result:

- `ARCHITECTURE_READY`: current architecture, material drivers/boundaries and relevant fitness evidence are clear enough for the Goal;
- `MATERIAL_ARCHITECTURE_GAPS`: list only material gaps/assumptions, consequence and targeted evidence needed; or
- `OWNER_INPUT_REQUIRED`: an Owner-controlled product/business/consequential choice blocks a material architecture decision.

A result is advisory engineering reasoning, not persisted process state or permission authority.
