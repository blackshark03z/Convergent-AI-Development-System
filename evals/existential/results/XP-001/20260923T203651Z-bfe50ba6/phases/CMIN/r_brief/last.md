IMPLEMENTATION_BRIEF

**Outcome:** On Production, the current primary action is visible and reachable on a supported desktop layout, including a constrained-height viewport, without scrolling to find it.

**Acceptance:** In isolated browser fixtures at 1366×768 and 1366×600, load Production at the top of the page with a current task whose content is long, such as voice review or preflight. When the task has a primary action, its full button must be visible, unobscured, and clickable. It must remain easy to reach while reviewing the task content. Verify that the button still shows and performs the action for the current task, and that the layout has no horizontal overflow. Run the affected Production browser behavior against the exact candidate delivered.

**Constraints / authority:** Preserve the existing workflow, action gates, and behavior outside this layout correction. Use an isolated runtime and fixtures; do not invoke providers, the canonical runtime, PREPARE, START_RENDER, or Human QA. Implementation completion and reasoning review are not Owner product acceptance.

OWNER_INPUT_REQUIRED: no