"""Pure projected-headroom governor with honest Desktop enforcement semantics."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .model import KernelError


POLICY_NAME = "PROJECTED_HEADROOM_ONE_CHAT_HYBRID"
DEFAULT_POLICY: dict[str, Any] = {
    "policy_name": POLICY_NAME,
    "warning_percent": 50,
    "compact_percent": 70,
    "rollover_percent": 80,
    "hard_stop_reserve_percent": 10,
    "hard_stop_min_reserve_tokens": 25_000,
    "known_payload_output_reserve_tokens": 0,
    "context_window_tokens": None,
    # This is a policy fallback, not a claim about the active model.  It keeps
    # missing-window operation no weaker than the former v1.22 absolute cap.
    "fallback_context_window_tokens": 128_000,
    "enforcement": "SUPERVISORY",
}

LEGACY_POLICY_FIELDS = {
    "compact_prompt_tokens",
    "rollover_prompt_tokens",
    "requests_per_epoch",
    "absolute_prompt_cap",
}
COMPACTION_FAILURES = {"UNAVAILABLE", "ATTEMPTED_INEFFECTIVE"}
COMPACTION_STATUSES = {"NOT_REPORTED", "NOT_ATTEMPTED", *COMPACTION_FAILURES}
PERSISTENT_POST_COMPACTION_SIGNALS = {
    "VERIFIED_STALE_CONTEXT_CONTRADICTION",
    "MATERIAL_TASK_OUTCOME_RESET",
    "DEMONSTRABLE_STATE_LOSS",
}


def _usage_value(value: Any, *, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise KernelError(f"context usage {field} must be a non-negative integer")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise KernelError(f"context usage {field} must be a non-negative integer") from exc
    if result < 0:
        raise KernelError(f"context usage {field} must be a non-negative integer")
    return result


def _positive_usage_value(value: Any, *, field: str) -> int | None:
    result = _usage_value(value, field=field)
    if result is not None and result <= 0:
        raise KernelError(f"context usage {field} must be a positive integer")
    return result


def _policy_integer(policy: dict[str, Any], field: str, *, positive: bool = True) -> int:
    raw = policy.get(field)
    if isinstance(raw, bool):
        adjective = "positive" if positive else "non-negative"
        raise KernelError(f"context policy {field} must be a {adjective} integer")
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        adjective = "positive" if positive else "non-negative"
        raise KernelError(f"context policy {field} must be a {adjective} integer") from exc
    if (positive and value <= 0) or (not positive and value < 0):
        adjective = "positive" if positive else "non-negative"
        raise KernelError(f"context policy {field} must be a {adjective} integer")
    policy[field] = value
    return value


def _validated_policy(value: Mapping[str, Any]) -> dict[str, Any]:
    supplied = dict(value)
    obsolete = sorted(LEGACY_POLICY_FIELDS.intersection(supplied))
    if obsolete:
        raise KernelError(
            "obsolete fixed context policy keys are not supported by "
            f"{POLICY_NAME}: {', '.join(obsolete)}"
        )
    policy = {**DEFAULT_POLICY, **supplied}
    if str(policy.get("policy_name") or "") != POLICY_NAME:
        raise KernelError(f"context policy_name must be {POLICY_NAME}")

    fixed_percentages = {
        "warning_percent": 50,
        "compact_percent": 70,
        "rollover_percent": 80,
        "hard_stop_reserve_percent": 10,
    }
    for field, required in fixed_percentages.items():
        if _policy_integer(policy, field) != required:
            raise KernelError(f"context policy {field} must be {required} for {POLICY_NAME}")
    if _policy_integer(policy, "hard_stop_min_reserve_tokens") != 25_000:
        raise KernelError(f"context policy hard_stop_min_reserve_tokens must be 25000 for {POLICY_NAME}")
    _policy_integer(policy, "known_payload_output_reserve_tokens", positive=False)
    fallback = _policy_integer(policy, "fallback_context_window_tokens")
    if fallback > int(DEFAULT_POLICY["fallback_context_window_tokens"]):
        raise KernelError("context policy fallback_context_window_tokens exceeds the conservative kernel fallback")

    configured_window = policy.get("context_window_tokens")
    if configured_window is not None:
        if isinstance(configured_window, bool):
            raise KernelError("context policy context_window_tokens must be a positive integer or null")
        try:
            configured_window = int(configured_window)
        except (TypeError, ValueError) as exc:
            raise KernelError("context policy context_window_tokens must be a positive integer or null") from exc
        if configured_window <= 0:
            raise KernelError("context policy context_window_tokens must be a positive integer or null")
        policy["context_window_tokens"] = configured_window

    enforcement = str(policy.get("enforcement", "SUPERVISORY")).upper()
    if enforcement not in {"SUPERVISORY", "BOUNDARY"}:
        raise KernelError("Desktop candidate supports only SUPERVISORY or BOUNDARY context enforcement")
    policy["enforcement"] = enforcement
    return policy


def load_policy(root_or_package: Path | str | None = None) -> dict[str, Any]:
    policy = dict(DEFAULT_POLICY)
    if root_or_package is None:
        return _validated_policy(policy)
    root = Path(root_or_package)
    candidates = [root / ".buildos-policy.json", Path(__file__).resolve().parents[1] / "config" / "policy.json"]
    for candidate in candidates:
        if candidate.is_file():
            try:
                raw = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise KernelError(f"context policy is unreadable: {candidate}") from exc
            if not isinstance(raw, dict):
                raise KernelError(f"context policy must be a JSON object: {candidate}")
            selected = raw.get("context_governor", raw)
            if not isinstance(selected, dict):
                raise KernelError(f"context_governor must be a JSON object: {candidate}")
            policy.update(selected)
            break
    return _validated_policy(policy)


def _threshold(window: int, percent: int) -> int:
    """Return ceil(window * percent / 100) using integer arithmetic."""
    return (window * percent + 99) // 100


def _explicit_bool(value: Any, *, field: str) -> bool:
    if value is None:
        return False
    if not isinstance(value, bool):
        raise KernelError(f"context usage {field} must be boolean")
    return value


def decide(usage: Mapping[str, Any] | None, policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return one orthogonal signal; never mutate lifecycle state.

    The current/latest prompt drives the action. Historical peak and request
    count remain visible evidence and can never independently change it.
    """
    policy = _validated_policy(dict(policy or {}))
    usage = dict(usage or {})

    raw_prompt = usage.get("projected_prompt_tokens", usage.get("latest_request_input_tokens"))
    prompt = _usage_value(raw_prompt, field="projected_prompt_tokens")
    raw_peak = usage.get("peak_prompt_tokens", usage.get("historical_peak_prompt_tokens"))
    supplied_peak = _usage_value(raw_peak, field="peak_prompt_tokens")
    peak = max(value for value in (prompt, supplied_peak, 0) if value is not None)
    raw_requests = usage.get("requests_in_epoch")
    requests = _usage_value(raw_requests, field="requests_in_epoch")

    raw_window = usage.get("model_context_window", usage.get("runtime_context_window_tokens"))
    runtime_window = _positive_usage_value(raw_window, field="model_context_window")
    if runtime_window is not None:
        window = runtime_window
        window_source = "RUNTIME_SURFACE"
        window_measurement = "MEASURED"
    elif policy.get("context_window_tokens") is not None:
        window = int(policy["context_window_tokens"])
        window_source = "POLICY_CONFIG"
        window_measurement = "CONFIGURED"
    else:
        window = int(policy["fallback_context_window_tokens"])
        window_source = "CONSERVATIVE_FALLBACK"
        window_measurement = "FALLBACK"

    warning = _threshold(window, int(policy["warning_percent"]))
    compact = _threshold(window, int(policy["compact_percent"]))
    rollover = _threshold(window, int(policy["rollover_percent"]))
    reserve_candidates = [
        _threshold(window, int(policy["hard_stop_reserve_percent"])),
        int(policy["hard_stop_min_reserve_tokens"]),
        int(policy["known_payload_output_reserve_tokens"]),
    ]
    usage_reserve = _usage_value(
        usage.get(
            "known_payload_output_reserve_tokens",
            usage.get("known_next_payload_or_output_reserve"),
        ),
        field="known_payload_output_reserve_tokens",
    )
    if usage_reserve is not None:
        reserve_candidates.append(usage_reserve)
    safety_reserve = max(reserve_candidates)
    hard_stop = max(0, window - safety_reserve)

    compaction_status = str(usage.get("compaction_status") or "NOT_REPORTED").strip().upper()
    if compaction_status not in COMPACTION_STATUSES:
        raise KernelError(
            "context usage compaction_status must be NOT_ATTEMPTED, UNAVAILABLE, or ATTEMPTED_INEFFECTIVE"
        )
    persistent_loss = str(usage.get("persistent_post_compaction_loss") or "").strip().upper() or None
    if persistent_loss is not None and persistent_loss not in PERSISTENT_POST_COMPACTION_SIGNALS:
        raise KernelError("context usage persistent_post_compaction_loss is not an allowed verified signal")
    evidence_reference = str(usage.get("compaction_evidence") or "").strip() or None
    if (compaction_status in COMPACTION_FAILURES or persistent_loss is not None) and evidence_reference is None:
        raise KernelError("compaction failure or persistent post-compaction loss requires an evidence reference")

    compact_failure_evidenced = compaction_status in COMPACTION_FAILURES and evidence_reference is not None
    persistent_loss_evidenced = persistent_loss is not None and evidence_reference is not None
    threshold_rollover_eligible = bool(
        prompt is not None and prompt >= rollover and compact_failure_evidenced
    )
    rollover_fallback_eligible = threshold_rollover_eligible or persistent_loss_evidenced
    runtime_overflow = _explicit_bool(usage.get("runtime_overflow"), field="runtime_overflow")

    action = "CONTINUE"
    reason = "WITHIN_PROJECTED_HEADROOM"
    if runtime_overflow:
        action = "HARD_STOP"
        reason = "EXPLICIT_RUNTIME_OVERFLOW"
    elif prompt is not None and prompt >= hard_stop:
        action = "HARD_STOP"
        reason = "DYNAMIC_SAFETY_RESERVE"
    elif persistent_loss_evidenced:
        action = "ROLLOVER_REQUIRED"
        reason = "VERIFIED_POST_COMPACTION_STATE_LOSS"
    elif prompt is None:
        action = "CONTINUE_UNMEASURED"
        reason = "CURRENT_PROMPT_UNMEASURED"
    elif threshold_rollover_eligible:
        action = "ROLLOVER_REQUIRED"
        reason = "RARE_COMPACTION_FALLBACK"
    elif prompt >= compact:
        action = "COMPACT_REQUIRED"
        reason = "SAME_CHAT_COMPACTION_THRESHOLD"
    elif prompt >= warning:
        action = "HEADROOM_WARNING"
        reason = "HEADROOM_WARNING"

    enforcement = str(policy.get("enforcement", "SUPERVISORY")).upper()
    return {
        "policy_name": POLICY_NAME,
        "action": action,
        "reason": reason,
        "measurement": "MEASURED" if prompt is not None else "UNMEASURED",
        "projected_prompt_tokens": prompt,
        "latest_prompt_tokens": prompt,
        "peak_prompt_tokens": peak if (prompt is not None or supplied_peak is not None) else None,
        "requests_in_epoch": requests,
        "request_count_role": "OBSERVATIONAL_ONLY",
        "model_context_window": window,
        "context_window_source": window_source,
        "context_window_measurement": window_measurement,
        "known_payload_output_reserve_tokens": max(
            int(policy["known_payload_output_reserve_tokens"]), usage_reserve or 0
        ),
        "safety_reserve_tokens": safety_reserve,
        "thresholds": {
            "warning": warning,
            "compact": compact,
            "rollover": rollover,
            "hard_stop": hard_stop,
        },
        "compaction_status": compaction_status,
        "persistent_post_compaction_loss": persistent_loss,
        "compaction_evidence": evidence_reference,
        "rollover_fallback_eligible": rollover_fallback_eligible,
        "cache_economics": {
            "role": "ADVISORY_ONLY",
            "cached_input_tokens": _usage_value(usage.get("cached_input_tokens"), field="cached_input_tokens"),
            "noncached_input_tokens": _usage_value(usage.get("noncached_input_tokens"), field="noncached_input_tokens"),
            "cache_write_input_tokens": _usage_value(usage.get("cache_write_input_tokens"), field="cache_write_input_tokens"),
        },
        "enforcement": enforcement,
        "hard_interception_guaranteed": False,
        "hard_stop_observed": runtime_overflow or (prompt is not None and prompt >= hard_stop),
    }
