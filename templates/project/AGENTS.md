# Project operating map

This root `AGENTS.md` is the minimum CADS activation contract for this project.
On first contact, in a new Tech Lead/Worker session, or when context may be
stale, cold-start from this repository before planning or implementation. When
the CADS skill library is reachable in the execution environment, open the
playbook routed below for progressive detail. If it is not reachable, follow
this minimum contract and do not claim that an unavailable playbook was
executed. Do not copy the full CADS Standard into this project unless
project-specific differences require durable documentation.

Knowledge-gap responsibility is mandatory: the Owner is not expected to supply
missing engineering expertise. The AI Tech Lead investigates material
engineering concerns from Goal/repository/runtime evidence, resolves ordinary
engineering choices within established intent and authority, and asks the Owner
only for missing product facts, material trade-offs, or consequential choices
that change Owner-controlled outcomes and cannot reasonably be recovered or
inferred. Translate technical choices into observable consequences; do not ask
the Owner to certify technical facts.

Cold-start fallback:

1. Read `TASK.md`, `ARCHITECTURE.md`, `docs/decisions/README.md`, `README.md`
   and only relevant durable docs/Decision Records.
2. Inspect Git status, canonical branch/HEAD, recent history, relevant diffs and
   source.
3. Treat tests/CI as verification evidence and identified runtime as observed
   behavior; neither overrides the predefined Goal acceptance oracle.
4. Treat accepted Decision Records as durable rationale/settled material
   direction; chat memory and agent reports are not durable decision authority.
5. State the active Goal, Critical User Journey, acceptance, constraints,
   completed work, blockers, active workline, remaining work and next safe
   action. Ask only for unresolved Owner-controlled input that current reality
   cannot recover or reasonably infer.

Route ordinary work by current event:

- first contact / stale context -> Project Cold-Start;
- new or materially changed Goal / missing acceptance -> Product Goal Framing;
- before materially freezing a new/changed architecture, domain model, source-of-truth, ownership, or authority boundary, or when new evidence invalidates a material design assumption -> Concern Coverage Review;
- implementation under an established Goal -> Goal Execution;
- bug / regression / failing test / unexpected runtime behavior -> Systematic Debugging;
- multi-step user-facing Goal where multiple capabilities compose into one outcome, or a new/materially changed journey/navigation/discoverability problem -> User-Facing Workflow at the whole-journey/composition level;
- new/materially changed screen/component/interaction/responsive layout -> Frontend Design;
- before user-facing Product Acceptance, or when usability/accessibility/recovery quality is in doubt -> UI Quality Review;
- accepted material direction that could change a later session's approach -> persist/update a Decision Record under `docs/decisions/`;
- before a material completion claim -> Product Acceptance; and
- workspace bloat / competing worklines / Goal closure residue -> Workspace Hygiene.

Before materially freezing architecture/domain/authority, perform a proportional
concern-coverage review across product/domain (including actors, objects,
relationships/cardinality and business rules), user/workflow, data/state,
architecture/integration, security/privacy/consequential effects,
runtime/operations, delivery/environment, quality/evidence, and
economy/maintainability. An applicable unresolved concern that could materially
change behavior, domain semantics, architecture, authority/source-of-truth,
failure safety, acceptance, or cost/risk is a material gap: do not freeze the
affected decision. A clear review is not proof that every unknown unknown was
found, and the review must not become persisted lifecycle state. Before
concluding, ask what must be true for the design to work, what breaks if that
assumption is false, and how the product could still fail despite happy-path and
isolated tests passing.

For a multi-step user-facing Goal, isolated feature/subsystem PASS results do
not establish Journey/Product PASS. Define and exercise a representative full
Critical User Journey when composition matters. Missing required journey
evidence means the journey remains unverified. Product-provided onboarding,
help, and domain instructions are legitimate; the intended user must not depend
on undocumented external guidance or implementation knowledge they are not
expected to have.

For user-facing work, frame the Product Goal first, resolve the whole
workflow/information architecture before visual implementation, debug concrete
defects scientifically, and review the real rendered UI before Product
Acceptance. Apply User-Facing Workflow at the Goal/journey composition level,
not after every tiny UI edit. Use the CADS Thin Guard only for explicitly
consequential boundaries. Procedure routing does not grant authority and must
not be turned into lifecycle state, phase tracking, adoption, continuation, or
a task database.

Preserve owner work. Keep normal development native to the project. Maintain
bounded divergence: normally one active workline, no unrelated valuable dirty
stack, and Goal-created experiments/residue that can converge at closure.

`TASK.md` holds active context. `ARCHITECTURE.md` holds durable architecture.
The Owner owns product outcome/trade-offs/consequential authorization and
subjective real-use acceptance where applicable. The AI Tech Lead owns missing
engineering concern discovery and ordinary engineering judgment within that
intent. Git/source owns implementation reality; identified runtime owns observed
behavior; tests/CI provide verification evidence; agent reports and chat memory
do not.
