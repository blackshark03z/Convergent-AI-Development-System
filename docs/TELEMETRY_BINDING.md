# Codex Desktop telemetry binding corrective

This bounded v1.22 corrective activates the existing context governor during
normal Codex Desktop work. It does not change lifecycle state, canonical
authority, risk, authorization, evidence, Skills, or governor thresholds.

## Binding contract

Configured normalized/app-server sources keep precedence. Otherwise the
Desktop adapter:

1. Reads the exact `CODEX_THREAD_ID` inherited by the facade process.
2. Resolves a rollout JSONL whose filename and first `session_meta.id` match
   that physical stream ID.
3. Requires `originator=Codex Desktop`, a root-user stream (`thread_source=user`
   and `id=session_id`), current-turn evidence for the Build OS task ID, and
   either an exact worktree cwd or current-turn worktree evidence. Replayed
   ancestor/history text cannot establish this association.
4. Persists an immutable binding keyed by Task, Revision, Epoch, and `epoch_id`.
   It records the physical source and the first safely observed cumulative
   baseline. A retry always reuses this file and never hops to a newer session.
5. Imports only cumulative advances after that baseline. Identical replayed
   `token_count` rows are deduplicated. A partially written final JSONL line is
   ignored; malformed complete records block only the adapter.

When no exact inherited ID exists, the fallback is intentionally narrower: the
session header cwd must equal the Git worktree, the task association must match,
the stream must still be active, and exactly one candidate may qualify. It
never chooses a globally newest file. `BUILDOS_CODEX_DESKTOP_SESSION_FILE`
provides a validated exact-file override. The sessions directory can be
relocated with `BUILDOS_CODEX_SESSIONS_DIR` for isolated installations/tests.

The observable binding states are:

- `BOUND`: immutable task/revision/epoch source selected;
- `TELEMETRY_UNBOUND/UNAVAILABLE`: no safe source, usage remains unmeasured;
- `TELEMETRY_UNBOUND/AMBIGUOUS`: multiple plausible sources, adapter blocked;
- `BOUND/SOURCE_UNAVAILABLE`: an already selected source path is temporarily
  absent, so its last measured projection is retained without rebinding;
- `ADAPTER_BLOCKED`: a source is malformed, has invalid required structure,
  conflicts with a prior epoch, or fails immutable identity validation.

These are projection diagnostics. They cannot mutate or invalidate `CURRENT`,
an immutable generation, a receipt, or lifecycle evidence.

## Accounting

The physical stream key is `session_meta.id`, not `session_id`: Desktop
subagents can share a parent `session_id` while maintaining independent token
counters. Automatic productive binding therefore excludes subagent streams.

One distinct cumulative `event_msg/token_count` advance is one productive model
request. Raw input, cached input, output, and reasoning come from the cumulative
Desktop totals. Noncached input is raw minus cached. Reasoning is already part
of output and is not added twice. The governor's prompt signal is the maximum
completed-request input after the persisted epoch baseline. `CONTROL` facade
tool actions remain separate and add zero model requests.

## Field replay

The recovered read-only `ADVANCED-STILL-CAMERA-MOTION-V1` Desktop trace parses
to the forensic full-turn totals:

```text
productive_requests=59
productive_raw_input_tokens=6483208
productive_cached_input_tokens=6276352
productive_noncached_input_tokens=206856
productive_output_tokens=28180
productive_reasoning_tokens=11521
max_context_signal=179884
```

v1.22 already defined first-bind baseline accounting. At the actual bootstrap
point, 10 requests had completed. A corrected adapter active at that point
therefore measures the following post-bind task/epoch usage, rather than
retroactively claiming the first ten requests:

```text
productive_requests=49
productive_raw_input_tokens=6222896
productive_cached_input_tokens=6047488
productive_noncached_input_tokens=175408
productive_output_tokens=25094
productive_reasoning_tokens=10245
max_context_signal=179884
```

That bounded replay reaches the fifth-request rollover requirement and the
40k compact, 64k rollover, and 128k hard-stop prompt boundaries. A first bind
performed only after a completed historical trace intentionally baselines the
tail; `inspect_desktop_session` is the read-only forensic parser used to verify
the full-turn counters without changing live accounting policy.

## Rollover

Rollover remains a normal canonical epoch transition with the same Task and
Revision and a fresh disposable `epoch_id`/thread label. Projection then binds
the new caller's physical Desktop stream under a new immutable binding. Prior
epoch stream IDs are excluded, and summary grouping remains epoch-scoped, so
old and new counters cannot be collapsed into one current-epoch value.

Desktop enforcement remains truthfully `SUPERVISORY`: the governor makes the
required next action visible in status/WORK_PACKET but cannot intercept an
already issued provider request.
