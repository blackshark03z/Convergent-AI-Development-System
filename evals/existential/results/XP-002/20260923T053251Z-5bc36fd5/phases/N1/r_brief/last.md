IMPLEMENTATION_BRIEF

**Outcome:** For an F5 story, produce an Owner reviewable table with a proposal row for every planned shot. Derive each shot’s stock search intent from its script and shot meaning, then present a bounded set of relevant online stock candidates. A proposal is never a final production choice.

**Acceptance:**
- Every planned F5 shot has a row, including shots with no suitable match. Each row identifies the shot and its story or visual intent, and shows candidate identity, a preview reference when available, and enough fit or exception information for the Owner to judge it.
- Distinct shot intents yield distinct searches and relevant rankings. Generic storywide keywords alone cannot drive every row. Ineligible, clearly conflicting, or unsuitable candidates are not presented as usable matches.
- Candidate lists have a small, enforced upper bound. Search failure or no match remains explicit; it does not trigger an arbitrary substitute.
- Producing the table does not approve, download, assign, or commit footage to the final timeline. Offline tests with a fake stock provider demonstrate these outcomes without calling external services or the production runtime.

**Scope:** This covers proposal compilation and reviewability only. The later approve, replace, confirm, and cancel lifecycle is outside this brief.

OWNER_INPUT_REQUIRED: no