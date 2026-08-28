"""Near-stateless Git/scope checks for consequential boundaries."""
from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path
from typing import Iterable

from .git_adapter import boundary_snapshot


class GuardInputError(ValueError):
    """The caller did not supply a safe, explicit guard input."""


_DRIVE = re.compile(r"^[A-Za-z]:")
_UNMERGED = {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}


def _patterns(values: Iterable[str], *, label: str) -> list[str]:
    result: list[str] = []
    for raw in values:
        pattern = str(raw).strip().replace("\\", "/")
        while pattern.startswith("./"):
            pattern = pattern[2:]
        parts = pattern.split("/")
        if (
            not pattern
            or pattern.startswith("/")
            or _DRIVE.match(pattern)
            or any(part in {"", ".", ".."} for part in parts)
            or parts[0].casefold() == ".git"
        ):
            raise GuardInputError(f"{label} must be a safe repo-relative pattern: {raw}")
        if pattern not in result:
            result.append(pattern)
    return result


def _matches(path: str, pattern: str, *, case_insensitive: bool) -> bool:
    normalized_path = path.replace("\\", "/")
    normalized_pattern = pattern.replace("\\", "/")
    if case_insensitive:
        normalized_path = normalized_path.casefold()
        normalized_pattern = normalized_pattern.casefold()
    prefix = normalized_pattern.rstrip("/")
    return (
        fnmatch.fnmatchcase(normalized_path, normalized_pattern)
        or normalized_path == prefix
        or normalized_path.startswith(prefix + "/")
    )


def _change_kinds(observed: dict, path: str) -> list[str]:
    kinds: list[str] = []
    for label, field in (
        ("COMMITTED", "committed_paths"),
        ("DIRTY", "dirty_paths"),
        ("DELETION", "deleted_paths"),
        ("TYPE_CHANGE", "type_changed_paths"),
        ("CONTROL", "changed_control_paths"),
    ):
        if path in observed[field]:
            kinds.append(label)
    return kinds


def check(
    root: Path | str,
    *,
    base: str,
    boundary: str,
    expected_paths: Iterable[str] = (),
    strict_paths: Iterable[str] = (),
    prohibited_paths: Iterable[str] = (),
) -> dict:
    """Derive PASS/WARN/BLOCK from the current repository and scope policy."""
    boundary_name = str(boundary).strip().upper()
    if not boundary_name:
        raise GuardInputError("boundary is required")
    expected = _patterns(expected_paths, label="expected path")
    strict = _patterns(strict_paths, label="strict path")
    prohibited = _patterns(prohibited_paths, label="prohibited path")
    observed = boundary_snapshot(root, base)
    changed = observed["changed_paths"]
    case_insensitive = observed["case_insensitive_paths"]

    blocking: list[dict] = []
    warnings: list[dict] = []
    relation = observed["relation_to_base"]
    if relation not in {"SAME", "DESCENDANT"}:
        blocking.append({
            "reason_code": "BASE_NOT_ANCESTOR",
            "relation_to_base": relation,
        })

    for path in observed["changed_control_paths"]:
        blocking.append({
            "reason_code": "CONTROL_PATH_CHANGED",
            "path": path,
            "change_kinds": _change_kinds(observed, path),
        })

    for entry in observed["dirty_entries"]:
        if entry["status"] in _UNMERGED:
            blocking.append({
                "reason_code": "UNMERGED_GIT_STATE",
                "path": entry["path"],
                "status": entry["status"],
            })

    for path in changed:
        kinds = _change_kinds(observed, path)
        if any(_matches(path, pattern, case_insensitive=case_insensitive) for pattern in prohibited):
            blocking.append({
                "reason_code": "PROHIBITED_PATH_CHANGED",
                "path": path,
                "change_kinds": kinds,
            })
        if strict and not any(
            _matches(path, pattern, case_insensitive=case_insensitive)
            for pattern in strict
        ):
            blocking.append({
                "reason_code": "STRICT_PATH_VIOLATION",
                "path": path,
                "change_kinds": kinds,
            })
        if expected and not any(
            _matches(path, pattern, case_insensitive=case_insensitive)
            for pattern in expected
        ):
            warnings.append({
                "reason_code": "EXPECTED_PATH_DEVIATION",
                "path": path,
                "change_kinds": kinds,
            })

    blocking_codes = [item["reason_code"] for item in blocking]
    warning_codes = [item["reason_code"] for item in warnings]
    reason_codes = list(dict.fromkeys([*blocking_codes, *warning_codes]))
    result = "BLOCK" if blocking else "WARN" if warnings else "PASS"
    if not reason_codes:
        reason_codes = ["SCOPE_COMPLIANT"]

    return {
        "result": result,
        "reason_codes": reason_codes,
        "boundary": boundary_name,
        "policy": {
            "expected_paths": expected,
            "strict_paths": strict,
            "prohibited_paths": prohibited,
        },
        "observed_root": observed["root"],
        "observed_branch": observed["branch"],
        "base_commit": observed["base"],
        "observed_head": observed["head"],
        "observed_tree": observed["tree"],
        "relation_to_base": relation,
        "dirty": observed["dirty"],
        "observed_state_digest": observed["observed_state_digest"],
        "index_fingerprint": observed["index_fingerprint"],
        "worktree_fingerprint": observed["worktree_fingerprint"],
        "committed_paths": observed["committed_paths"],
        "dirty_paths": observed["dirty_paths"],
        "changed_paths": changed,
        "deleted_paths": observed["deleted_paths"],
        "type_changed_paths": observed["type_changed_paths"],
        "tracked_control_paths": observed["tracked_control_paths"],
        "changed_control_paths": observed["changed_control_paths"],
        "warnings": warnings,
        "blocking_violations": blocking,
    }
