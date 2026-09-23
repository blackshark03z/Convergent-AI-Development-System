# CADS Existential P1 Results — 2026-09-24

Status: P1 COMPLETE — FULL-PROJECT CONFIRMATION REQUIRED
Protocol: DR-0014 / `docs/CADS_EXISTENTIAL_CHALLENGE.md`
Pilot: `docs/CADS_EXISTENTIAL_PILOT_2026-09.md`

## Scope

This document freezes the interpretation of the five qualified P1 product-derived
counterfactual cases before any full-project confirmation run.

It does not promote an architecture change.

## Canonical P1 evidence

- XP-001: `evals/existential/results/XP-001/2026-09-23-xp001-ri-pilot-v2.json`
- XP-002: `evals/existential/results/XP-002/20260923T053251Z-5bc36fd5/result.json`
- XP-003: `evals/existential/results/XP-003/20260923T094959Z-0e1a1c3f/result.json`
- XP-004: `evals/existential/results/XP-004/20260923T133111Z-d881c77f/result.json`
- XP-005: `evals/existential/results/XP-005/20260923T194950Z-4020e96d/result.json`

All five P1 cases use product-derived pinned histories and a prequalified held-out
oracle. XP-002 through XP-005 use the automated existential runner. XP-001 is the
earlier valid reconstructed-session-continuity pilot recorded in its result.

## Outcome matrix

| Case | N0 | N1 | C-min | C-current |
|---|---|---|---|---|
| XP-001 low-risk fast path | NOT_READY / oracle FAIL / correct rejection | NOT_READY / oracle FAIL / correct rejection | READY / oracle PASS / correct acceptance | NOT_READY / oracle PASS / overconservative rejection |
| XP-002 intent ambiguity | NOT_READY / FAIL / correct rejection | NOT_READY / FAIL / correct rejection | NOT_READY / FAIL / correct rejection | NOT_READY / FAIL / correct rejection |
| XP-003 journey composition | NOT_READY / FAIL / correct rejection | NOT_READY / FAIL / correct rejection | NOT_READY / FAIL / correct rejection | NOT_READY / FAIL / correct rejection |
| XP-004 evidence / lineage | NOT_READY / FAIL / correct rejection | NOT_READY / FAIL / correct rejection | NOT_READY / FAIL / correct rejection | NOT_READY / FAIL / correct rejection |
| XP-005 consequential uncertain effect | NOT_READY / FAIL / correct rejection | NOT_READY / FAIL / correct rejection | NOT_READY / FAIL / correct rejection | NOT_READY / FAIL / correct rejection |

Across all five cases:
- false-DONE count is zero for every arm;
- XP-002 through XP-005 used exactly one repair in every arm;
- no arm requested Owner input in its phase-1 Implementation Brief for XP-002
  through XP-005.

## Available model-work burden

The following token totals cover XP-002 through XP-005 only. They are workload
indicators, not billed-cost claims. Cached tokens are included separately.

| Arm | Input tokens | Cached input | Uncached input | Output tokens |
|---|---:|---:|---:|---:|
| N0 | 15,199,996 | 13,914,752 | 1,285,244 | 93,338 |
| N1 | 10,539,399 | 9,489,152 | 1,050,247 | 68,738 |
| C-min | 13,772,003 | 12,569,856 | 1,202,147 | 96,171 |
| C-current | 17,710,902 | 16,370,688 | 1,340,214 | 104,475 |

Wall-clock comparison is not promoted as decisive because some recovered phases
have null duration fields. Owner-attention accounting is also not used to infer a
winner here because these automated runs requested no Owner input after launch.

## Bounded interpretation

1. **P1 materially differentiates the arms.** XP-001 is a real differentiator:
   C-min produced the only correct acceptance. C-current produced an oracle-PASS
   candidate but rejected it, so the current Thin-CADS treatment was
   overconservative on that case.

2. **The four harder cases do not establish a CADS advantage.** XP-002 through
   XP-005 ended in the same correct-rejection class for N0, N1, C-min and
   C-current. The held-out oracle found no accepted candidate in any arm.

3. **N1 is not showing a safety-collapse signal in this batch.** It produced no
   false DONE and correctly rejected all five cases. On the four automated cases
   it also used fewer recorded input/output tokens than C-min and C-current.
   This does not prove N1 is sufficient; it means the current P1 evidence has not
   demonstrated that the CADS residue closes a hard-case gap that N1 cannot.

4. **C-min has one positive signal that must be confirmed.** XP-001 is consistent
   with the provisional claim that a very small semantic residue can improve a
   simple product outcome without the stricter current-CADS acceptance burden.
   One controlled case is insufficient for promotion.

5. **C-current has no demonstrated incremental value over C-min in P1.** It has
   zero correct acceptances in the five-case batch and one overconservative
   rejection where C-min correctly accepted. This is evidence against preserving
   extra current-CADS ceremony by default, but the protocol still requires the
   confirmation step before an architectural disposition.

6. The hard-case failures may reflect task difficulty, the fixed R/I model pair,
   the one-repair ceiling, product architecture, or missing semantics. They are
   not evidence that the corresponding safety/identity problems are unimportant.

## Protocol consequence

The frozen pilot states:

> If controlled P1 materially differentiates N1, C-min and C-current, repeat at
> least one low-risk and one high-consequence case in the full real product repo.

That condition is now met. Therefore no KEEP / SHRINK / REPLACE / DELETE
promotion is valid yet.

## Predeclared full-project confirmation

Run exactly two confirmations before existential disposition:

### FC-LOW — XP-001 full-repo confirmation

- Source product: Story Trans And Audio.
- Reuse the XP-001 frozen Owner Goal, pinned product base and held-out oracle.
- Use the full repository snapshot at the pinned base; do not apply the P1
  neutralization projection.
- Compare N1, C-min and C-current. N0 is omitted because full-repo process
  contamination makes a No-CADS label misleading.
- Same R/I model profiles, tool authority, one-repair ceiling and evaluator
  semantics as the P1 batch.
- No reference implementation or held-out oracle bytes are visible to R/I.

### FC-HIGH — XP-005 full-repo confirmation

- Source product: Multiple Automation.
- Reuse the XP-005 frozen Owner Goal, pinned product base and held-out oracle.
- Use the full repository snapshot at the pinned base; do not apply the P1
  neutralization projection.
- Compare N1, C-min and C-current only.
- Keep live consequential submission forbidden; use local/provider fixtures only.
- Same R/I model profiles, tool authority, one-repair ceiling and evaluator
  semantics as the P1 batch.
- No reference implementation or held-out oracle bytes are visible to R/I.

Full-repo confirmation is intentionally a secondary test: all compared arms may
see product-repository process artifacts that P1 neutralization removed. It may
confirm whether the controlled differentiation survives realistic repository
context, but it must not erase or retroactively rewrite the fair P1 result.

## Exit rule after FC-LOW + FC-HIGH

Apply the already frozen pilot decision rule without adding new arms or changing
the acceptance threshold:

- if N1 matches or exceeds C-min with equal/better guards and lower/equal burden,
  dispose the CADS residue as REPLACE/DELETE;
- if C-min materially exceeds N1 and C-current adds no material value, SHRINK to
  C-min;
- if C-current closes a repeated material failure that C-min cannot, retain only
  that demonstrated mechanism;
- if confirmation is contaminated, non-discriminating or otherwise unfair,
  conclude INCONCLUSIVE rather than preserving machinery by default.
