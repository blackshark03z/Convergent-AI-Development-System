IMPLEMENTATION_BRIEF

**Outcome:** A consequential submission remains attributable to the initiating phone or client when its response is lost. A retry of the same intended task resumes or reconciles that task; an intentional new task is treated separately and cannot silently take over an unresolved one.

**Acceptance:**
- Before dispatch, durably bind the initiating client, stable task identity, exact intent and target, and owning operation and effects. This binding survives disconnects and restarts.
- Repeated or concurrent submissions of the same task and intent return or resume the same operation without duplicate dispatch. Reusing that task identity with changed intent is rejected. A distinct task identity represents a new request, subject to any unresolved competing effect.
- After uncertain transport or partial success, reconcile each existing effect using evidence tied to that exact submission. Preserve confirmed partial effects and resume only unfinished work. Never attribute a result by list order, recency, or timing.
- Redispatch only with positive evidence that the prior effect did not occur, or with provider-backed idempotency for the same task. If evidence is insufficient, expose `RECONCILE_REQUIRED` and perform no consequential dispatch. Another client cannot adopt or overwrite the original task’s ownership.
- Demonstrate these outcomes with local/provider fixtures covering lost responses, duplicate and concurrent retries, partial success, competing tasks, and ambiguous evidence. No live consequential submission.

OWNER_INPUT_REQUIRED: no