Implemented the repair across five files.

- The product UI keeps a stable client ID and sends it with publish approval. Before any publish effect is prepared, the operation stores that client ID and a digest of the sealed package, channel, and visibility. Retries with a different client or task are rejected.
- Upload matches and thumbnail recovery require evidence for the exact package and target. Provider observations that cannot prove attribution remain unresolved and block redispatch.
- Added fixture coverage for competing clients and changed intent, alongside existing lost-response, restart, partial-effect, and unrelated-result cases.

Checks run: `38 passed` in the publish and runtime-adapter suites; `git diff --check` passed. No live submission was made.

Evidence is bound to base revision `191739c0efbf9f3086043fa9bcae71bbf1ee3f1f` plus candidate diff blob `38a10cf5c8b83e8431322e5da4d55e3f24324eb1`.

Known limit: the production Studio adapter cannot establish package identity from its title-based video observation, nor verify the thumbnail digest. Those outcomes stay unresolved; successful live reconciliation is not demonstrated. I do not claim Product Acceptance.