# Project operating map

On first contact, in a new Tech Lead/Worker session, or when context may be
stale, cold-start from this repository before planning or implementation. If
the CADS skill library is available, follow its Project Cold-Start playbook
and canonical Convergent AI Development Standard. Do not copy that Standard into
this project unless project-specific differences require durable documentation.
Otherwise:

1. Read `TASK.md`, `ARCHITECTURE.md`, `README.md` and relevant durable docs.
2. Inspect Git status, canonical branch/HEAD, recent history, relevant diffs and
   source.
3. Treat tests/CI as verification evidence and identified runtime as observed
   behavior; neither overrides the predefined Goal acceptance oracle.
4. State the active Goal, Critical User Journey, acceptance, constraints,
   completed work, blockers, active workline, remaining work and next safe
   action. Ask only for missing owner intent that current reality cannot recover.

When the CADS skill library is available, route ordinary work by current event:

- first contact / stale context -> Project Cold-Start;
- new or materially changed Goal / missing acceptance -> Product Goal Framing;
- implementation under an established Goal -> Goal Execution;
- bug / regression / failing test / unexpected runtime behavior -> Systematic Debugging;
- new/materially changed user journey, navigation, or discoverability problem -> User-Facing Workflow;
- new/materially changed screen/component/interaction/responsive layout -> Frontend Design;
- before user-facing Product Acceptance, or when usability/accessibility/recovery quality is in doubt -> UI Quality Review;
- before a material completion claim -> Product Acceptance; and
- workspace bloat / competing worklines / Goal closure residue -> Workspace Hygiene.

For user-facing work, frame the Product Goal first, resolve workflow/information
architecture before visual implementation, debug concrete defects scientifically,
and review the real rendered UI before Product Acceptance. Use the CADS Thin
Guard only for explicitly consequential boundaries. Procedure routing does not
grant authority and must not be turned into lifecycle state, phase tracking,
adoption, continuation, or a task database.

Preserve owner work. Keep normal development native to the project. Maintain
bounded divergence: normally one active workline, no unrelated valuable dirty
stack, and Goal-created experiments/residue that can converge at closure.

`TASK.md` holds active context. `ARCHITECTURE.md` holds durable architecture.
Git/source owns implementation reality; identified runtime owns observed
behavior; agent reports and chat memory do not.
