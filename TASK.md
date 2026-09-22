# Goal

Make CADS direct execution operational through one harness-neutral, read-only
handoff seam without making CADS own a model, agent, provider, session, context
engine, worker process, or harness lifecycle.

Preserve the canonical five-control model:

`Reality -> Intent / Design -> Change -> Acceptance -> Consequence`

# Critical User Journey

Tech Lead reconstructs reality -> frames the bounded Goal and material Design
Baseline when needed -> identifies explicit worker input files -> derives the
DIRECT/GOVERNED route from required runtime properties -> compiles one
content-addressed execution handoff -> an external compatible coding harness
consumes that packet natively -> Product Acceptance remains independent.

# Acceptance

- `python scripts/ai.py --root <repo> handoff --input <path>...` emits a
  deterministic JSON handoff using only explicit repo-local UTF-8 text inputs.
- Every input includes its repo-relative path, SHA-256 identity and exact text
  content so a receiving harness can bind execution to identified design truth.
- Handoff route reuses the existing property-based `DIRECT`/`GOVERNED`
  classifier and preserves stable property ordering.
- The handoff grants no authority, persists no lifecycle state and starts no
  harness/model/agent/provider/session process.
- Missing inputs, directories, non-UTF-8 inputs and paths escaping the repository
  root fail closed.
- The command is read-only against repository contents.
- Focused handoff/routing tests pass, then the full active CADS self-test passes.
- `docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md` remains unchanged.

# Non-goals

No sixth CADS control. No model/provider router, context engine, WebTurn equivalent, agent runtime,
session manager, subagent framework, harness plugin framework, task lifecycle,
routing database, automatic prompt planner, or CADS-owned worker launcher. Do not
make ChatCode, Codex, Claude Code, OMP, MAR, OpenSpec or Spec Kit a permanent
semantic dependency.

# Constraints

- Keep direct execution the default when no governed runtime property is required.
- Handoff compilation is a projection only; receiving/executing the packet belongs
  to the selected external harness.
- Inputs are explicit rather than auto-loading the whole CADS corpus.
- Preserve existing Consequence and Product Acceptance semantics.
- Preserve the frozen Convergent AI Development Standard unchanged in this slice.

# Material Decisions

- CADS owns accepted product/design semantics and the handoff contract, not harness
  cognition/execution mechanics.
- Content identity travels with the handoff so acceptance can reason about the
  actual baseline the Worker received.
- A stronger future harness should be able to consume the same packet or bypass
  the projection entirely when equivalent semantics are already native.
- MAR remains conditional for runtime properties; it is not introduced into this
  handoff path.

# Progress / Discoveries / Next

- Start HEAD: `9376c777076e3714ecb77d670fe02f7741b20a2c`.
- DR-0012 already requires a bounded execution package and replaceable spec
  substrate; DR-0013 already makes direct execution the default.
- Added `buildos/execution_handoff.py` and focused tests.
- Added the `handoff` CLI surface without starting or selecting a harness.
- Next: document the seam, run focused/full verification on an isolated checkout,
  then open/merge only after evidence is green.
