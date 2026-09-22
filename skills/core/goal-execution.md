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

## Intent Change Impact

Before local patching, when Owner intent or an accepted design decision is
clarified, extended or revised during execution:

1. identify which previously established behavior or assumptions are affected;
2. inspect impact on the affected CUJ, behavioral/system flow, state/data/
   authority, architecture contract, and acceptance criteria/oracles;
3. reopen only the affected portions;
4. do not patch the nearest code first;
5. mark affected or uncertain acceptance evidence as needing re-establishment
   where appropriate; and
6. preserve unaffected behavior/evidence when current evidence supports reuse.

Do not rerun or rewrite the whole project or every design artifact after each
intent change. The purpose is bounded propagation before implementation, not a
new phase or impact registry.

## Accepted Product Contract Continuity

When current work touches behavior that was already accepted, frozen or otherwise
established as part of the Product Goal, treat that behavior as `MUST-PRESERVE`
unless a legitimate Intent/Design change explicitly supersedes it. Current source,
runtime behavior and tests are authoritative evidence of what the implementation
currently does; they do not silently redefine what the accepted product is
supposed to continue doing.

Before a material change, identify only the accepted behavior obligations that
can actually be affected and give each one a bounded disposition:

- `PRESERVED`: current evidence shows the accepted behavior still composes into
  the required product journey;
- `INTENTIONALLY_CHANGED`: an explicit accepted Intent/Design change supersedes
  the earlier behavior and affected acceptance has been updated accordingly; or
- `UNVERIFIED`: preservation is not yet established, so the affected checkpoint
  or completion claim must remain open.

Use composition-level reasoning when a local component contract is narrower than
the accepted product contract. A subsystem may correctly return a local state
such as authentication-required, creation-required, retry-required or another
handoff condition; if the accepted journey requires the product to consume that
state and continue automatically, component PASS is insufficient until the
responsible orchestrator/consumer and the resulting journey behavior are
verified. Likewise, accepted configuration semantics are not preserved merely
because a reduced subset of fields still parses or has passing tests.

This is semantic-drift detection, not a second requirements system. Keep only the
necessary obligation/disposition with existing task/change notes; do not create a
mandatory contract registry, full-project traceability matrix, new lifecycle or
per-commit end-to-end ceremony. Use the cheapest relevant composition/regression
oracle during execution and the real supported journey at meaningful acceptance
convergence points.

## Worker-ready design and DESIGN_GAP

When an accepted Design Baseline or equivalent goal-specific spec exists, treat it
as compiled product/design input rather than asking the Worker to reconstruct the
whole CADS knowledge base. Reconcile it against current Git/source reality before
editing, then preserve its material obligations while choosing implementation
details locally.

Do not escalate normal code choices. Use `DESIGN_GAP` only when source reality
contradicts an accepted material design obligation or a missing decision could
materially change user-visible behavior, state/data ownership, authority/effects,
load-bearing architecture or the acceptance oracle. Pause only the affected slice,
return the concrete contradiction/missing decision to Design Authority, amend or
supersede the affected baseline, then resume. Do not silently invent material
product semantics and do not reopen unrelated accepted design.

Design depth does not justify giant-bang execution. Continue to build and verify
small coherent slices.

## Execution loop

1. Reconfirm the one active Goal, CUJ, acceptance and current Product HEAD.
2. Inspect the existing implementation before designing additions. Identify the
   behavior or assumption being changed and its affected dependencies using
   Scope and complexity control below. For an affected stateful handoff, clarify
   existing acceptance using the step-handoff guidance before editing.
3. Choose the smallest coherent change that advances the CUJ or removes its
   first real blocker.
4. Prefer, in order:
   - `REUSE` existing authoritative behavior;
   - `WIRE` existing capability into the required journey;
   - `FIX` the current authoritative path;
   - `REPLACE_AND_DELETE` when replacement is genuinely required; then
   - `ADD` only when no adequate authoritative capability exists.
5. Run focused verification for the changed behavior and affected behavior that
   must remain intact, using the impact findings to select relevant regression
   checks. Revisit those findings if implementation exposes another dependency.
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

- What behavior or assumption changes, and which producers, stored data or
  consumers depend on it directly or indirectly, as supported by source/runtime
  evidence rather than merely matching names or files?
- Which affected parts need changes, which remain valid, and what evidence
  verifies the new behavior and the behavior/data that must be preserved?
- What existing code was reused?
- What path is authoritative after this change?
- What became superseded?
- What can be deleted after acceptance?
- Did this create a second implementation of the same responsibility?

Follow dependencies only while the changed assumption can affect their behavior;
stop at a boundary whose relevant contract remains intact with supporting
evidence. Consider configuration, interfaces, tests, documentation and existing
data compatibility when implicated; being related does not mean needing edits.
Resolve or explicitly report uncertainty affecting acceptance or important
invariants; do not claim exhaustive coverage from a list of inspected files.
Keep the necessary findings with existing task/acceptance or change-review
notes, not a new impact document, registry or mandatory full-system audit.

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
