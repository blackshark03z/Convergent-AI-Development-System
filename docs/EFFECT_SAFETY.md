# Effect Safety

Effect Safety records only facts Git cannot reconstruct about an external call.
It is not a task lifecycle or execution engine.

Identity binds:

- operation;
- target;
- exact request SHA-256.

An optional provider idempotency key is bound inside the exact intent and may
justify retry, but changing the key cannot create a new semantic effect identity.

The durable states are:

- `PREPARED`: exact intent exists and dispatch was not crossed;
- `NOT_DISPATCHED`: the integration positively proved it stopped before transport;
- `DISPATCH_UNCERTAIN`: the boundary may have been crossed and outcome is unknown;
- `CONFIRMED`: provider evidence proves the effect occurred;
- `NO_EFFECT_CONFIRMED`: canonical reconciliation proves it did not occur.

The boundary sequence is:

```text
live Thin Guard
-> durable PREPARED intent
-> final Git re-observation
-> durable DISPATCH_UNCERTAIN marker
-> one explicit provider callable
-> CONFIRMED / NOT_DISPATCHED, or uncertainty remains
```

An exception, invalid response or process interruption after the uncertainty
marker never becomes inferred no-dispatch. Reload reads the same record from
the common Git administration directory.

A retry check is advisory and never dispatches. It reports safe only for exact
provider-enforced idempotency evidence or positive canonical no-effect proof.
Changing `effect_id` cannot bypass the same semantic effect identity.

Provider integrations stay outside the core. They receive the normalized exact
intent and must return either a content-bound `CONFIRMED` result or positive
`NOT_DISPATCHED` evidence. Arbitrary shell text is not an external adapter.
