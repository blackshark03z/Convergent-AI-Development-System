---
name: project-lifecycle-bootstrap
description: Establish or adopt the bounded Project Lifecycle Kit operating contract around Build OS v1.25 Work Loop candidate. Use for greenfield setup, existing-project adoption, accepted-baseline reconciliation, integrated execution admission, quality-gate verification, and explicitly requested project retirement.
---

# Project lifecycle bootstrap

Project Lifecycle Kit v1.4.0 is mandatory by the portable adoption contract,
not kernel-enforced security. It does not replace
`documentation-handoff-continuity v1.1.0`, which remains the sole
authority for active operational intent.

Read `docs/PROJECT_LIFECYCLE_KIT.md` for the authority model and the bounded
takeover path. At normal task startup, read the bounded status/engineering
entry, only the relevant architecture section, task-specific authorities, and
an active sidecar. Read ROADMAP, CHANGELOG, OPERATIONS, or other Knowledge Pack
material only when the impact check or a pointer requires it; do not reconstruct
state from chats, Git history, raw evidence, or every ADR.

Keep a bounded working set: objective, phase, constraints, touched-file summary,
short decisions and validation summary, evidence pointers, and next action.
Persist detailed command output once as an evidence file, then retain only a
bounded summary and pointer. Use scripts/state inspection for hashes, refs,
Git status, manifests, schemas and evidence existence; do not reread contents
when only deterministic state is needed. Keep task briefs product-specific;
the adopted lifecycle guidance supplies the stable operating rules.

For normal start/resume/takeover or post-compaction rehydration, first obtain
the Continuity Skill's read-only `working-set` (or `capsule`) projection. It
derives bounded live facts and targeted pointers; read only those authorities
or proofs afterward. Never use it as a second mutable state file, and do not
silently omit a mismatch or blocker to stay small.

For a long task at an existing governor `COMPACT_REQUIRED` or `HARD_STOP`, do
not hand-copy a compacted chat. First complete native compaction, then make one
real bounded readiness/productive request and measure its latest prompt. Stay
when the governor is `CONTINUE` or `HEADROOM_WARNING`. Only when material work
remains, the current atomic operation is complete, and the post-compaction
measurement remains cut-eligible, use `scripts/context_epoch.py handoff` with
its required bounded proof pointers. A closeout-only task stays in-context when
safe; it may use one epoch only when its measured unsafe continuation is paired
with unavailable/ineffective compaction. It creates a fresh zero-history Codex
thread, retains the exact Goal objective, rehydrates only through the Capsule
and its targeted reads, and fences the predecessor. Never use `thread/fork`.

Converge validation as one coherent slice: inspect, implement, focused tests,
fix relevant failures, integrated relevant validation, final acceptance, close.
Re-run only after relevant change, failure, staleness or a final clean-pass
requirement. Batch adjacent safe deterministic operations, never risky actions.

Before a Worker takes over, use the public `scripts/ai.py` facade. A v1.25
policy enables integrated admission so this one path composes execution
authority, project policy and context ownership before mutation. Use only its
recorded v1.25 executor; legacy project CLIs and `.ai` state are
never fallback authorities, and version mismatch or ambiguity is a Tech Lead
blocker. Archives and historical documents are provenance only.

Use `scripts/project_lifecycle.py`:

```powershell
python skills/project-lifecycle-bootstrap/scripts/project_lifecycle.py --root <repo> check
python skills/project-lifecycle-bootstrap/scripts/project_lifecycle.py --root <repo> bootstrap --mode greenfield --verify-gates
python skills/project-lifecycle-bootstrap/scripts/project_lifecycle.py --root <repo> reconcile --candidate-sha <sha>
python skills/project-lifecycle-bootstrap/scripts/project_lifecycle.py --root <repo> advance --expected-old-sha <sha> --target-sha <sha>
python skills/project-lifecycle-bootstrap/scripts/project_lifecycle.py --root <repo> retire-project --confirm
```

For an existing repository that still has supported v1.16-style callable
authority, read `docs/LEGACY_TERMINALITY_AND_ADOPTION.md` and use the dedicated
bridge before ordinary bootstrap:

```powershell
python skills/project-lifecycle-bootstrap/scripts/legacy_authority_bridge.py --root <repo> inspect
python skills/project-lifecycle-bootstrap/scripts/legacy_authority_bridge.py --root <repo> prepare --transition-id <id>
python skills/project-lifecycle-bootstrap/scripts/legacy_authority_bridge.py --root <repo> retire --transition-id <id>
```

Preparation is product-read-only. Never infer authorization to terminalize a
BLOCKED Goal: it requires the exact `--terminalize-blocked-goal` flag and a
specific `--authorization-reference`. Commit the verified retirement receipt
before initialization. After normal v1.25 bootstrap, run bridge `finalize` to
bind the first selected generation. Do not copy, edit, or manufacture either
receipt by hand, and do not revive legacy authority after activation.

Bootstrap reads the existing `.buildos-policy.json`; it never creates a second
project-policy authority. It refuses normal adoption without a resolved
accepted baseline, meaningful executable gates, all required documentation
impact mappings, defined runtime/data/production safety boundaries, enabled
continuity, or default-on external Field Study. Tech Lead decisions must be
made in that policy, explicitly and durably.

Prefer quality gates as a trusted `argv` list with `PROJECT_POLICY_TRUSTED` or
`PACKAGE_OWNED` provenance. The exact legacy shell-command shape remains a
labeled migration path only; an autonomous model must not silently author it.

Projects with externally visible, destructive, billable, or non-idempotent
effects must use `--execution-class EXTERNAL_EFFECT` and a compiled execution
spec. The canonical effect ledger makes unknown dispatch a queue barrier;
retry requires provider-enforced same-key idempotency or positive canonical
no-effect proof. The older `side_effect_contract` policy remains a static
compatibility contract, not a runtime ledger. A project-specific provider
name, request ID, status string, or heuristic is evidence input, never a
replacement for the semantic authority predicate.

For an existing repository, inspect Git and source first. Bootstrap writes only
missing canonical templates and labels unverified history/capabilities as
`UNKNOWN`; it never invents history. For a greenfield repository, create the
baseline commit before treating it as accepted. Do not run `retire-project`
unless retirement is explicitly requested.

When `accepted_ref` advances, run `reconcile`. Git's live `rev-parse` resolution
is machine authority; tracked PROJECT_STATUS, CHANGELOG and ROADMAP carry stable
semantic state and never self-pin the SHA of their containing commit. Reconcile
only lists semantic updates required for those documents.
After the Worker/Tech Lead makes and verifies those updates, checkpoint the
sidecar against the new state and retire it through the continuity Skill.
