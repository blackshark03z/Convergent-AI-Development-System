# Economical model delegation policy

Model choice is orchestration guidance, never deterministic-kernel authority.
Build OS validates artifacts, hashes, repository observations, action rights,
lifecycle transitions and effects without calling or selecting a model.

## Ownership tiers

| Work | Default owner | Delegation rule | Authority of output |
| --- | --- | --- | --- |
| Hashing, schema checks, Git identity, lifecycle/effect transitions | deterministic Build OS | never delegate to a model | canonical only through `CURRENT` |
| Repository grounding, implementation, local adaptation, test diagnosis | primary Worker | retain when repo interpretation or edits are material | evidence proposal until Build OS binds it |
| Product intent, business constraints, canonical architecture, acceptance | Tech Lead/Owner | never downgrade to a lower-cost model | canonical through an issued Work Contract/decision |
| Bounded extraction, deduplication, formatting, source triage | economical advisory model | use only when the input/output is bounded and independently checkable | advisory only |
| Open-ended research or design | Tech Lead or primary Worker | activate only when the Contract marks a material unknown and existing evidence is insufficient | advisory until an authority accepts the result |

The current vNext implementation and proof run make no Qwen or other provider
call. The policy is provider-neutral; a future economical model may be used by
the orchestrating Worker, but its identity never changes claim authority.

## Delegation gates

Delegate only when all are true:

1. The task is bounded and does not require repository mutation, provider
   dispatch, secret handling, product intent, or canonical architecture.
2. Inputs can be sent as targeted evidence rather than a full conversation or
   repository dump.
3. The output can be checked by the Worker or deterministic tooling at lower
   total cost than doing the work directly.
4. Failure, omission, or hallucination cannot itself cross an action boundary.

Do not delegate merely because a Skill exists. Skills remain explicit guidance
activated by the Worker when the repository/task actually needs them. There is
no semantic Skill router in the kernel.

## Context and evidence economics

- Transfer outcomes, claim status, evidence pointers, hashes, freshness and
  invalidators; never transfer hidden chain-of-thought.
- The Worker Capsule is capped at 8 KiB and requests targeted reads for
  overflow instead of copying the full handoff.
- Ground only the claims needed for the next action. Unrelated unknowns stay
  visible but do not block.
- Reuse hash-bound grounding and unchanged assurance evidence; re-execute
  final or rollback-sensitive checks where v1.24 already requires freshness.
- Escalate one coalesced typed Decision Request per canonical premise, not one
  message per observation.

## Evaluation metrics

Pilots record model-visible lifecycle operations, human relay count, scoped
claims, reused grounding/assurance claims, handoff/capsule bytes, decision
requests, and whether contradictions were found before product mutation. Model
price estimates are not invented when provider usage data is unavailable.
