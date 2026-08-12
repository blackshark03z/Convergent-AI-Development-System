# Project Lifecycle Kit

Project Lifecycle Kit v1.0.4 is the portable adoption layer around frozen Build
OS v1.22. It is mandatory by the adoption contract, not kernel-enforced
security. `buildos/` continues to own task, revision, lifecycle and immutable
validation evidence.

## Authorities and bounded reading path

Long-lived accepted project knowledge is the configured Knowledge Pack. Normal
task startup reads the bounded status/engineering entry, only the architecture
section relevant to the touched area, task-specific canonical docs, and the
active continuity sidecar when a task is active. Read ROADMAP, CHANGELOG,
OPERATIONS, or the rest of the pack only when the documentation-impact check or
a pointer requires them; `CHANGELOG.md` is accepted-history context, not a
default takeover read.

| Concern | Authority |
| --- | --- |
| Accepted current product state | `PROJECT_STATUS.md` |
| Planned direction | `ROADMAP.md` |
| Current accepted architecture | `ARCHITECTURE.md` and enabled ADRs |
| Engineering contract and executable gates | `ENGINEERING.md` and project policy |
| Accepted change history | `CHANGELOG.md` |
| Active task intent and handoff | `documentation-handoff-continuity` sidecar |
| Validation proof and task lifecycle | frozen Build OS evidence and CURRENT generation |
| Learning | external append-only Field Study |
| Actual bytes | live Git worktree |

Do not copy dirty state, raw evidence, session history, or sidecar content into
the Knowledge Pack. Do not make ROADMAP or CHANGELOG assertions about current
product behavior that belong in PROJECT_STATUS.

## Bounded worker working set

Keep the active model working set bounded. Retain the objective, phase,
relevant constraints, touched-file summary, short decisions, short validation
summary, evidence pointers, and next action. Persist detailed command output
once and retain a bounded summary plus a pointer; do not load or reread full
logs merely because they exist. Use deterministic tooling directly for hashes,
Git state, refs, manifests, sidecar schema, and evidence existence instead of
asking the model to reconstruct those facts from file contents.

The normal rehydration entrypoint is the Continuity Skill's read-only
`working-set` (or `capsule`) command. It derives a deterministic, model-facing
Working State Capsule from live Git, Build OS state and the active sidecar,
without creating another mutable task-state authority. Read the capsule first,
then only the authority sections or evidence pointers it names. A capsule is
normally 2--4 KiB and hard-limited to 8 KiB; bounded lists declare overflow.
If a safety-critical source will not safely fit, it returns
`TARGETED_READ_REQUIRED` with exact pointers rather than silently omitting
truth. A stale sidecar versus live Git or Build OS is exposed as a mismatch and
is never silently reconciled.

Use one coherent validation convergence loop: inspect, implement a coherent
slice, run focused tests, fix relevant failures, run integrated relevant
validation, perform one final acceptance pass, then close. Re-run a check only
after relevant change, a failure, a stale result, or a required final clean
pass. Batch adjacent safe deterministic discovery, status, hash, and test
operations, but never batch destructive or high-risk actions for efficiency.

Closeout is bounded: final required validation, evidence summaries and
pointers, continuity/documentation gates, record/validate/close, and one final
report. Do not reconstruct the entire task history or reread historical
evidence unless a deterministic mismatch requires it. Material-event
continuity checkpoints remain the recovery aid; do not add checkpoint history
or checkpoint every model/tool call.

After native compaction, continue in the same chat and rehydrate only current
state and required pointers. Do not replay the full Knowledge Pack or evidence,
and do not turn a historical prompt peak into a rollover reason. The frozen
governor, its thresholds, one-chat-first policy, and rollover semantics are
unchanged.

Task briefs should contain the product objective, task-specific constraints,
and acceptance criteria; stable safety, documentation-impact, continuity,
evidence, closeout, Field Study, and context-efficiency rules live here and in
the adopted Skills. This keeps Tech Lead prompts concise without weakening
acceptance.

## Field Study and observed efficiency

Every terminal task receives a cheap Field Study eligibility check. Record
directly available metrics only: execution mode, model, model requests, tool
actions, raw/cached/noncached input, output, reasoning, cache ratio, observed
prompt peak, automatic compactions, rollovers, closeout requests, and closeout
input. A metric unavailable without expensive reconstruction is `UNKNOWN`.
Deep forensic reconstruction is only for anomaly, baseline, failure, recovery,
or a Tech Lead request; Field Study remains external, append-only, default-on,
and non-authoritative.

