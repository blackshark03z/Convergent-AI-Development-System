IMPLEMENTATION_BRIEF

**Outcome:** On Production, the current primary action stays fully visible and operable in the initial viewport when a selected scope has long task content.

**Acceptance:**
- In an isolated browser fixture, check the Production surface at 1366×768 and a constrained-height 1366×600 desktop viewport. After the task renders, the current primary button is fully within the viewport, unobscured, and reachable by keyboard and pointer without scrolling to find it.
- Repeat after a task transition or refresh that changes the current action. The visible action still matches the authoritative task; states with no primary action do not gain one.
- Long content remains readable and reachable, with no horizontal overflow or action covering content. Existing focus, scroll, and production behavior remain intact.

**Constraints / authority:** Make the smallest coherent Production layout change. Preserve the existing task flow and separate PREPARE and START_RENDER actions. Verify against disposable fixture data without provider calls or the canonical runtime. Bind browser evidence to the candidate before READY; Owner product acceptance remains separate.

OWNER_INPUT_REQUIRED: no