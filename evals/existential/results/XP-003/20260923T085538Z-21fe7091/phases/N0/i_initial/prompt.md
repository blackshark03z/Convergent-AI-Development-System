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

**Outcome:** The Owner can move through the selected story and chapter scope from speaker review to voice configuration, saving, and the next production action as one clear flow.

**Acceptance:**

- After individual or batch speaker review, show the saved result and any remaining speaker decisions. Deferred, failed, or unanalyzed items must remain visible as blockers with a way to reach the action that clears them.
- Once speaker review is complete, provide a clear continuation into voice assignment for the same scope, with the current saved state shown.
- Voice status must reflect the actual remaining work, including unsaved choices, unusable or missing voices, and any casting plan creation or approval still required. A required step must remain actionable even when there are no voice changes to save.
- After voice work is saved or approved, show the result and the next valid production action for that scope. Failed or partial saves must not appear complete. Neither saving nor approval starts rendering automatically.
- Preserve unrelated Story Audio behavior.

**Constraints:** Use only the assigned repository for implementation and verification; do not call paid or external providers or the canonical production runtime.

OWNER_INPUT_REQUIRED: no

Work only inside this disposable clone. Do not call external or production services, paid providers, or mutate any path outside this clone. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report NEEDS_OWNER if material Owner intent or authority is missing.
