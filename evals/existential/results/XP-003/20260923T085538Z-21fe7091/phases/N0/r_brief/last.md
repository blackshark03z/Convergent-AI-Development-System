IMPLEMENTATION_BRIEF

**Outcome:** The Owner can move through the selected story and chapter scope from speaker review to voice configuration, saving, and the next production action as one clear flow.

**Acceptance:**

- After individual or batch speaker review, show the saved result and any remaining speaker decisions. Deferred, failed, or unanalyzed items must remain visible as blockers with a way to reach the action that clears them.
- Once speaker review is complete, provide a clear continuation into voice assignment for the same scope, with the current saved state shown.
- Voice status must reflect the actual remaining work, including unsaved choices, unusable or missing voices, and any casting plan creation or approval still required. A required step must remain actionable even when there are no voice changes to save.
- After voice work is saved or approved, show the result and the next valid production action for that scope. Failed or partial saves must not appear complete. Neither saving nor approval starts rendering automatically.
- Preserve unrelated Story Audio behavior.

**Constraints:** Use only the assigned repository for implementation and verification; do not call paid or external providers or the canonical production runtime.

OWNER_INPUT_REQUIRED: no