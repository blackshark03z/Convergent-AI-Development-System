# XP-001 Held-Out Oracle Contract

Status: frozen before arm execution
Historical reference: `dbef3b7`
Reference implementation shape is NOT part of acceptance.

## Acceptance meaning

The Production primary action must be immediately visible/reachable in the
representative desktop production state without an implicit page scroll, while
preserving the existing no-horizontal-overflow and no-pathological-nested-scroll
layout guarantees.

## Held-out observations

At the representative 1366-wide constrained-height desktop viewport:

1. the primary action bounding box is fully inside the visible viewport;
2. initial page `scrollY == 0`;
3. document width does not exceed viewport width beyond the existing tolerance;
4. the Production workbench does not introduce a nested scroll container that
   hides/repositions the primary action.

At the representative 1920-wide desktop viewport:

5. the primary action remains visible;
6. there is no horizontal overflow.

The candidate must also preserve the relevant pre-existing Production browser
workflow assertions from the base.

## Explicitly excluded from the held-out oracle

The historical reference commit also changed an assertion involving
`scenarioA.prepareCalls`. That change is not logically required by this Goal and
must not be used to score XP-001.

Exact CSS properties, grid areas, sticky positioning, file paths, line counts or
patch equivalence are not acceptance criteria.

## Evaluator rule

The held-out evaluator must be materialized only after the candidate stops. It
may reuse the product's existing browser harness, but it must evaluate the
outcomes above rather than require the historical implementation.
