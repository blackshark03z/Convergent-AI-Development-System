---
name: git-validation-v122
description: Inspect a clean Git product commit, ancestry, changed paths, and validation evidence before Build OS closeout. Use after a product-like commit or when HEAD advances legitimately; do not use it to override kernel ancestry, risk, authorization, or evidence invariants.
---

# Git validation workflow

1. Confirm generated `.buildos/` control state is locally excluded from product commits.
2. Inspect `git status --short`, the staged/committed diff, and the exact product commit SHA.
3. Run `scripts/ai.py record-commit` after the normal Git commit.
4. Run affected validation against the current descendant HEAD and inspect its output.
5. Run `scripts/ai.py validate` with the exact checks and inspection identity.
6. Run `scripts/ai.py close`; a later descendant with product changes requires fresh validation, while a tree-equivalent descendant is refreshed normally.

Never delete prior evidence or use a prose `reopen` workaround. This Skill is guidance only; the kernel remains authoritative.
