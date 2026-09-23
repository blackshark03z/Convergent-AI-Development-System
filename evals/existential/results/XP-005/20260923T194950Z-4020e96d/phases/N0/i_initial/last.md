Implemented durable submission ownership and retry binding.

- [store.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/N0/multiple_automation/store.py) persists each task’s initiating client, immutable intent digest, target, and operation. Repeated effect preparation reuses the same effect record.
- [control_center.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/N0/multiple_automation/control_center.py) binds the approved submission before browser access.
- [app.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/N0/multiple_automation/app.py) keeps client and task IDs in browser local storage and sends them with publish requests.
- [test_publishing.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/N0/tests/test_publishing.py) covers durable retries, changed intent, client ownership, and blocking a distinct task while an effect is unresolved.

Checks: 37 targeted tests passed; `compileall` passed; `git diff --check` passed. Existing fixture behavior records uncertain outcomes as `RECONCILE_REQUIRED` and avoids redispatch without confirming evidence.

Limitations: client identity is a browser-generated ID, not an authenticated identity. The new tests cover binding and effect persistence; they do not exercise simultaneous HTTP requests end to end. No live provider or production submission was used.