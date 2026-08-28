# Documentation impact gate

This is an operational gate before the ordinary product commit and Build OS
`record-commit`; it is not a kernel or security boundary.  Classify each change
as one or more of `USER_BEHAVIOR`, `ARCHITECTURE_OWNERSHIP_BOUNDARY`,
`API_CONFIG_SCHEMA`, `DEVELOPER_WORKFLOW`, `FEATURE_PRESET_INVENTORY`, or
`IMPLEMENTATION_ONLY`.  The first five mean `YES`; implementation-only means
`NO` with a bounded rationale. `UNKNOWN` blocks the wrapper's record-commit and
fails the deterministic validation re-check.

For `YES`, each selected category has exactly one policy-declared canonical
authority. Update it in the candidate tree before committing; record a bounded
semantic inspection declaration. The deterministic checker proves mappings,
paths and hashes only. A Worker or Tech Lead remains responsible for judging
whether prose describes implemented behavior rather than plans.
