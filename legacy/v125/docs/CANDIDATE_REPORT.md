# Final candidate handoff

task_id=BUILD-OS-FINAL-ULTRA-CANDIDATE
task_status=PASS

ultra_architecture_tournament_completed=YES

candidate_families_considered=A repaired v1.21; B thin transactional kernel; C OS+Skills; D Git-native; E full event-sourced; F personal transactional harness (minimal OS + on-demand Skills + bounded local proof)

personal_scale_tournament=YES; sensitivity scores A=2.59, B=4.37, C=4.58, D=3.41, E=3.91, F=4.68 (/5 directional averages); C was the close runner-up and no enterprise/distributed-concurrency credit was included

winner=Personal Transactional Harness (minimal WHAT/WHEN/WHETHER OS + on-demand declarative Skills + bounded transactional snapshot proof)

why_winner=It keeps the OS a small trustworthy harness for one Windows owner: one logical authority, one local writer/linearization point, deterministic receipt-frontier recovery, immutable proof, pure validated transitions, honest Desktop supervision, and low Worker ceremony. Specialized HOW is on-demand Skill guidance, while the kernel directly removes v1.21's mutation-before-validation evidence loss and duplicated state authorities.

why_not_repaired_v121=The 55-script/31-command multi-file model retained sequential task/state/runtime/evidence failure windows; its reopen path deleted assurance evidence before a Git validator failed. Repairing ceremony would preserve the causal complexity and hidden authority drift.

