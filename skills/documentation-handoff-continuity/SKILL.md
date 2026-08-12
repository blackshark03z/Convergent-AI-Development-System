---
name: documentation-handoff-continuity
description: Mandatory operational sidecar for portable Build OS adoption. Use at material handoffs and before every product record-commit to preserve bounded Git continuity and documentation impact evidence.
---

# Documentation handoff continuity

This Skill is mandatory by the portable adoption contract, but is guidance and
an operational wrapper only: it is **not** Build OS kernel enforcement or a
security boundary. The frozen `buildos/` kernel remains authoritative for its
lifecycle and is intentionally unchanged.

Use `scripts/continuity.py` against a product worktree. It stores one bounded,
atomically replaced JSON projection in the Git common directory, never diffs,
source content, logs, reasoning, tokens, credentials, or an ever-growing diary.
The declared `accepted_ref` is only a selector; every checkpoint pins its
resolved SHA, so later ref movement cannot rewrite earlier meaning.

Normal flow: coherent implementation → documentation impact check → synchronize
candidate documentation → continuity checkpoint → ordinary product commit →
`record-commit` → deterministic `docs-check` during validation → validate →
close. A post-record documentation tree change starts a new revision.

Revision identity is canonical across every command: the numeric form `1` and
the equivalent sidecar form `r001` resolve to the observed Build OS revision and
the same `r001` path. An explicit revision that does not match the observed
Build OS revision fails closed; it is never treated as an unobserved lifecycle.

Legacy sidecars created by the pre-1.0.2 explicit-revision defect have one
separate, explicit migration: `quarantine-legacy`. It requires a clean live
worktree, verified original self-hash, terminal successor proof, accepted
containment, and explicit Tech Lead authority. It preserves the original bytes
and revision as `QUARANTINED_LEGACY`; it is not retirement and never claims the
historical revision was CLOSED.

Checkpoint only at bootstrap, material decisions, unclear dirty milestones,
blockers/handoffs, before long/side-effectful validation, lifecycle transitions,
and terminal retirement. Do not checkpoint every tool call, edit, test, or
trivial milestone. For takeover use `takeover`, which re-observes Git, policy,
Skill, sidecar and referenced evidence before allowing writes; it never rereads
the repository.

Keep the sidecar as a bounded current-state projection, not a transcript. Store
detailed evidence once outside the model working set, carry a short result plus
safe evidence pointer, and use deterministic checks for hashes, Git state,
sidecar schema and pointer existence. Do not reread long logs or historical
evidence unless a mismatch requires it.

## Working State Capsule

At task start, resume, takeover, compaction, or when prior conversation is
large, first obtain the read-only bounded projection:

```powershell
python skills/documentation-handoff-continuity/scripts/continuity.py --root <repo> --task-id <TASK> working-set
```

`capsule` is an equivalent command alias. It derives live Git, accepted-ref,
worktree and Build OS facts when rendered; it never writes, checkpoints, or
reconciles state. Normal output targets 2--4 KiB and never exceeds 8 KiB. It
contains only the current task/revision/phase, accepted and task anchors,
dirty/touched summaries, short decisions/blockers, documentation impact,
validation/evidence pointers, unresolved acceptance items and next action.
It excludes logs, diffs, full documents, chat history, full test output, full
Git history, evidence bodies, secrets and environment dumps.

Continue only when `status=SAFE_TO_CONTINUE`. On a mismatch, use the listed
`targeted_reads` to inspect the named authority or proof; do not replay the
Knowledge Pack, history, or evidence corpus. `TARGETED_READ_REQUIRED` means a
safety-critical source cannot fit or cannot be safely projected, so read only
the listed source. The capsule is a read-only derived projection over canonical
Build OS state, the Continuity Sidecar, policy, live Git and referenced proof;
it is never a second task-state authority.

Closeout is a bounded phase: run final required validation, write evidence
summaries/pointers, verify continuity and documentation gates, record/validate/
close, then report. Do not reconstruct all history at closeout. After native
compaction, continue in the same chat with current sidecar state and required
pointers only; do not replay the full Knowledge Pack. Field Study measurement
is cheap when direct metrics are available; deep forensics is conditional on an
anomaly, baseline, failure, recovery, or Tech Lead request.

`retire` preserves a small terminal proof only after a Build OS CLOSED candidate
is contained by the currently resolved accepted SHA. Until then status is
`CLOSED_PENDING_BASELINE_ADVANCE`. Field Study remains external, append-only and
non-authoritative; never use it for task authority or dirty recovery.
