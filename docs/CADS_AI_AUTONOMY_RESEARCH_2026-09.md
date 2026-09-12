# CADS AI Autonomy Research — September 2026

Status: Research synthesis
Date: 2026-09-12
Scope: CADS / MAR / coding-agent architecture

## Question

How should CADS evolve to maximize verified product-development throughput,
quality and autonomy while minimizing Owner attention and avoiding a framework
that becomes obsolete as coding-agent harnesses improve?

The working north star is:

> Maximize verified autonomous product throughput per unit of human attention.

A shorter operating principle is:

> Owner declares intent. AI owns ordinary engineering work. Trusted evidence
> owns technical verdicts. Human attention is an exception.

This research does not amend the frozen Convergent AI Development Standard. It
records current evidence, an independent red-team review, the resulting design
direction and the experiments required before further promotion.

## Evidence basis

The synthesis used:

- current CADS repository architecture, Standard, playbooks and Decision Records;
- the 2026-09-12 internal Tech Lead review brief on autonomy, self-repair,
  evidence and escalation;
- an independent third-party red-team review that returned `MODIFY_DIRECTION`;
- public 2026 material reviewed in that red-team pass from OpenAI/Codex,
  Anthropic/Claude Code, GitHub Copilot, Google Gemini CLI, Devin/Cognition and
  METR.

External references used in the review include:

- OpenAI — Harness engineering: https://openai.com/index/harness-engineering/
- OpenAI — Running Codex safely: https://openai.com/index/running-codex-safely/
- Anthropic — Claude Code expertise/use research:
  https://www.anthropic.com/research/claude-code-expertise
- GitHub Copilot App concepts:
  https://docs.github.com/en/copilot/concepts/agents/github-copilot-app
- GitHub Copilot code review / Agent Skills:
  https://github.blog/changelog/2026-07-29-copilot-code-review-agent-skills-and-mcp-now-generally-available/
- Gemini CLI subagents:
  https://developers.googleblog.com/subagents-have-arrived-in-gemini-cli/
- Devin advanced capabilities:
  https://docs.devin.ai/work-with-devin/advanced-capabilities
- Devin Skills: https://docs.devin.ai/product-guides/skills
- METR time horizons: https://metr.org/time-horizons/
- METR GPT-5.6 Sol evaluation:
  https://metr.org/blog/2026-06-26-gpt-5-6-sol/

These references support architecture direction, not a claim that every vendor
feature or guarantee is equivalent. Provider behavior must be verified before
CADS/MAR relies on it for a concrete authority or safety guarantee.

## Findings

### 1. Coding is becoming less of the bottleneck

Frontier coding harnesses increasingly own repo exploration, long tool-use
sequences, subagents, isolated workspaces, browser/computer use, self-repair and
normal orchestration. The durable problem moves toward intent quality,
environment legibility, objective verification, authority, integration and
feedback loops.

CADS should therefore not compete with vendor intelligence or ordinary
orchestration. Its long-lived value is engineering semantics: Goal/CUJ/
acceptance, source-of-truth precedence, authority boundaries, evidence
requirements, product/invariant reasoning and consequence semantics.

### 2. Current thin CADS architecture remains directionally correct

The existing five controls remain the preferred universal mental model:

`Reality -> Intent / Design -> Change -> Acceptance -> Consequence`

No evidence from this review justifies restoring a task lifecycle engine,
permanent role hierarchy, context database, generic model router or always-on
review bureaucracy. DR-0003's anti-accretion rule remains applicable.

### 3. The main weakness is enforcement, not missing prose

CADS already states several important semantics:

- acceptance is defined before implementation and may not be weakened merely to
  make the implementation pass;
- verification independence is in the oracle, not necessarily in a second
  model or human;
- evidence without candidate/runtime identity is weak evidence;
- tests and agent reports alone do not establish Product Goal completion;
- Git/source, runtime and tests have distinct authority.

The gap is turning those semantics into objective, identity-bound evidence that
can support a deterministic technical verdict without adding a second task
runtime.

### 4. "Evidence" must mean trusted evidence

A Worker claim such as `completed=true`, a self-authored report, or a test whose
oracle was weakened by the implementation Worker is not strong completion
proof.

The implementation direction should therefore evaluate an **Evidence Envelope**:
criterion-oriented evidence tied to the exact candidate, environment and
verifier/oracle identity. A deterministic verifier derives `VERIFIED`,
`NOT_VERIFIED` or `UNKNOWN`; the Worker does not set the final technical verdict
directly.

