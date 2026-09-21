# System Purpose & Scope

<!-- What durable problem does this system solve, for whom, and what is inside/outside the system boundary? -->

# Stakeholders / Architecture Concerns

<!-- Populate only material concerns that shape architecture. Do not create a stakeholder matrix for trivial projects. -->

# Architecture Drivers

<!-- The small set of quality attributes, constraints, scale/security/operability/cost needs or other forces that materially shape the design. Prefer observable scenarios/targets when useful. -->

# Solution Strategy / Technology Stack

<!-- Record architecturally significant choices only. For each material role (for example frontend, backend/API, worker, data store, runtime/provider), state the actual choice, why it fits current drivers, and when it should be revisited. CADS does not prescribe one universal stack. -->

# System Context

<!-- Important users, external systems/providers and system boundary. A diagram is optional; text is sufficient when clearer. -->

# Components / Building Blocks / Ownership

<!-- Major components/modules/services and their responsibilities/ownership boundaries. Use the smallest decomposition needed to understand the current system. -->

# Data / Control Flow

<!-- Critical end-to-end interactions, asynchronous flows, startup/recovery paths or failure scenarios that a contributor must understand. Include data/control movement only when it matters. -->

# Authority / State Boundaries

<!-- Sources of truth, state ownership/lifetime, mutable vs frozen/snapshotted data, persistence/reset behavior, configuration/runtime identity and mutation authority when relevant. -->

# Deployment / Runtime Topology

<!-- Processes, machines/containers/cloud services, queues/workers, storage and runtime relationships only when they materially affect development/operations. When Product Acceptance depends on an observed product surface, record only the provenance mechanisms needed to reconstruct which candidate materially serves that surface (for example entrypoint/route, artifact or client assets, config/data authority, activation/reload if applicable, request-reachable replicas/versions, stale process/cache handling). These are examples, not a required deployment schema or lifecycle. -->

# External Boundaries / Trust Boundaries

<!-- Providers, APIs, authentication/authorization, secrets/untrusted input, consequential effects and other trust boundaries when relevant. -->

# Stable Invariants / Architecture Invariants

<!-- Properties that changes must preserve. Prefer statements that can be checked or tied to scenarios/evidence. When state ownership/source-of-truth, dependency direction, persistent schema, external-effect semantics or concurrency/fencing changes materially, identify the affected system-fitness invariant and the smallest integration evidence that protects it. -->

# Important Tradeoffs / Decisions

<!-- Current material choices and trade-offs. Link accepted Decision Records for durable rationale instead of duplicating history here. -->

# Known Risks / Technical Debt / Revisit Triggers

<!-- Material architecture risks/debt and concrete evidence/conditions that should reopen a decision. -->

# Deprecated / Legacy Notes

<!-- Legacy behavior that could otherwise be mistaken for current design. -->

Populate only sections that help reconstruct the current architecture. Choose views from current concerns; no diagram notation or complete view set is mandatory. Describe actual current Git/runtime reality rather than aspirational design. Keep transient task progress in `TASK.md`.
