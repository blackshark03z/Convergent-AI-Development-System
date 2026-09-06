# Product Goal Framing

An advisory procedure for turning owner intent into one bounded Product Goal
before implementation expands. It creates no lifecycle state or project
authority.

Use the canonical development semantics in
`docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`. This playbook operationalizes
Goal-defined acceptance; it does not redefine the Standard.

## When to use

Use when:

- starting a new product or materially new Product Goal;
- owner requirements materially change;
- acceptance is missing, ambiguous, or no longer matches owner intent; or
- implementation is about to begin without a clear real-user path.

If project context itself is unknown or stale, run `project-cold-start.md`
first.

## Frame the Goal

1. State one bounded owner outcome in user-observable terms.
2. Define the shortest Critical User Journey (CUJ) that proves the outcome.
3. Select one representative real acceptance fixture / golden input when the
   product has meaningful input or state. Prefer reusing the same fixture
   through the journey instead of proving isolated subsystems on unrelated
   fixtures.
4. Define observable acceptance before implementation. Include the final output
   or behavior, not merely test, commit, build, or subsystem success.
5. State non-goals and constraints that prevent adjacent technical work from
   silently becoming part of the Goal.
6. Identify only the authority/state boundaries material to this Goal: source,
   runtime, configuration, data and consequential external effects when
   relevant.
7. Choose rigor proportional to consequence. Personal/local tools still need
   correct acceptance and data safety; they do not automatically need
   enterprise lifecycle machinery.

## Acceptance rules

Acceptance must be independently observable and must not be weakened post hoc
merely to make an implementation pass. Tests are verification evidence, not the
acceptance oracle unless the Goal itself is explicitly test-only.

For user-facing work, the CUJ should normally express what the owner actually
does from entry to useful result. Hidden, unreachable, or technically present
capability does not satisfy a user-visible acceptance criterion.

Do not invent detailed architecture before current source has been inspected.
The Goal constrains implementation; it does not prescribe unnecessary new
subsystems.

## Context update

When authorized, keep the minimum current Goal context in `TASK.md`:

- Goal;
- Critical User Journey;
- Acceptance;
- Acceptance Fixture / Golden Input, when applicable;
- Non-goals;
- Constraints; and
- material owner/Tech Lead decisions.

Do not add task IDs, lifecycle stages, schemas, persisted status or a planning
database around this procedure.

## Result contract

Return one concise result:

- `GOAL_READY`: the owner outcome, CUJ, acceptance and boundaries are clear
  enough for bounded implementation; or
- `OWNER_INPUT_REQUIRED`: a material product decision cannot be recovered from
  repository/current evidence. Ask only for that missing decision.
