Implemented the F5 proposal review slice.

- Added a proposal compiler that creates a ranked shortlist for every cached body scene. It uses shot-specific visuals and action before narration, filters ineligible candidates, flags weak or contradictory matches, and preserves `NO_MATCH` rows.
- Added an F5-only review table with scene/shot IDs, narration intervals, visual purpose, source IDs, preview links, fit notes, and conflicts. It is explicitly labeled as proposals requiring Owner review.
- Added a read-only API that uses the cached shot plan and overlapping SRT cues. It does not approve or download clips or modify the production schedule.
- Added an offline fixture and evidence record at [f5-stock-proposal-offline-review.json](/D:/CADS-Benchmark/XP-002-AUTO/arms/CCURRENT/docs/evidence/f5-stock-proposal-offline-review.json).

The fixture shows distinct leads for the cycling and courtroom shots, exposes a conflicting celebration clip and a rights-unknown clip, and leaves the archive shot as `NO_MATCH`.

Checks run: focused pytest checks passed (4 tests); Python compilation, JavaScript syntax validation, and `git diff --check` passed. No external provider or production runtime was called.

Limitations: preview links and product rendering were not exercised against a live provider or browser. Candidate quality depends on the cached shot plan and available provider metadata. This is an implementation candidate for review; Product Acceptance is not claimed.