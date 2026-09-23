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

**Outcome:** Make Product Acceptance prove that the selected canonical RC4 format—F1, F2, F3, F4, or F5—governed the actual plan, timeline, composition, and rendered master, and that the accepted master came from the exact verified source and product state.

**Acceptance:**

- An offline, predeclared fixture for each format enters through the normal product path and produces a master. Verification checks the rendered visuals against identifiable source assets, including F1’s generated-video opening and generated-image body; F2’s opening plus intentional post-opening online stock and generated video; F3’s generated images throughout; F4’s readable original-video inset over a visible online-stock background; and F5’s online-stock footage throughout. Labels, manually assembled schedules, and stream metadata alone cannot establish a pass.
- CLI and Web resolve equivalent selections to the same format rules and output-affecting product state. The selected format, source classes, asset identities and ranges survive every plan, timeline, compose, render, and verification boundary.
- Missing media, unverified source identity, illegal source classes, stale artifacts, and failed required-source acquisition prevent acceptance. They cannot become placeholders, a different source class, or a different format silently. An intentional format change has a new identity and requires fresh affected verification.
- Acceptance evidence binds a clean, exact Git revision; effective configuration and input identities; format, creative plan, editorial timeline, and compose identities; selected asset/provider lineage; verification results; and the final file hash. Empty or mismatched identities, a dirty source tree, or a reused master whose identity cannot be proven are ineligible. The final file must pass required stream, duration, and full-decode checks.
- The repository provides one documented offline verification command whose pass/fail result exercises these paths and rejects representative format, source, and lineage mutations.

**Constraints:** Use RC4’s F1–F5 meanings where older format documentation conflicts. Keep verification isolated from paid providers and the canonical production runtime. Implementation shape is open.

OWNER_INPUT_REQUIRED: no

Work only inside this disposable clone. Do not call external or production services, paid providers, or mutate any path outside this clone. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report NEEDS_OWNER if material Owner intent or authority is missing.
