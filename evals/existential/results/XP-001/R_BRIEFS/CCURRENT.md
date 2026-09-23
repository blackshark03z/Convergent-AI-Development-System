IMPLEMENTATION_BRIEF

**Outcome**

- On `#/production`, keep the existing single canonical primary action fully visible and directly reachable at the initial scroll position on the supported desktop layout, including a constrained-height desktop viewport. The Owner must not need to vertically scroll merely to discover or reach the current action.
- Preserve the existing Production journey, action identity, labels, enabled/disabled semantics, consequence boundaries, and decision context. Do not introduce a second competing primary action.

**Acceptance**

- Extend the existing isolated real-Chromium Production acceptance with representative content-heavy actionable state(s).
- Verify at `1366x768`, `1366x600` constrained-height desktop, and retain the existing `1920x1080` regression.
- After Production has rendered and page scroll is reset to the initial position:
  - exactly one canonical primary action is visible;
  - its full bounding box is inside the unobscured viewport;
  - no vertical scroll is required to find it;
  - when existing semantics make it enabled, it remains keyboard-focusable and clickable; existing disabled/busy semantics remain unchanged;
  - the action remains logically associated with/follows its required decision context rather than being replaced by an unrelated shortcut;
  - no horizontal overflow or new operational nested-scroll requirement is introduced.
- Content and controls beneath/around any persistent action treatment must remain reachable and must not be permanently obscured.
- Existing affected Production browser journeys, primary-action labels, state transitions, and safety assertions continue to pass.

**Constraints / Non-goals**

- Make the smallest coherent Production layout change. Do not redesign unrelated Story Audio surfaces or workflows.
- Do not change Production state resolution, task projection, command semantics, PREPARE/START_RENDER separation, provider behavior, backend authority, or canonical data.
- Do not add a new lifecycle, state, endpoint, or layout abstraction solely for this Goal.
- Preserve existing responsive behavior outside the affected supported desktop layout unless a minimal adjustment is required to prevent regression.
- Verification must use isolated/local fixtures only; do not call paid/external providers or the canonical production runtime.

**Effects / Authority**

- Implementation may change the minimum Production UI/CSS/DOM and browser acceptance code necessary to satisfy the observable layout outcome.
- No new product-side authority or mutation capability is granted.
- READY evidence must come from the implemented candidate and include the representative real-browser viewport checks above.

OWNER_INPUT_REQUIRED: no
