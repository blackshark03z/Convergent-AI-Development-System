# Goal

Add lightweight durable decision continuity so material project-direction choices
survive chat/Tech Lead/Worker turnover without turning CADS into a context or
lifecycle management system.

# Critical User Journey

Owner/Tech Lead makes a material direction decision -> the current CADS procedure
applies a materiality test -> accepted rationale/direction is persisted in a
short repository Decision Record -> future Tech Lead/Worker cold-start reads the
active index and only relevant records -> continues from the settled direction
instead of rediscovering or silently reopening it.

# Acceptance

- Add a lightweight Decision Continuity Protocol defining authority, materiality,
  record format, supersession and bounded reading rules.
- Bootstrap creates a small `docs/decisions/README.md` active decision index while
  preserving all existing project files byte-for-byte.
- Detailed Decision Records are created only for material accepted decisions;
  routine reversible edits/checkpoints do not become records.
- Project Cold-Start reads the active index and relevant accepted Decision
  Records before planning when present.
- Product Goal Framing, Goal Execution and Product Acceptance enforce decision
  continuity at the moments material direction is created, discovered or closed.
- Root/project `AGENTS.md` state that accepted Decision Records own durable
  rationale/settled direction while chat memory/agent reports do not.
- Accepted records are superseded rather than silently rewritten.
- Existing six core skills, three conditional UI/UX skills, Thin Guard and the
  canonical Convergent AI Development Standard remain unchanged in role.
- Candidate/bootstrap/E2E tests prove the new index/protocol wiring and the full
  active source-checkout suite passes.
- Promotion finishes with clean synchronized `master` after post-merge tests.

# Acceptance Fixture / Golden Input

Bootstrap a temporary empty project and verify that the canonical context now
includes `docs/decisions/README.md`; rerun bootstrap to prove byte-preserving
idempotence. Use CADS itself as the first real Decision Record example by
persisting this accepted Decision Continuity direction under `docs/decisions/`.

# Non-goals

No memory database, vector store, context server, transcript ingestion, meeting
minutes archive, ADR approval workflow, task lifecycle, schema registry,
automatic decision extraction, Standard v2, Thin Guard redesign or legacy
rewrite.

# Constraints

- Decision continuity is docs-as-code and cross-cutting, not a seventh core
  skill or persisted workflow phase.
- Context must stay bounded: cold-start reads the index and only relevant records,
  not the entire historical decision archive.
- Do not modify `buildos/**`, legacy lifecycle sources, or
  `docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`.
- Preserve pre-existing bootstrap targets exactly; create only missing canonical
  context paths.

# Material Decisions

- A material decision discussed only in chat/memory/report is not durable project
  truth; accepted material direction must be persisted in the repository.
- `docs/decisions/README.md` is the active decision index and is bootstrapped by
  default; detailed records are conditional on the materiality test.
- Decision Records preserve WHY/settled direction. `TASK.md` preserves current
  Goal context, `ARCHITECTURE.md` current system design, Git/source implementation
  reality, and tests/runtime verification/observed reality.
- Accepted history is superseded rather than silently rewritten.
- The simplified thin-guard lineage remains rooted in baseline `8970dc8`; this
  Goal does not reopen or reinterpret that architecture decision.

# Progress / Discoveries / Next

- Started from clean `master` synchronized with `origin/master` (`0/0`) and
  created branch `task/cads-decision-continuity`.
- Confirmed the existing bootstrap only created three root context files and had
  no durable location for cross-session material decisions.
- Chosen minimum sufficient design: one protocol, one bootstrapped active index,
  conditional detailed Decision Records, and integration into existing CADS
  playbooks rather than a new core skill/subsystem.
- Implemented Decision Continuity protocol/index/self-hosted DR plus bootstrap,
  playbook, router, docs and packaging/test wiring without modifying
  `buildos/**`, legacy sources or the canonical Standard.
- Initial focused suite exposed one test-fixture-only nested-path assumption; the
  production bootstrap behavior was unchanged and the fixture was corrected.
- Focused bootstrap/candidate/E2E suite passes 21/21.
- Full active source-checkout suite passes 69/69 with
  `SIMPLIFIED_ACTIVE_SUITE=PASS`.

Next: final E2E/diff/scope review on exact bytes, then commit, push task branch,
merge to `master`, rerun the post-merge full suite, push `master`, verify
local/remote identity, and clean the task branch.
