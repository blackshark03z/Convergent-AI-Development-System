# Goal

Make material CADS research durable against normal technology churn: when research can shape a long-lived or costly-to-reverse direction, require reasoning that accounts for current reality, credible industry/technology trajectory, durable capabilities/invariants, volatile implementation choices, replacement/portability cost and explicit revisit triggers, without creating a new control, phase, lifecycle, skill or mandatory artifact.

Preserve the canonical five-control model:

`Reality -> Intent / Design -> Change -> Acceptance -> Consequence`

# Critical User Journey

AI Tech Lead encounters a material knowledge gap -> inspects current reality and performs targeted research -> separates what the product/system must durably preserve from today's replaceable technology choices -> considers credible industry/technology direction and replacement cost -> chooses the smallest current solution that preserves appropriate optionality -> persists material rationale/revisit triggers through existing Decision Continuity when needed -> implementation proceeds without adding research ceremony to cheap reversible questions.

# Acceptance

- `skills/core/product-goal-framing.md` makes material targeted research trajectory-aware while explicitly preserving a fast path for cheap/local/reversible questions.
- Material research distinguishes dated current evidence from durable capabilities/invariants and volatile models/providers/frameworks/APIs/products.
- Material choices consider credible industry/technology trajectory as uncertain evidence, not prediction-as-fact.
- Material choices consider replacement/portability cost and prefer capability/property/invariant-level commitments over unnecessary vendor/model/tool lock-in.
- Material research produces concrete evidence/context revisit triggers when the decision should survive task/chat turnover.
- `skills/core/architecture-description.md` applies the same durability semantics to architecturally significant technology choices only when expected lifetime or replacement cost is material.
- `docs/DECISION_CONTINUITY.md` preserves durable reasoning without freezing forecasts or requiring decisions to be reopened merely because time passed.
- `README.md` makes the rule discoverable from the existing knowledge-gap path.
- No sixth CADS control, new phase, lifecycle, skill, artifact family, research database, forecast registry or mandatory research document.
- `docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md` remains unchanged.
- Focused regression and full `python scripts/self_test.py` pass with `SIMPLIFIED_ACTIVE_SUITE=PASS`; `git diff --check` passes.

# Non-goals

No universal 1-3 year forecast for every question; no mandatory trend report; no fixed research horizon; no required vendor comparison count; no speculative future architecture; no technology prediction presented as fact; no new research skill/process/runtime; no unrelated cleanup.

# Constraints

Research depth scales with consequence, irreversibility and replacement cost. Current reality remains the starting point. Industry/technology trajectory informs optionality and revisit conditions but does not override observed source/runtime evidence or justify speculative architecture.

# Material Decisions

- Treat research durability as a quality property of existing knowledge-gap, architecture and Decision Continuity methods, not a sixth control or research phase.
- Express durable decisions primarily as capabilities/properties/invariants; named technologies remain replaceable realizations unless intentionally part of the material constraint.
- Preserve forecasts as uncertain evidence and concrete revisit triggers, never as durable future facts.
- Keep small/reversible research questions cheap.

# Progress / Discoveries / Next

- Start HEAD: `75c2f69b0616ad075e33729e1aa8de28fbbd2b40`.
- Isolated branch/worktree: `codex/research-durability`.
- Focused research/architecture/bootstrap regression: 21/21 PASS.
- Full CADS regression: 111/111 PASS with `SIMPLIFIED_ACTIVE_SUITE=PASS`.
- `git diff --check`: PASS.
- Frozen Standard diff: empty.
- No new file, skill, control, phase, lifecycle or artifact family introduced.

Next: apply this durability rule to future material research; revisit the method only if evidence shows it adds ceremony without preserving useful reasoning or fails to prevent technology lock-in/stale decisions.