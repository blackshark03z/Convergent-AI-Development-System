"""Optional, task-bound telemetry projection.

Telemetry is deliberately outside canonical lifecycle state.  Adapter failure
returns UNMEASURED/ADAPTER_BLOCKED and can never roll back or corrupt a task.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from .store import atomic_json


SCHEMA = "buildos.telemetry.v1"
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
    record = {
        "schema": SCHEMA,
        "task_id": task_id,
        "revision": revision,
        "epoch": payload_epoch,
        "epoch_id": payload.get("epoch_id") or (state.get("context") or {}).get("epoch_id"),
        "thread_id": payload.get("thread_id"),
        "source": source,
        "role": role,
        "raw_input_tokens": _number(payload.get("raw_input_tokens", payload.get("input_tokens"))),
        "cached_input_tokens": _number(payload.get("cached_input_tokens", payload.get("cached_read_tokens"))),
        "noncached_input_tokens": _number(payload.get("noncached_input_tokens")),
        "output_tokens": _number(payload.get("output_tokens")),
        "reasoning_tokens": _number(payload.get("reasoning_tokens")),
        "model_requests": _number(payload.get("model_requests", 0)),
        "model_requests_measured": bool(payload.get("model_requests_measured", "model_requests" in payload)),
        "tool_actions": _number(payload.get("tool_actions")),
        "projected_prompt_tokens": _number(payload.get("projected_prompt_tokens", payload.get("latest_request_input_tokens"))),
        "projected_prompt_tokens_measured": "projected_prompt_tokens" in payload or "latest_request_input_tokens" in payload,
        "cumulative": bool(payload.get("cumulative", False)),
        "observed_at": str(payload.get("observed_at") or _now()),
    }
    if not record["noncached_input_tokens"]:
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
    return {
        "thread_id": params.get("threadId"),
        "raw_input_tokens": total.get("inputTokens", last.get("inputTokens", 0)),
        "cached_input_tokens": total.get("cachedInputTokens", last.get("cachedInputTokens", 0)),
        "output_tokens": total.get("outputTokens", last.get("outputTokens", 0)),
        "reasoning_tokens": total.get("reasoningOutputTokens", last.get("reasoningOutputTokens", 0)),
        "model_requests": params.get("modelRequests"),
        "model_requests_measured": params.get("modelRequests") is not None,
        "turn_id": params.get("turnId"),
        "projected_prompt_tokens": last.get("inputTokens", 0),
        "role": "PRODUCTIVE",
        "cumulative": True,
    }


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
        if configured:
            records = [item for item in records if item.get("thread_id") == configured]
        elif len(threads) > 1:
            raise TelemetryError("multiple unbound Codex threads; refusing to guess active telemetry")
        # Cumulative notifications supersede older values from the same thread.
        if records:
            explicit = [_number(item.get("model_requests")) for item in records if item.get("model_requests_measured")]
            turns = {str(item.get("turn_id")) for item in records if item.get("turn_id")}
            latest = records[-1]
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
    path = Path(root).resolve() / ".buildos" / "runtime" / "telemetry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _baseline_file(root: Path | str) -> Path:
    path = Path(root).resolve() / ".buildos" / "runtime" / "telemetry_baselines.json"
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
        "output_tokens", "reasoning_tokens", "model_requests", "tool_actions",
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


def auto_refresh(root: Path | str, state: Mapping[str, Any]) -> dict[str, Any]:
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
            result.update({"adapter": source, "ingested": count, "adapter_failures": failures})
            return result
        except Exception as exc:
            failures.append(f"{source}: {exc}")
    result = summarize(root, state)
    if failures and result["status"] == "UNMEASURED":
        result["status"] = "ADAPTER_BLOCKED"
    result.update({"adapter": selected or "NONE", "ingested": 0, "adapter_failures": failures})
    return result


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
            "productive_noncached_input_tokens": 0,
            "productive_output_tokens": 0,
            "productive_reasoning_tokens": 0,
            "control_model_requests": 0,
            "control_tool_actions": 0,
            "control_raw_input_tokens": 0,
            "control_noncached_input_tokens": 0,
            "control_output_tokens": 0,
            "control_reasoning_tokens": 0,
            "max_projected_prompt_tokens": 0,
            "rollovers": max(0, int((state.get("context") or {}).get("epoch", 1)) - 1),
            "measurement_coverage": "UNMEASURED",
            "ledger_errors": errors,
            "current_epoch_model_requests": 0,
            "current_epoch_max_projected_prompt_tokens": 0,
            "current_epoch_measurement": "UNMEASURED",
            "current_epoch_requests_measurement": "UNMEASURED",
        }
    productive = [item for item in records if item.get("role") == "PRODUCTIVE"]
    control = [item for item in records if item.get("role") == "CONTROL"]
    current_epoch = int((state.get("context") or {}).get("epoch", 1))
    current_records = [item for item in productive if int(item.get("epoch", 0)) == current_epoch]

    def total(items: list[dict[str, Any]], field: str) -> int:
        delta = [item for item in items if not item.get("cumulative")]
        cumulative = [item for item in items if item.get("cumulative")]
        grouped: dict[tuple[str, str, int, str], int] = {}
        for item in cumulative:
            key = (str(item.get("source")), str(item.get("thread_id")), int(item.get("epoch", 0)), str(item.get("role")))
            grouped[key] = max(grouped.get(key, 0), _number(item.get(field)))
        return sum(_number(item.get(field)) for item in delta) + sum(grouped.values())

    return {
        "status": ("MEASURED" if not errors else "PARTIAL") if productive else "UNMEASURED",
        "source": "+".join(sorted({str(item.get("source")) for item in records})),
        "records": len(records),
        "productive_model_requests": total(productive, "model_requests"),
        "productive_raw_input_tokens": total(productive, "raw_input_tokens"),
        "productive_noncached_input_tokens": total(productive, "noncached_input_tokens"),
        "productive_output_tokens": total(productive, "output_tokens"),
        "productive_reasoning_tokens": total(productive, "reasoning_tokens"),
        "control_model_requests": total(control, "model_requests"),
        "control_tool_actions": total(control, "tool_actions"),
        "control_raw_input_tokens": total(control, "raw_input_tokens"),
        "control_noncached_input_tokens": total(control, "noncached_input_tokens"),
        "control_output_tokens": total(control, "output_tokens"),
        "control_reasoning_tokens": total(control, "reasoning_tokens"),
        "max_projected_prompt_tokens": max((_number(item.get("projected_prompt_tokens")) for item in productive), default=0),
        "rollovers": max(0, int((state.get("context") or {}).get("epoch", 1)) - 1),
        "measurement_coverage": (
            ("MEASURED" if not errors else "PARTIAL")
            if productive
            else ("PRODUCTIVE_UNMEASURED_CONTROL_MEASURED" if not errors else "PRODUCTIVE_UNMEASURED_CONTROL_PARTIAL")
        ),
        "ledger_errors": errors,
        "current_epoch_model_requests": total(current_records, "model_requests"),
        "current_epoch_max_projected_prompt_tokens": max((_number(item.get("projected_prompt_tokens")) for item in current_records), default=0),
        "current_epoch_measurement": "MEASURED" if any(item.get("projected_prompt_tokens_measured") for item in current_records) else "UNMEASURED",
        "current_epoch_requests_measurement": "MEASURED" if any(item.get("model_requests_measured") for item in current_records) else "UNMEASURED",
    }
