# Simplified Build OS architecture

## Ownership

The Owner/Tech Lead owns desired outcome and business intent. Identified
Git/source owns implementation reality. Identified runtime evidence owns
observed behavior for the source/configuration/environment exercised. Native
tests and CI provide verification evidence; predefined Goal acceptance
determines completion. Workers own repository reasoning, implementation and
normal reversible local decisions. Build OS only guards explicit consequential
boundaries.

Normal development follows the canonical Convergent AI Development Standard in
`docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md`; that standard is advisory operating
discipline, not kernel state. Normal development is not a Build OS lifecycle.
An ordinary commit is neither a permission transition nor an adoption event.

## Thin Guard

Every check derives a disposable `PASS`, `WARN` or `BLOCK` from current Git
state and explicit scope input. It observes the canonical base, HEAD/tree,
ancestry, committed delta, dirty tracked/untracked paths, deletions, type
changes, index identity and worktree content identity.

`expected_paths` is advisory. `strict_paths` is the hard allowed area.
`prohibited_paths` is always forbidden. Tracked `.buildos/**` mutation is a
hard violation independent of caller scope.

There is no unblock, continue, adopt or resume operation. Reality or policy is
fixed and the check is rerun.

## Explicit execution boundaries

`high-cost` is a cooperative caller declaration. Build OS does not infer danger
from command text. It compares exact observation digests immediately before one
shell-free native spawn. A microscopic malicious-process race after that point
requires OS sandboxing and is outside the cooperative-local threat model.

External effects use one narrow Python dispatch seam. Core semantics are
provider-free. Exact operation, target and request digest define semantic
effect identity. Optional idempotency assertions are bound to that identity but
cannot change, disguise or authorize it. Only proof returned through the
explicit trusted-verifier seam can affect retry eligibility. Durable state is written before
the dispatch boundary; `DISPATCH_UNCERTAIN` is durable before the provider call.

Retry is only considered safe after trusted positive no-effect proof or trusted
provider-idempotency proof bound to the same exact effect identity/request.
Build OS does not automatically retry.

## State

The only default durable runtime state is external-effect safety state, stored
under the repository common Git directory at `buildos/effects`. Git can
reconstruct product state; it cannot reconstruct an ambiguous provider call.

No task database, `CURRENT`, generation chain, grant, lease, runtime anchor,
Grounding lifecycle, Assurance lifecycle, model router or context governor is
part of the simplified kernel.

## Legacy boundary

The default CLI never imports or advances the v1.25 lifecycle. Read-only inspect
may report unresolved legacy effect evidence because external reality can remain
ambiguous. Closed legacy lifecycle data is historical only. No project or task
migration exists.
