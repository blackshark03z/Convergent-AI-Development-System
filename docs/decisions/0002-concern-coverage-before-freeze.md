# DR-0002: Add bounded concern coverage before material design freeze

Status: Superseded by DR-0003
Date: 2026-09-08
Scope: Process

## Context

Two different product efforts exposed the same meta-failure in event-routed
development. Story Audio could have individually working capabilities while the
composed user journey remained confusing. In Multiple Automation, a material
domain/cardinality question such as one Google account owning one versus many
channels could be missed unless someone happened to ask it before architecture
was frozen.

CADS already assigned Knowledge-Gap Responsibility to the AI Tech Lead, but the
router mainly activated procedures for concern classes that had already been
recognized. That left a discovery blind spot: knowing how to handle a concern is
not the same as reliably checking whether an important concern exists.

A focused research review compared this failure with requirements engineering,
business analysis/domain modeling, scenario-based architecture evaluation,
software quality models, secure-development frameworks, and systems-engineering
tailoring. The recurring pattern was broad reference coverage plus scenario/risk
review, tailored to consequence and context, rather than running every specialist
process on every project. Relevant reference families included ISO/IEC/IEEE
29148, ISO/IEC 25010/25019, IIBA business-analysis guidance, SEI ATAM/QAW, NIST
SSDF, NASA systems-engineering tailoring, and DDD domain analysis.

## Decision

Add one universal advisory core playbook, `Concern Coverage Review`, and route it
before materially treating a new or changed architecture, domain model,
source-of-truth, ownership boundary, or authority boundary as stable, and when
new evidence invalidates a material design assumption.

Embed a conditional Domain Semantics check in Product Goal Framing for Goals
where actors, domain objects, identity, relationships/cardinality, ownership,
business rules, entity state, or exceptions can materially change design.

The review scans a bounded concern surface across product/domain, user/workflow,
data/state, architecture/integration, security/privacy/effects,
runtime/operations, delivery/environment, quality/evidence, and
economy/maintainability. It reports material gaps and attacks important
assumptions. It does not claim exhaustive completeness.

## Why

The repeated failure is at the meta-routing layer, so merely adding a Business
Analysis skill would close one known concern while preserving the same blind
spot for security, migration, recovery, concurrency, operability, or another
unrecognized concern. One broad discovery review can detect and route those gaps
without turning every concern into a mandatory phase.

The approach also preserves CADS proportionality: small/reversible projects can
resolve or mark most concerns obviously inapplicable with little effort, while
high-consequence or coupled systems receive deeper scenario/evidence work.

## Consequences

CADS now has seven universal core playbooks. Concern-review findings such as
resolved, not-applicable, or material-gap are ephemeral reasoning results, not
persisted lifecycle state. Only material accepted decisions continue to use
Decision Records.

No standalone Business Analysis phase, security phase, compliance engine,
quality database, traceability database, or specialist skill family is created.
Domain semantics constrain architecture but do not prescribe database schemas,
classes, services, or deployment topology.

A clear review means no material gap was found under current Goal/evidence; it is
not proof that all unknown unknowns were eliminated. Material changes to scope,
risk, external contracts, or key assumptions trigger proportionate re-review of
the affected decision.

## Revisit When

Revisit if the same material concern class is repeatedly missed despite this
review, or if the review creates measurable ceremony across small projects
without reducing design rework. Split out a specialist playbook only when
repeated evidence shows the bounded review plus existing procedures cannot
handle that concern efficiently.