# Legacy authority terminality and adoption

Status: `FROZEN_IMPLEMENTATION_CONTRACT`

This contract defines the supported transition from a repository whose current
tracked execution authority is a legacy Build OS v1.16 family to the portable
v1.25 authority.  It is an adoption-layer capability.  It does not reinterpret
legacy work as v1.25-supervised work and it does not change the frozen
`buildos/` kernel.

## Eligibility

The bridge is fail-closed and binds one clean Git identity.  It refuses a
non-Git target, a dirty target, tracked `.buildos` content, existing v1.25
control state or authority, path indirection, malformed legacy state, HEAD/tree
drift, or a second/replayed transition.

A legacy task is terminal only when it is absent or is exactly `COMPLETED` or
`ABORTED` with a `RELEASED` lease.  `READY`, `ACTIVE`, `PAUSED`, and `BLOCKED`
tasks remain live and are refused.  A legacy Goal is terminal only when absent,
`COMPLETED`, or `ABORTED`; a `COMPLETED` Goal may contain only `DONE` or
`DEFERRED` nodes. `ACTIVE` is refused. `BLOCKED` remains resumable and is
refused unless an owner supplies both the explicit terminal-disposition flag
and an exact `buildos.legacy-terminal-disposition-authorization.v1` file.
Even then, an ACTIVE Goal node or claimed task lease is refused.

The authorization binds the repository origin/root commits/branch/HEAD/tree,
exact Goal ID and `GOAL_STATE.json` SHA-256, every decision/request identity and
fingerprint, the one terminal disposition, and the issuing OWNER identity. It
has a canonical self-hash and must also be pinned by the trusted launcher in
`BUILDOS_TRUSTED_LEGACY_TERMINAL_DISPOSITION_SHA256`. This reuses the Work
Loop's trusted-transport model: self-asserted role text alone is not authority.
A random reference, wrong/copy/stale authorization, or Goal/repository drift is
refused. The older `--authorization-reference` option is retained only to emit
a typed refusal; it cannot authorize transition.

```powershell
$env:BUILDOS_TRUSTED_LEGACY_TERMINAL_DISPOSITION_SHA256 = '<canonical-file-sha256>'
python skills/project-lifecycle-bootstrap/scripts/legacy_authority_bridge.py `
  --root <repo> prepare --transition-id <id> `
  --terminalize-blocked-goal `
  --terminal-disposition-authorization <authorization.json>
