# Build OS vNext Architecture Audit

## Verdict

The field diagnosis is substantially correct, but the root defect is not a
weak bootstrap checklist. Build OS had no canonical, machine-readable model
between a task request and lifecycle execution. Assumptions, capabilities,
field authority, provider limits, recovery families and acceptance checks
therefore lived in different scripts or prose and could not jointly prevent an
invalid plan. Strong post-facto lifecycle recovery then carried costs created
before the kernel saw the work.

The selected upgrade is an execution/effect runtime compiled before expensive
work and stored inside the same immutable generation selected by `CURRENT`.
It is not a second lifecycle authority or a mutable sidecar. The operating
sequence is now:

`Prevent -> Bound -> Execute -> Reconcile -> Verify`

Legacy local tasks remain compatible. High-cost and external-effect tasks must
opt into the stronger envelope and fail before canonical task creation if it
does not compile.

## Repository-grounded current-state reconstruction

Before this upgrade, responsibility was distributed as follows:

- `buildos/model.py`, `buildos/store.py` and `buildos/facade.py` owned local
  lifecycle transitions, immutable generations, `CURRENT`, operation intent,
  Git observation and assurance evidence.
- `scripts/ai.py` optionally ran context-epoch preflight for enrolled projects.
- `execution_authority.py` checked package/executor identity separately.
- `project_lifecycle.py` checked project policy and ran owner-supplied quality
  commands, including a legacy `shell=True` path.
- `side_effect_contract.py` validated static retry/no-effect declarations but
  did not persist a runtime provider-effect transaction.
- Continuity was a bounded context/document handoff authority, not a product or
  lifecycle authority.

The kernel correctly knew whether a product commit and validation existed. It
did not know whether the plan was executable, which assumptions supported it,
whether provider constraints matched the plan, which component owned a field,
or whether an unresolved external effect existed.

## Causal graph

```text
No canonical execution model
  + fragmented admission ownership
  + monolithic validation commands
  + local-only transaction semantics
        |
        v
Plan/capability/authority defects survive bootstrap
        |
        v
Expensive work or provider dispatch starts
        |
        +--> blocker treated as an isolated correction
        +--> uncertain external result has no durable effect state
        +--> any revision discards/repeats broad assurance work
        |
        v
Safe kernel stops and recovers correctly, but late and expensively
```

## Hypothesis disposition

| # | Disposition | Repository-grounded conclusion |
|---|---|---|
| 1 | Confirmed | Bootstrap validated task/risk/auth/Git, not assumptions or plan readiness. |
| 2 | Confirmed | Cheap deterministic plan/provider defects were not jointly checked before execution. |
| 3 | Confirmed | Evidence was revision-wide; no claim-to-source dependency identity existed. |
| 4 | Confirmed | Source-fix/block operations represented events, not within-plan blocker patterns. |
| 5 | Confirmed | Lifecycle phase remained valid even when the plan model ceased to be credible. |
| 6 | Confirmed | No typed capability inventory or availability/constraint evidence was canonical. |
| 7 | Confirmed | Authority existed in several mechanisms but not per plan field/read/write. |
| 8 | Confirmed | Provider limits were project/adaptor knowledge, not compiled step constraints. |
| 9 | Confirmed | Local CAS was strong; no durable intent/dispatch/output/reconciliation ledger covered providers. |
| 10 | Confirmed | Static side-effect semantics covered retry proof but not generic runtime transitions. |
| 11 | Confirmed | Recovery families were usually implemented after a failure or documented per project. |
| 12 | Confirmed | The kernel had no content-bound PASS/SALVAGEABLE/REJECT review epochs. |
| 13 | Confirmed | No bounded pre-provider deadline or explicit no-dispatch timeout transition existed. |
| 14 | Partly confirmed | Bounded autonomy was fragmented; broad shipping autonomy remains intentionally absent outside a valid envelope. |
| 15 | Confirmed operationally | Public deterministic blocker/effect/replan operations now remove routine relay, while human authority is retained for real decisions. |
| 16 | Confirmed | Admission invariants were split across facade, policy, authority and context scripts. |
| 17 | Partly rejected | The kernel already separates Task/Revision/Epoch/thread; confusion came mainly from adoption workflow and evidence granularity. |
| 18 | Confirmed | Validation had no dependency-based reuse; full reruns were the only generally safe choice. |
| 19 | Confirmed | Existing tests were adversarial for local CAS, but production plan/effect/QC families were missing. |
| 20 | Rejected as kernel responsibility | Model routing is advisory execution policy. Deterministic authority stays in code; capability metadata can inform an external planner. |
| 21 | Confirmed | Legacy acceptance and project gates used shell strings; provenance became unsafe once a model could author policy. |
| 22 | Confirmed | Adoption was growing by wrapper/script/sidecar addition without one compiled task envelope. |
| 23 | Confirmed strength | `CURRENT`, immutable generations/evidence, CAS, operation identity, recovery and fail-closed Git boundaries remain the foundation. |
| 24 | Accepted with refinement | Three layers are appropriate, but runtime state must be embedded in canonical generations rather than become another authority. |
| 25 | Confirmed target | Moving deterministic rejection and selective assurance earlier reduces cost without reducing checks. |
| 26 | Accepted principle | Normal flow now follows Prevent/Bound/Execute/Reconcile/Verify; recovery remains available for irreducible uncertainty. |

