IMPLEMENTATION_BRIEF

**Outcome:** A lost response or uncertain transport state leaves the original consequential task attributable to the initiating phone or client. The system reconciles that task before deciding whether any effect can be dispatched again.

**Acceptance:**

- A retry of the same request, including after restart or concurrent delivery, resumes or reports the same durable task and effect lineage. It does not create a second consequential effect.
- Reusing a request identity with a different material intent or target is rejected. A distinct, intentional task has separate lineage; it cannot take over an unresolved task or inherit its partial effects.
- If a submission may have produced a partial effect, reconciliation uses evidence tied to the exact task and remote or provider identity. Confirmed effects are retained and only unfinished steps may proceed.
- An uncertain outcome remains `RECONCILE_REQUIRED` or equivalent until there is positive evidence that redispatch is safe. Result ordering, timing, and absence of a local response are insufficient evidence.
- Local/provider fixture tests cover response loss, restart, duplicate delivery, partial success, and a competing request. No live consequential submission is used.

OWNER_INPUT_REQUIRED: no