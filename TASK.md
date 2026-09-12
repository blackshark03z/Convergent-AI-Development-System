# Goal

Preserve the September 2026 AI-autonomy research and independent red-team result
as repository truth, correct the Product Acceptance Owner gate to match the
existing Standard, and define a bounded implementation/evaluation path for
trusted evidence without adding another CADS runtime or changing the frozen
Standard.

# Critical User Journey

Fresh Tech Lead reads the decision index -> understands B-prime responsibility
boundaries and what remains only a candidate -> applies Product Acceptance
without unnecessary Owner ceremony -> can implement/evaluate Evidence Envelope,
Oracle Integrity and MAR boundary changes from an explicit plan -> promotes only
mechanisms that improve verified autonomy on representative Goals.

# Acceptance

- A durable research note records the internal review, third-party red-team
  corrections, external research references, B-prime responsibility boundary,
  do-not-build list and kill/revisit criteria.
- DR-0004 records the accepted architecture direction without adding a sixth
  control or amending the Standard.
- `docs/decisions/README.md` exposes DR-0004 as active.
- Product Acceptance aligns with the Standard: Owner real-use is required only
  where subjective human experience/judgement is part of the oracle; fully
  machine-observable user-facing Goals do not require ceremonial Owner UAT.
- Product Acceptance makes post-implementation oracle weakening/self-proof
  explicit enough to reject unsupported PASS while allowing legitimate oracle
  clarification/regression additions.
- An implementation plan defines Evidence Envelope/Oracle Integrity as an
  evaluated candidate, a representative autonomy eval suite, a MAR authority
  boundary audit, later conditional fresh review/parallel candidates, metrics
  and kill criteria.
- No task database, phase lifecycle, model router, permanent agent organization,
  context database or Standard amendment is introduced.

# Acceptance Fixture / Evidence Basis

Desk-review the updated material against these cases:

1. Objective user-facing Goal: a predefined end-to-end browser/runtime oracle
   objectively proves the journey and output; no subjective criterion remains.
   Expected: autonomous `PRODUCT_ACCEPTED` is allowed.
2. Subjective UX Goal: engineering/runtime evidence passes but intended user
   judgement such as usability/taste remains part of predefined acceptance.
   Expected: `PRODUCT_READY_FOR_OWNER_ACCEPTANCE`, not synthetic AI acceptance.
3. Oracle mutation: implementation changes a test/acceptance artifact and then
   cites only the changed artifact as proof. Expected: no independent PASS unless
   the oracle change is a legitimate explicit clarification/new regression and
   the criterion remains independently valid.
4. Parallel candidates: isolated Workers produce candidates independently.
   Expected: parallel candidate creation is not forbidden, but exactly one
   integration authority advances canonical state.
5. Vendor capability: a harness already provides an isolation/context/subagent
   mechanism with adequate guarantees. Expected: CADS/MAR may rely on/verify the
   guarantee rather than automatically reimplement it.

# Non-goals

No Evidence Envelope runtime implementation in this documentation Goal. No MAR
code mutation. No Standard v1.0 amendment. No always-on reviewer, agent swarm,
model trust tier, generic context service or broad cleanup.

# Constraints

Preserve DR-0003's five-control/anti-accretion direction and the Standard Freeze
Rule. Keep the canonical control sequence explicit:
`Reality -> Intent / Design -> Change -> Acceptance -> Consequence`.
Distinguish accepted architecture direction from mechanisms still pending
representative evaluation. Agent/vendor reports remain claims unless backed by
relevant evidence.

# Material Decisions

- Accept DR-0004: CADS owns engineering semantics; model/harness owns intelligence
  and ordinary orchestration; project runtime/CI owns product-specific oracles;
  MAR/integration authority owns only missing portable guarantees and canonical/
  consequential authority.
- Use "trusted evidence" rather than plain evidence for technical completion.
- Prefer "single canonical integration authority" over "single writer";
  parallel isolated candidates remain optional/conditional.
- Autonomy should be eval-gated rather than granted by model name or online
  short-term success.

# Progress / Discoveries / Next

- Live repository baseline inspected at master
  `e641af3f75b408926a589d7f4de762e6a892330b`.
- Current Standard, Product Acceptance, DR-0003 and decision index reviewed.
- Internal autonomy review and independent `MODIFY_DIRECTION` red-team result
  reconciled into the B-prime direction.
- Documentation candidate applied to the live checkout: research synthesis,
  DR-0004, implementation plan, Product Acceptance correction and active decision
  index update.
- Initial verification exposed missing cold-start activation literals in this
  `TASK.md`; the task context was corrected without weakening or changing the
  existing test contract.
- No Standard amendment is proposed. The final candidate remains gated by
  `git diff --check` and `python scripts/self_test.py`; execution evidence is
  reported from the exact final candidate rather than promoted into a durable
  architecture decision.

Next: after this documentation candidate is integrated, execute Workstream 1 as
a bounded prototype/eval Goal. Do not promote Evidence Envelope or new MAR
responsibility until representative evidence meets the promotion rule.
