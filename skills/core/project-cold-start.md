# Project Cold-Start

An advisory, repeatable procedure for reconstructing current project context.
It creates no authority or persisted cold-start status.

Use the canonical development semantics in
`docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md` when the CADS skill library is
available. Do not copy or redefine that Standard inside project context files.

## When to use

Use before planning or implementation when:

- this is first contact with a project;
- a new Tech Lead or Worker takes over;
- the user supplies only a repository;
- previous chat context is unavailable or untrusted; or
- repository documentation appears inconsistent.

## Read current reality in this order

1. Root `AGENTS.md` for the operating map.
2. `TASK.md` for active intent, predefined acceptance, constraints and progress.
3. `ARCHITECTURE.md` for durable design and invariants.
4. `README.md` and only the durable documentation relevant to the task.
5. `git status` for canonical branch/HEAD, owner work and uncommitted state.
6. Recent Git history, normally `git log -5`.
7. Relevant diffs and source for implementation reality.
8. Tests/CI for verification evidence and current identified runtime observations
   for observed behavior.

Preserve uncommitted owner work. Do not treat a branch name, old chat, agent
report, document claim, unbound test result, or unidentified runtime as proof of
current product completion.

## Recover the minimum working context

Establish:

- what the product does and what path is currently supported;
- canonical Git branch, Product HEAD and relevant working-tree state;
- current architecture;
- one active Product Goal and its predefined acceptance criteria;
- constraints and non-goals;
- implementation already completed;
- blockers and remaining work;
- the active workline and whether valuable dirty work is bounded; and
- the next safe action.

When runtime evidence matters, identify the source/configuration/environment it
actually exercised. Evidence without identity is weak evidence.

When it helps expose uncertainty, label a fact `CURRENT`, `STALE`, `LEGACY`, or
`UNKNOWN`. These labels are advisory findings for the current reading only and
must not be stored as lifecycle state.

## Reconcile contradictions

Check for competing architecture documents, a stale `TASK.md`, README claims
that disagree with code, completion claims supported only by tests, legacy
documents presented as current, unidentified runtime/source skew, multiple
competing worklines, large mixed dirty stacks, and the absence of a clear active
Goal.

Apply domain-specific authority:

- Owner/Tech Lead: desired outcome and business intent.
- Identified Git/source: implementation reality.
- Identified runtime evidence: observed behavior.
- Tests/CI: verification evidence.
- Durable docs: still-valid design/context.
- `TASK.md`: current work context.
- Agent reports: claims; chat memory: hints.

When authorized, normalize ordinary documentation using the smallest model:

- `AGENTS.md`: map and operating instructions;
- `TASK.md`: active Goal context only;
- `ARCHITECTURE.md`: durable architecture decisions;
- `README.md`: user/developer usage where appropriate; and
- Git/source/tests/runtime: current evidence in their respective domains.

Promote only still-valid durable information from old documents. Historical
material may remain under `docs/legacy` or `legacy` when useful. Do not add task
parsers, schemas, revisions, IDs, migration history, or a document database.

## Result contract

Return one concise result:

- `COLD_START_READY`: current reality is sufficient to state the Goal,
  acceptance, constraints, completed work, remaining work and next safe action.
- `NORMALIZATION_REQUIRED`: contradictions or missing intent prevent safe
  continuation. List only the smallest concrete documentation, workspace, or
  owner-input actions needed. Important business intent that exists only in an
  unavailable chat is missing information, not recoverable repository context.

If obvious folder bloat, forgotten worklines, or an unbounded mixed dirty stack
is observed, add a short `WORKSPACE_HYGIENE_WARNING` and refer to
`workspace-hygiene.md`. Never perform destructive cleanup as part of cold-start.
