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
`.buildos` path.  If a project needs thresholds different from the package
defaults, commit a namespaced `.buildos-policy.json` before bootstrap.  That
file can tighten, never weaken, the kernel maxima.

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
