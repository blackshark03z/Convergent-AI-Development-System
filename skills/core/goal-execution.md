# Goal Execution

An advisory procedure for implementing one established Product Goal through
small coherent changes while preserving continuity. It creates no task
lifecycle, phase machine or persisted execution state.

Use the canonical development semantics in
`docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`.

## When to use

Use during normal implementation after the Product Goal and acceptance are
clear. If they are not clear, use `product-goal-framing.md` first. For a bug or
regression that blocks the Goal, temporarily use `systematic-debugging.md` and
then resume this same Goal.

## Execution loop

1. Reconfirm the one active Goal, CUJ, acceptance and current Product HEAD.
2. Inspect the existing implementation before designing additions. For a change
   that materially affects handoff between journey steps, clarify the existing
   acceptance using the step-handoff guidance below before editing.
3. Choose the smallest coherent change that advances the CUJ or removes its
   first real blocker.
4. Prefer, in order:
   - `REUSE` existing authoritative behavior;
   - `WIRE` existing capability into the required journey;
   - `FIX` the current authoritative path;
   - `REPLACE_AND_DELETE` when replacement is genuinely required; then
   - `ADD` only when no adequate authoritative capability exists.
5. Run focused verification appropriate to the changed layer.
6. Resume the same real journey / acceptance fixture and find the next blocker.
7. Use broader regression at meaningful convergence points; do not pay full
   suite cost after every small edit unless consequence/risk justifies it.

Internal checkpoints are evidence and continuity aids, not new Goals, phases,
promotion states or product-completion claims.

## Handoff between journey steps

For an affected stateful handoff, establish from the existing domain contract:

- which authoritative state/postcondition means the step is complete;
- what the next step must receive and visibly allow, and what context or
  historical data must remain unchanged; and
- which relevant valid combination of status, counts or other fields could be
  misinterpreted as pending work or permission to proceed.

Record only the necessary Given/When/Then example in the existing acceptance,
or reference an equivalent existing scenario. Reuse the authoritative domain
meaning; do not invent a second completion rule from a convenient UI counter.
If expected behavior is missing or contradictory, resolve that affected part
before implementation using established engineering/Owner responsibilities.

Example from Story Audio: `APPROVED_CURRENT`, `unresolved_count=1`,
`remaining_review_count=0`, `blocks_progress=false` is a valid approved state.
The unresolved-target count does not mean one human review remains. The next
voice-configuration step must be available while book/range and approved data
remain intact. This illustrates field semantics, not a universal status schema.

Use focused verification for the affected handoff, following
`product-acceptance.md`. Reuse coverage where adequate; do not specify every
button, enumerate unrelated branches, or introduce another contract document,
registry or process phase. Then resume the same journey.

## Scope and complexity control

For every material change be able to answer:

- What existing code was reused?
- What path is authoritative after this change?
- What became superseded?
- What can be deleted after acceptance?
- Did this create a second implementation of the same responsibility?

Do not create a parallel implementation merely to avoid understanding the
current one. Prefer product composition and wiring when the required capability
already exists.

Classify findings only as:

- `BLOCKER`: prevents the current CUJ/acceptance, threatens a must-preserve
  invariant, or is required to make the current fix correct; or
- `DEFERRED_DEBT`: relevant but does not prevent the current Goal.

Technical interest alone is not a blocker.

## Stop-loss

Use any Goal-specific token/time/cost budget declared by the Tech Lead. When a
budget is exhausted, or repeated accepted changes do not measurably advance the
CUJ, stop expansion, checkpoint evidence and re-evaluate the path instead of
continuing to harden because work has already started.

Do not generalize a local fix into a policy subsystem unless repeated evidence,
material consequence, or the Goal itself requires that generalization.

## Decision continuity

When implementation reveals a material trade-off whose loss could make a later
session choose a different architecture, authoritative path, provider/framework,
deliberate non-goal or expensive line of investigation, ensure the accepted
Owner/Tech Lead decision is persisted under `docs/decisions/` using the Decision
Continuity Protocol when available. Do not record routine reversible edits or
turn every checkpoint into a Decision Record.

## Result contract

Continue the same Goal until one of these is true:

- a bounded change is verified and the CUJ can resume (`CHECKPOINT_OK`);
- progress is impossible without a concrete external/owner/material blocker
  (`BLOCKED`); or
- the predefined acceptance appears satisfied and the work is ready for
  `product-acceptance.md`.
