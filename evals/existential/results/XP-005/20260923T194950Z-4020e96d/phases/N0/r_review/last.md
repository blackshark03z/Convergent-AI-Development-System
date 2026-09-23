REPAIR: The publish path does not yet meet the handoff brief.

- Enforce one immutable client/task binding per active publish operation. A second task can currently bind before the first effect is prepared and overwrite the operation intent. Same-task retries must retain the original operation; competing tasks must wait for reconciliation.
- Make retries work after success. Once the operation is terminal, a lost-response retry currently fails during review instead of returning the original task’s recorded outcome.
- Require evidence tied to the exact submission before marking an upload successful or changing its thumbnail. The current adapter treats a single private video with the same title as a match, which can attribute an unrelated upload to this task. Ambiguous evidence must yield `RECONCILE_REQUIRED` without consequential dispatch.

Verify these cases with local fixtures, including concurrent submissions.