# Goal

Produce one stabilized simplified Build OS candidate ready for independent R3.

# Acceptance

- Thin Guard preserves scope, dirty-worktree, deletion/type-change, control-path and RC1 regressions.
- High-cost local execution blocks stale state and otherwise invokes native argv once.
- External intent precedes dispatch; known, ambiguous and reconciled outcomes survive reload.
- Blind retry is rejected; exact idempotency or positive no-effect proof is required.
- Repository-local evidence is sufficient for Worker and Tech Lead replacement.
- The simplified CLI is the default; legacy lifecycle machinery is disconnected/demoted.
- Focused, integration and one full active-suite stabilization gate pass.
- Exactly one package candidate passes identity, checksum, readback and secret checks.

# Non-goals

No task lifecycle, adoption, continuation, executor migration, grants, command
classifier, provider plugin framework, generic retry scheduler, self-R3,
promotion, push, merge or deployment.

# Constraints

- Stable ancestor: `ec01a97cce41f3628d00e14f01b76462dd616fe2`.
- Simplification baseline: `8970dc87a1bad6d649b4bb46272144c2e92b8118`.
- Frozen v1.26 checkout `13490a05fd2bc3d001b289b0e8d186973707ecb2` is read-only experimental evidence.
- Durable runtime state is allowed only for external-effect ambiguity.

# Material Decisions

- Semantic effect identity binds operation, target and request digest—not a task, worker or changeable idempotency key.
- Effect records live in the common Git administration directory, outside product history and across worktrees.
- External dispatch is an explicit Python integration seam; the CLI only inspects/reconciles effect truth.
- Legacy unresolved effects remain read-only detectable; closed legacy lifecycle data is historical.

# Progress / Discoveries / Next

- Phase 1A Thin Guard committed at `59398a7`.
- Phase 1B high-cost boundary committed at `8970dc8`.
- Provider-free Effect Safety, durable ambiguity, explicit dispatch API, thin CLI and fresh-policy reads are implemented and focused tests pass.
- Legacy lifecycle source/tests/assets are disconnected under `legacy/v125`; unresolved legacy effects have read-only detection and explicit effect-only reconciliation.
- All fourteen mandatory scenarios are mapped to active executable evidence in `docs/SCENARIO_EVIDENCE.md`.
- Focused thin-guard/high-cost security: 33 passed. Post-fix effect safety: 14 passed. Affected package/end-to-end: 7 passed. Final full active stabilization: 46 passed, 0 failed, 0 skipped.
- Next: if no verified receipt exists for the current clean HEAD, build/read back exactly one candidate; after a matching receipt exists, the next safe action is independent R3.