## Confirmed defects, tradeoffs and field-specific observations

Confirmed generic defects are the missing compiled execution envelope, absent
external-effect ledger, no plan invalidation semantics, broad assurance
invalidation and the model-authored shell trust gap. Context compaction and
continuity costs are real tradeoffs but are orthogonal to product revision and
were not collapsed into the new runtime. Provider names, media/reference
capacities and particular QC rules are field-specific; the runtime models their
constraints and evidence without hard-coding any provider. The claim that the
transactional kernel itself lacked Task/Revision/thread separation was false.

## Architecture tournament

Scores are 1 (weak) to 5 (strong). Safety and recovery correctness were treated
as non-negotiable; the remaining criteria selected the lowest-cost design that
preserved them.

| Candidate | Safety | Prevention | Recovery | Ceremony | Runtime cost | Complexity | Compatibility | Testability | Migration | Generality | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| A. More adoption checklists/scripts | 3 | 2 | 3 | 1 | 2 | 2 | 5 | 3 | 5 | 2 | Rejected: repeats fragmentation. |
| B. Mutable execution sidecar | 3 | 4 | 3 | 3 | 4 | 3 | 4 | 3 | 4 | 4 | Rejected: creates competing authority/crash semantics. |
| C. Put every workflow state in kernel FSM | 5 | 4 | 5 | 2 | 3 | 1 | 2 | 4 | 1 | 3 | Rejected: kernel/state-machine inflation. |
| D. Compile an execution runtime into `CURRENT` generations | 5 | 5 | 5 | 4 | 5 | 4 | 4 | 5 | 4 | 5 | Selected. |
| E. General workflow engine/orchestrator | 4 | 5 | 4 | 2 | 2 | 1 | 2 | 3 | 1 | 5 | Rejected: disproportionate for personal-agent scope. |

Candidate D reuses the proven transaction boundary. The task spec is source
input; its normalized envelope, effects, blockers, reviews and claim results
become immutable generation content. `CURRENT` remains the only selector.

## Target layering

### Layer A: project skills and adapters

Own domain-specific HOW, provider APIs, local tools and deterministic product
compilers. They publish capability/effect evidence but do not mutate lifecycle
truth directly.

### Layer B: execution/effect runtime

`buildos/execution.py` compiles assumptions, capabilities, field authorities,
trusted commands, claim dependencies, effects, plan DAG and recovery families.
It decides blocker escalation, validates effect transitions, records review
epochs and selects proportional assurance claims.

### Layer C: transactional lifecycle kernel

The existing store, generation, receipt, evidence, Git observation, risk/auth,
context and recovery mechanisms commit complete Layer B state atomically. The
store protocol is unchanged.

## Promotion boundary

The new runtime is shipped as a v1.24 candidate, not declared a permanently
frozen primitive. Promotion deeper into the kernel requires field evidence:

- materially lower blockers discovered after implementation/dispatch;
- zero duplicate provider effects across crash/retry fixtures and field runs;
- lower executed-claim/full-suite ratio with no escaped regression;
- fewer human relay events per task;
- stable envelope/recovery vocabulary across at least three distinct projects;
- no increase in ambiguous recovery, lifecycle corruption or false evidence;
- demonstrated migration of legacy local tasks without forced ceremony.

Until then, the store/CURRENT transaction protocol remains deliberately
unchanged and the execution runtime stays a separable module committed through
that protocol.
