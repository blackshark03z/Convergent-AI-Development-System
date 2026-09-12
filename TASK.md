# Goal

Make CADS fail closed when Product/Owner Acceptance relies on a stale, ambiguous or ungrounded observed product surface: add a lightweight Acceptance Surface Provenance invariant without changing the Five Controls, frozen Standard, or introducing deployment/promotion lifecycle machinery.

# Critical User Journey

AI Tech Lead completes a candidate -> when acceptance depends on an observed product surface, determines which runtime/artifact/assets/configuration/data authorities materially affect the claimed behavior -> establishes a traceable association from that surface to the intended candidate -> runs the representative CUJ on that grounded surface -> reports `PRODUCT_ACCEPTED` or `PRODUCT_READY_FOR_OWNER_ACCEPTANCE` only from admissible evidence. If the association is stale, materially ambiguous, conflicting or unknown, the surface evidence remains `UNVERIFIED` and the Owner is not asked to judge the wrong build.

# Acceptance

- `skills/core/product-acceptance.md` defines one conditional Acceptance Surface Provenance admissibility rule under the existing Acceptance control.
- The rule binds evidence to an intended candidate and only the material runtime/artifact/assets/configuration/data authorities that can affect the claimed behavior; it does not prescribe a fixed provenance topology.
- A preview/isolated candidate may provide valid evidence for that candidate, but evidence does not automatically transfer to a materially different integrated state.
- Material ambiguity such as mixed old/new request-reachable replicas, stale client assets/cache, or changed surface state between evidence and review keeps the affected evidence `UNVERIFIED`.
- Self-reported version strings alone are not sufficient provenance when they can diverge from the deployed material.
- Project architecture guidance may document provenance mechanisms conditionally when needed, but does not create a required deployment schema, activation phase, process manager or universal restart/deploy mechanism.
- Strengthen AE-003 so the autonomy eval covers stale runtime, stale frontend assets, mixed rollout, evidence-to-review drift, false/self-reported identity and preview-to-integrated-state transfer.
- Add one durable Decision Record for the cross-project acceptance semantic.
- Preserve `Reality -> Intent / Design -> Change -> Acceptance -> Consequence`, the frozen Standard and existing verdict vocabulary; missing provenance uses existing `UNVERIFIED` semantics rather than a new lifecycle state.
- Add focused tests and keep the full CADS regression suite passing without weakening existing tests.

# Acceptance Fixture / Evidence Basis

1. Pure library or non-persistent execution where no observed live surface is material: no extra runtime gate is invented.
2. Local server/Desktop/CLI: evidence is tied to the source/artifact actually executed, not inferred from Git alone.
3. SPA/client UI: stale static assets, service worker or cache capable of changing observed behavior keep UI evidence unverified until grounded.
4. Preview/worktree runtime: evidence may prove candidate C; it does not by itself prove later integrated state H if H materially differs.
5. Rolling/multi-replica runtime: one successful request does not prove the user-facing surface when request-reachable old/new replicas can differ.
6. Evidence taken at time T does not support Owner review after the material surface changed unless equivalence/provenance is re-established.
7. A `/version` or similar self-report is supporting evidence only when causally tied to the deployed material; a stale/hard-coded string cannot self-prove identity.
8. Subjective Owner judgement remains separate: grounded objective evidence may lead to `PRODUCT_READY_FOR_OWNER_ACCEPTANCE`, not fabricated Owner approval.

# Non-goals

No sixth CADS control, deployment/promotion lifecycle, `BUILDING -> PROMOTING -> ACTIVE -> ACCEPTED` state machine, deployment database, CADS process manager, universal deploy CLI, mandatory cloud/container/restart mechanism, canonical-HEAD-before-preview requirement, source/artifact/runtime hash equality, mandatory Owner UAT, MAR change or Standard amendment.

# Constraints

Preserve DR-0003 anti-accretion, DR-0004 trusted-evidence boundaries, DR-0005 lean architecture description, Decision Continuity and existing Product Acceptance authority semantics. Treat provenance as a traceable relationship over only material components, not as a universal fixed chain or mandatory schema.

# Material Decisions

- Adopt the independent-review refinement: frame the gap as evidence admissibility, not deployment/promotion.
- Name the rule **Acceptance Surface Provenance Invariant** because an acceptance surface may be a local process, desktop package, CLI execution, SPA/assets, preview, serverless revision, multi-service runtime or production route.
- Use existing `UNVERIFIED` semantics when material provenance cannot be established; do not create `NOT_READY_FOR_PRODUCT_REVIEW` as persisted/state-machine vocabulary.
- Candidate identity is the evidence anchor; canonical Product HEAD is not required before preview evidence, but evidence cannot silently transfer to a materially different integrated state.
- Ambiguity blocks only when it can materially change the acceptance claim.

# Progress / Discoveries / Next

- Independent review verdict: `ACCEPT_WITH_CHANGES`.
- Review confirmed a real operational enforcement gap while rejecting a deployment/promotion lifecycle framing.
- Minimum safe change selected: Product Acceptance admissibility rule + conditional architecture guidance + AE-003 strengthening + one Decision Record, with focused tests.
- Implemented the Acceptance Surface Provenance Invariant using existing `UNVERIFIED` semantics; no activation/deployment phase or fixed provenance topology was introduced.
- Strengthened AE-003 for stale runtime/assets, mixed request-reachable versions, evidence-to-review drift, false/self-reported identity and preview-to-integrated-state transfer.
- Focused provenance + architecture + autonomy-eval tests: 14/14 PASS; `git diff --check` PASS; frozen Standard diff is empty.
- Full CADS regression: 97/97 PASS with `SIMPLIFIED_ACTIVE_SUITE=PASS`.

Next: review the final bounded diff for anti-accretion, commit/push this Goal, then use production evidence from real CADS projects to evaluate whether any provenance mechanism needs future strengthening.
