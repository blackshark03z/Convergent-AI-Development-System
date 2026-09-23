IMPLEMENTATION_BRIEF

**Outcome:** The Owner can follow the selected story scope from speaker review through voice configuration and into the next production gate, with a truthful status and a clear next action at each transition.

**Acceptance:**
- After speaker review or approval, show the result and the number of decisions still requiring review. An approved current review with zero remaining decisions must allow continuation into voice configuration, even if historical unresolved items exist.
- If speaker or voice work is blocked, identify the current blocker and provide a path to the action that clears it. Do not show a completed or ready state while a required blocker remains.
- Voice configuration is reachable from completed speaker review and shows the effective speaking roles for the selected scope. After voice changes are saved or approved, show the saved result and a clear action to the next required gate: final voice-map review where required, then production preflight when ready.
- Preserve the selected scope across these steps. Saving or approving must not implicitly PREPARE a Job, start render, call a provider, or change existing audio.

**Verification:** Demonstrate the connected journey in an isolated browser fixture, including an approved review with a nonzero historical unresolved count, a remaining blocker, and a successful voice save. Confirm that the visible next action matches authoritative readiness and that no render command is issued.

OWNER_INPUT_REQUIRED: no