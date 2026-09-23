# XP-001 Neutral Product Projection

All four arms use the same source projection from Story Audio base
`b6a9efb1de053edccbf9541deaaf21a830d71727`.

## Remove from the neutral projection

The following are treatment/process artifacts, not required product runtime
inputs for this case:

- `.buildos-authority.json`
- `.buildos-legacy/`
- `.buildos-policy.json`
- root `AGENTS.md`
- root `TASK.md`
- root `NEXT_TASK.md`
- `skills/`
- `templates/`

## Keep

Keep product code, tests, scripts, UI assets, build configuration and ordinary
product/developer documentation, including `README.md`, `ARCHITECTURE.md`,
`ENGINEERING.md`, `ROADMAP.md`, `PROJECT_STATUS.md`, `docs/`, `prompts/`,
`config/`, `story_audio/`, `scripts/`, `tests/`, `tools/`, and `ui/`.

The goal is not to erase product knowledge. The goal is to prevent a No-CADS arm
from silently receiving the CADS/Build-OS control mechanism being tested.

## Projection validation

Before any arm runs:

1. create the neutral projection once;
2. initialize it as a fresh Git repository so deleted historical control files
   cannot be recovered through Git history;
3. run the relevant existing base tests/browser smoke;
4. require behavior-equivalence for the focused product surface;
5. clone that exact neutral commit into four disposable arm workspaces.

If removing these process artifacts changes the focused product behavior, revise
the projection before any arm runs or mark XP-001 INCONCLUSIVE.