The envelope is evidence/provenance, not workflow state. It must not contain
chain-of-thought, planner state, subagent hierarchy, model-routing history or a
persisted task lifecycle.

A candidate shape to evaluate is:

```text
goal_ref
candidate:
  base_revision
  candidate_revision
criteria:
  - criterion_id
    oracle_type
    verifier_identity
    verifier_version
    result: PASS | FAIL | UNKNOWN
    evidence_refs
invariants:
  - invariant_id
    result
    evidence_refs
authority:
  required_authorization
  authorization_status
review:
  required
  blocking_findings
provenance:
  execution_environment
  evidence_producer
derived_verdict:
  VERIFIED | NOT_VERIFIED | UNKNOWN
```

This is a research candidate, not yet a frozen universal schema.

### 5. Oracle integrity is a first-class concern

High autonomy creates Goodhart risk: an agent can optimize a metric or change a
test without satisfying product intent. CADS already has Verification
Independence; implementation should make relevant oracle mutation visible.

Where material to acceptance, evidence should be able to answer:

- did the oracle exist before the implementation change?
- did the candidate change the oracle/test?
- was that oracle change an accepted clarification or an unauthorized weakening?
- is there independent evidence for the criterion?

Not every test change requires human approval. The goal is provenance and
independence, not ceremony.

### 6. Replace "single writer" with "single canonical integration authority"

Parallel candidate generation is increasingly native to modern harnesses and can
improve throughput when isolated. File-level worktree isolation alone does not
solve semantic conflicts, but banning all parallel writing would unnecessarily
limit future capability.

Preferred invariant:

> Multiple isolated agents may explore or produce candidate changes when
> decomposition/conflict risk is bounded. Exactly one authority advances the
> canonical product state.

For small work, one active workline remains the default because it minimizes
coordination cost. Parallelism is a capability, not a mandatory organization.

### 7. MAR should own guarantees, not duplicate vendor mechanisms

The preferred responsibility split is:

**CADS owns**

- Goal/CUJ/acceptance semantics;
- engineering/source-of-truth/authority semantics;
- risk and evidence requirements;
- portable engineering skills and invariants.

**Model / harness owns**

- reasoning/planning;
- repo exploration and ordinary coding;
- normal context management;
- subagents and task decomposition;
- browser/computer use;
- ordinary self-repair and vendor-native orchestration.

**Project/runtime/CI owns**

- executable oracles;
- runtime observations;
- product-specific regression and invariant checks.

**MAR / integration authority owns only portable guarantees that must survive
vendor changes**, such as:

- candidate identity and evidence binding;
- canonical integration authority;
- consequential mutation/effect authority;
- stale-writer fencing where required;
- missing isolation guarantees that the selected harness does not provide;
- crash-safe canonical integration;
- cross-provider telemetry/audit where useful.

If a vendor already supplies a guarantee with adequate semantics and
auditability, MAR should prefer verifying/using that capability over rebuilding
an equivalent subsystem.

### 8. Autonomy should be eval-gated, not model-name- or recent-success-gated

Do not encode rules such as `Model X gets tier 4 authority`, and do not let a
short production success streak automatically expand permissions. Task mix and
oracle weakness can distort success metrics.

Preferred direction:

`model/harness -> representative CADS eval suite -> demonstrated capability
profile -> allowed autonomy envelope`

Production telemetry updates evidence and future evals. It should not silently
self-modify CADS policy or grant authority online.

### 9. Self-repair should optimize convergence, not retry count

`retry_count >= N -> human` is too primitive, but an unbounded
"continue while information increases" policy can also waste resources.

Continue autonomous repair while all are true:

- the action remains safe/reversible within authority;
- acceptance has not been silently changed;
- measurable progress toward the Goal exists; and
- the declared resource budget remains.

When progress stalls, prefer replan -> fresh review/alternate approach -> human
only when a genuine Owner-controlled decision or non-delegable authority is
required.

### 10. Fresh review is conditional capability, not a permanent role

A read-only fresh reviewer is useful when oracle weakness, consequence or
semantic novelty justifies it. Likely triggers include security/permission,
external effects, persistent-state/migration changes, architectural boundaries,
weak/non-deterministic oracles, interacting parallel candidates, repeated
non-converging repair, or material acceptance/test changes by the implementation
Worker.

