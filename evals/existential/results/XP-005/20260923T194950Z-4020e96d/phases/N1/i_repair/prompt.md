# XP-005 Common Implementer Prompt

You are the implementation role (I) for a controlled benchmark. You receive a
disposable neutral Multiple Automation snapshot and an Implementation Brief from
R. Implement the brief using the cheapest coherent technical path you judge
appropriate.

Rules:
- inspect the assigned repository as needed and own implementation details;
- keep changes scoped to the brief and run relevant deterministic local checks;
- never call live consequential submission, paid/external providers or production runtime;
- use only local/provider fixtures for effects;
- do not search for historical/reference implementations, sibling workspaces,
  results or hidden benchmark tests;
- do not weaken tests/acceptance surfaces to make the candidate pass;
- do not cross external or irreversible effect boundaries absent from the brief;
- decide ordinary implementation choices yourself; report a genuinely missing
  material product preference or authority decision rather than inventing it.

When finished, report exact files/behavior changed, checks actually run and
their results, product-level evidence observed, known limitations/untested
surfaces, and material assumptions. Do not claim Product Acceptance. Your output
is a candidate for R review and later hidden evaluation.



Original IMPLEMENTATION_BRIEF:
IMPLEMENTATION_BRIEF

**Outcome:** A lost response or uncertain transport state leaves the original consequential task attributable to the initiating phone or client. The system reconciles that task before deciding whether any effect can be dispatched again.

**Acceptance:**

- A retry of the same request, including after restart or concurrent delivery, resumes or reports the same durable task and effect lineage. It does not create a second consequential effect.
- Reusing a request identity with a different material intent or target is rejected. A distinct, intentional task has separate lineage; it cannot take over an unresolved task or inherit its partial effects.
- If a submission may have produced a partial effect, reconciliation uses evidence tied to the exact task and remote or provider identity. Confirmed effects are retained and only unfinished steps may proceed.
- An uncertain outcome remains `RECONCILE_REQUIRED` or equivalent until there is positive evidence that redispatch is safe. Result ordering, timing, and absence of a local response are insufficient evidence.
- Local/provider fixture tests cover response loss, restart, duplicate delivery, partial success, and a competing request. No live consequential submission is used.

OWNER_INPUT_REQUIRED: no

Your previous completion report:
**Implemented:** `finish_operation` now treats a repeated request to finish an operation in the same terminal state as idempotent. It returns the existing operation record, allowing duplicate completion after response loss without reactivating the task. A request to change an already terminal operation to a different state still fails.

**Checks:** `python -m pytest tests/test_publishing.py -q` passed: 13 tests.

**Evidence and limits:** The fixture suite covers upload response loss across restart, ambiguous thumbnail outcomes across restart, and reconciliation of an observed existing upload without redispatch. I did not add coverage for stable client request identities or concurrent duplicate delivery. A concurrent fixture attempt exposed an unresolved race while calls reconcile the thumbnail effect; I removed that test rather than claim concurrent delivery is handled. The service currently relies on the persisted operation and package/channel identity, not an explicit client-supplied request ID. No live submission or external provider was used.

Current candidate tree: 855d31c710795345c9408ded67deb60971b9e615
Current diff:
diff --git a/multiple_automation/store.py b/multiple_automation/store.py
index e0df09f..b7def20 100644
--- a/multiple_automation/store.py
+++ b/multiple_automation/store.py
@@ -1115,6 +1115,8 @@ class SQLiteProductStore:
         with self._transaction() as db:
             operation = self._require_row(db, "operations", "operation_id", operation_id)
             if operation["terminal_at"] is not None:
+                if operation["state"] == target:
+                    return self._operation_from_row(operation)
                 raise InvalidTransitionError("terminal Operation is historical and cannot reactivate")
             active = db.execute(
                 "SELECT workspace_id FROM workspace_active_operations WHERE operation_id=?",

R repair brief:
REPAIR: The terminal-state change does not satisfy the handoff. At the consequential submission entry point, persist an initiating client’s stable request identity with its material intent and owning operation. Repeated delivery, including after restart and concurrently, must return or resume that lineage without a second dispatch; reuse of the identity for different intent or target must fail. A distinct request must not take over unresolved effects.

Reconcile partial or uncertain effects using evidence attributable to that exact operation and remote identity. Title matches, result order, timing, or a missing response cannot establish success or justify redispatch; leave the effect `RECONCILE_REQUIRED` when attribution is insufficient. Add local fixture tests for response loss, restart, concurrent duplicates, partial success, and a competing request. No live submission.

This is the sole repair. Work only in this disposable clone. No external or production effects. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report checks actually run and remaining limits.
