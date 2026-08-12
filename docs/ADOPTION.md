# Unrelated-repository adoption

The candidate is intentionally installed outside the product repository.  The
minimum package is:

```text
buildos/                  # six stable modules plus CLI adapter
scripts/ai.py             # normal Worker facade
scripts/ai_os.py          # administrative facade
config/policy.json        # field defaults (package fallback)
skills/                   # optional static guidance only
```

No v1.21 `.ai` files, YouTube documents, prompts, templates, services, ports,
browser/media harnesses, or product source files are copied.  A caller points
the scripts at a target with `--root`.  On first bootstrap the kernel creates
only its reserved `.buildos/` control directory and a local Git exclude entry;
it rejects a dirty product baseline, a non-Git target, or a tracked
`.buildos` path. If a project needs explicit runtime headroom inputs, commit a
namespaced `.buildos-policy.json` before bootstrap. The
one-chat hybrid percentages are fixed; the file may declare a surface-provided
`context_window_tokens`, a larger known payload/output reserve, or a more
conservative fallback window. Legacy fixed 40k/64k/five-request/128k keys are
rejected so an old local file cannot silently restore the superseded governor.

At runtime, measured `model_context_window` takes precedence over configured W.
If neither exists, status labels the 128k compatibility bound
`CONSERVATIVE_FALLBACK` rather than claiming the active model window is known.
Missing current P remains truthfully unmeasured.

The supplied `--root` must be the Git worktree top-level. This keeps scope
patterns and the reserved control path unambiguous instead of silently making
them relative to an arbitrary subdirectory.

Optional repository-local Skill text may live at
`.buildos/skills/<id>/SKILL.md`, or a package Skill may be selected with the
explicit request field/CLI option.  The resolver reads at most 32KB and stores
its hash in the generated packet.  It never executes Skill code or accepts
Skill fields as policy.

The generic fixture shared by `tests/test_candidate.py` and
`tests/test_adversarial.py` contains only `app.py` and a small README. It
proves both a low-risk write task and an authorized R3 task,
normal product commits, descendant closeout, rollover, telemetry present and
absent, partial runtime repair, hard-process lock recovery, stale-pointer
recovery, scope/deletion checks, and immutable evidence preservation.

## Continuity adoption contract

The portable package includes the mandatory operational Skill
`documentation-handoff-continuity`, `adoption/initialize.ps1`, a policy example
and wrapper. Its sidecar is an atomically replaced bounded projection in the
Git common directory, never `.ai` or a tracked product file. It records both
the declared accepted-ref selector and the resolved SHA at checkpoint time.
It is not a kernel/security boundary and does not alter frozen `buildos/`.
Workers perform the impact check before `record-commit`; the injected
`docs-check` repeats deterministic validation during Build OS `validate`.

## Project Lifecycle Kit adoption

`adoption/initialize.ps1` now takes explicit project intent and an executable
quality gate, writes the single `.buildos-policy.json`, and invokes
`project-lifecycle-bootstrap`. The bootstrap creates only missing core
Knowledge Pack templates, preserving existing repository documentation and
marking unverified existing history `UNKNOWN`. It rejects absent accepted
baseline/SHA, gate, canonical authority mapping, safety boundary, continuity or
Field Study. See [PROJECT_LIFECYCLE_KIT.md](PROJECT_LIFECYCLE_KIT.md) for the
one canonical lifecycle specification and policy choices. For ordinary work,
the adopted guidance reads only relevant authorities, persists detailed command
output as evidence with short summaries/pointers, and keeps task briefs focused
on product-specific objectives, constraints, and acceptance criteria.
