IMPLEMENTATION_BRIEF

**Outcome:** A phone or client can recover an uncertain consequential submission under its original task identity. The system reconciles effects already attempted before deciding whether any dispatch is safe.

**Acceptance:**

- A submission has a stable identity bound to its initiating client, target, and intended task. A retry of that task returns or resumes its existing operation and effects, including after transport loss or restart; it does not create another dispatch.
- Reusing that identity with materially different intent is rejected. An explicitly new task remains distinct from the original. If it could compete with an unresolved effect, it cannot dispatch until that effect is reconciled.
- Recovery checks each possible partial effect against evidence attributable to the original task. Confirmed effects are recorded and not repeated. Redispatch occurs only with positive evidence of no effect or a proven idempotent retry path.
- Ambiguous, missing, or conflicting attribution leaves the task in a visible recovery state and blocks consequential redispatch. A result is never assigned by list position, recency, or timing.
- Fixture tests cover response loss before and after a partial effect, duplicate retries, changed intent, a competing new task, and ambiguous reconciliation. They assert task ownership, effect lineage, and dispatch counts.

**Constraints:** Use local/provider fixtures only. No live consequential submission.

OWNER_INPUT_REQUIRED: no