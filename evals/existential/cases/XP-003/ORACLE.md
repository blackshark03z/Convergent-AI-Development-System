# XP-003 Held-out Oracle

The oracle checks the observable assignment journey rather than historical patch equality.

It requires:
- speaker-review blockers are visible and truthful;
- voice assignment is unavailable while speaker review is unresolved;
- completing speaker review exposes and emphasizes the voice-assignment step;
- the completed state has no unresolved speaker row and presents character/voice work;
- saving voice assignment does not skip the required voice-map step and exposes a clear next action;
- voice-map review exposes a clear continuation;
- the selected book/range survives the transition back toward production;
- the assignment journey does not silently start rendering;
- the candidate worktree is unchanged by evaluation.

Layout, polling internals, repair workflow, historical class names, and patch/file equality are outside XP-003.