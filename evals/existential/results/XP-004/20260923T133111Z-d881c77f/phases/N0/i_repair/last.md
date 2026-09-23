Implemented a **partial repair** in this disposable clone.

- Compose writes source hashes and producer-location evidence; render checks that evidence against the current schedule and media. Format-plan identity is also checked.
- Cached segments are regenerated when source bytes or edit parameters change. Render manifests record output, timeline, plan, and provenance hashes.
- F4 rendering now combines the original video inset with the stock background for matching timeline intervals.
- Web runs no longer treat an existing master file as a completed render.
- The F4 schedule fixture now uses valid local videos generated with ffmpeg.

Checks run: `python -m compileall -q videopipeline` passed. The focused pytest selection passed: **37 tests**.

**The repair brief is not fully met.** I did not run successful end-to-end CLI and Web acceptance cases for F1–F5, verify rendered content by inspecting output frames, or demonstrate the requested negative lineage and output mutations. Producer-location evidence is also limited to recognized asset directories; other source layouts may be rejected. This is a candidate for review, not Product Acceptance.