# Goal

Clarify verification of material handoffs between journey steps inside the
existing CADS Goal Execution and Product Acceptance playbooks.

# Critical User Journey

Worker identifies the domain completion condition for an affected handoff ->
clarifies the existing acceptance -> makes the bounded change -> verifies the
action-to-next-step transition and reopening when they can behave differently ->
reports only the supported evidence and resumes the same product journey.

# Acceptance

- Goal Execution identifies authoritative completion state, downstream behavior,
  preserved context/data and relevant valid field combinations before editing.
- Examples belong in existing acceptance or reference existing scenarios; no
  new Journey Contract document, schema, registry, skill or universal control.
- Product Acceptance distinguishes same-session transition evidence from a
  fixture loaded in the completed state, with an adjacent blocked case only
  where relevant. Missing required evidence remains UNVERIFIED.
- Fixture evidence does not establish backend persistence, history preservation,
  real-product acceptance or authorization for production/provider effects.
- Keep `Reality -> Intent / Design -> Change -> Acceptance -> Consequence`,
  the Standard, Thin Guard and Owner authority intact.
- Review the bounded documentation diff and run the existing active CADS suite.
  These checks do not establish actual agent-behavior improvement.

# Acceptance Fixture / Evidence Basis

Story Audio worktree `D:\Youtube\_worktrees\story-audio-product-reconciliation`,
fix commit `4ee75e153911985f743c51625dbe22c07f1ea943`, parent
`91b329743945bfe0fabbe63326128cd5a41a08c7`:

- `story_audio/speaker_state.py` separates unresolved targets from remaining
  human review and supports APPROVED_CURRENT with unresolved_count=1,
  remaining_review_count=0 and blocks_progress=false.
- `ui/app.js` previously used unresolved_count to determine remaining review;
  the fix uses speakerReviewRemainingCount.
- `tests/test_assignment_completed_review_browser.py` loads the approved state
  and checks rendering; it does not perform the final review-save transition.
- This is an existing-requirement implementation/coverage failure, not evidence
  that a new CADS lifecycle or universal specification layer is needed.

# Non-goals

No Story Audio source/runtime/DB changes, provider calls, production replay,
agent benchmark, unrelated CADS cleanup, Standard amendment or automatic rollout
to other projects. No new tests that merely match prose.

# Constraints

Preserve owner work and existing cold-start context headings. Refine only the
affected handoff checks; ordinary changes do not incur a new mandatory phase.

# Material Decisions

Owner authorized the bounded playbook clarification on 2026-09-11. This applies
DR-0003's rule to refine an existing control after a concrete failure; it does
not introduce a new architecture or supersede that Decision Record.

# Progress / Discoveries / Next

- Baseline: clean CADS master at a3e24a1d28cea2a4ad0ee956dfa13ca2a2d211f5.
- Previous five-control consolidation is already committed at that HEAD; the old
  TASK instruction to commit it was stale. A fresh fetch on 2026-09-11 confirmed
  origin/master also at that baseline before publishing this clarification.
- Updated only Goal Execution, Product Acceptance and this current task context.
- 2026-09-11: `python scripts/self_test.py` ran 70 tests in 82.419s: 69 passed;
  the cold-start test failed because this task rewrite omitted its expected
  context headings. Restored those headings and the five-control reminder;
  no test or acceptance rule was weakened.
- After that task-only correction, `python -m unittest discover -s tests -p
  test_end_to_end.py -v` passed 4/4 in 3.885s, including the failed cold-start
  check. The other 66 checks passed in the full run; the full suite was not
  repeated after the context correction.
- Bounded playbook diff reviewed; `git diff --check` passes. Only these three
  documentation files are modified. Actual agent behavior and Story Audio's
  full journey remain unverified by this task.
- Owner authorized commit/push/merge on 2026-09-11. Baseline local/remote master
  matched, so no merge was needed at that check. Publication verification will
  run the full suite at the committed candidate and compare the remote commit
  and tree after a normal push; consult live Git for the publication outcome.

# Next Safe Action

Next: reconcile publication from live Git rather than repeating a stale release
instruction: if the clarification is absent from origin/master, finish the
authorized publication after candidate checks; if present, this CADS task is
complete. Resume product work only within that project's established scope.
This documentation update does not establish downstream product acceptance.
