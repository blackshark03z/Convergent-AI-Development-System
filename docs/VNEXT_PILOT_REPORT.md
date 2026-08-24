# Build OS vNext representative pilot report

Status: deterministic fixture pilots pass; real provider/model economics remain
unmeasured because this implementation run made no provider call.

| Pilot | Evidence | Result |
| --- | --- | --- |
| Small local | `test_one_normal_work_facade_bootstraps_then_assures_and_closes` | Two normal facade invocations produced bootstrap, product commit, validation and close. |
| Local high cost | `test_high_cost_work_reuses_grounding_and_preserves_enhanced_assurance` | Enhanced admission remained valid; two assurance claims executed; grounded repo claim was reused rather than rerun. |
| External effect | `test_external_effect_work_stops_before_dispatch_and_uses_v124_transaction` | Normal facade stopped with no effect ledger entry; explicit PREPARE durably recorded intent with no provider reference or inferred dispatch. |
| Dirty takeover | `test_dirty_takeover_is_grounded_but_not_laundered_into_a_task` | Worker could ground exact dirty bytes; canonical bootstrap refused, preserved bytes and created no control state. |

## Before/after structural measurements

| Measure | v1.24 normal path | vNext pilot | Change |
| --- | ---: | ---: | ---: |
| Model-visible lifecycle selections for small local work | 4 (`bootstrap`, `record-commit`, `validate`, `close`) | 2 (`work` start, `work --assure`) | -50% |
| Semantic values manually re-entered at Build OS command boundary | at least 5 (outcome/task/scope/check/inspector) | 0; two typed artifact references transfer them | removed in pilot |
| Grounded repo claims rerun during assurance | not transferable | 0 | one claim reused |
| Full assurance claims executed in high-cost pilot | 2 | 2 | unchanged safety work |
| Template Contract bytes | n/a | 1,554 | measured canonical JSON |
| Template Worker Capsule bytes | n/a | 1,155 | 74.3% of small template; hard cap 8 KiB |
| Total public/compatibility command names | 20 | 22 | +2; legacy retained |
| Normal Work Loop command names | n/a | 3 (`contract`, `work`, `inspect`) | bounded normal surface |
| `buildos/*.py` lines | 7,049 | 8,637 | +1,588 for typed intake/grounding/facade; field cost must be monitored |

No token-price or model-usage reduction is claimed from fixtures. Production
pilots must record handoff bytes, targeted reads, prompt input/cache metrics,
human relay events, contradictions before/after mutation, decision count,
executed/reused claims and late defect escapes.

