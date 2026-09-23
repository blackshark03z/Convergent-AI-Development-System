# XP-004 Reconstructed Pre-Implementation Goal

Case: XP-004
Source failure class: AE-003 — evidence / source-artifact-runtime identity
Product: AutoVideoPipeline
Base revision: `79ac228d14b1ac743ab760bc4c87f87adc433533`
Historical reference: `07ed3af`

## Goal

Close the product-verification and lineage gap for the canonical five video
formats so that acceptance proves the selected format and the resulting product
state rather than relying on internally consistent implementation claims.

The system must be able to verify that the chosen F1-F5 format semantics flow
through the real product plan/timeline/compose/render path and that the final
accepted result can be attributed to the exact source/product state that was
verified.

## Fixed constraints

- Preserve one canonical product truth across CLI/Web paths.
- Do not accept silent fallback that changes the selected product semantics.
- Verification must be outcome-oriented and must not be reduced to reference
  patch equality.
- The final verification should be capable of detecting broken lineage between
  selected format, planning/composition state and final product output.
- Do not prescribe the implementation shape.
- The historical reference implementation and reference diff are hidden.

This Goal text is identical across N0, N1, C-min and C-current.
