Implemented the repair in [online_stock.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/CMIN/videopipeline/stages/stage2_assets/online_stock.py) and updated [test_stock_shot_proposals.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/CMIN/tests/test_stock_shot_proposals.py).

Shot proposal queries now prioritize the shot’s structured visual direction within the bounded query, so shots with the same long script can search differently. Forbidden visuals are checked across title, description, tags, and alt metadata. Each candidate’s fit reason names matching terms from its metadata when available. Proposals remain capped at two alternatives in the existing API and proposal-only flow.

The offline fixture confirms distinct directions produce distinct queries and candidates, a forbidden visual in tags is excluded, and reasons include shot-specific matching terms.

**Checks run:** `python -m pytest tests/test_stock_shot_proposals.py -q` passed (1 test); Python compilation passed; `git diff --check` passed.

**Limits:** Forbidden-term filtering can only inspect metadata supplied by the provider. No external provider or production runtime was called. No Product Acceptance is claimed.