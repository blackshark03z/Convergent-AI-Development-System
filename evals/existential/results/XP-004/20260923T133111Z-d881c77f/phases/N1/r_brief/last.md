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