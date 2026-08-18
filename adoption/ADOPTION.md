# Portable adoption with continuity

Run `initialize.ps1 -Root <clean-git-worktree> -AcceptedRef <integration-ref>`.
It writes a namespaced `documentation_handoff` policy. Complete its canonical
authority mapping for the target project. A minimally documented project is
adoptable, but a `YES` impact must establish an authority before the product
commit; it may not silently omit documentation.
Commit `.buildos-policy.json` before the first Build OS bootstrap, because the
frozen kernel correctly rejects a dirty baseline.

The mandatory operational Skill uses `git rev-parse --git-common-dir` and puts
its active projection under `buildos-continuity/` there. This keeps it outside
the product tree and makes separate worktrees observable. Legacy `.ai` active
state projections are explicitly non-authoritative. Field Study is separate,
external, append-only evidence and never takeover, dirty-work or task state.

Use the wrapper for normal adoption. It performs `docs-check` before
`record-commit`; bootstrap injects the same deterministic command into Build OS
acceptance for validation. The wrapper does not replace the required pre-record
impact review. It cannot prove semantic accuracy of prose—record a Tech
Lead/Worker inspection declaration in the checkpoint.

Do not retire a closed task merely because Build OS reports CLOSED. `retire`
reports `CLOSED_PENDING_BASELINE_ADVANCE` until the resolved accepted ref
contains the candidate, then archives bounded terminal proof and removes only
the active sidecar.
