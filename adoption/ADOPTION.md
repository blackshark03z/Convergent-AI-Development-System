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

For a clean repository with supported terminal v1.16-style authority, run
`skills/project-lifecycle-bootstrap/scripts/legacy_authority_bridge.py inspect`,
then the explicit `prepare` and `retire` commands before this initializer.
Commit the generated `.buildos-legacy` transition archive/receipt and
fail-closed instruction replacement first. A BLOCKED Goal needs the exact
`--terminalize-blocked-goal --terminal-disposition-authorization <file>`
disposition plus the trusted launcher SHA-256 binding documented in the bridge
contract. A reference string is never authorization, and no flag can override
a live task/lease/node, dirty Git state, or malformed proof.
After normal v1.25 bootstrap, run bridge `finalize` to bind the first selected
generation. See `docs/LEGACY_TERMINALITY_AND_ADOPTION.md`.
