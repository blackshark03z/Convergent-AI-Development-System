IMPLEMENTATION_BRIEF

**Outcome:** On Production, the current primary action is visible and operable without scrolling to find it on the supported desktop layout, including a constrained-height viewport.

**Acceptance:** In an isolated browser fixture, verify at 1366×768 and 1366×600 that the primary action is within the visible viewport, unobscured, and keyboard and pointer operable at page scroll position 0. Cover both the no-scope state and a selected-scope task with content taller than the viewport. After the task changes, the action must still show the correct current label and invoke its existing behavior. Preserve access to task content and check for horizontal overflow.

**Constraints / authority:** Keep the change local to Production layout. Preserve the existing workflow, projection-driven action, command boundaries, and behavior on other surfaces. Use disposable fixtures only; do not contact providers or the canonical runtime.

OWNER_INPUT_REQUIRED: no