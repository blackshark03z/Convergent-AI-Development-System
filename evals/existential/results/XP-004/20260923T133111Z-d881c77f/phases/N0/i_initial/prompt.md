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

**Outcome:** Acceptance for each canonical F1–F5 format proves that the selected format and actual source assets pass through the product’s plan, timeline, compose, and render path, and binds the accepted output to the product state that produced it.

**Acceptance:**

- Exercise each format through the real CLI and Web product paths with local media and no external providers. Verify the rendered result against the selected format’s source semantics: F1 generated video opening and generated image body; F2 generated opening plus stock and generated video after the opening; F3 generated images only; F4 original video inset with stock background; F5 stock footage only. Check media used by the render, not just segment labels or validator return values.
- CLI and Web must resolve the same canonical format truth. An unknown format, missing required asset, unverifiable source class, or format mismatch between compose and render must produce an explicit non-accepted result. Neither path may silently select F2, invent a placeholder, or substitute another source class.
- A successful acceptance record identifies the selected format, the source assets actually used, the verified product state, and the output’s content identity. Its lineage must connect the plan, timeline, compose decision, render, and verification for that same run. Changed inputs, product state, or a reused stale output cannot retain the prior acceptance.
- Demonstrate rejection with negative cases that change a required source class, remove required media, or break lineage after verification. A record whose claims are internally consistent but disagree with the rendered media must fail.

**Constraints:** Use disposable local fixtures and local rendering or equivalent product-path evidence. Do not call paid or external providers or the canonical production runtime. Judge observable behavior; the storage format and implementation structure are open.

OWNER_INPUT_REQUIRED: no

Work only inside this disposable clone. Do not call external or production services, paid providers, or mutate any path outside this clone. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report NEEDS_OWNER if material Owner intent or authority is missing.
