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

## Optional lifecycle adoption

The repository includes a portable Lifecycle Kit, Continuity sidecar and
Context Epoch capability outside the frozen kernel. `adoption/initialize.ps1`
is the explicit enrollment path: it writes `.buildos-policy.json` with
`context_epoch.enabled: true`, creates the Project Knowledge Pack, and checks
the single active execution authority.

When that policy flag is absent or false, the regular Worker facade does not
run the context-epoch preflight. This preserves the original v1.22 flow for
small projects and trials. An operator may explicitly enable or disable the
guard for one invocation with `BUILDOS_CONTEXT_EPOCH_PREFLIGHT=1` or `=0`.
