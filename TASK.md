# Goal

Add one bounded universal Concern Coverage Review so CADS can proactively expose
material business/domain, user, data, architecture, security/effect, runtime,
delivery, quality, and economy gaps before hard-to-reverse design decisions,
without turning those concerns into mandatory lifecycle phases.

# Critical User Journey

Owner intent -> Product Goal Framing establishes the bounded Goal and applicable
domain semantics -> before materially stabilizing architecture/domain/source-of-
truth/authority, AI Tech Lead runs Concern Coverage Review -> only material gaps
are routed to existing procedures or targeted specialist analysis -> affected
decisions are stabilized only after gaps are resolved or scope is safely
restricted -> normal Goal Execution continues.

# Acceptance

- Add exactly one universal core playbook: Concern Coverage Review.
- Product Goal Framing conditionally establishes actors, domain objects,
  identity, relationships/cardinality, ownership, business rules, material
  object state transitions, exceptions, and Owner-controlled open questions when
  those semantics can materially change design.
- Root/project `AGENTS.md` route a material architecture/domain/source-of-truth/
  ownership/authority freeze through Concern Coverage Review, including a
  bounded fallback when the full CADS skill library is unavailable.
- The review covers broad concern classes proportionally to consequence and
  complexity, reports only material gaps/assumptions, and does not claim
  exhaustive completeness.
- New evidence that invalidates a material assumption triggers re-review of the
  affected decision rather than a permanent one-time approval.
- The canonical Standard gains only the smallest invariant needed to make this
  Knowledge-Gap Responsibility operational.
- No standalone Business Analysis phase, security phase, compliance engine,
  specialist skill family, task lifecycle, review database, or persisted concern
  status is introduced.
- A Decision Record explains why this repeated meta-failure justifies reopening
  the CADS Freeze Rule.
- Bootstrap/candidate/E2E and the full active CADS suite pass.

# Acceptance Fixture / Golden Input

Use the two failure classes that exposed the meta-gap:

- Story Audio: isolated feature PASS did not guarantee the composed user journey.
- Multiple Automation: architecture could miss material domain/cardinality facts
  such as GoogleAccount -> YouTubeChannel -> Workspace/Proxy/Profile ownership
  unless someone happened to ask the right question before freeze.

Also check a tiny reversible internal/docs change to prove the review is not
universally triggered after every edit.

# Non-goals

No comprehensive enterprise BA framework, BPMN requirement, stakeholder matrix,
requirements database, traceability engine, universal threat model, architecture
approval board, persisted `RESOLVED/NOT_APPLICABLE/MATERIAL_GAP` state, or new
CADS orchestration/runtime.

# Constraints

- Scan broadly, work narrowly: broad concern awareness must route only applicable
  material gaps to deeper work.
- Depth must scale with consequence, complexity, project size, operating context,
  and available evidence.
- A clear concern review is not proof that all unknown unknowns were eliminated.
- Domain semantics constrain architecture but do not prescribe schema, classes,
  services, aggregates, or deployment topology.
- Preserve CADS native Git/test workflow and Thin Guard boundaries.

# Material Decisions

- The repeated systemic failure is meta-routing blindness: CADS can handle a
  concern once recognized but lacked a bounded mechanism to search for concern
  classes that had not yet been recognized.
- Add one `skills/core/concern-coverage-review.md` rather than separate
  business-analysis/security/data/operations skills.
- Embed Domain Semantics in Product Goal Framing instead of creating a mandatory
  Business Analysis phase.
- Use scenario/assumption attack plus a broad reference concern model; findings
  are ephemeral reasoning evidence, not project state.
- Re-review is trigger-based when scope/risk/contracts/key assumptions change,
  not after every implementation edit.
- Research basis includes ISO/IEC/IEEE 29148 requirements engineering,
  ISO/IEC 25010/25019 quality models, IIBA business analysis, SEI ATAM/QAW,
  NIST SSDF, NASA SE tailoring, and DDD domain analysis.

# Progress / Discoveries / Next

- Started from clean synchronized `master` at
  `09ffd4aeea664519e46183408b8cc1a489c825a2`.
- Deep research confirmed the common industry pattern is broad reference coverage
  plus scenario/risk analysis, tailored to context, rather than running every
  specialist process on every project.
- Review changed the proposed name from `Completeness Scan` to `Concern Coverage
  Review` to avoid false assurance that a checklist can prove exhaustive
  completeness.
- Added the core playbook, Domain Semantics check, Standard/router/template/docs
  wiring, tests, and DR-0002 without adding runtime/lifecycle authority.
- First focused run caught root `AGENTS.md` exceeding its 4,000-character thin
  router budget; wording was compressed without weakening routing semantics.
- Focused bootstrap/candidate/E2E verification passes 24/24.
- First full-suite wrapper timed out under concurrent machine load after the child
  unittest process had already reported 69/69 `OK`; this was not accepted as the
  final gate.
- Clean full rerun completed normally: 69/69 PASS with
  `SIMPLIFIED_ACTIVE_SUITE=PASS`.

Next: perform final semantic/diff review, commit the bounded CADS correction, push
`master`, and freeze this concern-coverage design unless new project evidence
meets the existing Freeze Rule.