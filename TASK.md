# Goal

Add a thin, conditional Release Qualification method that prevents Product Acceptance evidence from silently drifting onto a later release candidate, while preserving existing Execution Reproducibility, Product Acceptance, Systematic Debugging and Acceptance Surface Provenance semantics. Distinguish product acceptance, release qualification and runtime activation as evidence-backed claims without creating a release lifecycle or state machine.

# Critical User Journey

AI Tech Lead reaches a release-bound product candidate -> Product Acceptance evidence is bound to identified candidate A -> release stabilization changes produce candidate B -> the A->B delta is inspected criterion-by-criterion -> acceptance evidence is carried forward only where claimed behavior, relevant inputs/state/data, oracle and surface provenance are shown preserved -> affected/unknown criteria are re-established -> the exact qualification subject (source/artifact/config/toolchain/environment) receives proportionate release verification -> `RELEASE_QUALIFIED` is claimed only for that identified subject -> existing Acceptance Surface Provenance verifies any later active runtime against the qualified release reality.

# Acceptance

- Add one conditional `skills/core/release-qualification.md` composition method for Goals with a material release boundary; it must not create a sixth control, release lifecycle, CI engine, deployment manager or persisted release state.
- Product Acceptance, Release Qualification and Runtime Activation are distinct evidence-backed claims; none implies the next.
- Clarify `skills/core/product-acceptance.md` so `PRODUCT_ACCEPTED` proves product outcome, not release qualification, when a material release boundary exists.
- Evidence established for candidate A may support candidate B only criterion-by-criterion when the identified delta is shown not to materially affect the claimed behavior, relevant inputs/state/data, acceptance oracle, or surface provenance. Unknown impact is not preservation.
- Post-acceptance changes are evaluated by material effect, not by file/category labels such as CI/test/config. Oracle-changing deltas cannot self-prove preserved acceptance.
- Release Qualification identifies the exact subject being qualified: source/artifact plus material configuration, dependencies/toolchain and supported release environment as applicable.
- Prefer cheapest discriminating release evidence first and broader/expensive confirmation at meaningful convergence points; do not mandate one universal test sequence.
- When qualification failures converge on a shared environment/harness/provider boundary or leaf patches stop producing measurable progress, route to existing Systematic Debugging/Goal Execution stop-loss semantics rather than patching tests independently.
- Prefer releasing the already-qualified identified artifact where the product has artifacts. A rebuild or materially different output is a delta and requires matching qualification evidence/equivalence; literal single-binary identity is not universal.
- Add focused eval/test coverage for evidence drift, behavior-neutral and behavior-impacting post-acceptance deltas, oracle changes, undeclared environment dependencies, old-HEAD verification and qualification/activation mismatch.
- Keep the frozen Standard unchanged; preserve `Reality -> Intent / Design -> Change -> Acceptance -> Consequence`.
- Keep full CADS regression passing without weakening existing tests.

# Acceptance Fixture / Evidence Basis

1. Owner accepts candidate A; candidate B changes only demonstrably non-material CI mechanics and leaves behavior/oracle/provenance intact: matching evidence may be carried criterion-by-criterion without ceremonial full re-UAT.
2. Candidate B changes backend semantics affecting an accepted journey: affected criteria become `UNVERIFIED` until matching acceptance evidence is re-established.
3. Candidate B changes a test/oracle to make CI pass: the changed test cannot self-prove preserved acceptance.
4. A clean supported runner exposes undeclared `ffmpeg`, browser, provider isolation, filesystem/path or configuration assumptions: Product Acceptance may remain valid while Release Qualification is blocked.
5. Multiple qualification failures point to one environment/harness boundary: stop leaf patching and debug the shared boundary using existing Systematic Debugging semantics.
6. A broad regression PASS belongs to old HEAD A while current candidate is B: it cannot qualify B without demonstrated equivalence or matching evidence.
7. Qualified source produces artifact X; deployment rebuild produces materially different artifact Y: X's qualification does not automatically qualify Y.
8. Exploratory Owner/UI review may happen before release qualification; only release-bound readiness claims require qualification when a material release boundary exists.

# Non-goals

No sixth CADS control, `DEV -> UAT -> RC -> QUALIFIED -> PROMOTED -> ACTIVE` state machine, release database/registry, CI orchestration engine, deployment/release service, process manager, hard-coded commit/file/line thresholds, hard-coded retry counts, mandatory clean-room CI for tiny tools, mandatory Owner re-UAT after every SHA change, mandatory container/cloud release, universal immutable-binary requirement, or Standard amendment.

# Constraints

Preserve DR-0003 anti-accretion, DR-0004 trusted-evidence boundaries, DR-0006 acceptance-surface provenance, oracle integrity, Execution Reproducibility and the frozen Standard. Compose existing Product Acceptance, Goal Execution and Systematic Debugging rather than duplicating their mechanics. Release qualification is conditional on a material release boundary and remains native to project Git/CI/build/deployment tooling.

# Material Decisions

- Accept the independent-review verdict `ACCEPT_WITH_CHANGES`: the real gap is release-evidence continuity at an operational boundary, not missing foundational evidence semantics.
- Keep Product Acceptance, Release Qualification and Runtime Activation as distinct evidence claims, never persisted process states.
- Adopt criterion-scoped carry-forward: evidence from A supports B only where the A->B delta is proven acceptance-preserving for the relevant claim/oracle/provenance; unresolved impact fails closed.
- Use effect-based delta reasoning rather than trusting filenames such as `ci`, `test`, `config` or `packaging` as neutral.
- Make preflight proportional and release-bound; exploratory product review remains allowed earlier.
- Prefer qualified artifact reuse where applicable, while expressing the invariant as traceable qualified identity/equivalence rather than literal hash equality.

# Progress / Discoveries / Next

- Story Audio PR #8 exposed a real sequence where accepted product behavior became separated from later branch HEAD while release-environment assumptions were discovered through repeated CI runs.
- Independent reviewer verdict: `ACCEPT_WITH_CHANGES`.
- Implemented one thin conditional Release Qualification composition method, clarified Product Acceptance vs release readiness, added DR-0008 and AE-021, and kept the frozen Standard unchanged.
- Evidence continuity is criterion-scoped: SHA change alone does not force full re-UAT, while unresolved material impact on behavior/oracle/provenance fails closed as `UNVERIFIED`.
- Focused release/autonomy/portability/cold-start regression: 39/39 PASS; `git diff --check` PASS; frozen Standard diff empty.
- Full CADS regression: 110/110 PASS with `SIMPLIFIED_ACTIVE_SUITE=PASS`.

Next: review the final bounded diff for anti-accretion, commit/push only the intended release-qualification paths, then use Story Audio as the first production case to evaluate whether the method reduces release evidence drift and CI whack-a-mole.
