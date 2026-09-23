# XP-002 Held-out Oracle

The oracle evaluates the frozen Owner Goal by observable proposal behavior, not historical patch equality.

It deliberately does **not** require a class named `StockProposalPlanner`, a method named `build_plan`, or the historical test/file layout. It discovers proposal/plan-oriented public capability under the existing `videopipeline.stages.stage2_assets` product boundary, injects local fake stock dependencies when signatures permit, and normalizes equivalent proposal containers.

The held-out checks require:
- only the STOCK_ONLINE shot receives a proposal;
- proposal identity/timing remains bound to the shot;
- stock search is driven by the shot-specific semantic intent;
- alternatives are bounded to at most three;
- an eligible strong candidate is exposed for preview/review without silently becoming a final production approval;
- forbidden stock is excluded;
- F5 no-match remains review/owner/no-match rather than silently falling back to generated media or dispatching Flow;
- candidate worktree is not mutated;
- no external network is needed.

The oracle is intentionally broader than the historical implementation shape while remaining narrow to the frozen XP-002 product outcome.
