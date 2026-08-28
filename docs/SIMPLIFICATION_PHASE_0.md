# Build OS simplification: Phase 0 inventory

The new path guards explicit consequential boundaries from live Git facts. It
does not own normal development or create a parallel task lifecycle. The
v1.25 path remains available in parallel during this first slice.

## Bounded inventory

- **KEEP:** `buildos/git_adapter.py` exact commit/tree/relation, dirty path,
  deletion/type-change, control-path and safe repository observations.
- **SIMPLIFY:** path-policy evaluation becomes the small pure evaluator in
  `buildos/thin_guard.py`; `buildos/cli.py check` is the experimental boundary.
- **DEMOTE:** `telemetry.py`, `governor.py`, the large Work Contract model,
  grounding/assurance, and their CLI operations are not part of the new happy
  path.
- **DELETE from the new happy path (not globally in Phase 1A):** `model.py`,
  `store.py`, and `facade.py` lifecycle state, `CURRENT`/generations, commit
  adoption, continuation, executor lifecycle, persisted grants, recovery and
  migration progression.
- **REUSE/EXTRACT LATER:** no-blind-retry effect semantics in `execution.py`
  and effect-related project scripts, in a separate Effect Safety slice.

Project lifecycle/bootstrap/context scripts and `scripts/ai_os.py` remain
legacy-only. `scripts/ai.py` exposes the thin `check` command without invoking
legacy lifecycle preflights or creating `.buildos` state.

## Phase 1A boundary

Each check re-observes the supplied repository root and base against current
HEAD, tree, index and worktree state. Results are disposable. No task record,
grant, lease, generation, authority record, runtime anchor, migration or resume
operation exists in this path.

The output binds the decision to HEAD/tree plus index/worktree fingerprints.
Tracked `.buildos/**` deltas are a hard boundary violation, independent of the
declared expected or strict paths.

## Phase 1B explicit local boundary

`high-cost` is an explicit cooperative declaration, not a command classifier.
It evaluates the thin guard, re-observes the same canonical base and complete
Git observation digest at the last practical point before spawning one native
argv, and returns `BLOCK_STALE_STATE` if they differ. It does not use a shell,
infer command meaning, retry, or create state or receipts.

A microscopic race after the final observation remains outside the cooperative
local threat model. Stronger protection would require OS/filesystem/network
sandboxing rather than Build OS lifecycle machinery.
