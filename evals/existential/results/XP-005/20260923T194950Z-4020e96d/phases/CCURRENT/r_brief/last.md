IMPLEMENTATION_BRIEF

**Outcome:** A repeated client request remains tied to the initiating client, its original task, and its exact intended effect. An uncertain transport result triggers reconciliation before any consequential redispatch. Use the repository’s existing operation and effect lineage where possible.

**Acceptance:**

- A fixture simulates a submission that creates a partial provider or remote effect, then loses its response. A retry with the same client and request identity resumes or reports the original task; it does not create a second task or repeat the unresolved effect. This remains true after restart and for concurrent duplicate requests.
- Reconciliation attributes outcomes using exact persisted request, effect, and remote identities. Fixtures with multiple plausible results in different orders cannot cause a result to be assigned by recency, position, or timing. Confirmed partial effects are retained, and only unfinished steps may proceed.
- Redispatch occurs only with evidence that the prior effect did not happen or with a proven idempotent retry of that same effect. If evidence is insufficient, the task stays visibly unresolved and no consequential dispatch occurs.
- Reusing a request identity with changed intent, or from another client, cannot take ownership of the original task. An explicitly new task receives separate lineage; if it competes with an unresolved effect, it cannot dispatch until the conflict is resolved. A delayed retry of a completed task returns that task’s result.
- Representative evidence exercises the product submission path with local/provider fixtures and shows persisted ownership, reconciliation decisions, and dispatch counts. No live consequential submission.

OWNER_INPUT_REQUIRED: no