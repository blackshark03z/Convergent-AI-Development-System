# Convergent AI Development System (CADS)

CADS combines the Convergent AI Development Standard, project-entry/cold-start
protocols, and a thin guard for explicit consequential boundaries. Normal
development stays native to Git, editors, tests, CI and the Worker.

Normal work stays native:

```text
understand -> inspect -> edit -> focused test -> ordinary commit -> continue
```

No task lifecycle, grant, adoption or continuation operation is required for
ordinary development.

## Starting or handing off a project

Initialize a new or existing project directory with the canonical context files:

```powershell
python scripts/bootstrap_project.py --root D:\path\to\project
```

Inspect legibility without changing anything:

```powershell
python scripts/bootstrap_project.py --root D:\path\to\project --check
```

The command creates only missing files and preserves existing files exactly.
Afterward, a new Tech Lead or Worker follows the target repository's root
`AGENTS.md`. AI-assisted development follows the canonical
[`Convergent AI Development Standard v1.0`](docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md);
project files point to that standard rather than duplicating it. Durable
repository context should carry repository-grounded facts, so a long chat
handoff is unnecessary; genuinely missing owner intent still requires
clarification.

The root `AGENTS.md` is also the minimum CADS activation surface for a coding
agent. A bootstrapped project therefore retains the essential authority,
knowledge-gap, journey-composition, and routing contract even when the full CADS
skill library is not mounted in that execution environment. When the skill
library is reachable, the Worker opens the routed playbook for progressive
detail; when it is unavailable, the Worker follows the minimum `AGENTS.md`
contract and must not claim that an unavailable playbook was executed. CADS does
not copy or synchronize its skill library into every project.

CADS uses one small conceptual control loop: **Reality -> Intent / Design ->
Change -> Acceptance -> Consequence**. Project Cold-Start implements Reality;
Product / Design Framing (`product-goal-framing.md`) combines bounded Goal/CUJ/
acceptance framing with proportionate material-design-driver discovery; Goal
Execution implements Change; Product Acceptance implements Acceptance; and the
Thin Guard handles applicable consequential effects. Systematic Debugging and
Workspace Hygiene remain conditional methods, as do User-Facing Workflow,
Frontend Design and UI Quality Review. They are pulled only when current reality
requires them, not treated as universal phases. No control creates persisted task
state, grants, adoption, or a second orchestration runtime.

Material decisions that must survive chat/agent turnover use the lightweight
[Decision Continuity Protocol](docs/DECISION_CONTINUITY.md). Bootstrap creates a
small `docs/decisions/README.md` active index. Detailed Decision Records are
created only when losing an accepted decision could materially change a later
session's scope, approach, acceptance, architecture, authoritative path or
expensive research. Decision continuity is docs-as-code and cross-cutting, not another development
control, context database or lifecycle state.

## Portable and external skills

CADS-owned skills have one canonical semantic source under `skills/core/` and
`skills/product/`. Generate Agent Skills-compatible projections for a supported
harness without creating manually duplicated copies:

```powershell
python scripts/project_agent_skills.py --output-dir D:\path\to\generated-cads-skills
python scripts/project_agent_skills.py --output-dir D:\path\to\generated-cads-skills --check
```

Projection metadata lives in `skills/agent-skills.json`; generated `SKILL.md`
files remain build/output artifacts. Trigger descriptions are behavior-bearing
metadata and are therefore explicit and tested.

Ordinary targeted research remains the default response to a technical knowledge
gap. When a reusable external specialist Agent Skill is materially preferable,
follow `skills/core/external-skill-acquisition.md`. Current persistent support is
limited to vetted docs/reference-only skill content. If exact external skill bytes
are kept for reuse, record immutable source/content/license review provenance in
a project-local `external-skills.lock.json` conforming to
`skills/external-skills-lock.schema.json`. CADS does not auto-install/update
skills from stack detection and does not grant external skills authority.

## Public surface

Read current Git and external-effect truth without writes:

```powershell
python scripts/ai.py --root D:\path\to\repo inspect
```

Check a declared boundary against the live base-to-HEAD and dirty delta:

```powershell
python scripts/ai.py --root D:\path\to\repo check `
  --base <commit-or-ref> --boundary R3 `
  --expected app.py --strict app.py --prohibited "secrets/**"
```

`expected` deviations are `WARN`. `strict` or `prohibited` violations are
`BLOCK`. A clean pre-existing descendant commit receives no special authority.
Tracked `.buildos/**` changes always block.

Use a repo-local policy when the caller wants path intent in a file. It is read
fresh on every invocation and is never migrated or adopted:

