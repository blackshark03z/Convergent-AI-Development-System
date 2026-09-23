# CADS Existential Challenge — A–F Synthesis

Status: Canonical research evidence; architecture change NOT yet promoted
Date: 2026-09-23
Decision basis: DR-0014
Current disposition: **SHRINK — provisional, benchmark-gated**

## Frozen lane inputs

The six lane reports were produced in isolated contexts before synthesis. The
canonical repository records their immutable SHA-256 identities:

- Lane A: `7105656471ad9d34321e7ac8e11424206c2e40400ba3551bbe790da952345bab`
- Lane B: `94c20b1da8c506292150f795ebfbf1be1194f34a1bb0335c987c0423ad0efdd7`
- Lane C: `45eec3a68c120c83e779e816e261457cbb023ee06ef8d8fedb96195cd634677e`
- Lane D: `5986af5f581174f8006912edfda796a15a912ddf8ae62528a176831fc61a3bff`
- Lane E: `544beabef4cc6a5880fd9cbbf29e4251003b0fe1c12453cf41b45e8e74a7e929`
- Lane F: `7f630372cd9e25b0b9516a25d81c00de649bbef4d5e7cc2766eafcc3dcf1fcdd`

The external full synthesis artifact has SHA-256:
`602fbc3d13630b2a4a55bad71e0bfc369918e7f47eb2d77f450fae8de4932b4c`.

This repository document is the canonical research conclusion used to design
the counterfactual pilot. It does not silently promote a new architecture.

## Executive conclusion

The six lanes converge strongly on one direction:

> CADS should not continue expanding as an AI runtime/orchestration framework.
> It should shrink toward a very small harness-neutral semantic/evaluation layer,
> or disappear as a named system if ordinary tools preserve the same guarantees
> at lower total cost.

The mechanics most consistently judged commodity, replaceable, or perishable are:

- planner/worker/subagent topology;
- model routing as CADS Core;
- session/context management;
- persistent agent memory as canonical truth;
- worktree/branch management;
- generic task lifecycle/state machines;
- per-command Owner approval;
- custom sandbox/permission systems where the harness/OS/cloud already enforces;
- custom PR/merge/convergence machinery;
- custom provenance/identity ledgers when ecosystem primitives suffice;
- mandatory full spec/SDD for every task;
- mandatory second-AI review for every task.

The surviving claim is semantic, not orchestration-heavy.

## Provisional irreducible residue

### G1 — Outcome / Intent boundary

The desired product outcome and material constraints are distinct from the
executor's method.

Retain only:

> Material ambiguity that can change the accepted outcome or consequence must be
> resolved, bounded, or converted into a cheap reversible experiment before
> irreversible execution.

Do not infer that every task needs a design phase or persisted specification.

### G2 — Acceptance / Oracle integrity

A worker saying DONE is not product acceptance.

For material work:
- acceptance evaluates the actual candidate;
- the worker narrative is non-authoritative;
- the worker must not silently weaken the decisive oracle and self-approve;
- product-level/E2E evidence is required when isolated checks cannot prove the
  composed user outcome.

CADS should not own a test framework.

### G3 — Evidence / Identity / canonical lineage

Evidence must apply to the exact state being accepted.

Where build/deploy transformations matter:

`accepted source -> built artifact -> deployed/runtime state`

Use existing identifiers first: Git SHA, CI check identity, artifact digest,
provenance/attestation, deployment record, runtime version.

### G4 — Consequence / Authority boundary

Competence does not imply authority.

Broad autonomy is desirable inside a bounded environment, while irreversible or
externally consequential effects should cross capability/credential/environment
boundaries proportional to consequence.

CADS may state the semantic requirement. It should not duplicate the actual
enforcement plane.

### M1 — Proportional / adaptive assurance

Assurance scales with uncertainty, consequence, observability gap,
irreversibility and exposure—not merely repository size or process prestige.

### M2 — Replaceability / deletion

Every persistent scaffold requires:
1. an observed failure class;
2. evidence it improves the outcome;
3. an exit/deletion condition.

A stronger model/harness is a reason to re-test and remove scaffolding.

## Commodity map

CADS should not own by default:
- coding-agent planning/execution;
- subagent topology;
- sessions/compaction/recovery;
- Git branch/worktree semantics;
- repository instruction formats;
- generic spec generation;
- CI/status checks;
- browser/E2E tooling;
- merge queues;
- supply-chain provenance;
- deployment records;
- sandbox implementation;
- credential systems;
- agent-to-agent/tool transport protocols.

The unresolved pieces are mostly project semantics:
- whether Owner intent was captured correctly;
- what counts as acceptance;
- what consequence is authorized;
- which exact state the evidence proves.

## Provisional disposition ledger

| Mechanism | Disposition |
|---|---|
| CADS planner / worker topology | DELETE |
| CADS model/provider router | DELETE by default |
| CADS session/context manager | DELETE |
| CADS persistent agent memory as truth | DELETE |
| CADS worktree/branch manager | DELETE |
| universal governed runtime | DELETE as default |
| MAR as mandatory CADS dependency | DELETE |
| direct execution default | KEEP as policy, not runtime |
| mandatory full SDD/spec | DELETE as default |
| material ambiguity handling | SHRINK |
| agent DONE as acceptance | DELETE |
| Product Acceptance semantic | KEEP pending counterfactual |
| mandatory second-model reviewer | DELETE |
| protected/held-out oracle | KEEP conditionally pending threshold benchmark |
| custom evidence bundle service | REPLACE with native evidence |
| custom source/artifact/runtime ledger | REPLACE with ecosystem identity |
| Acceptance/Release/Activation always separate | SHRINK to real identity gaps |
| custom external-effect approval service | REPLACE with actual enforcement plane |
| per-command Owner approvals | DELETE as default |
| CADS canonical-truth database | DELETE |
| CADS merge/convergence engine | DELETE |
| autonomy eval dataset | KEEP |
| DR-0014 Existential Challenge | KEEP, itself subject to deletion test |

## Why this is not yet a final architectural change

The A–F research shows a strong direction but does not prove that the remaining
CADS residue adds measurable value over a credible ordinary-engineering stack.

Required counterfactual arms:
- N0 — No CADS;
- N1 — existing/minimal assembled stack;
- C-min — N1 plus only G1/G2/G3/G4 and M1/M2;
- C-current — current Thin CADS.

If N1 matches or exceeds C-min on accepted outcomes, safety guards, Owner
attention and maintenance burden, the correct result is REPLACE/DELETE.

## Critical benchmark-integrity correction

A benchmark performed only inside the CADS repository is structurally biased:
the N0 arm would still inherit CADS-era repository artifacts, terminology and
accepted assumptions.

Therefore:
- **P0 historical CADS replay** validates runner/oracle/result capture only.
- **P1 product counterfactual** uses product-derived tasks with a neutral
  projection so the No-CADS arm does not silently receive CADS process artifacts.

Only P1 plus any required full-project confirmation may support the existential
KEEP/SHRINK/REPLACE/DELETE verdict.

See `docs/CADS_EXISTENTIAL_PILOT_2026-09.md` and
`evals/existential/cads_v1.json`.
