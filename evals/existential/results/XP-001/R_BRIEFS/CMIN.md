IMPLEMENTATION_BRIEF

**Outcome**

- On the Production surface, keep the existing canonical primary action visible and reachable without requiring the Owner to scroll merely to find it on supported desktop layouts, including the repository’s constrained-height desktop viewport of **1366×768**.
- Preserve the current Production workflow: primary-action identity, label, enabled/disabled state, command/navigation behavior, and surrounding user-facing behavior must not change.

**Acceptance**

- Add or update real-browser acceptance using the existing local fixture/harness.
- At **1366×768**, start from the top of the Production surface (`scrollY = 0`) and render a representative actionable Production state whose content is tall enough to exercise the problem. **Do not call `scrollIntoView` or otherwise pre-scroll before the assertion.**
- PASS when the single existing `#productionPrimaryAction` has a visible, non-zero rectangle fully inside the viewport (`top >= 0`, `bottom <= innerHeight`) and remains reachable for its existing interaction when that action is enabled.
- Verify the normal desktop case at **1920×1080** remains valid and no horizontal overflow or new nested operational scrolling is introduced.
- Existing Production workflow/browser acceptance must continue to pass, demonstrating that the change affects presentation only and does not alter Production behavior.
- Verification evidence must be produced from the exact candidate handed back by I.

**Constraints / Non-goals**

- Make the smallest coherent layout/presentation change necessary. Do not prescribe a particular CSS/layout technique.
- Do not add a second primary action or redesign unrelated Production/Story Audio surfaces.
- Do not change backend workflow/state semantics or introduce new lifecycle/architecture machinery.
- Verification must use local/test fixtures only; do not call paid/external providers or the canonical production runtime.

OWNER_INPUT_REQUIRED: no
