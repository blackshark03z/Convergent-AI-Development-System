# Build OS v1.22 candidate

This is the isolated candidate produced for `BUILD-OS-FINAL-ULTRA-CANDIDATE`.
It is a small, repository-independent control plane.  Point the external
facade at a product repository; do not copy generated control state into the
product source tree:

```powershell
python D:\path\to\build-os-v122-candidate\scripts\ai.py --root D:\path\to\product bootstrap `
  --task-id TASK-001 --outcome "the change is correct" --allow src/app.py
```

The candidate reserves `.buildos/` in the target repository and adds that
path to Git's local `info/exclude`.  A tracked `.buildos` path is rejected so
an existing product-owned control directory cannot be mistaken for OS state.
Project policy is optional and namespaced at `.buildos-policy.json`; absent
policy uses the field-tested defaults.

## Worker flow

The normal Worker facade exposes eight commands:

`bootstrap`, `status`, `next`, `record-commit`, `validate`, `rollover`,
`close`, and `recover`.

The administrative facade additionally exposes `new-revision`, `abort`, and
`telemetry-ingest`.  A rollover always names a fresh disposable
`--thread-id`; this makes a retry distinguishable from a new epoch.

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

## Telemetry and Skills

During normal Codex Desktop execution no telemetry configuration is required.
The facade uses the exact `CODEX_THREAD_ID` inherited by its tool process,
validates the corresponding root-user rollout JSONL against the active task and
repository, and persists one immutable source/baseline binding per
Task/Revision/Epoch under `.buildos/runtime/telemetry_bindings/`.  Retries reuse
that binding; a rollover selects a different physical Desktop stream and never
merges the prior epoch's counters.  Subagent streams are not selected as the
productive task stream.

If the exact Desktop identity is unavailable, discovery binds only one live
root-user session whose declared cwd is the repository.  Multiple plausible
sessions report `TELEMETRY_UNBOUND/AMBIGUOUS`; zero remain truthfully
`UNMEASURED`.  `BUILDOS_CODEX_DESKTOP_SESSION_FILE` is an explicit validated
file override for unusual environments.  Existing configured sources
(`BUILDOS_TELEMETRY_FILE`, `AI_BUILD_OS_CODEX_APP_SERVER_USAGE_FILE`, or
`AI_BUILD_OS_USAGE_FILE`) retain precedence.

Codex cumulative notifications are baselined at task and epoch binding.
Missing or malformed telemetry is reported as `UNMEASURED` or
`ADAPTER_BLOCKED`; it cannot change canonical lifecycle state.  CLI invocations
also append a `CONTROL` tool-action record, while productive model usage is
never fabricated when no source exists.  The detailed binding and field-replay
contract is in `docs/TELEMETRY_BINDING.md`.

Two optional static `SKILL.md` guides are included (`python-change-v122` and
`git-validation-v122`).  Selection is explicit; no registry, executable plugin,
or dynamic precedence exists.  Skill text is untrusted guidance and cannot
change risk, authorization, Git scope, lifecycle, or evidence rules.  The
kernel works with zero Skills.

Run the deterministic proof suite from this directory:

```powershell
python scripts/self_test.py
```

The candidate is ready for one real field benchmark only after the final
commit and clean-tree checks described in `docs/CANDIDATE_REPORT.md`.
