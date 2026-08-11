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
from buildos.store import read_current
from buildos.telemetry import _persist_binding, inspect_desktop_session
from tests.test_candidate import generic_repo, request


FIELD_TRACE = Path(
    r"C:\Users\ADMIN\.codex\sessions\2026\08\11\rollout-2026-08-11T06-38-27-019fee0a-b54a-7190-8a6f-d100ddb06a3a.jsonl"
)
FIELD_ROOT = Path(r"D:\Youtube\Youtube Studio\_worktrees\advanced-still-camera-motion-v1")
FIELD_TASK = "ADVANCED-STILL-CAMERA-MOTION-V1"
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
                    "output_tokens": row["output_tokens"],
                    "reasoning_output_tokens": row["reasoning_tokens"],
                    "total_tokens": row["raw_input_tokens"] + row["output_tokens"],
                },
                "last_token_usage": {
                    "input_tokens": row["prompt_tokens"],
                },
                "model_context_window": 258_400,
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
) -> Path:
    started = datetime.now(timezone.utc) - timedelta(seconds=1)
    path = sessions / "2026" / "08" / "11" / f"rollout-2026-08-11T00-00-00-{session_id}.jsonl"
    records = [
        {
            "timestamp": _stamp(started),
            "type": "session_meta",
            "payload": {
                "id": session_id,
                "session_id": logical_session_id or session_id,
                "timestamp": _stamp(started),
                "cwd": str(cwd or root),
                "originator": "Codex Desktop",
                "thread_source": thread_source,
                "source": "vscode",
            },
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
                usage.add(39_999)
                self.assertEqual(osys.status()["governor"]["action"], "CONTINUE")
                usage.add(40_000)
                self.assertEqual(osys.status()["governor"]["action"], "PREPARE_COMPACT")
                usage.add(64_000)
                self.assertEqual(osys.status()["governor"]["action"], "ROLLOVER_REQUIRED")
                usage.add(128_000)
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
                self.assertEqual(status["governor"]["action"], "ROLLOVER_REQUIRED")

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
            source = _session_file(sessions, session_id, root, "GENERIC-LOW", rows=[initial, initial])
            with desktop_environment(sessions, thread_id=session_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                UsageAppender(source, {key: initial[key] for key in FIELD_TOTAL}).add(39_999)
                status = osys.status()
                self.assertEqual(status["telemetry"]["current_epoch_model_requests"], 1)
                self.assertEqual(status["governor"]["projected_prompt_tokens"], 39_999)
                self.assertEqual(status["governor"]["action"], "CONTINUE")

    def test_subagent_stream_is_not_auto_bound_and_partial_live_tail_is_tolerated(self):
        with generic_repo("desktop-subagent") as root, tempfile.TemporaryDirectory(prefix="desktop-sessions-") as td:
            sessions = Path(td)
            stream_id = "00000000-0000-0000-0000-000000000045"
            _session_file(
                sessions,
                stream_id,
                root,
                "GENERIC-LOW",
                logical_session_id="00000000-0000-0000-0000-000000000099",
                thread_source="subagent",
            )
            with desktop_environment(sessions, thread_id=stream_id):
                osys = BuildOS(root, package_root=PACKAGE)
                osys.bootstrap(request())
                status = osys.status()
                self.assertEqual(status["telemetry"]["status"], "UNMEASURED")
                self.assertEqual(status["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(status["telemetry"]["binding_reason"], "NOT_ASSOCIATED")

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
            first_source = _session_file(sessions, first_id, root, "GENERIC-LOW")
            with desktop_environment(sessions, thread_id=first_id):
                osys = BuildOS(root, package_root=PACKAGE)
                first = osys.bootstrap(request()).snapshot
                first_usage = UsageAppender(first_source)
                for _ in range(5):
                    first_usage.add(1_000)
                self.assertEqual(osys.status()["governor"]["action"], "ROLLOVER_REQUIRED")

                rolled = osys.rollover(thread_id="epoch-two-label").snapshot
                self.assertEqual((rolled.state["task_id"], rolled.state["revision"]), (first.state["task_id"], first.state["revision"]))
                self.assertEqual(rolled.state["context"]["epoch"], 2)
                self.assertEqual(rolled.state["context"]["thread_id"], "epoch-two-label")
                blocked = osys.status()
                # The prior epoch's measured facts remain visible, while the
                # new epoch is explicitly unbound and cannot reuse its stream.
                self.assertEqual(blocked["telemetry"]["status"], "MEASURED")
                self.assertEqual(blocked["telemetry"]["binding_reason"], "PREVIOUS_EPOCH_SESSION")
                self.assertEqual(blocked["telemetry"]["current_epoch_measurement"], "UNMEASURED")
                self.assertEqual(blocked["telemetry"]["binding_status"], "TELEMETRY_UNBOUND")
                self.assertEqual(len(list((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))), 1)

                second_id = "00000000-0000-0000-0000-000000000052"
                second_source = _session_file(sessions, second_id, root, "GENERIC-LOW")
                with desktop_environment(sessions, thread_id=second_id):
                    rebound = osys.status()
                    self.assertEqual(rebound["telemetry"]["telemetry_binding"]["session_id"], second_id)
                    self.assertEqual(rebound["telemetry"]["current_epoch_model_requests"], 0)
                    UsageAppender(second_source).add(2_000)
                    status = osys.status()
                    self.assertEqual(status["telemetry"]["telemetry_binding"]["session_id"], second_id)
                    self.assertEqual(status["telemetry"]["current_epoch_model_requests"], 1)
                    self.assertEqual(status["telemetry"]["productive_model_requests"], 6)
                    self.assertEqual(status["governor"]["action"], "CONTINUE")
                    self.assertEqual(len(list((root / ".buildos/runtime/telemetry_bindings").glob("*.json"))), 2)

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
                self.assertEqual(telemetry["current_epoch_max_projected_prompt_tokens"], 179_884)
                self.assertEqual(status["governor"]["action"], "HARD_STOP")
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
        self.assertEqual((FIELD_TRACE.stat().st_size, FIELD_TRACE.stat().st_mtime_ns), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
