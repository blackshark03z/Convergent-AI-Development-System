# Active test classification

The active suite keeps or ports tests for live architecture and security:

- Git/base/dirty truth and exact path scope;
- RC1 clean-descendant and prohibited-path regressions;
- deletion, type-change and tracked control-state protection;
- high-cost TOCTOU and native exit behavior;
- external intent-before-dispatch, ambiguity, reconciliation and no-blind-retry;
- read-only inspection, fresh policy reads and cold-start continuity;
- simplified package identity, readback and secret checks.

Tests whose sole purpose was to assert v1.25 task lifecycle, generations,
adoption, continuation, context epochs, telemetry, Work Contracts, grounding,
assurance or generic execution-plan behavior are retired under
`legacy/v125/tests`. They are not weakened or translated into requirements for
the simplified kernel.

The stabilization gate discovers only `tests/test_*.py`. Historical tests are
preserved for reference but are not an active compatibility promise.
