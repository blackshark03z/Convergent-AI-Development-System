# Build OS vNext release candidate

An experimental simplification path now runs beside the v1.25 lifecycle path:

```powershell
python scripts/ai.py --root D:\path\to\product check `
  --base <commit-or-ref> --boundary R3 `
  --expected app.py --strict app.py --prohibited "secrets/**"
```

`check` derives `PASS`, `WARN`, or `BLOCK` only from the current Git delta and
the explicit path policy. It writes no Build OS state and does not execute the
requested boundary. See [docs/SIMPLIFICATION_PHASE_0.md](docs/SIMPLIFICATION_PHASE_0.md).

For one explicitly declared high-cost local action, use native argv after `--`:

```powershell
python scripts/ai.py --root D:\path\to\product high-cost `
  --base <commit-or-ref> --strict app.py -- python focused_check.py
```

The command is never semantically classified or retried. External effects are
outside this boundary's contract.

vNext evolves the v1.24 transactional candidate into an evidence-carrying Work
Loop:

`Tech Lead -> Work Contract -> Build OS -> Worker grounding -> implementation -> proportional assurance -> ship`

Point the repository-independent facade at a product repository; do not copy
generated control state into product source:

```powershell
python scripts/ai.py --root D:\path\to\product contract `
  --file .\WORK_CONTRACT.json --view worker-capsule

python scripts/ai.py --root D:\path\to\product work `
  --work-contract .\WORK_CONTRACT.json --grounding .\GROUNDING_REPORT.json
```

The candidate reserves `.buildos/` in the target repository and adds that
path to Git's local `info/exclude`.  A tracked `.buildos` path is rejected so
an existing product-owned control directory cannot be mistaken for OS state.
Project policy is optional and namespaced at `.buildos-policy.json`; absent
policy uses the field-tested defaults.

## Worker flow

The normal vNext surface is deliberately small:

- `contract` validates typed handoff/grounding evidence without writes.
- `work` starts or deterministically advances the normal lifecycle.
- `inspect` reports current Git/lifecycle/packet truth without any writes.

After implementation is committed, `work --assure` records the commit, runs
the bound proportional assurance and closes when safe. It never auto-dispatches
an external effect or adopts dirty/uncommitted product work. See
[docs/WORK_CONTRACT.md](docs/WORK_CONTRACT.md),
[docs/VNEXT_WORK_LOOP_ARCHITECTURE.md](docs/VNEXT_WORK_LOOP_ARCHITECTURE.md),
[docs/VNEXT_MIGRATION.md](docs/VNEXT_MIGRATION.md), and
[docs/VNEXT_PILOT_REPORT.md](docs/VNEXT_PILOT_REPORT.md).

An open canonical Decision Request survives every same-Contract grounding
refresh. The named authority may supply one trusted exact-request
`--decision-resolution`, or issue the next trusted Contract revision linked to
the active Contract and request hash. Both paths preserve immutable Decision
history; neither grants provider dispatch.

The detailed v1.24 commands remain compatibility and exceptional-operation
surfaces:

`admit`, `bootstrap`, `status`, `next`, `record-commit`, `validate`, `rollover`,
`close`, `recover`, `block-for-source-fix`, `continue-task`, `report-blocker`,
`replan`, `effect`, `review`, and `assurance-plan`.

The administrative facade additionally exposes `adopt-existing-change`,
`new-revision`, `abort`, and `telemetry-ingest`. A rollover always names a fresh disposable
`--thread-id`; this makes a retry distinguishable from a new epoch. Rollover is
a rare compact-failure fallback, not a normal request-count rhythm.

The legacy-compatible flow is:

1. `bootstrap` once (one kernel action).
2. Implement and commit product files with ordinary Git.
3. Run `status`/`next` at context checkpoints, then `record-commit`.
4. Run deterministic checks through `validate`; R3 also needs an independent
   reviewer, reference, and a distinct rollback/recovery check.
5. `close` after evidence is verified.

For expensive local work, set `--execution-class LOCAL_HIGH_COST`; for any
provider-side action, set `--execution-class EXTERNAL_EFFECT`. Both require an
`--execution-spec` that compiles assumptions, capabilities, field authority,
provider constraints, plan/recovery families, trusted argv commands and
acceptance claims before canonical task creation. Preview it without mutation:

```powershell
python scripts/ai.py --root D:\path\to\product admit `
  --task-id TASK-001 --outcome "the change is correct" --accept "behavior passes" `
  --execution-class LOCAL_HIGH_COST --execution-spec .\EXECUTION_SPEC.json `
  --allow src\app.py
```

