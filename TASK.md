# Goal

Create the first representative CADS Autonomy Eval Suite as a static, model-independent dataset and validator so future CADS/MAR autonomy changes can be compared on real failure classes without adding an eval runtime, task database or trust engine.

# Critical User Journey

Tech Lead selects the canonical eval dataset -> any supported model/harness executes matched cases under a baseline or candidate configuration -> the run records outcome, evidence and Owner-attention/guard metrics outside the dataset -> results can be compared without changing Goal/acceptance semantics or granting authority from model name.

# Acceptance

- Add a canonical static eval dataset with 15–25 representative Goals derived from real failure classes.
- Cover repeated-state leakage, journey composition, runtime/source mismatch, external-effect ambiguity, weak/oracle-integrity cases, decision/context drift, non-converging repair, persistence compatibility, UI discoverability/subjective acceptance, parallel candidate integration/semantic conflict, consequential authority, stale writer, provider fallback, artifact immutability and conditional fresh review.
- Each case declares risk, oracle strength, expected system behavior, expected human-attention boundary, required evidence, failure signals and anti-shortcuts.
- Keep the dataset model/vendor neutral and free of lifecycle state, retry history, planner/subagent/session state or model trust tiers.
- Add a deterministic read-only validator for dataset shape/coverage only. Validator PASS must not claim CADS/model capability.
- Document run metrics and comparison rules, including Owner active-attention minutes, Owner re-explanation load, false-DONE/escaped defects, reopen/rollback, wall-clock/cost and identity-bound evidence coverage.
- Add focused tests that protect representative size/coverage, keep human attention exceptional, and fail closed if execution/policy state is inserted into cases.
- Keep the full CADS regression suite passing without weakening existing tests.

# Acceptance Fixture / Evidence Basis

1. Canonical `evals/autonomy/cases.json` validates and contains exactly 20 unique cases.
2. Required failure-class coverage is present, including objective, subjective and weak-oracle cases plus both low- and high-risk Goals.
3. Most cases expect no Owner attention; subjective judgement and consequential authority remain explicit exceptions.
4. Adding a `phase`, model trust tier or similar execution/policy field to a case causes validator BLOCK.
5. Validation checks dataset integrity only and does not claim a model/CADS configuration passes any scenario.
6. Full `python scripts/self_test.py` remains PASS and `git diff --check` remains clean.

# Non-goals

No eval scheduler/orchestrator, result database, benchmark leaderboard, model router, online trust score, automatic authority promotion, MAR mutation, fresh-review implementation, parallel-worker runtime, Standard amendment or broad cleanup. No claim is made yet that B-prime improves autonomy; this Goal only creates the measurement baseline required to test that claim.

# Constraints

Preserve DR-0003, DR-0004, the frozen Standard and the existing Evidence Envelope candidate. Keep the universal control model `Reality -> Intent / Design -> Change -> Acceptance -> Consequence`; the eval suite is evidence for those controls, not a sixth control or runtime. Keep case definitions reusable and product-agnostic enough to run across supported harnesses while retaining the actual engineering failure semantics. Do not optimize cases to make the current implementation look good.

# Material Decisions

- Eval cases are immutable definitions during a matched comparison; run outputs belong outside the canonical dataset.
- Primary north-star remains verified accepted Goals per Owner active-attention, guarded by defect/reopen/cost/oracle-strength metrics.
- Production telemetry may inform new eval cases but cannot silently modify authority or trust.
- Passing dataset validation is not passing the autonomy eval suite.

# Progress / Discoveries / Next

- Workstream 1 Evidence Envelope prototype is integrated at `d0ffc8a106a653f92b0a0b065c805c63d9dd7106` with fresh full regression 83/83 PASS and `SIMPLIFIED_ACTIVE_SUITE=PASS`.
- Workstream 2 scope is intentionally dataset + validator + tests/docs only; no execution runtime is introduced.
- Canonical validator PASS: 20 cases, 19 failure classes; risk mix HIGH=8 / MEDIUM=9 / LOW=3; expected Owner attention NONE=16 / SUBJECTIVE_JUDGEMENT=2 / AUTHORITY_ONLY=2.
- Focused autonomy eval tests PASS. An initial full run exposed one existing cold-start invariant: current `TASK.md` must keep the Five Controls visible. The task context was corrected rather than weakening that test.
- Fresh full regression after the fix: 89/89 PASS with `SIMPLIFIED_ACTIVE_SUITE=PASS`; `git diff --check` PASS.

Next: review the bounded diff, commit/push this eval baseline, then execute matched baseline-vs-B-prime trials before promoting any further autonomy mechanism or expanding MAR/reviewer/parallel-worker machinery.