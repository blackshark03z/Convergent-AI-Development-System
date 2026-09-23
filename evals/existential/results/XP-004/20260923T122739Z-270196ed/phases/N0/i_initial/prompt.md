# XP-004 Common Implementer Prompt

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

**Outcome:** Product acceptance for the canonical RC4 F1–F5 formats proves that the selected format’s legal sources survive the real plan → timeline → compose → render path, and binds the accepted master to the exact product state and media used.

**Acceptance:**

- Offline, distinguishable fixtures exercise each format through the CLI and Web product paths without hand-built schedules or external providers. Both paths apply the same format rules and report the same acceptance outcome.
- Verification checks the rendered result as well as its plan and timeline: F1 has a generated-video opening and generated-image body; F2 has a generated-video opening plus both stock and generated video afterward; F3 uses generated images throughout; F4 visibly combines the original video inset with an online-stock background; F5 uses online-stock footage throughout. Source class must be supported by the selected asset’s provenance, not merely its label.
- A missing, substituted, ambiguous, or changed required asset; a changed plan or timeline; or a stale or changed output prevents Product Accepted. Failure remains attributed to the selected format unless an explicit, authorized format change creates a newly verified run.
- The final acceptance evidence identifies the selected format, exact input assets and content, relevant product code/configuration state, verified plan/timeline/compose state, and final output content. It can be checked against those states and fails if any bound state changes.

**Constraints:** Use the current RC4 canonical format meanings. Verification must run locally without paid providers or the canonical production runtime. Implementation shape and evidence serialization are open.

OWNER_INPUT_REQUIRED: no

Work only inside this disposable clone. Do not call external or production services, paid providers, or mutate any path outside this clone. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report NEEDS_OWNER if material Owner intent or authority is missing.
