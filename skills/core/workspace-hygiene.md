# Workspace Hygiene

An advisory procedure for keeping AI-assisted development convergent without a
cleanup subsystem. Temporary divergence is allowed; valuable work and canonical
product state must not become ambiguous.

This skill operationalizes Workspace Convergence from the canonical
`docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`. It creates no lifecycle state.

## During normal development

1. Keep one active workline by default. Use the canonical working tree for
   small/reversible work or a temporary worktree when isolation has concrete
   value. Parallel worklines need a real reason.
2. Allow dirty state while investigating, but do not carry unrelated reasoning
   layers in one giant dirty stack. Before changing direction, handing off, or
   leaving work for long, commit, revert, or explicitly preserve unique value.
3. Make experiments disposable by construction. Failed probes should be
   reverted or remain only in known disposable scratch.
4. Keep bulk generated/runtime data such as media, browser profiles, caches,
   downloads, rendered output, and disposable E2E projects outside canonical
   source where practical. Small designated ignored scratch may remain inside a
   project.
5. Do not create a parallel canonical implementation merely to avoid resolving
   the current one.

## Goal closure

Closure is Goal-scoped, not a license to clean the whole repository.

1. Identify the canonical branch and Product HEAD that contain the accepted
   work.
2. Preserve all unique Goal-created source/config/docs/scripts/evidence that
   still has value.
3. Resolve competing implementations introduced or exposed by this Goal when
   they would leave canonicality ambiguous.
4. Classify Goal-created residue:
   - `KEEP`: canonical, active, approved, or required evidence.
   - `SAFE_TO_DELETE`: deterministically disposable and independently verified.
   - `REVIEW_REQUIRED`: unknown ownership, intent, value, or recoverability.
5. Remove only exact `SAFE_TO_DELETE` residue with the authorization required
   for that consequence. Re-resolve the target immediately before deletion.
6. Remove a completed temporary worktree or explicitly designate it as the next
   active workline. There must be no forgotten workline with trapped unique
   value.
7. Verify that no unpreserved unique Goal value remains outside the identified
   Product HEAD.

Do not automatically clean unrelated pre-existing technical debt, dormant code,
historical artifacts, stale docs, or runtime data unless they directly block
the Goal or threaten a must-preserve invariant. Unknown value is never deleted
as cleanup.

## Deep bloat audit

Run a broad size/worktree/cache audit only when the Goal produced bulk data,
disk pressure is observed, worktree/candidate proliferation is suspected, or
known heavy temporary artifacts need closure. A normal Goal should not pay this
cost routinely.

Inspect likely bloat such as stale worktrees, candidate extraction folders,
package staging, temporary output, caches, `node_modules`, `.venv`, media/render
output, and old Build OS artifacts. Verify ownership, current use,
Git/worktree registration, release relevance, and recovery value before any
deletion.

Never automatically delete canonical repositories/source, unknown user data,
media/output without explicit intent, approved release artifacts, or unresolved
external-effect evidence.

Do not build a cleanup daemon, storage manager, artifact registry, branch
governor, entropy score, or persisted hygiene state.
