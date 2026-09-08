# Goal

Refactor CADS from an accumulating procedure list into one smaller universal
control model while preserving the concrete failure coverage earned from Story
Audio, Multiple Automation and MAR-like systems.

# Critical User Journey

Owner intent -> Worker cold-starts from current reality -> AI Tech Lead frames
Goal/CUJ/acceptance and only material design drivers -> Worker makes the smallest
coherent change and resumes the real journey -> Product Acceptance proves the
outcome -> Thin Guard is used only when the action crosses a consequential
boundary. Debugging, hygiene and UI/UX methods are pulled only when applicable.

# Acceptance

- Universal mental model is `Reality -> Intent / Design -> Change -> Acceptance -> Consequence`.
- Product Goal Framing and standalone Concern Coverage Review are consolidated
  into one Product / Design Framing procedure without losing explicit domain,
  state, security/effect, concurrency/fencing, quality or economy questions.
- Remove `skills/core/concern-coverage-review.md`; add no replacement skill.
- Systematic Debugging and Workspace Hygiene remain available but are described
  as conditional methods/helpers, not universal stages.
- State Lifecycle & Ownership remains a conditional design lens, not a new skill;
  repeatable workflows gain a matching repeat-cycle acceptance oracle.
- Tiny local tools can collapse to near-zero ceremony; Story Audio, Multiple
  Automation and MAR-like systems deepen the same controls only where material.
- Thin Guard, Owner/Tech Lead/Worker authority, Knowledge-Gap Responsibility,
  Decision Continuity, tests-as-evidence, feature-PASS != journey-PASS and
  `REUSE -> WIRE -> FIX -> REPLACE_AND_DELETE -> ADD` remain intact.
- DR-0003 supersedes DR-0002 without rewriting history.
- Focused semantic/archetype regression and the full active CADS suite pass.

# Acceptance Fixture / Golden Input

Use four archetypes as semantic regression:

- Tiny local tool: reversible calculator/file-converter style change incurs no
  irrelevant design ceremony.
- Story Audio: composed user journey plus `Run A complete -> Run B starts clean`
  while historical Run A remains bound to its correct snapshot.
- Multiple Automation: account/channel/workspace/profile/proxy identity,
  cardinality and ownership must be surfaced before expensive design freeze.
- MAR-like runtime: concurrency/resource ownership/fencing/recovery and external-
  effect ambiguity/idempotency remain explicit when applicable.

# Non-goals

No new skill, lifecycle, process database, approval board, universal security/
performance/state-machine phase, specialist encyclopedia, runtime or authority.
Do not rename files merely for cosmetic purity when compatibility can be kept.

# Constraints

- Simplification is valid only if failure coverage remains explicit.
- Scan broad concern lenses only when being wrong could materially change design,
  acceptance, safety or cost; work narrowly on actual drivers.
- A clear framing never claims exhaustive unknown-unknown coverage.
- Preserve normal native Git/test workflow and the Thin Guard boundary.

# Material Decisions

- Independent reviewer verdict: `REFACTOR_WITH_CORRECTIONS`, classifying current
  CADS as `EARLY_PROCESS_ACCRETION` rather than over-engineered.
- Keep five control points as the stable mental model; specialist procedures are
  conditional methods.
- Merge Concern Coverage into Product / Design Framing and delete the standalone
  playbook while retaining concrete trigger questions.
- Do not create State Lifecycle & Ownership as a skill; use a design lens plus
  repeat-cycle acceptance evidence.
- Every future ADD to CADS must include a consolidation check for MERGE/DELETE.

# Progress / Discoveries / Next

- Started from clean synchronized `master` at
  `fea7cac5dc74598cf6e83f432538a2ec33418288`.
- Independent review completed before mutation and explicitly challenged both
  keeping and simplifying the current structure.
- Current-reality audit confirmed overlap between Product Goal Framing and
  Concern Coverage Review, while Debugging/Hygiene are naturally conditional.
- Consolidated Concern Coverage into Product / Design Framing and removed the
  standalone `concern-coverage-review.md` skill; no replacement skill/runtime/
  lifecycle authority was added.
- Preserved explicit archetype lenses for journey composition, repeat-cycle state
  isolation, domain/cardinality/ownership, concurrency/fencing/recovery and
  external-effect ambiguity/idempotency.
- Added repeat-cycle Product Acceptance evidence for `Run A -> Run B` state
  isolation while preserving historical Run A snapshots/artifacts.
- DR-0003 is Accepted and DR-0002 is marked `Superseded by DR-0003`.
- Initial focused run caught two template/prose line-wrap contract regressions;
  semantic probes showed the actual failure coverage was intact, so wording was
  repaired without weakening test or acceptance oracles.
- Focused bootstrap/candidate/E2E verification passes 25/25, including the new
  four-archetype semantic regression.
- Full active suite passes 70/70 with `SIMPLIFIED_ACTIVE_SUITE=PASS` in ~81s.
- `git diff --check` passes; active docs/templates contain no route to the removed
  standalone skill.

Next: perform final staged-diff review, commit the bounded consolidation, push
`master`, verify local/remote convergence, then freeze CADS until a real Class A
or repeated systemic failure satisfies the existing Freeze Rule.