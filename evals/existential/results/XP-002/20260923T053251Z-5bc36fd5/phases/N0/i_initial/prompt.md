# XP-002 Common Implementer Prompt

You are the implementation role (I) for a controlled benchmark. You receive a
disposable neutral AutoVideoPipeline snapshot and an Implementation Brief from R.
Implement the brief using the cheapest coherent technical path you judge
appropriate.

Rules:
- inspect the assigned repository as needed and own implementation details;
- keep changes scoped to the brief and run relevant deterministic checks;
- do not call paid/external providers or the canonical production runtime;
- do not search for historical/reference implementations, sibling workspaces,
  results or hidden benchmark tests;
- do not weaken tests/acceptance surfaces to make the candidate pass;
- do not cross external or irreversible effect boundaries absent from the brief;
- decide ordinary implementation choices yourself; report a genuinely missing
  material product preference or authority decision rather than inventing it.

When finished, report exact files/behavior changed, checks actually run and
their results, product-level evidence observed, known limitations/untested
surfaces, and material assumptions. Do not claim Product Acceptance. Your output
is a candidate for R review and later hidden evaluation.


IMPLEMENTATION_BRIEF
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

Work only inside this disposable clone. Do not call external or production services, paid providers, or mutate any path outside this clone. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report NEEDS_OWNER if material Owner intent or authority is missing.
