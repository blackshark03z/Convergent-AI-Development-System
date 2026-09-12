# Project operating map

This root `AGENTS.md` is the minimum CADS activation contract. On first contact
or stale context, reconstruct current repository/runtime truth before planning.
When the CADS skill library is reachable, open the routed playbook for detail;
otherwise follow this minimum contract and do not claim an unavailable playbook
was executed.

Knowledge-gap responsibility is mandatory: the Owner is not expected to supply
missing engineering expertise. The AI Tech Lead investigates material concerns,
resolves ordinary engineering choices within Owner intent/authority, and asks the
Owner only for missing product facts, material trade-offs, or consequential
Owner-controlled choices. If reusable external specialist instructions are used,
they remain advisory; stack detection alone does not authorize persistent install,
and exact reusable content must be vetted/pinned before persistent use.

Use five reasoning controls, not a persisted lifecycle:

1. **Reality** — cold-start from `TASK.md`, `ARCHITECTURE.md`, active Decision
   Records, Git/source, tests/CI evidence and identified runtime. Use Workspace
   Hygiene only for actual bloat, competing worklines, or closure residue.
2. **Intent / Design** — frame one bounded Goal/CUJ/acceptance and identify only
   material, expensive-to-get-wrong design drivers before stabilizing an
   architecture/domain/source-of-truth/ownership/authority decision.
3. **Change** — make the smallest coherent change under the Goal; debug
   scientifically only when an actual defect exists, then resume the same Goal.
4. **Acceptance** — prove the real supported path; isolated feature/subsystem PASS
   does not establish Journey/Product PASS.
5. **Consequence** — use the existing Thin Guard only for applicable destructive,
   external, privileged/security-sensitive, or explicitly high-cost effects.

When full CADS skills are available, route Intent / Design to Product / Design Framing
(`skills/core/product-goal-framing.md`) and use `skills/core/architecture-description.md`
conditionally for material durable system shape/technology/runtime/state/deployment
architecture; route Change to Goal Execution, actual defects to Systematic Debugging,
material completion to Product Acceptance, release-bound readiness to
`skills/core/release-qualification.md` when a material release boundary exists,
and actual workspace convergence problems to Workspace Hygiene. User-Facing Workflow, Frontend Design
and UI Quality Review remain conditional product/UI methods, not universal phases.

For material design framing, ask what must be true and what becomes expensive or
unsafe if it is false. Apply only relevant lenses: product/domain/state,
user/journey, data/authority, external/security/safety, runtime/operations, and
quality/economy. Preserve explicit questions when applicable:

- identity, relationships/cardinality, ownership and business rules;
- for repeatable/persistent/asynchronous workflows: state scope/owner/lifetime,
  snapshot/freeze point, terminal behavior, reset versus persist, next-cycle
  re-entry and stale-state isolation;
- source of truth and consistency/migration/recovery where material;
- external-effect identity, ambiguity, authorization, idempotency and retry
  safety;
- concurrency/resource ownership, fencing and recovery when multiple/replaced
  actors can mutate shared state; and
- acceptance oracle/fixture, duplicate authoritative paths and cheaper safe path.

Tiny reversible tools should collapse to little ceremony. Deeper analysis is
required only when consequence, irreversibility, complexity or uncertainty makes
being wrong expensive.

For repeatable workflows, acceptance must cover a representative completed cycle
and the next-cycle transition when state leakage is a material risk: the new
cycle starts with the intended active context while historical completed output
remains bound to its correct snapshot/state.

Accepted material direction that could change a later session's approach belongs
in `docs/decisions/`. Preserve Owner work. Git/source owns implementation reality;
identified runtime owns observed behavior; tests/CI are verification evidence;
predefined Goal acceptance is the completion oracle. `TASK.md` is
current context, not runtime authority.