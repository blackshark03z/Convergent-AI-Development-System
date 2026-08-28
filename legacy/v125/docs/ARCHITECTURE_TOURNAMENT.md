# Architecture tournament

## Hard field inputs

The v1.21 adoption and corrective lineage was:

| item | Git identity |
|---|---|
| adoption | `1cc2008d95345ca7629714ac6af0e68fdf755f9f` |
| corrective #1 | `653490a3d0a1056ff9e582795bc32d4a19fb8d96` |
| corrective #2 | `bef92e6ec612c994958f70f16db86ae9b13efc7e` |

The pathological pre-v1.21 run measured 149 requests, 144 tool actions,
16,762,045 raw input tokens, a 218,627 maximum context, and 39 closeout
requests. Benchmark #1 reduced execution to 70 requests/58 tool actions and
6,397,174 raw input tokens (6,046,976 cached; 350,198 noncached), but still
reached a 144,689 context signal with no rollover and did not collect normal
workflow telemetry. The observed v1.21 reopen failure deleted the assurance
bundle before validating a legitimate Git HEAD advancement, leaving READY
state with missing evidence. The release package measured 55 scripts, about
12,596 Python LOC, 31 canonical commands, and ten mutable runtime files.

## Personal-production constraint

This is a harness for one owner on a Windows workstation, not a team control
plane. The tournament gives no bonus for RBAC, multi-user coordination,
clusters, remote workers, a central database, SaaS tenancy, or a plugin
marketplace. It gives extra weight to failures that are actually expensive in
this workload: a process dying during a local code/media operation, an
accidental mutation of a production repository, a lost review bundle, a stale
Codex Desktop continuation, and the friction of making a normal Git commit.

The selected design keeps only the local crash/retry machinery that prevents
those concrete failures. Its writer guard is a single-workstation safety
boundary, not an enterprise concurrency service; immutable generations are
inspectable files, not a distributed event store. Specialized HOW is loaded
on demand as static Skill guidance, so Python, FFmpeg, AutoSub, browser/UI,
provider, release, and repository-specific procedures stay outside the
universal WHAT/WHEN/WHETHER kernel. The generic flow remains valid with zero
Skills.

## Scoring method

Each family received a directional 1-5 score. The original weights sum to 100
and favor accepted quality, invariants, failure atomicity, deterministic
recovery, low ceremony, testability, and resistance to hidden field failures.
The totals are structural estimates, not measurements or false precision.

| family | original weighted /500 | original average /5 |
|---|---:|---:|
| A repaired v1.21 | 259 | 2.59 |
| B thin transactional kernel | 446 | 4.46 |
| C OS + Skills | 409 | 4.09 |
| D Git-native control | 346 | 3.46 |
| E full append-only/event-sourced | 409 | 4.09 |
| F personal transactional harness (minimal OS + Skills + bounded snapshot proof) | **471** | **4.71** |

The original principal axes and weights were: invariant strength 10, failure
atomicity 10, deterministic recovery 10, mutable-authority reduction 8,
lifecycle-op reduction 5, mandatory-artifact reduction 4, Worker load 7,
model-request overhead 6, prompt/context overhead 6, observability 5,
portability 5, testability 6, migration simplicity 4, hidden-field-failure
resistance 8, R0/R3 support 3, and Desktop compatibility 3.

For auditability, the original 1-5 score vectors in exactly that axis order
were: A `[4,2,3,1,2,1,2,2,2,4,3,3,4,2,5,3]`; B
`[5,5,4,5,5,4,5,4,4,4,5,5,2,4,4,5]`; C
`[5,5,4,4,4,4,4,4,4,4,5,4,2,3,4,4]`; D
`[3,4,3,4,4,4,4,4,4,3,2,4,2,3,3,4]`; E
`[5,5,5,4,4,2,4,3,3,5,4,5,1,4,4,4]`; and F
`[5,5,5,5,5,4,5,4,4,4,5,5,3,5,5,5]`.

### Personal-scale sensitivity check

To test that the selection was not an enterprise-complexity artifact, we
reweighted the axes and rescored the explicit on-demand Skill split for this
actual workload. The 100 points
are: accepted quality/safety 8, invariants 8, failure atomicity 8,
deterministic recovery 7, mutable-authority reduction 6, lifecycle-operation
reduction 8, mandatory-artifact reduction 6, Worker load 8, model-request
overhead 5, prompt/context overhead 5, observability 4, portability 5,
testability 4, migration simplicity 6, hidden-field-failure resistance 7,
R0/R3 support 3, and Desktop compatibility 2. No distributed-concurrency or
enterprise-compliance points are included.

| family | personal-scale weighted /500 | average /5 |
|---|---:|---:|
| A repaired v1.21 | 259 | 2.59 |
| B thin transactional kernel | 437 | 4.37 |
| C OS + Skills (without bounded proof anchor) | 458 | 4.58 |
| D Git-native control | 341 | 3.41 |
| E full append-only/event-sourced | 391 | 3.91 |
| F personal transactional harness (C + bounded local proof) | **468** | **4.68** |

