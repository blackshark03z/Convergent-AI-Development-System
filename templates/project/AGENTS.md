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
4. State the active Goal, acceptance, constraints, completed work, blockers,
   active workline, remaining work and next safe action. Ask for missing owner
   intent.

Preserve owner work. Keep normal development native to the project. Maintain
bounded divergence: normally one active workline, no unrelated valuable dirty
stack, and Goal-created experiments/residue that can converge at closure. If
CADS is available, use it only at explicitly consequential boundaries; do
not add or infer lifecycle, adoption, or continuation concepts.

`TASK.md` holds active context. `ARCHITECTURE.md` holds durable architecture.
Git/source owns implementation reality; agent reports and chat memory do not.
