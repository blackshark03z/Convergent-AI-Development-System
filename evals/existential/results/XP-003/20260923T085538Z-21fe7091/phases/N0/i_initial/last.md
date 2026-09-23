Implemented the selected scope’s speaker-to-voice continuation in [ui/app.js](/D:/CADS-Benchmark/XP-003-AUTO-V2/arms/N0/ui/app.js:1613).

Voice status now shows unsaved choices, unusable voices, missing voices, and when a Casting Plan still needs creation or approval. If voices are already saved and usable but the plan step remains, **Mở bước Casting Plan** opens that action without requiring a save. Missing voices remain visible while the existing production readiness flow decides whether work can continue.

**Checks:** `node --check ui/app.js` passed; 55 focused UI tests passed; the assignment workflow browser smoke test passed after I adjusted the readiness display to preserve its existing fallback behavior. That browser test reported that saving voice configuration unlocked preflight.

Only `ui/app.js` changed. I did not verify every partial-save or approval scenario in a browser, and this candidate is not Product Acceptance.