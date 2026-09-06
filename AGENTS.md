# Worker operating map

On first contact, in a new Tech Lead/Worker session, or whenever prior context
is unknown or stale, **MUST** follow
[`skills/core/project-cold-start.md`](skills/core/project-cold-start.md) before
planning or implementation. Rerun it from current reality; completion is not
persisted authority.

Mandatory procedure routing:

- First contact, new session, or stale/unknown context -> `skills/core/project-cold-start.md`.
- New/materially changed Goal or missing acceptance -> `skills/core/product-goal-framing.md`.
- Normal implementation under an established Goal -> `skills/core/goal-execution.md`.
- Bug, regression, failing test, or unexpected runtime/provider behavior -> `skills/core/systematic-debugging.md`.
- Before a material `FIXED`/`DONE`/product-ready/completion claim -> `skills/core/product-acceptance.md`.
- Workspace bloat, competing worklines, or Goal closure residue -> `skills/core/workspace-hygiene.md`.
- Explicit consequential action -> the existing CADS Thin Guard; procedure routing never expands guard authority.

If more than one trigger applies, reconstruct trustworthy context first, then use
the procedure closest to the current decision. These procedures are advisory
playbooks, not persisted lifecycle state.

Canonical commands:

```powershell
python scripts/ai.py --root . inspect
python scripts/self_test.py
python scripts/ai.py --root . check --base <sha> --boundary R3 --policy <file>
```

Normal edits, focused tests and ordinary commits use native tools. CADS is
invoked only at an explicitly declared consequential boundary.

Stable invariants:

- Owner/Tech Lead owns desired outcome; identified Git/source owns implementation reality.
- Identified runtime evidence owns observed behavior; tests/CI provide verification evidence.
- Goal-defined acceptance determines completion; `TASK.md` is current context, not runtime authority.
- `expected_paths` warns; `strict_paths` and `prohibited_paths` block.
- Tracked `.buildos/**` changes cannot cross a guarded boundary.
- High-cost local actions re-observe immediately before native spawn.
- External intent is durable before dispatch; ambiguity is never blindly retried.
- No lifecycle state, generations, adoption, continuation, grants or migration.

Follow the canonical development standard in
[`docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`](docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md).
Durable architecture belongs in `ARCHITECTURE.md`. Keep temporary progress in
`TASK.md`; do not build parsers, schemas or migrations around it.
