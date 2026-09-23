IMPLEMENTATION_BRIEF

**Outcome:** The Owner can select a story, prepare and review its speakers, configure and save voices, and see the next production action as one continuous journey.

**Acceptance:**

- For the selected chapter or range, the visible speaker status reflects work still required on the current text. Pending review leads to the review action. Completed review, including when historical unresolved items remain, is shown as complete; stale approval does not clear a current blocker.
- Completing speaker review or approval shows a clear result and a direct way into voice configuration for the same scope.
- Voice configuration identifies the narrator and speaking roles in scope. Unsaved choices and remaining blockers are visible. Each blocker leads to the action that can clear it, including missing or unavailable voices and any required final voice map review or approval. The journey must not present a disabled or ineffective action as its only way forward.
- After a successful voice save or approval, the refreshed status shows what was saved and the next available production action. An unsuccessful or uncertain result is not shown as complete. Saving or approving does not start PREPARE or render.
- Existing Story Audio behavior outside this journey remains intact. Verification uses local fixtures only; it does not call external providers or the canonical production runtime.

OWNER_INPUT_REQUIRED: no