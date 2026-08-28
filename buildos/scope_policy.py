"""Read one explicit repo-local scope policy without retaining task state."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .thin_guard import GuardInputError


FIELDS = {"expected_paths", "strict_paths", "prohibited_paths"}
MAX_BYTES = 64 * 1024


def load_scope_policy(root: Path | str, policy_file: Path | str) -> dict[str, list[str]]:
    repository = Path(root).resolve()
    supplied = Path(policy_file)
    unresolved = supplied if supplied.is_absolute() else repository / supplied
    if unresolved.is_symlink():
        raise GuardInputError("scope policy cannot be a symbolic link")
    target = unresolved.resolve(strict=False)
    try:
        if os.path.commonpath([str(repository), str(target)]) != str(repository):
            raise GuardInputError("scope policy must remain inside the repository")
    except ValueError as exc:
        raise GuardInputError("scope policy must remain inside the repository") from exc
    if target == repository / ".git" or repository / ".git" in target.parents:
        raise GuardInputError("scope policy cannot read Git control state")
    if not target.is_file() or target.is_symlink():
        raise GuardInputError("scope policy must be a regular repository file")
    if target.stat().st_size > MAX_BYTES:
        raise GuardInputError("scope policy exceeds 64 KiB")
    try:
        raw = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GuardInputError("scope policy is unreadable or invalid JSON") from exc
    if not isinstance(raw, dict) or set(raw) - FIELDS:
        raise GuardInputError("scope policy contains unsupported fields")
    result: dict[str, list[str]] = {}
    for field in FIELDS:
        values = raw.get(field, [])
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            raise GuardInputError(f"scope policy {field} must be a list of strings")
        result[field] = list(values)
    return result