```json
{
  "expected_paths": ["src/**"],
  "strict_paths": ["src/**", "tests/**", ".buildos-scope.json"],
  "prohibited_paths": ["secrets/**"]
}
```

```powershell
python scripts/ai.py --root D:\path\to\repo check `
  --base <commit> --boundary R3 --policy .buildos-scope.json
```

For one explicitly declared high-cost local action:

```powershell
python scripts/ai.py --root D:\path\to\repo high-cost `
  --base <commit> --strict "src/**" -- python focused_tool.py
```

CADS does not classify the command. It re-observes exact Git state at the
last practical point, uses native argv without a shell, and either returns
`BLOCK_STALE_STATE` or invokes the command once.

## External effects

External dispatch is available only through the narrow Python API
`buildos.external_effect.execute_external_effect(...)`, where an explicit
integration supplies one known dispatcher callable. There is no generic remote
command, provider plugin system or automatic retry.

Exact intent is durable before dispatch. The record becomes
`DISPATCH_UNCERTAIN` before the one provider call. A crash or ambiguous response
therefore cannot be mistaken for no dispatch.

Inspect durable effect truth or record a confirmed occurrence:

```powershell
python scripts/ai.py --root D:\path\to\repo effect list
python scripts/ai.py --root D:\path\to\repo effect inspect --effect-id <id>
python scripts/ai.py --root D:\path\to\repo effect retry-check --effect-id <id>
python scripts/ai.py --root D:\path\to\repo reconcile `
  --effect-id <id> --outcome CONFIRMED `
  --reference <provider-reference> --evidence "provider result metadata"
```

Free-form CLI evidence is never trusted retry proof. Positive no-effect or
provider-idempotency proof can be accepted only through the explicit Python
trusted-verifier seam, bound to the exact effect identity, operation, target,
request digest and idempotency key where applicable. With no trusted verifier,
the request fails closed.

For a confirmed unresolved v1.25 effect, use `--legacy-effect-id <id>` instead.
This copies only the exact unresolved effect ambiguity into the new Effect
Safety store; it does not migrate or reactivate the legacy task.

Ambiguous effects are never redispatched automatically. Retry is only reported
safe when exact trusted provider-idempotency or positive no-effect proof has
been persisted. Caller assertions remain non-authoritative metadata.

Effect records live under the repository's common Git administration directory
(`buildos/effects`), not product history. This is the only default durable
runtime state in the simplified architecture.

Compatibility note: the Python package name `buildos`, tracked guard namespace
`.buildos/**`, and `buildos/effects` state location remain stable internal
identifiers. The product-facing name is Convergent AI Development System (CADS).

## Repository map

- [AGENTS.md](AGENTS.md): short operating map for a fresh Worker.
- [ARCHITECTURE.md](ARCHITECTURE.md): durable ownership and safety invariants.
- [TASK.md](TASK.md): current goal and progress only.
- [docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md](docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md): canonical AI development invariants, DoD, rabbit-hole rule and freeze rule.
- [docs/EFFECT_SAFETY.md](docs/EFFECT_SAFETY.md): effect contract and recovery semantics.
- [skills/core/external-skill-acquisition.md](skills/core/external-skill-acquisition.md): conditional vetting/pinning boundary for reusable external specialist Agent Skills.
- [skills/agent-skills.json](skills/agent-skills.json): explicit routing metadata for deterministic Agent Skills projections of CADS-owned skills.
- [skills/external-skills-lock.schema.json](skills/external-skills-lock.schema.json): optional project-local provenance-lock schema for persisted docs-only external skills.
- [skills/product/user-facing-workflow.md](skills/product/user-facing-workflow.md): task-flow, navigation and discoverability procedure for user-facing Goals.
- [skills/product/frontend-design.md](skills/product/frontend-design.md): deliberate frontend implementation, states, accessibility and rendered verification.
- [skills/product/ui-quality-review.md](skills/product/ui-quality-review.md): high-impact usability/accessibility review before user-facing acceptance.
- [docs/LEGACY_V125.md](docs/LEGACY_V125.md): historical compatibility boundary.

From a Git source checkout, run the full active stabilization suite with:

```powershell
python scripts/self_test.py
```

That suite intentionally includes source-only Git and package-construction
tests. It fails clearly outside a Git checkout. From freshly extracted
candidate bytes, run the portable suite instead:

```powershell
python scripts/portable_self_test.py
```

The portable suite validates every packaged source byte against the embedded
manifest without requiring `.git` or attempting to build a package from a
package.

Historical v1.25 lifecycle sources remain repository evidence during the
transition, but they are disconnected from the default CLI and are not active
task authority. The v1.26 executor-lifecycle candidate was experimental and was
not adopted into this architecture.
