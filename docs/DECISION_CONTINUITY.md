# Decision Continuity Protocol

A lightweight docs-as-code protocol for preserving material project decisions
across chats, Tech Leads and Workers without adding a context service or
lifecycle engine.

## Authority

A material decision discussed only in chat, memory, an agent report or a stale
handoff is not durable project truth. Once the Owner/Tech Lead accepts a material
direction, persist it in the repository under `docs/decisions/`.

Use the smallest authority model:

- Owner/Tech Lead owns the decision itself.
- Accepted Decision Records preserve durable rationale and settled direction.
- `TASK.md` holds the current Goal context, not historical rationale.
- `ARCHITECTURE.md` describes the current durable system, not the full history of
  why alternatives were rejected.
- Git/source owns implementation reality.
- Tests/runtime own verification/observed evidence in their respective domains.
- Chat memory and agent reports remain hints/claims, not durable authority.

## Materiality test

Create or update a Decision Record only when losing the decision could
materially change a later session's scope, approach, acceptance, architecture,
authoritative path or expensive research. Typical material decisions include:

- Product Goal, Critical User Journey or Definition of Done direction;
- architecture, provider, framework or authority-boundary choices;
- deliberate non-goals and rejected parallel implementations;
- product/navigation/UX direction likely to be reopened later;
- trade-offs that explain why an apparently reasonable alternative is not used;
- a decision whose rediscovery would consume substantial time/cost; or
- a revisit condition that should control when a rejected option becomes valid.

Do not create records for routine edits, variable names, temporary debugging
findings, test commands, ordinary reversible implementation details or the next
small action.

## Research durability in material decisions

When material research supports a direction expected to survive beyond the
current task, preserve the reasoning so normal technology churn does not make the
research disposable. Distinguish:

- dated/current evidence from durable product or engineering invariants;
- the capability/property required from the particular model, provider,
  framework, API or product currently used to realize it;
- known volatile assumptions and meaningful portability/replacement cost; and
- concrete revisit triggers tied to evidence or context change.

Do not record forecasts as facts or freeze a predicted vendor/tool roadmap into
project truth. The durable decision should remain understandable if the named
technology changes; reopen it when its stated assumptions or revisit triggers are
materially crossed, not merely because time passed or a newer tool exists.

## Project layout

`docs/decisions/README.md` is the active decision index. Keep it short. Detailed
records are created only for material decisions:

```text
docs/decisions/
├── README.md
├── 0001-short-decision-name.md
├── 0002-another-decision.md
└── ...
```

The index should identify active accepted decisions and any superseded records a
new session could otherwise mistake for current direction. A cold-start reads
the index first and opens only relevant records, keeping context bounded.

## Decision Record format

Use a short record:

```markdown
# DR-0001: Short decision title

Status: Accepted
Date: YYYY-MM-DD
Scope: Product | Architecture | Process | UX | Integration | Other

## Context
What problem or trade-off required a durable decision?

## Decision
What was accepted?

## Why
Why this direction rather than the realistic alternatives?

## Consequences
What becomes true, constrained or intentionally deferred?

## Revisit When
What concrete change in evidence/context would justify reopening this decision?
```

Keep the record concise. Link evidence or other records instead of reproducing
large research notes.

## Superseding a decision

Do not silently rewrite an accepted record into a different historical decision.
When direction materially changes:

1. create a new Decision Record;
2. mark the old record `Superseded by DR-xxxx`;
3. update the active decision index; and
4. update current `TASK.md` / `ARCHITECTURE.md` only where current truth changed.

This preserves the difference between "we never considered this" and "we
considered it, rejected it under earlier constraints, and later changed course
because evidence changed."

## Integration with CADS

Decision continuity is cross-cutting, not another development control:

- Project Cold-Start reads the active index and relevant accepted records.
- Product / Design Framing persists accepted material product/design direction.
- Goal Execution persists material implementation/product trade-offs that would
  otherwise exist only in chat.
- Product Acceptance checks that no material Goal decision remains chat-only.
- `AGENTS.md` reminds Workers that chat/memory/reports are not durable decision
  authority.

Do not add a decision database, vector store, schema registry, approval state
machine, automatic meeting-minutes dump, or record for every conversation.
