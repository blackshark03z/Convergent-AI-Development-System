# CADS Model Routing Benchmark — 2026-09

Status: Experimental benchmark protocol, not CADS architecture or routing policy.

## Purpose

Measure whether newer model capability improves the CADS operating model before changing any canonical model-routing policy.

This benchmark is also evidence for the DR-0014 Existential Challenge: stronger models should be allowed to make CADS scaffolding unnecessary. It must not be used to justify GPT-specific CADS architecture.

This benchmark does **not** add a model router, scheduler, task lifecycle, worker runtime, provider abstraction, or new CADS control. It is an evaluation layer over the existing harness-neutral execution contract.

The benchmark keeps three questions separate:

1. **Model capability/economics** — which model profile reaches the same acceptance with less time, cost, repair, and Owner attention?
2. **Harness overhead/value** — holding the model profile constant, does governed execution add enough safety/recovery value to justify its overhead for the task class?
3. **CADS semantics** — do Intent/Design, Acceptance, Evidence, and Consequence remain unchanged across model/harness choices?

## Existing eval source

The benchmark reuses evals/autonomy/cases.json, especially AE-025 and AE-027..AE-035. Those cases remain the semantic eval dataset. Model-routing runs must not add live state or vendor policy to that dataset.

## Phase A — direct model comparison

Use the same DIRECT execution harness, same base revision, same Goal text, same authority, and same acceptance oracle for every model profile.

Initial candidate profiles:

- GPT-5.6 Sol High — historical/control profile when still available.
- GPT-6 Luna High.
- GPT-6 Luna Max.
- GPT-6 Sol High.

Do not assume the newest or most expensive profile is better. Model names are run metadata, not trust tiers.

The initial CADS replay corpus is defined in evals/model_routing/cads_v1.json.

### Correctness gate

A profile is not eligible for default routing if it produces any unresolved false-DONE, weakens acceptance, changes the Goal/oracle to make itself pass, or requires Owner engineering work that another equivalent run resolves autonomously.

Passing a reference diff comparison is **not** required. Different implementations are valid when they satisfy the same Goal and held-out acceptance semantics.

### Metrics

Record per run:

- model and reasoning-effort profile;
- harness and concrete version where available;
- base revision and final candidate identity;
- first-pass acceptance result;
- final acceptance result;
- false-DONE / escaped defect / reopen / rollback;
- repair iterations;
- Owner active-attention minutes;
- Owner re-explanation/intervention count;
- wall-clock duration;
- input/output/cached tokens where measurable;
- model/tool cost where measurable;
- acceptance/evidence references;
- files changed and whether scope escaped the Goal.

Primary comparison remains the CADS autonomy north star: verified accepted Goals with the least Owner active attention, guarded by correctness/evidence quality. Cost and latency break ties only after acceptance integrity is preserved.

## Phase B — harness comparison

Do **not** mix model comparison with MAR comparison.

After Phase A identifies one or more credible model profiles, replay a smaller representative subset while holding the model profile constant:

- DIRECT/raw harness;
- GOVERNED/MAR only when the Goal actually requires isolation, recovery, fencing, durable cancellation, or equivalent runtime properties.

Measure added wall-clock time, task block/cancel/retry rate, Owner attention, recovery quality, and any defects prevented or recovered.

MAR is promoted for a task class only when the observed runtime property is valuable enough to justify its measured coordination cost. A successful DIRECT run is not evidence that MAR is unnecessary for task classes that genuinely need governed runtime properties.

## Initial replay corpus

The first four cases are historical CADS changes with pinned base and reference commits. They intentionally span design-heavy change, execution-policy change, harness handoff, and a focused Windows portability defect.

The reference commit is used only to recover held-out oracle material and historical intent. The candidate must not receive the reference implementation diff.

The evaluator should materialize held-out tests/oracles from the reference side after the candidate finishes, then run the normal active CADS self-test. Exact patch equivalence is not an oracle.

## Promotion rule

This first four-case corpus is a pilot, not enough evidence to canonicalize a global routing policy.

Promote a default model profile only after:

1. it preserves or improves acceptance integrity versus the current baseline;
2. it does not increase false-DONE, escaped-defect, or Owner-engineering burden;
3. its cost/latency advantage is repeatable across more than one task class;
4. representative cross-project tasks are added after the CADS-only replay works.

Routing should remain capability/evidence driven. A future stronger model may bypass obsolete scaffolding; a capability regression may temporarily require stronger assurance. Neither direction changes CADS semantics.

## Non-goals

- No model/provider selection logic in CADS Core.
- No persisted benchmark lifecycle.
- No vendor-specific CADS architecture.
- No permanent assumption that Luna is implementation-only or Sol is Tech-Lead-only.
- No MAR lifecycle changes.
- No weakening of Product Acceptance to improve benchmark throughput.

## Immediate next action

Run Phase A once an execution surface can launch the selected Codex/model profiles non-interactively. Until then, the corpus and oracle contract can be validated without changing CADS architecture.
