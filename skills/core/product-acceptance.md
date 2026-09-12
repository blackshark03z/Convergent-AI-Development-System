# Product Acceptance

An advisory procedure for proving that engineering work has converged into the
actual product before declaring completion. It creates no acceptance database,
lifecycle state or runtime authority.

Use the predefined Goal acceptance from `TASK.md` and the canonical development
semantics in `docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`.

## When to use

Use before making a material product-completion claim such as `FIXED`, `DONE`,
`READY`, product-complete, or equivalent. Run it after implementation has
already reached the predefined acceptance boundary, not as a substitute for
that definition. When a material release boundary exists, Product Acceptance is
necessary evidence about product outcome but does not by itself establish
`RELEASE_QUALIFIED`; use `release-qualification.md` before a release-ready claim.

## Acceptance proof

1. Re-read the original Goal, CUJ and acceptance. Do not weaken acceptance to
   match the implementation that happened to be built. If a material acceptance
   criterion or oracle changed after implementation began, establish that the
   change is an explicit legitimate clarification/change of intent rather than a
   weakening made merely to obtain PASS. A changed implementation-coupled test
   does not independently prove the criterion simply because it now passes.
2. Identify the canonical Product HEAD / source state containing the intended
   work and confirm valuable Goal work is not stranded in another workline.
3. When runtime behavior matters, identify the actual runtime source/build,
   configuration/environment and data authority exercised. Do not infer runtime
   identity from Git state alone.
4. Run the representative acceptance fixture / golden input through the full
   Critical User Journey on the real supported surface whenever feasible. When
   the Goal depends on multiple capabilities composing into one user outcome,
   isolated feature/subsystem checks cannot substitute for this journey evidence.
   For affected stateful handoffs, use the focused checks below as part of this
   journey evidence.
   For a workflow intended to run repeatedly, include the terminal-to-next-cycle
   transition when state leakage is a material risk: complete Run A, start the
   representative Run B, verify B receives the intended active context rather
   than stale state from A, and verify A's historical configuration/artifacts
   remain bound to the correct snapshot/state.
5. Confirm the observable final output or behavior, including discoverability
   and reachability for user-facing capability. The intended user should be able
   to identify relevant next actions, retain necessary context, recover from
   applicable failures, and reach the useful result without undocumented
   external guidance or implementation knowledge they are not expected to have.
   Product-provided onboarding/help is legitimate guidance.
6. Run the relevant focused/integration/regression evidence required by the
   Goal and risk. Tests support the conclusion; they do not replace the real
   acceptance oracle.
7. Check that the change has converged: one authoritative product path, no
   accidental competing implementation, and no unpreserved Goal value trapped
   outside the Product HEAD.
8. Check decision continuity: no material accepted Goal/product/architecture
   direction that would alter a later session remains only in chat, memory or an
   agent report. Persist it under `docs/decisions/` before closure when the
   materiality test is met.
9. If Goal-created workspaces/residue now need closure, hand off to
   `workspace-hygiene.md`; cleanup is not itself proof of product acceptance.

Treat evidence criterion-by-criterion. A command, test, or observation proves an
acceptance criterion only when it is a relevant oracle for that criterion and is
tied to the identified candidate and applicable conditions. Missing matching
evidence means `UNVERIFIED`; do not convert it to PASS, and do not infer Journey
PASS from the sum of isolated feature PASS results. Evidence carried to a later
candidate must satisfy the same rule: changed SHA alone does not invalidate
unaffected criteria, but unresolved material impact on behavior, inputs/state/data,
the oracle or surface provenance leaves the affected criterion `UNVERIFIED`.

## Acceptance Surface Provenance Invariant

When Product or Owner Acceptance relies on an observed product surface, evidence
from that surface is admissible only when the material runtime, artifact/assets,
configuration and data authorities that can affect the claimed behavior are
traceably associated with the intended candidate. The association is a
provenance relationship, not a requirement that source, artifact, process,
assets and configuration share one literal hash or identity.