Existing field traces classify as follows, without claiming a kernel defect:

| Existing trace | Classification |
| --- | --- |
| 108-call Cinematic Lens / Atmosphere goal | `HIGH_CONTEXT/CLOSEOUT_OVERHEAD — OBSERVE/AVOID PATTERN` |
| 25-call Editorial Impact Stack goal | `HEALTHY BOUNDED EXECUTION` |
| 19-call Lifecycle Reconciliation goal | `HEALTHY BOUNDED EXECUTION` |

## Adoption contract

`project-lifecycle-bootstrap` reads the existing `.buildos-policy.json` and
adds no competing policy file. The policy retains `documentation_handoff` as
the single accepted-ref and documentation-category-map authority. Its optional
`project_lifecycle` object supplies profile, Knowledge Pack paths, quality
gates, safety boundaries and modules.

Normal adoption must have a resolving accepted ref/SHA, one or more executable
quality-gate commands, all five documentation-impact mappings, canonical core
document paths, defined production/data/runtime boundaries, enabled continuity,
and default-on external Field Study. These are mandatory by adoption contract,
not a kernel security boundary. Tech Lead choices remain explicit in policy:
paths, profile, ref, gates, testing strategy, boundaries, modules, release
flow and project-specific engineering rules.

## Single active execution authority

`SINGLE_ACTIVE_EXECUTION_AUTHORITY` is a mandatory fail-closed adoption
invariant. `initialize.ps1` writes `.buildos-authority.json`, binding the
portable package root, v1.22 kernel commit, lifecycle-kit version, facade hash,
and the sole resolution rule: `python <package_root>/scripts/ai.py --root
<project-root> <lifecycle-command>`. The paired `ai_os.py` is an administrative
facade from that same package authority, not a second authority.

Run `python skills/project-lifecycle-bootstrap/scripts/execution_authority.py
--root <repo> check` before Worker takeover and before lifecycle operations.
It rejects callable project-local legacy CLIs, legacy `.ai` operational state,
conflicting Worker instructions, missing/incorrect package identity, and any
non-unique executor. It deliberately does not scan archival roots or historical
documentation, which are provenance only. If the record cannot resolve, do not
fall back to PATH or another Build OS version; stop for Tech Lead action.

## Lifecycle

`task bootstrap -> continuity checkpoint -> implementation -> focused evidence
-> documentation impact check -> synchronize affected canonical authorities ->
continuity checkpoint -> product commit -> record-commit -> deterministic
continuity/docs recheck -> validate -> close -> CLOSED candidate -> accepted
baseline integration -> accepted knowledge reconciliation -> continuity
retirement`.

Build OS `CLOSED`, inclusion in `accepted_ref`, and release/deployment are
different events. A CLOSED candidate not contained by the resolved accepted
SHA is `CLOSED_PENDING_BASELINE_ADVANCE`. When the accepted ref advances,
`reconcile` deterministically lists semantic updates; a Worker or Tech Lead
performs semantic status/changelog/roadmap updates. The helper never fabricates
prose and never requires tracked docs to self-pin their containing commit SHA. A
new continuity checkpoint follows reconciliation before
the active sidecar is retired.

## Profiles and modules

`small-tool`, `library`, `desktop-app`, `production-app`, `service`, and
`custom` are bounded profile labels, not technology assumptions. Core files
are always concise. Optional modules are `operations`, `adr`, `security`,
`migrations`, `project_closure`, and `project_brief`. Only enabled modules
receive templates. Closure is explicitly invoked; it is never generated during
ordinary bootstrap. The project brief is optional because README plus the
policy `project_intent` is the economical default intent authority.

Operations/release is enabled only for projects with meaningful runtime,
deployment, persistent-data or recovery responsibilities. It describes
accepted baseline, version/artifact, migration, deployment, verification,
rollback and health as applicable; it does not change the Build OS lifecycle.

## Existing repositories and retirement

Existing adoption inspects Git and seeds the resolved accepted SHA. Unknown
historical capabilities, roadmap and history are written as `UNKNOWN`, never
invented. Reconcile them incrementally from verified reality.

`retire-project` is explicit. It creates the mapped closure record only after
confirmation and records final accepted SHA/tag, archive/rebuild guidance,
artifact hashes, runtime shutdown, backups, data disposition, secret exclusion,
limitations and restore/handoff instructions as applicable.
