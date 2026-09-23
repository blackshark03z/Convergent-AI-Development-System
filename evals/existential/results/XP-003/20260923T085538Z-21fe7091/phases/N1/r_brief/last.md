IMPLEMENTATION_BRIEF

**Outcome:** For the selected Story Audio book and chapter range, the Owner can move through speaker review, voice assignment, save, and approval as one clear journey, with a truthful status and next action at each step.

**Acceptance:**

- While speaker decisions remain, show the remaining work and an action that reaches it. Once review is complete, show completion and a clear path into voice configuration; historical unresolved counts must not appear as a current blocker.
- Voice configuration shows the selected scope and any actual missing, unavailable, or conflicting voices. A blocker points to the action needed to clear it. The journey remains usable when there are no Gemini voice suggestions.
- After saving voice changes, show what was saved and whether voice-map approval is still required. After approval, show the next production action in the same scope without a dead end or a misleading “ready” state.
- Speaker approval, voice save, and voice-map approval do not silently PREPARE a Job or start render. PREPARE and START_RENDER remain separate explicit Owner actions.
- Verify the connected journey with isolated, offline evidence, including an incomplete review, completed review, a voice blocker, and successful voice approval. Preserve unrelated Story Audio behavior.

OWNER_INPUT_REQUIRED: no