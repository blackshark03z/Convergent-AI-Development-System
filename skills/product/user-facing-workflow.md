# User-Facing Workflow

An advisory procedure for shaping a user-facing flow around the user's real job
instead of backend modules, implementation history, or isolated capabilities.
It creates no persisted UX state, design phase, or workflow authority.

Use after Product Goal Framing when a Goal materially changes a user journey,
navigation, discoverability, or task flow. If the Goal/acceptance itself is
unclear, return to `../core/product-goal-framing.md` first.

## When to use

Use when:

- a new user-facing flow or materially changed screen changes how a user
  completes the Goal;
- navigation or information architecture is being designed or repaired;
- a capability exists but users cannot find, understand, or reach it; or
- the current UI mirrors subsystems more than operator intent.

Do not use for a purely visual restyle that preserves an already-proven flow.

## Build the flow from user intent

Establish, in this order:

1. **User / operator** — who is performing the task?
2. **Job / intent** — what are they trying to finish in real-world terms?
3. **Entry point** — where would they naturally begin?
4. **Primary action** — what is the next action that advances the Goal?
5. **Required information** — what must be visible or editable at that moment?
6. **System feedback** — how does the user know what is happening?
7. **Failure / recovery** — what can fail and how does the user recover without
   losing orientation or valuable work?
8. **Success / next action** — how does the user know the step or journey is
   complete and what should happen next?

Prefer one coherent task path over exposing every backend capability as a
peer-level destination. Contextual actions may be better than permanent global
navigation when they only make sense inside a book, project, job, scene, order,
or other active object.

## Required journey states

For every material step, consider only the states that can really occur:

- ready / initial;
- loading or in-progress;
- empty / no-result;
- success or partial success;
- error;
- blocked by permission, prerequisite, stale/offline state, or external
  dependency; and
- retry, repair, cancel, undo, or other recovery when relevant.

Do not invent states merely to fill a checklist. Do not hide a real state just
because backend code already handles it.

## Information architecture rules

- Organize primary surfaces by user intent and frequency, not implementation
  ownership.
- Keep the primary action visually and structurally obvious.
- Prefer recognition over recall: show current object, stage, status, and next
  action where the decision is made.
- Use user vocabulary; implementation/provider terminology belongs in
  diagnostics or secondary detail unless the user genuinely works in those
  terms.
- Progressive disclosure is preferred over exposing advanced controls before
  they are needed.
- A capability that is unreachable or undiscoverable in the real journey is not
  a complete product capability.

## Result contract

Return a compact flow description containing:

- user/job;
- entry point;
- shortest coherent Critical User Journey;
- primary action for each material step;
- required feedback and recovery paths;
- navigation or contextual-placement decisions; and
- any current UI element that should be reused, moved, combined, hidden,
  deferred, or removed.

Then resume the same Product Goal. Use `frontend-design.md` when implementing or
materially restyling the resulting interface. A journey design is not Product
Acceptance evidence until the real rendered flow is exercised.
