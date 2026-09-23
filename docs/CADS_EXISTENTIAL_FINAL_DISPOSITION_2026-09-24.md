# CADS Existential Final Disposition — 2026-09-24

Status: FINAL — INCONCLUSIVE
Protocol: DR-0014 / `docs/CADS_EXISTENTIAL_CHALLENGE.md`
Controlled P1 freeze: `docs/CADS_EXISTENTIAL_P1_RESULTS_2026-09-24.md`

## Decision scope

This document applies the predeclared exit rule after the controlled P1 batch and
the two required full-project confirmations. It does not reopen case selection,
change acceptance thresholds, add arms or use post-hoc reference knowledge.

The disputed question is whether the current CADS semantic/process residue is
demonstrably necessary relative to N1 or a smaller C-min residue under the frozen
R/I model pair and one-repair ceiling.

## Canonical confirmation evidence

- FC-LOW — XP-001 full-project confirmation:
  `evals/existential/results/XP-001/20260923T203651Z-bfe50ba6/result.json`
- FC-HIGH — XP-005 full-project confirmation:
  `evals/existential/results/XP-005/20260923T214417Z-eb8eef4a/result.json`

An additional XP-001 full-project run, `20260923T205918Z-1dde4893`, reproduced the
same outcome class but was not part of the predeclared confirmation set and is not
used to vote on the disposition.

## Confirmation outcome matrix

| Confirmation | N1 | C-min | C-current |
|---|---|---|---|
| FC-LOW / XP-001 | NOT_READY / oracle PASS / overconservative rejection | NOT_READY / oracle PASS / overconservative rejection | NOT_READY / oracle PASS / overconservative rejection |
| FC-HIGH / XP-005 | NOT_READY / oracle FAIL / correct rejection | NOT_READY / oracle FAIL / correct rejection | NOT_READY / oracle FAIL / correct rejection |

All compared arms used one repair. No arm produced false DONE.

## Relationship to controlled P1

Controlled P1 did materially differentiate the arms on XP-001: C-min was the only
READY/oracle-PASS correct acceptance, while N1 failed and C-current produced an
oracle-PASS candidate but rejected it. XP-002 through XP-005 did not demonstrate
an advantage for C-min or C-current: all arms correctly rejected oracle-FAIL
candidates.

The required full-project confirmation did not reproduce the XP-001 advantage.
On FC-LOW, all three compared arms produced oracle-PASS candidates and all three
rejected them. On FC-HIGH, all three produced oracle-FAIL candidates and all three
rejected them. Therefore the confirmation is non-discriminating with respect to
the architectural alternatives under test.

## Frozen exit-rule application

The predeclared rules were:

1. N1 matches or exceeds C-min with equal/better guards and lower/equal burden →
   REPLACE/DELETE CADS residue.
2. C-min materially exceeds N1 and C-current adds no material value → SHRINK to
   C-min.
3. C-current closes a repeated material failure that C-min cannot → retain only
   that demonstrated mechanism.
4. Confirmation is contaminated, non-discriminating or otherwise unfair →
   INCONCLUSIVE rather than preserving machinery by default.

Observed evidence does not establish rule 1 strongly enough to delete the residue:
full-project outcomes are equal in classification, but the controlled P1 XP-001
result prevents treating N1 sufficiency as proven. Rule 2 is also not established:
C-min's controlled XP-001 advantage did not survive full-project confirmation.
Rule 3 is not established: C-current closed no repeated material failure that
C-min could not. Rule 4 applies directly because both required confirmations are
non-discriminating.

## Final disposition

**INCONCLUSIVE**

This supersedes the provisional `SHRINK — benchmark-gated` research synthesis as
an architectural disposition. The provisional shrink hypothesis remains a useful
research hypothesis, not a promoted architecture decision.

Consequences:

- do not promote new durable CADS machinery from this challenge;
- do not claim C-min, C-current or N1 as the proven winner;
- do not preserve extra current-CADS ceremony merely because the benchmark did
  not prove deletion safe;
- do not rerun the same five-case corpus to manufacture a winner;
- keep architecture changes bounded and reversible until genuinely new evidence
  exists, such as a materially different model/harness capability or a new
  independently qualified product-derived failure class.

## What the evidence *does* support

- The five controlled P1 cases and both confirmations produced zero false-DONE
  classifications.
- Current-CADS showed no repeated incremental advantage over C-min.
- N1 did not show a safety-collapse signal in this corpus.
- C-min showed one controlled positive signal, but it was not confirmed in the
  full repository context.
- All three full-project arms were overconservative on the low-risk case and
  unable to solve the high-consequence case within one repair.

These findings justify stopping architecture expansion and keeping future changes
benchmark-gated. They do not justify a stronger KEEP, SHRINK, REPLACE or DELETE
claim under the frozen protocol.
