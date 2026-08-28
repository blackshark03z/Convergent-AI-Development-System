# Effect Safety

Effect Safety records only facts Git cannot reconstruct about an external call.
It is not a task lifecycle or execution engine.

Identity binds:

- operation;
- target;
- exact request SHA-256.

An optional provider idempotency key and claimed provider semantics are bound
inside the exact intent as assertions. They never justify retry by themselves,
and changing the key cannot create a new semantic effect identity.

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

A retry check is advisory and never dispatches. It reports safe only after an
explicit trusted verifier returns proof bound to the exact semantic identity,
operation, target, request digest and idempotency key where applicable. The
verified proof is sealed by the verifier seam before it can enter durable state.
Raw CLI/API strings and self-declared booleans remain untrusted. With no trusted
verifier the operation fails closed. Changing `effect_id` or idempotency key
cannot bypass the same semantic effect identity.

Provider integrations stay outside the core. They receive the normalized exact
intent and must return either a content-bound `CONFIRMED` result or positive
`NOT_DISPATCHED` evidence. Arbitrary shell text is not an external adapter.

An exact `PREPARED` record has not crossed dispatch. If final Git observation
blocked the first invocation, fixing Git and invoking the exact same intent may
reuse that record and cross the dispatch seam once. Changed intent or any
`DISPATCH_UNCERTAIN` record fails closed through this path.
