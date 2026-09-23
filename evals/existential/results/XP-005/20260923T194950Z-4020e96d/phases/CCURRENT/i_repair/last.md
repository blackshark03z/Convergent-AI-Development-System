Implemented a partial repair candidate.

- Added durable `client_id`/`request_id` ownership in [store.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CCURRENT/multiple_automation/store.py). Reusing a request ID from another client raises an identity conflict; changed intent is also rejected.
- Added request identity parameters to the publish API and controller. A delayed retry of a completed task returns its original operation and result.
- Made effect preparation reuse existing lineage for the same operation, effect type, and target.
- Added a fixture test covering successful submission, reopening the store, delayed retry, and rejection of a different client.

Checks run: `python -m pytest tests/test_publishing.py -q` passed (14 tests); `git diff --check` passed.

The fixture observed one upload dispatch across the restart and retry, and the original operation remained associated with the request. No live submission or external provider was used.

Remaining gaps: the browser UI does not yet create and resend a stable request ID; separate tasks competing for an unresolved effect are not blocked by workspace-wide lineage; and fixtures do not cover partial remote effects, ambiguous reordered observations, concurrent product submissions, or competing intent. Exact remote attribution under those cases remains unverified. This is not a complete implementation of the repair brief, and I make no Product Acceptance claim.