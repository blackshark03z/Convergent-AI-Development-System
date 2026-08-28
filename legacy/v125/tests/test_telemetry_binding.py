from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
from threading import Barrier
import unittest
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[1]
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))

from buildos.facade import BuildOS
from buildos.governor import decide
from buildos.model import KernelError
from buildos.store import read_current
from buildos.telemetry import (
    _desktop_header_fingerprint,
    _persist_binding,
    discover_desktop_session,
    inspect_desktop_session,
)
from tests.test_candidate import generic_repo, request, run_git


FIELD_TRACE = Path(
    r"C:\Users\ADMIN\.codex\sessions\2026\08\11\rollout-2026-08-11T06-38-27-019fee0a-b54a-7190-8a6f-d100ddb06a3a.jsonl"
)
EDITORIAL_FIELD_TRACE = Path(
    r"C:\Users\ADMIN\.codex\sessions\2026\08\11\rollout-2026-08-11T07-59-44-019fee55-2373-7402-a2ab-1690908c2fed.jsonl"
)
FIELD_ROOT = Path(r"D:\Youtube\Youtube Studio\_worktrees\advanced-still-camera-motion-v1")
FIELD_TASK = "ADVANCED-STILL-CAMERA-MOTION-V1"
ROLLOVER_FIELD_TRACE = Path(
    r"C:\Users\ADMIN\.codex\sessions\2026\08\11\rollout-2026-08-11T08-02-09-019fee57-56d3-7f50-a14a-b026a8da8500.jsonl"
)
ROLLOVER_FIELD_SESSIONS = Path(r"C:\Users\ADMIN\.codex\sessions")
ROLLOVER_FIELD_ROOT = Path(r"D:\Youtube\Youtube Studio\_worktrees\editorial-punch-zoom-v1")
ROLLOVER_FIELD_TASK = "EDITORIAL-PUNCH-ZOOM-V1"
ROLLOVER_FIELD_PARENT = "019fee55-2373-7402-a2ab-1690908c2fed"
ROLLOVER_FIELD_SESSION = "019fee57-56d3-7f50-a14a-b026a8da8500"
FIELD_BASELINE = {
    "raw_input_tokens": 260_312,
    "cached_input_tokens": 228_864,
    "output_tokens": 3_086,
    "reasoning_tokens": 1_276,
}
FIELD_TOTAL = {
    "raw_input_tokens": 6_483_208,
    "cached_input_tokens": 6_276_352,
    "output_tokens": 28_180,
    "reasoning_tokens": 11_521,
}


def _stamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _token_record(at: datetime, row: dict[str, int]) -> dict:
    return {
        "timestamp": _stamp(at),
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "info": {
                "total_token_usage": {
                    "input_tokens": row["raw_input_tokens"],
                    "cached_input_tokens": row["cached_input_tokens"],
                    "cache_write_input_tokens": row.get("cache_write_input_tokens", 0),
                    "output_tokens": row["output_tokens"],
                    "reasoning_output_tokens": row["reasoning_tokens"],
                    "total_tokens": row["raw_input_tokens"] + row["output_tokens"],
                },
                "last_token_usage": {
                    "input_tokens": row["prompt_tokens"],
                    "cached_input_tokens": row.get("last_cached_input_tokens", 0),
                    "cache_write_input_tokens": row.get("last_cache_write_input_tokens", 0),
                },
                "model_context_window": row.get("model_context_window", 258_400),
            },
        },
    }


def _write_records(path: Path, records: list[dict], *, append: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _session_file(
    sessions: Path,
    session_id: str,
    root: Path,
    task_id: str,
    *,
    cwd: Path | None = None,
    rows: list[dict[str, int]] | None = None,
    logical_session_id: str | None = None,
    thread_source: str = "user",
    forked_from_id: str | None = None,
    session_day: str = "11",
    started_at: datetime | None = None,
) -> Path:
    started = started_at or datetime.now(timezone.utc) - timedelta(seconds=1)
    path = sessions / "2026" / "08" / session_day / f"rollout-2026-08-{session_day}T00-00-00-{session_id}.jsonl"
    metadata = {
        "id": session_id,
        "session_id": logical_session_id or session_id,
        "timestamp": _stamp(started),
        "cwd": str(cwd or root),
        "originator": "Codex Desktop",
        "thread_source": thread_source,
        "source": "vscode",
    }
    if forked_from_id is not None:
        metadata["forked_from_id"] = forked_from_id
    records = [
        {
            "timestamp": _stamp(started),
            "type": "session_meta",
            "payload": metadata,
        },
        {
            "timestamp": _stamp(started + timedelta(milliseconds=100)),
            "type": "event_msg",
            "payload": {"type": "task_started", "turn_id": f"turn-{session_id}"},
        },
        {
            "timestamp": _stamp(started + timedelta(milliseconds=200)),
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call",
                "name": "exec",
                "input": (
                    f"tools.shell_command({{command: 'python ai.py --root \\\"{root}\\\" "
                    f"bootstrap --task-id {task_id}', workdir: '\"{root}\"'}})"
                ),
            },
        },
    ]
    for index, row in enumerate(rows or [], 1):
        records.append(_token_record(started + timedelta(milliseconds=200 + index), row))
    _write_records(path, records)
    return path


def _append_rows(path: Path, rows: list[dict[str, int]]) -> None:
    base = datetime.now(timezone.utc)
    _write_records(path, [_token_record(base + timedelta(milliseconds=index), row) for index, row in enumerate(rows)], append=True)


def _distribute(total: int, count: int) -> list[int]:
    quotient, remainder = divmod(total, count)
    return [quotient + (1 if index < remainder else 0) for index in range(count)]


def _cumulative_rows(
    start: dict[str, int],
    target: dict[str, int],
    count: int,
    *,
    final_prompt: int | None = None,
) -> list[dict[str, int]]:
    increments: dict[str, list[int]] = {}
    for field in FIELD_TOTAL:
        delta = target[field] - start[field]
        if field == "raw_input_tokens" and final_prompt is not None:
            increments[field] = [*_distribute(delta - final_prompt, count - 1), final_prompt]
        else:
            increments[field] = _distribute(delta, count)
    current = dict(start)
    result = []
    for index in range(count):
        for field in FIELD_TOTAL:
            current[field] += increments[field][index]
        result.append({**current, "prompt_tokens": increments["raw_input_tokens"][index]})
    return result


class UsageAppender:
    def __init__(self, path: Path, start: dict[str, int] | None = None):
        self.path = path
        self.current = dict(start or {
            "raw_input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0,
        })

    def add(self, prompt: int, *, cached: int | None = None, output: int = 10, reasoning: int = 4) -> None:
        self.current["raw_input_tokens"] += prompt
        self.current["cached_input_tokens"] += cached if cached is not None else max(0, prompt - 100)
        self.current["output_tokens"] += output
        self.current["reasoning_tokens"] += reasoning
        _append_rows(self.path, [{**self.current, "prompt_tokens": prompt}])


@contextmanager
def desktop_environment(sessions: Path, *, thread_id: str = "", override: Path | None = None):
    values = {
        "BUILDOS_TELEMETRY_FILE": "",
        "AI_BUILD_OS_CODEX_APP_SERVER_USAGE_FILE": "",
        "AI_BUILD_OS_USAGE_FILE": "",
        "BUILDOS_THREAD_ID": "",
        "AI_BUILD_OS_CODEX_THREAD_ID": "",
        "BUILDOS_CODEX_SESSIONS_DIR": str(sessions),
        "BUILDOS_CODEX_DESKTOP_SESSION_FILE": str(override) if override else "",
        "CODEX_THREAD_ID": thread_id,
    }
    with patch.dict(os.environ, values, clear=False):
        yield


