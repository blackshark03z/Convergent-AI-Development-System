# v1.25 legacy boundary

The v1.25 Work Loop, lifecycle store, telemetry, governor, grounding, assurance,
adoption/bootstrap and context-epoch machinery are not part of the simplified
production path. The public CLI does not import or advance them.

Source remains temporarily in the repository as historical implementation
evidence. Active tests for behavior owned solely by that removed architecture
are retired from the stabilization suite rather than forcing the new kernel to
preserve obsolete semantics.

One exception remains safety-relevant: read-only `inspect` checks legacy
`.buildos/control/CURRENT` for unresolved external-effect ledger entries. Closed
task state is historical. Unresolved provider reality is reported because it
may require reconciliation. `reconcile --legacy-effect-id` carries only the
exact request/contract identity into Effect Safety and leaves the legacy bytes
read-only; no task/project migration or commit adoption is performed.

The v1.26 executor-lifecycle candidate is frozen experimental evidence. It is
not an upgrade predecessor, release authority or source for simplification.
