# Goal

Evolve CADS so current and future AI capability improvements can translate into more verified autonomy without turning today's compensating mechanisms into permanent constraints.

Preserve the canonical five-control model:

`Reality -> Intent / Design -> Change -> Acceptance -> Consequence`

The target layering is:

`durable semantic invariants -> adaptive assurance -> removable capability scaffolding`

Owner burden should shrink as demonstrated AI/tool capability and evidence quality improve. Autonomy may contract again when capability or evidence regresses; it is a reversible evidence-calibrated envelope, not a one-way ratchet.

# Critical User Journey

Tech Lead/Worker receives a Goal -> reconstructs current reality and durable semantic obligations -> selects the lightest assurance justified by risk and available evidence -> uses or removes capability scaffolding according to its current trigger -> executes through any compatible harness/protocol/topology -> verifies the same intent/authority/acceptance/consequence semantics -> asks the Owner only for genuinely subjective product judgement or consequential authority.

# Acceptance

- `evals/autonomy/cases.json` contains AE-027..AE-035, bringing the representative suite to exactly 35 cases.
- The nine cases cover capability obstruction, harness semantic lock-in, Owner-burden stagnation, protocol lock-in, execution-topology lock-in, stale capability scaffolding, autonomy contraction/re-expansion after capability regression, correlated generator/verifier blind spots, and runtime/CADS semantic-contract mismatch.
- `scripts/validate_autonomy_evals.py` admits up to 35 cases and requires all new failure classes while retaining existing fail-closed schema, risk, oracle and human-attention checks.
- Existing autonomy regression tests are updated to the 35-case contract and continue to reject forbidden runtime/model trust state.
- `ARCHITECTURE.md` states the durable-semantic-invariants / adaptive-assurance / removable-capability-scaffolding model and the reversible evidence-calibrated autonomy envelope.
- Existing `docs/CADS_AUTONOMY_EVAL_SUITE.md` reflects the 35-case suite without creating a new artifact family.
- `docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md` remains unchanged.
- Focused autonomy validation passes and MAR `python-portable` verification passes.

# Non-goals

No sixth CADS control is introduced. Do not create a new CADS control, lifecycle, workflow state, task database, model router, context governor, policy engine, protocol, execution topology or persistent autonomy controller. Do not add a new skill or artifact family. Do not implement a new agent runtime, benchmark runner, embeddings/vector DB, multi-agent orchestrator or remote cache. Do not change the frozen canonical Standard.

# Constraints

Capability is demonstrated by task-relevant evidence, not model branding, vendor tier or a permanently trusted harness. Semantic invariants outlive current implementation mechanisms. Assurance may strengthen or weaken with evidence; scaffolding must have a material trigger and remain removable. Product judgement and consequential authority remain Owner boundaries even as routine engineering attention shrinks.

# Material Decisions

- Preserve semantics, not today's harness mechanics.
- Treat capability scaffolding as conditional and removable, never as an automatic permanent layer.
- Use a reversible evidence-calibrated autonomy envelope: expand when evidence supports it; contract when capability/evidence regresses; re-expand when evidence recovers.
- Do not require independent reviewers or extra models universally; seek materially diverse evidence when correlation risk can invalidate the oracle.
- Runtime/MAR may execute CADS semantics but must not redefine CADS intent, authority, acceptance or consequence boundaries.
- Keep the canonical five-control model unchanged.

# Progress / Discoveries / Next

- Start HEAD: `a30b1311a9caf642a72c4de8ae42c5382cf72152`.
- MAR runtime `local-6b28ea160b9e` recognizes CADS as mixed `artifact + python` and recommends `python-portable`.
- This slice uses corrected `python-portable`: changed `tests/**/test_*.py` from candidate diff plus compileall, with evidence bound to the effective verification plan.
- Planned delta is limited to the existing autonomy dataset, validator/test coverage, architecture clarification, eval-suite documentation and this TASK.md.
- Verification target: focused autonomy validator/tests plus authoritative MAR `python-portable`; canonical Standard remains unchanged.

Next: complete AE-027..AE-035, verify and integrate, then use the expanded suite to challenge future CADS/MAR autonomy changes without freezing current AI limitations into architecture.
