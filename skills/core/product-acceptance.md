# Product Acceptance

An advisory procedure for proving that engineering work has converged into the
actual product before declaring completion. It creates no acceptance database,
lifecycle state or runtime authority.

Use the predefined Goal acceptance from `TASK.md` and the canonical development
semantics in `docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`.

## When to use

Use before making a material completion claim such as `FIXED`, `DONE`, `READY`,
release-ready, product-complete, or equivalent. Run it after implementation has
already reached the predefined acceptance boundary, not as a substitute for
that definition.

## Acceptance proof

1. Re-read the original Goal, CUJ and acceptance. Do not weaken acceptance to
   match the implementation that happened to be built.
2. Identify the canonical Product HEAD / source state containing the intended
   work and confirm valuable Goal work is not stranded in another workline.
3. When runtime behavior matters, identify the actual runtime source/build,
   configuration/environment and data authority exercised. Do not infer runtime
   identity from Git state alone.
4. Run the representative acceptance fixture / golden input through the full
   Critical User Journey on the real supported surface whenever feasible.
5. Confirm the observable final output or behavior, including discoverability
   and reachability for user-facing capability.
6. Run the relevant focused/integration/regression evidence required by the
   Goal and risk. Tests support the conclusion; they do not replace the real
   acceptance oracle.
7. Check that the change has converged: one authoritative product path, no
   accidental competing implementation, and no unpreserved Goal value trapped
   outside the Product HEAD.
8. If Goal-created workspaces/residue now need closure, hand off to
   `workspace-hygiene.md`; cleanup is not itself proof of product acceptance.

## Authority and verdicts

Workers and Tech Leads may establish engineering evidence and report:

- `CHECKPOINT_OK`: a bounded blocker/change is verified but product acceptance
  is not yet established;
- `BLOCKED`: the predefined journey cannot proceed, with concrete evidence; or
- `PRODUCT_READY_FOR_OWNER_ACCEPTANCE`: the predefined real journey and evidence
  are complete enough for owner real-use where owner experience is the final
  oracle.

For a user-facing product, only the Owner's real-use decision can establish
`PRODUCT_ACCEPTED`. Do not translate engineering PASS, clean Git, build/package
hashes, CI success, browser fixtures or an agent report into owner acceptance.

For non-user-facing Goals whose predefined acceptance is fully machine-observable,
the Tech Lead may close the Goal from that oracle; do not invent owner ceremony
where no owner-use criterion exists.

## Failure handling

If the real journey exposes a blocker, return to `systematic-debugging.md` for
that first blocker, make the smallest coherent fix, and resume the same
acceptance fixture. Do not open a new product Goal merely because acceptance
found a defect.
