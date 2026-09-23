# DR-0015: Retire CADS as the active development architecture

Status: Accepted
Date: 2026-09-24
Scope: Architecture / Product Development Model / Repository Lifecycle

## Context

CADS was created to make one human plus AI capable of producing software with
stronger intent handling, bounded authority, deterministic acceptance, source/
runtime identity and safer consequential effects.

The 2026-09 existential challenge compared no-CADS, minimal-assembled and
current-CADS approaches across five product-derived cases plus two required
full-project confirmations. The final disposition was INCONCLUSIVE: current CADS
showed no repeated incremental advantage over the smaller alternatives, while the
full-project confirmations did not reproduce the one controlled C-min advantage.
The same evidence also did not justify claiming that every CADS semantic can be
deleted safely.

Separately, the AI-Native Development Model — Closure Synthesis v2 converged on a
smaller architecture built primarily from existing primitives: durable intent,
an isolated executor, protected verification, exact candidate/artifact identity,
promotion, and production feedback. It deliberately rejects a new global
orchestrator, policy language, evidence database, profile engine, recovery engine,
or permanent benchmark platform unless a demonstrated failure later requires one.

The Owner has chosen to stop developing CADS as an active architecture rather
than continue paying maintenance and conceptual cost without demonstrated
incremental value.

## Decision

CADS is **RETIRED / END-OF-LIFE as an active development architecture** effective
2026-09-24.

This repository becomes a **research archive and reference implementation**.

After this decision:

- do not bootstrap new projects onto CADS;
- do not add new CADS controls, lifecycle machinery, routing layers, durable
  state, benchmark infrastructure or generalized governance abstractions;
- do not treat `buildos`, the CADS skill library, Thin Guard, evidence envelopes,
  execution routing/handoff, or the existential harness as the default path for
  future projects;
- do not reopen the XP-001..XP-005 existential corpus to manufacture a stronger
  architectural verdict;
- preserve the repository history, final evidence, decisions and implementation
  so the research remains auditable;
- successor work should use the smaller AI-native model based on existing
  Git/CI/provider/runtime primitives.

## Salvaged semantics

Retirement does **not** mean every CADS idea is discarded.

Two semantics remain explicitly reusable outside CADS:

1. **AI Tech Lead discovery / acceptance framing** — turn vague Owner intent into
   researched knowledge gaps, critical user journeys, observable acceptance and
   only the genuinely Owner-owned decisions. This should become a portable
   skill/convention, not a CADS framework dependency.
2. **Task-local external-effect safety** — for irreversible or externally
   consequential operations, preserve exact effect identity, idempotency where
   available, timeout-after-success reconciliation and fail-closed retry
   semantics. Reuse this only where the task actually has such effects; do not
   retain a global CADS recovery/control layer for ordinary development.

Everything else must earn its way back through a concrete failure in the
successor system and the smallest-remaining-gap rule.

## Successor direction

The intended development flow is:

`Owner idea -> AI Tech Lead -> frozen acceptance -> isolated worker -> Git candidate -> protected verifier -> exact verified source/artifact -> promotion -> product -> feedback`

The implementation should prefer native provider/platform mechanisms and small
project-local conventions. New custom machinery is justified only after a real
failure demonstrates that existing primitives cannot preserve the required
invariant.

## Repository policy after EOL

Allowed changes are limited to archival integrity, factual documentation fixes,
security-sensitive archival corrections, and extraction of reusable knowledge
without reviving CADS as a platform.

Any proposal to resume CADS development requires an explicit new Owner decision;
it must not happen implicitly through maintenance work.

## Preserved evidence

The canonical closure evidence remains:

- `docs/CADS_EXISTENTIAL_FINAL_DISPOSITION_2026-09-24.md`
- `docs/CADS_EXISTENTIAL_P1_RESULTS_2026-09-24.md`
- `docs/CADS_EXISTENTIAL_CHALLENGE.md`
- `evals/existential/`

No historical implementation or evidence is deleted by this retirement decision.
