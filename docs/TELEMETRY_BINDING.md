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
   either an exact worktree cwd or current-turn worktree evidence. The sole
   exception is the explicit rollover handoff described below. Replayed
   ancestor/history text cannot establish either association.
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
- `TELEMETRY_UNBOUND/NOT_EXPECTED_CONTINUATION`: the caller is not the exact
  physical session named by the current rollover epoch;
- `BOUND/SOURCE_UNAVAILABLE`: an already selected source path is temporarily
  absent, so its last measured projection is retained without rebinding;
- `ADAPTER_BLOCKED`: a source is malformed, has invalid required structure,
  conflicts with a prior epoch, or fails immutable identity validation.

These are projection diagnostics. They cannot mutate or invalidate `CURRENT`,
an immutable generation, a receipt, or lifecycle evidence.

## Accounting

The physical stream key is `session_meta.id`, not `session_id`: Desktop
subagents can share a parent `session_id` while maintaining independent token
counters. Automatic productive binding therefore excludes subagent streams
except for the exact validated rollover handoff described below.

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
Revision and a fresh disposable `epoch_id`/`thread_id`. The existing rollover
generation is also the narrow handoff producer: its current context names the
one expected physical Desktop continuation. `WORK_PACKET.json` projects that
same non-durable ID for Worker visibility, but remains guidance only.

The consumer is Desktop discovery for the current epoch. A root-user
continuation must have the exact expected physical ID. A Desktop fork may bind
only when all of the following hold:

1. its first header is self-owned (`id=session_id`) and declares
   `thread_source=subagent`;
2. its physical ID equals the current canonical rollover `thread_id`;
3. its first-header `forked_from_id` equals the validated immutable binding for
   the immediately previous epoch of the same Task and Revision in this exact
   worktree; and
4. current-turn Task and exact-worktree evidence passes the ordinary strict
   association checks.

The handoff is scoped to the current disposable epoch and is invalidated when
`CURRENT` selects another epoch, Revision, or Task. It is not a replayable
token, session registry, or telemetry authority. When `CODEX_THREAD_ID` is
present after rollover it must equal the canonical expected ID; an unrelated
newer caller cannot override it. Duplicate physical files remain ambiguous,
prior sessions remain rejected, and the immutable epoch binding makes retry
idempotent. The binding fingerprints the fork parent, records association kind
plus parent for later header validation, and validates every persisted handoff
against the immediately preceding epoch. Legacy root-user bindings already
persisted by the first v1.22 corrective remain readable, but new rollover
discovery never substitutes an arbitrary physical stream for the expected ID.

Only while executing the next rollover may the currently bound Desktop caller
or the exact requested fresh caller consume the persisted prior epoch's
already-recorded governor signal. When inherited `CODEX_THREAD_ID` differs from
the bound source, it must exactly equal the requested new `thread_id`.
Callerless CLI operation retains its existing access to the bound source.
Ordinary status from a mismatched Desktop caller remains unbound until the
transition makes it the expected epoch, keeping repeated B-to-C rollovers usable
without letting C masquerade as B.

If the expected source is missing, ambiguous, malformed, or no longer
available, lifecycle state remains valid and current-epoch governor coverage is
UNMEASURED. `WORK_PACKET.json` exposes `telemetry_binding_status` and
`telemetry_binding_reason`, and its next action explicitly stops model work
until the expected binding is restored. Aggregate prior-epoch measurements do
not advertise current-epoch coverage in that packet.

Prior epoch stream IDs are excluded, and summary grouping remains epoch-scoped,
so old and new counters cannot be collapsed into one current-epoch value.

Desktop enforcement remains truthfully `SUPERVISORY`: the governor makes the
required next action visible in status/WORK_PACKET but cannot intercept an
already issued provider request.
