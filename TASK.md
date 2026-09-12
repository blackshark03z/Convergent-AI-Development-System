# Goal

Strengthen CADS project-level architecture legibility without changing the Five Controls or frozen Standard: make durable system shape, architecture drivers, technology/framework choices, runtime/state/deployment boundaries and material trade-offs reconstructable by a fresh AI, while keeping the method proportional and conditional.

# Critical User Journey

A fresh AI Tech Lead opens a CADS project -> reads the project `ARCHITECTURE.md` -> can reconstruct the actual system boundary, material architecture drivers, chosen technologies/frameworks, major building blocks, critical runtime flows, state/authority ownership, deployment/trust boundaries and stable invariants -> can tell which decisions are durable versus task-local -> changes architecture only after proportionate scenario/evidence review rather than guessing from implementation fragments.

# Acceptance

- Replace the project architecture template with a lean Architecture Description profile that is explicit about purpose/scope, concerns, architecture drivers, technology choices, structure, runtime, state/authority, deployment, trust boundaries, invariants, trade-offs and revisit triggers.
- Add one conditional `skills/core/architecture-description.md` playbook; it must not create a lifecycle phase, approval gate, architecture database or mandatory diagram set.
- Product / Design Framing must turn material design concerns into architecture drivers and route material architecture description/evaluation to the new playbook when needed.
- Root and project-template `AGENTS.md` must make the conditional routing discoverable without making it a universal phase.
- Material framework/technology choices must record role, choice, rationale and a revisit trigger when the choice is architecturally significant; CADS must not mandate a universal FE/BE/database stack.
- Architecture evaluation remains lightweight and scenario-based: driver -> decision -> expected property/scenario -> evidence/risk/trade-off.
- Architecture views are concern-driven and optional: context, building blocks, runtime, data/state/authority, deployment and trust/security only when they answer a material concern.
- Preserve the existing Five Controls and frozen Standard; do not add runtime/process state.
- Add focused tests and keep the full CADS regression suite passing without weakening existing tests.

# Acceptance Fixture / Evidence Basis

1. A small local personal tool may omit irrelevant deployment/security views and choose a simple stack without ceremony.
2. A user-facing FE+BE product records the actual frontend/backend/data/runtime technology choices and why/revisit-when, rather than CADS prescribing React/FastAPI/Postgres.
3. A repeated asynchronous workflow records runtime flow, snapshot/state ownership and stale-context prevention where material.
4. A framework replacement that materially changes deployment, interfaces or maintainability is represented as a material architecture decision and DR when rationale must survive turnover.
5. A fresh AI can answer “what is the FE, BE, data store, runtime topology and state owner?” from architecture truth when those concepts exist in the project.
6. Architecture documentation cannot be treated as aspirational truth when Git/runtime contradict it.

# Non-goals

No sixth CADS control, architecture lifecycle, mandatory V-model/MBSE/SysML/UML/C4/arc42 adoption, architecture approval board, technology catalog, universal frontend/backend framework, service decomposition mandate, architecture database, model router, MAR change or Standard amendment.

# Constraints

Preserve `Reality -> Intent / Design -> Change -> Acceptance -> Consequence`, DR-0003 anti-accretion, DR-0004 trusted-evidence boundaries, Decision Continuity and Knowledge-Gap Responsibility. Use relevant systems/software architecture practices as semantic guidance rather than importing their full ceremony. Architecture docs describe current durable truth; transient implementation progress remains in `TASK.md`.

# Material Decisions

- Keep CADS core architecture unchanged; strengthen only project architecture description/evaluation.
- Use a lean concern-driven profile influenced by ISO/IEC/IEEE 42010/42030 semantics, systems/software lifecycle standards, quality-attribute/scenario practice, arc42 and C4, without mandating those frameworks.
- Architecture drivers are the small set of material quality attributes/constraints that shape design; they are not a checklist of every possible quality attribute.
- Technology/framework selection remains an AI Tech Lead engineering decision within Owner intent/constraints unless it creates an Owner-controlled material product trade-off.
- Material accepted rationale belongs in Decision Records; `ARCHITECTURE.md` holds current durable structure, not decision history.

# Progress / Discoveries / Next

- Research comparison found CADS already strong in Goal/CUJ, concern coverage, authority/state reasoning, V&V, trusted evidence and decision continuity.
- The material gap was project architecture description/legibility: the previous template was too thin to reliably expose architecture drivers, technology/framework rationale, runtime/deployment views and quality-scenario fitness to a fresh AI.
- Added the lean Architecture Description profile, conditional architecture skill, Product / Design Framing routing, activation wiring, research note and DR-0005; no runtime or Standard change was introduced.
- First full regression exposed one compatibility issue: the stronger template had renamed canonical bootstrap headings such as `# Components`. The implementation was corrected to preserve those existing headings while retaining the richer semantics; no test was weakened.
- Focused architecture/compatibility tests: 5/5 PASS; `git diff --check` PASS.
- Full CADS regression: 93/93 PASS with `SIMPLIFIED_ACTIVE_SUITE=PASS`.

Next: review the bounded final diff, commit/push this Goal if only intended documentation/skill/template/test paths changed, then use the profile in real CADS projects and let production evidence determine whether any viewpoint needs future strengthening.
