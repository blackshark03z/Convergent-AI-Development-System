# XP-005 Frozen Owner Goal

Case: XP-005
Source failure classes: AE-004 + AE-015 — ambiguous external effect and
reconciliation before retry
Product: Multiple Automation
Base revision: `7683e2617f2aacb962c905bfe1eb67a749252f6d`
Historical reference: `36c954f`

## Owner Goal

When a phone/client submission may have partially succeeded or transport state
is uncertain, do not blindly submit again.

Keep ownership of the original task/effect attributable to the initiating phone
or client, reconcile the existing submission first, and distinguish a retry of
the same intended task from an intentional new/competing task.

The system must fail closed when it cannot establish enough evidence to decide
whether redispatch would duplicate a consequential effect.

## Fixed constraints

- Live consequential submission is forbidden in this benchmark.
- Use local/provider fixtures only.
- Transport loss must not silently change task ownership.
- Duplicate submissions must respect idempotency/retry semantics.
- Partial side effects are reconciled before any redispatch decision.
- Do not infer success from newest/first/last result, timing, or other guessed
  attribution.
- The historical reference implementation is hidden from the candidate.

This Goal text is identical across N0, N1, C-min and C-current.
