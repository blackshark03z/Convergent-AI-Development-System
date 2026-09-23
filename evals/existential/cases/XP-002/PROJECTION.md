# XP-002 Neutral Projection

Pinned product base: `eb0a6480962612865a4974c960e6c6547b7b2009`

The benchmark projects the pinned Git commit, not the current AutoVideoPipeline working tree.

Removed only process-control artifacts that would contaminate the arm treatment:

- `AGENTS.md`
- `TASK.md`
- `.agents/`

Product code, product tests, architecture/specification documents, and normal engineering tooling remain available as product reality.

Qualified neutral identity:

- projection commit: `48bcc66a0bc364d5edd85476cea52f025bd739c5`
- tree: `57f32d1190646df8c35cba75a1190c5a07b15000`

Qualification used the same held-out behavioral oracle against a disposable base snapshot and a disposable historical-reference snapshot. Base failed and reference passed. Neither historical patch bytes nor oracle files are copied into the neutral projection shown to R/I.
