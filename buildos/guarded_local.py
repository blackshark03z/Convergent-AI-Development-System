"""Explicit, near-stateless execution boundary for high-cost local actions."""
from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Iterable, Sequence

from .git_adapter import boundary_snapshot
from .thin_guard import GuardInputError, check


def _command_argv(command: Sequence[str]) -> list[str]:
    argv = [str(value) for value in command]
    if argv[:1] == ["--"]:
        argv = argv[1:]
    if not argv:
        raise GuardInputError("native command argv is required after --")
    if not argv[0] or any("\0" in value for value in argv):
        raise GuardInputError("native command executable is empty or argv contains NUL")
    return argv


def _spawn(root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def execute_high_cost(
    root: Path | str,
    *,
    base: str,
    command: Sequence[str],
    expected_paths: Iterable[str] = (),
    strict_paths: Iterable[str] = (),
    prohibited_paths: Iterable[str] = (),
) -> dict:
    """Check once, re-observe at spawn, then invoke one native local argv."""
    argv = _command_argv(command)
    evaluated = check(
        root,
        base=base,
        boundary="HIGH_COST_LOCAL",
        expected_paths=expected_paths,
        strict_paths=strict_paths,
        prohibited_paths=prohibited_paths,
    )
    evidence = {
        "guard_result": evaluated["result"],
        "reason_codes": evaluated["reason_codes"],
        "evaluated_head": evaluated["observed_head"],
        "evaluated_tree": evaluated["observed_tree"],
        "evaluated_observation_digest": evaluated["observed_state_digest"],
        "pre_spawn_head": None,
        "pre_spawn_tree": None,
        "pre_spawn_observation_digest": None,
        "executed": False,
        "command_exit_code": None,
        "command_stdout": "",
        "command_stderr": "",
    }
    if evaluated["result"] == "BLOCK":
        return evidence

    try:
        pre_spawn = boundary_snapshot(
            evaluated["observed_root"], evaluated["base_commit"],
        )
    except (OSError, RuntimeError) as exc:
        evidence.update({
            "guard_result": "BLOCK",
            "reason_codes": ["BLOCK_STALE_STATE"],
            "pre_spawn_error": str(exc),
        })
        return evidence

    evidence.update({
        "pre_spawn_head": pre_spawn["head"],
        "pre_spawn_tree": pre_spawn["tree"],
        "pre_spawn_observation_digest": pre_spawn["observed_state_digest"],
    })
    if pre_spawn["observed_state_digest"] != evaluated["observed_state_digest"]:
        evidence.update({
            "guard_result": "BLOCK",
            "reason_codes": ["BLOCK_STALE_STATE"],
        })
        return evidence

    completed = _spawn(Path(evaluated["observed_root"]), argv)
    evidence.update({
        "executed": True,
        "command_exit_code": completed.returncode,
        "command_stdout": completed.stdout,
        "command_stderr": completed.stderr,
    })
    return evidence
