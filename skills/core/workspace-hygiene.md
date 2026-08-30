# Workspace Hygiene

An audit-first advisory procedure for local project-folder bloat. It is
separate from Project Cold-Start and must not run destructive cleanup during
cold-start.

## Procedure

1. Identify the canonical repository/source and explicit excluded paths before
   enumerating or changing anything.
2. Inspect likely bloat such as stale worktrees, candidate extraction folders,
   package staging, temporary output, caches, `node_modules`, `.venv`, media or
   render output, and old Build OS artifacts.
3. Verify ownership, current use, Git/worktree registration, release relevance,
   and recovery value.
4. Classify each exact path:
   - `KEEP`: canonical, active, approved, or required evidence.
   - `SAFE_TO_DELETE`: deterministically disposable and independently verified.
   - `REVIEW_REQUIRED`: unknown ownership, intent, value, or recoverability.
5. Clean only exact `SAFE_TO_DELETE` paths and only with explicit authorization.
   Recheck the resolved target immediately before deletion and report what was
   removed and whether recovery is possible.

Never automatically delete canonical repositories or source, unknown user
data, media/output without explicit intent, approved release artifacts, or
unresolved external-effect evidence. Merged or abandoned worktrees, candidate
verification extracts, package staging and known caches are only cleanup
candidates after verification.

Do not build a cleanup daemon, storage manager, or persisted hygiene state.
