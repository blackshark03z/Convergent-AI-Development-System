Implemented the repair in [online_stock.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/N1/videopipeline/stages/stage2_assets/online_stock.py) and added fake-provider coverage in [test_stock_proposals.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/N1/tests/test_stock_proposals.py).

Shot-specific required visuals now lead the five-term provider query, even when shots share a subject and action. A provider exception produces an explicit `SEARCH_FAILED` proposal row for that shot, and later shots are still processed. Results remain proposal-only, with the shortlist capped at five.

**Checks run:** `python -m pytest tests/test_stock_proposals.py tests/test_stock_constraints.py -q` — **9 passed**.

The fake provider confirmed distinct queries and matching rain/snow shortlists, plus row-local failure handling. No external provider or production runtime was used. Provider exceptions are reported as search failures; exception handling for other failures outside the provider search call was not expanded.