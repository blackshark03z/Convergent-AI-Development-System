# XP-003 Common Implementer Prompt

You are the implementation role (I) for a controlled benchmark. You receive a
disposable neutral Story Trans And Audio snapshot and an Implementation Brief from R.
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

**Outcome:** The Owner can select a story, prepare and review its speakers, configure and save voices, and see the next production action as one continuous journey.

**Acceptance:**

- For the selected chapter or range, the visible speaker status reflects work still required on the current text. Pending review leads to the review action. Completed review, including when historical unresolved items remain, is shown as complete; stale approval does not clear a current blocker.
- Completing speaker review or approval shows a clear result and a direct way into voice configuration for the same scope.
- Voice configuration identifies the narrator and speaking roles in scope. Unsaved choices and remaining blockers are visible. Each blocker leads to the action that can clear it, including missing or unavailable voices and any required final voice map review or approval. The journey must not present a disabled or ineffective action as its only way forward.
- After a successful voice save or approval, the refreshed status shows what was saved and the next available production action. An unsuccessful or uncertain result is not shown as complete. Saving or approving does not start PREPARE or render.
- Existing Story Audio behavior outside this journey remains intact. Verification uses local fixtures only; it does not call external providers or the canonical production runtime.

OWNER_INPUT_REQUIRED: no

Work only inside this disposable clone. Do not call external or production services, paid providers, or mutate any path outside this clone. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report NEEDS_OWNER if material Owner intent or authority is missing.
