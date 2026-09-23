Updated [ui/app.js](/D:/CADS-Benchmark/XP-003-AUTO-V2/arms/N0/ui/app.js) to:

- Keep the readiness step blocked while a Casting Plan in the selected chapter range awaits approval, show that status, and provide a button to open the approval action.
- Keep readiness blocked after a batch save’s readback check finds a voice mismatch, and show the failed result in the voice section. A successful batch save clears this blocker.
- Preserve the existing readiness decision for missing voices. Saving or approving still does not start rendering.

**Checks run:** `node --check ui/app.js`, `git diff --check`, and `pytest -q tests/test_assignment_workflow_browser.py` all passed; the browser test reported `1 passed`.

The browser fixture does not cover the pending-approval or readback-mismatch cases, so those behaviors were not verified in a browser. This candidate is not Product Acceptance.