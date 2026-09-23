IMPLEMENTATION_BRIEF

**Outcome:** A consequential submission remains attributable to the initiating client and its intended task when the response is lost or a side effect is only partly confirmed. A retry of that same task resumes its original operation; an intentional new task has distinct lineage.

**Acceptance:**
- With local fixtures, lose the response after a paid phone acquisition or publish dispatch. Retrying the same client intent, including after restart, returns or reconciles the original operation and effect without a second consequential dispatch.
- A repeated intent with changed payload, or a competing client intent for the same unresolved target, cannot take over the original operation or dispatch. An explicitly new task receives new lineage only when the prior effect has been reconciled and the new action is authorized.
- Reconciliation uses evidence tied to the exact operation, target, and effect. If evidence cannot establish whether the prior dispatch took effect, the result remains unresolved and redispatch is blocked. Result order or timing alone never establishes attribution.
- The client can observe which operation owns the submission, its current outcome, and the safe next action.

**Constraints:** Use local/provider fixtures only. Do not perform live consequential submissions or external effects.

OWNER_INPUT_REQUIRED: no