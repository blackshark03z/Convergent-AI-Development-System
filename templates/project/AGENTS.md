# Project operating map

On first contact, in a new Tech Lead/Worker session, or when context may be
stale, cold-start from this repository before planning or implementation. If
the Build OS skill library is available, follow its Project Cold-Start
playbook. Otherwise:

1. Read `TASK.md`, `ARCHITECTURE.md`, `README.md` and relevant durable docs.
2. Inspect Git status, the current branch/HEAD, recent history, relevant diffs,
   source and tests.
3. Reconcile prose with current reality. Git/source wins over stale product
   claims; tests/CI wins over stale verification claims.
4. State the active goal, acceptance, constraints, completed work, blockers,
   remaining work and next safe action. Ask for missing owner intent.

Preserve owner work. Keep normal development native to the project. If Build OS
is available, use it only at explicitly consequential boundaries; do not add or
infer lifecycle, adoption, or continuation concepts.

`TASK.md` holds active context. `ARCHITECTURE.md` holds durable architecture.
