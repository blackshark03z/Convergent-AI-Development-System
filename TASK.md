# Goal

Make CADS vNext operationally prefer the ChatCode-like direct coding path while
keeping durable governance conditional on concrete execution properties.

Preserve the canonical five-control model:

`Reality -> Intent / Design -> Change -> Acceptance -> Consequence`

# Critical User Journey

Tech Lead receives a Goal -> reconstructs current reality -> compiles a
goal-specific Design Baseline only when material ambiguity justifies it -> names
only execution properties the Goal actually requires -> routes ordinary work
directly to a compatible coding harness -> obtains a candidate -> independently
attacks the candidate against the predefined acceptance -> uses a governed runtime
such as MAR only when required properties justify it.

# Acceptance

- A read-only `python scripts/ai.py route` command returns `DIRECT` when no
  governed runtime property is declared.
- Declaring any supported runtime property returns `GOVERNED`; properties are
  deterministic, deduplicated and no route call persists lifecycle state or grants
  authority.
- The supported property set covers isolated mutation, durable recovery,
  concurrent-writer fencing, durable execution authority, resource governance and
  crash-safe integration.
- Architecture/Decision truth states that MAR is an optional governed substrate,
  not the default CADS coding path.
- The Design Baseline template carries optional execution-substrate requirements
  without naming one mandatory harness.
- Product Acceptance explicitly attacks the candidate independently of the
  Worker's completion narrative and does not require a second model universally.
- Focused routing/contract tests pass, then the full active CADS self-test passes.
- `docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md` remains unchanged.

# Non-goals

No sixth CADS control. Do not add a task lifecycle, routing database, policy engine,
numeric risk score, model/provider router, agent runtime, session manager,
subagent framework, automatic danger classifier or mandatory MAR path. Do not
make OpenSpec, Spec Kit, ChatCode, Codex, Claude Code, OMP or MAR a permanent CADS
semantic dependency.

# Constraints

- Preserve the five-control CADS model and existing repository-context contract.
- Keep routing derived/read-only: it may not grant authority or persist execution state.
- Keep the execution harness replaceable; route on required properties, not vendor identity.
- Preserve the frozen Convergent AI Development Standard unchanged in this slice.

# Material Decisions

- Design heavy, execution light, acceptance independent, governance conditional.
- Direct execution is the default when no material runtime property requires a
  governed substrate.
- Governed routing is property-based and harness-neutral.
- Consequential effects still use the CADS Consequence boundary regardless of
  execution route.
- Independence belongs to the oracle/evidence, not automatically to reviewer
  count or model count.
- MAR may implement governed execution properties but may not redefine CADS
  intent/design/acceptance semantics.

# Progress / Discoveries / Next

- Start HEAD: `e4a62632872ac5610667d013dae3d1d41a6599e4`.
- DR-0011/DR-0012 already provide adaptive control and replaceable Design
  Compilation; this slice operationalizes the missing execution-routing and
  acceptance-independence boundary.
- Next: implement route helper + docs/contracts, run focused/full verification,
  integrate, then align MAR's own roadmap/README with its optional-kernel role.
