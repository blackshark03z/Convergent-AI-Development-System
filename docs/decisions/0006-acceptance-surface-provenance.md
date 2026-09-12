# DR-0006: Require acceptance-surface provenance for product evidence

Status: Accepted
Date: 2026-09-13
Scope: Acceptance / Evidence

## Context

CADS already requires identified runtime evidence, candidate-bound evidence and real supported-surface CUJ verification. A remaining operational gap allowed an AI to finish source/build verification while an Owner-visible surface still served stale or ambiguous material, leaving the Owner to discover that engineering/runtime convergence problem.

Independent review confirmed the failure class but rejected framing it as a new deployment/promotion lifecycle. Different products expose acceptance through different shapes: direct source/CLI execution, desktop packages, client assets/cache, previews, serverless revisions, rolling replicas, multi-service routes or production surfaces. A fixed `source -> binary -> process -> surface` schema would therefore be both incomplete and over-prescriptive.

## Decision

Adopt an **Acceptance Surface Provenance Invariant** inside the existing Acceptance control:

> When Product or Owner Acceptance relies on an observed product surface, that evidence is valid only when the material runtime, artifact/assets, configuration and data authorities affecting the claimed behavior are traceably associated with the intended candidate. If that association is stale, materially ambiguous, conflicting, or cannot be established, the evidence is `UNVERIFIED` and must not support Product/Owner Acceptance.

Additional interpretation:

- provenance is a traceable relationship across only material components, not literal identity/hash equality or a mandatory topology;
- ambiguity blocks only when it can materially change the claimed behavior;
- isolated preview evidence may prove its candidate before canonical integration, but does not automatically prove a materially different later integrated state;
- evidence must still match the surface/state relevant to the eventual claim or Owner review; material drift after observation requires equivalence or renewed evidence;
- client assets/cache, configuration, data authority, route/replica composition and similar factors belong to provenance only when they can materially affect the observed behavior;
- self-reported version metadata cannot be the sole proof when it may diverge from the served material.

Operationalize this rule through Product Acceptance, conditional project architecture guidance, and AE-003. Keep the frozen Standard unchanged because this strengthens semantics already present there.

## Consequences

- The AI Tech Lead, rather than the Owner, is responsible for catching stale/ambiguous acceptance surfaces before subjective review.
- `UNVERIFIED` remains the fail-closed vocabulary; no new persisted readiness state is introduced.
- CADS gains no deployment lifecycle, promotion phase, process manager, universal deploy CLI, mandatory restart/cloud/container behavior, or canonical-HEAD-before-preview requirement.
- Projects document provenance mechanisms only when needed to reconstruct material acceptance evidence.
- Preview, local, desktop, SPA, distributed and production surfaces can use different evidence shapes under one invariant.

## Revisit

Revisit if representative project evidence shows the invariant creates recurring ceremony without preventing false-DONE/Owner rework, or if a repeated surface-provenance failure cannot be expressed without adding a genuinely new evidence primitive.
