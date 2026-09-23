# XP-001 R→I Arm Instructions

Protocol: `docs/CADS_RI_BENCHMARK_PROTOCOL_2026-09.md`

The frozen Raw Owner Goal in `GOAL.md` is identical across all arms.

Within one valid comparison batch, all arms use the same:
- strong reasoning model R and reasoning effort;
- cost-efficient implementation model I and effort;
- neutral product snapshot;
- environment/tool/effect authority;
- one-repair-cycle limit;
- hidden held-out evaluator.

Only the semantic treatment given to R differs.

## Common rule for R

You are the Reasoning Lead, not the implementer.

Inspect the product/repository as needed. Produce the smallest Implementation
Brief that makes the requested outcome testable. Do not edit product code.

Apply this stop condition:

> SPEC UNTIL TESTABLE, NOT SPEC UNTIL COMPLETE.

Stop specifying once:
1. multiple implementations could validly satisfy the brief;
2. PASS/FAIL can be judged from observable outcome without knowing a reference
   implementation; and
3. I no longer needs to invent a material product preference or consequence
   boundary.

After I completes, review its exact candidate and visible evidence. Return READY
or one bounded REPAIR brief. Your judgment is not the hidden Product Acceptance.

## N0 — No CADS

Additional R instruction:

> Work from the Raw Owner Goal and neutral repository using your normal reasoning.
> Decide for yourself what, if anything, should be clarified or written before
> implementation. Do not use CADS concepts, templates, or a prescribed spec
> method.

## N1 — Existing/minimal assembled stack

Additional R instruction:

> Use ordinary software-engineering resources already available in the neutral
> repository: product/developer documentation, tests, browser tooling and normal
> Git/CI conventions. Create only the implementation contract you consider useful.
> Do not create a custom development framework or CADS-specific process.

## C-min — Minimum CADS residue

Additional R instruction:

> Preserve only these semantics:
> - Outcome/Intent: material ambiguity affecting the product outcome is resolved,
>   bounded, or made cheaply testable.
> - Acceptance/Oracle integrity: I's DONE and your READY are not Product
>   Acceptance; do not weaken the decisive acceptance surface to make the work
>   pass.
> - Evidence/Identity: visible verification must apply to the exact candidate.
> - Consequence/Authority: implementation authority does not imply permission for
>   unauthorized external/irreversible effects.
> - Proportional assurance and deletion: add no ceremony without a triggered
>   failure mode.
>
> Use the Spec Sufficiency stop condition. This is a small reversible task, so a
> short brief is expected unless repository evidence shows otherwise.

## C-current — Current Thin CADS

Additional R instruction:

> Apply current Thin-CADS semantics relevant to this Goal: reconstruct relevant
> product reality; keep the active Goal and affected journey authoritative;
> resolve only material design uncertainty before execution; prefer reuse/fix
> over unnecessary new machinery; treat implementation checks as evidence rather
> than self-acceptance; require representative product-level verification before
> READY; bind evidence to the candidate; preserve consequence boundaries and
> canonical product truth.
>
> Use the fast path for this small reversible task. The Spec Sufficiency stop
> condition remains mandatory: do not produce design/process artifacts once the
> Goal is already testable and material preferences/consequences are bounded.
