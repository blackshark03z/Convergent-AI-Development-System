# Frontend Design

An advisory implementation procedure for building a deliberate, usable,
accessible user interface after the user-facing workflow is sufficiently clear.
It is not a design-system runtime, theme generator, or aesthetic approval state.

If navigation, discoverability, or the task flow is still the real problem, use
`user-facing-workflow.md` first. Reuse the project's existing components,
tokens, patterns, and visual language unless the Goal specifically requires a
change.

## When to use

Use for:

- a new page, screen, component, or interaction;
- a material restyle or responsive redesign;
- implementing a user-facing workflow; or
- repairing visual hierarchy or interaction affordance that blocks or confuses
  the Goal.

## Before implementation

Inspect the real interface and existing source before inventing new UI.
Establish:

- the user task and primary action;
- existing reusable components and tokens;
- content density and hierarchy;
- the product's current visual character; and
- one short visual thesis for the changed surface, such as compact operator
  console, calm document workspace, or media review surface.

The thesis guides hierarchy and composition; it is not permission for ornamental
redesign unrelated to the Goal.

## Implementation rules

1. **Hierarchy before decoration.** Make primary, secondary, destructive, status,
   and informational elements distinguishable without relying on novelty.
2. **Reuse before parallel UI.** Extend an existing component/pattern when it can
   remain authoritative; do not introduce a second design language casually.
3. **Complete interaction states.** For relevant controls and surfaces cover
   rest, hover, focus, active/selected, disabled, busy/loading, success, error,
   empty/no-result, and retry/recovery states when they can actually occur.
4. **Use real content pressure.** Check long labels, realistic data volume,
   empty data, errors, and representative output rather than only ideal fixture
   strings.
5. **Responsive by product need.** Verify the widths and input methods the real
   product supports; do not spend effort on irrelevant form factors.
6. **Accessibility is a hard quality gate.** Prefer semantic/native controls,
   keyboard operation, visible focus, accessible names/labels, understandable
   errors/status, sufficient contrast, non-color-only meaning, and reasonable
   target size/reflow. Use established ARIA widget patterns only when native
   semantics are insufficient.
7. **User language over implementation language.** Provider IDs, internal state
   names, database vocabulary, and architecture concepts should not leak into
   primary UI unless the user needs them.
8. **Motion must explain change.** Avoid animation that competes with task
   completion; respect reduced-motion expectations when motion is present.

## Visual quality without AI-template drift

Avoid defaulting to generic card grids, excessive gradients/glass effects,
indiscriminate pill shapes, decorative dashboards, or large empty hero areas
when they do not serve the task. Deliberate simplicity is preferable to visual
novelty.

A distinctive interface should emerge from typography, spacing, density,
hierarchy, composition, and content behavior that fit the product—not from
adding more effects.

## Verification

Do not call a user-facing implementation complete from source inspection alone.
Verify the actual rendered UI with representative content and the interaction
methods relevant to the product. Check the Critical User Journey, relevant
states, responsive widths, and keyboard/focus behavior.

If rendered verification exposes a functional defect, route the defect through
`../core/systematic-debugging.md` and resume the same journey after the smallest
coherent fix.
