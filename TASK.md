# Repository Status

**CADS is RETIRED / END-OF-LIFE as an active development architecture as of 2026-09-24.**

There is no active CADS product-development Goal.

Canonical closure decision:

- `docs/decisions/0015-retire-cads-active-architecture.md`

Canonical existential evidence:

- `docs/CADS_EXISTENTIAL_FINAL_DISPOSITION_2026-09-24.md`
- `docs/CADS_EXISTENTIAL_P1_RESULTS_2026-09-24.md`
- `evals/existential/`

## Allowed future work in this repository

Only archival integrity, factual documentation corrections, security-sensitive
archival fixes, and bounded extraction of reusable knowledge are in scope.

Do not:

- bootstrap new projects onto CADS;
- add or revive CADS controls, lifecycle/state machinery, routing/governance
  layers, benchmark infrastructure, or generalized framework code;
- treat this repository as the default development workflow;
- rerun the closed XP-001..XP-005 corpus to manufacture a stronger verdict.

## Successor direction

Future development work should use the smaller AI-native model based primarily on
existing Git/CI/provider/runtime primitives:

`Owner idea -> AI Tech Lead -> frozen acceptance -> isolated worker -> Git candidate -> protected verifier -> exact verified source/artifact -> promotion -> product -> feedback`

Reusable CADS knowledge may be extracted only as small independent pieces, most
notably AI Tech Lead discovery/acceptance framing and task-local external-effect
safety where the task truly requires it.
