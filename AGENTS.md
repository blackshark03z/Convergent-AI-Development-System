# Worker operating map

On first contact, new Tech Lead/Worker session, or stale/unknown context, **MUST**
run [`skills/core/project-cold-start.md`](skills/core/project-cold-start.md)
before planning or implementation. Reconstruct from current reality; completion
is not persisted authority.

Mandatory routing:

- New/materially changed Goal or missing acceptance -> `skills/core/product-goal-framing.md`.
- Before materially stabilizing new/changed architecture, domain, source-of-truth, ownership, or authority, or after a material assumption changes -> `skills/core/concern-coverage-review.md`.
- Established Goal implementation -> `skills/core/goal-execution.md`.
- Bug/regression/failing test/unexpected runtime/provider behavior -> `skills/core/systematic-debugging.md`.
- Before material `FIXED`/`DONE`/ready/completion claim -> `skills/core/product-acceptance.md`.
- Workspace bloat/competing worklines/Goal closure residue -> `skills/core/workspace-hygiene.md`.
- Multi-step user outcome or changed journey/navigation/discoverability -> `skills/product/user-facing-workflow.md` at whole-journey composition level.
- Changed screen/component/interaction/responsive layout/visual hierarchy -> `skills/product/frontend-design.md`.
- Before user-facing Product Acceptance or when usability/accessibility/recovery is doubtful -> `skills/product/ui-quality-review.md`.
- Accepted material direction that must survive turnover -> Decision Record under `docs/decisions/` using `docs/DECISION_CONTINUITY.md`.
- Explicit consequential action -> existing CADS Thin Guard; routing never expands guard authority.

When triggers overlap: reconstruct context first; frame Goal and applicable domain
semantics before material design freeze; run Concern Coverage Review before that
freeze; resolve whole user workflow before visual implementation; debug actual
defects scientifically; run UI Quality Review before user-facing Product
Acceptance. Do not run journey/design review after every tiny edit. All playbooks
are advisory, not persisted lifecycle state.

Canonical commands:

```powershell
python scripts/ai.py --root . inspect
python scripts/self_test.py
python scripts/ai.py --root . check --base <sha> --boundary R3 --policy <file>
```

Normal edits, focused tests and ordinary commits use native tools. CADS is
invoked only at an explicitly declared consequential boundary.

Stable invariants:

- Owner owns desired outcome, material product trade-offs, consequential authorization and subjective real-use acceptance; AI Tech Lead owns missing engineering-concern discovery and ordinary engineering choices within that intent.
- Identified Git/source owns implementation reality; identified runtime owns observed behavior; tests/CI provide verification evidence.
- Goal-defined acceptance determines completion; `TASK.md` is current context, not runtime authority.
- Accepted Decision Records own durable rationale/settled material direction; chat memory and agent reports do not.
- `expected_paths` warns; `strict_paths` and `prohibited_paths` block.
- Tracked `.buildos/**` changes cannot cross a guarded boundary.
- High-cost local actions re-observe immediately before native spawn.
- External intent is durable before dispatch; ambiguity is never blindly retried.
- No lifecycle state, generations, adoption, continuation, grants or migration.

Follow [`docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`](docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md).
Durable architecture belongs in `ARCHITECTURE.md`; temporary progress in
`TASK.md`. Do not build parsers, schemas or migrations around task prose.
