"""Pure context governor with honest Desktop enforcement semantics."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .model import KernelError


DEFAULT_POLICY: dict[str, Any] = {
    "compact_prompt_tokens": 40_000,
    "rollover_prompt_tokens": 64_000,
    "requests_per_epoch": 5,
    "absolute_prompt_cap": 128_000,
    "enforcement": "SUPERVISORY",
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


def _validated_policy(value: Mapping[str, Any]) -> dict[str, Any]:
    policy = {**DEFAULT_POLICY, **dict(value)}
    integer_fields = (
        "compact_prompt_tokens", "rollover_prompt_tokens",
        "requests_per_epoch", "absolute_prompt_cap",
    )
    for field in integer_fields:
        raw = policy.get(field)
        if isinstance(raw, bool):
            raise KernelError(f"context policy {field} must be a positive integer")
        try:
            policy[field] = int(raw)
        except (TypeError, ValueError) as exc:
            raise KernelError(f"context policy {field} must be a positive integer") from exc
        if policy[field] <= 0:
            raise KernelError(f"context policy {field} must be a positive integer")
    # Repository policy may tighten the proven field limits, never weaken
    # them.  This prevents a project-local config file from silently turning
    # off the governor that is supposed to supervise it.
    for field in integer_fields:
        if policy[field] > int(DEFAULT_POLICY[field]):
            raise KernelError(f"context policy {field} exceeds the kernel safety maximum")
    if not (
        policy["compact_prompt_tokens"]
        <= policy["rollover_prompt_tokens"]
        <= policy["absolute_prompt_cap"]
    ):
        raise KernelError("context policy thresholds must satisfy compact <= rollover <= absolute")
    enforcement = str(policy.get("enforcement", "SUPERVISORY")).upper()
    if enforcement not in {"SUPERVISORY", "BOUNDARY"}:
        raise KernelError("Desktop candidate supports only SUPERVISORY or BOUNDARY context enforcement")
    policy["enforcement"] = enforcement
    return policy


def load_policy(root_or_package: Path | str | None = None) -> dict[str, Any]:
    policy = dict(DEFAULT_POLICY)
    if root_or_package is None:
        return policy
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


def decide(usage: Mapping[str, Any] | None, policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return one orthogonal signal; never mutate lifecycle state."""
    policy = _validated_policy(dict(policy or {}))
    usage = dict(usage or {})
    raw_prompt = usage.get("projected_prompt_tokens", usage.get("latest_request_input_tokens"))
    raw_requests = usage.get("requests_in_epoch")
    measured = raw_prompt is not None or raw_requests is not None
    measured_prompt = _usage_value(raw_prompt, field="projected_prompt_tokens")
    measured_requests = _usage_value(raw_requests, field="requests_in_epoch")
    prompt = measured_prompt or 0
    requests = measured_requests or 0
    action = "CONTINUE"
    reason = "WITHIN_POLICY"
    if not measured:
        action = "CONTINUE_UNMEASURED"
        reason = "CONTEXT_UNMEASURED"
    elif prompt >= int(policy["absolute_prompt_cap"]):
        action = "HARD_STOP"
        reason = "ABSOLUTE_PROMPT_CAP"
    elif prompt >= int(policy["rollover_prompt_tokens"]):
        action = "ROLLOVER_REQUIRED"
        reason = "FRESH_CONTEXT_THRESHOLD"
    elif requests >= int(policy["requests_per_epoch"]):
        action = "ROLLOVER_REQUIRED"
        reason = "REQUESTS_PER_EPOCH_LIMIT"
    elif prompt >= int(policy["compact_prompt_tokens"]):
        action = "PREPARE_COMPACT"
        reason = "COMPACT_THRESHOLD"
    enforcement = str(policy.get("enforcement", "SUPERVISORY")).upper()
    return {
        "action": action,
        "reason": reason,
        "measurement": "MEASURED" if measured else "UNMEASURED",
        "projected_prompt_tokens": prompt if raw_prompt is not None else None,
        "requests_in_epoch": requests if raw_requests is not None else None,
        "thresholds": {
            "compact": int(policy["compact_prompt_tokens"]),
            "rollover": int(policy["rollover_prompt_tokens"]),
            "requests": int(policy["requests_per_epoch"]),
            "absolute": int(policy["absolute_prompt_cap"]),
        },
        "enforcement": enforcement,
        "hard_interception_guaranteed": False,
        "over_cap_observed": prompt >= int(policy["absolute_prompt_cap"]) if raw_prompt is not None else False,
    }
