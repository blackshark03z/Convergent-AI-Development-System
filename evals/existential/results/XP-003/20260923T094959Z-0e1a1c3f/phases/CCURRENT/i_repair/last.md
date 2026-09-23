**Candidate repair complete; Product Acceptance is not claimed.**

Changed the assignment journey in [ui/app.js](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-003/20260923T094959Z-0e1a1c3f/arms/CCURRENT/ui/app.js):

- Unassigned voices now keep configuration in the current state and block the production handoff. The page names each affected role and links to its voice selector.
- Clicking a blocker opens the voice section and focuses that role’s selector.
- A failed save reconciliation retains the selected voice draft and displays the failure, leaving the scope unresolved until corrected and saved.

**Checks run**

- `node --check ui/app.js` and `git diff --check`: passed.
- Local browser fixtures for speaker review and character assignment: 2 passed. The assignment fixture observed voice save and a path to production with no render commands.
- The broader UI contract run had one failure: an existing assertion expects the prior handoff label “Continue: check & prepare audio.” The current candidate already uses “Continue: open production”; I left that behavior intact. The remaining 27 tests in that run passed.

The local browser fixtures demonstrated the existing review and assignment path. They did not exercise an unassigned role or a forced reconciliation failure in a rendered session, so those two repaired states are not independently demonstrated by browser evidence here. No production runtime or external provider was used.