# Systematic Debugging

An advisory, evidence-driven procedure for removing a current Goal blocker
without turning one defect into an unbounded investigation chain. It creates no
incident lifecycle or persisted debug state.

Use the canonical development semantics in
`docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`.

## When to use

Use for a reproducible or user-observed bug, regression, failing test, unexpected
runtime behavior, provider anomaly, or other defect that may block the current
Goal.

## Debugging loop

1. **Reproduce or bound the symptom.** Record expected behavior, actual behavior
   and the smallest known path that exposes the defect. If exact reproduction is
   impossible, state the missing observation rather than guessing.
2. **Identify the exercised reality.** When relevant, bind the observation to
   source/HEAD, runtime, configuration, data root/input and provider version or
   request identity. An unidentified runtime is weak evidence.
3. **Localize the failing layer.** Narrow the search across UI, API, business
   logic, provider/adapter, persistence/state, filesystem, runtime/configuration,
   or another project-specific boundary before broad code archaeology.
4. **Form a falsifiable hypothesis.** State what evidence would prove the
   hypothesis wrong as well as what would support it.
5. **Run the cheapest discriminating check.** Prefer targeted observations over
   broad audits.
6. **Apply the smallest coherent root-cause fix** supported by evidence. Do not
   redesign adjacent subsystems merely because they could be cleaner.
7. **Add or run focused regression evidence** that would have caught the defect
   when practical.
8. **Resume the original CUJ / acceptance fixture immediately.** The purpose of
   debugging is to restore Goal progress.

## Drift stop

Once the original blocker is removed, stop the debugging branch of work.
Investigate a newly discovered anomaly now only if at least one is true:

- it blocks the current CUJ/acceptance;
- it threatens a must-preserve safety/data/security invariant; or
- the current fix cannot be correct without resolving it.

Otherwise record it as `DEFERRED_DEBT` and return to the Goal.

Do not automatically generalize one startup issue, provider quirk, schema
mismatch or UI defect into a new policy/authority/framework subsystem. Generalize
only when repeated evidence or material consequence makes the broader rule part
of the cheapest safe fix.

Historical branches and deep archaeology are not the default search path when
current source already contains enough capability to diagnose and complete the
Goal.

## Result contract

Return one concise result:

- `BLOCKER_REMOVED`: focused evidence shows the original symptom/root cause is
  addressed; resume the original Goal; or
- `BLOCKED_WITH_EVIDENCE`: a concrete missing authority, external dependency,
  unreproducible condition or unresolved hypothesis prevents a safe fix.

Do not report `FIXED` solely because a unit test, isolated fixture or internal
subsystem passes when the user-visible blocker still has a real journey to
resume.
