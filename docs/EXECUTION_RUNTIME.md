# Execution and Effect Runtime

## Purpose

The optional enhanced runtime prevents expensive work from beginning without a
compiled execution envelope. It is mandatory when `--execution-class` is
`LOCAL_HIGH_COST` or `EXTERNAL_EFFECT`. `LOCAL_REVERSIBLE` remains the explicit
compatibility class and uses the prior lifecycle behavior unless a spec is
provided.

Use `templates/execution/EXECUTION_SPEC.json.tmpl` as source and
`schemas/execution-spec.v1.json` as the portable shape. The Python compiler is
the semantic authority because it verifies cross-object references and
constraints that JSON Schema alone cannot express.

## Composed public-facade admission

`admit` performs a read-only preview. `bootstrap`, `continue-task` and
`adopt-existing-change` compile the same envelope before creating canonical
state. A blocked compilation leaves no `CURRENT` generation.

For a newly enrolled policy v1.24 project, `scripts/ai.py` is the normal Worker
entry point. It composes separate fail-closed responsibilities behind that one
facade; there is deliberately no second monolithic admission engine:

1. exact package/executor authority;
2. project policy/package compatibility;
3. context ownership when the action needs it;
4. task risk/authorization and clean Git baseline;
5. capability, authority, plan and effect admission;
6. immutable canonical bootstrap.

Older policies are not silently opted in. `recover`, `status` and `next` stay
available even if adoption configuration needs repair.

The direct Python `BuildOS` API is the kernel API: it enforces task/Git and
execution-envelope admission, but it does not impersonate the opt-in project
adoption or context preflights. The administrative `scripts/ai_os.py` facade is
break-glass lifecycle authority, not a Worker bypass. Its
`adopt-existing-change` command now uses the same authority/project-policy
preflight because it creates admitted execution state. `abort` and `recover`
remain available when those adoption checks are what require repair. Bootstrap
and external adoption create a first context and therefore do not require a
pre-existing context-owner receipt.

## Compiled guarantees

The compiler rejects the task before implementation when any of these is true:

- a critical assumption is UNKNOWN/REJECTED, or a proof/fallback is missing;
- a required capability is unavailable/unknown or its exact constraint differs;
- a step reads/writes a field without an authority row;
- an LLM is declared canonical rather than advisory;
- an external step lacks a provider capability/effect/recovery family;
- external or high-cost work is under-declared as a cheaper execution class;
- a non-idempotent action lacks a canonical no-effect predicate;
- an idempotent action lacks a stable provider-supported key;
- a plan DAG is cyclic or references unknown steps;
- an acceptance criterion is not bound to an executable claim;
- no FINAL claim exists, or R3 has no rollback/recovery claim;
- a command is not an argv registry entry with admitted provenance.

Capabilities never become product authority. They state whether/how an
operation can run. Authority rows state who owns each input/output meaning.
LLMs can remain semantic advisers but cannot be compiled as canonical owners.

## Blocker and plan validity semantics

Every step names admitted failure families and every family has one disposition:
`BOUNDED_FIX`, `REPLAN`, `RECONCILE` or `STOP`.

- First non-critical `BOUNDED_FIX` occurrence: one bounded correction.
- Second occurrence of the same family: `REPLAN_REQUIRED`.
- Second distinct unexpected family in one plan: `REPLAN_REQUIRED`.
- Any blocker tied to a critical assumption: immediate `REPLAN_REQUIRED`.
- A family declared `REPLAN`: immediate `REPLAN_REQUIRED`.
- A family declared `RECONCILE`: effect reconciliation, never speculative retry.
- A family declared `STOP`: autonomous continuation is forbidden.

`replan` atomically replaces the envelope only while lifecycle phase is ACTIVE,
the product HEAD still equals the clean task baseline, and no unresolved effect
exists. A product commit or assurance requires lifecycle adoption/a new
revision instead; it cannot become a new provenance source during replan. A new revision resets effects, blockers, reviews
and current claim results; the immutable prior generation remains available
only as evidence lineage.

Every prepared effect binds an `effect_contract_hash` to its exact canonical
input hash, adapter-contract hash, provider/idempotency/no-effect contract, and
the capabilities, constraints, authorities and dependencies of its external
step. Replan retains terminal records as history. A terminal record remains in
the active ledger only when this semantic identity is byte-for-byte identical;
that explicit carry-forward can satisfy identical required work. A changed or
unbound record is retired to `effect_history`, cannot satisfy the replacement
action and cannot reuse its historical `effect_id`. Unresolved effects still
block replan and must be reconciled under their originating envelope.

## External-effect transaction

An effect action is declared once in the envelope. An effect identity is stable
within a lifecycle revision; a second identity for the same action is rejected.

