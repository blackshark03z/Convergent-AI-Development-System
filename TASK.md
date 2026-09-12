# Goal

Prototype a deterministic, read-only Evidence Envelope / Oracle Integrity gate
that can derive `VERIFIED`, `NOT_VERIFIED`, or `UNKNOWN` from candidate-bound
acceptance evidence without adding a task lifecycle, database, reviewer role, or
new CADS control.

# Critical User Journey

Tech Lead prepares a repo-local JSON evidence envelope -> CADS validates exact
candidate/provenance, criteria, invariants, oracle integrity, authority and any
required review result -> a deterministic read-only gate derives the technical
verdict -> the same envelope can be used in future autonomy evals without giving
the Worker authority to set its own final verdict.

# Acceptance

- Add a pure Evidence Envelope evaluator with no persistence or lifecycle state.
- Require non-empty Goal reference, base/candidate revision identity and evidence
  provenance (`execution_environment`, `evidence_producer`).
- Each required criterion/invariant uses `PASS | FAIL | UNKNOWN`; PASS without
  relevant evidence cannot become `VERIFIED`.
- Oracle changes are provenance-aware: weakened or implementation-coupled
  self-proof cannot establish PASS; legitimate clarification/regression coverage
  requires the bounded integrity evidence defined by the prototype.
- Required consequential authority and required fresh-review outcomes affect the
  derived verdict without creating a new workflow phase.
- Verdict precedence is deterministic: contradicted/blocked evidence ->
  `NOT_VERIFIED`; otherwise missing/ambiguous/untrusted evidence -> `UNKNOWN`;
  only complete trusted evidence -> `VERIFIED`.
- Reject lifecycle/orchestration fields such as phase/retry/planner/subagent/
  chain-of-thought/session state from the envelope surface.
- Add a read-only `verify-envelope --input <repo-local-json>` CLI path. It must
  reject input outside the declared repository root, return 0 only for VERIFIED,
  and return 2 for NOT_VERIFIED/UNKNOWN/invalid input.
- Add focused unit/CLI tests covering the acceptance cases above and keep the
  existing CADS suite passing without weakening tests.

# Acceptance Fixture / Evidence Basis

1. Objective criterion with candidate identity, independent oracle/verifier and
   evidence -> `VERIFIED`.
2. Declared PASS with no evidence -> `UNKNOWN`.
3. Criterion/invariant FAIL with evidence -> `NOT_VERIFIED`.
4. Candidate changes its oracle and marks it weakened/implementation-coupled ->
   `UNKNOWN`, even if it declares PASS.
5. Legitimate oracle clarification with explicit authorization plus independent
   evidence -> may remain `VERIFIED`.
6. New regression coverage without independent evidence for the criterion ->
   `UNKNOWN` rather than self-proof.
7. Required authority missing -> `UNKNOWN`; explicitly denied -> `NOT_VERIFIED`.
8. Required review with blocking findings -> `NOT_VERIFIED`; required review not
   completed -> `UNKNOWN`.
9. Envelope carrying lifecycle/orchestration state -> invalid/BLOCK.
10. CLI evaluation leaves repository files unchanged and cannot read outside the
    declared root.

# Non-goals

No MAR mutation, task database, persisted envelope ledger, lifecycle state,
online trust score, model router, permanent reviewer, parallel-worker runtime,
external-effect dispatch, Standard amendment or broad cleanup. This Goal does
not claim the Evidence Envelope is ready to become a universal CADS invariant.

# Constraints

Preserve `Reality -> Intent / Design -> Change -> Acceptance -> Consequence`,
DR-0003 anti-accretion, DR-0004 responsibility boundaries and the frozen
Standard. Prefer a small deterministic module and project-native tests. The
prototype must be removable if representative evals show ceremony without a
reliability/Owner-attention benefit.

# Material Decisions

- Evidence Envelope is evidence/provenance, not workflow state.
- Worker-declared PASS is input to evaluation, never final technical authority.
- Oracle integrity is enforced conservatively: a changed oracle cannot be sole
  proof of the implementation that changed it.
- `UNKNOWN` is a first-class outcome for missing authority, review or trustworthy
  evidence; it must not be coerced into PASS.

# Progress / Discoveries / Next

- Research/DR/implementation-plan Goal was integrated and pushed at
  `3a7e890e3c2fe13e624a18b8cba5b17dc390ab93`.
- Implemented a pure `buildos.evidence_envelope` evaluator plus read-only
  `verify-envelope` CLI; no persistence, lifecycle state or additional runtime
  was introduced.
- Oracle Integrity fails closed to `UNKNOWN` for weakened/implementation-coupled
  self-proof and for regression coverage without independent criterion evidence.
- Nested envelope schema is intentionally strict so execution/lifecycle state
  cannot silently accumulate under otherwise valid evidence objects.
- Focused Evidence Envelope suite: 13/13 PASS.
- Full CADS regression on the candidate: 83/83 PASS with
  `SIMPLIFIED_ACTIVE_SUITE=PASS`; `git diff --check` PASS.
- The prototype remains a Workstream 1 candidate, not yet a frozen universal
  CADS invariant. Promotion still depends on representative autonomy evaluation.

Next: review the bounded diff, commit/push this prototype, then move to
Workstream 2 by constructing the first representative CADS Autonomy Eval set
from real failure classes. Do not expand MAR/reviewer/parallel-worker machinery
before that evaluation baseline exists.
