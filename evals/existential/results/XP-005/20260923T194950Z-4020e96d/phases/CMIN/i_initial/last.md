Implemented exact-effect reconciliation for phone and OTP submissions.

- [eligibility_phone.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CMIN/multiple_automation/eligibility_phone.py) now closes an uncertain effect only when reconciliation evidence matches its effect ID, target identity, and submission ID. Effect lookup also requires an exact target match.
- [raw_cdp.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-005/20260923T194950Z-4020e96d/arms/CMIN/multiple_automation/adapters/raw_cdp.py) passes the expected effect identity into reconciliation. Its current page-state observations remain unattributed, so uncertain effects stay `RECONCILE_REQUIRED`.
- Added fixture coverage for lost response across restart, generic accepted-but-unattributed evidence, and exact matching evidence. Updated runtime adapter calls in the tests.

**Checks:** `python -m unittest tests.test_eligibility_phone tests.test_runtime_adapters` passed (11 tests). `git diff --check` passed.

**Observed behavior:** An uncertain phone submission is not repeated after restart. A generic accepted screen state does not resolve it; fixture evidence tied to the exact submission does.

**Limitations:** The current browser adapter cannot produce exact-submission evidence, so it will require reconciliation for uncertain phone or OTP outcomes. The brief’s broader changed-intent and competing-new-task cases are not implemented for a separate client retry identity; this change covers the existing phone verification operation/effect flow. No live or external effects were used.