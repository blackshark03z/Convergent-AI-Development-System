You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-005 Reasoning Lead Prompt - N1

You are R, the Reasoning Lead. You do not edit product code.

## Frozen Raw Owner Goal

When a phone/client submission may have partially succeeded or transport state
is uncertain, do not blindly submit again.

Keep ownership of the original task/effect attributable to the initiating phone
or client, reconcile the existing submission first, and distinguish a retry of
the same intended task from an intentional new/competing task.

The system must fail closed when it cannot establish enough evidence to decide
whether redispatch would duplicate a consequential effect.

## Fixed intent and constraints

- Live consequential submission is forbidden in this benchmark.
- Use local/provider fixtures only.
- Transport loss must not silently change task ownership.
- Duplicate submissions must respect idempotency/retry semantics.
- Partial side effects are reconciled before any redispatch decision.
- Do not infer success from newest/first/last result, timing, or other guessed attribution.
- The historical implementation and held-out evaluator are hidden.
- Do not inspect sibling benchmark workspaces or results.
- You may inspect the assigned neutral repository, but must not edit product code.

## Common R-to-I rule

Produce the smallest Implementation Brief that makes the outcome testable.
SPEC UNTIL TESTABLE, NOT SPEC UNTIL COMPLETE.
Stop specifying once multiple implementations could satisfy the brief, PASS/FAIL
can be judged from observable outcome, and I need not invent a material product
preference or consequence boundary.

Your brief may use Outcome, Acceptance, Constraints / Non-goals, Effects /
Authority, and material assumptions/open questions only if needed. Do not add
design/architecture/task artifacts unless they solve a concrete ambiguity or risk.

## Arm treatment

Use ordinary product/developer documentation, existing tests and normal engineering conventions available in the neutral repository. Do not create a custom process/framework.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.



IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** A lost response or uncertain transport state leaves the original consequential task attributable to the initiating phone or client. The system reconciles that task before deciding whether any effect can be dispatched again.

**Acceptance:**

- A retry of the same request, including after restart or concurrent delivery, resumes or reports the same durable task and effect lineage. It does not create a second consequential effect.
- Reusing a request identity with a different material intent or target is rejected. A distinct, intentional task has separate lineage; it cannot take over an unresolved task or inherit its partial effects.
- If a submission may have produced a partial effect, reconciliation uses evidence tied to the exact task and remote or provider identity. Confirmed effects are retained and only unfinished steps may proceed.
- An uncertain outcome remains `RECONCILE_REQUIRED` or equivalent until there is positive evidence that redispatch is safe. Result ordering, timing, and absence of a local response are insufficient evidence.
- Local/provider fixture tests cover response loss, restart, duplicate delivery, partial success, and a competing request. No live consequential submission is used.

OWNER_INPUT_REQUIRED: no

I completion report:
**Implemented:** `finish_operation` now treats a repeated request to finish an operation in the same terminal state as idempotent. It returns the existing operation record, allowing duplicate completion after response loss without reactivating the task. A request to change an already terminal operation to a different state still fails.

**Checks:** `python -m pytest tests/test_publishing.py -q` passed: 13 tests.

**Evidence and limits:** The fixture suite covers upload response loss across restart, ambiguous thumbnail outcomes across restart, and reconciliation of an observed existing upload without redispatch. I did not add coverage for stable client request identities or concurrent duplicate delivery. A concurrent fixture attempt exposed an unresolved race while calls reconcile the thumbnail effect; I removed that test rather than claim concurrent delivery is handled. The service currently relies on the persisted operation and package/channel identity, not an explicit client-supplied request ID. No live submission or external provider was used.

Candidate tree: 855d31c710795345c9408ded67deb60971b9e615
Candidate status:
M  multiple_automation/store.py
Candidate diff:
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

Return exactly READY or REPAIR: followed by one bounded repair brief. If no safe repair is possible, return NOT_READY with a reason.
