IMPLEMENTATION_BRIEF

**Outcome:** Acceptance of a rendered master proves the selected canonical F1–F5 format, the media actually used, and the exact product state that produced it. CLI and Web apply the same format semantics.

**Acceptance:**

- Exercise each format through the real plan → timeline → compose → render path with local representative media. Verify the resulting output and asset lineage: F1 generated-video opening plus generated-image body; F2 generated-video opening plus intentional post-opening online stock and generated video; F3 generated images throughout; F4 readable original-video inset over visible online-stock background; F5 online-stock footage throughout. Use the current RC4 F1–F5 meanings.
- Acceptance independently checks the selected format against the actual timeline, source identities and classes, composed media, and rendered output. Metadata or a validator’s self-reported pass alone is insufficient.
- The accepted result identifies the exact candidate source state, resolved format and product settings, selected asset contents, plan/timeline/compose state, and output contents. Changing any material input, reusing a stale render, or presenting evidence from another candidate invalidates acceptance.
- CLI and Web selections produce the same canonical format decision and failure behavior. Missing, invalid, or unverifiable required media stops acceptance with a clear disposition; it never becomes a placeholder, black filler, another source class, or another format silently.

**Constraints / evidence:** Use local fixtures and local rendering only; do not call paid or external providers or the canonical production runtime. Provide candidate-bound, reproducible product-level evidence for all five positive paths and representative missing-media, illegal-source, and stale-lineage failures.

OWNER_INPUT_REQUIRED: no