# DR-0004: Adopt trusted-evidence and canonical-integration boundaries

Status: Accepted direction; implementation subject to evaluation
Date: 2026-09-12
Scope: Architecture / Integration

## Context

CADS was intentionally simplified around five reasoning controls and normal
native Git/test/CI development. A subsequent autonomy review asked how to use
stronger coding agents to reduce Owner intervention without reintroducing a
workflow runtime. The internal review proposed evidence-centric autonomous
execution. An independent red-team review returned `MODIFY_DIRECTION`: keep the
thin direction, but strengthen evidence provenance, avoid treating a single
coding Worker as a permanent architecture invariant, and prevent MAR from
reimplementing capabilities that model/vendor harnesses increasingly provide.

The Standard already requires predefined acceptance, verification independence,
identity-bound evidence and one canonical Product HEAD. This decision therefore
does not amend the frozen Standard or add another CADS control.

## Decision

Adopt the following architecture direction, referred to in research as
**B-prime — Trusted Evidence Kernel + Runtime Authority + Vendor-Native
Intelligence**:

1. CADS owns engineering semantics: Goal/CUJ/acceptance, source-of-truth and
   authority semantics, risk/evidence requirements, invariants and portable
   engineering skills.
2. Model/harnesses own intelligence and ordinary orchestration: planning,
   exploration, coding, normal context management, subagents, browser/computer
   use and normal self-repair.
3. Project runtime/tests/CI own product-specific executable oracles and observed
   behavior.
4. MAR or an equivalent integration authority owns only portable guarantees that
   must survive vendor changes and are not otherwise adequately guaranteed:
   candidate/evidence identity binding, canonical integration authority,
   consequential mutation/effect authority, required fencing/isolation,
   crash-safe integration and useful cross-provider audit/telemetry.
5. Technical completion must converge toward **trusted evidence**: evidence tied
   to the exact candidate/environment and a relevant independently valid oracle.
   A Worker report is a claim, not final technical authority.
6. Multiple isolated agents may explore or produce candidate changes when
   decomposition/conflict risk justifies it. Exactly one authority advances the
   canonical product state. One active workline remains the economical default
   for small work.
7. Expanded autonomy is earned by representative evaluations of a
   model+harness+tooling profile, not by vendor/model name or an online success
   streak. Production telemetry informs later evals; it does not silently grant
   authority or self-modify CADS policy.
8. Owner owns product intent, material trade-offs, subjective product judgement
   where human experience is the oracle, and non-delegable consequential
   authority. Objective acceptance execution may be autonomous when the
   predefined oracle fully determines the criterion.

## Why

This boundary is intended to preserve the parts of CADS that remain valuable as
models improve while avoiding competition with rapidly improving vendor
harnesses. It strengthens the weakest current area—objective completion proof—
without restoring a task database, phase machine, role hierarchy or generic
agent orchestration layer.

"Single canonical integration authority" is chosen instead of "single writer"
because isolated parallel candidates can improve throughput while canonical
mutation still needs one authority. "Trusted evidence" is chosen instead of
plain evidence because high autonomy increases the risk of self-serving oracles,
metric gaming and evidence that is detached from the exact candidate/runtime.

## Consequences

- The five-control CADS model remains unchanged.
- The Convergent AI Development Standard remains frozen; this Decision Record
  does not change its invariants.
- Product Acceptance should align with the Standard by requiring Owner real-use
  only when Owner experience/judgement is actually part of the oracle.
- Evidence Envelope / Oracle Integrity is an implementation candidate to be
  evaluated before becoming a universal mechanism. It must remain evidence and
  provenance, not task lifecycle state.
- MAR must be audited capability-by-capability. Vendor-native mechanisms should
  be reused when they provide adequate guarantees/auditability; MAR should not
  become a universal agent platform.
- Fresh review and parallel candidate writing remain conditional capabilities,
  not permanent roles or mandatory stages.
- Project/domain invariants remain necessary because isolated Git workspaces
  prevent file races but not incompatible semantic assumptions.

## Revisit When

Revisit this direction if representative real-Goal evaluation shows that:

- trusted-evidence machinery adds significant ceremony/latency without reducing
  false-DONE, escaped defects or Owner QA/re-explanation load;
- vendor-native integration/effect/isolation guarantees make a MAR guarantee a
  duplicate proxy;
- isolated parallel candidates consistently cost more in semantic reconciliation
  than they save in wall-clock time;
- objective machine acceptance repeatedly misses meaningful Owner product
  failures for a Goal class; or
- Owner active attention per verified accepted outcome does not decrease after a
  representative deployment period.

Do not reopen this decision merely because a new model, vendor feature or agent
framework appears. Re-evaluate the affected responsibility only when its
concrete guarantee or measured economics change.
