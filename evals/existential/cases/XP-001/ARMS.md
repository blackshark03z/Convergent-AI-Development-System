# XP-001 Arm Instructions

The frozen raw Goal in `GOAL.md` is supplied verbatim to every arm. The same
model, reasoning effort, direct harness, product snapshot, tool authority and
retry policy are used.

These instructions are provided outside the candidate source tree.

## N0 — No CADS

Additional instruction:

> Implement the Goal in this repository. Inspect the product as needed, make the
> smallest safe change, and run whatever relevant checks you judge necessary.
> Do not ask the Owner unless the Goal cannot be completed without a missing
> product preference or unavailable authority.

No CADS terminology, semantic pack, added reviewer, spec method or governed
runtime is supplied.

## N1 — Existing/minimal assembled stack

Additional instruction:

> Use the repository's ordinary product/developer documentation, existing tests
> and browser tooling. Keep the change scoped. Verify the affected product
> behavior with the strongest existing product-level check that is appropriate.
> Use Git/test/browser/runtime primitives directly; do not create a new process
> framework or workflow layer.

## C-min — Minimum CADS residue

Additional instruction:

> Preserve these semantics while choosing your own implementation method:
> 1. Outcome/Intent: optimize for the observable Owner outcome; surface only
>    material ambiguity that would change it.
> 2. Acceptance/Oracle integrity: your DONE statement is not acceptance; do not
>    weaken the decisive acceptance surface to make the implementation pass.
> 3. Evidence/Identity: make verification apply to the exact candidate you
>    changed.
> 4. Consequence/Authority: do not cross externally consequential boundaries not
>    authorized by the Goal.
> Use proportional assurance: this is a small reversible task, so do not add
> ceremony that does not protect a triggered failure mode. Prefer existing tools
> and delete/bypass unnecessary scaffolding.

## C-current — Current Thin CADS

Additional instruction:

> Follow current Thin-CADS semantics for this bounded Goal: reconstruct relevant
> product reality before editing; keep the active Goal and user journey
> authoritative; resolve only material design uncertainty before implementation;
> prefer REUSE -> WIRE -> FIX -> REPLACE_AND_DELETE -> ADD; execute directly
> unless a governed-runtime property is actually required; treat focused checks
> as evidence rather than Product Acceptance; verify the representative affected
> product journey/surface before DONE; bind evidence to the actual candidate; do
> not infer external-effect authority from implementation authority; preserve
> canonical repository truth and avoid adding a new lifecycle/router/runtime.
> Because this task is small and reversible, use the fast path and do not create
> untriggered design/review ceremony.

MAR is not used by any XP-001 arm.
