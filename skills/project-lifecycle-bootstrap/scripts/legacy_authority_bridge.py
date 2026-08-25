#!/usr/bin/env python3
"""Fail-closed, provenance-preserving legacy authority retirement bridge."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any


BRIDGE_VERSION = "1.0.0"
TRANSITION_SCHEMA = "buildos.legacy-authority-transition.v1"
ACTIVATION_SCHEMA = "buildos.legacy-authority-activation.v1"
JOURNAL_SCHEMA = "buildos.legacy-authority-journal.v1"
AUTHORITY_SCHEMA = "buildos.execution-authority.v1"
ARCHIVE_ROOT = Path(".buildos-legacy") / "archives"
CURRENT_PATH = Path(".buildos") / "control" / "CURRENT"
ACTIVATION_ROOT = Path(".buildos") / "control" / "legacy-bridge-receipts"
AUTHORITY_RECORD = Path(".buildos-authority.json")
EXECUTOR_FILENAMES = {"ai.py", "ai_os.py", "buildos.py", "build_os.py"}
WORKER_FILES = ("AGENTS.md", "WORKER_INSTRUCTIONS.md", "prompts/03_WORKER.md")
LEGACY_VERSION = re.compile(r"(?i)build\s*os\s*v1\.(?:[0-9]|1[0-9]|20|21)\b")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
SHA256 = re.compile(r"[0-9a-f]{64}")
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


def find_executors(root: Path) -> list[str]:
    found: set[str] = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in {".git", ".buildos", ".buildos-legacy", "archive", "archives"} for part in relative.parts):
            continue
        if path.is_file() and path.name in EXECUTOR_FILENAMES:
            reject_indirection(root, path)
            found.add(relative.as_posix())
    return sorted(found)


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


def inspect_goal(root: Path, *, allow_blocked: bool, authorization_reference: str | None) -> dict[str, Any]:
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
        if not allow_blocked or not str(authorization_reference or "").strip():
            raise BridgeError("LEGACY_GOAL_BLOCKED_REQUIRES_TERMINAL_DISPOSITION_AUTHORIZATION")
        disposition = "OWNER_AUTHORIZED_TERMINAL_DISPOSITION"
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


def inspect_runtime(
    root: Path, *, allow_blocked: bool, authorization_reference: str | None,
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
        elif status == "BLOCKED" and (
            not allow_blocked or not str(authorization_reference or "").strip()
        ):
            raise BridgeError("LEGACY_RUNTIME_GOAL_BLOCKED_REQUIRES_TERMINAL_DISPOSITION_AUTHORIZATION")
        elif status not in TERMINAL_GOAL_STATES | {"BLOCKED"}:
            raise BridgeError(f"LEGACY_RUNTIME_GOAL_MALFORMED:{status}")
    return {"present": True, "observations": observations}


def inspect_legacy(
    root: Path, package_root: Path, *, allow_blocked: bool = False,
    authorization_reference: str | None = None, require_clean: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    repository = repository_identity(root, require_clean=require_clean)
    if (root / CURRENT_PATH).exists() or (root / AUTHORITY_RECORD).exists():
        raise BridgeError("CURRENT_AUTHORITY_ALREADY_PRESENT")
    existing_archives = root / ARCHIVE_ROOT
    if existing_archives.exists():
        raise BridgeError("LEGACY_BRIDGE_ALREADY_PRESENT")
    executors = find_executors(root)
    if any(Path(item).parts and Path(item).parts[0] == ".ai" for item in executors):
        raise BridgeError("LEGACY_EXECUTOR_INSIDE_AI_UNSUPPORTED")
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
    goal = inspect_goal(
        root, allow_blocked=allow_blocked,
        authorization_reference=authorization_reference,
    )
    runtime = inspect_runtime(
        root, allow_blocked=allow_blocked,
        authorization_reference=authorization_reference,
    )
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
            "size": len(content),
            "content_base64": base64.b64encode(content).decode("ascii"),
        }
    return result


def prepare(
    root: Path, package_root: Path, transition_id: str, *, allow_blocked: bool,
    authorization_reference: str | None, replacement_rows: list[str],
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
            "blocked_goal_terminal_disposition": bool(allow_blocked),
            "reference": str(authorization_reference or "").strip() or None,
        },
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
    exact = {
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


def verify_archived_ai(root: Path, transition_id: str, inventory: dict[str, Any]) -> None:
    base = root / transition_path(transition_id) / "legacy"
    expected_rows = inventory.get("files")
    if not isinstance(expected_rows, list):
        raise BridgeError("RECEIPT_AI_INVENTORY_INVALID")
    expected_paths = {str(row.get("path")) for row in expected_rows if isinstance(row, dict)}
    observed_paths: set[str] = set()
    ai_root = base / ".ai"
    if not ai_root.is_dir() or is_reparse(ai_root):
        raise BridgeError("ARCHIVED_AI_STATE_MISSING")
    for path in sorted(ai_root.rglob("*")):
        if path.is_dir():
            if is_reparse(path):
                raise BridgeError(f"ARCHIVE_REPARSE_POINT:{path}")
            continue
        relative = path.relative_to(base).as_posix()
        observed_paths.add(relative)
        matches = [row for row in expected_rows if isinstance(row, dict) and row.get("path") == relative]
        if len(matches) != 1:
            raise BridgeError(f"ARCHIVED_AI_UNEXPECTED_FILE:{relative}")
        verify_file_matches(path, matches[0], "ARCHIVED_AI_HASH_MISMATCH")
    if observed_paths != expected_paths:
        raise BridgeError("ARCHIVED_AI_FILE_SET_MISMATCH")


def failpoint(name: str) -> None:
    if os.environ.get("BUILDOS_LEGACY_BRIDGE_FAIL_AFTER") == name:
        raise BridgeError(f"INJECTED_FAILURE:{name}")


def sanitized_legacy(legacy: dict[str, Any]) -> dict[str, Any]:
    goal = dict(legacy["goal"])
    decisions = goal.pop("decisions_required", [])
    goal["decisions_required_count"] = len(decisions) if isinstance(decisions, list) else -1
    goal["decisions_required_sha256"] = hashlib.sha256(canonical_bytes(decisions)).hexdigest()
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
        "authorization": journal["authorization"],
        "legacy": legacy,
        "legacy_state_fingerprint": hashlib.sha256(canonical_bytes(legacy)).hexdigest(),
        "worker_replacements": {
            relative: {"sha256": row["sha256"], "size": row["size"]}
            for relative, row in journal["worker_replacements"].items()
        },
        "retired_authority_disposition": {
            "legacy_ai": "TRACKED_BYTE_IDENTICAL_ARCHIVE",
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
                verify_file_matches(source, replacement, "WORKER_REPLACEMENT_DRIFT")
            else:
                atomic_write(source, content, overwrite=False)
            verify_file_matches(source, replacement, "WORKER_REPLACEMENT_DRIFT")
        failpoint("workers")

        ai_state = journal["legacy"].get("ai_state")
        if ai_state:
            source_ai = root / ".ai"
            destination_ai = root / transition_path(transition_id) / "legacy" / ".ai"
            if source_ai.exists() and destination_ai.exists():
                raise BridgeError("SOURCE_AND_ARCHIVED_AI_BOTH_PRESENT")
            if destination_ai.exists():
                verify_archived_ai(root, transition_id, ai_state)
            else:
                verify_directory_inventory(root, ai_state)
                destination_ai.parent.mkdir(parents=True, exist_ok=True)
                os.replace(source_ai, destination_ai)
                verify_archived_ai(root, transition_id, ai_state)
        failpoint("legacy_state")

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
    if ai_state:
        verify_archived_ai(root, transition_id, ai_state)
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
        verify_file_matches(root / relative, replacement, "WORKER_REPLACEMENT_CHANGED")
    if require_clean:
        expected_tracked = {receipt_file.relative_to(root).as_posix()}
        expected_tracked.update(
            encoded_executor_path(root, transition_id, str(item["path"])).relative_to(root).as_posix()
            for item in legacy.get("executors", []) if isinstance(item, dict)
        )
        expected_tracked.update(
            archive_path(root, transition_id, str(item["path"])).relative_to(root).as_posix()
            for item in legacy.get("worker_instructions", []) if isinstance(item, dict)
        )
        if ai_state:
            expected_tracked.update(
                (transition_path(transition_id) / "legacy" / str(item["path"])).as_posix()
                for item in ai_state.get("files", []) if isinstance(item, dict)
            )
        untracked = sorted(
            path for path in expected_tracked
            if not git_succeeds(root, "ls-files", "--error-unmatch", "--", path)
        )
        if untracked:
            raise BridgeError(f"TRANSITION_EVIDENCE_NOT_TRACKED:{untracked}")
    remaining = find_executors(root)
    if remaining:
        raise BridgeError(f"LEGACY_EXECUTOR_CALLABLE:{remaining}")
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
    inspect_parser.add_argument("--authorization-reference")
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--transition-id", required=True)
    prepare_parser.add_argument("--terminalize-blocked-goal", action="store_true")
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
                authorization_reference=args.authorization_reference, require_clean=True,
            )
            return emit({"status": "PASS", **value})
        if args.command == "prepare":
            value = prepare(
                root, package, args.transition_id,
                allow_blocked=args.terminalize_blocked_goal,
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
