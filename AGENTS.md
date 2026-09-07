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
- Multi-step user-facing Goal where multiple capabilities compose into one outcome, or a new/materially changed user journey, navigation, or discoverability problem -> `skills/product/user-facing-workflow.md` at the whole-journey/composition level before isolated capabilities are treated as a complete product.
- New/materially changed screen, component, interaction, responsive layout, or visual hierarchy -> `skills/product/frontend-design.md`.
- Before user-facing Product Acceptance, or when usability/accessibility/recovery quality is in doubt -> `skills/product/ui-quality-review.md`.
- Accepted material direction that could change a later session's approach -> persist a Decision Record under `docs/decisions/` using `docs/DECISION_CONTINUITY.md`; this is cross-cutting, not a new lifecycle phase.
- Explicit consequential action -> the existing CADS Thin Guard; procedure routing never expands guard authority.

If more than one trigger applies, reconstruct trustworthy context first. Frame the
Product Goal before UI work; resolve the whole user journey/information
architecture before visual implementation; use Systematic Debugging for actual
defects; run UI Quality Review before user-facing Product Acceptance. Apply
User-Facing Workflow at the Goal/journey composition level, not after every tiny
UI edit. These procedures are advisory playbooks, not persisted lifecycle state.

Canonical commands:

```powershell
python scripts/ai.py --root . inspect
python scripts/self_test.py
python scripts/ai.py --root . check --base <sha> --boundary R3 --policy <file>
```

Normal edits, focused tests and ordinary commits use native tools. CADS is
invoked only at an explicitly declared consequential boundary.

Stable invariants:

- Owner owns desired outcome, material product trade-offs, consequential authorization, and subjective real-use acceptance; the AI Tech Lead owns discovery of missing engineering concerns and ordinary engineering choices within that intent. Identified Git/source owns implementation reality.
- Identified runtime evidence owns observed behavior; tests/CI provide verification evidence.
- Goal-defined acceptance determines completion; `TASK.md` is current context, not runtime authority.
- Accepted Decision Records own durable rationale/settled material direction; chat memory and agent reports do not.
- `expected_paths` warns; `strict_paths` and `prohibited_paths` block.
- Tracked `.buildos/**` changes cannot cross a guarded boundary.
- High-cost local actions re-observe immediately before native spawn.
- External intent is durable before dispatch; ambiguity is never blindly retried.
- No lifecycle state, generations, adoption, continuation, grants or migration.

Follow the canonical development standard in
[`docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`](docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md).
Durable architecture belongs in `ARCHITECTURE.md`. Keep temporary progress in
`TASK.md`; do not build parsers, schemas or migrations around it.
