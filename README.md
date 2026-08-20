# Build OS v1.23 candidate

This is the isolated candidate produced for `BUILD-OS-FINAL-ULTRA-CANDIDATE`.
It is a small, repository-independent control plane.  Point the external
facade at a product repository; do not copy generated control state into the
product source tree:

```powershell
python D:\path\to\build-os-v123-candidate\scripts\ai.py --root D:\path\to\product bootstrap `
  --task-id TASK-001 --outcome "the change is correct" --allow src/app.py
```

The candidate reserves `.buildos/` in the target repository and adds that
path to Git's local `info/exclude`.  A tracked `.buildos` path is rejected so
an existing product-owned control directory cannot be mistaken for OS state.
Project policy is optional and namespaced at `.buildos-policy.json`; absent
policy uses the field-tested defaults.

## Worker flow

The normal Worker facade exposes ten commands:

`bootstrap`, `status`, `next`, `record-commit`, `validate`, `rollover`,
`close`, `recover`, `block-for-source-fix`, and `continue-task`.

The administrative facade additionally exposes `adopt-existing-change`,
`new-revision`, `abort`, and `telemetry-ingest`. A rollover always names a fresh disposable
`--thread-id`; this makes a retry distinguishable from a new epoch. Rollover is
a rare compact-failure fallback, not a normal request-count rhythm.

Typical flow is:

1. `bootstrap` once (one kernel action).
2. Implement and commit product files with ordinary Git.
3. Run `status`/`next` at context checkpoints, then `record-commit`.
4. Run deterministic checks through `validate`; R3 also needs an independent
   reviewer, reference, and a distinct rollback/recovery check.
5. `close` after evidence is verified.

There is no `reopen`.  A product change after assurance is preserved as proof
of the prior revision and requires `new-revision`; a legitimate tree-equivalent
descendant is simply recorded during close.

A live task blocked by a defect in its source system uses
`block-for-source-fix`. This releases its lease without rewriting the event as
an ordinary abort. After a bounded repair task is complete, `continue-task`
creates a fresh identity with immutable lineage to the released task; it never
resurrects that task. An already-existing clean Git change can be enrolled only
through the admin `adopt-existing-change` path and is permanently labelled
`EXTERNAL_PREEXISTING`, so Build OS does not claim to have supervised creation
of that commit.

## Authority and crash model

The single logical canonical authority is the validated immutable generation
selected by `.buildos/control/CURRENT`.  `CURRENT` is only an atomic locator;
it is not a second state document.  Generation records, commit receipts, and
evidence are content-addressed and never overwritten.  `WORK_PACKET.json` is
regenerated from the current generation and is continuation guidance, never
lifecycle authority.

Every lifecycle write validates preconditions, computes a complete candidate,
stages artifacts, obtains the single-writer lock, re-checks Git immediately
before the pointer swap, atomically replaces `CURRENT`, verifies it, writes an
immutable receipt, and projects the packet.  A process death before the swap
leaves the previous generation valid; after the swap, `recover` uses only
receipted/validated generations and repairs a missing or stale pointer without
guessing.  The proof is scoped to process crashes and logical filesystem
atomicity.  POSIX directory flush is best effort; the Windows build does not
claim sudden power-loss durability.

Git proves commit/tree identity, ancestry, cleanliness, and changed paths.  It
does not prove authorization, lifecycle, reviewer independence, telemetry, or
context interception.  The Desktop governor is therefore explicitly
SUPERVISORY/BOUNDARY: it makes the next action cheap and truthful, but cannot
intercept an already-issued model request.

## One-chat-first context governor

`PROJECTED_HEADROOM_ONE_CHAT_HYBRID` compares the latest/current prompt `P`
with the effective runtime context window `W`. Below 50% it continues; 50-70%
is a nonblocking warning; at 70% it tells the Worker to compact the active chat,
re-measure P, and continue the same outcome there when healthy. Historical
`PEAK` and productive request count remain telemetry only, so a successful
compact can return the action to `CONTINUE` without erasing peak evidence.

Rollover becomes eligible at 80% only with a reference proving same-chat
compaction unavailable/ineffective, or with an allowed material state-loss
condition proven to persist after compaction. Hard stop is dynamic at
`W - max(10% W, 25000, known payload/output reserve)` or an explicit runtime
overflow. Runtime telemetry supplies W; an explicit surface configuration is
second choice. If neither is available, status labels a conservative 128k
fallback and never pretends it measured the active model. Cache-read,
noncached, and cache-write totals are advisory economics and cannot relax
safety.

## Telemetry and Skills

During normal Codex Desktop execution no telemetry configuration is required.
The facade uses the exact `CODEX_THREAD_ID` inherited by its tool process,
validates the corresponding rollout JSONL against the active task and
repository, and persists one immutable source/baseline binding per
Task/Revision/Epoch under `.buildos/runtime/telemetry_bindings/`.  Initial
binding requires a root-user stream.  A rollover may also bind the exact
self-owned Desktop fork named by the canonical disposable `thread_id`, but only
when its first-header `forked_from_id` is the immediately prior epoch's bound
session.  Retries reuse that binding and old/new counters are never merged.
Other subagent streams remain ineligible.

For a new Desktop binding after rollover, `--thread-id` names the fresh
physical continuation exactly; it remains disposable with the epoch and is not
a durable lifecycle identity. Already-persisted bindings from the first v1.22
corrective remain readable for compatibility.

If the exact Desktop identity is unavailable, discovery binds only one live
root-user session whose declared cwd is the repository.  Multiple plausible
sessions report `TELEMETRY_UNBOUND/AMBIGUOUS`; zero remain truthfully
`UNMEASURED`.  `BUILDOS_CODEX_DESKTOP_SESSION_FILE` is an explicit validated
file override for unusual environments.  Existing configured sources
(`BUILDOS_TELEMETRY_FILE`, `AI_BUILD_OS_CODEX_APP_SERVER_USAGE_FILE`, or
`AI_BUILD_OS_USAGE_FILE`) retain precedence.

Codex cumulative notifications are baselined at task and epoch binding. The
latest prompt drives the governor while the historical maximum remains a
separate evidence field; the same-cumulative zero-prompt notification after a
Desktop `compacted` marker rebaselines the latest prompt without incrementing
request count.
Missing or malformed telemetry is reported as `UNMEASURED` or
`ADAPTER_BLOCKED`; it cannot change canonical lifecycle state.  CLI invocations
also append a `CONTROL` tool-action record, while productive model usage is
never fabricated when no source exists.  The detailed binding and field-replay
contract is in `docs/TELEMETRY_BINDING.md`.

`WORK_PACKET.json` projects the current disposable `thread_id` beside Task,
Revision, Epoch, and `epoch_id`, so the expected rollover continuation remains
visible without making the packet authoritative. It also projects current
governor measurement plus telemetry binding status/reason. An unbound or
unavailable rollover source explicitly tells the Worker to stop model work and
restore binding before continuing.

Two optional static `SKILL.md` guides are included (`python-change-v122` and
`git-validation-v122`).  Selection is explicit; no registry, executable plugin,
or dynamic precedence exists.  Skill text is untrusted guidance and cannot
change risk, authorization, Git scope, lifecycle, or evidence rules.  The
kernel works with zero Skills.

## Optional lifecycle adoption

The repository also ships the `documentation-handoff-continuity` and
`project-lifecycle-bootstrap` Skills, adoption scripts, and Knowledge Pack
templates. They are an opt-in adoption layer: the frozen `buildos/` kernel
remains usable on its own.

Run `adoption/initialize.ps1` to create a project policy and enroll a product
repository. The generated policy sets `context_epoch.enabled` to `true`; only
then does `scripts/ai.py` run the context-epoch preflight before mutating
lifecycle actions. Unenrolled projects retain the same kernel lifecycle rules,
including the two new public release/continuation commands. Set
`BUILDOS_CONTEXT_EPOCH_PREFLIGHT=1` only for a deliberate
one-off opt-in, or `=0` to override the policy for an isolated diagnostic run.

See [docs/PROJECT_LIFECYCLE_KIT.md](docs/PROJECT_LIFECYCLE_KIT.md),
[docs/LIFECYCLE_LINEAGE_AND_ADOPTION.md](docs/LIFECYCLE_LINEAGE_AND_ADOPTION.md),
[docs/SIDE_EFFECT_SPEC_CONTRACT.md](docs/SIDE_EFFECT_SPEC_CONTRACT.md), and
[docs/CONTEXT_EPOCH_RUNTIME.md](docs/CONTEXT_EPOCH_RUNTIME.md) for the adoption
contract and runtime boundaries.

Run the deterministic proof suite from this directory:

```powershell
python scripts/self_test.py
```

The candidate is ready for a real field benchmark only after the final
commit and clean-tree checks described in `docs/V1.23_CANDIDATE_REPORT.md`.
