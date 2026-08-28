# Disposable Codex runtime capability proof

This package's context-epoch adapter is gated on the installed Codex
app-server protocol; this is not an API-documentation assumption.

Run a new disposable proof with:

```powershell
python skills/project-lifecycle-bootstrap/scripts/prove_context_epoch_runtime.py --cwd <safe-disposable-worktree>
```

The disposable proof uses persistent `thread/start`, `thread/read`,
`thread/goal/get`, `thread/goal/set`, `thread/inject_items`, `turn/start`,
`turn/interrupt`, and `thread/archive` calls. It observed:

- a predecessor with a completed real turn;
- `thread/start` returning a new persistent thread with `turns=[]` and no
  `forkedFromId`;
- `thread/fork` copying predecessor completed turns, and therefore being
  rejected by this capability;
- a paused predecessor Goal and a paused successor Goal with the same bounded
  objective hash;
- one bounded injected bootstrap marker becoming visible to the successor's
  first real request, while predecessor turns/tool items did not appear;
- stable distinct predecessor/successor identifiers; and
- archiving the predecessor after successor activation.

The adapter independently checks zero history, a matching canonical
Build-OS thread ID, the live Goal-objective hash, and receipt bindings before
activation or later substantive mutation. All disposable proof threads were
archived. No product repository or YouTube runtime was used.
