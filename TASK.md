# Goal

Rename the product-facing identity from Build OS to **Convergent AI Development
System (CADS)** without changing architecture, runtime semantics, authority, or
compatibility contracts.

# Acceptance

- Active product-facing docs, CLI descriptions, scripts, skills and project templates use `Convergent AI Development System (CADS)` or `CADS` consistently.
- Existing compatibility identifiers remain unchanged where they are technical contracts: Python package `buildos`, `.buildos/**`, `buildos/effects`, schema IDs, CLI/script filenames and historical legacy evidence.
- The canonical Convergent AI Development Standard remains the development standard inside CADS rather than being renamed into a second concept.
- Historical simplification/legacy evidence is not mechanically rewritten merely for branding.
- The full active source-checkout suite passes from the exact rename revision; portable verification remains an extracted-candidate-only gate and is not falsely claimed from a source checkout.
- One clean local task commit is produced; no push, merge or deployment.

# Non-goals

No architecture redesign, lifecycle reintroduction, package/module rename,
protocol/schema migration, state-path migration, GitHub repository rename,
remote push, merge or deployment.

# Constraints

- Rename baseline: `7a6053db2b98ce09601a0a4f57e91d7295e8ed3a` (`origin/master`).
- Work occurs in isolated worktree `D:\Buil OS\_worktrees\cads-rename` on branch `task-cads-rename`.
- Compatibility-first: branding may change; technical identity changes require separate justification and migration work.

# Material Decisions

- This is a product-facing rename only; architecture and runtime behavior remain unchanged.
- Technical compatibility identifiers such as `buildos`, `.buildos/**`, schema IDs and effect-state paths remain stable.
- Historical evidence retains the old name where it describes earlier phases rather than current product identity.
- The simplified thin-guard lineage remains rooted in baseline `8970dc8`; this rename does not reopen that architecture decision.

# Progress / Discoveries / Next

- Confirmed the configured Build OS project root contains the real Git repository as a nested checkout; avoided committing against the parent non-repository state.
- Confirmed current canonical remote baseline at `origin/master` and created an isolated rename worktree from it.
- Audited active branding references and separated product-facing names from compatibility/protocol identifiers.
- Full active source-checkout suite passes 66/66. The portable runner correctly rejects the source checkout with `EXTRACTED_CANDIDATE_REQUIRED`; no candidate package is created for this branding-only task.
- Final diff/scope review is clean: 13 active files changed, `git diff --check` passes, CLI help identifies `CADS`, and compatibility identifiers remain unchanged by design.
- This task closes when the reviewed rename is captured in one local commit.

Next: after closure, await Owner decision for any repository-slug rename, promotion, push or merge.
