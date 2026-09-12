# CADS Project Architecture Research — September 2026

Status: Research synthesis
Date: 2026-09-12
Scope: project-level systems/software architecture description and evaluation

## Question

Does CADS need a different development architecture/process after comparison with systems engineering and software architecture practice, or is the current Five-Control model sound and only the project architecture contract needs strengthening?

## Sources reviewed

The comparison used current CADS Standard/playbooks/Decision Records plus representative external references:

- ISO/IEC/IEEE 15288:2023 — system life cycle processes;
- ISO/IEC/IEEE 12207:2026 — software life cycle processes;
- ISO/IEC/IEEE 42010 — architecture description;
- ISO/IEC/IEEE 42020 / 42030 — architecture processes/evaluation;
- ISO/IEC 25010:2023 — product quality model;
- SEI architecture quality-attribute / ATAM practice;
- arc42 architecture documentation structure;
- C4 model architecture views;
- NIST SP 800-218 Secure Software Development Framework.

These are used as semantic references, not certifications or mandates to import their full process.

## Finding 1 — Keep the CADS control architecture

The external standards define concerns/processes but do not require CADS to adopt one persisted lifecycle, V-model, task database or universal sequence. CADS already covers the important engineering semantics through `Reality -> Intent / Design -> Change -> Acceptance -> Consequence`, conditional specialist methods, independent acceptance, source-of-truth precedence and evidence-bound completion.

Verdict: **KEEP** the Five Controls and frozen Standard. Do not add a sixth Architecture phase.

## Finding 2 — CADS already has strong systems-engineering reasoning

Product / Design Framing already covers Goal/CUJ, domain identity/ownership, persistent and asynchronous state, source of truth, consistency/migration/recovery, security/external effects, concurrency/fencing, runtime/config identity, observability, quality/economy and assumption attack. Decision Continuity preserves material rationale. Trusted Evidence and Product Acceptance provide V&V semantics.

Verdict: **ALREADY SOLVED / STRONG** at reasoning level.

## Finding 3 — Project architecture description is under-specified

The existing project `ARCHITECTURE.md` template names useful sections but is too thin to reliably let a fresh AI reconstruct:

- which stakeholder/engineering concerns actually shaped architecture;
- the top quality attributes/constraints (architecture drivers);
- architecturally significant frontend/backend/worker/store/provider/framework choices and rationale;
- current system context and building-block ownership;
- critical runtime/recovery flows;
- data/state/authority and snapshot/lifetime semantics;
- deployment/runtime topology;
- trust/external boundaries;
- architecture fitness scenarios, risks and revisit triggers.

This is the main gap exposed by the practical question “what is the FE, BE, framework, state owner and runtime topology?”

Verdict: **STRENGTHEN**, not redesign.

## Finding 4 — Use concern-driven views, not mandatory diagrams

ISO 42010-style viewpoints are useful because they connect architecture descriptions to concerns. C4 context/container ideas and arc42's building-block/runtime/deployment/quality organization are useful lightweight projections. CADS should borrow the semantics while keeping the representation optional: prose/table/diagram according to the concern.

No project must produce UML, SysML, C4 or every arc42 section. Small personal tools should remain small.

## Finding 5 — Make architecture drivers explicit

The current framing contains quality/economy reasoning but leaves the relation between quality attributes and architecture implicit. Projects should expose the small set of quality attributes/constraints that materially drive design, preferably through observable scenarios when useful.

Examples include reliability, recoverability, usability, security, performance, maintainability, interoperability, operability, scale and cost. This is not permission to copy the whole ISO 25010 quality model into every project.

## Finding 6 — Technology/framework selection belongs to project architecture

CADS should not prescribe one frontend/backend/database stack. The AI Tech Lead selects technology from Goal, constraints, drivers, existing source and operating environment. Architecturally significant choices should record:

`role -> choice -> why -> trade-off -> revisit trigger`.

Owner input is required only when the choice changes an Owner-controlled product outcome, material business trade-off or consequential authority.

## Finding 7 — Add lightweight architecture fitness, not a review ceremony

Full architecture evaluation workshops would be disproportionate for the target 1 Owner + AI model. The useful minimum is a scenario/evidence relation:

`driver -> architecture decision -> expected property/scenario -> evidence/risk/trade-off`.

This connects architecture directly to CADS Acceptance and Trusted Evidence without creating another process runtime.

## Decision

Adopt a **Lean Project Architecture Description Profile**:

1. strengthen `templates/project/ARCHITECTURE.md`;
2. add one conditional `architecture-description.md` skill under Intent / Design;
3. route material architecture drivers from Product / Design Framing into that skill;
4. preserve material rationale through Decision Continuity;
5. add focused regression tests so future simplification does not erase architecture legibility.

Do not amend the frozen Standard for this change. Revisit the Standard only if repeated real-project evidence satisfies its Freeze Rule.

## Do not add

- a sixth CADS Architecture phase;
- a persisted architecture workflow/status database;
- mandatory C4/arc42/UML/SysML/MBSE artifacts;
- architecture approval boards or fixed review gates;
- a universal FE/BE/database framework stack;
- automatic service/microservice decomposition;
- documentation that overrides contradictory Git/runtime evidence.

## Evaluation / revisit criteria

Shrink the profile if it creates recurring documentation cost without reducing Owner re-explanation, architecture drift, state/boundary mistakes or onboarding/context-reconstruction time. Strengthen a specific viewpoint only when real project failures show the current description cannot expose a material concern early enough.
