# Context-epoch runtime capability

The reusable package implements `COMPACT_THEN_CONTEXT_EPOCH_HYBRID` as an
adoption-layer capability. Build OS v1.22, its governor, and its rollover CAS
are unchanged.

## Gate and orchestration

The installed Codex app-server protocol is exercised through `thread/start`,
`thread/read`, `thread/fork`, `thread/goal/get`, `thread/goal/set`,
`turn/interrupt`, and `thread/archive`. `thread/start` creates a persistent
idle thread with `turns=[]` and `forkedFromId=null`; `thread/fork` is rejected
for epoch creation because it copies completed turns. Goal activation is held
until the receipt is published and verified.

Run the bounded handoff only after native compaction has completed, or its
unavailability has been established, and one real current-context request has
been measured:

```powershell
python <package-root>/skills/project-lifecycle-bootstrap/scripts/context_epoch.py `
  --root <product-root> handoff `
  --compaction-status ATTEMPTED_INEFFECTIVE `
  --compaction-evidence <bounded-compaction-proof-pointer> `
  --post-compaction-evidence <bounded-real-request-proof-pointer> `
  --projected-prompt-tokens <non-zero-latest-measurement> `
  --model-context-window <measured-window> `
  --material-work-remains YES `
  --atomic-operation-complete YES
```

Bounded closeout normally remains in the current context. `--closeout-only YES`
is eligible for one controlled fresh Context Epoch only when native compaction
is unavailable or ineffective, the measured post-compaction governor result is
`COMPACT_REQUIRED`, `HARD_STOP`, or `ROLLOVER_REQUIRED`, no material work
remains, the atomic boundary is complete, and
`--would-continuing-same-context-violate-headroom-safety YES` is supplied.
`CONTINUE`, `HEADROOM_WARNING`, an unmeasured footprint, a zero marker, or a
safe same-context continuation never creates an epoch. If the Context Epoch
capability is absent, the adapter stops safely instead of continuing an unsafe
context. The adapter never changes governor policy or uses request count. For
the hybrid's verified `COMPACT_REQUIRED`/`HARD_STOP` fallback it uses the
kernel's existing forced rollover entrypoint, retaining its sole CAS;
`ROLLOVER_REQUIRED` uses the ordinary guarded entrypoint.

This is a safety fallback, not an economic trigger. The successor receives the
same bounded Goal objective and Working State Capsule, then performs only
targeted evidence reads and immediate validation/assurance/close actions. It
receives no predecessor conversation or tool output. `PRODUCT_COMMITTED`
remains a legal boundary; `ASSURANCE_READY` does not become eligible.

The adapter pauses and interrupts the predecessor, creates the inactive
zero-history successor, calls the existing `scripts/ai.py rollover` CAS,
checkpoints Continuity, renders the existing bounded Working State Capsule,
publishes an immutable `buildos.context-epoch-receipt.v1`, preflights the
successor, activates the same bounded Goal objective, and archives the stale
predecessor. If any step before activation fails, the successor is archived and
the command returns `ACTION_REQUIRED`; it never activates two owners.

The receipt is proof/projection only. It binds task, revision, epoch/thread,
generation hashes, lifecycle phase, worker, operation, worktree/Git identity,
Continuity hash, Capsule hash, and Goal-objective hash. It contains no
transcript, logs, old reasoning, Knowledge Pack, environment dump, or secrets.

Before substantive Worker mutation, `scripts/ai.py` invokes the read-only
`context_epoch.py preflight`. Epoch-one tasks remain unaffected; later epochs
fail closed without `CODEX_THREAD_ID`, and for wrong thread, live Goal hash,
generation, worktree, Continuity, receipt, dirty state, or Capsule binding.
