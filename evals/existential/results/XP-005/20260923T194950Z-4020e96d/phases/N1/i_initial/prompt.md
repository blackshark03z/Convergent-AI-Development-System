# XP-005 Common Implementer Prompt

You are the implementation role (I) for a controlled benchmark. You receive a
disposable neutral Multiple Automation snapshot and an Implementation Brief from
R. Implement the brief using the cheapest coherent technical path you judge
appropriate.

Rules:
- inspect the assigned repository as needed and own implementation details;
- keep changes scoped to the brief and run relevant deterministic local checks;
- never call live consequential submission, paid/external providers or production runtime;
- use only local/provider fixtures for effects;
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

**Outcome:** A lost response or uncertain transport state leaves the original consequential task attributable to the initiating phone or client. The system reconciles that task before deciding whether any effect can be dispatched again.

**Acceptance:**

- A retry of the same request, including after restart or concurrent delivery, resumes or reports the same durable task and effect lineage. It does not create a second consequential effect.
- Reusing a request identity with a different material intent or target is rejected. A distinct, intentional task has separate lineage; it cannot take over an unresolved task or inherit its partial effects.
- If a submission may have produced a partial effect, reconciliation uses evidence tied to the exact task and remote or provider identity. Confirmed effects are retained and only unfinished steps may proceed.
- An uncertain outcome remains `RECONCILE_REQUIRED` or equivalent until there is positive evidence that redispatch is safe. Result ordering, timing, and absence of a local response are insufficient evidence.
- Local/provider fixture tests cover response loss, restart, duplicate delivery, partial success, and a competing request. No live consequential submission is used.

OWNER_INPUT_REQUIRED: no

Work only inside this disposable clone. Do not call external or production services, paid providers, or mutate any path outside this clone. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report NEEDS_OWNER if material Owner intent or authority is missing.
