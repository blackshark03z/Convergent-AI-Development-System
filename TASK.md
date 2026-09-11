# Goal

Clarify change-impact analysis inside existing CADS Goal Execution and route
root-cause fixes through that same scope check, without another contract layer.

# Critical User Journey

Worker identifies intended behavior/assumption delta -> traces evidenced affected
dependencies -> chooses changes and preservation checks -> implements and verifies
that bounded scope -> resumes the original product journey.

# Acceptance

- Goal Execution checks direct/indirect dependencies before choosing edits and
  selects regression from affected behavior, not just changed files.
- Related components may remain unchanged with a reason/evidence; dependency
  tracing stops where the relevant contract remains intact. Material uncertainty
  is resolved or reported, not disguised as exhaustive coverage.
- Keep existing reuse/authoritative-path/duplicate-implementation questions,
  stateful-handoff examples, Product Acceptance and effect/Owner boundaries.
- Systematic Debugging references the same scope check before applying a fix.
- Keep Reality -> Intent / Design -> Change -> Acceptance -> Consequence.
- Review proportionality against the three scenarios below and run the existing
  CADS suite. These checks do not prove agent behavior or standards certification.

# Acceptance Fixture / Evidence Basis

Desk-review scenarios, not newly executed product tests:

1. Display-label correction: inspect affected presentation and verify it; no
   automatic persistence, renderer or migration audit without a dependency.
2. Shared-state interpretation bug: inspect consumers of the relevant meaning;
   retain valid uses of raw counts. Keep the existing Story Audio approved-review
   handoff example and transition-versus-reopening evidence distinction.
3. Configuration-scope change (hypothetical): consider evidenced storage/readers,
   snapshot boundaries and existing-data compatibility; verify new behavior and
   preservation of historical jobs rather than editing every related component.

Engineering reference: NASA SWE-080, Track and Evaluate Changes, describes
impact evaluation and proportional treatment for small projects:
https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695459/SWE-080%2B-%2BTrack%2Band%2BEvaluate%2BChanges
This is a reference for the approach, not a claim of NASA/ISO compliance.

# Non-goals

No new skill, phase, impact schema/document, test that merely matches new prose,
Standard amendment, general cleanup, Story Audio mutation or provider call.
No agent-behavior benchmark or downstream rollout in this task.

# Constraints

Preserve owner work, existing cold-start headings and concrete handoff coverage.
The affected playbooks own analysis and routing respectively; acceptance owns
verification semantics. Avoid copying the same checklist across procedures.

# Material Decisions

Owner authorized this bounded refinement after reviewing lighter alternatives.
Apply DR-0003's existing-control refinement rule: extend existing scope questions
and add one debugging reference; preserve the existing five questions and handoff
section rather than rewrite the architecture or introduce another contract.

# Progress / Discoveries / Next

- Baseline: clean master at 0dcab3002cb78269141b1c12691531f8da4251bb.
- Existing playbooks inspected: scope questions already address excessive and
  duplicate changes; the refinement adds evidenced dependency coverage and
  preservation-based regression selection at the implementation decision point.
- Modified Goal Execution, Systematic Debugging and this current task context.
- Desk review against all three scenarios found proportional scope: a label
  does not imply data migration; a shared-state fix inspects semantic consumers
  without replacing valid raw-count uses; a scope change includes implicated
  compatibility and historical preservation. This is reasoning review only.
- `python scripts/self_test.py`: 70/70 PASS in 89.015s,
  `SIMPLIFIED_ACTIVE_SUITE=PASS`. No tests were added or weakened.
- Bounded diff reviewed; `git diff --check` PASS. Actual agent effectiveness,
  downstream product behavior and formal standards compliance remain unverified.

Next: Owner has authorized commit/push. Verify the committed candidate and normal
publication from live Git; if origin/master contains this clarification, the CADS
task is complete. Apply the guidance within the next product task's authorized
scope and evaluate whether it catches omissions without unnecessary expansion.
