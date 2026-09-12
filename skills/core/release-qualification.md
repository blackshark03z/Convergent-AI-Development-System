# Release Qualification

A conditional CADS composition method for proving that an identified release subject is reproducibly releasable in its supported context without conflating that claim with Product Acceptance or Runtime Activation. It creates no release lifecycle, phase state, CI engine, deployment authority, registry or second runtime.

Use the canonical development semantics in `docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`. Reuse `product-acceptance.md` for product outcome/oracle semantics, `goal-execution.md` for impact and proportional regression, `systematic-debugging.md` for root-cause convergence, and the Acceptance Surface Provenance invariant for observed runtime identity.

## When to use

Use only when the Goal has a material release boundary such as a distributable package/executable, supported install/start environment, hosted deployment, release artifact, extension/app publication or equivalent release context.

Do not invoke this merely for exploratory Owner/UI review, a tiny local edit with no meaningful release boundary, or because a branch/PR exists.

## Distinct claims

Keep these evidence claims separate:

- **Product Acceptance** — the identified candidate satisfies the predefined Goal/CUJ/product outcome.
- **Release Qualification** — the identified release subject can be built/installed/started/verified/released in the supported release context with matching evidence.
- **Runtime Activation** — the observed serving surface is traceably associated with the intended qualified release reality.

None implies the next. `PRODUCT_ACCEPTED` is not `RELEASE_QUALIFIED`, and `RELEASE_QUALIFIED` is not proof that a runtime is active.

## Establish the qualification subject

Identify only the release reality material to the claim. Depending on product shape this may include:

- source/candidate revision;
- artifact/package/assets or direct-source execution identity;
- material build/package configuration;
- dependency/toolchain versions or required system tools;
- supported OS/runtime/browser/provider isolation assumptions; and
- release environment/configuration that can change build, start or verification behavior.

Do not require one universal source-to-binary topology. Prefer the already-qualified artifact when a product produces one; a rebuild or materially different output is a new delta whose qualification/equivalence must be established.

## Evidence continuity across post-acceptance deltas

Evidence established for candidate A may support candidate B only criterion-by-criterion when the identified A -> B delta is shown not to materially affect:

- the claimed accepted behavior;
- relevant inputs, state or data;
- the acceptance/qualification oracle; or
- provenance of the surface/artifact on which that evidence depends.

Unknown or unresolved impact is not preservation. The affected criterion remains `UNVERIFIED` for B until matching evidence is re-established.

Do not infer neutrality from filenames or labels such as CI, test, config, packaging, timeout, fixture or dependency. Those changes may alter behavior or the oracle. If the harness/oracle changed, the changed harness cannot independently self-prove that prior acceptance remains valid.

Do not invalidate unrelated criteria merely because the commit SHA changed. Re-establish only evidence whose claim is materially affected. Return to Owner judgement only when an affected criterion actually uses subjective Owner experience as its oracle.

## Qualification evidence

Use proportional evidence. Prefer the cheapest check that can discriminate the current release risk, then broader confirmation at meaningful convergence points. Typical concerns may include declared dependencies/system tools, supported OS/path behavior, provider isolation, browser/runtime startup, filesystem/config roots, build/package smoke, affected tests, a critical release journey and broader regression.

This is not a mandatory fixed order and does not make a full suite mandatory for every project. A fast comprehensive suite may be cheaper than a special preflight; a costly golden journey may belong later. Use current risk and evidence cost.

Product Acceptance remains the oracle for product behavior. Release Qualification must not weaken product criteria or tests merely to make CI green.

## Convergence / shared-boundary failures

When multiple qualification failures point to the same environment, harness, provider, filesystem, browser/runtime or other shared boundary—or local fixes stop measurably improving qualification—stop treating each leaf failure as an independent patch target.

Invoke `systematic-debugging.md` to localize and test the shared root-cause hypothesis, and use Goal Execution stop-loss/impact reasoning. Do not introduce a retry counter or new persisted failure state.

## Qualification claim

Claim `RELEASE_QUALIFIED` only when the required release evidence matches the identified qualification subject and material conditions. Evidence belonging to an older candidate/HEAD/artifact does not qualify the current one without established preservation/equivalence.

If required qualification evidence is missing, failed or mismatched, report the concrete release blocker without revoking unrelated Product Acceptance evidence. It is valid to report in prose that the product is accepted while release qualification is blocked.

After qualification, native project tooling may merge/promote/deploy according to project authority. Use Acceptance Surface Provenance to prove any observed active runtime corresponds to the intended qualified release reality. Promotion/deployment itself is not a CADS control.

## Result contract

Return one concise result:

- `RELEASE_QUALIFIED`: matching evidence establishes release readiness for the identified subject/context;
- `RELEASE_BLOCKED`: concrete qualification evidence is missing/failing/mismatched, while separately reporting any still-valid Product Acceptance evidence; or
- `NOT_APPLICABLE`: no material release boundary exists for this Goal.

These are evidence conclusions, not persisted lifecycle states, grants or deployment authority.
