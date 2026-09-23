IMPLEMENTATION_BRIEF

**Outcome:** An uncertain phone/client submission remains tied to its original initiating client, task, and consequential effect. Reconcile that submission before deciding whether any dispatch may occur.

**Acceptance:**

- A retry of the same intended task resolves to the original task and effect, including after transport loss or restart. It does not create a second consequential effect or transfer ownership to another client.
- A submission with changed intent under the same retry identity is rejected. An explicitly new task receives separate identity, but cannot dispatch a competing effect while the original effect is unresolved.
- Reconciliation uses evidence attributable to the exact submission. Confirmed partial effects are retained and only unfinished work may proceed. If absence or idempotent retry is positively established, redispatch may follow the existing policy. If attribution or outcome remains uncertain, the system reports reconciliation required and dispatches nothing.
- Local/provider fixture tests cover lost response after dispatch, partial success, repeated retry, changed intent, competing new task, and ambiguous results. No test uses newest/first/last result or timing as proof of attribution.

**Effects / Authority:** Implementation and fixture testing are authorized. Live consequential submission is forbidden.

OWNER_INPUT_REQUIRED: no