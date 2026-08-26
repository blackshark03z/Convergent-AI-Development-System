#!/usr/bin/env python3
"""Fail-closed, provenance-preserving legacy authority retirement bridge."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any
import zipfile


BRIDGE_VERSION = "1.0.1"
TRANSITION_SCHEMA = "buildos.legacy-authority-transition.v1"
ACTIVATION_SCHEMA = "buildos.legacy-authority-activation.v1"
JOURNAL_SCHEMA = "buildos.legacy-authority-journal.v1"
AUTHORITY_SCHEMA = "buildos.execution-authority.v1"
TERMINAL_AUTHORIZATION_SCHEMA = "buildos.legacy-terminal-disposition-authorization.v1"
TERMINAL_AUTHORIZATION_ENV = "BUILDOS_TRUSTED_LEGACY_TERMINAL_DISPOSITION_SHA256"
TERMINAL_DISPOSITION = "TERMINALIZE_BLOCKED_LEGACY_GOAL_FOR_V125_ADOPTION"
ARCHIVE_ROOT = Path(".buildos-legacy") / "archives"
CURRENT_PATH = Path(".buildos") / "control" / "CURRENT"
ACTIVATION_ROOT = Path(".buildos") / "control" / "legacy-bridge-receipts"
AUTHORITY_RECORD = Path(".buildos-authority.json")
LEGACY_ATTRIBUTES = Path(".buildos-legacy") / ".gitattributes"
LEGACY_ATTRIBUTES_BYTES = b"** -text\n"
CANONICAL_EXECUTOR_PATHS = {"scripts/ai.py", "scripts/ai_os.py"}
WORKER_FILES = ("AGENTS.md", "WORKER_INSTRUCTIONS.md", "prompts/03_WORKER.md")
LEGACY_VERSION = re.compile(r"(?i)build\s*os\s*v1\.(?:[0-9]|1[0-9]|20|21)\b")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
SHA256 = re.compile(r"[0-9a-f]{64}")
AUTHORIZATION_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
LIVE_TASK_STATES = {"READY", "ACTIVE", "PAUSED", "BLOCKED"}
TERMINAL_TASK_STATES = {"COMPLETED", "ABORTED"}
TERMINAL_GOAL_STATES = {"COMPLETED", "ABORTED"}
TERMINAL_COMPLETED_NODE_STATES = {"DONE", "DEFERRED"}
FILE_ATTRIBUTE_REPARSE_POINT = 0x400


class BridgeError(RuntimeError):
    """A typed, fail-closed bridge refusal."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def object_hash(value: dict[str, Any], field: str) -> str:
    payload = dict(value)
    payload.pop(field, None)
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def strict_json_loads(payload: str | bytes) -> object:
    def pairs(rows: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in rows:
            if key in result:
                raise ValueError(f"duplicate JSON object key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise ValueError(f"non-finite JSON constant is forbidden: {value}")

    return json.loads(payload, object_pairs_hook=pairs, parse_constant=reject_constant)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = strict_json_loads(path.read_bytes())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise BridgeError(f"JSON_INVALID:{path}:{exc}") from exc
    if not isinstance(value, dict):
        raise BridgeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def atomic_write(path: Path, data: bytes, *, overwrite: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not overwrite and path.exists():
        if path.is_file() and path.read_bytes() == data:
            return
        raise BridgeError(f"IMMUTABLE_PATH_CONFLICT:{path}")
    temp = path.parent / f".{path.name}.{os.getpid()}.{os.urandom(6).hex()}.tmp"
    try:
        with temp.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_text_sha256(content: bytes) -> str:
    text = content.decode("utf-8", errors="strict")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def git(root: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args], text=True, encoding="utf-8",
        errors="replace", capture_output=True, timeout=60,
    )
    if check and completed.returncode:
        raise BridgeError(f"GIT_FAILED:{' '.join(args)}:{completed.stderr.strip()}")
    return completed.stdout.strip()


def validate_identifier(value: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise BridgeError("TRANSITION_ID_INVALID")
    return value


def is_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    attributes = int(getattr(info, "st_file_attributes", 0))
    return path.is_symlink() or bool(attributes & FILE_ATTRIBUTE_REPARSE_POINT)


def reject_indirection(root: Path, path: Path) -> None:
    root = root.resolve()
    try:
        relative = path.absolute().relative_to(root)
    except ValueError as exc:
        raise BridgeError(f"PATH_ESCAPE:{path}") from exc
    current = root
    if is_reparse(current):
        raise BridgeError(f"REPARSE_POINT_FORBIDDEN:{current}")
    for part in relative.parts:
        current = current / part
        if current.exists() and is_reparse(current):
            raise BridgeError(f"REPARSE_POINT_FORBIDDEN:{current}")


def package_identity(package_root: Path) -> dict[str, Any]:
    manifest = read_json(package_root / "PACKAGE_MANIFEST.json")
    package_id = manifest.get("package_id")
    kernel_commit = manifest.get("frozen_kernel_commit")
    kernel_version = manifest.get("frozen_kernel_version")
    lifecycle = manifest.get("project_lifecycle_kit")
    if (
        not isinstance(package_id, str) or not package_id
        or not isinstance(kernel_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", kernel_commit)
        or not isinstance(kernel_version, str) or not kernel_version
        or not isinstance(lifecycle, dict) or not isinstance(lifecycle.get("version"), str)
    ):
        raise BridgeError("PACKAGE_IDENTITY_INVALID")
    return {
        "package_id": package_id,
        "frozen_kernel_commit": kernel_commit,
        "frozen_kernel_version": kernel_version,
        "project_lifecycle_kit_version": lifecycle["version"],
        "bridge_version": BRIDGE_VERSION,
    }


def repository_identity(root: Path, *, require_clean: bool) -> dict[str, Any]:
    root = root.resolve()
    top = Path(git(root, "rev-parse", "--show-toplevel")).resolve()
    if top != root:
        raise BridgeError("ROOT_MUST_BE_GIT_TOPLEVEL")
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if require_clean and status:
        raise BridgeError("DIRTY_REPOSITORY_REFUSED")
    tracked_control = git(root, "ls-files", "--", ".buildos")
    if tracked_control:
        raise BridgeError("TRACKED_BUILDOS_REFUSED")
    if (root / ".buildos").exists():
        reject_indirection(root, root / ".buildos")
    origin = git(root, "remote", "get-url", "origin", check=False)
    roots = sorted(line for line in git(root, "rev-list", "--max-parents=0", "HEAD").splitlines() if line)
    if not roots or any(not re.fullmatch(r"[0-9a-f]{40}", item) for item in roots):
        raise BridgeError("REPOSITORY_ROOT_IDENTITY_INVALID")
    return {
        "origin": origin,
        "root_commits": roots,
        "head": git(root, "rev-parse", "HEAD"),
        "tree": git(root, "rev-parse", "HEAD^{tree}"),
        "branch": git(root, "branch", "--show-current"),
        "clean": not bool(status),
    }


def inventory_file(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    reject_indirection(root, path)
    if not path.is_file():
        raise BridgeError(f"SOURCE_FILE_MISSING:{relative}")
    return {"path": relative, "sha256": sha256_file(path), "size": path.stat().st_size}


def inventory_directory(root: Path, relative: str) -> dict[str, Any]:
    directory = root / relative
    reject_indirection(root, directory)
    if not directory.is_dir():
        raise BridgeError(f"SOURCE_DIRECTORY_MISSING:{relative}")
    files: list[dict[str, Any]] = []
    for path in sorted(directory.rglob("*")):
        reject_indirection(root, path)
        if path.is_dir():
            continue
        if not path.is_file():
            raise BridgeError(f"UNSUPPORTED_SOURCE_ENTRY:{path.relative_to(root).as_posix()}")
        files.append(inventory_file(root, path.relative_to(root).as_posix()))
    return {"path": relative, "kind": "directory", "files": files}


def verify_directory_inventory(root: Path, inventory: dict[str, Any]) -> None:
    observed = inventory_directory(root, str(inventory.get("path", "")))
    if observed != inventory:
        raise BridgeError(f"SOURCE_DIRECTORY_DRIFT:{inventory.get('path')}")


def legacy_executor_signature(content: str) -> str | None:
    """Recognize supported legacy lifecycle entry points, not product basenames."""
    prefix = content[:2_048]
    executable_python = prefix.startswith("#!/usr/bin/env python3")
    kernel = (
        executable_python
        and re.search(r"(?i)Senior AI Build OS v1\.(?:[0-9]|1[0-9]|20|21)\b", prefix) is not None
        and "ACTIVE_TASK.md" in content
        and (
            "GOAL_STATE.json" in content
            or (
                "from goal_support import (" in content
                and "begin_goal" in content
                and "complete_goal" in content
            )
        )
        and "argparse" in content
        and (
            "add_subparsers" in content
            or (
                "from cli_support import build_parser" in content
                and "build_parser().parse_args" in content
            )
        )
    )
    facade = (
        executable_python
        and "Small agent-facing facade over the full ai_os.py kernel" in prefix
        and "ai_os.py" in content
        and "add_subparsers" in content
        and all(command in content for command in ("start", "finish", "status", "next"))
    )
    if kernel:
        return "LEGACY_BUILD_OS_ADMIN_KERNEL"
    if facade:
        return "LEGACY_BUILD_OS_AGENT_FACADE"
    return None


def identify_legacy_executors(root: Path) -> dict[str, list[str]]:
    """Return exact supported authorities and strong-but-unsupported candidates.

    Git archaeology for the supported legacy family contains only scripts/ai.py
    and scripts/ai_os.py. A strong signature elsewhere is refused for explicit
    inspection; an unrelated product file is never retired by basename alone.
    """
    executors: set[str] = set()
    ambiguous: set[str] = set()
    excluded = {
        ".git", ".buildos", ".buildos-legacy", "archive", "archives",
        ".venv", "venv", "node_modules", "site-packages", "__pycache__",
    }
    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        if any(part in excluded for part in relative.parts):
            continue
        name = relative.as_posix()
        if is_reparse(path):
            if name in CANONICAL_EXECUTOR_PATHS or path.name in {"ai.py", "ai_os.py", "buildos.py", "build_os.py"}:
                reject_indirection(root, path)
            continue
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError) as exc:
            if name in CANONICAL_EXECUTOR_PATHS:
                raise BridgeError(f"AMBIGUOUS_LEGACY_EXECUTOR_CANDIDATE:{name}") from exc
            continue
        signature = legacy_executor_signature(content)
        if name in CANONICAL_EXECUTOR_PATHS:
            if signature is None:
                ambiguous.add(name)
            else:
                executors.add(name)
        elif signature is not None:
            ambiguous.add(name)
    return {"executors": sorted(executors), "ambiguous": sorted(ambiguous)}


def encoded_executor_path(root: Path, transition_id: str, relative: str) -> Path:
    return root / transition_path(transition_id) / "encoded-executors" / Path(relative + ".base64")


def field(text: str, label: str) -> str | None:
    match = re.search(rf"(?mi)^\s*(?:-\s*)?{re.escape(label)}\s*:\s*(.*?)\s*$", text)
    return match.group(1).strip() if match else None


def inspect_task(root: Path) -> dict[str, Any]:
    path = root / ".ai" / "ACTIVE_TASK.md"
    if not path.exists():
        return {"status": "ABSENT", "lease_status": "ABSENT", "path": None}
    reject_indirection(root, path)
    text = path.read_text(encoding="utf-8", errors="strict")
    status = field(text, "Task Status")
    lease = field(text, "Lease Status")
    if not status or not lease:
        raise BridgeError("LEGACY_TASK_STATE_MALFORMED")
    status = status.upper()
    lease = lease.upper()
    if status in LIVE_TASK_STATES:
        raise BridgeError(f"LEGACY_TASK_LIVE:{status}")
    if status not in TERMINAL_TASK_STATES:
        raise BridgeError(f"LEGACY_TASK_STATE_UNKNOWN:{status}")
    if lease != "RELEASED":
        raise BridgeError(f"LEGACY_TASK_LEASE_LIVE:{lease}")
    return {"status": status, "lease_status": lease, "path": ".ai/ACTIVE_TASK.md", "sha256": sha256_file(path)}


def inspect_goal(root: Path) -> dict[str, Any]:
    path = root / ".ai" / "GOAL_STATE.json"
    if not path.exists():
        return {"status": "ABSENT", "path": None, "disposition": "NATIVELY_TERMINAL"}
    reject_indirection(root, path)
    goal = read_json(path)
    status = str(goal.get("status", "")).upper()
    if status == "ACTIVE":
        raise BridgeError("LEGACY_GOAL_LIVE:ACTIVE")
    tasks = goal.get("tasks", {})
    if not isinstance(tasks, dict):
        raise BridgeError("LEGACY_GOAL_TASKS_MALFORMED")
    node_states: dict[str, str] = {}
    for node_id, raw in sorted(tasks.items()):
        if not isinstance(node_id, str) or not isinstance(raw, dict):
            raise BridgeError("LEGACY_GOAL_NODE_MALFORMED")
        node_status = str(raw.get("status", "")).upper()
        if not node_status:
            raise BridgeError(f"LEGACY_GOAL_NODE_STATUS_MALFORMED:{node_id}")
        node_states[node_id] = node_status
        if node_status == "ACTIVE":
            raise BridgeError(f"LEGACY_GOAL_NODE_LIVE:{node_id}")
    disposition = "NATIVELY_TERMINAL"
    if status == "BLOCKED":
        disposition = "TERMINAL_DISPOSITION_AUTHORIZATION_REQUIRED"
    elif status not in TERMINAL_GOAL_STATES:
        raise BridgeError(f"LEGACY_GOAL_STATE_UNKNOWN:{status or 'MISSING'}")
    elif status == "COMPLETED":
        unfinished = sorted(
            node_id for node_id, node_status in node_states.items()
            if node_status not in TERMINAL_COMPLETED_NODE_STATES
        )
        if unfinished:
            raise BridgeError(f"LEGACY_COMPLETED_GOAL_HAS_UNFINISHED_NODES:{unfinished}")
    return {
        "status": status,
        "path": ".ai/GOAL_STATE.json",
        "sha256": sha256_file(path),
        "goal_id": goal.get("goal_id"),
        "node_states": node_states,
        "decisions_required": goal.get("decisions_required", []),
        "disposition": disposition,
    }


def decision_bindings(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise BridgeError("LEGACY_GOAL_DECISIONS_MALFORMED")
    result: list[dict[str, Any]] = []
    for index, row in enumerate(value):
        identity: str | None = None
        if isinstance(row, str) and row.strip():
            identity = row.strip()
        elif isinstance(row, dict):
            for key in ("request_id", "decision_id", "id"):
                candidate = row.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    identity = candidate.strip()
                    break
        result.append({
            "index": index,
            "identity": identity,
            "sha256": hashlib.sha256(canonical_bytes(row)).hexdigest(),
        })
    return result


def _exact_object(value: object, *, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise BridgeError(f"{label}_INVALID")
    return value


def validate_terminal_authorization(
    path: Path, repository: dict[str, Any], goal: dict[str, Any], *, require_transport: bool,
) -> tuple[dict[str, Any], bytes, str]:
    candidate = path.absolute()
    if (
        not candidate.is_file()
        or any(part.exists() and is_reparse(part) for part in (candidate, *candidate.parents))
    ):
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_FILE_INVALID")
    raw = read_json(candidate)
    row = _exact_object(
        raw,
        keys={
            "schema", "authorization_id", "repository", "legacy_goal",
            "disposition", "authority", "authorization_sha256",
        },
        label="TERMINAL_DISPOSITION_AUTHORIZATION",
    )
    if row["schema"] != TERMINAL_AUTHORIZATION_SCHEMA:
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_SCHEMA_INVALID")
    authorization_id = str(row["authorization_id"])
    if not AUTHORIZATION_ID.fullmatch(authorization_id):
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_ID_INVALID")
    if row["disposition"] != TERMINAL_DISPOSITION:
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_DISPOSITION_INVALID")
    bound_repository = _exact_object(
        row["repository"],
        keys={"origin", "root_commits", "branch", "head", "tree"},
        label="TERMINAL_DISPOSITION_AUTHORIZATION_REPOSITORY",
    )
    expected_repository = {
        key: repository[key] for key in ("origin", "root_commits", "branch", "head", "tree")
    }
    if bound_repository != expected_repository:
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_REPOSITORY_MISMATCH")
    legacy_goal = _exact_object(
        row["legacy_goal"],
        keys={"goal_id", "path", "status", "sha256", "decision_bindings"},
        label="TERMINAL_DISPOSITION_AUTHORIZATION_GOAL",
    )
    expected_goal = {
        "goal_id": goal.get("goal_id"),
        "path": goal.get("path"),
        "status": goal.get("status"),
        "sha256": goal.get("sha256"),
        "decision_bindings": decision_bindings(goal.get("decisions_required")),
    }
    if not isinstance(expected_goal["goal_id"], str) or not expected_goal["goal_id"]:
        raise BridgeError("LEGACY_GOAL_ID_MALFORMED")
    if legacy_goal != expected_goal:
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_GOAL_MISMATCH")
    authority = _exact_object(
        row["authority"],
        keys={"role", "identity", "authority_reference", "authorized_at"},
        label="TERMINAL_DISPOSITION_AUTHORIZATION_AUTHORITY",
    )
    if authority["role"] != "OWNER":
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_AUTHORITY_INVALID")
    for key, maximum in (("identity", 256), ("authority_reference", 2_048), ("authorized_at", 128)):
        value = authority.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_AUTHORITY_INVALID")
    normalized = {
        "schema": TERMINAL_AUTHORIZATION_SCHEMA,
        "authorization_id": authorization_id,
        "repository": expected_repository,
        "legacy_goal": expected_goal,
        "disposition": TERMINAL_DISPOSITION,
        "authority": {
            "role": "OWNER",
            "identity": authority["identity"].strip(),
            "authority_reference": authority["authority_reference"].strip(),
            "authorized_at": authority["authorized_at"].strip(),
        },
    }
    authorization_sha256 = object_hash({**normalized, "authorization_sha256": ""}, "authorization_sha256")
    if row.get("authorization_sha256") != authorization_sha256:
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_HASH_INVALID")
    normalized["authorization_sha256"] = authorization_sha256
    canonical = canonical_bytes(normalized)
    transport_digest = hashlib.sha256(canonical).hexdigest()
    if require_transport:
        supplied = str(os.environ.get(TERMINAL_AUTHORIZATION_ENV) or "").strip().lower()
        if not SHA256.fullmatch(supplied):
            raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_TRUSTED_BINDING_REQUIRED")
        if not hmac.compare_digest(supplied, transport_digest):
            raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_TRUSTED_BINDING_MISMATCH")
    return normalized, canonical, transport_digest


def inspect_runtime(
    root: Path, *, allow_blocked: bool,
) -> dict[str, Any]:
    runtime = root / ".ai" / "runtime"
    if not runtime.exists():
        return {"present": False, "observations": {}}
    reject_indirection(root, runtime)
    observations: dict[str, Any] = {}
    for name in ("task.json", "goal.json"):
        path = runtime / name
        if not path.exists():
            continue
        value = read_json(path)
        observations[name] = {"sha256": sha256_file(path), "value": value}
        status_keys = ("task_status", "status") if name == "task.json" else ("goal_status", "status")
        supplied = [str(value[key]).upper() for key in status_keys if key in value]
        if not supplied or len(set(supplied)) != 1:
            raise BridgeError(f"LEGACY_RUNTIME_STATUS_MALFORMED:{name}")
        status = supplied[0]
        if name == "task.json":
            lease = str(value.get("lease_status", "")).upper()
            if status in LIVE_TASK_STATES or lease == "CLAIMED":
                raise BridgeError(f"LEGACY_RUNTIME_TASK_LIVE:{status or lease}")
            if status not in TERMINAL_TASK_STATES or lease != "RELEASED":
                raise BridgeError(f"LEGACY_RUNTIME_TASK_MALFORMED:{status}:{lease or 'MISSING'}")
        elif status == "ACTIVE":
            raise BridgeError("LEGACY_RUNTIME_GOAL_LIVE:ACTIVE")
        elif status == "BLOCKED" and not allow_blocked:
            raise BridgeError("LEGACY_RUNTIME_GOAL_BLOCKED_REQUIRES_TERMINAL_DISPOSITION_AUTHORIZATION")
        elif status not in TERMINAL_GOAL_STATES | {"BLOCKED"}:
            raise BridgeError(f"LEGACY_RUNTIME_GOAL_MALFORMED:{status}")
    return {"present": True, "observations": observations}


def inspect_legacy(
    root: Path, package_root: Path, *, allow_blocked: bool = False,
    authorization_path: Path | None = None, authorization_reference: str | None = None,
    require_clean: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    repository = repository_identity(root, require_clean=require_clean)
    if (root / CURRENT_PATH).exists() or (root / AUTHORITY_RECORD).exists():
        raise BridgeError("CURRENT_AUTHORITY_ALREADY_PRESENT")
    existing_archives = root / ARCHIVE_ROOT
    if existing_archives.exists():
        raise BridgeError("LEGACY_BRIDGE_ALREADY_PRESENT")
    executor_inventory = identify_legacy_executors(root)
    executors = executor_inventory["executors"]
    if executor_inventory["ambiguous"]:
        raise BridgeError(
            f"AMBIGUOUS_LEGACY_EXECUTOR_CANDIDATE:{executor_inventory['ambiguous']}"
        )
    conflicting_workers: list[dict[str, Any]] = []
    for relative in WORKER_FILES:
        path = root / relative
        if path.is_file():
            reject_indirection(root, path)
            text = path.read_text(encoding="utf-8", errors="replace")
            if LEGACY_VERSION.search(text):
                conflicting_workers.append(inventory_file(root, relative))
    ai_path = root / ".ai"
    if ai_path.exists() and (not ai_path.is_dir() or is_reparse(ai_path)):
        raise BridgeError("LEGACY_AI_STATE_PATH_INVALID")
    ai_inventory = inventory_directory(root, ".ai") if ai_path.is_dir() else None
    task = inspect_task(root)
    goal = inspect_goal(root)
    terminal_authorization: dict[str, Any] | None = None
    if authorization_reference:
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_REFERENCE_UNSUPPORTED")
    if goal["status"] == "BLOCKED":
        if not allow_blocked:
            raise BridgeError("LEGACY_GOAL_BLOCKED_REQUIRES_TERMINAL_DISPOSITION_AUTHORIZATION")
        if authorization_path is None:
            raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_FILE_REQUIRED")
        terminal_authorization, _, _ = validate_terminal_authorization(
            authorization_path, repository, goal, require_transport=True,
        )
        goal = {**goal, "disposition": "OWNER_AUTHORIZED_TERMINAL_DISPOSITION"}
    elif allow_blocked or authorization_path is not None or authorization_reference:
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_UNEXPECTED")
    runtime = inspect_runtime(root, allow_blocked=terminal_authorization is not None)
    if not executors and ai_inventory is None and not conflicting_workers:
        raise BridgeError("SUPPORTED_LEGACY_AUTHORITY_NOT_FOUND")
    return {
        "eligible": True,
        "repository": repository,
        "package": package_identity(package_root),
        "legacy": {
            "family": "BUILD_OS_V1_16_STYLE",
            "task": task,
            "goal": goal,
            "runtime": runtime,
            "executors": [inventory_file(root, item) for item in executors],
            "worker_instructions": conflicting_workers,
            "ai_state": ai_inventory,
        },
        "terminal_disposition_authorization": terminal_authorization,
    }


def git_common_dir(root: Path) -> Path:
    raw = Path(git(root, "rev-parse", "--git-common-dir"))
    return (root / raw).resolve() if not raw.is_absolute() else raw.resolve()


def journal_paths(root: Path, transition_id: str) -> tuple[Path, Path]:
    base = git_common_dir(root) / "buildos-legacy-bridge" / validate_identifier(transition_id)
    return base / "journal.json", base / "backup"


def save_journal(path: Path, value: dict[str, Any]) -> None:
    value = dict(value)
    value["journal_sha256"] = object_hash(value, "journal_sha256")
    atomic_write(path, canonical_bytes(value))


def load_journal(root: Path, transition_id: str) -> tuple[Path, Path, dict[str, Any]]:
    journal_path, backup = journal_paths(root, transition_id)
    journal = read_json(journal_path)
    if journal.get("schema") != JOURNAL_SCHEMA or journal.get("transition_id") != transition_id:
        raise BridgeError("JOURNAL_IDENTITY_INVALID")
    digest = journal.get("journal_sha256")
    if not isinstance(digest, str) or digest != object_hash(journal, "journal_sha256"):
        raise BridgeError("JOURNAL_HASH_INVALID")
    return journal_path, backup, journal


def parse_replacements(rows: list[str], workers: list[dict[str, Any]], transition_id: str) -> dict[str, dict[str, Any]]:
    supplied: dict[str, bytes] = {}
    for row in rows:
        relative, separator, source = row.partition("=")
        if not separator or relative not in WORKER_FILES:
            raise BridgeError("REPLACEMENT_WORKER_FORMAT_INVALID")
        path = Path(source).resolve()
        if not path.is_file() or is_reparse(path):
            raise BridgeError(f"REPLACEMENT_WORKER_INVALID:{relative}")
        supplied[relative] = path.read_bytes()
    expected = {str(item["path"]) for item in workers}
    if set(supplied) - expected:
        raise BridgeError("REPLACEMENT_WORKER_NOT_CONFLICTING")
    result: dict[str, dict[str, Any]] = {}
    for relative in sorted(expected):
        content = supplied.get(relative)
        if content is None:
            content = (
                "# Execution authority transition\n\n"
                f"Legacy project-local authority was retired by transition `{transition_id}`.\n"
                "The original instructions are preserved in the tracked transition archive.\n"
                "No product or lifecycle mutation is authorized by this notice. Use only the\n"
                "externally enrolled portable package after its authority and activation checks pass.\n"
            ).encode("utf-8")
        text = content.decode("utf-8", errors="strict")
        if LEGACY_VERSION.search(text):
            raise BridgeError(f"REPLACEMENT_WORKER_STILL_CONFLICTS:{relative}")
        result[relative] = {
            "sha256": hashlib.sha256(content).hexdigest(),
            "text_sha256": normalized_text_sha256(content),
            "size": len(content),
            "content_base64": base64.b64encode(content).decode("ascii"),
        }
    return result


def prepare(
    root: Path, package_root: Path, transition_id: str, *, allow_blocked: bool,
    authorization_path: Path | None, authorization_reference: str | None,
    replacement_rows: list[str],
) -> dict[str, Any]:
    transition_id = validate_identifier(transition_id)
    journal_path, backup = journal_paths(root, transition_id)
    if journal_path.exists():
        _, _, existing = load_journal(root, transition_id)
        if existing.get("state") == "TRANSITION_PREPARED":
            return existing
        raise BridgeError("JOURNAL_ALREADY_EXISTS")
    inspected = inspect_legacy(
        root, package_root, allow_blocked=allow_blocked,
        authorization_path=authorization_path,
        authorization_reference=authorization_reference, require_clean=True,
    )
    replacements = parse_replacements(
        replacement_rows, inspected["legacy"]["worker_instructions"], transition_id,
    )
    ai_state = inspected["legacy"]["ai_state"]
    after = repository_identity(root, require_clean=True)
    if after != inspected["repository"]:
        raise BridgeError("REPOSITORY_DRIFT_DURING_PREPARE")
    if ai_state:
        verify_directory_inventory(root, ai_state)
    for item in [*inspected["legacy"]["executors"], *inspected["legacy"]["worker_instructions"]]:
        if inventory_file(root, str(item["path"])) != item:
            raise BridgeError(f"SOURCE_DRIFT_DURING_PREPARE:{item['path']}")
    journal: dict[str, Any] = {
        "schema": JOURNAL_SCHEMA,
        "bridge_version": BRIDGE_VERSION,
        "transition_id": transition_id,
        "state": "TRANSITION_PREPARED",
        "prepared_at": utc_now(),
        "repository": inspected["repository"],
        "package": inspected["package"],
        "legacy": inspected["legacy"],
        "authorization": {
            "blocked_goal_terminal_disposition": inspected["terminal_disposition_authorization"] is not None,
            "schema": (
                inspected["terminal_disposition_authorization"].get("schema")
                if inspected["terminal_disposition_authorization"] else None
            ),
            "authorization_id": (
                inspected["terminal_disposition_authorization"].get("authorization_id")
                if inspected["terminal_disposition_authorization"] else None
            ),
            "authorization_sha256": (
                inspected["terminal_disposition_authorization"].get("authorization_sha256")
                if inspected["terminal_disposition_authorization"] else None
            ),
        },
        "terminal_disposition_authorization": inspected["terminal_disposition_authorization"],
        "worker_replacements": replacements,
    }
    save_journal(journal_path, journal)
    return journal


def git_succeeds(root: Path, *args: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(root), *args], text=True, encoding="utf-8",
        errors="replace", capture_output=True, timeout=60,
    )
    return completed.returncode == 0


def transition_path(transition_id: str) -> Path:
    return ARCHIVE_ROOT / validate_identifier(transition_id)


def receipt_path(root: Path, transition_id: str) -> Path:
    return root / transition_path(transition_id) / "receipt.json"


def archive_path(root: Path, transition_id: str, relative: str) -> Path:
    return root / transition_path(transition_id) / "legacy" / Path(relative)


def ai_archive_path(root: Path, transition_id: str) -> Path:
    return root / transition_path(transition_id) / "legacy-ai.zip"


def terminal_authorization_path(root: Path, transition_id: str) -> Path:
    return root / transition_path(transition_id) / "terminal-disposition-authorization.json"


def ensure_legacy_attributes(root: Path) -> None:
    path = root / LEGACY_ATTRIBUTES
    if path.exists():
        if not path.is_file() or is_reparse(path) or path.read_bytes() != LEGACY_ATTRIBUTES_BYTES:
            raise BridgeError("LEGACY_ARCHIVE_ATTRIBUTES_INVALID")
        return
    atomic_write(path, LEGACY_ATTRIBUTES_BYTES, overwrite=False)


def verify_legacy_attributes(root: Path) -> None:
    path = root / LEGACY_ATTRIBUTES
    if not path.is_file() or is_reparse(path) or path.read_bytes() != LEGACY_ATTRIBUTES_BYTES:
        raise BridgeError("LEGACY_ARCHIVE_ATTRIBUTES_INVALID")


def quarantined_ai_path(root: Path, transition_id: str) -> Path:
    journal, _ = journal_paths(root, transition_id)
    return journal.parent / "retired-ai"


def lock_path(root: Path, transition_id: str) -> Path:
    journal, _ = journal_paths(root, transition_id)
    return journal.parent / "writer.lock"


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except (PermissionError, OSError):
        return True
    return True


class TransitionLock:
    def __init__(self, root: Path, transition_id: str) -> None:
        self.path = lock_path(root, transition_id)
        self.acquired = False

    def __enter__(self) -> "TransitionLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                prior = read_json(self.path)
                pid = int(prior.get("pid", -1))
            except (BridgeError, TypeError, ValueError):
                raise BridgeError("TRANSITION_LOCK_INVALID")
            if process_alive(pid):
                raise BridgeError("TRANSITION_WRITER_ACTIVE")
            self.path.unlink()
        payload = canonical_bytes({"pid": os.getpid(), "created_at": utc_now()})
        try:
            with self.path.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError as exc:
            raise BridgeError("TRANSITION_WRITER_ACTIVE") from exc
        self.acquired = True
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.acquired and self.path.exists():
            self.path.unlink()


def assert_repository_binding(root: Path, expected: dict[str, Any], *, require_clean: bool) -> dict[str, Any]:
    observed = repository_identity(root, require_clean=require_clean)
    for key in ("origin", "root_commits", "head", "tree"):
        if observed.get(key) != expected.get(key):
            raise BridgeError(f"REPOSITORY_BINDING_DRIFT:{key}")
    return observed


def transition_dirty_paths(root: Path) -> set[str]:
    tracked = set(filter(None, git(root, "diff", "--name-only", "HEAD").splitlines()))
    untracked = set(filter(None, git(root, "ls-files", "--others", "--exclude-standard").splitlines()))
    return {Path(item).as_posix() for item in tracked | untracked}


def assert_only_transition_dirtiness(root: Path, journal: dict[str, Any]) -> None:
    transition_id = str(journal["transition_id"])
    exact = {LEGACY_ATTRIBUTES.as_posix()} | {
        str(item["path"])
        for item in [
            *journal["legacy"]["executors"],
            *journal["legacy"]["worker_instructions"],
        ]
    }
    prefixes = [f"{transition_path(transition_id).as_posix()}/"]
    if journal["legacy"].get("ai_state"):
        prefixes.append(".ai/")
    unexpected = sorted(
        path for path in transition_dirty_paths(root)
        if path not in exact and not any(path.startswith(prefix) for prefix in prefixes)
    )
    if unexpected:
        raise BridgeError(f"UNRELATED_DIRTY_PATHS_DURING_RECOVERY:{unexpected}")


def verify_file_matches(path: Path, expected: dict[str, Any], error: str) -> None:
    if (
        not path.is_file() or is_reparse(path)
        or sha256_file(path) != expected.get("sha256")
        or path.stat().st_size != expected.get("size")
    ):
        raise BridgeError(f"{error}:{path}")


def verify_worker_replacement(path: Path, expected: dict[str, Any]) -> None:
    if not path.is_file() or is_reparse(path):
        raise BridgeError(f"WORKER_REPLACEMENT_CHANGED:{path}")
    content = path.read_bytes()
    exact = (
        len(content) == expected.get("size")
        and hashlib.sha256(content).hexdigest() == expected.get("sha256")
    )
    try:
        portable = normalized_text_sha256(content) == expected.get("text_sha256")
    except UnicodeError:
        portable = False
    if not exact and not portable:
        raise BridgeError(f"WORKER_REPLACEMENT_CHANGED:{path}")


def verify_encoded_executor(path: Path, expected: dict[str, Any]) -> None:
    if not path.is_file() or is_reparse(path):
        raise BridgeError(f"ENCODED_EXECUTOR_ARCHIVE_MISSING:{path}")
    try:
        decoded = base64.b64decode(path.read_bytes(), validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise BridgeError(f"ENCODED_EXECUTOR_ARCHIVE_INVALID:{path}") from exc
    if (
        len(decoded) != expected.get("size")
        or hashlib.sha256(decoded).hexdigest() != expected.get("sha256")
    ):
        raise BridgeError(f"ENCODED_EXECUTOR_ARCHIVE_HASH_MISMATCH:{path}")


def verify_quarantined_ai(root: Path, transition_id: str, inventory: dict[str, Any]) -> Path:
    directory = quarantined_ai_path(root, transition_id)
    common = git_common_dir(root)
    reject_indirection(common, directory)
    expected_rows = inventory.get("files")
    if not directory.is_dir() or not isinstance(expected_rows, list):
        raise BridgeError("QUARANTINED_AI_STATE_INVALID")
    expected = {
        Path(str(row["path"])).relative_to(".ai").as_posix(): row
        for row in expected_rows if isinstance(row, dict)
    }
    if len(expected) != len(expected_rows):
        raise BridgeError("RECEIPT_AI_INVENTORY_INVALID")
    observed: set[str] = set()
    for path in sorted(directory.rglob("*")):
        reject_indirection(common, path)
        if path.is_dir():
            continue
        relative = path.relative_to(directory).as_posix()
        row = expected.get(relative)
        if row is None:
            raise BridgeError(f"QUARANTINED_AI_UNEXPECTED_FILE:{relative}")
        if (
            not path.is_file() or sha256_file(path) != row.get("sha256")
            or path.stat().st_size != row.get("size")
        ):
            raise BridgeError(f"QUARANTINED_AI_HASH_MISMATCH:{relative}")
        observed.add(relative)
    if observed != set(expected):
        raise BridgeError("QUARANTINED_AI_FILE_SET_MISMATCH")
    return directory


def build_ai_archive(root: Path, transition_id: str, inventory: dict[str, Any]) -> bytes:
    source_root = verify_quarantined_ai(root, transition_id, inventory)
    expected_rows = inventory.get("files")
    if not isinstance(expected_rows, list):
        raise BridgeError("RECEIPT_AI_INVENTORY_INVALID")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for row in sorted(expected_rows, key=lambda item: str(item.get("path", "")) if isinstance(item, dict) else ""):
            if not isinstance(row, dict):
                raise BridgeError("RECEIPT_AI_INVENTORY_INVALID")
            relative = str(row.get("path", ""))
            source = source_root / Path(relative).relative_to(".ai")
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())
    return output.getvalue()


def verify_archived_ai(root: Path, transition_id: str, inventory: dict[str, Any]) -> None:
    path = ai_archive_path(root, transition_id)
    reject_indirection(root, path)
    if not path.is_file():
        raise BridgeError("ARCHIVED_AI_STATE_MISSING")
    expected_rows = inventory.get("files")
    if not isinstance(expected_rows, list) or any(not isinstance(row, dict) for row in expected_rows):
        raise BridgeError("RECEIPT_AI_INVENTORY_INVALID")
    expected = {str(row["path"]): row for row in expected_rows}
    try:
        with zipfile.ZipFile(path, "r") as archive:
            names = archive.namelist()
            if len(names) != len(set(names)) or set(names) != set(expected):
                raise BridgeError("ARCHIVED_AI_FILE_SET_MISMATCH")
            for info in archive.infolist():
                if info.is_dir() or info.compress_type != zipfile.ZIP_STORED:
                    raise BridgeError(f"ARCHIVED_AI_MEMBER_INVALID:{info.filename}")
                content = archive.read(info)
                row = expected[info.filename]
                if len(content) != row.get("size") or hashlib.sha256(content).hexdigest() != row.get("sha256"):
                    raise BridgeError(f"ARCHIVED_AI_HASH_MISMATCH:{info.filename}")
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise BridgeError(f"ARCHIVED_AI_ZIP_INVALID:{path}") from exc


def failpoint(name: str) -> None:
    if os.environ.get("BUILDOS_LEGACY_BRIDGE_FAIL_AFTER") == name:
        raise BridgeError(f"INJECTED_FAILURE:{name}")


def sanitized_legacy(legacy: dict[str, Any]) -> dict[str, Any]:
    goal = dict(legacy["goal"])
    decisions = goal.pop("decisions_required", [])
    goal["decisions_required_count"] = len(decisions) if isinstance(decisions, list) else -1
    goal["decisions_required_sha256"] = hashlib.sha256(canonical_bytes(decisions)).hexdigest()
    goal["decision_bindings"] = decision_bindings(decisions)
    runtime_rows: dict[str, Any] = {}
    for name, row in legacy["runtime"].get("observations", {}).items():
        if isinstance(row, dict):
            runtime_rows[name] = {"sha256": row.get("sha256")}
    return {
        "family": legacy["family"],
        "task": legacy["task"],
        "goal": goal,
        "runtime": {"present": legacy["runtime"].get("present"), "observations": runtime_rows},
        "executors": legacy["executors"],
        "worker_instructions": legacy["worker_instructions"],
        "ai_state": legacy.get("ai_state"),
    }


def build_receipt(journal: dict[str, Any]) -> dict[str, Any]:
    legacy = sanitized_legacy(journal["legacy"])
    receipt: dict[str, Any] = {
        "schema": TRANSITION_SCHEMA,
        "bridge_version": BRIDGE_VERSION,
        "transition_id": journal["transition_id"],
        "state": "LEGACY_RETIRED",
        "prepared_at": journal["prepared_at"],
        "retired_at": journal.get("retirement_started_at"),
        "repository": journal["repository"],
        "package": journal["package"],
        "authorization": {
            **journal["authorization"],
            "evidence": journal.get("terminal_disposition_authorization_evidence"),
        },
        "legacy": legacy,
        "legacy_state_fingerprint": hashlib.sha256(canonical_bytes(legacy)).hexdigest(),
        "legacy_ai_archive": journal.get("legacy_ai_archive"),
        "worker_replacements": {
            relative: {
                "sha256": row["sha256"], "text_sha256": row["text_sha256"],
                "size": row["size"],
            }
            for relative, row in journal["worker_replacements"].items()
        },
        "retired_authority_disposition": {
            "legacy_ai": "TRACKED_DETERMINISTIC_ZIP_WITH_BYTE_IDENTICAL_MEMBERS",
            "legacy_executors": "TRACKED_BASE64_RECONSTRUCTIBLE_ARCHIVE_AND_LIVE_PATH_REMOVAL",
            "legacy_worker_instructions": "TRACKED_BYTE_IDENTICAL_ARCHIVE_AND_FAIL_CLOSED_REPLACEMENT",
            "future_authority": "EXTERNAL_PORTABLE_PACKAGE_PENDING_NORMAL_BOOTSTRAP",
        },
        "rollback_boundary": "PREPARED_ONLY_CANCELLABLE; AFTER_RETIREMENT_EXPLICIT_REENROLLMENT_REQUIRED",
    }
    receipt["receipt_sha256"] = object_hash(receipt, "receipt_sha256")
    return receipt


def move_original(root: Path, destination: Path, expected: dict[str, Any]) -> None:
    source = root / str(expected["path"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        verify_file_matches(destination, expected, "ARCHIVE_FILE_HASH_MISMATCH")
        if source.exists():
            raise BridgeError(f"SOURCE_AND_ARCHIVE_BOTH_PRESENT:{expected['path']}")
        return
    verify_file_matches(source, expected, "SOURCE_FILE_DRIFT")
    os.replace(source, destination)
    verify_file_matches(destination, expected, "ARCHIVE_FILE_HASH_MISMATCH")


def retire_executor(root: Path, transition_id: str, expected: dict[str, Any]) -> None:
    source = root / str(expected["path"])
    destination = encoded_executor_path(root, transition_id, str(expected["path"]))
    if destination.exists():
        verify_encoded_executor(destination, expected)
    else:
        verify_file_matches(source, expected, "SOURCE_FILE_DRIFT")
        atomic_write(destination, base64.b64encode(source.read_bytes()), overwrite=False)
        verify_encoded_executor(destination, expected)
    if source.exists():
        verify_file_matches(source, expected, "SOURCE_FILE_DRIFT")
        source.unlink()


def retire(root: Path, package_root: Path, transition_id: str) -> dict[str, Any]:
    transition_id = validate_identifier(transition_id)
    with TransitionLock(root, transition_id):
        journal_path, _, journal = load_journal(root, transition_id)
        state = journal.get("state")
        if state == "LEGACY_RETIRED":
            return verify_transition(root, package_root, transition_id, require_clean=False, require_activation_if_current=False)
        if state not in {"TRANSITION_PREPARED", "RETIRING_LEGACY"}:
            raise BridgeError(f"JOURNAL_STATE_INVALID:{state}")
        if state == "TRANSITION_PREPARED":
            assert_repository_binding(root, journal["repository"], require_clean=True)
            ai_state = journal["legacy"].get("ai_state")
            if ai_state:
                verify_directory_inventory(root, ai_state)
            for item in [*journal["legacy"]["executors"], *journal["legacy"]["worker_instructions"]]:
                if inventory_file(root, str(item["path"])) != item:
                    raise BridgeError(f"SOURCE_DRIFT_BEFORE_RETIREMENT:{item['path']}")
            journal["state"] = "RETIRING_LEGACY"
            journal["retirement_started_at"] = utc_now()
            save_journal(journal_path, journal)
        else:
            observed = repository_identity(root, require_clean=False)
            for key in ("origin", "root_commits", "head", "tree"):
                if observed.get(key) != journal["repository"].get(key):
                    raise BridgeError(f"REPOSITORY_BINDING_DRIFT:{key}")
            assert_only_transition_dirtiness(root, journal)

        ensure_legacy_attributes(root)

        for index, item in enumerate(journal["legacy"]["executors"]):
            retire_executor(root, transition_id, item)
            if index == 0:
                failpoint("first_executor")
        failpoint("executors")

        for item in journal["legacy"]["worker_instructions"]:
            relative = str(item["path"])
            destination = archive_path(root, transition_id, relative)
            replacement = journal["worker_replacements"][relative]
            source = root / relative
            if destination.exists():
                verify_file_matches(destination, item, "ARCHIVE_WORKER_HASH_MISMATCH")
            elif source.is_file() and sha256_file(source) == item["sha256"]:
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(source, destination)
            elif not source.exists():
                raise BridgeError(f"WORKER_SOURCE_AND_ARCHIVE_MISSING:{relative}")
            content = base64.b64decode(replacement["content_base64"], validate=True)
            if source.exists():
                verify_worker_replacement(source, replacement)
            else:
                atomic_write(source, content, overwrite=False)
            verify_worker_replacement(source, replacement)
        failpoint("workers")

        ai_state = journal["legacy"].get("ai_state")
        if ai_state:
            source_ai = root / ".ai"
            quarantine_ai = quarantined_ai_path(root, transition_id)
            destination_ai = ai_archive_path(root, transition_id)
            if source_ai.exists() and quarantine_ai.exists():
                raise BridgeError("SOURCE_AND_QUARANTINED_AI_BOTH_PRESENT")
            if source_ai.exists():
                verify_directory_inventory(root, ai_state)
                quarantine_ai.parent.mkdir(parents=True, exist_ok=True)
                os.replace(source_ai, quarantine_ai)
                failpoint("ai_quarantine")
            verify_quarantined_ai(root, transition_id, ai_state)
            if not destination_ai.exists():
                atomic_write(
                    destination_ai, build_ai_archive(root, transition_id, ai_state),
                    overwrite=False,
                )
            verify_archived_ai(root, transition_id, ai_state)
            verify_quarantined_ai(root, transition_id, ai_state)
            journal["legacy_ai_archive"] = inventory_file(
                root, destination_ai.relative_to(root).as_posix(),
            )
            save_journal(journal_path, journal)
        failpoint("legacy_state")

        terminal_authorization = journal.get("terminal_disposition_authorization")
        if terminal_authorization is not None:
            authorization_target = terminal_authorization_path(root, transition_id)
            atomic_write(
                authorization_target, canonical_bytes(terminal_authorization), overwrite=False,
            )
            validate_terminal_authorization(
                authorization_target, journal["repository"], journal["legacy"]["goal"],
                require_transport=False,
            )
            journal["terminal_disposition_authorization_evidence"] = inventory_file(
                root, authorization_target.relative_to(root).as_posix(),
            )
            save_journal(journal_path, journal)

        receipt = build_receipt(journal)
        atomic_write(receipt_path(root, transition_id), canonical_bytes(receipt), overwrite=False)
        failpoint("receipt")
        journal["state"] = "LEGACY_RETIRED"
        journal["receipt_sha256"] = receipt["receipt_sha256"]
        journal["retired_at"] = receipt["retired_at"]
        save_journal(journal_path, journal)
        return verify_transition(root, package_root, transition_id, require_clean=False, require_activation_if_current=False)


def validate_receipt_shape(receipt: dict[str, Any], transition_id: str) -> None:
    if (
        receipt.get("schema") != TRANSITION_SCHEMA
        or receipt.get("bridge_version") != BRIDGE_VERSION
        or receipt.get("transition_id") != transition_id
        or receipt.get("state") != "LEGACY_RETIRED"
    ):
        raise BridgeError("TRANSITION_RECEIPT_IDENTITY_INVALID")
    digest = receipt.get("receipt_sha256")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest) or digest != object_hash(receipt, "receipt_sha256"):
        raise BridgeError("TRANSITION_RECEIPT_HASH_INVALID")
    legacy = receipt.get("legacy")
    if not isinstance(legacy, dict) or receipt.get("legacy_state_fingerprint") != hashlib.sha256(canonical_bytes(legacy)).hexdigest():
        raise BridgeError("LEGACY_STATE_FINGERPRINT_INVALID")
    package = receipt.get("package")
    if (
        not isinstance(package, dict)
        or set(package) != {
            "package_id", "frozen_kernel_commit", "frozen_kernel_version",
            "project_lifecycle_kit_version", "bridge_version",
        }
        or not isinstance(package.get("package_id"), str) or not package["package_id"]
        or not isinstance(package.get("frozen_kernel_commit"), str)
        or not re.fullmatch(r"[0-9a-f]{40}", package["frozen_kernel_commit"])
        or package.get("bridge_version") != BRIDGE_VERSION
    ):
        raise BridgeError("TRANSITION_RECEIPT_PACKAGE_IDENTITY_INVALID")
    archive = receipt.get("legacy_ai_archive")
    if legacy.get("ai_state"):
        expected_path = (transition_path(transition_id) / "legacy-ai.zip").as_posix()
        if (
            not isinstance(archive, dict) or archive.get("path") != expected_path
            or not isinstance(archive.get("sha256"), str) or not SHA256.fullmatch(archive["sha256"])
            or not isinstance(archive.get("size"), int) or archive["size"] < 1
        ):
            raise BridgeError("TRANSITION_RECEIPT_AI_ARCHIVE_IDENTITY_INVALID")
    elif archive is not None:
        raise BridgeError("TRANSITION_RECEIPT_AI_ARCHIVE_UNEXPECTED")
    authorization = receipt.get("authorization")
    if not isinstance(authorization, dict) or set(authorization) != {
        "blocked_goal_terminal_disposition", "schema", "authorization_id",
        "authorization_sha256", "evidence",
    }:
        raise BridgeError("TRANSITION_RECEIPT_AUTHORIZATION_INVALID")
    authorized = authorization.get("blocked_goal_terminal_disposition") is True
    expected_authorized = legacy.get("goal", {}).get("disposition") == "OWNER_AUTHORIZED_TERMINAL_DISPOSITION"
    if authorized != expected_authorized:
        raise BridgeError("TRANSITION_RECEIPT_AUTHORIZATION_DISPOSITION_MISMATCH")
    if authorized:
        evidence = authorization.get("evidence")
        expected_path = (transition_path(transition_id) / "terminal-disposition-authorization.json").as_posix()
        if (
            authorization.get("schema") != TERMINAL_AUTHORIZATION_SCHEMA
            or not isinstance(authorization.get("authorization_id"), str)
            or not AUTHORIZATION_ID.fullmatch(authorization["authorization_id"])
            or not isinstance(authorization.get("authorization_sha256"), str)
            or not SHA256.fullmatch(authorization["authorization_sha256"])
            or not isinstance(evidence, dict)
            or evidence.get("path") != expected_path
            or not isinstance(evidence.get("sha256"), str)
            or not SHA256.fullmatch(evidence["sha256"])
            or not isinstance(evidence.get("size"), int) or evidence["size"] < 1
        ):
            raise BridgeError("TRANSITION_RECEIPT_AUTHORIZATION_EVIDENCE_INVALID")
    elif any(authorization.get(key) is not None for key in ("schema", "authorization_id", "authorization_sha256", "evidence")):
        raise BridgeError("TRANSITION_RECEIPT_AUTHORIZATION_UNEXPECTED")


def verify_terminal_authorization_evidence(
    root: Path, transition_id: str, receipt: dict[str, Any],
) -> None:
    authorization = receipt["authorization"]
    if not authorization["blocked_goal_terminal_disposition"]:
        return
    target = terminal_authorization_path(root, transition_id)
    evidence = authorization["evidence"]
    verify_file_matches(target, evidence, "TERMINAL_DISPOSITION_AUTHORIZATION_EVIDENCE_MISMATCH")
    value = read_json(target)
    if set(value) != {
        "schema", "authorization_id", "repository", "legacy_goal",
        "disposition", "authority", "authorization_sha256",
    }:
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_INVALID")
    digest = value.get("authorization_sha256")
    if (
        value.get("schema") != TERMINAL_AUTHORIZATION_SCHEMA
        or value.get("authorization_id") != authorization.get("authorization_id")
        or digest != authorization.get("authorization_sha256")
        or not isinstance(digest, str) or digest != object_hash(value, "authorization_sha256")
        or value.get("disposition") != TERMINAL_DISPOSITION
    ):
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_IDENTITY_INVALID")
    repository = receipt["repository"]
    expected_repository = {
        key: repository[key] for key in ("origin", "root_commits", "branch", "head", "tree")
    }
    if value.get("repository") != expected_repository:
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_REPOSITORY_MISMATCH")
    goal = receipt["legacy"]["goal"]
    expected_goal = {
        "goal_id": goal.get("goal_id"),
        "path": goal.get("path"),
        "status": goal.get("status"),
        "sha256": goal.get("sha256"),
        "decision_bindings": goal.get("decision_bindings"),
    }
    if value.get("legacy_goal") != expected_goal:
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_GOAL_MISMATCH")
    authority = value.get("authority")
    if (
        not isinstance(authority, dict)
        or set(authority) != {"role", "identity", "authority_reference", "authorized_at"}
        or authority.get("role") != "OWNER"
        or any(not isinstance(authority.get(key), str) or not authority[key].strip()
               for key in ("identity", "authority_reference", "authorized_at"))
    ):
        raise BridgeError("TERMINAL_DISPOSITION_AUTHORIZATION_AUTHORITY_INVALID")


def frozen_kernel_current(package_root: Path, root: Path) -> dict[str, Any]:
    program = (
        "import json,sys;"
        "sys.path.insert(0,sys.argv[1]);"
        "from buildos.store import read_current;"
        "s=read_current(sys.argv[2]);"
        "print(json.dumps({'generation':s.generation,'generation_hash':s.generation_hash,'file':s.filename},sort_keys=True))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program, str(package_root.resolve()), str(root.resolve())],
        cwd=str(package_root.resolve()), text=True, encoding="utf-8", errors="replace",
        capture_output=True, timeout=60,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        suffix = detail[-1] if detail else "unknown frozen-kernel validation error"
        raise BridgeError(f"CURRENT_REJECTED_BY_FROZEN_KERNEL:{suffix}")
    try:
        value = strict_json_loads(completed.stdout)
    except (ValueError, json.JSONDecodeError) as exc:
        raise BridgeError("FROZEN_KERNEL_CURRENT_RESULT_INVALID") from exc
    if not isinstance(value, dict):
        raise BridgeError("FROZEN_KERNEL_CURRENT_RESULT_INVALID")
    return value


def read_current_binding(root: Path, package_root: Path) -> dict[str, Any]:
    frozen = frozen_kernel_current(package_root, root)
    current_path = root / CURRENT_PATH
    current = read_json(current_path)
    if set(current) != {"schema", "generation", "generation_hash", "file"} or current.get("schema") != "buildos.current.v1":
        raise BridgeError("CURRENT_POINTER_INVALID")
    filename = str(current.get("file", ""))
    if Path(filename).name != filename or not filename.endswith(".json"):
        raise BridgeError("CURRENT_GENERATION_FILENAME_INVALID")
    generation_path = root / ".buildos" / "control" / "generations" / filename
    reject_indirection(root, generation_path)
    generation = read_json(generation_path)
    if (
        generation.get("schema") != "buildos.generation.v1"
        or generation.get("generation") != current.get("generation")
        or generation.get("generation_hash") != current.get("generation_hash")
        or generation.get("generation_hash") != object_hash(generation, "generation_hash")
        or frozen != {
            "generation": current.get("generation"),
            "generation_hash": current.get("generation_hash"),
            "file": current.get("file"),
        }
    ):
        raise BridgeError("CURRENT_GENERATION_IDENTITY_MISMATCH")
    commit_receipt_path = (
        root / ".buildos" / "control" / "receipts"
        / f"p{int(current['generation']):08d}-{str(current['generation_hash'])[:16]}.json"
    )
    if not commit_receipt_path.is_file():
        raise BridgeError("KERNEL_COMMIT_RECEIPT_MISSING_OR_INVALID_RUN_RECOVER")
    commit_receipt = read_json(commit_receipt_path)
    expected_commit_receipt = {**current, "schema": "buildos.commit_receipt.v1"}
    if commit_receipt != expected_commit_receipt:
        raise BridgeError("KERNEL_COMMIT_RECEIPT_MISSING_OR_INVALID_RUN_RECOVER")
    return {
        "pointer": current,
        "pointer_sha256": sha256_file(current_path),
        "generation_file_sha256": sha256_file(generation_path),
        "kernel_commit_receipt_sha256": sha256_file(commit_receipt_path),
    }


def verify_activation(root: Path, transition_id: str, receipt: dict[str, Any]) -> dict[str, Any]:
    path = root / ACTIVATION_ROOT / f"{transition_id}.json"
    reject_indirection(root, path)
    if not path.is_file():
        raise BridgeError("ACTIVATION_RECEIPT_MISSING")
    activation = read_json(path)
    if (
        activation.get("schema") != ACTIVATION_SCHEMA
        or activation.get("transition_id") != transition_id
        or activation.get("transition_receipt_sha256") != receipt.get("receipt_sha256")
    ):
        raise BridgeError("ACTIVATION_RECEIPT_IDENTITY_INVALID")
    digest = activation.get("activation_receipt_sha256")
    if not isinstance(digest, str) or digest != object_hash(activation, "activation_receipt_sha256"):
        raise BridgeError("ACTIVATION_RECEIPT_HASH_INVALID")
    generation = activation.get("initial_generation")
    if not isinstance(generation, dict):
        raise BridgeError("ACTIVATION_GENERATION_BINDING_INVALID")
    filename = str(generation.get("file", ""))
    path_to_generation = root / ".buildos" / "control" / "generations" / filename
    kernel_receipt = (
        root / ".buildos" / "control" / "receipts"
        / f"p{int(generation.get('generation', -1)):08d}-{str(generation.get('generation_hash', ''))[:16]}.json"
    )
    if (
        Path(filename).name != filename or not path_to_generation.is_file()
        or sha256_file(path_to_generation) != generation.get("generation_file_sha256")
        or not kernel_receipt.is_file()
        or sha256_file(kernel_receipt) != generation.get("kernel_commit_receipt_sha256")
    ):
        raise BridgeError("ACTIVATION_GENERATION_MISSING_OR_CHANGED")
    authority = root / AUTHORITY_RECORD
    if not authority.is_file() or sha256_file(authority) != activation.get("authority_record_sha256"):
        raise BridgeError("ACTIVATION_AUTHORITY_RECORD_CHANGED")
    return activation


def expected_transition_evidence_paths(
    root: Path, transition_id: str, receipt_file: Path, receipt: dict[str, Any],
) -> set[str]:
    legacy = receipt["legacy"]
    expected = {receipt_file.relative_to(root).as_posix()}
    expected.add(LEGACY_ATTRIBUTES.as_posix())
    expected.update(
        encoded_executor_path(root, transition_id, str(item["path"])).relative_to(root).as_posix()
        for item in legacy.get("executors", []) if isinstance(item, dict)
    )
    expected.update(
        archive_path(root, transition_id, str(item["path"])).relative_to(root).as_posix()
        for item in legacy.get("worker_instructions", []) if isinstance(item, dict)
    )
    if legacy.get("ai_state"):
        expected.add(ai_archive_path(root, transition_id).relative_to(root).as_posix())
    if receipt.get("authorization", {}).get("blocked_goal_terminal_disposition"):
        expected.add(terminal_authorization_path(root, transition_id).relative_to(root).as_posix())
    return expected


def untracked_transition_evidence(root: Path, expected: set[str]) -> list[str]:
    return sorted(
        path for path in expected
        if not git_succeeds(root, "ls-files", "--error-unmatch", "--", path)
    )


def verify_transition(
    root: Path, package_root: Path, transition_id: str, *, require_clean: bool,
    require_activation_if_current: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    transition_id = validate_identifier(transition_id)
    receipt_file = receipt_path(root, transition_id)
    reject_indirection(root, receipt_file)
    receipt = read_json(receipt_file)
    validate_receipt_shape(receipt, transition_id)
    verify_legacy_attributes(root)
    verify_terminal_authorization_evidence(root, transition_id, receipt)
    observed = repository_identity(root, require_clean=require_clean)
    bound = receipt.get("repository")
    if not isinstance(bound, dict):
        raise BridgeError("RECEIPT_REPOSITORY_BINDING_INVALID")
    for key in ("origin", "root_commits"):
        if observed.get(key) != bound.get(key):
            raise BridgeError(f"RECEIPT_COPIED_OR_REPOSITORY_MISMATCH:{key}")
    base_head = str(bound.get("head", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", base_head) or not git_succeeds(root, "merge-base", "--is-ancestor", base_head, "HEAD"):
        raise BridgeError("RECEIPT_BASE_HEAD_NOT_ANCESTOR")
    if git(root, "rev-parse", f"{base_head}^{{tree}}") != bound.get("tree"):
        raise BridgeError("RECEIPT_BASE_TREE_MISMATCH")
    package_identity(package_root)
    legacy = receipt["legacy"]
    ai_state = legacy.get("ai_state")
    expected_tracked = expected_transition_evidence_paths(
        root, transition_id, receipt_file, receipt,
    )
    untracked = untracked_transition_evidence(root, expected_tracked)
    durable_retirement = not untracked
    if ai_state:
        verify_archived_ai(root, transition_id, ai_state)
        archive = receipt.get("legacy_ai_archive")
        if not isinstance(archive, dict):
            raise BridgeError("TRANSITION_RECEIPT_AI_ARCHIVE_IDENTITY_INVALID")
        verify_file_matches(
            ai_archive_path(root, transition_id), archive,
            "ARCHIVED_AI_CONTAINER_HASH_MISMATCH",
        )
        quarantine = quarantined_ai_path(root, transition_id)
        if quarantine.exists():
            verify_quarantined_ai(root, transition_id, ai_state)
        elif not durable_retirement:
            raise BridgeError("QUARANTINED_AI_STATE_REQUIRED_FOR_INCOMPLETE_TRANSITION")
    if (root / ".ai").exists():
        raise BridgeError("LIVE_LEGACY_AI_STATE_REAPPEARED")
    for item in legacy.get("executors", []):
        if not isinstance(item, dict):
            raise BridgeError("RECEIPT_EXECUTOR_INVENTORY_INVALID")
        verify_encoded_executor(encoded_executor_path(root, transition_id, str(item["path"])), item)
        if (root / str(item["path"])).exists():
            raise BridgeError(f"LEGACY_EXECUTOR_REAPPEARED:{item['path']}")
    replacements = receipt.get("worker_replacements")
    if not isinstance(replacements, dict):
        raise BridgeError("RECEIPT_WORKER_REPLACEMENTS_INVALID")
    for item in legacy.get("worker_instructions", []):
        if not isinstance(item, dict):
            raise BridgeError("RECEIPT_WORKER_INVENTORY_INVALID")
        relative = str(item["path"])
        verify_file_matches(archive_path(root, transition_id, relative), item, "ARCHIVED_WORKER_HASH_MISMATCH")
        replacement = replacements.get(relative)
        if not isinstance(replacement, dict):
            raise BridgeError(f"WORKER_REPLACEMENT_BINDING_MISSING:{relative}")
        verify_worker_replacement(root / relative, replacement)
    if require_clean:
        if untracked:
            raise BridgeError(f"TRANSITION_EVIDENCE_NOT_TRACKED:{untracked}")
    remaining = identify_legacy_executors(root)
    if remaining["executors"]:
        raise BridgeError(f"LEGACY_EXECUTOR_CALLABLE:{remaining['executors']}")
    if remaining["ambiguous"]:
        raise BridgeError(f"AMBIGUOUS_LEGACY_EXECUTOR_CANDIDATE:{remaining['ambiguous']}")
    authority = root / AUTHORITY_RECORD
    if authority.exists():
        record = read_json(authority)
        expected_binding = {
            "schema": TRANSITION_SCHEMA,
            "transition_id": transition_id,
            "path": receipt_file.relative_to(root).as_posix(),
            "receipt_sha256": receipt["receipt_sha256"],
        }
        if record.get("legacy_transition") != expected_binding:
            raise BridgeError("AUTHORITY_RECORD_TRANSITION_BINDING_MISMATCH")
    activation = None
    if (root / CURRENT_PATH).exists() and require_activation_if_current:
        activation = verify_activation(root, transition_id, receipt)
    return {
        "status": "PASS",
        "invariant": "PROVENANCE_PRESERVING_SINGLE_EXECUTION_AUTHORITY",
        "transition_id": transition_id,
        "state": "V125_ACTIVE" if activation else "LEGACY_RETIRED",
        "receipt": receipt_file.relative_to(root).as_posix(),
        "receipt_sha256": receipt["receipt_sha256"],
        "activation_receipt": (
            (ACTIVATION_ROOT / f"{transition_id}.json").as_posix() if activation else None
        ),
    }


def discover_transition(root: Path) -> str | None:
    archive_root = root / ARCHIVE_ROOT
    if not archive_root.exists():
        return None
    reject_indirection(root, archive_root)
    receipts = sorted(archive_root.glob("*/receipt.json"))
    if len(receipts) != 1:
        raise BridgeError("EXACTLY_ONE_LEGACY_TRANSITION_RECEIPT_REQUIRED")
    transition_id = receipts[0].parent.name
    validate_identifier(transition_id)
    return transition_id


def authority_binding(root: Path, package_root: Path) -> dict[str, Any] | None:
    transition_id = discover_transition(root)
    if transition_id is None:
        return None
    verified = verify_transition(
        root, package_root, transition_id, require_clean=False,
        require_activation_if_current=True,
    )
    return {
        "schema": TRANSITION_SCHEMA,
        "transition_id": transition_id,
        "path": verified["receipt"],
        "receipt_sha256": verified["receipt_sha256"],
    }


def finalize(root: Path, package_root: Path, transition_id: str) -> dict[str, Any]:
    transition_id = validate_identifier(transition_id)
    repository_identity(root, require_clean=True)
    verified = verify_transition(
        root, package_root, transition_id, require_clean=True,
        require_activation_if_current=False,
    )
    authority_path = root / AUTHORITY_RECORD
    authority = read_json(authority_path)
    if authority.get("schema") != AUTHORITY_SCHEMA:
        raise BridgeError("AUTHORITY_RECORD_INVALID_FOR_ACTIVATION")
    binding = authority.get("legacy_transition")
    if not isinstance(binding, dict) or binding.get("receipt_sha256") != verified["receipt_sha256"]:
        raise BridgeError("AUTHORITY_RECORD_NOT_BOUND_TO_TRANSITION")
    existing = root / ACTIVATION_ROOT / f"{transition_id}.json"
    reject_indirection(root, existing)
    if existing.exists():
        return verify_transition(
            root, package_root, transition_id, require_clean=True,
            require_activation_if_current=True,
        )
    current = read_current_binding(root, package_root)
    activation: dict[str, Any] = {
        "schema": ACTIVATION_SCHEMA,
        "bridge_version": BRIDGE_VERSION,
        "transition_id": transition_id,
        "activated_at": utc_now(),
        "transition_receipt_sha256": verified["receipt_sha256"],
        "authority_record_sha256": sha256_file(authority_path),
        "package": package_identity(package_root),
        "initial_generation": {
            **current["pointer"],
            "current_pointer_sha256": current["pointer_sha256"],
            "generation_file_sha256": current["generation_file_sha256"],
            "kernel_commit_receipt_sha256": current["kernel_commit_receipt_sha256"],
        },
        "post_transition_verification": "PASS",
    }
    activation["activation_receipt_sha256"] = object_hash(activation, "activation_receipt_sha256")
    target = root / ACTIVATION_ROOT / f"{transition_id}.json"
    reject_indirection(root, target)
    atomic_write(target, canonical_bytes(activation), overwrite=False)
    return verify_transition(
        root, package_root, transition_id, require_clean=True,
        require_activation_if_current=True,
    )


def cancel(root: Path, transition_id: str) -> dict[str, Any]:
    transition_id = validate_identifier(transition_id)
    journal_path, _, journal = load_journal(root, transition_id)
    if journal.get("state") != "TRANSITION_PREPARED":
        raise BridgeError("ONLY_PREPARED_TRANSITION_CAN_BE_CANCELLED")
    assert_repository_binding(root, journal["repository"], require_clean=True)
    base = journal_path.parent
    shutil.rmtree(base)
    return {"status": "PASS", "transition_id": transition_id, "state": "LEGACY_ACTIVE", "cancelled": True}


def emit(value: dict[str, Any]) -> int:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if value.get("status", "PASS") == "PASS" else 2


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    package_root = Path(__file__).resolve().parents[3]
    if argv == ["--version"]:
        return emit({"status": "PASS", "component": "legacy-authority-bridge", **package_identity(package_root)})
    parser = argparse.ArgumentParser(description="Build OS legacy authority terminality/adoption bridge")
    parser.add_argument("--root", required=True)
    parser.add_argument("--package-root", default=str(package_root))
    sub = parser.add_subparsers(dest="command", required=True)
    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--terminalize-blocked-goal", action="store_true")
    inspect_parser.add_argument("--terminal-disposition-authorization", type=Path)
    inspect_parser.add_argument("--authorization-reference")
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--transition-id", required=True)
    prepare_parser.add_argument("--terminalize-blocked-goal", action="store_true")
    prepare_parser.add_argument("--terminal-disposition-authorization", type=Path)
    prepare_parser.add_argument("--authorization-reference")
    prepare_parser.add_argument("--replacement-worker", action="append", default=[])
    for name in ("retire", "recover", "cancel", "verify", "finalize"):
        command = sub.add_parser(name)
        command.add_argument("--transition-id", required=True)
        if name == "verify":
            command.add_argument("--require-clean", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    package = Path(args.package_root).resolve()
    try:
        if args.command == "inspect":
            value = inspect_legacy(
                root, package, allow_blocked=args.terminalize_blocked_goal,
                authorization_path=args.terminal_disposition_authorization,
                authorization_reference=args.authorization_reference, require_clean=True,
            )
            return emit({"status": "PASS", **value})
        if args.command == "prepare":
            value = prepare(
                root, package, args.transition_id,
                allow_blocked=args.terminalize_blocked_goal,
                authorization_path=args.terminal_disposition_authorization,
                authorization_reference=args.authorization_reference,
                replacement_rows=args.replacement_worker,
            )
            return emit({
                "status": "PASS", "transition_id": value["transition_id"],
                "state": value["state"], "repository": value["repository"],
            })
        if args.command in {"retire", "recover"}:
            return emit(retire(root, package, args.transition_id))
        if args.command == "cancel":
            return emit(cancel(root, args.transition_id))
        if args.command == "verify":
            return emit(verify_transition(
                root, package, args.transition_id, require_clean=args.require_clean,
                require_activation_if_current=True,
            ))
        if args.command == "finalize":
            return emit(finalize(root, package, args.transition_id))
        raise BridgeError("COMMAND_NOT_IMPLEMENTED")
    except (BridgeError, OSError, UnicodeError, ValueError, TypeError, KeyError, base64.binascii.Error) as exc:
        return emit({"status": "FAIL", "invariant": "PROVENANCE_PRESERVING_SINGLE_EXECUTION_AUTHORITY", "error": str(exc)})


if __name__ == "__main__":
    raise SystemExit(main())
