# Worker operating map

On first contact, in a new Tech Lead/Worker session, or whenever prior context
is unknown or stale, **MUST** follow
[`skills/core/project-cold-start.md`](skills/core/project-cold-start.md) before
planning or implementation. Rerun it from current reality; completion is not
persisted authority.

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
