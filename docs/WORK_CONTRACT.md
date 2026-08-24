# Evidence-carrying Work Contract

## Purpose

The Work Contract transfers completed Tech Lead intent, decisions, acceptance,
evidence status and repository hypotheses into Build OS without compiling a
universal implementation plan.

It is an immutable source artifact. In M1 it is read-only intake and grants no
mutation authority. A later milestone binds its content hash into the canonical
generation selected by `CURRENT`.

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

The M1 Capsule grants only `READ_AND_VERIFY` and declares
`mutation_authority=NONE_READ_ONLY_INTAKE`. Grounding and progressive action
rights are introduced in M2/M3 rather than inferred prematurely.

## Worker grounding

The Worker chooses the smallest claim set needed for the next action and
submits a grounding report bound to the exact repository HEAD, tree and dirty
product-state digest. Build OS independently re-reads those anchors and hashes
repository files named as evidence. Stale or external-only proof cannot verify
a repository claim.

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

## Canonical start and normal loop

Once grounding grants the requested action, one command compiles the normal
lifecycle request and atomically binds both immutable inputs into `CURRENT`:

```powershell
python scripts/ai.py --root <target-repo> work `
  --work-contract <work-contract.json> --grounding <grounding-report.json>
```

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
