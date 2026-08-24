"""Optional, task-bound telemetry projection.

Telemetry is deliberately outside canonical lifecycle state.  Adapter failure
returns UNMEASURED/ADAPTER_BLOCKED and can never roll back or corrupt a task.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Iterable, Mapping
import uuid

from .model import canonical_bytes
from .store import (
    RecoveryRequired, atomic_json, atomic_write, publish_immutable,
    safe_repository_descendant,
)


SCHEMA = "buildos.telemetry.v1"
BINDING_SCHEMA = "buildos.telemetry_binding.v1"
DESKTOP_SOURCE = "CODEX_DESKTOP_JSONL"
ROOT_USER_ASSOCIATION = "ROOT_USER"
ROLLOVER_HANDOFF_ASSOCIATION = "ROLLOVER_HANDOFF"
DESKTOP_SESSION_FILE_ENV = "BUILDOS_CODEX_DESKTOP_SESSION_FILE"
DESKTOP_SESSIONS_DIR_ENV = "BUILDOS_CODEX_SESSIONS_DIR"
SESSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
ENV_SOURCES = (
    ("BUILDOS_TELEMETRY_FILE", "NORMALIZED"),
    ("AI_BUILD_OS_CODEX_APP_SERVER_USAGE_FILE", "CODEX_APP_SERVER"),
    ("AI_BUILD_OS_USAGE_FILE", "NORMALIZED"),
)


class TelemetryError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _number(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _desktop_number(value: Any, *, field: str) -> int:
    if isinstance(value, bool):
        raise TelemetryError(f"Codex Desktop {field} must be a non-negative integer")
    try:
        result = int(value or 0)
    except (TypeError, ValueError) as exc:
        raise TelemetryError(f"Codex Desktop {field} must be a non-negative integer") from exc
    if result < 0:
        raise TelemetryError(f"Codex Desktop {field} must be a non-negative integer")
    return result


def _safe_session_id(value: Any) -> str | None:
    selected = str(value or "").strip()
    return selected if SESSION_ID_RE.fullmatch(selected) else None


def desktop_session_id_from_environment() -> str | None:
    """Return only a portable exact Desktop identity inherited by this process."""
    return _safe_session_id(os.environ.get("CODEX_THREAD_ID"))


def _same_path(left: Path | str, right: Path | str) -> bool:
    return os.path.normcase(str(Path(left).resolve())) == os.path.normcase(str(Path(right).resolve()))


def _contains_path(text: str, root: Path) -> bool:
    marker = re.sub(r"\\+", r"\\", str(root.resolve()).replace("/", "\\")).rstrip("\\").casefold()
    # Tool calls are stored as source text, so a Windows separator can appear
    # once as a path character or twice as a language-string escape.
    candidate = re.sub(r"\\+", r"\\", str(text).replace("/", "\\")).casefold()
    start = 0
    boundaries = set("\\\"'` \t\r\n,;:)]}")
    while True:
        index = candidate.find(marker, start)
        if index < 0:
            return False
        after = index + len(marker)
        if after == len(candidate) or candidate[after] in boundaries:
            return True
        start = index + 1


def _contains_task_id(text: str, task_id: str) -> bool:
    escaped = re.escape(task_id)
    return re.search(rf"(?<![A-Za-z0-9_.-]){escaped}(?![A-Za-z0-9_.-])", str(text), re.IGNORECASE) is not None


def _association_fragments(record: Mapping[str, Any]) -> list[str]:
    payload = record.get("payload") or {}
    if not isinstance(payload, Mapping):
        return []
    fragments: list[str] = []
    record_type = str(record.get("type") or "")
    payload_type = str(payload.get("type") or "")
    if record_type == "response_item" and payload_type in {
        "custom_tool_call", "custom_tool_call_output", "function_call", "function_call_output", "message",
    }:
        for field in ("input", "arguments", "output", "message"):
            value = payload.get(field)
            if value is not None:
                fragments.append(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True))
        content = payload.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, Mapping):
                    value = item.get("text")
                    if value is not None:
                        fragments.append(str(value))
    elif record_type == "event_msg" and payload_type in {"user_message", "agent_message"}:
        for field in ("message", "text"):
            if payload.get(field) is not None:
                fragments.append(str(payload[field]))
    return fragments


def inspect_desktop_session(
    path: Path | str,
    *,
    root: Path | str | None = None,
    task_id: str | None = None,
    expected_session_id: str | None = None,
) -> dict[str, Any]:
    """Inspect a Codex Desktop rollout JSONL without treating it as authority.

    A live file may end in a partially written final line.  Only that tail is
    ignored; malformed complete records fail the adapter safely.
    """
    source_path = Path(path).expanduser().resolve()
    if not source_path.is_file():
        raise TelemetryError(f"Desktop session file does not exist: {source_path}")
    repository = Path(root).resolve() if root is not None else None
    expected = _safe_session_id(expected_session_id) if expected_session_id else None
    if expected_session_id and not expected:
        raise TelemetryError("Desktop session identity is invalid")

    metadata: dict[str, Any] | None = None
    repository_match = False
    cwd_match = False
    task_match = task_id is None
    current_turn_repository_match = False
    current_turn_task_match = task_id is None
    current_turn_started = False
    last_repository_activity: datetime | None = None
    latest_started: datetime | None = None
    latest_complete: datetime | None = None
    last_timestamp: datetime | None = None
    partial_tail = False
    token_events = 0
    totals: dict[str, int] | None = None
    max_prompt = 0
    peak_prompt_measured = False
    latest_prompt: int | None = None
    latest_prompt_measured = False
    latest_context_window: int | None = None
    cached_input_complete = True
    cache_write_input_complete = True
    request_prompt_tokens: list[int | None] = []
    request_context_windows: list[int | None] = []
    compaction_events = 0
    context_compacted_events = 0
    compaction_zero_events = 0
    compaction_pending = False
    latest_compacted_at: str | None = None
    last_token_at: str | None = None

    with source_path.open("rb") as handle:
        for line_number, raw in enumerate(handle, 1):
            complete_line = raw.endswith(b"\n")
            try:
                record = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                if not complete_line:
                    partial_tail = True
                    break
                raise TelemetryError(f"invalid Desktop JSONL record at line {line_number}") from exc
            if not isinstance(record, dict):
                continue
            observed = _timestamp(record.get("timestamp"))
            if observed and (last_timestamp is None or observed > last_timestamp):
                last_timestamp = observed
            record_type = str(record.get("type") or "")
            payload = record.get("payload") or {}
            if not isinstance(payload, Mapping):
                continue
            payload_type = str(payload.get("type") or "")
            if record_type == "compacted":
                compaction_events += 1
                compaction_pending = True
                latest_compacted_at = str(record.get("timestamp") or latest_compacted_at or _now())
            if record_type == "event_msg" and payload_type == "context_compacted":
                context_compacted_events += 1
                compaction_pending = False
                latest_compacted_at = str(record.get("timestamp") or latest_compacted_at or _now())
            if record_type == "session_meta":
                # Compacted/forked rollouts may replay ancestor metadata after
                # the current file header.  The first header owns this physical
                # stream; later headers are historical context only.
                if metadata is None:
                    metadata = dict(payload)
                    session_cwd = payload.get("cwd")
                    if repository is not None and session_cwd:
                        try:
                            if _same_path(str(session_cwd), repository):
                                repository_match = True
                                cwd_match = True
                                last_repository_activity = observed
                        except OSError:
                            pass
            if record_type == "event_msg" and payload_type == "task_started":
                latest_started = observed or latest_started
                if payload.get("model_context_window") is not None:
                    task_window = _desktop_number(
                        payload.get("model_context_window"), field="model_context_window"
                    )
                    if task_window <= 0:
                        raise TelemetryError("Codex Desktop model_context_window must be a positive integer")
                    latest_context_window = task_window
                # Fork/compaction history can replay old task and repository
                # strings before the current turn. Only current-turn evidence
                # may establish automatic task association.
                current_turn_started = True
                current_turn_repository_match = False
                current_turn_task_match = task_id is None
            if record_type == "event_msg" and payload_type == "task_complete":
                latest_complete = observed or latest_complete

            fragments = _association_fragments(record)
            if repository is not None and any(_contains_path(item, repository) for item in fragments):
                repository_match = True
                if current_turn_started:
                    current_turn_repository_match = True
                if observed and (last_repository_activity is None or observed > last_repository_activity):
                    last_repository_activity = observed
            if task_id is not None and any(_contains_task_id(item, task_id) for item in fragments):
                task_match = True
                if current_turn_started:
                    current_turn_task_match = True

            if record_type != "event_msg" or payload_type != "token_count":
                continue
            info = payload.get("info") or {}
            total_usage = info.get("total_token_usage") or {}
            last_usage = info.get("last_token_usage") or {}
            if not isinstance(total_usage, Mapping) or not total_usage:
                raise TelemetryError(f"Desktop token_count has no cumulative usage at line {line_number}")
            if info.get("model_context_window") is not None:
                observed_window = _desktop_number(
                    info.get("model_context_window"), field="model_context_window"
                )
                if observed_window <= 0:
                    raise TelemetryError("Codex Desktop model_context_window must be a positive integer")
            else:
                observed_window = None
            observed_prompt_measured = isinstance(last_usage, Mapping) and "input_tokens" in last_usage
            observed_prompt = (
                _desktop_number(last_usage.get("input_tokens"), field="last input_tokens")
                if observed_prompt_measured else None
            )
            prior_cached = totals.get("cached_input_tokens", 0) if totals is not None else 0
            if "cached_input_tokens" in total_usage:
                observed_cached = _desktop_number(
                    total_usage.get("cached_input_tokens"), field="cached_input_tokens"
                )
                if observed_cached < prior_cached:
                    cached_input_complete = False
                    observed_cached = prior_cached
            else:
                cached_input_complete = False
                observed_cached = prior_cached
            prior_cache_write = totals.get("cache_write_input_tokens", 0) if totals is not None else 0
            if "cache_write_input_tokens" in total_usage:
                observed_cache_write = _desktop_number(
                    total_usage.get("cache_write_input_tokens"), field="cache_write_input_tokens"
                )
                if observed_cache_write < prior_cache_write:
                    cache_write_input_complete = False
                    observed_cache_write = prior_cache_write
            else:
                cache_write_input_complete = False
                observed_cache_write = prior_cache_write
            current = {
                "raw_input_tokens": _desktop_number(total_usage.get("input_tokens"), field="input_tokens"),
                "cached_input_tokens": observed_cached,
                "cache_write_input_tokens": observed_cache_write,
                "output_tokens": _desktop_number(total_usage.get("output_tokens"), field="output_tokens"),
                "reasoning_tokens": _desktop_number(total_usage.get("reasoning_output_tokens"), field="reasoning_output_tokens"),
            }
            core_cumulative = ("raw_input_tokens", "output_tokens", "reasoning_tokens")
            if totals is not None and any(current[field] < totals[field] for field in core_cumulative):
                raise TelemetryError(f"Desktop cumulative usage regressed at line {line_number}")
            if totals is not None and all(current[field] == totals[field] for field in core_cumulative):
                # Desktop can replay an identical token_count notification.
                # Advisory cache counters may appear/disappear independently;
                # a model request is one core cumulative advance, not one row.
                if compaction_pending and observed_prompt_measured and observed_prompt == 0:
                    # A real Desktop compact emits: top-level `compacted`, a
                    # same-cumulative zero prompt, then `context_compacted`.
                    # Only that sequence may let a non-request row rebaseline P.
                    latest_prompt = 0
                    latest_prompt_measured = True
                    if observed_window is not None:
                        latest_context_window = observed_window
                    last_token_at = str(record.get("timestamp") or last_token_at or _now())
                    compaction_zero_events += 1
                    compaction_pending = False
                totals = current
                continue
            totals = current
            token_events += 1
            latest_prompt = observed_prompt if observed_prompt_measured else None
            latest_prompt_measured = observed_prompt_measured
            if observed_prompt_measured:
                max_prompt = max(max_prompt, int(observed_prompt))
                peak_prompt_measured = True
            if observed_window is not None:
                latest_context_window = observed_window
            last_token_at = str(record.get("timestamp") or last_token_at or _now())
            compaction_pending = False
            request_prompt_tokens.append(latest_prompt if latest_prompt_measured else None)
            request_context_windows.append(latest_context_window)

    if metadata is None:
        raise TelemetryError("Desktop JSONL has no session_meta record")
    # `id` is the physical rollout/stream and matches CODEX_THREAD_ID and the
    # filename.  Subagents can inherit a parent's `session_id`, so that field
    # is diagnostic only and must never be used to merge counters.
    session_id = _safe_session_id(metadata.get("id"))
    logical_session_id = _safe_session_id(metadata.get("session_id"))
    raw_forked_from_id = metadata.get("forked_from_id")
    forked_from_id = _safe_session_id(raw_forked_from_id)
    if session_id is None or logical_session_id is None:
        raise TelemetryError("Desktop session_meta requires valid id and session_id identities")
    if raw_forked_from_id is not None and forked_from_id is None:
        raise TelemetryError("Desktop session_meta forked_from_id is invalid")
    if expected and session_id != expected:
        raise TelemetryError("Desktop session identity does not match the requested session")
    if not source_path.stem.endswith(f"-{session_id}"):
        raise TelemetryError("Desktop session identity does not match the rollout filename")
    if str(metadata.get("originator") or "").casefold() != "codex desktop":
        raise TelemetryError("telemetry source is not a Codex Desktop session")

    usage = None
    if totals is not None:
        usage = {
            "thread_id": session_id,
            **totals,
            "model_requests": token_events,
            "model_requests_measured": True,
            "cached_input_tokens_measured": token_events > 0 and cached_input_complete,
            "cache_write_input_tokens_measured": token_events > 0 and cache_write_input_complete,
            "projected_prompt_tokens": latest_prompt,
            "projected_prompt_tokens_measured": latest_prompt_measured,
            "peak_prompt_tokens": max_prompt if peak_prompt_measured else None,
            "peak_prompt_tokens_measured": peak_prompt_measured,
            "model_context_window": latest_context_window,
            "model_context_window_measured": latest_context_window is not None,
            "role": "PRODUCTIVE",
            "cumulative": True,
            "observed_at": last_token_at or _now(),
        }
    active = latest_complete is None or (latest_started is not None and latest_started > latest_complete)
    return {
        "path": str(source_path),
        "session_id": session_id,
        "logical_session_id": logical_session_id,
        "forked_from_id": forked_from_id,
        "thread_source": metadata.get("thread_source"),
        "self_owned_stream": logical_session_id == session_id,
        "eligible_user_stream": (
            str(metadata.get("thread_source") or "").casefold() == "user"
            and logical_session_id == session_id
        ),
        "originator": metadata.get("originator"),
        "session_started_at": metadata.get("timestamp"),
        "session_cwd": metadata.get("cwd"),
        "repository_match": repository_match if repository is not None else None,
        "cwd_match": cwd_match if repository is not None else None,
        "task_match": task_match if task_id is not None else None,
        "current_turn_repository_match": current_turn_repository_match if repository is not None else None,
        "current_turn_task_match": current_turn_task_match if task_id is not None else None,
        "last_repository_activity": last_repository_activity.isoformat().replace("+00:00", "Z") if last_repository_activity else None,
        "last_timestamp": last_timestamp.isoformat().replace("+00:00", "Z") if last_timestamp else None,
        "active": active,
        "partial_tail": partial_tail,
        "token_events": token_events,
        "compaction_events": compaction_events,
        "context_compacted_events": context_compacted_events,
        "compaction_zero_events": compaction_zero_events,
        "latest_compacted_at": latest_compacted_at,
        "request_prompt_tokens": request_prompt_tokens,
        "request_context_windows": request_context_windows,
        "usage": usage,
    }


def _binding_identity(state: Mapping[str, Any]) -> dict[str, Any]:
    context = state.get("context") or {}
    return {
        "task_id": str(state.get("task_id") or ""),
        "revision": int(state.get("revision", 0)),
        "epoch": int(context.get("epoch", 1)),
        "epoch_id": str(context.get("epoch_id") or ""),
    }


def _desktop_header_fingerprint(
    inspected: Mapping[str, Any],
    *,
    include_fork_parent: bool = True,
) -> str:
    identity = {
        "session_id": inspected.get("session_id"),
        "logical_session_id": inspected.get("logical_session_id"),
        "session_started_at": inspected.get("session_started_at"),
        "session_cwd": inspected.get("session_cwd"),
        "originator": inspected.get("originator"),
        "thread_source": inspected.get("thread_source"),
    }
    # Preserve fingerprints written by the first v1.22 corrective while
    # covering the parent identity when Desktop declares a fork relationship.
    if include_fork_parent and inspected.get("forked_from_id"):
        identity["forked_from_id"] = inspected.get("forked_from_id")
    return hashlib.sha256(canonical_bytes(identity)).hexdigest()


def _binding_file(root: Path | str, state: Mapping[str, Any]) -> Path:
    identity = _binding_identity(state)
    key = hashlib.sha256(canonical_bytes(identity)).hexdigest()
    return safe_repository_descendant(
        root, Path(".buildos") / "runtime" / "telemetry_bindings" / f"{key}.json",
        label="telemetry binding target",
    )


def _read_binding(root: Path | str, state: Mapping[str, Any]) -> dict[str, Any] | None:
    path = _binding_file(root, state)
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TelemetryError("persisted Desktop telemetry binding is unreadable") from exc
    identity = _binding_identity(state)
    if not isinstance(value, dict) or value.get("schema") != BINDING_SCHEMA:
        raise TelemetryError("persisted Desktop telemetry binding has invalid structure")
    if any(value.get(field) != expected for field, expected in identity.items()):
        raise TelemetryError("persisted Desktop telemetry binding identity mismatch")
    if value.get("source") != DESKTOP_SOURCE or not _safe_session_id(value.get("session_id")):
        raise TelemetryError("persisted Desktop telemetry binding source is invalid")
    association = value.get("association", ROOT_USER_ASSOCIATION)
    if association not in {ROOT_USER_ASSOCIATION, ROLLOVER_HANDOFF_ASSOCIATION}:
        raise TelemetryError("persisted Desktop telemetry binding association is invalid")
    expected_rollover_thread = _safe_session_id((state.get("context") or {}).get("thread_id"))
    if (
        "association" in value
        and identity["epoch"] > 1
        and (not expected_rollover_thread or value.get("session_id") != expected_rollover_thread)
    ):
        raise TelemetryError("persisted Desktop telemetry binding is not the expected rollover continuation")
    parent_session_id = value.get("parent_session_id")
    if association == ROLLOVER_HANDOFF_ASSOCIATION:
        if int(value.get("epoch", 0)) <= 1 or not _safe_session_id(parent_session_id):
            raise TelemetryError("persisted Desktop rollover handoff is invalid")
        if parent_session_id == value.get("session_id"):
            raise TelemetryError("persisted Desktop rollover handoff reuses its parent session")
    elif parent_session_id not in {None, ""}:
        raise TelemetryError("persisted root-user Desktop binding has unexpected rollover ancestry")
    if not re.fullmatch(r"[0-9a-f]{64}", str(value.get("header_fingerprint") or "")):
        raise TelemetryError("persisted Desktop telemetry binding header fingerprint is invalid")
    if not value.get("path") or not value.get("repository_root"):
        raise TelemetryError("persisted Desktop telemetry binding repository is missing")
    if not _same_path(value.get("repository_root"), root):
        raise TelemetryError("persisted Desktop telemetry binding repository mismatch")
    baseline = value.get("baseline")
    baseline_fields = {
        "raw_input_tokens", "cached_input_tokens", "output_tokens",
        "reasoning_tokens", "model_requests",
    }
    if not isinstance(baseline, dict) or not baseline_fields.issubset(baseline):
        raise TelemetryError("persisted Desktop telemetry binding baseline is invalid")
    for field in baseline_fields:
        _desktop_number(baseline.get(field), field=f"binding baseline {field}")
    if "cache_write_input_tokens" in baseline:
        _desktop_number(
            baseline.get("cache_write_input_tokens"),
            field="binding baseline cache_write_input_tokens",
        )
    return value


def _persist_binding(
    root: Path | str,
    state: Mapping[str, Any],
    inspected: Mapping[str, Any],
    *,
    association: str = ROOT_USER_ASSOCIATION,
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    final = _binding_file(root_path, state)
    existing = _read_binding(root_path, state)
    if existing is not None:
        return existing
    if association not in {ROOT_USER_ASSOCIATION, ROLLOVER_HANDOFF_ASSOCIATION}:
        raise TelemetryError("Desktop telemetry binding association is invalid")
    parent_session_id = inspected.get("forked_from_id") if association == ROLLOVER_HANDOFF_ASSOCIATION else None
    if association == ROLLOVER_HANDOFF_ASSOCIATION and not _safe_session_id(parent_session_id):
        raise TelemetryError("Desktop rollover handoff requires a valid parent session")
    usage = inspected.get("usage") or {}
    value = {
        "schema": BINDING_SCHEMA,
        **_binding_identity(state),
        "source": DESKTOP_SOURCE,
        "association": association,
        "session_id": inspected["session_id"],
        "parent_session_id": parent_session_id,
        "path": str(Path(str(inspected["path"])).resolve()),
        "repository_root": str(root_path),
        "session_started_at": inspected.get("session_started_at"),
        "header_fingerprint": _desktop_header_fingerprint(inspected),
        # The first safely selected cumulative snapshot is the immutable epoch
        # baseline. This preserves the existing v1.22 accounting contract and
        # closes the bind-before-ledger crash window.
        "baseline": {
            "raw_input_tokens": _number(usage.get("raw_input_tokens")),
            "cached_input_tokens": _number(usage.get("cached_input_tokens")),
            "cache_write_input_tokens": _number(usage.get("cache_write_input_tokens")),
            "output_tokens": _number(usage.get("output_tokens")),
            "reasoning_tokens": _number(usage.get("reasoning_tokens")),
            "model_requests": _number(usage.get("model_requests")),
        },
    }
    data = canonical_bytes(value)
    final.parent.mkdir(parents=True, exist_ok=True)
    stage = final.parent / f".{final.stem}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    atomic_write(stage, data)
    try:
        publish_immutable(stage, final)
    except RecoveryRequired:
        if stage.exists():
            stage.unlink()
        # A simultaneous observer may have selected the binding first.  Its
        # immutable result wins; retries never replace it.
        selected = _read_binding(root_path, state)
        if selected is None:
            raise TelemetryError("Desktop telemetry binding publication conflicted")
        return selected
    return value


def _sessions_root() -> Path:
    configured = os.environ.get(DESKTOP_SESSIONS_DIR_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return (Path(codex_home).expanduser().resolve() / "sessions")
    return (Path.home() / ".codex" / "sessions").resolve()


def _task_repository_associated(inspected: Mapping[str, Any]) -> bool:
    return bool(
        inspected.get("repository_match")
        and inspected.get("task_match")
        and inspected.get("current_turn_task_match")
        and (inspected.get("cwd_match") or inspected.get("current_turn_repository_match"))
    )


def _associated(inspected: Mapping[str, Any]) -> bool:
    return bool(inspected.get("eligible_user_stream") and _task_repository_associated(inspected))


def _rollover_handoff_associated(
    inspected: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    previous_epoch_session: str | None,
) -> bool:
    """Accept only the exact self-owned Desktop fork named by rollover.

    Ordinary subagent streams remain ineligible.  This exception joins the
    current disposable context to the immediately previous immutable Desktop
    binding; it does not create a session registry or lifecycle authority.
    """
    context = state.get("context") or {}
    expected_session = _safe_session_id(context.get("thread_id"))
    return bool(
        int(context.get("epoch", 1)) > 1
        and expected_session
        and inspected.get("session_id") == expected_session
        and inspected.get("self_owned_stream")
        and str(inspected.get("thread_source") or "").casefold() == "subagent"
        and previous_epoch_session
        and inspected.get("forked_from_id") == previous_epoch_session
        and _task_repository_associated(inspected)
    )


def _association_kind(
    inspected: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    previous_epoch_session: str | None,
) -> str | None:
    if _associated(inspected):
        return ROOT_USER_ASSOCIATION
    if _rollover_handoff_associated(
        inspected,
        state,
        previous_epoch_session=previous_epoch_session,
    ):
        return ROLLOVER_HANDOFF_ASSOCIATION
    return None


def _bound_stream_matches_association(
    root: Path | str,
    inspected: Mapping[str, Any],
    binding: Mapping[str, Any],
    state: Mapping[str, Any],
) -> bool:
    association = binding.get("association", ROOT_USER_ASSOCIATION)
    if association == ROOT_USER_ASSOCIATION:
        context = state.get("context") or {}
        expected = _safe_session_id(context.get("thread_id"))
        return bool(
            inspected.get("eligible_user_stream")
            and (
                "association" not in binding
                or int(context.get("epoch", 1)) <= 1
                or expected == binding.get("session_id")
            )
        )
    if association != ROLLOVER_HANDOFF_ASSOCIATION:
        return False
    context = state.get("context") or {}
    previous = _previous_epoch_bindings(root, state).get(int(context.get("epoch", 1)) - 1)
    return bool(
        int(context.get("epoch", 1)) > 1
        and _safe_session_id(context.get("thread_id")) == binding.get("session_id")
        and inspected.get("session_id") == binding.get("session_id")
        and inspected.get("self_owned_stream")
        and str(inspected.get("thread_source") or "").casefold() == "subagent"
        and previous
        and previous == binding.get("parent_session_id")
        and inspected.get("forked_from_id") == previous
    )


def _unbound(reason: str, *, candidates: Iterable[str] = ()) -> dict[str, Any]:
    return {
        "status": "TELEMETRY_UNBOUND",
        "reason": reason,
        "source": DESKTOP_SOURCE,
        "candidates": sorted(set(str(item) for item in candidates if item)),
    }


def _previous_epoch_bindings(root: Path | str, state: Mapping[str, Any]) -> dict[int, str]:
    identity = _binding_identity(state)
    root_path = Path(root).resolve()
    directory = safe_repository_descendant(
        root_path, Path(".buildos") / "runtime" / "telemetry_bindings",
        label="telemetry binding directory",
    )
    if not directory.is_dir():
        return {}
    result: dict[int, str] = {}
    relevant: dict[int, dict[str, Any]] = {}
    for path in directory.glob("*.json"):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TelemetryError("persisted Desktop telemetry binding history is unreadable") from exc
        if not isinstance(value, dict) or value.get("schema") != BINDING_SCHEMA:
            raise TelemetryError("persisted Desktop telemetry binding history has invalid structure")
        try:
            historical_state = {
                "task_id": str(value["task_id"]),
                "revision": int(value["revision"]),
                "context": {
                    "epoch": int(value["epoch"]),
                    "epoch_id": str(value["epoch_id"]),
                    "thread_id": str(value["session_id"]),
                },
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise TelemetryError("persisted Desktop telemetry binding history has invalid identity") from exc
        expected_path = _binding_file(root_path, historical_state)
        if not _same_path(path, expected_path):
            raise TelemetryError("persisted Desktop telemetry binding history filename mismatch")
        validated = _read_binding(root_path, historical_state)
        if validated is None:
            raise TelemetryError("persisted Desktop telemetry binding history disappeared during validation")
        if (
            validated.get("task_id") == identity["task_id"]
            and int(validated.get("revision", 0)) == identity["revision"]
            and int(validated.get("epoch", 0)) < identity["epoch"]
        ):
            epoch = int(validated["epoch"])
            session_id = str(validated["session_id"])
            if epoch in result:
                raise TelemetryError("multiple Desktop telemetry bindings claim one previous epoch")
            result[epoch] = session_id
            relevant[epoch] = validated
    for epoch, binding in relevant.items():
        if binding.get("association", ROOT_USER_ASSOCIATION) != ROLLOVER_HANDOFF_ASSOCIATION:
            continue
        if result.get(epoch - 1) != binding.get("parent_session_id"):
            raise TelemetryError("persisted Desktop rollover handoff ancestry is inconsistent")
    return result


def _desktop_bound_usage(
    inspected: Mapping[str, Any],
    binding: Mapping[str, Any],
    state: Mapping[str, Any],
) -> dict[str, Any] | None:
    current = inspected.get("usage")
    if not isinstance(current, Mapping):
        return None
    baseline = binding.get("baseline") or {}
    numeric = (
        "raw_input_tokens", "cached_input_tokens", "cache_write_input_tokens",
        "output_tokens", "reasoning_tokens", "model_requests",
    )
    adjusted: dict[str, int] = {}
    for field in numeric:
        current_value = _desktop_number(current.get(field), field=field)
        baseline_value = _desktop_number(baseline.get(field), field=f"binding baseline {field}")
        if current_value < baseline_value:
            raise TelemetryError(f"Desktop cumulative {field} fell below the persisted epoch baseline")
        adjusted[field] = current_value - baseline_value
    if adjusted["model_requests"] == 0:
        return None
    prompts = inspected.get("request_prompt_tokens") or []
    baseline_requests = _desktop_number(baseline.get("model_requests"), field="binding baseline model_requests")
    if not isinstance(prompts, list) or len(prompts) < baseline_requests:
        raise TelemetryError("Desktop request history no longer contains the persisted epoch baseline")
    current_prompts = [
        _desktop_number(value, field="last input_tokens")
        for value in prompts[baseline_requests:]
        if value is not None
    ]
    context_thread = (state.get("context") or {}).get("thread_id")
    payload: dict[str, Any] = {
        **adjusted,
        "thread_id": context_thread or binding.get("session_id"),
        "source_session_id": binding.get("session_id"),
        "model_requests_measured": True,
        "cached_input_tokens_measured": bool(current.get("cached_input_tokens_measured")),
        "cache_write_input_tokens_measured": bool(current.get("cache_write_input_tokens_measured")),
        "role": "PRODUCTIVE",
        "cumulative": True,
        "observed_at": current.get("observed_at") or _now(),
    }
    if current.get("projected_prompt_tokens_measured"):
        payload["projected_prompt_tokens"] = _desktop_number(
            current.get("projected_prompt_tokens"), field="latest input_tokens"
        )
    if current_prompts:
        payload["peak_prompt_tokens"] = max(current_prompts)
    if current.get("model_context_window_measured"):
        payload["model_context_window"] = _desktop_number(
            current.get("model_context_window"), field="model_context_window"
        )
    return payload


def discover_desktop_session(
    root: Path | str,
    state: Mapping[str, Any],
    *,
    rollover_thread_id: str | None = None,
) -> dict[str, Any]:
    """Resolve exactly one Desktop session or fail observability closed."""
    root_path = Path(root).resolve()
    identity = _binding_identity(state)
    raw_context_thread = (state.get("context") or {}).get("thread_id")
    context_thread = _safe_session_id(raw_context_thread)
    if identity["epoch"] > 1 and raw_context_thread and context_thread is None:
        return _unbound("INVALID_EXPECTED_CONTINUATION")
    environment_thread = desktop_session_id_from_environment()
    rollover_caller = _safe_session_id(rollover_thread_id)
    if rollover_thread_id is not None and rollover_caller is None:
        return _unbound("INVALID_EXPECTED_CONTINUATION")
    persisted = _read_binding(root_path, state)
    if persisted is not None:
        if rollover_caller and rollover_caller == persisted.get("session_id"):
            return _unbound("PREVIOUS_EPOCH_SESSION", candidates=[rollover_caller])
        if identity["epoch"] > 1:
            prior_sessions: set[str] | None = None
            if rollover_caller and rollover_caller != persisted.get("session_id"):
                prior_sessions = set(_previous_epoch_bindings(root_path, state).values())
                if rollover_caller in prior_sessions:
                    return _unbound("PREVIOUS_EPOCH_SESSION", candidates=[rollover_caller])
            if environment_thread and environment_thread != persisted.get("session_id"):
                if prior_sessions is None:
                    prior_sessions = set(_previous_epoch_bindings(root_path, state).values())
                if environment_thread in prior_sessions:
                    return _unbound("PREVIOUS_EPOCH_SESSION", candidates=[environment_thread])
                if environment_thread != rollover_caller:
                    return _unbound("NOT_EXPECTED_CONTINUATION", candidates=[environment_thread])
        return {
            "status": "BOUND",
            "reason": "PERSISTED",
            "source": DESKTOP_SOURCE,
            "binding": persisted,
            "available": Path(str(persisted["path"])).is_file(),
        }

    prior_bindings = _previous_epoch_bindings(root_path, state)
    prior_sessions = set(prior_bindings.values())
    previous_epoch_session = prior_bindings.get(identity["epoch"] - 1)
    expected_rollover_thread = context_thread if identity["epoch"] > 1 else None

    # A rollover already selected one disposable physical continuation.  The
    # current caller may be that stream (or have no inherited Desktop ID), but
    # an unrelated caller must not replace the canonical expectation merely by
    # being newer or by mentioning the same task and repository.
    if expected_rollover_thread and environment_thread and environment_thread != expected_rollover_thread:
        if environment_thread in prior_sessions:
            return _unbound("PREVIOUS_EPOCH_SESSION", candidates=[environment_thread])
        return _unbound("NOT_EXPECTED_CONTINUATION", candidates=[environment_thread])

    override = os.environ.get(DESKTOP_SESSION_FILE_ENV)
    if override:
        try:
            inspected = inspect_desktop_session(
                override,
                root=root_path,
                task_id=str(state.get("task_id") or ""),
                expected_session_id=environment_thread,
            )
        except TelemetryError as exc:
            raise TelemetryError(f"explicit Desktop telemetry override is invalid: {exc}") from exc
        association = _association_kind(
            inspected,
            state,
            previous_epoch_session=previous_epoch_session,
        )
        if expected_rollover_thread and inspected["session_id"] != expected_rollover_thread:
            raise TelemetryError("explicit Desktop telemetry override is not the expected rollover continuation")
        if association is None:
            raise TelemetryError("explicit Desktop telemetry override is not associated with the active repository and task")
        if inspected["session_id"] in prior_sessions:
            raise TelemetryError("explicit Desktop telemetry override reuses a prior epoch session")
        binding = _persist_binding(root_path, state, inspected, association=association)
        return {"status": "BOUND", "reason": "EXPLICIT_OVERRIDE", "source": DESKTOP_SOURCE, "binding": binding, "available": True}

    sessions = _sessions_root()
    if not sessions.is_dir():
        return _unbound("UNAVAILABLE")

    exact_thread = expected_rollover_thread or environment_thread or context_thread
    if exact_thread:
        matches: list[tuple[dict[str, Any], str]] = []
        exact_errors: list[str] = []
        exact_candidates = [
            candidate
            for candidate in sorted(sessions.rglob(f"*{exact_thread}*.jsonl"), key=lambda item: str(item).casefold())
            if candidate.stem.endswith(f"-{exact_thread}")
        ]
        if len(exact_candidates) > 1:
            return _unbound("AMBIGUOUS", candidates=[exact_thread])
        for candidate in exact_candidates:
            try:
                inspected = inspect_desktop_session(
                    candidate,
                    root=root_path,
                    task_id=str(state.get("task_id") or ""),
                    expected_session_id=exact_thread,
                )
            except TelemetryError as exc:
                exact_errors.append(str(exc))
                continue
            association = _association_kind(
                inspected,
                state,
                previous_epoch_session=previous_epoch_session,
            )
            if association is not None:
                matches.append((inspected, association))
        if not matches:
            if exact_errors:
                raise TelemetryError(f"exact Desktop session is unreadable: {exact_errors[0]}")
            if environment_thread or expected_rollover_thread:
                return _unbound("NOT_ASSOCIATED", candidates=[exact_thread])
        elif any(item[0]["session_id"] in prior_sessions for item in matches):
            return _unbound("PREVIOUS_EPOCH_SESSION", candidates=[item[0]["session_id"] for item in matches])
        elif len(matches) > 1:
            return _unbound("AMBIGUOUS", candidates=[item[0]["session_id"] for item in matches])
        elif len(matches) == 1:
            inspected, association = matches[0]
            binding = _persist_binding(root_path, state, inspected, association=association)
            reason = "ROLLOVER_HANDOFF" if association == ROLLOVER_HANDOFF_ASSOCIATION else "EXACT_SESSION_ID"
            return {"status": "BOUND", "reason": reason, "source": DESKTOP_SOURCE, "binding": binding, "available": True}

    created = _timestamp(state.get("created_at")) or datetime.now(timezone.utc)
    freshness_floor = created - timedelta(minutes=5)
    plausible: list[dict[str, Any]] = []
    for candidate in sorted(sessions.rglob("rollout-*.jsonl"), key=lambda item: str(item).casefold()):
        try:
            inspected = inspect_desktop_session(candidate, root=root_path, task_id=str(state.get("task_id") or ""))
        except (OSError, TelemetryError):
            continue
        activity = _timestamp(inspected.get("last_repository_activity"))
        if (
            _associated(inspected)
            and inspected.get("cwd_match")
            and inspected.get("active")
            and inspected.get("session_id") not in prior_sessions
            and activity
            and activity >= freshness_floor
        ):
            plausible.append(inspected)
    if not plausible:
        return _unbound("UNAVAILABLE")
    if len(plausible) > 1:
        return _unbound("AMBIGUOUS", candidates=[item["session_id"] for item in plausible])
    binding = _persist_binding(root_path, state, plausible[0], association=ROOT_USER_ASSOCIATION)
    return {"status": "BOUND", "reason": "UNIQUE_REPOSITORY_ACTIVITY", "source": DESKTOP_SOURCE, "binding": binding, "available": True}


def _record_id(record: Mapping[str, Any]) -> str:
    base = {k: v for k, v in record.items() if k not in {"record_id", "observed_at"}}
    raw = json.dumps(base, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def normalize(payload: Mapping[str, Any], state: Mapping[str, Any], *, source: str) -> dict[str, Any]:
    task_id = str(payload.get("task_id") or state.get("task_id") or "")
    revision = _number(payload.get("revision", payload.get("task_revision", state.get("revision"))))
    if task_id != state.get("task_id") or revision != int(state.get("revision", 0)):
        raise TelemetryError("telemetry identity does not match active task/revision")
    role = str(payload.get("role", "PRODUCTIVE")).upper()
    if role in {"WORKER", "IMPLEMENTATION", "PRODUCT"}:
        role = "PRODUCTIVE"
    if role in {"OS", "KERNEL", "CONTROL_PLANE"}:
        role = "CONTROL"
    if role not in {"PRODUCTIVE", "CONTROL"}:
        raise TelemetryError("telemetry role must be PRODUCTIVE or CONTROL")
    active_thread = (state.get("context") or {}).get("thread_id")
    if active_thread and payload.get("thread_id") != active_thread:
        raise TelemetryError("telemetry thread does not match the active disposable epoch")
    active_epoch_id = (state.get("context") or {}).get("epoch_id")
    if payload.get("epoch_id") and active_epoch_id and payload.get("epoch_id") != active_epoch_id:
        raise TelemetryError("telemetry epoch identity does not match the active disposable epoch")
    active_epoch = _number((state.get("context") or {}).get("epoch", 1)) or 1
    payload_epoch = _number(payload.get("epoch", active_epoch)) or 1
    if payload_epoch != active_epoch:
        raise TelemetryError("telemetry epoch number does not match the active disposable epoch")
    raw_prompt = payload.get("projected_prompt_tokens", payload.get("latest_request_input_tokens"))
    prompt_present = (
        ("projected_prompt_tokens" in payload or "latest_request_input_tokens" in payload)
        and raw_prompt is not None
    )
    prompt_measured = bool(payload.get("projected_prompt_tokens_measured", prompt_present)) and prompt_present
    raw_peak = payload.get("peak_prompt_tokens", raw_prompt)
    peak_present = ("peak_prompt_tokens" in payload and raw_peak is not None) or prompt_measured
    peak_measured = bool(payload.get("peak_prompt_tokens_measured", peak_present)) and peak_present
    raw_input_present = (
        ("raw_input_tokens" in payload or "input_tokens" in payload)
        and payload.get("raw_input_tokens", payload.get("input_tokens")) is not None
    )
    cached_input_present = (
        ("cached_input_tokens" in payload or "cached_read_tokens" in payload)
        and payload.get("cached_input_tokens", payload.get("cached_read_tokens")) is not None
    )
    cache_write_present = (
        ("cache_write_input_tokens" in payload or "cache_write_tokens" in payload)
        and payload.get("cache_write_input_tokens", payload.get("cache_write_tokens")) is not None
    )
    cached_input_measured = bool(
        payload.get("cached_input_tokens_measured", cached_input_present)
    ) and cached_input_present
    cache_write_measured = bool(
        payload.get("cache_write_input_tokens_measured", cache_write_present)
    ) and cache_write_present
    noncached_present = "noncached_input_tokens" in payload and payload.get("noncached_input_tokens") is not None
    noncached_measured = bool(payload.get(
        "noncached_input_tokens_measured",
        noncached_present or (raw_input_present and cached_input_measured),
    )) and (noncached_present or (raw_input_present and cached_input_measured))
    record = {
        "schema": SCHEMA,
        "task_id": task_id,
        "revision": revision,
        "epoch": payload_epoch,
        "epoch_id": payload.get("epoch_id") or (state.get("context") or {}).get("epoch_id"),
        "thread_id": payload.get("thread_id"),
        "source_session_id": payload.get("source_session_id"),
        "source": source,
        "role": role,
        "raw_input_tokens": _number(payload.get("raw_input_tokens", payload.get("input_tokens"))),
        "cached_input_tokens": _number(payload.get("cached_input_tokens", payload.get("cached_read_tokens"))),
        "cache_write_input_tokens": _number(
            payload.get("cache_write_input_tokens", payload.get("cache_write_tokens"))
        ),
        "cached_input_tokens_measured": cached_input_measured,
        "cache_write_input_tokens_measured": cache_write_measured,
        "noncached_input_tokens": _number(payload.get("noncached_input_tokens")),
        "noncached_input_tokens_measured": noncached_measured,
        "output_tokens": _number(payload.get("output_tokens")),
        "reasoning_tokens": _number(payload.get("reasoning_tokens")),
        "model_requests": _number(payload.get("model_requests", 0)),
        "model_requests_measured": bool(payload.get("model_requests_measured", "model_requests" in payload)),
        "tool_actions": _number(payload.get("tool_actions")),
        "projected_prompt_tokens": _number(raw_prompt),
        "projected_prompt_tokens_measured": prompt_measured,
        "peak_prompt_tokens": _number(raw_peak),
        "peak_prompt_tokens_measured": peak_measured,
        "model_context_window": _number(
            payload.get("model_context_window", payload.get("context_window_tokens"))
        ),
        "model_context_window_measured": bool(
            payload.get(
                "model_context_window_measured",
                _number(payload.get("model_context_window", payload.get("context_window_tokens"))) > 0,
            )
        ),
        "cumulative": bool(payload.get("cumulative", False)),
        "observed_at": str(payload.get("observed_at") or _now()),
    }
    if noncached_measured and not noncached_present:
        record["noncached_input_tokens"] = max(0, record["raw_input_tokens"] - record["cached_input_tokens"])
    record["record_id"] = str(payload.get("record_id") or _record_id(record))
    return record


def _codex_notification(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    if payload.get("method") != "thread/tokenUsage/updated":
        return None
    params = payload.get("params") or {}
    usage = params.get("tokenUsage") or {}
    total = usage.get("total") or {}
    last = usage.get("last") or {}
    if not total and not last:
        raise TelemetryError("Codex token notification has no usage payload")
    result = {
        "thread_id": params.get("threadId"),
        "raw_input_tokens": total.get("inputTokens", last.get("inputTokens", 0)),
        "output_tokens": total.get("outputTokens", last.get("outputTokens", 0)),
        "reasoning_tokens": total.get("reasoningOutputTokens", last.get("reasoningOutputTokens", 0)),
        "model_requests": params.get("modelRequests"),
        "model_requests_measured": params.get("modelRequests") is not None,
        "turn_id": params.get("turnId"),
        "role": "PRODUCTIVE",
        "cumulative": True,
    }
    if "inputTokens" in last:
        result["projected_prompt_tokens"] = last.get("inputTokens")
    if "cachedInputTokens" in total or "cachedInputTokens" in last:
        result["cached_input_tokens"] = total.get("cachedInputTokens", last.get("cachedInputTokens"))
    if "cacheWriteInputTokens" in total or "cacheWriteInputTokens" in last:
        result["cache_write_input_tokens"] = total.get(
            "cacheWriteInputTokens", last.get("cacheWriteInputTokens")
        )
    context_window = params.get("modelContextWindow", usage.get("modelContextWindow"))
    if context_window is not None:
        result["model_context_window"] = context_window
    return result


def _load_source(path: Path, source: str) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8")
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        decoded = []
        for line in raw.splitlines():
            if line.strip():
                decoded.append(json.loads(line))
    if isinstance(decoded, dict):
        decoded = decoded.get("records", [decoded])
    if not isinstance(decoded, list):
        raise TelemetryError("telemetry source must contain an object, list, or JSONL records")
    records: list[dict[str, Any]] = []
    for item in decoded:
        if not isinstance(item, dict):
            continue
        if source == "CODEX_APP_SERVER":
            parsed = _codex_notification(item)
            if parsed:
                records.append(parsed)
        else:
            records.append(dict(item))
    if source == "CODEX_APP_SERVER":
        threads = {str(item.get("thread_id")) for item in records if item.get("thread_id")}
        configured = os.environ.get("BUILDOS_THREAD_ID") or os.environ.get("AI_BUILD_OS_CODEX_THREAD_ID")
        inherited = desktop_session_id_from_environment()
        if configured:
            records = [item for item in records if item.get("thread_id") == configured]
        elif inherited and inherited in threads:
            records = [item for item in records if item.get("thread_id") == inherited]
        elif len(threads) > 1:
            raise TelemetryError("multiple unbound Codex threads; refusing to guess active telemetry")
        # Cumulative notifications supersede older values from the same thread.
        if records:
            explicit = [_number(item.get("model_requests")) for item in records if item.get("model_requests_measured")]
            turns = {str(item.get("turn_id")) for item in records if item.get("turn_id")}
            latest = records[-1]
            measured_prompts = [
                _number(item.get("projected_prompt_tokens"))
                for item in records
                if "projected_prompt_tokens" in item
            ]
            if measured_prompts:
                latest["peak_prompt_tokens"] = max(measured_prompts)
            measured_windows = [
                _number(item.get("model_context_window"))
                for item in records
                if _number(item.get("model_context_window")) > 0
            ]
            if measured_windows and not _number(latest.get("model_context_window")):
                latest["model_context_window"] = measured_windows[-1]
            if explicit:
                latest["model_requests"] = max(explicit)
                latest["model_requests_measured"] = True
            elif turns:
                latest["model_requests"] = len(turns)
                latest["model_requests_measured"] = True
            else:
                latest["model_requests"] = 0
                latest["model_requests_measured"] = False
            records = [latest]
    return records


def _ledger(root: Path | str) -> Path:
    path = safe_repository_descendant(
        root, Path(".buildos") / "runtime" / "telemetry.jsonl",
        label="telemetry event target",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _baseline_file(root: Path | str) -> Path:
    path = safe_repository_descendant(
        root, Path(".buildos") / "runtime" / "telemetry_baselines.json",
        label="telemetry baseline target",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _apply_cumulative_baseline(root: Path | str, state: Mapping[str, Any], payload: Mapping[str, Any], source: str) -> dict[str, Any]:
    path = _baseline_file(root)
    if path.is_file():
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TelemetryError("telemetry baseline is unreadable") from exc
        if not isinstance(document, dict) or not isinstance(document.get("streams", {}), dict):
            raise TelemetryError("telemetry baseline has invalid structure")
    else:
        document = {"schema": "buildos.telemetry_baselines.v1", "streams": {}}
    key = json.dumps([
        state.get("task_id"), int(state.get("revision", 0)),
        int((state.get("context") or {}).get("epoch", 1)), source,
        payload.get("thread_id"),
    ], separators=(",", ":"))
    numeric = (
        "raw_input_tokens", "cached_input_tokens", "noncached_input_tokens",
        "cache_write_input_tokens", "output_tokens", "reasoning_tokens",
        "model_requests", "tool_actions",
    )
    current = {field: _number(payload.get(field)) for field in numeric}
    current["model_requests_measured"] = bool(payload.get("model_requests_measured"))
    baseline = document["streams"].get(key)
    if not isinstance(baseline, dict) or any(current[field] < _number(baseline.get(field)) for field in numeric):
        baseline = current
        document["streams"][key] = baseline
        atomic_json(path, document)
    adjusted = dict(payload)
    adjusted.pop("record_id", None)
    for field in numeric:
        adjusted[field] = max(0, current[field] - _number(baseline.get(field)))
    adjusted["model_requests_measured"] = bool(current["model_requests_measured"] and baseline.get("model_requests_measured"))
    adjusted["cumulative"] = True
    return adjusted


def read(root: Path | str) -> tuple[list[dict[str, Any]], list[str]]:
    path = _ledger(root)
    if not path.exists():
        return [], []
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    with path.open("rb") as handle:
        for index, raw in enumerate(handle, 1):
            if not raw.endswith(b"\n"):
                errors.append(f"partial telemetry tail at line {index}")
                break
            try:
                item = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                errors.append(f"invalid telemetry record at line {index}")
                break
            if item.get("schema") == SCHEMA and item.get("record_id"):
                records.append(item)
    return records, errors


def ingest(root: Path | str, state: Mapping[str, Any], payloads: Iterable[Mapping[str, Any]], *, source: str) -> int:
    ledger = _ledger(root)
    existing, ledger_errors = read(root)
    if ledger_errors:
        raise TelemetryError(f"telemetry ledger requires repair before append: {ledger_errors[0]}")
    normalized = [normalize(item, state, source=source) for item in payloads]
    context = state.get("context") or {}
    if not context.get("thread_id"):
        task_id = state.get("task_id")
        revision = int(state.get("revision", 0))
        epoch = int(context.get("epoch", 1))
        relevant = [
            item for item in [*existing, *normalized]
            if item.get("role") == "PRODUCTIVE"
            and item.get("task_id") == task_id
            and int(item.get("revision", 0)) == revision
            and int(item.get("epoch", 0)) == epoch
        ]
        bindings = {str(item.get("thread_id") or "<UNBOUND>") for item in relevant}
        if len(bindings) > 1:
            raise TelemetryError("multiple productive threads cannot be bound to one unrolled epoch")
    seen = {
        (
            item.get("task_id"), int(item.get("revision", 0)), int(item.get("epoch", 0)),
            item.get("source"), item.get("record_id"),
        )
        for item in existing
    }
    fresh = [
        item for item in normalized
        if (item["task_id"], int(item["revision"]), int(item["epoch"]), item["source"], item["record_id"]) not in seen
    ]
    if not fresh:
        return 0
    with ledger.open("ab") as handle:
        for item in fresh:
            handle.write((json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    return len(fresh)


def _without_current_epoch_coverage(
    result: dict[str, Any],
    state: Mapping[str, Any],
    *,
    rollover_requested: bool = False,
) -> dict[str, Any]:
    """Retain ledger facts but never claim live coverage for a blocked rollover."""
    if rollover_requested or int((state.get("context") or {}).get("epoch", 1)) > 1:
        result["current_epoch_measurement"] = "UNMEASURED"
        result["current_epoch_requests_measurement"] = "UNMEASURED"
        result["current_epoch_context_window_measurement"] = "UNMEASURED"
    return result


def auto_refresh(
    root: Path | str,
    state: Mapping[str, Any],
    *,
    rollover_thread_id: str | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    selected: str | None = None
    for variable, source in ENV_SOURCES:
        raw = os.environ.get(variable)
        if not raw:
            continue
        selected = source
        try:
            source_path = Path(raw).expanduser().resolve()
            if not source_path.is_file():
                raise TelemetryError(f"source file does not exist: {source_path}")
            payloads = _load_source(source_path, source)
            payloads = [
                _apply_cumulative_baseline(root, state, item, source) if item.get("cumulative") else item
                for item in payloads
            ]
            count = ingest(root, state, payloads, source=source)
            result = summarize(root, state)
            result.update({
                "adapter": source,
                "ingested": count,
                "adapter_failures": failures,
                "binding_status": "CONFIGURED_SOURCE",
                "binding_reason": variable,
                "telemetry_binding": {
                    "status": "CONFIGURED_SOURCE",
                    "reason": variable,
                    "source": source,
                    "session_id": None,
                },
            })
            return result
        except Exception as exc:
            failures.append(f"{source}: {exc}")
    if selected:
        result = summarize(root, state)
        if result["status"] == "UNMEASURED":
            result["status"] = "ADAPTER_BLOCKED"
        result.update({
            "adapter": selected,
            "ingested": 0,
            "adapter_failures": failures,
            "binding_status": "CONFIGURED_SOURCE",
            "binding_reason": "ADAPTER_BLOCKED",
            "telemetry_binding": {
                "status": "CONFIGURED_SOURCE",
                "reason": "ADAPTER_BLOCKED",
                "source": selected,
                "session_id": None,
            },
        })
        return _without_current_epoch_coverage(
            result,
            state,
        )

    try:
        discovery = discover_desktop_session(
            root,
            state,
            rollover_thread_id=rollover_thread_id,
        )
    except Exception as exc:
        result = summarize(root, state)
        if result["status"] == "UNMEASURED":
            result["status"] = "ADAPTER_BLOCKED"
        result.update({
            "adapter": DESKTOP_SOURCE,
            "ingested": 0,
            "adapter_failures": [f"{DESKTOP_SOURCE}: {exc}"],
            "binding_status": "TELEMETRY_UNBOUND",
            "binding_reason": "ADAPTER_BLOCKED",
            "telemetry_binding": {
                "status": "TELEMETRY_UNBOUND",
                "reason": "ADAPTER_BLOCKED",
                "source": DESKTOP_SOURCE,
                "session_id": None,
            },
        })
        return _without_current_epoch_coverage(
            result,
            state,
        )

    if discovery["status"] != "BOUND":
        result = summarize(root, state)
        if result["status"] == "UNMEASURED" and discovery.get("reason") in {"AMBIGUOUS", "PREVIOUS_EPOCH_SESSION"}:
            result["status"] = "ADAPTER_BLOCKED"
        result.update({
            "adapter": DESKTOP_SOURCE if discovery.get("reason") == "AMBIGUOUS" else "NONE",
            "ingested": 0,
            "adapter_failures": [],
            "binding_status": "TELEMETRY_UNBOUND",
            "binding_reason": discovery.get("reason"),
            "telemetry_binding": {
                "status": "TELEMETRY_UNBOUND",
                "reason": discovery.get("reason"),
                "source": DESKTOP_SOURCE,
                "session_id": None,
                "candidates": discovery.get("candidates") or [],
            },
        })
        return _without_current_epoch_coverage(
            result,
            state,
            rollover_requested=(
                rollover_thread_id is not None
                and discovery.get("reason") in {"PREVIOUS_EPOCH_SESSION", "INVALID_EXPECTED_CONTINUATION"}
            ),
        )

    binding = discovery["binding"]
    binding_view = {
        "status": "BOUND",
        "reason": discovery.get("reason"),
        "source": DESKTOP_SOURCE,
        "session_id": binding.get("session_id"),
        "path": binding.get("path"),
        "task_id": binding.get("task_id"),
        "revision": binding.get("revision"),
        "epoch": binding.get("epoch"),
        "epoch_id": binding.get("epoch_id"),
        "association": binding.get("association", ROOT_USER_ASSOCIATION),
        "parent_session_id": binding.get("parent_session_id"),
    }
    if not discovery.get("available"):
        result = summarize(root, state)
        binding_view["reason"] = "SOURCE_UNAVAILABLE"
        result.update({
            "adapter": DESKTOP_SOURCE,
            "ingested": 0,
            "adapter_failures": [],
            "binding_status": "BOUND",
            "binding_reason": "SOURCE_UNAVAILABLE",
            "telemetry_binding": binding_view,
        })
        return _without_current_epoch_coverage(
            result,
            state,
        )
    try:
        inspected = inspect_desktop_session(binding["path"], expected_session_id=binding["session_id"])
        if not _bound_stream_matches_association(root, inspected, binding, state):
            raise TelemetryError("bound Desktop source no longer satisfies its association proof")
        if _desktop_header_fingerprint(
            inspected,
            include_fork_parent="association" in binding,
        ) != binding.get("header_fingerprint"):
            raise TelemetryError("bound Desktop source header identity changed")
        payload = _desktop_bound_usage(inspected, binding, state)
        payloads = [payload] if payload else []
        count = ingest(root, state, payloads, source=DESKTOP_SOURCE)
        result = summarize(root, state)
        warnings = ["partial Desktop telemetry tail ignored"] if inspected.get("partial_tail") else []
        result.update({
            "adapter": DESKTOP_SOURCE,
            "ingested": count,
            "adapter_failures": [],
            "adapter_warnings": warnings,
            "binding_status": "BOUND",
            "binding_reason": discovery.get("reason"),
            "telemetry_binding": binding_view,
        })
        return result
    except Exception as exc:
        result = summarize(root, state)
        if result["status"] == "UNMEASURED":
            result["status"] = "ADAPTER_BLOCKED"
        result.update({
            "adapter": DESKTOP_SOURCE,
            "ingested": 0,
            "adapter_failures": [f"{DESKTOP_SOURCE}: {exc}"],
            "binding_status": "BOUND",
            "binding_reason": "ADAPTER_BLOCKED",
            "telemetry_binding": {**binding_view, "reason": "ADAPTER_BLOCKED"},
        })
        return _without_current_epoch_coverage(
            result,
            state,
        )


def summarize(root: Path | str, state: Mapping[str, Any]) -> dict[str, Any]:
    records, errors = read(root)
    records = [
        item for item in records
        if item.get("task_id") == state.get("task_id") and int(item.get("revision", 0)) == int(state.get("revision", 0))
    ]
    if not records:
        return {
            "status": "UNMEASURED",
            "source": "NONE",
            "records": 0,
            "productive_model_requests": 0,
            "productive_raw_input_tokens": 0,
            "productive_cached_input_tokens": 0,
            "productive_cache_write_input_tokens": 0,
            "productive_noncached_input_tokens": 0,
            "productive_cached_input_measurement": "UNMEASURED",
            "productive_cache_write_input_measurement": "UNMEASURED",
            "productive_noncached_input_measurement": "UNMEASURED",
            "productive_output_tokens": 0,
            "productive_reasoning_tokens": 0,
            "control_model_requests": 0,
            "control_tool_actions": 0,
            "control_raw_input_tokens": 0,
            "control_cached_input_tokens": 0,
            "control_cache_write_input_tokens": 0,
            "control_noncached_input_tokens": 0,
            "control_output_tokens": 0,
            "control_reasoning_tokens": 0,
            "max_projected_prompt_tokens": 0,
            "rollovers": max(0, int((state.get("context") or {}).get("epoch", 1)) - 1),
            "measurement_coverage": "UNMEASURED",
            "ledger_errors": errors,
            "current_epoch_model_requests": 0,
            "current_epoch_latest_projected_prompt_tokens": 0,
            "current_epoch_max_projected_prompt_tokens": 0,
            "current_epoch_measurement": "UNMEASURED",
            "current_epoch_peak_measurement": "UNMEASURED",
            "current_epoch_requests_measurement": "UNMEASURED",
            "current_epoch_model_context_window": 0,
            "current_epoch_context_window_measurement": "UNMEASURED",
        }
    productive = [item for item in records if item.get("role") == "PRODUCTIVE"]
    control = [item for item in records if item.get("role") == "CONTROL"]
    current_epoch = int((state.get("context") or {}).get("epoch", 1))
    current_records = [item for item in productive if int(item.get("epoch", 0)) == current_epoch]
    latest_current_record = current_records[-1] if current_records else None
    current_window_records = [
        item for item in current_records
        if item.get("model_context_window_measured") and _number(item.get("model_context_window")) > 0
    ]

    def total(items: list[dict[str, Any]], field: str) -> int:
        delta = [item for item in items if not item.get("cumulative")]
        cumulative = [item for item in items if item.get("cumulative")]
        grouped: dict[tuple[str, str, int, str], int] = {}
        for item in cumulative:
            key = (str(item.get("source")), str(item.get("thread_id")), int(item.get("epoch", 0)), str(item.get("role")))
            grouped[key] = max(grouped.get(key, 0), _number(item.get(field)))
        return sum(_number(item.get(field)) for item in delta) + sum(grouped.values())

    def prompt_peak(item: Mapping[str, Any]) -> int:
        values = []
        if item.get("projected_prompt_tokens_measured"):
            values.append(_number(item.get("projected_prompt_tokens")))
        if item.get("peak_prompt_tokens_measured"):
            values.append(_number(item.get("peak_prompt_tokens")))
        return max(values, default=0)

    return {
        "status": ("MEASURED" if not errors else "PARTIAL") if productive else "UNMEASURED",
        "source": "+".join(sorted({str(item.get("source")) for item in records})),
        "records": len(records),
        "productive_model_requests": total(productive, "model_requests"),
        "productive_raw_input_tokens": total(productive, "raw_input_tokens"),
        "productive_cached_input_tokens": total(productive, "cached_input_tokens"),
        "productive_cache_write_input_tokens": total(productive, "cache_write_input_tokens"),
        "productive_noncached_input_tokens": total(productive, "noncached_input_tokens"),
        "productive_cached_input_measurement": (
            "MEASURED" if productive and productive[-1].get("cached_input_tokens_measured") else "UNMEASURED"
        ),
        "productive_cache_write_input_measurement": (
            "MEASURED" if productive and productive[-1].get("cache_write_input_tokens_measured") else "UNMEASURED"
        ),
        "productive_noncached_input_measurement": (
            "MEASURED" if productive and productive[-1].get("noncached_input_tokens_measured") else "UNMEASURED"
        ),
        "productive_output_tokens": total(productive, "output_tokens"),
        "productive_reasoning_tokens": total(productive, "reasoning_tokens"),
        "control_model_requests": total(control, "model_requests"),
        "control_tool_actions": total(control, "tool_actions"),
        "control_raw_input_tokens": total(control, "raw_input_tokens"),
        "control_cached_input_tokens": total(control, "cached_input_tokens"),
        "control_cache_write_input_tokens": total(control, "cache_write_input_tokens"),
        "control_noncached_input_tokens": total(control, "noncached_input_tokens"),
        "control_output_tokens": total(control, "output_tokens"),
        "control_reasoning_tokens": total(control, "reasoning_tokens"),
        "max_projected_prompt_tokens": max((prompt_peak(item) for item in productive), default=0),
        "rollovers": max(0, int((state.get("context") or {}).get("epoch", 1)) - 1),
        "measurement_coverage": (
            ("MEASURED" if not errors else "PARTIAL")
            if productive
            else ("PRODUCTIVE_UNMEASURED_CONTROL_MEASURED" if not errors else "PRODUCTIVE_UNMEASURED_CONTROL_PARTIAL")
        ),
        "ledger_errors": errors,
        "current_epoch_model_requests": total(current_records, "model_requests"),
        "current_epoch_latest_projected_prompt_tokens": (
            _number(latest_current_record.get("projected_prompt_tokens"))
            if latest_current_record and latest_current_record.get("projected_prompt_tokens_measured") else 0
        ),
        "current_epoch_max_projected_prompt_tokens": max(
            (prompt_peak(item) for item in current_records), default=0
        ),
        "current_epoch_measurement": (
            "MEASURED"
            if latest_current_record and latest_current_record.get("projected_prompt_tokens_measured")
            else "UNMEASURED"
        ),
        "current_epoch_peak_measurement": (
            "MEASURED"
            if any(
                item.get("peak_prompt_tokens_measured") or item.get("projected_prompt_tokens_measured")
                for item in current_records
            )
            else "UNMEASURED"
        ),
        "current_epoch_requests_measurement": "MEASURED" if any(item.get("model_requests_measured") for item in current_records) else "UNMEASURED",
        "current_epoch_model_context_window": (
            _number(current_window_records[-1].get("model_context_window"))
            if current_window_records else 0
        ),
        "current_epoch_context_window_measurement": "MEASURED" if current_window_records else "UNMEASURED",
    }
