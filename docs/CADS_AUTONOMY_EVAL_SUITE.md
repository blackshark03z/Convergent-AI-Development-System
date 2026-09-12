# CADS Autonomy Eval Suite

Status: Initial representative dataset
Date: 2026-09-12

## Purpose

Measure whether CADS changes improve the real operating model of one Owner plus AI without turning evaluation into another CADS runtime.

The suite is a **dataset and scoring rubric**, not a scheduler, task database, model router, persisted workflow or authority system. Any harness may execute the cases. CADS only defines what must be measured and what shortcuts invalidate the comparison.

## Dataset

`evals/autonomy/cases.json` contains 20 representative Goals derived from failure classes observed across CADS-related product work and architecture reviews. Cases are intentionally phrased as reusable engineering scenarios rather than product-specific scripts.

The initial suite covers repeated-workflow state leakage, end-to-end journey composition failure, runtime/source identity mismatch, ambiguous external effects, weak/missing acceptance oracles, oracle self-proof, decision/context drift, non-converging repair, persistence compatibility, UI discoverability, subjective acceptance boundaries, isolated parallel candidates, semantic conflict, stale physical writers, provider fallback, artifact immutability and conditional fresh review.

## What a run records

A comparison run should record per case, outside the canonical case dataset:

- configuration label (for example current thin CADS vs B-prime candidate);
- model/harness/tooling profile, by concrete version where available;
- final Goal verdict and acceptance evidence references;
- Owner active-attention minutes;
- Owner re-explanation count;
- wall-clock duration;
- model/tool cost where measurable;
- repair iterations;
- false-DONE / escaped defect / reopen / rollback outcomes;
- identity-bound evidence coverage;
- whether expected human-attention boundary was respected.

Do not add live run state to `cases.json`. Results may be ephemeral or stored as normal eval artifacts by the executing harness/project.

## Primary score

Primary north-star comparison: `verified accepted Goals / Owner active-attention minutes`.

When Owner attention is zero, report the numerator and zero-attention count explicitly rather than dividing by zero or inventing a denominator.

Always pair the primary score with guard metrics: false-DONE/escaped defects; reopen/rollback/post-integration repair; consequential incidents; oracle strength and evidence coverage; wall-clock/compute/tool cost; and Owner re-explanation load.

Stratify results by risk and failure class. A system must not appear more autonomous merely because it receives easier Goals or weaker oracles.

## Comparison rule

At minimum compare a current thin-CADS baseline with the B-prime candidate mechanisms actually under test, such as Evidence Envelope / Oracle Integrity. Keep Goal text, acceptance meaning and environmental preconditions equivalent between compared runs. Do not rewrite acceptance after observing a candidate merely to make one configuration pass.

## Case interpretation

Each case declares `oracle_strength`, `expected_behavior`, `expected_human_attention`, `required_evidence`, `failure_signals` and `anti_shortcuts`. These are evaluation semantics, not a process lifecycle. Harnesses remain free to plan, parallelize, use subagents, repair and inspect context however they choose within authority.

## Promotion rule

Do not promote a new CADS/MAR mechanism because it sounds more agentic or because it performs well on one case. Promotion requires representative evidence that it improves the north star or closes a serious safety/authority gap without unacceptable regression in guard metrics.

A mechanism should be shrunk or removed when it adds ceremony/latency without reducing false-DONE, escaped defects or Owner attention/re-explanation load.

## Integrity

The validator in `scripts/validate_autonomy_evals.py` checks only dataset structure and coverage. It does **not** judge model capability or product correctness. Passing validation means the eval definitions are well-formed, not that CADS passes the eval suite.