If that association is stale, materially ambiguous, conflicting, or cannot be
established, the affected evidence remains `UNVERIFIED` and must not support
`PRODUCT_ACCEPTED` or `PRODUCT_READY_FOR_OWNER_ACCEPTANCE`. Ambiguity matters
only when it can change the behavior claimed by the acceptance evidence; an
unrelated old process or artifact is not automatically blocking.

Use the smallest evidence appropriate to the product shape. A CLI may execute
source directly; a desktop product may bind an executable/package; a SPA may
need client-visible asset/cache provenance; a rolling or multi-replica service
may need proof that request-reachable versions cannot expose materially stale
behavior. A self-reported version string is supporting evidence only when it is
causally tied to the material actually serving the surface; it cannot self-prove
identity when it may be stale or hard-coded.

An isolated preview/worktree/runtime may be a valid acceptance surface for its
identified candidate. Evidence for candidate C does not automatically prove a
later integrated state H when H materially differs; establish equivalence or
obtain matching evidence for the state being claimed. Likewise, evidence from
an earlier observation does not support a later Owner review if the material
surface changed in between unless matching provenance/equivalence is
re-established.

This invariant introduces no deployment/promotion phase, persistent state,
mandatory restart, canonical-HEAD-before-preview rule, or universal provenance
schema. When no persistent/observed surface is material to the criterion, normal
Product Acceptance applies without extra runtime ceremony.

## Focused handoff evidence

When a change materially affects the next journey step, verify the existing
acceptance against the authoritative domain postcondition, including any
relevant valid field combination identified during Goal Execution.

When the paths can behave differently, exercise both:

- completing the action through the supported surface and observing the next
  step in the same session; and
- reopening/reloading into the completed state and observing the next step.

Check the expected next action and the context/data that must remain unchanged.
Where an adjacent incomplete state could accidentally become unblocked, include
that focused negative case. Reuse existing evidence when it covers these paths;
do not expand this into all possible state/branch combinations.

A fixture initialized in a completed state proves that state's rendering, not
the action-to-next-step transition. Report those observations separately; an
unexercised required path remains `UNVERIFIED`. Mocked responses do not prove
backend persistence or historical-data preservation. Use an appropriate oracle
for those claims. Offline fixtures may establish bounded regression evidence
without authorizing production mutations or provider calls, and do not replace a
required real-journey or subjective Owner oracle.

## Authority and verdicts

Workers and Tech Leads may establish engineering evidence and report:

- `CHECKPOINT_OK`: a bounded blocker/change is verified but product acceptance
  is not yet established;
- `BLOCKED`: the predefined journey cannot proceed, with concrete evidence;
- `PRODUCT_READY_FOR_OWNER_ACCEPTANCE`: all objectively dischargeable evidence
  is complete but one or more predefined acceptance criteria require subjective
  Owner product/real-use judgement; or
- `PRODUCT_ACCEPTED`: every predefined acceptance criterion is satisfied and no
  remaining criterion requires unresolved Owner judgement/authority.

Owner owns product intent, material product trade-offs, consequential
authorization and subjective real-use acceptance where human experience is the
oracle. Engineering PASS, clean Git, build/package hashes, CI success, browser
fixtures or an agent report must not be substituted for such a subjective Owner
criterion.

When the predefined acceptance is fully machine-observable, including for a
user-facing Goal whose required journey and outcome are objectively decidable,
the Tech Lead may establish `PRODUCT_ACCEPTED` from the independent oracle. Do
not invent Owner ceremony solely because the product has a UI.

For a mixed Goal, discharge objective criteria autonomously and request Owner
attention only for the remaining subjective/material Owner-controlled criteria.
Do not broaden one subjective criterion into manual acceptance of otherwise
objective criteria.

## Failure handling

If the real journey exposes a blocker, return to `systematic-debugging.md` for
that first blocker, make the smallest coherent fix, and resume the same
acceptance fixture. Do not open a new product Goal merely because acceptance
found a defect.
