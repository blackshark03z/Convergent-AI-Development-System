# Design Baseline

<!-- Optional. Use only when the Intent Boundary does not collapse to pass-through.
This is one worker-ready representation of accepted design truth, not a mandatory
phase artifact. OpenSpec/Spec Kit/structured equivalents are valid substitutes. -->

# Baseline Identity

<!-- Identify the Goal/design revision or digest that execution and acceptance use. -->

# Product Outcome / Non-goals

<!-- What must the user/operator be able to accomplish? What is explicitly outside this Goal? -->

# Material Journeys / Actions

<!-- Only material end-to-end paths. For each relevant state, make the visible next
action and resulting state/outcome clear enough that execution cannot invent product semantics. -->

# Domain / State Semantics

<!-- Identities, ownership, mutable vs historical/frozen state, persist/reset/re-entry
rules and stale-state isolation when applicable. -->

# Required System Behavior

<!-- Ordered behavior, handoffs, postconditions and material failure/recovery semantics
when the CUJ alone is insufficient. -->

# Data / Authority / Effect Boundaries

<!-- Sources of truth, mutation authority, external targets/effect identity and trust
boundaries that constrain this Goal. -->

# Architecture Constraints

<!-- Only load-bearing existing/new boundaries and invariants. Do not prescribe classes,
functions or file layout unless that detail is itself a material constraint. -->

# Acceptance / Oracle Map

<!-- Map each material obligation to an observable oracle/evidence surface. Independent
Product Acceptance still decides completion. -->

# Execution Slices

<!-- Optional. Small coherent slices, ordered only where dependencies require it. Deep
design does not imply giant-bang implementation. -->

# Assumptions / Experiments / Revisit Triggers

<!-- State uncertainty honestly. Use a probe/experiment for empirical unknowns rather than
pretending the baseline is certain. -->

# Design Gap Rule

Implementation details are Worker-owned. If source reality contradicts this baseline
or a missing decision could materially change product behavior, state/data/authority,
architecture or acceptance, return a concrete `DESIGN_GAP` for only the affected
slice. Do not silently invent material product semantics and do not reopen unrelated
accepted design.
