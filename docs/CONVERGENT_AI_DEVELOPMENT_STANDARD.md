# Convergent AI Development Standard v1.0

This is the canonical development standard used by Convergent AI Development
System (CADS). It is a reasoning and operating standard, not a lifecycle engine,
state machine, policy runtime, project profile system, or a second orchestration
system.

The invariants are universal. The depth of implementation and verification is
proportional to consequence, irreversibility, complexity, expected lifetime,
external dependency, and number of users. For personal/internal tools: senior
principles, proportional rigor, minimal ceremony.

## 1. Product Convergence

Maintain one active, bounded, end-to-end Product Goal: the smallest coherent
product outcome worth validating. Define observable acceptance before
implementation. Acceptance may be clarified, but it must not be weakened after
the fact merely to make implementation pass. A material owner requirement
change supersedes the old Goal/acceptance explicitly.

One Goal is not one giant diff. Work inside the Goal stays small-batch and
coherent.

**Knowledge-Gap Responsibility:** the Owner is not responsible for supplying
missing engineering expertise. The AI Tech Lead must investigate material
engineering concerns from the Goal, repository, runtime evidence, and supported
operating context; resolve ordinary engineering choices within established
intent and authority; and ask the Owner only for missing product facts,
trade-offs, or consequential choices that materially affect owner-controlled
outcomes and cannot reasonably be recovered or inferred. Translate technical
choices into observable product consequences. If material technical uncertainty
remains, obtain proportionate evidence or restrict the affected action; do not
turn uncertainty into unsupported assurance or ask the Owner to certify a
technical fact.

For a multi-step user-facing Product Goal, define at least one representative
Critical User Journey at the composition level. Isolated feature or subsystem
verification does not establish Product Goal acceptance. When feasible, exercise
the journey end-to-end on the supported product surface: the intended user must
be able to identify relevant next actions, retain necessary context, recover
from applicable failures, and reach the useful result without undocumented
external guidance or implementation knowledge they are not expected to have.
Product-provided onboarding, help text, and domain instructions are allowed.

## 2. Authority Convergence

Authority is domain-specific:

- Owner/Tech Lead owns desired product outcome and business intent.
- Identified Git/source owns implementation reality.
- Identified runtime evidence owns observed behavior for the source,
  configuration, and environment actually exercised.
- Tests/CI provide verification evidence.
- Durable repository docs carry still-valid architecture and context.
- `TASK.md` carries current work context, not runtime authority.
- Agent reports are claims. Chat memory is hints.

Evidence without identity is weak evidence. Tests passing alone do not imply the
Product Goal is done.

## 3. Execution Reproducibility

A fresh Worker must be able to install, run, and verify the relevant product
path without guessing material environment assumptions. This requires a
reconstructable development environment, not mandatory containers or hermetic
build infrastructure.

## 4. Verification Independence

Final acceptance criteria must be independent of the implementation produced to
satisfy them. The implementation author may execute verification, but may not
manufacture or weaken the acceptance oracle after coding.

Independent verification does not require a second model or human reviewer for
every change. Independence is in the oracle.

## 5. Change Economy

Make the minimum sufficient system change. Prefer:

`REUSE -> WIRE -> FIX -> REPLACE_AND_DELETE -> ADD`

A new abstraction, dependency, durable state, authority, or parallel path needs
concrete Goal or invariant justification. Do not under-engineer solely to keep a
diff small, but abstract volatility rather than possibility.

## 6. Workspace Convergence

Temporary divergence is allowed during development. Maintain one active
workline by default; it may be the canonical working tree or a temporary
worktree when isolation has concrete value.

Dirty work is allowed while investigating, but unique valuable work must not
accumulate across unrelated changes of direction. Before changing direction,
handing off, or leaving work for long, commit, revert, or explicitly preserve
it.

Experiments and probes should be disposable by construction. Bulk generated
media, caches, browser profiles, runtime projects, and similar heavy artifacts
should normally live outside canonical source. Small designated ignored scratch
may live inside a project.

At Goal closure, converge all unique Goal-created value into one identified
canonical Product HEAD, resolve competing implementations introduced or exposed
by the Goal, and remove only proven Goal-created disposable residue. A completed
worktree is removed or explicitly designated as the next active workline.
Unknown value is never deleted as cleanup. Goal closure is not permission to
refactor unrelated pre-existing debt.

Runtime acceptance counts only when tied to identified source/configuration and
the relevant environment.

## 7. Consequence Boundary

Ordinary reversible development stays native to Git, editors, tests, CI, and
normal project tools.

External effects, destructive or hard-to-recover owner-data changes,
privileged/security-sensitive effects, and explicitly high-cost actions cross an
explicit consequence decision when applicable. CADS guards only boundaries it
can actually guarantee; it is not a semantic command classifier or general
sandbox.

## Goal Definition of Done

A Goal is done only when:

1. The predefined product/consumer outcome is achieved.
2. The normal end-to-end product path provides applicable acceptance evidence;
   for a multi-step user-facing Goal, this includes representative end-to-end
   CUJ evidence and is not inferred from isolated feature/subsystem PASS results.
3. Relevant independent regression evidence passes.
4. Known applicable must-preserve invariants remain intact.
5. One identified canonical Product HEAD contains the completed work.
6. No competing canonical implementation introduced or exposed by the Goal
   remains unresolved.
7. Goal-created disposable workspace residue has converged, with no unpreserved
   unique value.
8. No known blocker preventing the defined acceptance journey remains.

Tests passing alone do not imply DONE. Missing required journey evidence means
the journey remains unverified, not implicitly accepted from the sum of feature
PASS results. Manual runtime success alone does not imply DONE when
source/configuration/environment identity is unknown.

## Direct Blockers and Rabbit Holes

A direct blocker is a condition causally preventing the defined acceptance
journey from succeeding.

Use this decision rule:

```text
Does it causally block the current Goal?
  YES -> FIX
  NO  -> Does it threaten a must-preserve invariant?
           YES -> FIX
           NO  -> DEFER
```

`DEFER` does not require a new phase, subgoal, or management system. Record it
only when it is worth retaining.

## Personal/Internal Tool Default

Prove the smallest useful real-user journey as early as practical, normally
before generalized recovery, extensibility, or architecture hardening.
Resilience complexity must be justified by demonstrated failures, known
high-cost consequences, or unavoidable external contracts.

A useful heuristic, not an invariant: when critical external dependencies are
already understood, target a narrow usable slice within roughly 1-3 working
days. Missing that target is a signal to review scope and process before adding
architecture, not a mandate to lower acceptance quality.

## Freeze Rule

Freeze this Standard after integration. Change it only when either condition is
met:

- **Class A — Serious failure:** the Standard permits data loss, a security
  incident, a wrong consequential effect, canonical source corruption, or an
  unrecoverable product state.
- **Class B — Repeated systemic failure:** the same failure class occurs in at
  least two different projects and no existing rule handles it.

Do not change the Standard merely because a new model, article, tool, process,
or optimization idea appears. Project-specific bugs do not justify changing the
universal Standard.