The reviewer must not silently change Goal/acceptance, mutate the candidate or
advance canonical state. Same-model fresh context is the default; a different
model is justified only when measured incremental value supports the cost.

### 11. Owner owns acceptance semantics/authority, not every acceptance action

The Standard already limits Owner subjective acceptance to cases where human
experience is the oracle. A user-facing Goal that is fully and objectively
machine-observable should not require manual Owner ceremony solely because it has
a UI.

Owner attention remains required for subjective product/UX judgement, material
product trade-offs and non-delegable consequential authority.

### 12. Context should remain repo-first and portable

Keep `AGENTS.md` as a short activation/routing map and use progressive,
non-monolithic skills. Portable Agent Skills-compatible packaging is a reasonable
future projection of the same canonical knowledge, but CADS should not create a
sync daemon, vector database or vendor-specific duplicated standards unless real
failure demonstrates the need.

### 13. Measure autonomy instead of debating it

The most useful next investment after the small documentation corrections is a
representative CADS autonomy evaluation set built from real failure classes.
Important measures include:

- Owner active-attention minutes per verified accepted Goal;
- time-to-verified-done;
- escaped-defect and false-DONE rate;
- reopen/rollback/post-integration repair rate;
- repair iterations/cost stratified by risk;
- acceptance criteria with objective identity-bound evidence;
- fresh-review incremental defect discovery when applicable;
- Owner re-explanation load: how often the Owner must restate an already-set
  requirement, flow, decision or previously reported defect.

Metrics must be stratified by task difficulty/risk so easier tasks or weaker
oracles cannot masquerade as improved autonomy.

## Preferred architecture: B-prime

The research direction is named **B-prime — Trusted Evidence Kernel + Runtime
Authority + Vendor-Native Intelligence**.

It is not a new runtime or sixth CADS control. It is a responsibility boundary:

```text
Owner
  -> intent / material trade-offs / subjective judgement / consequential authority

CADS
  -> Goal/CUJ/acceptance + engineering/authority/evidence semantics + skills

Model/Harness
  -> intelligence + ordinary orchestration + coding + self-repair + subagents

Project Runtime / CI
  -> objective oracles and observed behavior

MAR / Integration Authority
  -> only missing portable guarantees, evidence binding, canonical/effect authority

Git
  -> canonical source state
```

The durable invariants are:

1. Owner owns intent and non-delegable judgement/authority.
2. AI owns ordinary engineering execution and self-repair.
3. Trusted, identity-bound, independently valid evidence owns technical verdicts.
4. Exactly one authority advances canonical state; isolated agents may produce
   candidates in parallel when justified.

## Do not build from this research alone

Do not add, without new evidence:

- a CADS task lifecycle database or persistent phase machine;
- permanent planner/architect/coder/QA/reviewer role organizations;
- a generic cross-vendor model router;
- a global vector/knowledge database or context planner;
- always-on expensive LLM review for every change;
- agent-authored final `DONE=true` as completion authority;
- trust tiers based on model names;
- online self-modifying CADS policy;
- a sophisticated information-gain policy engine;
- MAR reimplementations of vendor sandbox/subagent/context mechanisms when the
  vendor guarantee is already adequate;
- multiple agents mutating the canonical worktree concurrently.

## Revisit / kill criteria

Revisit or shrink a proposed mechanism when evidence shows it is not improving
the north star. In particular:

- shrink the Evidence Envelope if it creates substantial ceremony/latency
  without reducing false-DONE, escaped defects or Owner QA burden;
- shrink MAR when vendor-native guarantees become equivalent and MAR is only a
  duplicate proxy;
- increase isolated parallel candidate writing only if wall-clock improvement
  exceeds integration/semantic reconciliation cost;
- remove a fresh-review trigger class if matched experiments show poor defect
  yield and excessive false positives/cost;
- restore mandatory Owner acceptance for a Goal class if objective machine
  acceptance repeatedly passes while meaningful Owner product failures escape;
- reconsider the whole direction if, after a representative set of real Goals,
  Owner active attention per verified product outcome does not decrease.

## Implementation direction

See `docs/CADS_AUTONOMY_IMPLEMENTATION_PLAN.md` and DR-0004. The immediate work
is intentionally narrow: correct the Product Acceptance Owner gate, prototype
Evidence Envelope/Oracle Integrity as an evaluated candidate rather than a new
universal lifecycle, build an autonomy eval set, and audit MAR against the
responsibility boundary above.
