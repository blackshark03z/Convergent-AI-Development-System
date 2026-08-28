# Lifecycle lineage and existing-change adoption

Build OS v1.23 adds public lifecycle semantics for source defects and durable
continuation, plus one narrowly administrative path for pre-existing Git
changes. These primitives are generic and do not encode a project, provider,
runtime, or Goal numbering scheme.

## Source defect release

`block-for-source-fix` is valid from any live phase: `ACTIVE`,
`PRODUCT_COMMITTED`, or `ASSURANCE_READY`.
It records the reason and defect reference, changes the phase to
`BLOCKED_SOURCE_FIX`, and changes the lease from `CLAIMED` to `RELEASED`.
It does not modify product code, call a provider, or classify the task as a
successful close.

The repair is a separate task with a fresh task ID. After repair, a normal
Worker uses `continue-task` to create another fresh task whose immutable
lineage names the exact source task, revision, phase, generation/hash, reason,
and resolution reference. A blocked-source continuation requires that
resolution reference. Build OS never reopens or mutates the historical source
task.

## Existing clean changes

`adopt-existing-change` is admin-only because it changes the lifecycle from a
Git commit that Build OS did not supervise. It accepts only a clean current
HEAD, an explicit base, a fresh task ID, normal scope/risk/authorization, and a
reason. The product commit is marked `EXTERNAL_PREEXISTING`; subsequent
validation and close use the ordinary assurance path.

This records provenance without claiming that Build OS created, authorized, or
observed the original external change. It rejects a target that is not current
HEAD, dirty state, changed paths outside scope, prohibited paths, and unsafe
change kinds.

## Runtime-only continuation without a source delta

A task that performs runtime work but must not alter the product repository is
declared `NO_SOURCE_DELTA` (`--no-source-delta` in the facade). This is not a
substitute for `PRODUCT_COMMITTED`: it is a separate, narrow assurance path:

`ACTIVE -> ASSURANCE_READY -> CLOSED`

The transition requires an observable baseline HEAD captured at task start,
the exact same current HEAD, a clean product tree, no product commit anchor,
deterministic acceptance checks, an assurance inspector, and a non-empty
runtime acceptance reference. Any dirty path, real product delta, empty/no-op
commit, synthetic commit anchor, or missing runtime evidence fails closed.
Normal product-changing tasks continue to require
`ACTIVE -> PRODUCT_COMMITTED -> ASSURANCE_READY -> CLOSED`.

R3 remains full independent assurance. Its reviewer, reference, and distinct
rollback/recovery check are mandatory, but its recorded scope is
`NO_SOURCE_DELTA_RUNTIME_ASSURANCE`, not a fabricated product-delta review.

A released `BLOCKED_SOURCE_FIX` task is never reopened for this path. Use
`continue-task` with a fresh task ID and the required resolution reference;
the new task carries immutable source generation/hash lineage and may declare
`NO_SOURCE_DELTA`. The source task remains terminal and unchanged.

## State compatibility

The immutable state schema remains `buildos.state.v1.22` because lineage,
source-defect metadata, and product origin are additive optional fields. Old
generations remain readable and a missing product origin means `NATIVE` for
compatibility. Work-packet projection is versioned separately as v1.23.

If a future lifecycle change is not backward readable, it must use an explicit
migrator with source-schema validation, a new immutable generation, a migration
receipt, post-write verification, and a single guarded pointer swap. Silent
in-place migration and historical-state rewriting are forbidden.