The enhanced flow is `Prevent -> Bound -> Execute -> Reconcile -> Verify`.
Repeated blocker families invalidate the plan, unresolved provider effects
block assurance, and unchanged claim dependencies may reuse intact immutable
evidence while FINAL claims still execute. See
[docs/EXECUTION_RUNTIME.md](docs/EXECUTION_RUNTIME.md) and
[docs/VNEXT_ARCHITECTURE_AUDIT.md](docs/VNEXT_ARCHITECTURE_AUDIT.md).

Validation freezes one exact product HEAD/tree before any check runs. Every
executed check must leave that product identity unchanged; ignored `.buildos/`
test output remains permitted. Evidence and assurance bind the frozen identity,
and close may refresh only to a clean tree-equivalent descendant. In R3,
ordinary unchanged `AFFECTED` acceptance/security/QC claims remain reusable,
but `ROLLBACK_RECOVERY` always executes in the current revision.

Replan keeps the immutable task-base commit as its trust source while recording
the current allowed descendant/dirty product bytes separately as
`IN_PROGRESS_UNADOPTED`. It can therefore preserve valid work in place without
pretending that WIP is a trusted registry or adopted product commit. External
effects bind real provider-request, canonical-input and adapter implementation
artifacts; those bytes are rechecked before provider authority changes.

An explicitly runtime-only task uses `--no-source-delta`. It captures the
baseline product HEAD at bootstrap and may validate directly from `ACTIVE`
only when that exact HEAD remains current, the product tree is clean, and
`validate` receives a durable `--runtime-acceptance-reference`. Its canonical
state and evidence say `NO_SOURCE_DELTA`; `product_commit` remains empty. Empty
or synthetic commits, baseline-as-new-commit recording, and product drift all
fail closed. Ordinary write-capable tasks still require `record-commit` and
`PRODUCT_COMMITTED` before assurance.

R3 rules are unchanged: owner authorization, an independent reviewer and
reference, and a distinct rollback/recovery check remain mandatory. For a
runtime-only task the immutable review scope is
`NO_SOURCE_DELTA_RUNTIME_ASSURANCE`, so the review verifies runtime/lifecycle
proof and does not claim a nonexistent product diff.

There is no `reopen`.  A product change after assurance is preserved as proof
of the prior revision and requires `new-revision`; a legitimate tree-equivalent
descendant is simply recorded during close. For enrolled projects,
`new-revision` passes the same execution-authority and project-policy admission
as other authority mutations, plus context ownership when enabled. `abort` and
`recover` remain break-glass operations; status/next/assurance-plan and
telemetry ingestion remain diagnostic or observational.

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
does not prove human authorship, authorization, lifecycle, reviewer
independence, telemetry, or context interception. Project Git-bound commands
are therefore labelled `PROJECT_POLICY_TRUSTED`; historical `OWNER_AUTHORED`
input is only a compatibility alias. The Desktop governor is explicitly
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

New v1.24 policies also enable `execution_admission`: the normal Worker facade
composes package authority, project-policy compatibility, context ownership
where an existing epoch is required, and kernel execution-envelope admission.
These are separate checks behind one public workflow, not one interchangeable
admission object. Administrative recovery stays separately scoped;
`adopt-existing-change` uses the same adoption preflight while `abort` and
`recover` remain available to repair a broken adoption. Use
`-QualityGateArgvJson` during adoption so gates run without a shell. The legacy
`-QualityGate` string remains a clearly labeled compatibility path for existing
single-owner projects.

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
