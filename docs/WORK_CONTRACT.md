# Evidence-carrying Work Contract

## Purpose

The Work Contract transfers completed Tech Lead intent, decisions, acceptance,
evidence status and repository hypotheses into Build OS without compiling a
universal implementation plan.

It is an immutable source artifact. Read-only intake grants no mutation
authority. Initial canonicalization binds its content hash into the generation
selected by `CURRENT`.

## Authority model

- Owner/Tech Lead may issue canonical intent, decisions and acceptance.
- Repository claims are always `VERIFY_IN_REPO`; the Worker or deterministic
  tooling must verify them against current repository evidence.
- Advisory models cannot own canonical meaning.
- Provider facts require provider evidence in the effect runtime.
- Lifecycle/effect truth remains exclusively in Build OS generations.

The contract transfers reasoning outcomes, not raw chain-of-thought. It stores
bounded statements, evidence pointers, hashes, freshness and invalidators.

## Read-only command

Validate without creating `.buildos`, telemetry or a Work Packet:

```powershell
python scripts/ai.py --root <target-repo> contract `
  --file <work-contract.json> --view validation
```

Render the bounded Worker intake projection:

```powershell
python scripts/ai.py --root <target-repo> contract `
  --file <work-contract.json> --view worker-capsule
```

The intake Capsule grants only `READ_AND_VERIFY` and declares
`mutation_authority=NONE_READ_ONLY_INTAKE`. Grounding and progressive action
rights are introduced in M2/M3 rather than inferred prematurely.

## Worker grounding

The Tech Lead declares a bounded `action_basis_ids` set containing every
repository-verification claim plus only the open questions that materially
gate execution. The Worker may ground a smaller set for read-only exploration,
but any mutation request must cover the full declared action basis. This keeps
unrelated questions non-blocking without letting the Worker selectively omit a
difficult repository premise.

The grounding report is bound to the exact repository branch, HEAD, tree and
dirty product-state digest. Build OS independently re-reads those anchors, hashes
repository files, and requires claim evidence to cover its declared path/HEAD/
tree binding. Stale, unrelated-file, Build OS control-state, or external-only
proof cannot verify a repository claim.

For the local runtime, `target.repository` must be an absolute path and must
resolve exactly to the Git worktree root used by Build OS. The trusted Contract
pin therefore cannot be replayed accidentally against another same-branch repo.

Repository-claim path bindings name exact files, not globs or directories. A
glob cannot be truthfully represented by one matching evidence row; callers
must enumerate the bounded dependency files or bind the claim to an exact Git
tree/HEAD observation.

```powershell
python scripts/ai.py --root <target-repo> contract `
  --file <work-contract.json> --grounding <grounding-report.json> `
  --view grounding
```

A contradiction to a repository claim produces local-adaptation permission,
not an owner escalation. A contradiction to canonical intent, acceptance,
architecture or business constraints produces a deterministic typed Decision
Request. Its blocking scope is only actions dependent on that claim. Unscoped
claims and unrelated unknowns remain non-blocking at this read-only stage.

An open canonical Decision Request remains part of the current authority debt
even if a later Worker grounding report labels the claim `VERIFIED`. The same
Contract can advance only with a strict `buildos.decision-resolution.v1` file
that binds the exact request ID and request SHA-256, names the requested
Owner/Tech Lead role, and is pinned by the trusted launcher through
`BUILDOS_TRUSTED_DECISION_RESOLUTION_SHA256`:

```powershell
python scripts/ai.py --root <target-repo> work `
  --work-contract <work-contract.json> --grounding <fresh-grounding.json> `
  --decision-resolution <decision-resolution.json>
```

The original request and its immutable resolution evidence remain visible in
`work_loop.decision_history`. An authority may instead issue the next Contract
revision. That Contract must retain `contract_id`, bind the active hash through
`metadata.parent_contract_hash`, and include the exact
`buildos-decision-request:<id>:sha256:<request-sha256>` reference in
`metadata.source_context_refs`. Its trusted Contract hash then authorizes one
atomic `WORK_CONTRACT_SUPERSESSION`; a Worker cannot use an unrelated Contract
as a replacement.

## Canonical start and normal loop

Before the Worker starts, the trusted Tech Lead launcher sets
`BUILDOS_TRUSTED_CONTRACT_SHA256` to the SHA-256 emitted by the read-only
validator. Build OS compares it with the hash of the normalized Contract before
any `.buildos` write. There is no fallback to the issuer's self-declared role,
identity or authority reference. Once grounding grants the requested action,
one command compiles the normal lifecycle request and atomically binds both
immutable inputs into `CURRENT`:

```powershell
python scripts/ai.py --root <target-repo> work `
  --work-contract <work-contract.json> --grounding <grounding-report.json>
```

This transport pin assumes a cooperative local Worker and a trusted launcher
whose input the Worker does not control. It prevents accidental or model-driven
authority substitution, but it is not authentication against a hostile process
running as the same OS identity. Deployments with an untrusted Worker must
replace the launcher pin with a signed authorization receipt verified from a
pinned public key or an equivalent separate-identity/ACL boundary.

After the Worker commits the implementation, `work --assure` records the
commit, runs only the bound proportional assurance, and closes when every
existing v1.24 transaction gate passes. Dirty work, divergent Git state,
external effects, missing decisions and R3 reviewer/rollback requirements stop
at their existing explicit boundaries.

`inspect` is strictly read-only: it revalidates canonical handoff evidence and
derives current Git/lifecycle truth without refreshing telemetry or rewriting
the Worker packet.

## Status and evidence meanings

`DECIDED` is an authority decision. `VERIFIED` requires evidence appropriate to
the claim domain. `SUPPORTED` is reusable input that still needs its declared
verification. `HYPOTHESIS` and `UNKNOWN` remain explicit. `CONTRADICTED` and
`SUPERSEDED` preserve history instead of rewriting it.

Repository claims that say `VERIFIED` must include repository binding and
source evidence. A Tech Lead may provide strong repository evidence, but the
Worker still independently checks critical repo-sensitive premises.

## Projection boundary

The Worker Contract Capsule is a derived, non-authoritative projection capped
at 8 KiB. Long statements become deterministic SHA-256 pointers with targeted
reads; bounded-list overflow is explicit. Evidence bodies and source content
are never copied into the Capsule.
