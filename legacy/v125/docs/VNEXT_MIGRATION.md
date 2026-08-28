# Migration from v1.24 to the vNext Work Loop

## Compatibility contract

- `buildos.state.v1.22`, generation records, `CURRENT`, receipts and recovery
  remain readable and unchanged.
- Existing live or historical v1.24 tasks are not rewritten or automatically
  enrolled. Continue them with the compatibility lifecycle commands.
- New evidence-carrying tasks add optional `work_loop` content to the same
  immutable state and use the same store linearization point.
- Existing enhanced execution specs and effect adapter contracts remain valid.

## Starting new work

1. Issue `buildos.work-contract.v1` from Tech Lead/Owner authority.
2. Validate it and render the bounded Worker Capsule with `contract`.
3. Ground only the claims needed for the next action in
   `buildos.grounding-report.v1`.
4. Run `work --work-contract ... --grounding ...` once.
5. Implement and commit through normal Git.
6. Run `work --assure`; use explicit effect/recovery commands where reported.

The facade compiles the lifecycle task ID, outcome, acceptance, scope, risk,
Worker and action class from the two inputs. Do not re-enter those semantics as
legacy task flags.

## Existing and dirty repositories

Grounding may inspect and bind a dirty worktree, but bootstrap still refuses to
launder owner work into a supervised task. Preserve it, finish or explicitly
adopt it through the existing admin provenance workflow, then start from a
clean observable baseline. `.buildos` remains reserved and locally excluded.

## Revisions and canonical decisions

A Work Loop Contract is immutable. Repository contradictions may be adapted
locally when canonical intent and acceptance remain intact. A material
Decision Request must be resolved by the named authority through exact
request-hash-bound immutable resolution evidence, or by the next trusted Work
Contract revision linked through `parent_contract_hash` and the exact Decision
Request reference. Same-Contract Worker grounding cannot clear the obligation.
Legacy `new-revision` remains rejected for Work Loop tasks so scope or intent
cannot diverge from the bound handoff.

## Rollback

The migration is additive. To stop using Work Loop intake, finish or abort the
active Work Loop task and start a fresh legacy task; do not delete generations,
edit evidence or repoint `CURRENT`. Package rollback uses the prior immutable
portable package and does not reinterpret vNext generations as legacy tasks.
