# Project Cold-Start

An advisory, repeatable procedure for reconstructing current project context.
It creates no authority or persisted cold-start status.

## When to use

Use before planning or implementation when:

- this is first contact with a project;
- a new Tech Lead or Worker takes over;
- the user supplies only a repository;
- previous chat context is unavailable or untrusted; or
- repository documentation appears inconsistent.

## Read current reality in this order

1. Root `AGENTS.md` for the operating map.
2. `TASK.md` for active intent, acceptance, constraints and progress.
3. `ARCHITECTURE.md` for durable design and invariants.
4. `README.md` and only the durable documentation relevant to the task.
5. `git status` for branch, owner work and uncommitted state.
6. Recent Git history, normally `git log -5`.
7. Relevant diffs, source, tests/CI and current runtime observations.

Git and current runtime reality beat stale prose. Preserve uncommitted owner
work. Do not treat a branch name, old chat, or document claim as proof of
current source or verification state.

## Recover the minimum working context

Establish:

- what the project does;
- canonical Git branch, HEAD and relevant working-tree state;
- current architecture;
- active goal and acceptance criteria;
- constraints and non-goals;
- implementation already completed;
- blockers and remaining work; and
- the next safe action.

When it helps expose uncertainty, label a fact `CURRENT`, `STALE`, `LEGACY`, or
`UNKNOWN`. These labels are advisory findings for the current reading only and
must not be stored as lifecycle state.

## Reconcile contradictions

Check for competing architecture documents, a stale `TASK.md`, README claims
that disagree with code, completed claims unsupported by Git/source/tests,
legacy documents presented as current, and the absence of a clear active goal.
Tests/CI are verification truth; Git is product truth.

When authorized, normalize ordinary documentation using the smallest model:

- `AGENTS.md`: map and operating instructions;
- `TASK.md`: active task context only;
- `ARCHITECTURE.md`: durable architecture decisions;
- `README.md`: user/developer usage where appropriate;
- Git: product truth; and
- tests/CI: verification truth.

Promote only still-valid durable information from old documents. Historical
material may remain under `docs/legacy` or `legacy` when useful. Do not add task
parsers, schemas, revisions, IDs, migration history, or a document database.

## Result contract

Return one concise result:

- `COLD_START_READY`: current reality is sufficient to state the goal,
  constraints, completed work, remaining work and next safe action.
- `NORMALIZATION_REQUIRED`: contradictions or missing intent prevent safe
  continuation. List only the smallest concrete documentation or owner-input
  actions needed. Important business intent that exists only in an unavailable
  chat is missing information, not recoverable repository context.

If obvious folder bloat is observed, add a short `WORKSPACE_HYGIENE_WARNING` and
refer to `workspace-hygiene.md`. Never perform destructive cleanup as part of
cold-start.
