# Mandatory scenario evidence map

The active tests map the frozen end-to-end scenarios to executable evidence:

1. Native bugfix/ordinary commit: `test_normal_bugfix_uses_native_commit_without_lifecycle_ceremony`.
2. Expected expansion warns: `test_warn_only_expected_deviation_preserves_warn_and_executes` and Thin Guard WARN test.
3. Strict/prohibited violations block: Phase 1A and guarded-local scope tests.
4. Fix reality/rerun passes: `test_fixing_scope_reality_then_rerunning_passes_without_resume`.
5. Clean descendant unauthorized delta blocks: `test_clean_descendant_outside_strict_scope_blocks`.
6. Worker replacement: repo-local cold-start test plus `AGENTS.md`/Git/source.
7. Tech Lead replacement: the same test verifies `TASK.md` goal/acceptance/constraints and `ARCHITECTURE.md`.
8. Build OS/worktree replacement: `test_effect_ambiguity_survives_replacement_worktree_without_migration`.
9. Policy change: `test_scope_policy_is_reread_on_every_invocation_without_migration`.
10. High-cost drift: committed and dirty `BLOCK_STALE_STATE` tests.
11. Known external success: `test_known_success_records_intent_before_exactly_one_dispatch`.
12. Ambiguity survives reload: `test_dispatch_exception_preserves_ambiguity_across_reload`.
13. Blind retry is rejected, including changed `effect_id` or idempotency key: the dedicated blind-retry regressions.
14. Retry is only considered safe after positive no-effect or exact provider idempotency tests.

Candidate identity/readback/secret checks are covered by
`tests/test_candidate_package.py` and repeated on the one final archive.
