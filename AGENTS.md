# Worker operating map

On first contact, new Tech Lead/Worker session, or stale/unknown context, **MUST**
run [`skills/core/project-cold-start.md`](skills/core/project-cold-start.md) to
reconstruct current reality before planning or implementation.

Use one small control model; these are reasoning controls, not persisted phases:

1. **Reality** -> Project Cold-Start when context is new/stale; Workspace Hygiene
   only when bloat, competing worklines, or closure residue is actually present.
2. **Intent / Design** -> `skills/core/product-goal-framing.md` as the adaptive Intent Boundary for a new/changed Goal, missing acceptance, material uncertainty, or expensive-to-recover design; scale depth by its Risk Envelope and use `skills/core/architecture-description.md` only when durable system shape is material.
3. **Change** -> `skills/core/goal-execution.md` for the smallest coherent change;
   use `skills/core/systematic-debugging.md` conditionally for an actual defect,
   then resume the same Goal.
4. **Acceptance** -> `skills/core/product-acceptance.md` before a material `FIXED`/`DONE`/product-ready claim. Bind evidence to its oracle/candidate and add affected system-fitness evidence before canonical promotion when cross-cutting invariants change; use `skills/core/release-qualification.md` only for a separate material release boundary.
5. **Consequence** -> existing CADS Thin Guard only for applicable destructive,
   external, privileged/security-sensitive, or explicitly high-cost effects.

Conditional product/UI methods:

- changed journey/navigation/discoverability -> `skills/product/user-facing-workflow.md`;
- changed screen/component/interaction/layout -> `skills/product/frontend-design.md`;
- before user-facing acceptance or when usability/accessibility/recovery is in doubt -> `skills/product/ui-quality-review.md`.

Product / Design Framing must preserve Knowledge-Gap Responsibility: the Owner
is not expected to provide engineering expertise. The AI Tech Lead identifies
material design drivers and assumptions proportionally to consequence. When
applicable this includes domain identity/cardinality/ownership, repeatable-workflow
state lifetime/reset/re-entry/stale-state isolation, data/source-of-truth,
security/external-effect ambiguity and idempotency, concurrency/resource
ownership/fencing/recovery, quality evidence, and economy. Tiny reversible work
does not pay for irrelevant lenses. If targeted investigation identifies a
materially useful reusable external Agent Skill, route persistent use through
`skills/core/external-skill-acquisition.md`; stack detection alone is not
installation authority.

Feature/subsystem PASS does not establish Journey/Product PASS. Tests/CI provide
verification evidence; identified runtime provides observed behavior; predefined
Goal acceptance determines completion. Accepted material direction that must
survive turnover belongs in a Decision Record under `docs/decisions/`.

Canonical commands:

```powershell
python scripts/ai.py --root . inspect
python scripts/self_test.py
python scripts/ai.py --root . check --base <sha> --boundary R3 --policy <file>
```

Normal edits, focused tests and ordinary commits stay native. Owner owns desired
outcome, material product trade-offs, consequential authorization and subjective
real-use acceptance; AI Tech Lead owns missing engineering-concern discovery and
ordinary engineering judgment within that intent. Identified Git/source owns
implementation reality; `TASK.md` is current context, not runtime authority.

Follow [`docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`](docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md).
Durable architecture belongs in `ARCHITECTURE.md`; temporary progress in
`TASK.md`. No routing result creates lifecycle state, grants, adoption, or a
second runtime.