# Stabilization evidence

Focused security command:

```text
python -m unittest tests.test_thin_guard tests.test_guarded_local tests.test_effect_safety -v
```

Result: 33 passed, 0 failed, 0 skipped.

Affected integration/package command:

```text
python -m unittest tests.test_simplified_cli tests.test_end_to_end tests.test_candidate_package -v
```

Result: 12 passed, 0 failed, 0 skipped.

The first full active-suite stabilization run executed 45 tests: 44 passed and
one cold-start test failed because it incorrectly required a dirty worktree.
Product behavior was unaffected. Commit `8c9af7c` corrected the test to inspect
branch/status evidence in both clean and dirty states. The affected test passed.

Required green stabilization rerun:

```text
python scripts/self_test.py
```

Result: 45 passed, 0 failed, 0 skipped and
`SIMPLIFIED_ACTIVE_SUITE=PASS`.

The pre-candidate completion audit then found and repaired an effect-identity
gap: changing only an idempotency key could previously disguise the same
semantic request. Semantic identity now excludes the key, and a dedicated
no-blind-retry regression covers the case.

Post-fix proportional stabilization:

```text
python -m unittest tests.test_effect_safety -v
python -m unittest tests.test_candidate_package tests.test_end_to_end -v
python scripts/self_test.py
```

Results: 14 effect-safety tests passed; 7 package/end-to-end tests passed; the
final active suite discovered and passed 46 tests, with 0 failures and 0 skips.

No provider dispatch, self-R3, promotion, push, merge or deployment occurred.
