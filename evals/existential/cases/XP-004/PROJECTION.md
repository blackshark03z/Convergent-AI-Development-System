# XP-004 Neutral Projection

Pinned AutoVideoPipeline base: `79ac228d14b1ac743ab760bc4c87f87adc433533`.

The runner archives the pinned commit, not the current product working tree.
It removes the process-control files `AGENTS.md` and `TASK.md` and the
`.agents/` directory. Product code, tests, format specifications, architecture,
and ordinary engineering tooling remain in the snapshot.

Qualified neutral tree: `5b60e9938fdef5b60250805d3490f55bc4aefcef`.
Qualification projection commit: `734054913dc039f8e7aa3e8c5774dc4c1419d35d`.

Qualification used disposable local base and historical-reference snapshots
under the same hidden behavioral oracle. Base FAIL and reference PASS are
recorded in PRECHECK.json. Reference bytes, diff and oracle files are absent
from the R/I neutral projection and prompts.
