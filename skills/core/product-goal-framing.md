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

## Knowledge-gap responsibility

The Owner is not expected to supply missing engineering expertise. The AI Tech
Lead must investigate material engineering concerns using the Goal, repository,
runtime evidence, and supported operating context, and resolve ordinary
engineering choices within established intent and authority. Ask the Owner only
for missing product facts, material trade-offs, or consequential choices that
change owner-controlled outcomes and cannot reasonably be recovered or inferred.
Translate technical choices into observable consequences. Where a material
technical uncertainty remains, obtain proportionate evidence or restrict the
affected action; do not ask the Owner to certify a technical fact.

## Frame the Goal

1. State one bounded owner outcome in user-observable terms.
2. Define the shortest Critical User Journey (CUJ) that proves the outcome. For
   a multi-step user-facing Goal, make it a representative full journey across
   the capabilities that compose the outcome, not merely a feature list.
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
7. Apply the Decision Continuity materiality test. If an Owner/Tech Lead choice
   here would materially change a later session's scope, approach, acceptance,
   architecture, authoritative path or expensive research, persist it under
   `docs/decisions/` rather than leaving it only in chat. Use
   `docs/DECISION_CONTINUITY.md` when available.
8. Choose rigor proportional to consequence. Personal/local tools still need
   correct acceptance and data safety; they do not automatically need
   enterprise lifecycle machinery.

## Acceptance rules

Acceptance must be independently observable and must not be weakened post hoc
merely to make an implementation pass. Tests are verification evidence, not the
acceptance oracle unless the Goal itself is explicitly test-only.

For user-facing work, the CUJ should normally express what the owner actually
does from entry to useful result. Hidden, unreachable, or technically present
capability does not satisfy a user-visible acceptance criterion. For multi-step
Goals, isolated feature/subsystem PASS results do not compose into Journey PASS;
acceptance must cover the representative flow when composition matters.

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
- material owner/Tech Lead decisions relevant to the current Goal.

`TASK.md` may summarize the current decision, but material rationale/direction
that must survive Goal/chat turnover belongs in an accepted Decision Record.
Do not add task IDs, lifecycle stages, schemas, persisted status or a planning
database around this procedure.

## Result contract

Return one concise result:

- `GOAL_READY`: the owner outcome, CUJ, acceptance and boundaries are clear
  enough for bounded implementation; or
- `OWNER_INPUT_REQUIRED`: a material Owner-controlled product fact, trade-off,
  or consequential choice cannot be recovered or reasonably inferred from
  repository/current evidence. Ask only for that missing decision, translated
  into observable consequences rather than implementation jargon.
