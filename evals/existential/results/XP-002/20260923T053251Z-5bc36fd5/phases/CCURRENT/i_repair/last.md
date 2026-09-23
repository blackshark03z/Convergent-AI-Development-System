Implemented the F5 proposal repair in the disposable clone.

- The proposal endpoint now combines cached `chapter1_shots` and `body_scenes`, preserves their shot identities, derives opening intervals from `time_range`, sorts rows by start time, and attaches overlapping SRT narration without modifying the cached plan.
- The review table now displays each proposal’s fit reason.
- Extended the offline fixture and candidate evidence to cover an endpoint request with an opening shot, a suitable proposal, conflicting and ineligible candidates, a `NO_MATCH` shot, and the fit-reason display path.

**Checks:** `python -m pytest tests/test_stock_proposals.py -q` passed (2 tests); Python compilation, `node --check`, and `git diff --check` passed. Git reported line-ending conversion warnings; `git diff --check` found no whitespace errors.

The tests observed a 0–6 second opening row with matching narration, distinct proposals and conflicts in the response, and the archive shot remaining `NO_MATCH`. The UI check verifies that the row template displays `fit_reason`; it does not run a browser. No external provider, downloads, approvals, schedule changes, or production runtime were used. Live provider behavior and browser rendering remain untested.