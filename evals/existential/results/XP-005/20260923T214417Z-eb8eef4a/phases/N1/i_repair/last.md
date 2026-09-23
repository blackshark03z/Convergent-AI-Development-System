I made one scoped change in [raw_cdp.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/N1/multiple_automation/adapters/raw_cdp.py): a single Studio row matching the sealed title now yields `UNCERTAIN`, with evidence explaining that a title match cannot attribute the video to the original task.

Check run: `python -m pytest tests/test_publishing.py -q` — **16 passed**.

The R repair is incomplete. The public `/publish` path still does not require or bind client/task identity, and retries after completion do not return the historical result. The requested public-path fixture cases were not added. I did not use live providers or production runtime. No Product Acceptance is claimed.