The personal-scale vectors add accepted quality/safety as the first axis, then
use the sixteen axes above: A
`[3,4,2,3,1,2,1,2,2,2,4,3,3,4,2,5,3]`; B
`[4,5,5,4,5,5,4,5,4,4,4,5,5,2,4,4,5]`; C
`[5,5,4,4,4,5,5,5,5,5,4,5,4,4,4,5,5]`; D
`[3,3,4,3,4,4,4,4,4,4,3,2,4,2,3,3,4]`; E
`[4,5,5,5,4,4,2,4,3,3,5,4,5,1,4,4,4]`; and F
`[5,5,5,5,5,5,4,5,4,4,4,5,5,3,5,5,5]`.

The sensitivity result makes C the close runner-up and still selects F. C earns
top marks for operations, artifacts, Worker load, and prompt reuse; it loses
only because the exact local crash/evidence failure still needs a durable
commit witness. F's narrow margin comes from that local behavior, not from
multi-user or distributed features. F is implemented as a small OS around
Codex with optional on-demand Skills, not as a general workflow platform.

## Family decisions

**A - Repaired v1.21.** It retains useful risk and assurance gates, but its
causal complexity is the defect: prose, task/state/runtime/evidence files and
many commands remain mutable authorities. Sequential writes, advisory intent
journals, and the observed destructive `reopen` leave failure windows. The
Worker must remember activation, governor, telemetry, and reconciliation
ceremony.

**B - Thin transactional kernel.** This is the best baseline: a pure FSM,
risk/authorization, governor, Git adapter, and optional telemetry are small,
portable, and testable. It needs immutable evidence and a recovery anchor to
make cross-resource side effects safe; those are supplied by F.

**C - OS + Skills.** At personal scale this is a serious contender: a static
`skill.md` can carry Python, FFmpeg, AutoSub, browser, UI, provider, or release
HOW without making every task prompt repeat it. A pure C design still needs a
durable proof/recovery boundary for the exact evidence-loss failure observed in
v1.21. Dynamic discovery, executable plugins, wrong-skill selection, and
version precedence are rejected. The selected F keeps the useful C split and
ships two explicit guides as examples; the kernel remains safe with none.

**D - Git-native.** Git naturally proves commit/tree identity and ancestry,
but cannot prove owner authorization, lifecycle, reviewer evidence, telemetry,
context limits, or a non-Git adoption boundary. Rebase, dirty-tree, and
control-path cases still require a sidecar kernel.

**E - Full event sourcing.** Immutable history and replay are attractive, but
unbounded event growth, compaction/schema migration, and replay/context cost
are disproportionate for a six-transition control plane. F borrows bounded
active projections and receipts without making model context a replay log.

**F - selected: Personal transactional harness.** This is C plus the smallest
bounded proof machinery that C alone lacks: one single-writer local snapshot,
immutable generations/evidence, a receipt frontier, deterministic recovery,
and Git as a measured anchor. It eliminates the observed v1.21 failure while
keeping the packet and Worker interaction small. There is no RBAC, cluster,
remote coordinator, database service, or plugin framework. The active packet
never contains history; immutable proof remains inspectable on disk. Long-term
generation/evidence retention is an explicit archive responsibility rather than
hidden lifecycle mutation.

## Adversarial semantics

The candidate treats `CURRENT` as the linearization point. A precommit Git
re-observation rejects stale product anchors; a post-swap process crash is
recovered from the valid pointer and receipt frontier. A pointer older than a
valid receipt, competing receipt histories, malformed generation/receipt JSON,
or a reused operation key are safe-stop conditions. Staging files are
noncanonical; immutable evidence is never deleted.

Product commits are ordinary external Git commits. `record-commit` accepts a
clean descendant of the bootstrap anchor and stores its SHA/tree. Validation
binds checks and inspection evidence to that target. A tree-equivalent
descendant at close is a normal refresh; product changes after validation stay
assured-but-open and require an explicit new revision. There is no destructive
reopen.

R3 authorization is validated before any canonical mutation and requires an
approved owner reference plus a non-self reviewer, distinct rollback check,
and immutable evidence. Risk floors are derived from side effect; a request
cannot downgrade DELETE/type changes to R0/R1. Read-only tasks validate an
unchanged baseline directly and cannot record a product commit.

The corrective governor is one-chat-first: current P is compared with runtime
W at 50% warning, 70% same-chat compact, evidence-gated 80% rare rollover, and
a dynamic hard reserve. Historical PEAK and request count remain evidence only.
A project cannot restore fixed 40k/64k/five-request/128k triggers or claim HARD
interception. Source telemetry is task/epoch bound; absent productive prompt
measurements stay UNMEASURED even when control-plane overhead is known.
