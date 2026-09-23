# XP-005 Held-out Oracle

The local oracle drives the pinned product's verification action through a fake
CDP transport and drives the real phone orchestration and SQLite product store
through local provider and vault fixtures. It calls no live browser, provider,
paid service, or production runtime.

It checks that generic SMS wording on the first verification step is not
accepted as a completed submission, while a distinct positive second-step
readback can reconcile the same effect. It injects transport loss both before
and during a simulated click, checks the resulting fail-closed state,
and verifies that uncertainty remains attached to the original workspace,
operation, effect, and lease after a process restart. It also checks that an
independent workspace may own a separate task, a competing task cannot replace
an unresolved one, and a later intentional task receives a distinct identity.
The newer independent task is created before the original task is retried, so
recency cannot stand in for ownership. The oracle checks that evaluation leaves
candidate files unchanged.

Base and historical reference run under this same oracle. Its local fixture
does not prove behavior against the live verification site, paid provider, or
other external systems; those effects are forbidden in this benchmark.
