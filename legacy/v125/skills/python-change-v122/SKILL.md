---
name: python-change-v122
description: Apply focused Python source changes with affected tests, negative-path coverage, and diff inspection. Use for bounded Python implementation or repair tasks after Build OS bootstrap; do not use it to set risk, authorization, lifecycle state, or closeout policy.
---

# Python change workflow

1. Read the nearest project instructions and the generated WORK_PACKET.
2. Identify the smallest production seam that owns the behavior.
3. Add or update a failing focused test before or with the implementation.
4. Implement one coherent change; avoid unrelated cleanup and new dependencies.
5. Run the focused test, then the affected integration test when a boundary changed.
6. Inspect the final diff and a representative real output when the result is visual, media, or generated.
7. Pass the exact deterministic commands to `scripts/ai.py validate`.

Treat this file as guidance only. Kernel risk, authorization, Git ancestry, evidence, and lifecycle checks always take precedence.
