# XP-005 Neutral Projection

Pinned Multiple Automation base: `7683e2617f2aacb962c905bfe1eb67a749252f6d`.

The runner archives that commit, not the current product working tree. It
removes eight historical worker and CADS process-control documents from
`docs/handoff/`. Product implementation, tests, architecture, decisions,
acceptance and recovery documentation remain available. No historical
reference bytes or held-out oracle files enter candidate workspaces.

Qualified neutral tree: `c6ac5eaa5a2909951b3302e04d25304eca070671`.
Qualification projection commit: `955ea309e756d4674ad4dcfbcdd1f8520dc6dc0e`.

The neutral tree is the Git tree produced by archiving the pinned base,
removing the listed files, and committing the remaining snapshot. The commit
identity records this disposable qualification projection only; the runner
checks the tree identity.
