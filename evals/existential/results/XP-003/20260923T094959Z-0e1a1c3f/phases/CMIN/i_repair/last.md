Implemented the repair in [ui/app.js](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-003/20260923T094959Z-0e1a1c3f/arms/CMIN/ui/app.js).

- The approval result is tied to the approved chapter, scope, and draft. It is hidden when a different or stale draft is displayed.
- **Cấu hình giọng** now forces a fresh registry load for the current scope, including when an earlier registry request is still in flight.
- The handoff does not issue PREPARE or start a render.

**Checks passed:** `node --check ui/app.js`, `git diff --check`, the speaker review UI and workspace UI checks (27 tests), the production scope browser check, and the speaker review workspace browser checks (2 tests).

**Limit:** The available offline browser fixtures do not cover the exact chapter draft approval → **Cấu hình giọng** click path. So I could not confirm in a browser that narrator and speaking role controls are configurable after approval. No paid provider or production runtime was used. This is a candidate for R review, not product acceptance.