```

The authorization is not `--force`, does not accept dirty work, and grants no
product or provider action.

## Provenance and authority transition

`legacy_authority_bridge.py prepare` records a private, repository-bound
transaction journal containing hashes and inventories of the exact legacy
authority bytes. It deliberately makes no callable backup and does not change
the product tree. `retire` rechecks the same HEAD, tree,
cleanliness, origin/root identity, state and hashes, then:

1. disables callable project-local legacy executors before exposing any current
   authority;
2. archives the complete legacy `.ai` tree as a deterministic ZIP with every
   member checked against its original size/hash, archives conflicting
   instruction bytes under `.buildos-legacy/archives/<transition-id>/legacy/`,
   and stores executor bytes as hash-verified base64 evidence so all bytes are
   exactly reconstructible without expanding deep legacy paths or retaining
   executable entry points;
3. installs either explicitly supplied replacement worker instructions or a
   canonical fail-closed transition notice;
4. publishes one tracked `buildos.legacy-authority-transition.v1` receipt last.

Supported legacy Git history contains exactly `scripts/ai.py` and
`scripts/ai_os.py` as execution entry points. The bridge requires strong Build
OS lifecycle signatures at those canonical paths. A canonical file with
unrecognized content, or a strong legacy signature at any other path, is an
explicit ambiguous-authority refusal. Unrelated product files such as
`src/ai.py` or a package-local `buildos.py` are not authority and are never
retired merely because of their basename. The post-transition authority checker
uses the same identification contract.

The receipt binds the source HEAD/tree, repository roots and origin, package and
frozen-kernel identity, task/Goal/lease disposition, operator authorization,
all old authority hashes, archive disposition and replacement hashes.  It has
a canonical self-hash and is validated from actual bytes.  Editing prose cannot
create a valid receipt.

The receipt keeps the package identity that performed retirement as historical
provenance. Verification validates that immutable identity and receipt schema;
it does not require it to equal every future compatible package identity.
Normal package adoption still rewrites and validates the separate current
authority record, so an upgrade cannot silently reuse stale executable or
package bindings.

After the retirement delta is committed, normal `adoption/initialize.ps1`
creates policy and a `.buildos-authority.json` record.  That authority record
binds the transition receipt hash.  Normal v1.25 bootstrap then creates the
first immutable generation.  `legacy_authority_bridge.py finalize` writes one
immutable local `buildos.legacy-authority-activation.v1` receipt under reserved
`.buildos/control/legacy-bridge-receipts/`, binding the tracked transition,
authority record, package, `CURRENT`, and first selected generation.  Once
`CURRENT` exists, current authority admission fails closed until this activation
receipt is durable.

This produces four observable states:

- `LEGACY_ACTIVE`: no prepared journal; legacy authority remains callable.
- `TRANSITION_PREPARED`: private immutable snapshot exists; product bytes are
  unchanged and preparation may be cancelled.
- `LEGACY_RETIRED`: old entry points are absent, evidence and tracked receipt are
  present, and no current work may start until adoption completes.
- `V125_ACTIVE`: normal v1.25 `CURRENT` is selected and the activation receipt
  binds it to the retired legacy authority.

There is never a state in which the bridge activates v1.25 while a legacy
project-local executor remains callable.

## Interruption and recovery

The journal is written before retirement. Retirement operations are
idempotent and compare each source/archive/replacement hash. Legacy `.ai` is
atomically renamed into a Git-private quarantine before archive creation; the
quarantined tree is never recursively deleted by the transition, and the
canonical deterministic ZIP container bytes as well as every member are bound
by the receipt. Quarantine is mandatory recovery evidence until the receipt,
ZIP, executor/instruction archives, optional authorization evidence, and archive
attributes are all Git-tracked. After that durable boundary, tracked evidence
is sufficient in a fresh clone. A retained quarantine is still verified when
present, but its absence does not invalidate committed provenance. A crash before
retirement leaves `LEGACY_ACTIVE`; cancellation is supported.  A crash during
retirement leaves no v1.25 authority and `recover` completes the same bound
transaction or refuses unexpected drift.  A crash after tracked receipt
publication leaves `LEGACY_RETIRED`; normal adoption can resume.  Frozen-kernel
bootstrap retains its generation/receipt/guarded-`CURRENT` recovery rules.  A
crash after `CURRENT` but before activation-receipt durability blocks all normal
mutations until `finalize` completes idempotently.

## Rollback boundary

`TRANSITION_PREPARED` may be cancelled because no product byte changed.  Once
retirement starts, recovery only completes or diagnoses that exact transition;
it never silently resurrects legacy authority.  Before v1.25 activation, an
owner may use ordinary reviewed Git history to create a new explicit restoration
change.  After v1.25 activation or supervised work, rollback means terminalize
the current authority and explicitly enroll another authority.  It never means
editing legacy evidence, restoring `CURRENT` by hand, or treating v1.25
generations as v1.16 state.

## Acceptance

The candidate must prove all of the following with deterministic fixtures:

1. clean terminal v1.16 transition succeeds and preserves byte-identical
   evidence;
2. live tasks, leases, Goals, dirty trees, malformed/tampered state and tracked
   `.buildos` are rejected without laundering;
3. a BLOCKED Goal requires an exact schema-valid, Goal/repository-bound,
   trusted-launcher-pinned authorization and no active node;
4. copied, stale, replayed, path-traversing, symlink/reparse and HEAD/dirty
   race inputs fail closed;
5. interruption at each retirement boundary recovers deterministically and
   never creates dual authority;
6. old executors cannot run after retirement;
7. normal unrelated and v1.24/v1.25 adoption remains unchanged;
8. a disposable Story Audio-shaped legacy branch completes retirement,
   v1.25 bootstrap, activation binding and a read-only/NO_SOURCE_DELTA Work Loop;
9. frozen-kernel bytes remain exactly equal to `FROZEN_KERNEL.sha256`;
10. changed bytes receive new candidate identity and evidence without a stable
    or independent-R3 claim;
11. a committed transition verifies in a fresh clone without Git-private
    quarantine, while incomplete retirement still requires quarantine;
12. unrelated `ai.py`/`buildos.py` product modules survive byte-identically and
    ambiguous legacy signatures are refused rather than removed.