why_not_alternative_families=B alone lacked an immutable cross-file proof/recovery anchor; C is attractive at this scale but without that small anchor cannot preserve evidence across a local crash (F retains C's static Skills and adds only the needed proof boundary); D cannot prove authorization/lifecycle/telemetry/evidence and has rebase/dirty edge cases; E full replay grows context/storage and needs compaction/schema migration. No family receives credit for enterprise-only coordination features.

skills_decision=USE_NOW

skills_role=Two optional, explicitly selected declarative SKILL.md guides (`python-change-v122`, `git-validation-v122`) demonstrate the on-demand HOW layer; the same path is available for FFmpeg, AutoSub, browser/UI, provider, release, and repository-specific procedures. They are untrusted guidance only; no executable plugins, registry, dynamic selection, risk/auth/lifecycle/evidence authority, or requirement that a Skill exist.

recommended_version=1.22-candidate

candidate_start_head=eb9dc8dda5d9c7c91a16c00718bd4c1d39df27ef
candidate_commit=RECORDED_IN_FINAL_HANDOFF (a commit cannot contain its own resulting SHA)

architecture_summary=Pure lifecycle FSM plus a small content-addressed generation store, atomic CURRENT locator, immutable commit receipts/evidence, measured Git adapter, context governor, optional bound telemetry, and a compact CLI facade. Specialized production HOW is loaded only through explicit static Skills. The active packet contains no history replay.

canonical_state_authority=Exactly one logical authority: the validated immutable generation selected by `.buildos/control/CURRENT`; CURRENT is an atomic locator, not a second state document.

transaction_mechanism=Single-writer OS advisory guard; validate -> pure candidate -> fsynced exclusive staging -> immutable hard-link publication -> Git re-observation -> atomic CURRENT replacement -> read-back verification -> immutable receipt -> monotonic packet projection. Recovery scans valid chains/receipts under the same guard and never guesses forks.

product_commit_semantics=Bootstrap stores base SHA/tree. A normal external Git commit advances HEAD; `record-commit` accepts a clean descendant, enforces path/risk/deletion/type scope, and stores target SHA/tree. `validate` binds checks/inspection/R3 proof to that target. A tree-equivalent descendant at close is a normal refresh; product changes after validation require a new revision and fresh evidence.

reopen_semantics=REMOVED. `recover` repairs only pointer/receipt/projection damage; `new-revision` preserves prior evidence and starts fresh proof. No evidence directory is deleted.

stable_kernel=model.py (pure state/invariants/transitions); store.py (lock, generations, CURRENT, receipts, recovery); git_adapter.py (Git observation); governor.py (pure thresholds/policy validation); telemetry.py (bound optional projection); facade.py (orchestration and packet)

adapters=Git observation; Codex/normalized telemetry adapters; CLI/admin entry points; optional explicit Skill resolver. Product-specific HOW (browser/media/renderer/health/economics/guardian) is outside the kernel.

worker_facade=bootstrap, status, next, record-commit, validate, rollover, close, recover

skills=skills/python-change-v122/SKILL.md; skills/git-validation-v122/SKILL.md; both optional and guidance-only

lifecycle_identities=Durable Task ID and immutable Revision generation/lineage. Attempt is not persisted. Epoch and thread_id are disposable runtime/telemetry identities; an explicit fresh thread_id is required for rollover. Operation ID is a retry key, not a user outcome identity.

lifecycle_states=UNINITIALIZED (no CURRENT), ACTIVE, PRODUCT_COMMITTED, ASSURANCE_READY, CLOSED, ABORTED, RECOVERY_REQUIRED (safe-stop result, not a guessed phase); HEADROOM_WARNING/COMPACT_REQUIRED/ROLLOVER_REQUIRED/HARD_STOP are orthogonal governor signals.

lifecycle_commands=bootstrap, record-commit, validate, rollover, close, recover, new-revision, abort (status/next are derived views; telemetry-ingest is an optional adapter)

persistent_runtime_artifacts=.buildos/control/CURRENT; .buildos/control/LOCK.guard; immutable generations; immutable receipts; immutable evidence; .buildos/runtime/WORK_PACKET.json; optional append-only .buildos/runtime/telemetry.jsonl; optional telemetry_baselines.json; immutable per-epoch telemetry_bindings/*.json; quarantine for invalid receipts

context_governor=PROJECTED_HEADROOM_ONE_CHAT_HYBRID. Latest prompt P drives action against effective runtime window W: warning at 50%, same-chat compact at 70%, evidence-gated rare rollover at 80%, and hard stop at W minus max(10% W, 25000, known payload/output reserve). Request count and historical PEAK are observational only. Missing W uses a labeled conservative 128k policy fallback; Desktop enforcement remains truthfully SUPERVISORY/BOUNDARY.

telemetry=Facade gives configured source adapters precedence, otherwise safely auto-binds the initial exact root-user Codex Desktop rollout or the exact validated rollover handoff to task/revision/epoch. Cumulative totals are baselined and distinct advances counted; latest P and runtime W drive policy while PEAK remains evidence. Cached/noncached/cache-write totals are advisory economics. Source absence is UNMEASURED, ambiguity/failure is explicit, and control actions are separately tagged CONTROL. Telemetry is a projection and cannot alter canonical lifecycle.

minimal_usage_scorecard=productive model requests; productive raw/cached/noncached/cache-write input tokens; productive output/reasoning tokens; control model requests/tool actions and control token totals; latest and peak productive prompt; effective runtime context window; epoch/rollover count; measurement coverage/status

risk_authorization=Pure side-effect floor: READ_ONLY=R0, write/create=R1, mutate/type change=R2, delete=R3. Explicit lower risk escalates rather than downgrades. R3 start/revision requires owner APPROVED + nonempty reference and rejects Worker self-approval; validation additionally requires independent reviewer/reference and a distinct rollback/recovery check. Missing/invalid Git, scope, or authorization fails closed.

proof_model=75 deterministic unittest cases: the original 45 cases preserve shared store failure injection at every low-level boundary; every lifecycle mutation at six meaningful boundaries plus bootstrap Git-exclude boundaries and retry; evidence publication failures; hard process-death lock recovery; stale/missing/corrupt CURRENT and receipt-frontier recovery; competing/forked receipts; global operation-key binding; monotonic status/packet projection; Git HEAD/root/scope/deletion/type/race/closed-retry cases; R0/R3 authorization; thread rollover and retry under fresher telemetry; telemetry available/unavailable/baseline/thread-binding/dedup; and direct/compact-facade unrelated-repository adoption. Thirty corrective cases add Desktop binding identity, ambiguity, immutable publication race/history/ancestry corruption, current-turn association, live-tail/replay, proportional thresholds, two real field traces, exact compact-rebaseline ordering, latest-versus-peak separation, explicit forked-rollover handoff, exact root-user continuation, legacy-binding compatibility, parallel repo/worktree rejection, stale/duplicate/missing continuation safety, safe-stop guidance, rollover idempotence, failure isolation, productive/control, and legacy-source coverage.

removed_or_demoted_from_v121=destructive reopen; prose/task/state/runtime files as authorities; multi-file sequential lifecycle writes; advisory-only transaction markers; durable Attempt/Epoch hierarchy; goal/economics/health/Guardian/browser/media-specific machinery; dynamic Skills/plugin framework; automatic Git rollback/rebase; replay/history in WORK_PACKET

project_specific_assumptions_removed=YouTube Auto names, renderer/browser/media harnesses, fixed branches/remotes, service/port assumptions, package-overlay nested directories, project health/economics gates, and copied product-local docs/config/scripts. Adoption uses an external package, reserved `.buildos/`, explicit Git observation, and optional namespaced `.buildos-policy.json` only.

stable_core_module_count=6
stable_core_loc=3941 (15 total Python files/6715 nonblank LOC including CLI, scripts, and proof suite; LOC is descriptive, not the selection objective)
lifecycle_command_count=8
mutable_runtime_file_count=4 (CURRENT, LOCK.guard, WORK_PACKET.json, normal-facade telemetry.jsonl; baseline and crash LOCK/quarantine are optional/exception artifacts; Desktop binding files are immutable)
canonical_state_authority_count=1
normal_bootstrap_actions=1
normal_closeout_actions=3 (record-commit, validate, close)
expected_normal_control_tool_calls=6 (design estimate: bootstrap + two status/checkpoints + record-commit + validate + close; rollover adds one when required; unmeasured until field run)

failure_injection_tests=PASS
retry_idempotence_tests=PASS
product_commit_transition_test=PASS
recovery_tests=PASS
authorization_tests=PASS
rollover_tests=PASS
telemetry_tests=PASS
generic_repo_adoption_test=PASS
full_candidate_self_test=PASS (75/75; 366.945 seconds on Windows)
diff_check=PASS (staged content/whitespace/manifest audit; exact clean-tree result is recorded in the final handoff after the single commit)

youtube_auto_modified=NO
production_runtime_modified=NO
production_8765_untouched=YES

known_residual_risks=Windows power-loss durability beyond process-crash atomicity is not claimed; Git commit and CURRENT cannot be one hardware transaction if a non-cooperative concurrent writer races the final micro-window; Desktop cannot hard-intercept model requests, so periodic status/next checkpoints remain supervisory; missing runtime W uses an explicitly labeled conservative fallback; immutable generation/evidence retention grows on disk until an explicit archive policy is applied; local tampering with reparse points or shell validation commands is outside the normal cooperative-worker threat model; absent prompt telemetry remains honestly UNMEASURED.

field_benchmark_ready=YES

recommended_single_field_benchmark_shape=Use the external candidate package against one clean, unrelated product worktree (no copied `.buildos` or tracked control path). Bootstrap one normal R1 or real R3 task, make the ordinary product Git commit, record it, run the real acceptance/inspection and (for R3) independent rollback proof, exercise status and same-chat compaction if telemetry crosses 70% of W, close, then inspect evidence/CURRENT/packet and run recovery once. Use rollover only with the documented rare-fallback evidence. Measure productive versus control metrics; do not run the benchmark here.

freeze_if_field_passes=YES

research_after_candidate=NONE

NEXT=READY_FOR_REAL_FIELD_PROOF

## Bounded telemetry governor activation corrective

The field proof exposed `CONFIG_NOT_ENABLED`: Desktop JSONL usage existed but
the optional configured-file adapter was never automatically selected. The
bounded corrective documented in `TELEMETRY_BINDING.md` adds native safe
Desktop binding. It preserves all 45 original
candidate proof behaviors and adds focused binding, ambiguity, parallel-stream,
field-replay, threshold, failure-isolation, and rollover regression coverage.
The final self-test passed all 61 cases (45 preserved plus 16 corrective) in
328.034 seconds on Windows, including the recovered read-only field trace.
This is a corrective candidate commit only; it does not promote or freeze the
release.

## Rollover session binding corrective

The next field proof exposed one remaining association defect: the legitimate
self-owned Desktop fork selected for the new epoch was globally rejected only
because its first header declared `thread_source=subagent`. The bounded fix
accepts only the exact canonical continuation whose immutable fork parent is
the immediately prior validated binding, while retaining task, worktree,
current-turn, ancestry, ambiguity, and stale-session checks. Failed or missing
coverage now yields an explicit current-epoch safe-stop without changing
canonical lifecycle state. The current self-test passed all 72 cases (45
preserved plus 27 corrective) in 316.931 seconds on Windows, including the
read-only failed rollover trace and repeated rollover association proof. This is
a corrective candidate commit only; it does not promote or freeze the release.

## Projected-headroom one-chat-first corrective

The recovered Advanced and Editorial field traces showed that the fixed 40k,
64k, five-request, and 128k policy fragmented healthy work and sent inherited
forks through costly cold starts. `PROJECTED_HEADROOM_ONE_CHAT_HYBRID` replaces
that policy without changing canonical state or successor binding. Current P,
not historical PEAK, now drives proportional 50/70/80 percent signals against
runtime W; same-chat compaction rebaselines P; rollover requires explicit
compact-failure or persistent post-compact loss evidence; and the hard reserve
is dynamic. This remains a bounded corrective candidate, not a field-frozen
release. The complete candidate self-test passed all 75 cases in 366.945
seconds on Windows; the independent generic-repository adoption/CLI smoke test
passed 2/2 cases in 15.866 seconds.
