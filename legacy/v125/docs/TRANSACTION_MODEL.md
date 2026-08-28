# Transaction and adoption contract

## On-disk layout

`.buildos/control/CURRENT` is the only mutable lifecycle locator.  It points
to an immutable, content-addressed generation:

```text
.buildos/
  control/
    CURRENT
    LOCK.guard
    generations/g00000001-<hash16>.json
    receipts/p00000001-<hash16>.json
    staging/                  # disposable, never canonical
    quarantine/               # invalid receipts retained for inspection
  evidence/<task>/rNNN/validation-<hash>.json
  runtime/WORK_PACKET.json    # generated continuation view
  runtime/telemetry.jsonl     # append-only optional projection
  runtime/telemetry_baselines.json  # optional cumulative-source baseline
  runtime/telemetry_bindings/<identity-hash>.json  # immutable Desktop epoch binding/baseline
```

The logical authority count is one: the validated generation named by
`CURRENT`.  Generation files, receipts, evidence, telemetry, and Desktop
binding files do not assert independent lifecycle state.  A packet that is torn or stale is simply
regenerated.

## Commit sequence

Each mutating lifecycle operation follows this order:

1. Validate request, risk floor, authorization, Git ancestry/cleanliness, and
   scope. Bootstrap also validates the target before adding the idempotent
   local `.buildos/` exclude entry.
2. Compute a complete pure candidate state and stable transition intent.
3. Prepare non-destructive evidence using a unique fsynced temporary file and
   exclusive immutable publication.
4. Acquire the advisory single-writer guard, reconcile the receipt frontier,
   and compare the expected generation hash.
5. Build and immutably publish the complete generation under that guard,
   re-observe Git immediately before the pointer swap, and atomically replace
   `CURRENT`.
6. Read `CURRENT` back, verify the content hash, write a content-addressed
   commit receipt, then generate the monotonic `WORK_PACKET` projection.

Failures before step 5 leave the prior pointer valid; noncanonical orphan
staging/generations are ignored.  Failures after step 5 leave a valid pointer
that startup `recover` can receipt and project.  Recovery holds the same writer
guard while scanning, chooses only one receipt frontier, repairs a stale or
missing pointer, and refuses forks or ambiguous evidence.  Invalid receipts
beside a valid current pointer are moved to a quarantine directory; invalid
receipts are never silently used as proof.

The guarantee is for process death and logical atomic replacement.  POSIX
parent-directory flush is attempted; Python's portable Windows path does not
claim power-loss/drive-removal durability.  A cooperative single product
writer is assumed because Git's own commit and the OS pointer are separate
resources; precommit checks and subsequent status/revalidation expose a race,
but cannot make those two resources one hardware transaction.

## Retry keys

Operation IDs are portable filename-safe strings.  Default IDs bind stable
command inputs and external Git anchors/signals.  Receipts and all prepared
generations bind an operation to its transition intent globally; reusing a key
for another command, parent, epoch, or payload fails closed.  A retry after a
pointer swap confirms the missing receipt and regenerates the latest packet.
Rollover requires a new disposable `thread_id`, so a repeated command is
unambiguously a retry rather than an accidental second epoch.

## Git boundary

The candidate never performs, rolls back, rebases, or overwrites a product Git
commit.  It observes SHA, tree, ancestry, dirty paths, case semantics, scope,
deletions, and type changes.  Product changes are compared from the immutable
revision base, preventing a late prohibited commit from being laundered by a
new revision.  A rebase/non-descendant is a fail-closed recovery/new-task
condition; a tree-equivalent descendant is normal close refresh.