@contextmanager
def generic_worktree_pair(name: str):
    with tempfile.TemporaryDirectory(prefix=f"buildos-{name}-") as td:
        container = Path(td)
        root = container / "primary"
        other = container / "other-worktree"
        root.mkdir()
        run_git(root, "init", "-q")
        run_git(root, "config", "user.email", "generic@example.invalid")
        run_git(root, "config", "user.name", "Generic Fixture")
        (root / "app.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
        (root / "README.md").write_text("# Unrelated calculator fixture\n", encoding="utf-8")
        run_git(root, "add", "app.py", "README.md")
        run_git(root, "commit", "-qm", "generic baseline")
        run_git(root, "worktree", "add", "-q", "-b", f"fixture-{name}", str(other))
        yield root, other


class DesktopBindingTests(unittest.TestCase):
    def test_legacy_app_server_unique_thread_ignores_unrelated_desktop_identity(self):
        def notification(turn: int, total_input: int) -> dict:
            return {
                "method": "thread/tokenUsage/updated",
                "params": {
                    "threadId": "legacy-thread",
                    "turnId": f"turn-{turn}",
                    "tokenUsage": {
                        "total": {
                            "inputTokens": total_input,
                            "cachedInputTokens": total_input // 2,
                            "outputTokens": turn * 10,
                        },
                        "last": {"inputTokens": 1_000 + turn},
                    },
                },
            }

        with generic_repo("legacy-app-server") as root:
            source = root / ".buildos" / "runtime" / "legacy-source.jsonl"
            source.parent.mkdir(parents=True, exist_ok=True)
            _write_records(source, [notification(1, 1_000)])
            env = {
                "BUILDOS_TELEMETRY_FILE": "",
                "AI_BUILD_OS_CODEX_APP_SERVER_USAGE_FILE": str(source),
                "AI_BUILD_OS_USAGE_FILE": "",
                "BUILDOS_THREAD_ID": "",
                "AI_BUILD_OS_CODEX_THREAD_ID": "",
                # Codex Desktop always exports its own physical identity. It
                # must not turn the legacy source's unique thread into zero
                # records when no legacy filter was explicitly configured.
                "CODEX_THREAD_ID": "unrelated-desktop-stream",
            }
            with patch.dict(os.environ, env, clear=False):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                _write_records(source, [notification(2, 2_000)], append=True)
                status = osys.status()
                self.assertEqual(status["telemetry"]["adapter"], "CODEX_APP_SERVER")
                self.assertEqual(status["telemetry"]["current_epoch_model_requests"], 1)
                self.assertEqual(status["telemetry"]["productive_raw_input_tokens"], 1_000)

    def test_unique_repository_session_binds_and_persisted_binding_cannot_be_hijacked(self):
        with generic_repo("desktop-unique") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            selected_id = "00000000-0000-0000-0000-000000000001"
            source = _session_file(sessions, selected_id, root, "GENERIC-LOW")
            unrelated = Path(td) / "unrelated-repository"
            _session_file(
                sessions,
                "00000000-0000-0000-0000-000000000002",
                unrelated,
                "OTHER-TASK",
                cwd=unrelated,
            )
            with desktop_environment(sessions):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                first = osys.status()
                self.assertEqual(first["telemetry"]["binding_status"], "BOUND")
                self.assertEqual(first["telemetry"]["telemetry_binding"]["session_id"], selected_id)
                # A later equally plausible file cannot replace the immutable
                # Task/Revision/Epoch selection.
                _session_file(
                    sessions,
                    "00000000-0000-0000-0000-000000000003",
                    root,
                    "GENERIC-LOW",
                )
                appender = UsageAppender(source)
                appender.add(2_000)
                second = osys.status()
                self.assertEqual(second["telemetry"]["telemetry_binding"]["session_id"], selected_id)
                self.assertEqual(second["telemetry"]["productive_model_requests"], 1)
                self.assertEqual(len(list((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))), 1)

    def test_two_plausible_sessions_fail_safely_as_ambiguous(self):
        with generic_repo("desktop-ambiguous") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            for suffix in ("11", "12"):
                _session_file(
                    sessions,
                    f"00000000-0000-0000-0000-0000000000{suffix}",
                    root,
                    "GENERIC-LOW",
                )
            with desktop_environment(sessions):
                osys = BuildOS(root, package_root=PACKAGE)
                started = osys.bootstrap(request()).snapshot
                status = osys.status()
                self.assertEqual(status["telemetry"]["status"], "ADAPTER_BLOCKED")
                self.assertEqual(status["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(status["telemetry"]["binding_reason"], "AMBIGUOUS")
                self.assertEqual(read_current(root).generation_hash, started.generation_hash)
                directory = root / ".buildos/runtime/telemetry_bindings"
                self.assertEqual(list(directory.glob("*.json")) if directory.exists() else [], [])

    def test_explicit_valid_file_override_resolves_ambiguity(self):
        with generic_repo("desktop-override") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            requested_id = "00000000-0000-0000-0000-000000000021"
            requested = _session_file(sessions, requested_id, root, "GENERIC-LOW")
            _session_file(sessions, "00000000-0000-0000-0000-000000000022", root, "GENERIC-LOW")
            with desktop_environment(sessions, override=requested):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                status = osys.status()
                self.assertEqual(status["telemetry"]["binding_status"], "BOUND")
                self.assertEqual(status["telemetry"]["binding_reason"], "PERSISTED")
                self.assertEqual(status["telemetry"]["telemetry_binding"]["session_id"], requested_id)

    def test_desktop_updates_drive_every_governor_boundary(self):
        with generic_repo("desktop-prompts") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            session_id = "00000000-0000-0000-0000-000000000031"
            source = _session_file(sessions, session_id, root, "GENERIC-LOW")
            with desktop_environment(sessions, thread_id=session_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                usage = UsageAppender(source)
                usage.add(129_199)
                self.assertEqual(osys.status()["governor"]["action"], "CONTINUE")
                usage.add(129_200)
                warning = osys.status()
                self.assertEqual(warning["governor"]["action"], "HEADROOM_WARNING")
                self.assertNotIn("compact active context", warning["next_action"])
                usage.add(180_880)
                compact = osys.status()
                self.assertEqual(compact["governor"]["action"], "COMPACT_REQUIRED")
                self.assertIn("continue this outcome/chat", compact["next_action"])
                usage.add(206_720)
                self.assertEqual(osys.status()["governor"]["action"], "COMPACT_REQUIRED")
                rare = osys.status(usage={
                    "compaction_status": "ATTEMPTED_INEFFECTIVE",
                    "compaction_evidence": "desktop/compact-attempt",
                })
                self.assertEqual(rare["governor"]["action"], "ROLLOVER_REQUIRED")
                usage.add(232_560)
                self.assertEqual(osys.status()["governor"]["action"], "HARD_STOP")

        with generic_repo("desktop-requests") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            session_id = "00000000-0000-0000-0000-000000000032"
            source = _session_file(sessions, session_id, root, "GENERIC-LOW")
            with desktop_environment(sessions, thread_id=session_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                usage = UsageAppender(source)
                for _ in range(4):
                    usage.add(1_000)
                self.assertEqual(osys.status()["governor"]["action"], "CONTINUE")
                usage.add(1_000)
                status = osys.status()
                self.assertEqual(status["telemetry"]["current_epoch_model_requests"], 5)
                self.assertEqual(status["governor"]["action"], "CONTINUE")
                self.assertEqual(status["governor"]["request_count_role"], "OBSERVATIONAL_ONLY")

    def test_prebinding_prompt_is_baselined_and_duplicate_rows_are_not_requests(self):
        with generic_repo("desktop-baseline") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            session_id = "00000000-0000-0000-0000-000000000041"
            initial = {
                "raw_input_tokens": 144_000,
                "cached_input_tokens": 140_000,
                "output_tokens": 20,
                "reasoning_tokens": 8,
                "prompt_tokens": 144_000,
            }
            deceptive_replay = {**initial, "prompt_tokens": 1}
            source = _session_file(
                sessions, session_id, root, "GENERIC-LOW", rows=[initial, deceptive_replay]
            )
            before_binding = inspect_desktop_session(source, root=root, task_id="GENERIC-LOW")
            self.assertEqual(before_binding["token_events"], 1)
            self.assertEqual(before_binding["usage"]["projected_prompt_tokens"], 144_000)
            with desktop_environment(sessions, thread_id=session_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                UsageAppender(source, {key: initial[key] for key in FIELD_TOTAL}).add(39_999)
                status = osys.status()
                self.assertEqual(status["telemetry"]["current_epoch_model_requests"], 1)
                self.assertEqual(status["governor"]["projected_prompt_tokens"], 39_999)
                self.assertEqual(status["governor"]["action"], "CONTINUE")

    def test_desktop_compaction_zero_signal_rebaselines_latest_and_preserves_peak(self):
        with generic_repo("desktop-compaction") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            session_id = "00000000-0000-0000-0000-000000000042"
            source = _session_file(sessions, session_id, root, "GENERIC-LOW")
            high = {
                "raw_input_tokens": 185_000,
                "cached_input_tokens": 180_000,
                "cache_write_input_tokens": 7,
                "output_tokens": 20,
                "reasoning_tokens": 8,
                "prompt_tokens": 185_000,
            }
            zero = {**high, "prompt_tokens": 0}
            compacted_at = datetime.now(timezone.utc)
            with desktop_environment(sessions, thread_id=session_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                _write_records(source, [
                    _token_record(compacted_at, high),
                    {
                        "timestamp": _stamp(compacted_at + timedelta(milliseconds=1)),
                        "type": "compacted",
                        "payload": {
                            "message": "opaque compacted history",
                            "replacement_history": [],
                            "window_number": 2,
                            "first_window_id": "window-1",
                            "previous_window_id": "window-1",
                            "window_id": "window-2",
                        },
                    },
                    _token_record(compacted_at + timedelta(milliseconds=2), zero),
                    {
                        "timestamp": _stamp(compacted_at + timedelta(milliseconds=3)),
                        "type": "event_msg",
                        "payload": {"type": "context_compacted"},
                    },
                ], append=True)
                compacted = osys.status()
                self.assertEqual(compacted["telemetry"]["current_epoch_model_requests"], 1)
                self.assertEqual(compacted["telemetry"]["current_epoch_latest_projected_prompt_tokens"], 0)
                self.assertEqual(compacted["telemetry"]["current_epoch_max_projected_prompt_tokens"], 185_000)
                self.assertEqual(compacted["governor"]["action"], "CONTINUE")

                after = {
                    "raw_input_tokens": 238_000,
                    "cached_input_tokens": 232_000,
                    "cache_write_input_tokens": 12,
                    "output_tokens": 30,
                    "reasoning_tokens": 12,
                    "prompt_tokens": 53_000,
                }
                _append_rows(source, [after])
                status = osys.status()
                self.assertEqual(status["telemetry"]["current_epoch_model_requests"], 2)
                self.assertEqual(status["telemetry"]["current_epoch_latest_projected_prompt_tokens"], 53_000)
                self.assertEqual(status["telemetry"]["current_epoch_max_projected_prompt_tokens"], 185_000)
                self.assertEqual(status["telemetry"]["productive_cache_write_input_tokens"], 12)
                self.assertEqual(status["governor"]["projected_prompt_tokens"], 53_000)
                self.assertEqual(status["governor"]["peak_prompt_tokens"], 185_000)
                self.assertEqual(status["governor"]["action"], "CONTINUE")

            inspected = inspect_desktop_session(source, root=root, task_id="GENERIC-LOW")
            self.assertEqual(inspected["token_events"], 2)
            self.assertEqual(inspected["compaction_events"], 1)
            self.assertEqual(inspected["context_compacted_events"], 1)
            self.assertEqual(inspected["compaction_zero_events"], 1)
            self.assertEqual(inspected["usage"]["projected_prompt_tokens"], 53_000)
            self.assertEqual(inspected["usage"]["peak_prompt_tokens"], 185_000)
            self.assertEqual(inspected["usage"]["model_context_window"], 258_400)

            missing_cache = _token_record(datetime.now(timezone.utc) + timedelta(milliseconds=10), {
                "raw_input_tokens": 292_000,
                "cached_input_tokens": 0,
                "cache_write_input_tokens": 0,
                "output_tokens": 40,
                "reasoning_tokens": 16,
                "prompt_tokens": 54_000,
            })
            del missing_cache["payload"]["info"]["total_token_usage"]["cached_input_tokens"]
            del missing_cache["payload"]["info"]["total_token_usage"]["cache_write_input_tokens"]
            _write_records(source, [missing_cache], append=True)
            advisory_missing = inspect_desktop_session(source, root=root, task_id="GENERIC-LOW")
            self.assertEqual(advisory_missing["token_events"], 3)
            self.assertEqual(advisory_missing["usage"]["projected_prompt_tokens"], 54_000)
            self.assertFalse(advisory_missing["usage"]["cached_input_tokens_measured"])
            self.assertFalse(advisory_missing["usage"]["cache_write_input_tokens_measured"])
            with desktop_environment(sessions, thread_id=session_id):
                missing_status = osys.status()
            self.assertEqual(missing_status["governor"]["action"], "CONTINUE")
            self.assertIsNone(missing_status["governor"]["cache_economics"]["cached_input_tokens"])
            self.assertIsNone(missing_status["governor"]["cache_economics"]["noncached_input_tokens"])
            self.assertIsNone(missing_status["governor"]["cache_economics"]["cache_write_input_tokens"])

    def test_subagent_stream_is_not_auto_bound_and_partial_live_tail_is_tolerated(self):
        with generic_repo("desktop-subagent") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            stream_id = "00000000-0000-0000-0000-000000000045"
            _session_file(
                sessions,
                stream_id,
                root,
                "GENERIC-LOW",
                thread_source="subagent",
                forked_from_id="00000000-0000-0000-0000-000000000099",
            )
            with desktop_environment(sessions, thread_id=stream_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                status = osys.status()
                self.assertEqual(status["telemetry"]["status"], "UNMEASURED")
                self.assertEqual(status["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(status["telemetry"]["binding_reason"], "NOT_ASSOCIATED")
                inspected = inspect_desktop_session(
                    next(sessions.rglob(f"*{stream_id}*.jsonl")),
                    root=root,
                    task_id="GENERIC-LOW",
                )
                self.assertTrue(inspected["self_owned_stream"])
                self.assertFalse(inspected["eligible_user_stream"])

        with generic_repo("desktop-partial-tail") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            stream_id = "00000000-0000-0000-0000-000000000046"
            source = _session_file(sessions, stream_id, root, "GENERIC-LOW")
            with desktop_environment(sessions, thread_id=stream_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                UsageAppender(source).add(2_000)
                with source.open("a", encoding="utf-8", newline="") as handle:
                    handle.write('{"timestamp":')
                status = osys.status()
                self.assertEqual(status["telemetry"]["productive_model_requests"], 1)
                self.assertEqual(status["telemetry"]["adapter_warnings"], ["partial Desktop telemetry tail ignored"])

    def test_replayed_historical_task_mentions_cannot_prove_current_association(self):
        with generic_repo("desktop-replayed-association") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            unrelated = Path(td) / "unrelated-current-work"
            session_id = "00000000-0000-0000-0000-000000000044"
            source = _session_file(sessions, session_id, unrelated, "OTHER-TASK", cwd=unrelated)
            records = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
            records.insert(1, {
                "timestamp": _stamp(datetime.now(timezone.utc) - timedelta(seconds=2)),
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "content": [{"type": "input_text", "text": f"old task GENERIC-LOW in {root}"}],
                },
            })
            _write_records(source, records)
            with desktop_environment(sessions, thread_id=session_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                status = osys.status()
                self.assertEqual(status["telemetry"]["status"], "UNMEASURED")
                self.assertEqual(status["telemetry"]["binding_reason"], "NOT_ASSOCIATED")
                binding_dir = root / ".buildos/runtime/telemetry_bindings"
                self.assertEqual(list(binding_dir.glob("*.json")) if binding_dir.exists() else [], [])

    def test_stream_identity_is_strict_and_replayed_session_metadata_keeps_first_header(self):
        with tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            root = Path(td) / "repo"
            stream_id = "00000000-0000-0000-0000-000000000047"
            source = _session_file(sessions, stream_id, root, "STRICT-ID")
            records = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
            replay = {
                "timestamp": _stamp(datetime.now(timezone.utc)),
                "type": "session_meta",
                "payload": {
                    "id": "00000000-0000-0000-0000-000000000098",
                    "session_id": "00000000-0000-0000-0000-000000000098",
                    "timestamp": _stamp(datetime.now(timezone.utc)),
                    "cwd": str(Path(td) / "ancestor"),
                    "originator": "Codex Desktop",
                    "thread_source": "user",
                },
            }
            records.insert(1, replay)
            _write_records(source, records)
            inspected = inspect_desktop_session(source, root=root, task_id="STRICT-ID")
            self.assertEqual(inspected["session_id"], stream_id)
            self.assertTrue(inspected["eligible_user_stream"])

            missing_id = [dict(item) for item in records]
            missing_id[0] = {**missing_id[0], "payload": dict(missing_id[0]["payload"])}
            del missing_id[0]["payload"]["id"]
            _write_records(source, missing_id)
            with self.assertRaisesRegex(ValueError, "requires valid id and session_id"):
                inspect_desktop_session(source)

            missing_session_id = [dict(item) for item in records]
            missing_session_id[0] = {**missing_session_id[0], "payload": dict(missing_session_id[0]["payload"])}
            del missing_session_id[0]["payload"]["session_id"]
            _write_records(source, missing_session_id)
            with self.assertRaisesRegex(ValueError, "requires valid id and session_id"):
                inspect_desktop_session(source)

            _write_records(source, records)
            wrong_name = source.with_name(source.stem + "-extra.jsonl")
            _write_records(wrong_name, records)
            with self.assertRaisesRegex(ValueError, "rollout filename"):
                inspect_desktop_session(wrong_name)

    def test_persisted_binding_detects_corruption_and_header_replacement(self):
        with generic_repo("desktop-binding-corrupt") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            stream_id = "00000000-0000-0000-0000-000000000048"
            _session_file(sessions, stream_id, root, "GENERIC-LOW")
            with desktop_environment(sessions, thread_id=stream_id):
                osys = BuildOS(root, package_root=PACKAGE)
                started = osys.bootstrap(request()).snapshot
                binding = next((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))
                binding.write_text("{corrupt-binding}\n", encoding="utf-8")
                status = osys.status()
                self.assertEqual(status["telemetry"]["status"], "ADAPTER_BLOCKED")
                self.assertEqual(read_current(root).generation_hash, started.generation_hash)

        with generic_repo("desktop-header-replaced") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            stream_id = "00000000-0000-0000-0000-000000000049"
            source = _session_file(sessions, stream_id, root, "GENERIC-LOW")
            with desktop_environment(sessions, thread_id=stream_id):
                osys = BuildOS(root, package_root=PACKAGE)
                started = osys.bootstrap(request()).snapshot
                records = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
                records[0]["payload"]["timestamp"] = "2026-08-11T12:00:00.000Z"
                _write_records(source, records)
                status = osys.status()
                self.assertEqual(status["telemetry"]["status"], "ADAPTER_BLOCKED")
                self.assertEqual(status["telemetry"]["binding_status"], "BOUND")
                self.assertIn("header identity changed", status["telemetry"]["adapter_failures"][0])
                self.assertEqual(read_current(root).generation_hash, started.generation_hash)

    def test_concurrent_binding_publication_has_one_immutable_winner(self):
        with generic_repo("desktop-binding-race") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            with desktop_environment(sessions):
                osys = BuildOS(root, package_root=PACKAGE)
                state = osys.bootstrap(request()).snapshot.state
            inspected = []
            for suffix in ("71", "72"):
                source = _session_file(
                    sessions,
                    f"00000000-0000-0000-0000-0000000000{suffix}",
                    root,
                    "GENERIC-LOW",
                )
                inspected.append(inspect_desktop_session(source, root=root, task_id="GENERIC-LOW"))
            barrier = Barrier(2)

            def publish(item: dict) -> dict:
                barrier.wait(timeout=10)
                return _persist_binding(root, state, item)

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = [future.result(timeout=30) for future in [pool.submit(publish, item) for item in inspected]]
            self.assertEqual(results[0]["session_id"], results[1]["session_id"])
            bindings = list((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))
            self.assertEqual(len(bindings), 1)
            self.assertEqual(json.loads(bindings[0].read_text(encoding="utf-8"))["session_id"], results[0]["session_id"])

    def test_rollover_rebinds_new_session_without_merging_epoch_counters(self):
        with generic_repo("desktop-rollover") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            first_id = "00000000-0000-0000-0000-000000000051"
            second_id = "00000000-0000-0000-0000-000000000052"
            unrelated_id = "00000000-0000-0000-0000-000000000053"
            first_source = _session_file(sessions, first_id, root, "GENERIC-LOW")
            # Desktop forks the continuation before that continuation invokes
            # the lifecycle rollover. Its header cwd is the shared workspace,
            # while its current turn names the exact task worktree.
            second_source = _session_file(
                sessions,
                second_id,
                root,
                "GENERIC-LOW",
                cwd=root.parent,
                thread_source="subagent",
                forked_from_id=first_id,
            )
            _session_file(sessions, unrelated_id, root, "GENERIC-LOW")
            with desktop_environment(sessions, thread_id=first_id):
                osys = BuildOS(root, package_root=PACKAGE)
                first = osys.bootstrap(request()).snapshot
                first_usage = UsageAppender(first_source)
                for _ in range(5):
                    first_usage.add(1_000)
                self.assertEqual(osys.status()["governor"]["action"], "CONTINUE")
                with self.assertRaisesRegex(KernelError, "rollover requires a governor signal"):
                    osys.rollover(thread_id=first_id)
                self.assertEqual(read_current(root).state["context"]["epoch"], 1)

            with desktop_environment(sessions, thread_id=second_id):
                rolled = osys.rollover(force=True, thread_id=second_id).snapshot
                self.assertEqual((rolled.state["task_id"], rolled.state["revision"]), (first.state["task_id"], first.state["revision"]))
                self.assertEqual(rolled.state["context"]["epoch"], 2)
                self.assertNotEqual(rolled.state["context"]["epoch_id"], first.state["context"]["epoch_id"])
                self.assertEqual(rolled.state["context"]["thread_id"], second_id)
                projected = json.loads((root / ".buildos/runtime/WORK_PACKET.json").read_text(encoding="utf-8"))
                self.assertEqual(projected["thread_id"], second_id)
                self.assertEqual(projected["telemetry_binding_status"], "BOUND")
                self.assertEqual(projected["telemetry_binding_reason"], "ROLLOVER_HANDOFF")
                rebound = osys.status()
                self.assertEqual(rebound["telemetry"]["binding_status"], "BOUND")
                self.assertEqual(rebound["telemetry"]["binding_reason"], "PERSISTED")
                self.assertEqual(rebound["telemetry"]["telemetry_binding"]["session_id"], second_id)
                self.assertEqual(rebound["telemetry"]["telemetry_binding"]["association"], "ROLLOVER_HANDOFF")
                self.assertEqual(rebound["telemetry"]["telemetry_binding"]["parent_session_id"], first_id)
                self.assertEqual(rebound["telemetry"]["current_epoch_model_requests"], 0)
                with desktop_environment(sessions, thread_id=unrelated_id):
                    unrelated_after_binding = osys.status()
                    self.assertEqual(unrelated_after_binding["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                    self.assertEqual(unrelated_after_binding["telemetry"]["binding_reason"], "NOT_EXPECTED_CONTINUATION")
                    self.assertEqual(unrelated_after_binding["governor"]["measurement"], "UNMEASURED")
                    self.assertEqual(unrelated_after_binding["next_action"], "stop model work; restore the expected rollover telemetry binding")
                with desktop_environment(sessions, thread_id=first_id):
                    stale_after_binding = osys.status()
                    self.assertEqual(stale_after_binding["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                    self.assertEqual(stale_after_binding["telemetry"]["binding_reason"], "PREVIOUS_EPOCH_SESSION")
                    self.assertEqual(stale_after_binding["governor"]["measurement"], "UNMEASURED")
                    self.assertEqual(stale_after_binding["next_action"], "stop model work; restore the expected rollover telemetry binding")
                second_usage = UsageAppender(second_source)
                second_usage.add(2_000)
                status = osys.status()
                self.assertEqual(status["telemetry"]["telemetry_binding"]["session_id"], second_id)
                self.assertEqual(status["telemetry"]["current_epoch_model_requests"], 1)
                self.assertEqual(status["telemetry"]["productive_model_requests"], 6)
                self.assertEqual(status["governor"]["action"], "CONTINUE")
                bindings = list((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))
                self.assertEqual(len(bindings), 2)
                epoch_two = next(
                    path for path in bindings
                    if json.loads(path.read_text(encoding="utf-8"))["epoch"] == 2
                )
                before_retry = epoch_two.read_bytes()
                retried = osys.status()
                self.assertEqual(retried["telemetry"]["binding_reason"], "PERSISTED")
                self.assertEqual(retried["telemetry"]["current_epoch_model_requests"], 1)
                self.assertEqual(epoch_two.read_bytes(), before_retry)
                for _ in range(3):
                    second_usage.add(2_000)
                self.assertEqual(osys.status()["governor"]["action"], "CONTINUE")
                second_usage.add(2_000)
                epoch_limit = osys.status()
                self.assertEqual(epoch_limit["telemetry"]["current_epoch_model_requests"], 5)
                self.assertEqual(epoch_limit["governor"]["action"], "CONTINUE")
                self.assertEqual(epoch_limit["governor"]["request_count_role"], "OBSERVATIONAL_ONLY")
                second_source.unlink()
                source_missing = osys.status()
                self.assertEqual(source_missing["telemetry"]["binding_status"], "BOUND")
                self.assertEqual(source_missing["telemetry"]["binding_reason"], "SOURCE_UNAVAILABLE")
                self.assertEqual(source_missing["telemetry"]["current_epoch_measurement"], "UNMEASURED")
                self.assertEqual(source_missing["telemetry"]["current_epoch_requests_measurement"], "UNMEASURED")
                self.assertEqual(source_missing["governor"]["measurement"], "UNMEASURED")
                self.assertEqual(source_missing["governor"]["action"], "CONTINUE_UNMEASURED")
                self.assertEqual(source_missing["next_action"], "stop model work; restore the expected rollover telemetry binding")
                self.assertEqual(source_missing["work_packet"]["telemetry_availability"], "UNMEASURED")

    def test_rollover_rejects_unrelated_caller_and_different_repository(self):
        with generic_repo("desktop-rollover-unrelated") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            unrelated = sessions / "unrelated-repository"
            first_id = "00000000-0000-0000-0000-000000000081"
            expected_id = "00000000-0000-0000-0000-000000000082"
            unrelated_id = "00000000-0000-0000-0000-000000000083"
            _session_file(sessions, first_id, root, "GENERIC-LOW")
            # Even possession of the expected physical ID and parent ID is
            # insufficient when the current-turn repository evidence is for
            # another repository.
            _session_file(
                sessions,
                expected_id,
                unrelated,
                "GENERIC-LOW",
                cwd=unrelated,
                thread_source="subagent",
                forked_from_id=first_id,
            )
            _session_file(sessions, unrelated_id, unrelated, "GENERIC-LOW", cwd=unrelated)
            with desktop_environment(sessions, thread_id=first_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
            with desktop_environment(sessions, thread_id=expected_id):
                rolled = osys.rollover(force=True, thread_id=expected_id).snapshot

            with desktop_environment(sessions, thread_id=unrelated_id):
                unrelated_status = osys.status()
                self.assertEqual(unrelated_status["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(unrelated_status["telemetry"]["binding_reason"], "NOT_EXPECTED_CONTINUATION")

            with desktop_environment(sessions, thread_id=expected_id):
                wrong_repository = osys.status()
                self.assertEqual(wrong_repository["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(wrong_repository["telemetry"]["binding_reason"], "NOT_ASSOCIATED")
                self.assertEqual(wrong_repository["next_action"], "stop model work; restore the expected rollover telemetry binding")

            self.assertEqual(read_current(root).generation_hash, rolled.generation_hash)
            self.assertEqual(len(list((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))), 1)

    def test_rollover_rejects_same_task_from_a_different_git_worktree(self):
        with generic_worktree_pair("rollover-worktree") as (root, other), tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            first_id = "00000000-0000-0000-0000-000000000084"
            expected_id = "00000000-0000-0000-0000-000000000085"
            _session_file(sessions, first_id, root, "GENERIC-LOW")
            _session_file(
                sessions,
                expected_id,
                other,
                "GENERIC-LOW",
                cwd=other,
                thread_source="subagent",
                forked_from_id=first_id,
            )
            self.assertNotEqual(
                Path(run_git(root, "rev-parse", "--show-toplevel")).resolve(),
                Path(run_git(other, "rev-parse", "--show-toplevel")).resolve(),
            )
            with desktop_environment(sessions, thread_id=first_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
            with desktop_environment(sessions, thread_id=expected_id):
                rolled = osys.rollover(force=True, thread_id=expected_id).snapshot
            with desktop_environment(sessions, thread_id=expected_id):
                status = osys.status()
                self.assertEqual(status["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(status["telemetry"]["binding_reason"], "NOT_ASSOCIATED")
                self.assertEqual(status["next_action"], "stop model work; restore the expected rollover telemetry binding")
            self.assertEqual(read_current(root).generation_hash, rolled.generation_hash)
            self.assertEqual(len(list((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))), 1)

    def test_rollover_rejects_stale_previous_epoch_session(self):
        with generic_repo("desktop-rollover-stale") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            first_id = "00000000-0000-0000-0000-000000000086"
            expected_id = "00000000-0000-0000-0000-000000000087"
            _session_file(sessions, first_id, root, "GENERIC-LOW")
            _session_file(
                sessions,
                expected_id,
                root,
                "GENERIC-LOW",
                cwd=root.parent,
                thread_source="subagent",
                forked_from_id="00000000-0000-0000-0000-000000000080",
            )
            with desktop_environment(sessions, thread_id=first_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
            with desktop_environment(sessions, thread_id=expected_id):
                rolled = osys.rollover(force=True, thread_id=expected_id).snapshot
            with desktop_environment(sessions, thread_id=first_id):
                stale = osys.status()
                self.assertEqual(stale["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(stale["telemetry"]["binding_reason"], "PREVIOUS_EPOCH_SESSION")
                self.assertEqual(stale["telemetry"]["current_epoch_measurement"], "UNMEASURED")
            with desktop_environment(sessions, thread_id=expected_id):
                wrong_parent = osys.status()
                self.assertEqual(wrong_parent["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(wrong_parent["telemetry"]["binding_reason"], "NOT_ASSOCIATED")
                self.assertEqual(wrong_parent["next_action"], "stop model work; restore the expected rollover telemetry binding")
            self.assertEqual(read_current(root).generation_hash, rolled.generation_hash)
            self.assertEqual(len(list((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))), 1)

    def test_rollover_duplicate_exact_continuations_fail_safely_as_ambiguous(self):
        with generic_repo("desktop-rollover-ambiguous") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            first_id = "00000000-0000-0000-0000-000000000088"
            expected_id = "00000000-0000-0000-0000-000000000089"
            _session_file(sessions, first_id, root, "GENERIC-LOW")
            for day in ("11", "12"):
                _session_file(
                    sessions,
                    expected_id,
                    root,
                    "GENERIC-LOW",
                    cwd=root.parent,
                    thread_source="subagent",
                    forked_from_id=first_id,
                    session_day=day,
                )
            with desktop_environment(sessions, thread_id=first_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
            with desktop_environment(sessions, thread_id=expected_id):
                rolled = osys.rollover(force=True, thread_id=expected_id).snapshot
            with desktop_environment(sessions, thread_id=expected_id):
                ambiguous = osys.status()
                self.assertEqual(ambiguous["telemetry"]["status"], "ADAPTER_BLOCKED")
                self.assertEqual(ambiguous["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(ambiguous["telemetry"]["binding_reason"], "AMBIGUOUS")
                self.assertEqual(ambiguous["telemetry"]["telemetry_binding"]["candidates"], [expected_id])
                self.assertEqual(ambiguous["next_action"], "stop model work; restore the expected rollover telemetry binding")
            self.assertEqual(read_current(root).generation_hash, rolled.generation_hash)
            self.assertEqual(len(list((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))), 1)

    def test_rollover_missing_expected_source_is_unmeasured_and_noncorrupting(self):
        with generic_repo("desktop-rollover-missing") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            first_id = "00000000-0000-0000-0000-000000000090"
            missing_id = "00000000-0000-0000-0000-000000000091"
            _session_file(sessions, first_id, root, "GENERIC-LOW")
            with desktop_environment(sessions, thread_id=first_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
            with desktop_environment(sessions, thread_id=missing_id):
                rolled = osys.rollover(force=True, thread_id=missing_id).snapshot
            with desktop_environment(sessions, thread_id=missing_id):
                missing = osys.status()
                self.assertEqual(missing["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(missing["telemetry"]["binding_reason"], "NOT_ASSOCIATED")
                self.assertEqual(missing["telemetry"]["current_epoch_measurement"], "UNMEASURED")
                self.assertEqual(missing["telemetry"]["current_epoch_requests_measurement"], "UNMEASURED")
                self.assertEqual(missing["next_action"], "stop model work; restore the expected rollover telemetry binding")
                self.assertEqual(missing["work_packet"]["telemetry_availability"], "UNMEASURED")
                self.assertEqual(missing["work_packet"]["telemetry_binding_status"], "TELEMETRY_UNBOUND")
                (root / "app.py").write_text("def add(a, b):\n    return a + b + 1\n", encoding="utf-8")
                run_git(root, "add", "app.py")
                run_git(root, "commit", "-qm", "unadopted while telemetry is unbound")
                still_blocked = osys.status()
                self.assertTrue(still_blocked["unadopted_product_commit"])
                self.assertEqual(still_blocked["next_action"], "stop model work; restore the expected rollover telemetry binding")
            self.assertEqual(read_current(root).generation_hash, rolled.generation_hash)
            self.assertEqual(read_current(root).state["context"]["epoch"], 2)
            self.assertEqual(len(list((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))), 1)

    def test_repeated_rollover_for_same_expected_session_is_idempotent(self):
        with generic_repo("desktop-rollover-idempotent") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            first_id = "00000000-0000-0000-0000-000000000092"
            expected_id = "00000000-0000-0000-0000-000000000093"
            third_id = "00000000-0000-0000-0000-000000000102"
            _session_file(sessions, first_id, root, "GENERIC-LOW")
            second_source = _session_file(
                sessions,
                expected_id,
                root,
                "GENERIC-LOW",
                cwd=root.parent,
                thread_source="subagent",
                forked_from_id=first_id,
            )
            _session_file(
                sessions,
                third_id,
                root,
                "GENERIC-LOW",
                cwd=root.parent,
                thread_source="subagent",
                forked_from_id=expected_id,
            )
            with desktop_environment(sessions, thread_id=first_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
            with desktop_environment(sessions, thread_id=expected_id):
                first_rollover = osys.rollover(force=True, thread_id=expected_id)
                retry = osys.rollover(force=True, thread_id=expected_id)
                self.assertFalse(first_rollover.idempotent)
                self.assertTrue(retry.idempotent)
                self.assertEqual(retry.snapshot.generation_hash, first_rollover.snapshot.generation_hash)
                self.assertEqual(retry.snapshot.state["context"]["epoch"], 2)
                rebound = osys.status()
                self.assertEqual(rebound["telemetry"]["binding_reason"], "PERSISTED")
                self.assertEqual(rebound["telemetry"]["telemetry_binding"]["session_id"], expected_id)
                second_usage = UsageAppender(second_source)
                for _ in range(5):
                    second_usage.add(1_000)
                self.assertEqual(osys.status()["governor"]["action"], "CONTINUE")
                with self.assertRaisesRegex(KernelError, "rollover requires a governor signal"):
                    osys.rollover(thread_id="invalid/context")
            with desktop_environment(sessions, thread_id=first_id):
                with self.assertRaisesRegex(KernelError, "rollover requires a governor signal"):
                    osys.rollover(thread_id=first_id)
            with desktop_environment(sessions):
                with self.assertRaisesRegex(KernelError, "rollover requires a governor signal"):
                    osys.rollover(thread_id=first_id)
            self.assertEqual(read_current(root).state["context"]["epoch"], 2)
            self.assertEqual(read_current(root).state["context"]["thread_id"], expected_id)
            with desktop_environment(sessions, thread_id=third_id):
                second_rollover = osys.rollover(force=True, thread_id=third_id)
                self.assertFalse(second_rollover.idempotent)
                self.assertEqual(second_rollover.snapshot.state["context"]["epoch"], 3)
                self.assertEqual(second_rollover.snapshot.state["context"]["thread_id"], third_id)
                third_status = osys.status()
                self.assertEqual(third_status["telemetry"]["binding_status"], "BOUND")
                self.assertEqual(third_status["telemetry"]["telemetry_binding"]["session_id"], third_id)
                self.assertEqual(third_status["telemetry"]["telemetry_binding"]["parent_session_id"], expected_id)
                self.assertEqual(third_status["telemetry"]["current_epoch_model_requests"], 0)
            self.assertEqual(len(list((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))), 3)

    def test_root_user_rollover_binds_only_when_canonical_context_names_its_physical_id(self):
        with generic_repo("desktop-rollover-root-user") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            first_id = "00000000-0000-0000-0000-000000000094"
            second_id = "00000000-0000-0000-0000-000000000095"
            _session_file(sessions, first_id, root, "GENERIC-LOW")
            _session_file(sessions, second_id, root, "GENERIC-LOW")
            with desktop_environment(sessions, thread_id=first_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
            with desktop_environment(sessions, thread_id=second_id):
                rolled = osys.rollover(force=True, thread_id=second_id).snapshot
                status = osys.status()
                self.assertEqual(status["telemetry"]["binding_status"], "BOUND")
                self.assertEqual(status["telemetry"]["telemetry_binding"]["session_id"], second_id)
                self.assertEqual(status["telemetry"]["telemetry_binding"]["association"], "ROOT_USER")
                self.assertEqual(status["work_packet"]["thread_id"], second_id)
            self.assertEqual(read_current(root).generation_hash, rolled.generation_hash)

    def test_legacy_root_binding_with_context_label_and_fork_header_remains_readable(self):
        with generic_repo("desktop-rollover-legacy-binding") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            first_id = "00000000-0000-0000-0000-000000000096"
            second_id = "00000000-0000-0000-0000-000000000097"
            _session_file(sessions, first_id, root, "GENERIC-LOW")
            second_source = _session_file(
                sessions,
                second_id,
                root,
                "GENERIC-LOW",
                forked_from_id=first_id,
            )
            with desktop_environment(sessions, thread_id=first_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                rolled = osys.rollover(force=True, thread_id="legacy-epoch-label").snapshot

            inspected = inspect_desktop_session(second_source, root=root, task_id="GENERIC-LOW")
            _persist_binding(root, rolled.state, inspected)
            epoch_two = next(
                path for path in (root / ".buildos/runtime/telemetry_bindings").glob("*.json")
                if json.loads(path.read_text(encoding="utf-8"))["epoch"] == 2
            )
            with desktop_environment(sessions, thread_id=second_id):
                new_format_mismatch = osys.status()
                self.assertEqual(new_format_mismatch["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(new_format_mismatch["telemetry"]["binding_reason"], "ADAPTER_BLOCKED")
                self.assertIn("not the expected rollover continuation", new_format_mismatch["telemetry"]["adapter_failures"][0])
            legacy = json.loads(epoch_two.read_text(encoding="utf-8"))
            legacy.pop("association")
            legacy.pop("parent_session_id")
            legacy["header_fingerprint"] = _desktop_header_fingerprint(
                inspected,
                include_fork_parent=False,
            )
            epoch_two.write_text(json.dumps(legacy, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

            with desktop_environment(sessions, thread_id=second_id):
                status = osys.status()
                self.assertEqual(status["telemetry"]["binding_status"], "BOUND")
                self.assertEqual(status["telemetry"]["binding_reason"], "PERSISTED")
                self.assertEqual(status["telemetry"]["telemetry_binding"]["session_id"], second_id)
                self.assertEqual(status["telemetry"]["telemetry_binding"]["association"], "ROOT_USER")

    def test_corrupt_handoff_ancestry_blocks_the_next_epoch_without_corrupting_lifecycle(self):
        with generic_repo("desktop-rollover-ancestry") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            first_id = "00000000-0000-0000-0000-000000000098"
            second_id = "00000000-0000-0000-0000-000000000099"
            third_id = "00000000-0000-0000-0000-000000000100"
            _session_file(sessions, first_id, root, "GENERIC-LOW")
            _session_file(
                sessions,
                second_id,
                root,
                "GENERIC-LOW",
                cwd=root.parent,
                thread_source="subagent",
                forked_from_id=first_id,
            )
            with desktop_environment(sessions, thread_id=first_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
            with desktop_environment(sessions, thread_id=second_id):
                osys.rollover(force=True, thread_id=second_id)

            epoch_two = next(
                path for path in (root / ".buildos/runtime/telemetry_bindings").glob("*.json")
                if json.loads(path.read_text(encoding="utf-8"))["epoch"] == 2
            )
            corrupt = json.loads(epoch_two.read_text(encoding="utf-8"))
            corrupt["parent_session_id"] = "00000000-0000-0000-0000-000000000001"
            epoch_two.write_text(json.dumps(corrupt, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

            with desktop_environment(sessions, thread_id=third_id):
                third = osys.rollover(force=True, thread_id=third_id).snapshot
                status = osys.status()
                self.assertEqual(third.state["context"]["epoch"], 3)
                self.assertEqual(read_current(root).generation_hash, third.generation_hash)
                self.assertEqual(status["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(status["telemetry"]["binding_reason"], "ADAPTER_BLOCKED")
                self.assertIn("handoff ancestry is inconsistent", status["telemetry"]["adapter_failures"][0])
                self.assertEqual(status["next_action"], "stop model work; restore the expected rollover telemetry binding")

    def test_invalid_rollover_context_identity_fails_telemetry_closed(self):
        with generic_repo("desktop-rollover-invalid-context") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            first_id = "00000000-0000-0000-0000-000000000101"
            _session_file(sessions, first_id, root, "GENERIC-LOW")
            with desktop_environment(sessions, thread_id=first_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                rolled = osys.rollover(force=True, thread_id="invalid/context").snapshot
                status = osys.status()
                self.assertEqual(rolled.state["context"]["epoch"], 2)
                self.assertEqual(status["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(status["telemetry"]["binding_reason"], "INVALID_EXPECTED_CONTINUATION")
                self.assertEqual(status["next_action"], "stop model work; restore the expected rollover telemetry binding")
                self.assertEqual(read_current(root).generation_hash, rolled.generation_hash)

    def test_corrupt_prior_epoch_binding_blocks_rebinding_without_blocking_rollover(self):
        with generic_repo("desktop-prior-binding-corrupt") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            first_id = "00000000-0000-0000-0000-000000000053"
            _session_file(sessions, first_id, root, "GENERIC-LOW")
            with desktop_environment(sessions, thread_id=first_id):
                osys = BuildOS(root, package_root=PACKAGE)
                first = osys.bootstrap(request()).snapshot
                prior_binding = next((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))
                prior_binding.write_text("{corrupt-binding}\n", encoding="utf-8")
                rolled = osys.rollover(thread_id="fresh-epoch-label", force=True).snapshot
                self.assertEqual((rolled.state["task_id"], rolled.state["revision"]), (first.state["task_id"], first.state["revision"]))
                self.assertEqual(rolled.state["context"]["epoch"], 2)
                status = osys.status()
                self.assertEqual(status["telemetry"]["status"], "ADAPTER_BLOCKED")
                self.assertIn("binding history is unreadable", status["telemetry"]["adapter_failures"][0])
                self.assertEqual(len(list((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))), 1)

    def test_unavailable_or_malformed_desktop_source_never_changes_lifecycle(self):
        with generic_repo("desktop-unavailable") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            with desktop_environment(sessions):
                osys = BuildOS(root, package_root=PACKAGE)
                started = osys.bootstrap(request()).snapshot
                status = osys.status()
                self.assertEqual(status["telemetry"]["status"], "UNMEASURED")
                self.assertEqual(status["telemetry"]["binding_reason"], "UNAVAILABLE")
                self.assertEqual(read_current(root).generation_hash, started.generation_hash)

        with generic_repo("desktop-malformed") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            session_id = "00000000-0000-0000-0000-000000000061"
            source = _session_file(sessions, session_id, root, "GENERIC-LOW")
            with desktop_environment(sessions, thread_id=session_id):
                osys = BuildOS(root, package_root=PACKAGE)
                started = osys.bootstrap(request()).snapshot
                with source.open("a", encoding="utf-8", newline="\n") as handle:
                    handle.write("{malformed-json}\n")
                status = osys.status()
                self.assertEqual(status["telemetry"]["status"], "ADAPTER_BLOCKED")
                self.assertEqual(status["telemetry"]["binding_status"], "BOUND")
                self.assertEqual(read_current(root).generation_hash, started.generation_hash)

    def test_equivalent_field_replay_preserves_baseline_and_exact_counters(self):
        with generic_repo("desktop-field-replay") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            session_id = "019fee0a-b54a-7190-8a6f-d100ddb06a3a"
            zero = {field: 0 for field in FIELD_TOTAL}
            prebootstrap = _cumulative_rows(zero, FIELD_BASELINE, 10)
            source = _session_file(sessions, session_id, root, FIELD_TASK, rows=prebootstrap)
            with desktop_environment(sessions, thread_id=session_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request(FIELD_TASK))
                postbootstrap = _cumulative_rows(FIELD_BASELINE, FIELD_TOTAL, 49, final_prompt=179_884)
                _append_rows(source, postbootstrap)
                status = osys.status()
                telemetry = status["telemetry"]
                self.assertEqual(telemetry["productive_model_requests"], 49)
                self.assertEqual(telemetry["productive_raw_input_tokens"], 6_222_896)
                self.assertEqual(telemetry["productive_cached_input_tokens"], 6_047_488)
                self.assertEqual(telemetry["productive_noncached_input_tokens"], 175_408)
                self.assertEqual(telemetry["productive_output_tokens"], 25_094)
                self.assertEqual(telemetry["productive_reasoning_tokens"], 10_245)
                self.assertEqual(telemetry["current_epoch_latest_projected_prompt_tokens"], 179_884)
                self.assertEqual(telemetry["current_epoch_max_projected_prompt_tokens"], 179_884)
                self.assertEqual(telemetry["current_epoch_model_context_window"], 258_400)
                self.assertEqual(status["governor"]["action"], "HEADROOM_WARNING")
                self.assertEqual(status["governor"]["requests_in_epoch"], 49)
                self.assertEqual(telemetry["control_model_requests"], 0)
                self.assertTrue(osys.record_control_action("status", "PASS"))
                accounted = osys.status()["telemetry"]
                self.assertEqual(accounted["productive_model_requests"], 49)
                self.assertEqual(accounted["control_model_requests"], 0)
                self.assertEqual(accounted["control_tool_actions"], 1)

                raw = inspect_desktop_session(source, root=root, task_id=FIELD_TASK)
                self.assertEqual(raw["token_events"], 59)
                self.assertEqual(raw["usage"]["raw_input_tokens"], 6_483_208)
                self.assertEqual(raw["usage"]["cached_input_tokens"], 6_276_352)
                self.assertEqual(raw["usage"]["output_tokens"], 28_180)
                self.assertEqual(raw["usage"]["reasoning_tokens"], 11_521)
                self.assertEqual(raw["usage"]["projected_prompt_tokens"], 179_884)
                self.assertEqual(raw["usage"]["peak_prompt_tokens"], 179_884)
                self.assertEqual(raw["usage"]["model_context_window"], 258_400)

    @unittest.skipUnless(
        ROLLOVER_FIELD_TRACE.is_file() and ROLLOVER_FIELD_ROOT.is_dir(),
        "failed rollover Desktop field trace is not present",
    )
    def test_failed_rollover_field_trace_would_bind_via_read_only_handoff_proof(self):
        before_trace = (ROLLOVER_FIELD_TRACE.stat().st_size, ROLLOVER_FIELD_TRACE.stat().st_mtime_ns)
        binding_dir = ROLLOVER_FIELD_ROOT / ".buildos" / "runtime" / "telemetry_bindings"
        before_bindings = sorted(path.name for path in binding_dir.glob("*.json")) if binding_dir.is_dir() else []
        inspected = inspect_desktop_session(
            ROLLOVER_FIELD_TRACE,
            root=ROLLOVER_FIELD_ROOT,
            task_id=ROLLOVER_FIELD_TASK,
            expected_session_id=ROLLOVER_FIELD_SESSION,
        )
        self.assertEqual(inspected["thread_source"], "subagent")
        self.assertTrue(inspected["self_owned_stream"])
        self.assertFalse(inspected["eligible_user_stream"])
        self.assertEqual(inspected["forked_from_id"], ROLLOVER_FIELD_PARENT)
        self.assertTrue(inspected["repository_match"])
        self.assertTrue(inspected["task_match"])
        self.assertTrue(inspected["current_turn_repository_match"])
        self.assertTrue(inspected["current_turn_task_match"])

        state = {
            "task_id": ROLLOVER_FIELD_TASK,
            "revision": 1,
            "created_at": "2026-08-11T01:00:58Z",
            "updated_at": "2026-08-11T01:02:46Z",
            "context": {
                "epoch": 2,
                "epoch_id": "epoch-cafbcd8f05594080b76f9e29924fbb37",
                "thread_id": ROLLOVER_FIELD_SESSION,
            },
        }

        def read_only_binding(_root, _state, selected, *, association):
            return {
                "session_id": selected["session_id"],
                "association": association,
                "parent_session_id": selected["forked_from_id"],
            }

        # Discovery, the legacy epoch-one binding, and association run against
        # the real field artifacts. Only publication is replaced, so this
        # proof can never write the interrupted product's runtime.
        with (
            patch("buildos.telemetry._persist_binding", side_effect=read_only_binding) as publish,
            desktop_environment(ROLLOVER_FIELD_SESSIONS, thread_id=ROLLOVER_FIELD_SESSION),
        ):
            discovery = discover_desktop_session(ROLLOVER_FIELD_ROOT, state)

        self.assertEqual(discovery["status"], "BOUND")
        self.assertIn(discovery["reason"], {"ROLLOVER_HANDOFF", "PERSISTED"})
        self.assertEqual(discovery["binding"]["session_id"], ROLLOVER_FIELD_SESSION)
        self.assertEqual(discovery["binding"]["parent_session_id"], ROLLOVER_FIELD_PARENT)
        if discovery["reason"] == "ROLLOVER_HANDOFF":
            self.assertEqual(publish.call_count, 1)
            self.assertEqual(publish.call_args.kwargs["association"], "ROLLOVER_HANDOFF")
        else:
            self.assertEqual(publish.call_count, 0)
        after_bindings = sorted(path.name for path in binding_dir.glob("*.json")) if binding_dir.is_dir() else []
        self.assertEqual(after_bindings, before_bindings)
        self.assertEqual((ROLLOVER_FIELD_TRACE.stat().st_size, ROLLOVER_FIELD_TRACE.stat().st_mtime_ns), before_trace)

    @unittest.skipUnless(FIELD_TRACE.is_file(), "recovered read-only Desktop field trace is not present")
    def test_recovered_field_trace_is_parsed_read_only_with_exact_full_turn_usage(self):
        before = (FIELD_TRACE.stat().st_size, FIELD_TRACE.stat().st_mtime_ns)
        inspected = inspect_desktop_session(FIELD_TRACE, root=FIELD_ROOT, task_id=FIELD_TASK)
        self.assertTrue(inspected["eligible_user_stream"])
        self.assertTrue(inspected["repository_match"])
        self.assertTrue(inspected["task_match"])
        self.assertTrue(inspected["current_turn_repository_match"])
        self.assertTrue(inspected["current_turn_task_match"])
        self.assertEqual(inspected["token_events"], 59)
        self.assertEqual(inspected["usage"]["raw_input_tokens"], 6_483_208)
        self.assertEqual(inspected["usage"]["cached_input_tokens"], 6_276_352)
        self.assertEqual(inspected["usage"]["output_tokens"], 28_180)
        self.assertEqual(inspected["usage"]["reasoning_tokens"], 11_521)
        self.assertEqual(inspected["usage"]["projected_prompt_tokens"], 179_884)
        self.assertEqual(inspected["usage"]["peak_prompt_tokens"], 179_884)
        self.assertEqual(inspected["usage"]["model_context_window"], 258_400)
        replay = decide({
            "projected_prompt_tokens": inspected["usage"]["projected_prompt_tokens"],
            "peak_prompt_tokens": inspected["usage"]["peak_prompt_tokens"],
            "requests_in_epoch": inspected["token_events"],
            "model_context_window": inspected["usage"]["model_context_window"],
        })
        self.assertEqual(replay["requests_in_epoch"], 59)
        self.assertEqual(replay["action"], "HEADROOM_WARNING")
        self.assertEqual((FIELD_TRACE.stat().st_size, FIELD_TRACE.stat().st_mtime_ns), before)

    @unittest.skipUnless(EDITORIAL_FIELD_TRACE.is_file(), "Editorial Desktop field trace is not present")
    def test_editorial_request_twenty_replays_without_request_count_rollover(self):
        before = (EDITORIAL_FIELD_TRACE.stat().st_size, EDITORIAL_FIELD_TRACE.stat().st_mtime_ns)
        inspected = inspect_desktop_session(EDITORIAL_FIELD_TRACE)
        self.assertGreaterEqual(len(inspected["request_prompt_tokens"]), 20)
        prompt = inspected["request_prompt_tokens"][19]
        self.assertEqual(prompt, 95_985)
        replay = decide({
            "projected_prompt_tokens": prompt,
            "peak_prompt_tokens": prompt,
            "requests_in_epoch": 11,
            "model_context_window": 258_400,
        })
        self.assertEqual(replay["action"], "CONTINUE")
        self.assertEqual(replay["request_count_role"], "OBSERVATIONAL_ONLY")
        self.assertEqual((EDITORIAL_FIELD_TRACE.stat().st_size, EDITORIAL_FIELD_TRACE.stat().st_mtime_ns), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
