Implemented a provisional F5 stock proposal table. The compiler searches each scheduled F5 segment using its overlapping SRT narration and visual description, filters ineligible or poor-fit footage, and marks segments unresolved when no candidate fits. Results include preview links, candidate identity, and a concise fit reason. Compiling the table does not write to the timeline.

The studio requires an existing F5 schedule. The proposal endpoint reads that schedule and rejects schedules for other formats.

**Files changed:** [stock_proposals.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/N0/videopipeline/stages/stage2_assets/stock_proposals.py:20), [server.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/N0/videopipeline/web/server.py:1356), [index.html](/D:/CADS-Benchmark/XP-002-AUTO/arms/N0/videopipeline/web/static/index.html:324), [app.js](/D:/CADS-Benchmark/XP-002-AUTO/arms/N0/videopipeline/web/static/js/app.js:844), and [test_stock_proposals.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/N0/tests/test_stock_proposals.py:23).

**Checks:** The fake-provider proposal test passed; stock constraint and shot-coverage tests also passed (10 total). Python compilation and `git diff --check` passed. No external provider or production runtime was called.

The tests cover per-shot searches, bounded results, mismatch and eligibility filtering, unresolved shots, and the provisional boundary. I did not exercise the live UI or endpoint against an actual schedule, and I do not claim Product Acceptance.