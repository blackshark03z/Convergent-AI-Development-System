"""Harness-neutral execution handoff for CADS.

The handoff compiles only explicit repo-local inputs plus the already-derived
execution route. It does not select or start a coding harness, create a model or
agent, persist lifecycle state, or grant execution authority.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from collections.abc import Iterable

from .execution_route import classify


SCHEMA = "cads-execution-handoff-v1"


class ExecutionHandoffError(ValueError):
    """The requested handoff cannot be compiled safely from repository inputs."""


def _repo_file(root: Path, raw: Path) -> tuple[Path, str]:
    root = root.resolve()
    candidate = raw if raw.is_absolute() else root / raw
    candidate = candidate.resolve()

    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ExecutionHandoffError(
            f"handoff input escapes repository root: {raw}"
        ) from exc

    if not candidate.exists():
        raise ExecutionHandoffError(f"handoff input does not exist: {relative.as_posix()}")
    if not candidate.is_file():
        raise ExecutionHandoffError(f"handoff input is not a file: {relative.as_posix()}")

    return candidate, relative.as_posix()


def compile_handoff(
    root: Path,
    input_paths: Iterable[Path],
    required_properties: Iterable[str] = (),
) -> dict[str, object]:
    """Compile explicit worker inputs without owning execution."""

    requested = list(input_paths)
    if not requested:
        raise ExecutionHandoffError("at least one explicit handoff input is required")

    seen: set[str] = set()
    inputs: list[dict[str, str]] = []
    for raw in requested:
        path, relative = _repo_file(root, Path(raw))
        if relative in seen:
            continue
        seen.add(relative)

        data = path.read_bytes()
        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ExecutionHandoffError(
                f"handoff input must be UTF-8 text: {relative}"
            ) from exc

        inputs.append({
            "path": relative,
            "sha256": hashlib.sha256(data).hexdigest(),
            "content": content,
        })

    route = classify(required_properties)
    return {
        "schema": SCHEMA,
        "result": "PASS",
        "route": route["route"],
        "required_properties": route["required_properties"],
        "inputs": inputs,
        "authority_granted": False,
        "persists_state": False,
        "starts_harness": False,
    }
