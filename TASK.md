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
- PR #10 was squash-merged as `c67cd2f340929e78821fd9bec078dd6f42a97aa5`.
  Remote and local `master` have the same verified tree
  `6bd6407601362281e096cbea0b775bf8ee710006`.
- Final pre-merge evidence: 13/13 targeted handoff/routing/contract tests PASS and
  the full active suite 133/133 PASS with `SIMPLIFIED_ACTIVE_SUITE=PASS`.
- Pilot 1 exercised the merged seam with a DIRECT handoff for this `TASK.md`,
  bound to SHA-256
  `be214c149f3ff20f07eeb042ce2d3b1d14cc431480cfe8ed93146486ec63eccf`.
  ChatCode accepted the packet as execution context. Its semantic mutation API
  was blocked by the daily AI-write quota (923410 / 600000), so no mutation was
  attributed to that failed attempt; the equivalent native direct path performed
  the bounded SoT update without MAR or a CADS-owned runtime.
- ChatCode predictive retrieval also ranked unrelated legacy files for this
  already-bounded task. Treat explicit handoff inputs as authoritative execution
  context and heuristic retrieval only as supplemental discovery when scope is known.

- Cross-project Pilot 2 used clean AutoSub HEAD `e843b5dde1383248ef8d306a84a4402cd7fc627e`
  for A5 Voice Preview Integrity. The explicit DIRECT packet contained five
  repo-local inputs; `_cads_pilot_a5.md` was bound to SHA-256
  `265c20c37d1ba4460bf6faddd3c84af79b7e77a295cdd8a9e42f05e105c07e9b`.
- The first real cross-project handoff exposed a Windows portability defect:
  JSON containing a BOM/Vietnamese text could raise `UnicodeEncodeError` when
  stdout used cp1252. The CLI now preserves Unicode JSON when the stream supports
  it and falls back to ASCII JSON escapes only when required by the output
  encoding. The regression explicitly exercises `PYTHONIOENCODING=cp1252`.
- Portability-fix evidence: 12/12 focused handoff/routing tests PASS; full active
  CADS suite 134/134 PASS with `SIMPLIFIED_ACTIVE_SUITE=PASS`.
- Retried AutoSub handoff PASS: `DIRECT`, five inputs,
  `authority_granted=false`, `persists_state=false`,
  `starts_harness=false`. ChatCode ranked the explicit packet first, although
  supplemental predictive retrieval again included an unrelated Gemini test.
- AutoSub already implemented A5 stale-preview invalidation. The pilot therefore
  produced a test-only candidate using the project's existing Python
  source-contract pattern rather than rewriting working UI logic or adding a JS
  test framework. Focused UI contract: 7/7 PASS on first candidate. A held-out
  negative probe temporarily removed voice-change invalidation; the new oracle
  failed as expected and the product source was restored exactly.
- Pilot 2 metrics: first-pass candidate acceptance PASS; DESIGN_GAP count 0;
  Owner interruptions 0; CADS portability repair rounds 1; product-logic repair
  rounds 0. ChatCode semantic-write quota was again unavailable
  (1041316 / 600000), while the native DIRECT path remained usable.
- Conclusion from Pilots 1-2: keep explicit handoff inputs authoritative,
  heuristic retrieval supplemental, and harness quota/model/session mechanics
  outside CADS Core. Do not add a new CADS runtime/retrieval layer from this
  evidence.

- Cross-project Pilot 3 used clean Story Audio HEAD
  `04e602958d615c0581723ee46a89b505fbbdfe7f` for the design-heavy
  `SAVE_VOICE_CONFIGURATION_BATCH` contract. The DIRECT handoff contained four
  explicit inputs; the pilot design input was bound to SHA-256
  `2ca78763695d8ac27f2b40278784aede7a6d675f7c43cc9206e0bfd1e06f6b69`.
  Packet compilation took about 0.74 s and granted no authority, persisted no
  state and started no harness.
- The design contract covered eight coupled obligations: local draft vs one batch
  commit, pre-write validation, shared transaction/no PARTIAL, at-most-one draft
  Casting Plan per chapter, inheritance normalization, stale-default recovery,
  no provider/PREPARE/render/QA side effects, and disposable-test-only evidence.
- Source audit found the accepted design already implemented: the production
  command validates submitted rows before durable success, wraps scoped plan,
  Book Voice Profile and Character writes in one `Database.transaction()`, passes
  that shared connection into the scoped batch writer, and returns only APPLIED
  for this command. `Database.transaction()` rolls back on exceptions.
- Eight focused oracles PASS: four domain tests prove one-plan-per-chapter,
  invalid-item zero-plan write, default-to-inheritance normalization and
  unavailable-voice no-partial-write; four API/UI tests prove the shared scoped
  mutation transaction, one final batch-save workflow, effective-voice
  reconciliation and one visible atomic recovery action with no PREPARE/render.
  The first combined test command used the system Python and partly failed on
  missing FastAPI / an incorrect guessed class name; rerunning those tests with
  the repository `.venv` and exact class names passed 4/4. This was test-runner
  discovery noise, not product failure.
- Pilot 3 found no product DESIGN_GAP and made no Story Audio source/test commit.
  One small evidence gap remains: there is no single explicit failure-injection
  test that starts a mixed scoped+Book/Character batch, mutates an early item and
  then proves rollback after a later write-time exception. Current source
  structure plus transaction semantics support the guarantee, while existing
  domain tests cover the highest-risk component failures. Record this as an
  optional future oracle, not a reason to manufacture product work.
- ChatCode predictive retrieval again ranked unrelated acceptance/Gemini/legacy
  files ahead of the actual API/domain implementation even though the explicit
  packet was precise. Manual targeted discovery found the authoritative files
  immediately. This is further evidence that handoff semantics and harness code
  retrieval are separate concerns; do not build a CADS retrieval/runtime layer
  from this harness behavior.
- Pilot 3 metrics: first-pass design contract valid; DESIGN_GAP count 0; Owner
  interruptions 0; product mutations 0; handoff repair rounds 0; manual code
  discovery was required after noisy supplemental retrieval.
- Cross-project Pilot 3 closed cleanly; temporary packet/design files were removed
  and Story Audio returned to clean `main...origin/main`.
- Handoff Goal conclusion after three pilots: the harness-neutral seam is
  operational across CADS itself, a small UI-state Goal and a design-heavy
  transactional Goal. Observed failures were a Windows serialization defect
  (fixed) and harness-specific quota/retrieval/environment friction. None justify
  adding a CADS-owned agent runtime, model/session router or retrieval subsystem.
- Next: use the handoff seam in normal project work and collect representative
  failure evidence. Add or change CADS machinery only when repeated cross-project
  evidence shows a semantic guarantee missing from the existing five controls,
  Design Baseline, handoff, Acceptance or Consequence boundaries.