```text
PREPARE
  -> INTENT_RECORDED (stable identity/key and deadline durable)
DISPATCH
  -> DISPATCH_UNCONFIRMED (durable boundary before the provider call)
ACK
  -> DISPATCH_CONFIRMED (provider reference required)
RESULT
  -> OUTPUT_CONFIRMED (result reference + SHA-256 required)
COMMIT
  -> COMMITTED (durable local persistence reference required)
```

If preparation fails before `DISPATCH`, `FAIL_BEFORE_DISPATCH` records positive
pre-provider evidence and resolves no effect. `TIMEOUT_NO_DISPATCH` is allowed
only after the compiled deadline while state is still `INTENT_RECORDED`.

After the dispatch boundary, lack of a local result is never no-dispatch proof.
`RECONCILE_CONFIRMED` binds provider evidence for the already-run action.
`RECONCILE_NO_EFFECT` requires the exact canonical predicate declared by that
action plus a positive evidence reference.

### Exact retry rule

`AUTHORIZE_RETRY` is legal only when either:

1. state is `DISPATCH_UNCONFIRMED`, the provider contract declares
   `IDEMPOTENT_WITH_KEY`, and the same stable idempotency key is retained; or
2. state is `RESOLVED_NO_EFFECT` after positive reconciliation with the exact
   action predicate (or a proven pre-provider no-dispatch outcome).

It is illegal after a confirmed/ambiguous output, without the provider key, or
from labels such as failure/timeout alone. Every retry increments the durable
attempt and writes a new dispatch boundary. Validation and close fail until all
effects are terminal and every required action is COMMITTED in the current
revision.

## Review, salvage and supersession

`review` records `PASS`, `SALVAGEABLE` or `REJECT` against exact asset identity
and content SHA-256. A superseding review is a fresh epoch and must bind the
same bytes; prior review rows remain immutable. `SALVAGEABLE` authorizes only
the deterministic salvage already represented by the plan, followed by fresh
QC. Salvage records a new asset identity and content hash with
`derived_from_review` plus transformation evidence. It does not silently
convert rejected bytes into accepted bytes or reuse one asset identity for
different content.

## Change-proportional assurance

Each claim binds:

- exact task acceptance criteria;
- an admitted argv command and provenance;
- semantic claim hash;
- Git path dependency patterns;
- `AFFECTED` or `FINAL` mode and evidence role.

At validation, Build OS hashes the exact Git blob identities selected by each
claim. A prior `AFFECTED` PASS is reused only when claim semantics, dependency
fingerprint and immutable prior evidence bytes are identical. Missing or
modified evidence forces execution. `FINAL` claims always execute. R3 still
requires independent reviewer/reference, and its rollback/recovery claim is
always part of the admitted command set.

This is claim-level evidence reuse, not test skipping by intuition. The final
evidence records both executed and reused claims.

## Command trust boundary

Enhanced claim commands and new project-policy quality gates use argv with
`shell=False`. A provenance label is not trust evidence:

- `OWNER_AUTHORED` must match one exact argv entry in a command registry whose
  bytes and SHA-256 match the current Git baseline;
- `PACKAGE_OWNED` must match a package registry whose path/hash is declared by
  `PACKAGE_MANIFEST.json`;
- `MODEL_PROPOSED_APPROVED` must bind the exact command hash and task approval
  reference to one entry in a command-approval registry already present with
  the same bytes/hash in the Git baseline.

Changing argv after approval or merely self-labelling a model command as owner
or package provenance is rejected. Legacy lifecycle `--check` strings and old
`{"command": ...}` project gates remain readable for v1.22 compatibility and
are labeled `LEGACY_SHELL`; they do not gain enhanced guarantees.

## Migration

- Existing tasks and states without an execution runtime remain readable as
  `LEGACY_LOCAL`.
- Existing CLI calls default to `LOCAL_REVERSIBLE`.
- Choose `LOCAL_HIGH_COST` for expensive local model/media work and supply a
  spec; choose `EXTERNAL_EFFECT` whenever a provider-side action may occur.
- Migrate project gates to `argv` plus a deterministic registry source/hash;
  `templates/execution/COMMAND_REGISTRY.json.tmpl` provides the portable shape.
- For an approved model proposal, use the separate tracked
  `COMMAND_APPROVAL_REGISTRY.json.tmpl`; a status/reference written only inside
  the model request is not approval provenance.
- Re-run `execution_authority.py write-record` when intentionally adopting a
  new package build, then commit the updated adoption record with the project.
- Context epoch and continuity stay orthogonal; rollover never creates a
  product revision and a tiny product revision never creates a thread epoch.
