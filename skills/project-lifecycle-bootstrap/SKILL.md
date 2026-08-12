---
name: project-lifecycle-bootstrap
description: Establish or adopt the bounded Project Lifecycle Kit operating contract around frozen Build OS v1.22. Use for greenfield setup, existing-project adoption, accepted-baseline reconciliation, quality-gate verification, and explicitly requested project retirement.
---

# Project lifecycle bootstrap

Project Lifecycle Kit v1.0.4 is mandatory by the portable adoption contract,
not kernel-enforced security. It does not modify frozen `buildos/` and it does
not replace `documentation-handoff-continuity v1.0.0`, which remains the sole
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

Converge validation as one coherent slice: inspect, implement, focused tests,
fix relevant failures, integrated relevant validation, final acceptance, close.
Re-run only after relevant change, failure, staleness or a final clean-pass
requirement. Batch adjacent safe deterministic operations, never risky actions.

Before a Worker takes over, run the portable execution-authority preflight.
Use only its recorded v1.22 executor; legacy project CLIs and `.ai` state are
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

Bootstrap reads the existing `.buildos-policy.json`; it never creates a second
project-policy authority. It refuses normal adoption without a resolved
accepted baseline, meaningful executable gates, all required documentation
impact mappings, defined runtime/data/production safety boundaries, enabled
continuity, or default-on external Field Study. Tech Lead decisions must be
made in that policy, explicitly and durably.

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
