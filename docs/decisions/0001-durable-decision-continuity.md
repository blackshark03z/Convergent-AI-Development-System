# DR-0001: Preserve material decisions as repository truth

Status: Accepted
Date: 2026-09-06
Scope: Process

## Context

Material project-direction decisions were sometimes finalized in one chat but
not recovered accurately by a later chat/Tech Lead. Existing CADS context files
could reconstruct current Goal, architecture and implementation reality but did
not reliably preserve why a direction had been chosen or which alternatives had
already been deliberately rejected.

## Decision

Use lightweight repository Decision Records under `docs/decisions/` for
material accepted decisions. Bootstrap creates only the active decision index;
detailed records are added only when the materiality test is met. Decision
continuity is integrated into existing CADS playbooks instead of becoming a new
core skill or lifecycle subsystem.

## Why

Repository docs survive chat boundaries and can be reconstructed by any future
Tech Lead/Worker. A small index plus bounded records preserves rationale without
requiring a memory database, context service, workflow engine or unbounded chat
transcript ingestion.

## Consequences

New sessions must read the active decision index during cold-start. Material
accepted direction must not remain chat-only. Routine reversible details do not
receive Decision Records. Accepted history is superseded rather than silently
rewritten.

## Revisit When

Revisit only if repository Decision Records prove insufficient across multiple
projects and there is concrete evidence that a more structured persistence
mechanism would materially improve continuity without reintroducing lifecycle or
context-management complexity.
