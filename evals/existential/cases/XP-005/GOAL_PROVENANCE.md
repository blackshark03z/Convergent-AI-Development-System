# XP-005 Goal Provenance

Status: reconstructed from pre-implementation Owner constraints and product
safety requirements, not from the reference diff.

## Source evidence

Historical requirements for the phone/task workflow stated that:
- multiple clients may submit independent tasks;
- task ownership must remain attributable to the initiating phone/client;
- transport loss does not change ownership;
- duplicate submissions require idempotency-key handling that distinguishes a
  retry from an intentional duplicate/competing task; and
- partial side effects must be reconciled instead of blindly retried.

The Owner also repeatedly required no blind redispatch, exact
ownership/attribution, fail-closed ambiguity and reconciliation before retry in
adjacent provider-effect workflows.

## Anti-leak rule

The candidate is not told the historical reference patch, exact state-machine
names, internal adapters, or assertion structure. The held-out evaluator must
score externally meaningful reconciliation/idempotency outcomes only.
