Implemented client/task identity for publish intake in four files:

- [store.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/N1/multiple_automation/store.py): persists each `(workspace, client, task)` mapping. Identical retries return the same operation; reusing the key with a different kind or intent raises `IdentityConflictError`.
- [control_center.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/N1/multiple_automation/control_center.py) and [app.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/N1/multiple_automation/app.py): pass optional `client_id` and `task_id` through content intake.
- [test_publishing.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T214417Z-eb8eef4a/arms/N1/tests/test_publishing.py): adds fixture coverage for restart retries, changed intent, competing tasks during unresolved effects, and response loss after an upload effect.

The existing publish service records dispatch lineage before dispatch and reconciles observations before any retry. The new tests observed that a partial upload was attributed to the original effect after restart, with one upload dispatch; a distinct task was blocked while that effect remained unresolved.

Check run: `python -m pytest tests/test_publishing.py -q` — **16 passed**.

Limitations: client/task keys are optional for compatibility, so callers that omit them do not get request-level deduplication. The identity is bound to the intake intent, including package path; target channel and sealed-package digest are checked later by the existing publish review flow. No live submission or provider was used. I’m reporting this as an implementation candidate, not Product Acceptance.