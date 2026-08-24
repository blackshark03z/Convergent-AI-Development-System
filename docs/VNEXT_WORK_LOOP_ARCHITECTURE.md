# Build OS vNext Work Loop architecture

## 1. Current pipeline audit

The v1.24 candidate has strong `CURRENT`-selected immutable generations,
compare-and-swap transitions, Git identity/scope checks, immutable assurance,
receipt-based recovery, and an explicit external-effect ledger. Its normal
input is still a task-shaped CLI request. Tech Lead reasoning therefore arrives
as prose, while the Worker or human re-enters outcome, acceptance, scope, risk,
commands, assumptions and execution detail across bootstrap, runtime specs,
validation and relay messages.

The enhanced execution envelope prevents late plan/effect errors, but asking
every task to author its eight semantic collections and a detailed plan before
repo grounding can repeat Tech Lead work and prematurely freeze implementation
detail. `status`/`next` also refresh telemetry and rewrite projections, so the
candidate lacks a strictly read-only current-truth path.

## 2. Top cost and failure modes

1. Completed Tech Lead research is not transferred as typed status/evidence.
2. Repository hypotheses can survive until implementation or assurance.
3. Intent is manually translated into several task/spec/message shapes.
4. Unrelated unknowns can trigger broad readiness ceremony.
5. The Worker may repeat analysis merely to rediscover authority and evidence.
6. Normal local work exposes four lifecycle choices (`bootstrap`,
   `record-commit`, `validate`, `close`) plus diagnostics.
7. Late canonical contradictions are mixed with locally adaptable repo facts.
8. Broad context/spec payloads consume tokens when targeted reads would suffice.

## 3. Architecture options considered

| Option | Result |
| --- | --- |
| Handoff compiler that emits a full execution plan | Rejected. It repeats Worker repo judgment and tends toward a universal DAG. |
| Binary design-readiness phase | Rejected. Readiness is action-relative; unrelated unknowns must not block. |
| Semantic Skill/model router in the kernel | Rejected. Selection requires judgment and must not become lifecycle authority. |
| AI product-manager/orchestrator inside Build OS | Rejected. It duplicates Tech Lead/Worker reasoning and expands model/token cost. |
| Mutable handoff/grounding sidecar | Rejected. It competes with immutable generation truth. |
| Evidence-Carrying Work Contract plus Worker grounding and progressive boundaries | Selected. It transfers completed reasoning while retaining Worker intelligence and v1.24 transactions. |

## 4. Recommended target architecture

```text
Tech Lead
  -> immutable Work Contract (intent, decisions, acceptance, claim status/evidence)
Build OS read-only intake
  -> bounded Worker Capsule / targeted reads
Worker
  -> exact Git-bound grounding report, local adaptations, material conflicts
Build OS
  -> typed Decision Requests OR progressive action right
  -> one canonical Work Loop binding in CURRENT
Worker
  -> implementation and repo-dependent verification
Build OS
  -> existing commit/effect/assurance transactions
  -> declared ship-mode readiness
```

The Work Contract is not a compiled implementation plan. The grounding report
is not a second lifecycle state. Canonical generations store compact hashes,
status and immutable evidence references; the source artifacts live in the
append-only evidence tree and are rehashed before lifecycle operations.

## 5. Why it wins

It moves contradiction discovery before mutation, eliminates semantic re-entry,
keeps repository interpretation with the Worker, and preserves the proven
effect/recovery kernel. Gates apply to the requested action and scoped claims,
not to a global design phase. One normal `work` facade chooses only
deterministic lifecycle transitions; ambiguous Git state and external effects
remain explicit stops.

## 6. What remains in Tech Lead

- Product intent, business constraints and canonical architecture.
- Acceptance meaning and declared shipping mode.
- Evidence/status from completed research and decisions.
- Resolution of typed material Decision Requests.
- Superseding a Work Contract when canonical meaning changes.

## 7. What lives in Build OS

