Implemented part of the repair, but **the Product Acceptance path is not complete**.

- F4 rendering now combines the original video inset and online-stock background into one segment, so both can appear in the same frame.
- CLI and Web format selections use a shared resolver; unsupported formats now fail instead of silently defaulting to F2.
- Added an offline fixture command and [usage guide](</C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N1/docs/OFFLINE_PRODUCT_ACCEPTANCE.md>).

**Checks run:** `compileall` passed; the timeline-builder and Web tests passed (8); `git diff --check` passed. I did not run the offline command: it intentionally exits on this dirty working tree, and I did not commit the candidate to satisfy that gate.

**Remaining limits:** The command’s self-test does not yet demonstrate rejection of all requested mutations (wrong-source render, stale master, mismatched lineage, and dirty tree). It does not establish complete acceptance binding for effective configuration, verified source semantics across every format, or an exact verified master. The render integration also lacks a demonstrated end-to-end run through equivalent CLI and Web selections. No Product Acceptance is claimed.

Files changed include the F4 renderer, shared format resolver, CLI/Web format handling, offline verification script, and guide.