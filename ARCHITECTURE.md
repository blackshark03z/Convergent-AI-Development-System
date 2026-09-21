# Convergent AI Development System (CADS) architecture

## Ownership

The Owner owns desired product outcome, material product trade-offs,
consequential authorization, and subjective real-use acceptance where human
experience is the oracle. The AI Tech Lead owns adaptive engineering judgment:
discovering material engineering concerns, resolving ordinary engineering
choices within established intent/authority, and framing proportionate
acceptance/oracles/evidence. Identified Git/source owns implementation reality.
Identified runtime evidence owns observed behavior for the
source/configuration/environment exercised.
Native tests and CI provide verification evidence; predefined Goal acceptance
determines completion. Workers own bounded repository reasoning, implementation
and normal reversible local decisions. CADS only guards explicit consequential
boundaries.

Normal development follows the canonical Convergent AI Development Standard in
`docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`; that standard is advisory operating
discipline, not kernel state. Normal development is not a CADS lifecycle.
An ordinary commit is neither a permission transition nor an adoption event.

CADS is organized conceptually around five controls rather than one procedure per
engineering discipline: **Reality, Intent / Design, Change, Acceptance, and
Consequence**. Product / Design Framing combines Goal/CUJ/acceptance framing with
a proportionate search for material design drivers and unsafe assumptions.
Systematic Debugging, Workspace Hygiene, User-Facing Workflow, Frontend Design
and UI Quality Review are conditional methods pulled when current reality needs
them; they are not universal phases. This keeps specialist knowledge on demand
while preserving explicit questions learned from real failures. No control or
method creates design authority or persisted process state.

## Capability-adaptive autonomy

CADS preserves **durable semantic invariants -> adaptive assurance -> removable capability scaffolding**. Intent, authority, acceptance and consequence boundaries remain stable while assurance depth adapts to current evidence, task risk and demonstrated agent/tool capability. Compensating mechanisms introduced for a temporary capability gap must remain removable rather than becoming permanent architecture.

Autonomy is a **reversible evidence-calibrated autonomy envelope**, not a one-way ratchet. As reliable capability improves, unnecessary scaffolding and routine Owner burden should shrink. If capability, environment or evidence quality regresses, assurance may contract autonomy until sufficient evidence returns. This principle defines semantics, not persisted process state, and does not prescribe one harness, protocol, model family or execution topology.

### Adaptive delivery boundaries

DR-0011 composes the existing Five Controls into five lightweight delivery boundaries: **Intent Boundary, Risk Envelope, Execution Authority, Versioned Acceptance, and Canonical Promotion**. These are not new lifecycle stages or a sixth control. The Intent boundary should collapse to pass-through for clear reversible work; assurance expands only when uncertainty, consequence, recoverability, observability or blast radius makes late correction materially expensive.

Local CUJ success does not by itself prove global system health. When a change materially alters state ownership/source-of-truth, dependency direction, persistent schema, external-effect semantics, concurrency/fencing, or another cross-cutting invariant, canonical promotion includes the affected system-fitness evidence. Parallel execution may create many candidates, but one authority serializes canonical product truth. The canonical obligation is one identifiable product lineage, not preservation of the first implementation architecture.

Transport availability does not redefine execution authority. If the current cognition client cannot expose the selected execution authority directly, an alternate bounded transport may be used only when it reaches the same durable authority and preserves the same Goal/task/evidence semantics. Missing direct tool exposure never implies that durable work is absent, completed work should be resubmitted, or direct repository mutation may substitute for the required integration authority. If equivalence cannot be established, fail closed at the transport boundary. See DR-0009.

## Advisory procedure routing

Root `AGENTS.md` maps current work onto the five controls. Cold-start reconstructs
Reality. Product / Design Framing establishes Intent and acceptance while
surfacing only material design drivers before expensive-to-reverse decisions.
Goal Execution advances Change in small coherent batches. Product Acceptance
proves the real outcome. Thin Guard applies only at Consequence boundaries.
Debugging, hygiene and product/UI methods are conditional helpers that return to
the same Goal. Routing is evaluated from current reality and is not persisted;
there is no workflow engine, phase database or new authority layer.

The target project's root `AGENTS.md` is the minimum CADS activation contract
for coding agents. It carries enough authority, knowledge-gap, journey
composition, and routing semantics to prevent silent fallback to an unrelated
process. When the CADS skill library is reachable, the Worker opens the routed
playbook for progressive detail. When it is not reachable, the Worker follows
the minimum `AGENTS.md` contract and must not claim that an unavailable playbook
was executed. Missing skill access never transfers engineering expertise to the
Owner. CADS does not add a skill-copy service, sync lifecycle, or second runtime
for activation.

Project templates expose the minimum context these procedures need. `TASK.md`
may carry a Critical User Journey and representative acceptance fixture;
`ARCHITECTURE.md` may carry explicit code/data/config/runtime/effect authority
boundaries when relevant. Empty/inapplicable sections do not create obligations
for every project.

## Decision continuity

Material accepted rationale/direction that must survive chat or agent turnover is
stored as lightweight docs-as-code under `docs/decisions/`, following
`docs/DECISION_CONTINUITY.md`. Bootstrap creates only the active decision index;
detailed records exist only when the materiality test is met. Accepted records
are superseded rather than silently rewritten. Decision Records complement, but
do not replace, current `TASK.md`, `ARCHITECTURE.md`, Git/source, tests or runtime
evidence. No decision database, context service, vector store or extra process
control is introduced.

## Thin Guard

Every check derives a disposable `PASS`, `WARN` or `BLOCK` from current Git
state and explicit scope input. It observes the canonical base, HEAD/tree,
ancestry, committed delta, dirty tracked/untracked paths, deletions, type
changes, index identity and worktree content identity.

`expected_paths` is advisory. `strict_paths` is the hard allowed area.
`prohibited_paths` is always forbidden. Tracked `.buildos/**` mutation is a
hard violation independent of caller scope.

There is no unblock, continue, adopt or resume operation. Reality or policy is
fixed and the check is rerun.

## Explicit execution boundaries

`high-cost` is a cooperative caller declaration. CADS does not infer danger
from command text. It compares exact observation digests immediately before one
shell-free native spawn. A microscopic malicious-process race after that point
requires OS sandboxing and is outside the cooperative-local threat model.

External effects use one narrow Python dispatch seam. Core semantics are
provider-free. Exact operation, target and request digest define semantic
effect identity. Optional idempotency assertions are bound to that identity but
cannot change, disguise or authorize it. Only proof returned through the
explicit trusted-verifier seam can affect retry eligibility. Durable state is written before
the dispatch boundary; `DISPATCH_UNCERTAIN` is durable before the provider call.

Retry is only considered safe after trusted positive no-effect proof or trusted
provider-idempotency proof bound to the same exact effect identity/request.
CADS does not automatically retry.

## State

The only default durable runtime state is external-effect safety state, stored
under the repository common Git directory at `buildos/effects`. Git can
reconstruct product state; it cannot reconstruct an ambiguous provider call.

No task database, `CURRENT`, generation chain, grant, lease, runtime anchor,
Grounding lifecycle, Assurance lifecycle, model router or context governor is
part of the simplified kernel.

## Legacy boundary

The default CLI never imports or advances the v1.25 lifecycle. Read-only inspect
may report unresolved legacy effect evidence because external reality can remain
ambiguous. Closed legacy lifecycle data is historical only. No project or task
migration exists.
