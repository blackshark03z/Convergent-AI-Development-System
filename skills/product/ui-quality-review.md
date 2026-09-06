# UI Quality Review

An advisory review gate for the real rendered interface before user-facing
Product Acceptance, or when the Owner reports that the UI is hard to find,
understand, operate, recover, or trust.

It does not create a separate review lifecycle. It prioritizes the few findings
that materially affect the current Product Goal and defers cosmetic debt that
does not block or meaningfully degrade the journey.

## When to use

Use:

- before a material user-facing product-ready/completion claim;
- after implementing or materially changing a user-facing workflow;
- when users cannot find a capability, know what to do next, understand system
  status, or recover from failure; or
- when responsive/accessibility/interaction quality is in doubt.

Review the actual rendered product and real journey, not screenshots or source
alone when live verification is available.

## Review dimensions

### 1. Task completion

Can the intended user enter the flow, identify the next action, complete the
Critical User Journey, recognize success, and obtain the expected output?

### 2. Information architecture and discoverability

Is navigation organized around user intent? Are important capabilities reachable
where the user expects them? Is the primary action obvious without memorizing
implementation structure?

### 3. Interaction, status, and recovery

Does the interface expose meaningful loading/in-progress, empty, success,
partial, error, blocked, retry, undo/cancel, and recovery states when relevant?
Does the user retain orientation and valuable work after failure?

### 4. Usability heuristics

Check the high-impact equivalents of established usability heuristics:

- visible system status;
- match with user vocabulary and the real-world task;
- user control and escape/recovery;
- consistency and familiar conventions;
- error prevention;
- recognition rather than recall;
- efficient paths for frequent work;
- focused/minimal presentation;
- useful error messages and recovery; and
- help/instructions only where the product cannot remain self-explanatory.

### 5. Accessibility and responsive quality

For relevant surfaces verify semantic/native interaction, keyboard operation,
visible focus, accessible labels/names, understandable errors/status, contrast,
non-color-only meaning, target size, reflow/zoom expectations, and supported
viewport/input modes. For complex widgets, follow established WAI-ARIA Authoring
Practices rather than inventing keyboard behavior.

## Finding discipline

Return only the highest-impact findings, normally 3–6. Each finding must state:

- observable fact;
- user consequence;
- severity: `BLOCKER`, `HIGH`, or `DEFERRED_POLISH`; and
- smallest actionable repair.

`BLOCKER` prevents the current journey or hides/corrupts a critical action/state.
`HIGH` materially harms comprehension, recovery, accessibility, or repeated use
but may not fully block completion. `DEFERRED_POLISH` is non-blocking refinement
and must not spawn an open-ended redesign chain.

Do not create issues merely because another visual direction could also look
good. Do not turn a local UX defect into a product-wide design system unless
repeated evidence shows a shared rule is actually needed.

## Exit

When blockers/high findings relevant to acceptance are resolved, rerun the same
real Critical User Journey and pass current evidence to
`../core/product-acceptance.md`. The Owner remains final authority for real-use
acceptance.
