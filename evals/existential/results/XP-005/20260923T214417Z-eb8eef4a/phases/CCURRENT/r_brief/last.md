IMPLEMENTATION_BRIEF

**Outcome:** A consequential submission remains owned by the initiating phone or client and its original intended task when the response is lost or partial effects may have occurred. Recovery reconciles that submission before deciding whether any further dispatch is safe.

**Acceptance:**

- Persist the initiating client, stable task intent, owning operation, and effect lineage before dispatch. A retry of the same intended task resumes that lineage and cannot create a duplicate consequential effect.
- A changed intent presented as the same retry is rejected. An intentional new or competing task has distinct identity and cannot take over or bypass an unresolved submission.
- Reconcile each possibly completed side effect using evidence tied to the exact task and target. Do not attribute an unrelated result by recency or ordering. If evidence cannot establish the outcome or prove a retry safe, retain a visible unresolved state and do not redispatch.
- Demonstrate these outcomes through the product submission path with local/provider fixtures covering lost responses, partial success, restart, duplicate and competing submissions, and unrelated or reordered provider results. Bind the evidence to the candidate revision. No live consequential submission.

OWNER_INPUT_REQUIRED: no