- Strict contract/grounding schemas and semantic validation.
- Hashing, freshness, evidence integrity and exact Git binding.
- Authority separation and deterministic Decision Request typing/coalescing.
- Progressive action rights and normal-loop lifecycle compilation.
- `CURRENT`, generations, receipts, Git scope, effects, assurance, recovery and
  ship-readiness projection.
- A strictly read-only `inspect` path.

Build OS does not research product meaning, choose architecture, select Skills
or models, or synthesize a universal implementation plan.

## 8. Worker responsibility

- Independently inspect the real repository and current dirty/committed state.
- Select the smallest claim set needed for the next action.
- Verify or contradict repo-sensitive premises with locally checkable evidence.
- Adapt locally when repo truth changes implementation detail.
- Implement, test, diagnose and challenge the handoff when evidence conflicts.
- Use Skills or advisory delegation only when their total cost is justified.

## 9. Human escalation contract

Escalation occurs only for a scoped open question or evidence contradicting
canonical intent, acceptance, architecture, business constraint or authority.
Build OS emits one coalesced `buildos.decision-request.v1` per premise with the
claim, authority, evidence, options and `ACTIONS_DEPENDENT_ON_CLAIM` scope.
Repository-claim contradictions produce local adaptation, not escalation.
Unscoped questions are visible and non-blocking.

## 10. Handoff and evidence model

Claims declare kind, authority, binding, status, source pointers, repo binding,
freshness/invalidators and verification owner. Raw chain-of-thought is excluded.
The Worker report binds contract hash, HEAD, tree, dirty product-state digest,
scoped outcomes, discoveries and proposed execution boundary. Repository proof
must include a locally rehashed file or exact Git observation. The canonical
generation stores compact bindings and hashes; evidence bodies are not copied
through every revision or packet.

## 11. Skill and reasoning routing model

Deterministic work uses no model. The primary Worker owns repo grounding,
implementation and diagnosis. Economical advisory models may perform bounded,
independently checkable extraction or triage, but cannot own canonical claims,
grounding truth, Decision Request resolution or effects. Tech Lead/Owner keeps
material product and architecture decisions. Skills are explicitly activated
guidance, not semantically routed kernel plugins.

## 12. Migration from v1.24

The state schema and store protocol remain readable and additive. Existing
legacy tasks continue with the old commands. New Work Loop tasks use new
contract/grounding schemas and optional `work_loop` state. No historical
generation is rewritten. A Work Loop task cannot use legacy `new-revision` to
silently change intent; it starts a fresh Contract revision/task after the
prior lease is released. Enhanced runtime/effect specs remain required for
high-cost and external-effect work.

## 13. What not to build

- AI product manager or autonomous semantic planner in Build OS.
- Full-plan handoff compiler or universal workflow DAG.
- `DESIGN_READY` lifecycle phase.
- Semantic Skill/model router in deterministic code.
- Mutable contract/grounding authority store.
- Raw chain-of-thought archive.
- A generic wrapper around every legacy command.
- Automatic provider dispatch or inferred retry.

## 14. Implementation phases

M0 measured the v1.24 surface. M1 added read-only Contract intake. M2 added
grounding and Decision Requests. M3 bound progressive rights into `CURRENT`.
M4 added `inspect` and the normal `work` facade. M5 consolidated evidence and
proportional assurance. M6 documented economical delegation. M7 runs local,
high-cost, external-effect and dirty-takeover pilots, migration/package proof,
the full deterministic suite and independent release review.

## 15. Risks and open questions

- Total source surface grows while the normal model-visible surface shrinks;
  field pilots must confirm the trade is favorable.
- Tech Lead Contract quality still matters; schemas cannot prove semantic
  completeness.
- A Worker can choose an incomplete grounding scope; final assurance and code
  review remain necessary.
- Exact provider/model token savings are unmeasured until real usage telemetry
  is available.
- Automatic assurance commands remain an explicit `--assure` boundary; command
  trust for legacy low-risk tasks is unchanged from v1.24.
- Merge/deploy/runtime activation still needs the existing authorized
  external-effect path; close only reports readiness for the declared mode.
