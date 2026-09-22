# DR-0013: Default to direct execution and add governance only for required runtime properties

Status: Accepted
Date: 2026-09-22
Scope: Execution / Harness / Acceptance / Governance

## Context

A direct ChatCode benchmark separated product/design quality from MAR runtime
overhead. With the same execution substrate, a goal-specific spec-driven
candidate reached the product obligations without a repair round while a Raw arm
required repair and still missed held-out product checks. The timing comparison
is directional rather than statistically independent because the spec arm ran
later in the same model context.

The benchmark also showed that ordinary fully specified coding work can often
execute as a short native loop -- inspect, edit, focused verification, commit --
without a durable task lifecycle. Earlier MAR-heavy experiments mixed
product/design semantics with worker lifecycle, resource waiting, cognition
relay, durable authority and recovery. The resulting blocked/cancelled rate made
the execution substrate itself a major confound.

CADS already separates product/design semantics from execution substrate in
DR-0011 and DR-0012. This decision makes the routing consequence explicit.

## Decision

For CADS development, **direct execution is the default route** when the current
Goal does not require a runtime property that the selected direct harness cannot
provide.

Direct execution means a compatible coding harness works natively against the
bounded repository authority, using ordinary Git/edit/test/commit mechanics.
Examples include ChatCode, Codex, Claude Code, OMP or a future equivalent. CADS
does not own the harness's model routing, session topology, subagents, context
management, LSP/DAP or internal reasoning loop.

Use a **governed execution substrate** only when the accepted Goal/design requires
one or more material runtime properties such as:

- isolated mutation;
- durable crash/restart recovery;
- concurrent-writer or stale-writer fencing;
- durable execution authority across client/session loss;
- enforced shared resource governance; or
- crash-safe canonical integration/promotion.

These are execution properties, not CADS lifecycle stages. A governed substrate
may be MAR or another implementation that demonstrably supplies the required
properties. **MAR is one current governed substrate**, not a CADS semantic
dependency and not the mandatory path for ordinary coding work.

Consequential external effects remain subject to the existing CADS Consequence
boundary regardless of route. A single bounded effect protected by the Thin Guard
does not by itself require MAR. Escalate to a governed runtime only when the Goal
also needs one of the runtime properties above.

## Property-based routing helper

Expose a small read-only helper:

`python scripts/ai.py route [--require <property>]...`

The helper maps explicit required properties to `DIRECT` or `GOVERNED`. It does
not infer risk from command text, inspect model identity, grant authority, persist
task state, select a vendor, start a runtime or prove that a chosen substrate
actually satisfies the properties.

Design Authority remains responsible for identifying material requirements from
the current Goal/reality. The helper exists to make the routing rule deterministic
and testable, not to create a policy engine.

## Independent acceptance

Execution speed does not transfer completion authority to the Worker. Product
Acceptance evaluates the identified candidate against the predefined
Goal/design/oracle rather than accepting the Worker's completion narrative.

Independence is primarily an oracle/evidence property, not a universal
requirement for a second model. For material Goals, acceptance should attack the
candidate from the accepted obligations and include a cheap held-out, negative,
composition, or supported-journey check when that check can expose a plausible
blind spot. Use a fresh evaluator/model/tool/human only when correlated
generator/verifier reasoning could materially invalidate the oracle.

## Consequences

- The normal happy path becomes Design Authority -> direct harness -> candidate ->
  independent Product Acceptance.
- Design-heavy work can still use OpenSpec, Spec Kit or another replaceable
  goal-specific baseline without forcing a durable runtime.
- MAR can shrink toward an optional trusted execution kernel instead of competing
  with coding harnesses for provider/session/cognition responsibilities.
- Blocked/cancelled durable runtime states stop being part of ordinary coding work
  unless the Goal actually needs the runtime properties that justify them.
- CADS remains compatible with stronger future agents because model/harness
  mechanics remain replaceable.

## Explicitly rejected

Do not add:

- a universal numeric risk score;
- a persisted routing state or task database;
- automatic command-text danger classification;
- MAR-by-default for all tasks;
- one permanent coding harness;
- a CADS model/provider router;
- a mandatory second-model reviewer for every change; or
- weakening Consequence/Acceptance semantics merely because execution is direct.

## Revisit

Revisit when representative evidence shows direct execution repeatedly violates a
required property that was not expressible here, or when a commodity harness
reliably supplies properties that currently trigger governed execution. In that
case remove obsolete governance scaffolding rather than preserving it for
historical reasons.
