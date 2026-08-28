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

## Targeted independent-R3 blocker repair

Focused commands:

```text
python -m unittest tests.test_effect_safety -v
python -m unittest tests.test_candidate_package -v
python -m unittest tests.test_thin_guard -v
python -m unittest tests.test_simplified_cli tests.test_end_to_end tests.test_guarded_local -v
```

Results: 20 effect-safety, 5 candidate-package, 10 Git/scope and 19 affected
integration tests passed; 0 failed and 0 skipped. These cover untrusted retry
assertions, exact trusted binding, exact `PREPARED` reuse, extracted-candidate
testing and staged Git-mode type changes.

One replacement stabilization command was then run:

```text
python scripts/self_test.py
```

Result: 54 source-checkout tests discovered and passed; 0 failed and 0 skipped.
Portable extracted-candidate verification is a separate final-package gate.

The completion audit then made exact-intent mismatch reporting explicitly
unsafe, so trusted proof for one idempotency key cannot appear to bless a
different submitted intent. The affected 20-test Effect Safety suite was rerun
and passed with 0 failures and 0 skips; no second full suite was required.
