IMPLEMENTATION_BRIEF

**Outcome:** For F5, compile a bounded, owner-reviewable table of online stock proposals for every planned shot, grounded in that shot’s script and visual intent.

**Acceptance:**

- Every planned F5 shot has a row identifying the shot, its timing or narration context, its visual intent, and a small bounded set of stock candidates.
- Each candidate has enough identity and preview information for the Owner to inspect it, plus a concise reason it fits the shot. Distinct shot intents produce appropriately distinct searches or proposals; generic story-wide keywords alone do not satisfy this.
- Ineligible or clearly mismatched footage is excluded. A shot with no suitable candidate is marked unresolved, without arbitrary filler.
- Compiling or viewing the table leaves every candidate provisional. It does not approve a clip, assign a final production choice, or silently substitute one into the production timeline.
- Offline tests with a fake stock provider demonstrate shot coverage, intent-based proposals, bounded results, unresolved shots, and the provisional boundary.

**Constraints / non-goals:** Keep F5 footage within its online stock source policy. The later approve, replace, confirm, and cancel lifecycle is outside this brief. Verification must not call external providers or the canonical production runtime.

OWNER_INPUT_REQUIRED: no