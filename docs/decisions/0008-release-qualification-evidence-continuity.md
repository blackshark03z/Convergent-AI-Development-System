# DR-0008: Separate release qualification from product acceptance and activation

Status: Accepted
Date: 2026-09-13
Scope: Acceptance / Release Evidence

## Context

Story Audio exposed a release-boundary failure class after product behavior had been accepted: clean CI revealed hidden system/environment assumptions and the release branch continued changing while older acceptance evidence remained associated with earlier candidate reality. CADS already had Execution Reproducibility, candidate-bound Product Acceptance, Systematic Debugging and Acceptance Surface Provenance, but no explicit composition method for deciding when a later exact release subject is qualified or when earlier acceptance evidence may safely support it.

Independent review concluded that the foundational semantics are already correct and the operational gap is narrow. Product Acceptance currently risked semantic overlap by including `release-ready` among its claims even though product outcome, release qualification and runtime activation answer different questions.

## Decision

Keep the Five Controls and frozen Standard unchanged. Add one conditional Release Qualification method for Goals with a material release boundary.

Treat these as distinct evidence-backed claims, not lifecycle states:

- Product Acceptance proves the identified candidate satisfies the predefined Goal/CUJ/product outcome.
- Release Qualification proves an identified source/artifact plus material release conditions is reproducibly releasable with matching verification evidence.
- Runtime Activation/Acceptance Surface Provenance proves an observed serving surface corresponds to the intended qualified release reality.

Adopt criterion-scoped evidence continuity:

> Evidence established for candidate A may support candidate B only where the identified A-to-B delta is shown not to materially affect the claimed behavior, relevant inputs/state/data, the oracle, or dependent surface provenance. Unknown or unresolved impact leaves the affected criterion `UNVERIFIED` until matching evidence is re-established.

Do not infer neutrality from file/category labels. Do not require full re-UAT merely because a SHA changes. Do not transfer old-HEAD/full-suite evidence to a later candidate without preservation/equivalence evidence.

Release qualification composes existing Goal Execution proportional regression/stop-loss, Systematic Debugging root-cause localization, Product Acceptance oracle integrity and Acceptance Surface Provenance. It does not redefine them.

## Consequences

- A product may legitimately be `PRODUCT_ACCEPTED` while release qualification is blocked by environment/build/install/runtime assumptions.
- Exploratory Owner review remains possible before release qualification; release-bound readiness gets stronger evidence only when a material release boundary exists.
- Qualification uses cheapest discriminating evidence first and broader confirmation when justified, not a universal fixed pipeline.
- Repeated CI failures that converge on a shared environment/harness/provider boundary return to existing root-cause debugging rather than creating a retry counter or patching every leaf independently.
- Where artifacts exist, reusing the already-qualified identified artifact is preferred; rebuilds/materially different outputs require matching qualification evidence or equivalence.
- CADS gains no release database, RC phase machine, CI engine, deployment manager, promotion service or new runtime authority.

## Revisit

Revisit if representative projects show the conditional method adds ceremony without reducing stale-evidence/false-release failures, or if a second systemic failure demonstrates that the frozen Standard itself lacks a universal invariant that cannot be expressed through existing evidence semantics.
