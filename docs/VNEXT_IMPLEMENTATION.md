# Build OS vNext implementation ledger

Status: `ACTIVE_CONTINUOUS_GOAL`

Target flow:

`Tech Lead -> Work Contract -> Build OS -> Worker grounding -> implementation -> proportional assurance -> ship`

This ledger records milestone evidence and architectural drift checks. It is
not lifecycle authority and does not replace `CURRENT`, immutable generations,
or release evidence.

## M0 structural/economic baseline

Baseline source: v1.24 candidate `c33278ee0b43374dfbbdb8e39d834a596fbcbad5`.

These are structural cost proxies, not invented field measurements:

| Signal | v1.24 baseline | Correctness cost represented |
| --- | ---: | --- |
| `buildos/*.py` source | 7,049 lines | Universal kernel/runtime surface before vNext |
| Public/admin lifecycle commands | 20 | Model-visible operation and relay surface |
| Enhanced execution semantic collections | 8 | Up-front assumptions/capabilities/authorities/commands/claims/effects/steps/recovery authoring |
| Reference execution-spec template | 176 lines | Premature plan/effect declaration burden |
| Normal kernel mutations | 4 | bootstrap, record, validate, close, excluding Git and adoption operations |
| Core effect success mutations | 5 | prepare, dispatch, acknowledge, result, persistence commit |
| Intent representations | at least 3 | kernel outcome, Continuity operational intent, live Codex Goal |
| Enrolled mutation preflights | 2 or 3 | executor authority, project policy, and later-epoch context ownership |
| Strictly read-only status path | absent | status writes packet/telemetry projections |
| Structured upstream reasoning transfer | absent | Tech Lead work must be relayed/reconstructed |

Existing field traces already track requests, tool actions, raw/cached input,
reasoning, context peak, compactions, rollovers and closeout calls. vNext pilots
must additionally measure handoff evidence reuse, repository contradictions
before/after edit, material decision count, human relay count, model-visible
lifecycle operations, and executed/reused assurance claims.

## Success-criterion evidence map

| Criterion | Intended authoritative evidence |
| --- | --- |
| Structured evidence-carrying intake | Work Contract schema, semantic validator, CLI and adversarial tests |
| Targeted Worker grounding | Repo-bound verification events and drift tests |
| Local adaptation vs escalation | Typed contradiction classification and Decision Request tests |
| Unrelated unknowns do not globally block | Progressive action-right derivation tests |
| v1.24 effect/runtime guarantees retained | Existing adversarial suite plus new boundary integration tests |
| Lower normal ceremony | Before/after model-visible operation counts in pilots |
| No duplicate semantic authority | `CURRENT`-bound contract hash; all capsules/goals derived and verified |
| Canonical Worker Capsule | Contract/generation/Git projection tests and 8 KiB bound |
| Representative improvement | Small local, high-cost, external-effect, and dirty-takeover pilot evidence |
| Explicit compatible migration | Legacy state/spec fixtures and migration documentation |
| Release readiness | Full deterministic suite, package identity, frozen bytes, independent final review |

## Milestones

- M0: baseline and evidence map — `COMPLETE`
- M1: Work Contract schema + read-only validator/projection — `COMPLETE`
- M2: Worker grounding + Decision Requests — `COMPLETE`
- M3: progressive action rights — `COMPLETE`
- M4: runtime/facade simplification — `COMPLETE`
- M5: assurance/evidence consolidation — `COMPLETE`
- M6: economical model-routing policy — `COMPLETE`
- M7: representative pilots + release preparation — `PENDING`

## Architectural drift rules

- No LLM output becomes kernel authority by self-declaration.
- No binary design-readiness lifecycle phase.
- No universal implementation DAG.
- No new mutable sidecar authority.
- No ambiguous external-effect retry.
- No model or Skill selection in the deterministic kernel.
- No release claim before independent final assurance.
