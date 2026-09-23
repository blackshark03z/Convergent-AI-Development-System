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

**Outcome:** Acceptance of a rendered master proves the selected canonical F1–F5 format, the media actually used, and the exact product state that produced it. CLI and Web apply the same format semantics.

**Acceptance:**

- Exercise each format through the real plan → timeline → compose → render path with local representative media. Verify the resulting output and asset lineage: F1 generated-video opening plus generated-image body; F2 generated-video opening plus intentional post-opening online stock and generated video; F3 generated images throughout; F4 readable original-video inset over visible online-stock background; F5 online-stock footage throughout. Use the current RC4 F1–F5 meanings.
- Acceptance independently checks the selected format against the actual timeline, source identities and classes, composed media, and rendered output. Metadata or a validator’s self-reported pass alone is insufficient.
- The accepted result identifies the exact candidate source state, resolved format and product settings, selected asset contents, plan/timeline/compose state, and output contents. Changing any material input, reusing a stale render, or presenting evidence from another candidate invalidates acceptance.
- CLI and Web selections produce the same canonical format decision and failure behavior. Missing, invalid, or unverifiable required media stops acceptance with a clear disposition; it never becomes a placeholder, black filler, another source class, or another format silently.

**Constraints / evidence:** Use local fixtures and local rendering only; do not call paid or external providers or the canonical production runtime. Provide candidate-bound, reproducible product-level evidence for all five positive paths and representative missing-media, illegal-source, and stale-lineage failures.

OWNER_INPUT_REQUIRED: no

Work only inside this disposable clone. Do not call external or production services, paid providers, or mutate any path outside this clone. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report NEEDS_OWNER if material Owner intent or authority is missing.
