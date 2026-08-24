"""Crash-safe content-addressed generation store for Build OS v1.22.

The only canonical logical authority is the generation named by ``CURRENT``.
Generation files are immutable.  A transition becomes canonical at the single
``os.replace`` of CURRENT; everything before it is preparation and everything
after it is verification/projection.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import socket
import time
import uuid
from typing import Any, Callable, Iterable, Iterator, Mapping

from .model import GENERATION_SCHEMA, KernelError, canonical_bytes, now_iso, sha256_json, validate_state


CURRENT_SCHEMA = "buildos.current.v1"
RECEIPT_SCHEMA = "buildos.commit_receipt.v1"
LOCK_SCHEMA = "buildos.lock.v1"
FAIL_ENV = "BUILDOS_FAIL_AT"
OPERATION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class InjectedFailure(RuntimeError):
    """Deterministic test-only process-failure surrogate."""


class RecoveryRequired(KernelError):
    """Recovery cannot safely choose among valid competing candidates."""


def validate_operation_id(value: str) -> str:
    value = str(value).strip()
    if not OPERATION_ID_RE.fullmatch(value):
        raise KernelError("operation_id must be 1-128 portable filename-safe characters")
    return value


@dataclass(frozen=True)
class StorePaths:
    root: Path
    control: Path
    generations: Path
    staging: Path
    receipts: Path
    current: Path
    lock: Path
    evidence: Path
    runtime: Path


@dataclass(frozen=True)
class Snapshot:
    state: dict[str, Any]
    generation: int
    generation_hash: str
    filename: str
    operation_id: str
    intent_hash: str
    event: dict[str, Any]


@dataclass(frozen=True)
class CommitResult:
    snapshot: Snapshot
    committed: bool
    idempotent: bool
    recovered_orphan: bool = False


def _is_reparse_point(path: Path) -> bool:
    try:
        stat = path.lstat()
    except OSError:
        return False
    return path.is_symlink() or bool(getattr(stat, "st_file_attributes", 0) & 0x400)


def _normalized_absolute(path: Path) -> str:
    value = os.path.normcase(os.path.abspath(str(path)))
    if os.name == "nt" and value.startswith("\\\\?\\"):
        value = value[4:]
    return value


def _is_within(root: Path, target: Path) -> bool:
    normalized_root = _normalized_absolute(root)
    normalized_target = _normalized_absolute(target)
    try:
        return os.path.commonpath([normalized_root, normalized_target]) == normalized_root
    except ValueError:
        return False


def _assert_control_paths_safe(root: Path) -> None:
    """Reject pre-existing aliases that could redirect canonical control bytes."""
    relative_paths = (
        Path(".buildos"), Path(".buildos/control"),
        Path(".buildos/control/generations"), Path(".buildos/control/staging"),
        Path(".buildos/control/receipts"), Path(".buildos/evidence"),
        Path(".buildos/runtime"),
    )
    for relative in relative_paths:
        current = root
        for part in relative.parts:
            current = current / part
            if _is_reparse_point(current):
                raise KernelError(
                    f"Build OS control path must not be a symlink, junction, or reparse point: {current}"
                )
            if not current.exists():
                break
            try:
                resolved = current.resolve(strict=True)
            except OSError as exc:
                raise KernelError("Build OS control path escapes the repository root") from exc
            if not _is_within(root, resolved):
                raise KernelError("Build OS control path escapes the repository root")


def safe_repository_descendant(root: Path | str, relative: Path | str, *, label: str) -> Path:
    """Resolve one repository-relative target without following an existing alias.

    Dynamic evidence paths contain task-controlled segments, so checking only the
    fixed ``.buildos`` directories is insufficient: any existing child junction
    could redirect an otherwise valid-looking publication outside the repository.
    """
    root = Path(root).resolve()
    relative = Path(relative)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise KernelError(f"{label} must be a canonical repository-relative path")
    current = root
    for part in relative.parts:
        current = current / part
        if _is_reparse_point(current):
            raise KernelError(f"{label} must not traverse a symlink, junction, or reparse point: {current}")
        if current.exists():
            try:
                resolved = current.resolve(strict=True)
            except OSError as exc:
                raise KernelError(f"{label} escapes the repository root") from exc
            if not _is_within(root, resolved):
                raise KernelError(f"{label} escapes the repository root")
    try:
        resolved = current.resolve(strict=False)
    except OSError as exc:
        raise KernelError(f"{label} escapes the repository root") from exc
    if not _is_within(root, resolved):
        raise KernelError(f"{label} escapes the repository root")
    return current


def paths(root: Path | str) -> StorePaths:
    root = Path(root).resolve()
    _assert_control_paths_safe(root)
    buildos = root / ".buildos"
    control = buildos / "control"
    return StorePaths(
        root=root,
        control=control,
        generations=control / "generations",
        staging=control / "staging",
        receipts=control / "receipts",
        current=control / "CURRENT",
        lock=control / "LOCK",
        evidence=buildos / "evidence",
        runtime=buildos / "runtime",
    )


def ensure_layout(root: Path | str) -> StorePaths:
    p = paths(root)
    for directory in (p.generations, p.staging, p.receipts, p.evidence, p.runtime):
        directory.mkdir(parents=True, exist_ok=True)
    _assert_control_paths_safe(p.root)
    return p


def _fsync_directory(directory: Path) -> None:
    """Best-effort directory durability.

    POSIX supports opening/fsyncing directories.  Windows atomic replacement
    is still process-crash safe, but Python does not expose a portable directory
    flush; this limitation is reported rather than hidden.
    """
    if os.name == "nt":
        return
    try:
        fd = os.open(str(directory), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_fsynced(path: Path, data: bytes, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_BINARY", 0) | (os.O_EXCL if exclusive else os.O_TRUNC)
    fd = os.open(str(path), flags, 0o600)
    try:
        offset = 0
        while offset < len(data):
            offset += os.write(fd, data[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write(path: Path, data: bytes) -> None:
    token = f"{os.getpid()}-{time.time_ns()}"
    temp = path.with_name(f".{path.name}.{token}.tmp")
    _write_fsynced(temp, data, exclusive=True)
    os.replace(temp, path)
    _fsync_directory(path.parent)


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    atomic_write(path, canonical_bytes(value))


def publish_immutable(temp: Path, final: Path) -> None:
    """Publish without ever overwriting an existing immutable path."""
    final.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(temp, final)
    except FileExistsError:
        if final.read_bytes() != temp.read_bytes():
            raise RecoveryRequired(f"immutable target already exists with different content: {final.name}")
        temp.unlink()
    else:
        temp.unlink()
        _fsync_directory(final.parent)


def _failure_points(value: str | None = None) -> set[str]:
    raw = os.environ.get(FAIL_ENV, "") if value is None else value
    return {part.strip() for part in raw.split(",") if part.strip()}


def failpoint(name: str, configured: str | None = None) -> None:
    if name in _failure_points(configured):
        raise InjectedFailure(f"injected failure at {name}")


@contextmanager
def _advisory_guard(path: Path) -> Iterator[None]:
    """OS-released guard serializing metadata takeover after hard process death."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
            os.fsync(handle.fileno())
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            raise KernelError("single-writer guard is held by another live process") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        handle.close()


@contextmanager
def writer_lock(root: Path | str) -> Iterator[None]:
    """Acquire the local OS-released guard and publish diagnostic metadata."""
    p = ensure_layout(root)
    nonce = uuid.uuid4().hex
    payload = {
        "schema": LOCK_SCHEMA,
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "created_at": now_iso(),
        "created_unix": time.time(),
        "nonce": nonce,
    }
    guard_path = p.control / "LOCK.guard"
    with _advisory_guard(guard_path):
        if p.lock.exists():
            stale_dir = p.control / "stale-locks"
            stale_dir.mkdir(parents=True, exist_ok=True)
            archived = stale_dir / f"LOCK-{time.time_ns()}.json"
            os.replace(p.lock, archived)
            _fsync_directory(stale_dir)
        _write_fsynced(p.lock, canonical_bytes(payload), exclusive=True)
        try:
            yield
        finally:
            try:
                current = json.loads(p.lock.read_text(encoding="utf-8"))
                if current.get("nonce") == nonce:
                    p.lock.unlink()
                    _fsync_directory(p.control)
            except (FileNotFoundError, json.JSONDecodeError, AttributeError):
                pass


def _payload_from_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in record.items() if k != "generation_hash"}


def validate_record(record: Mapping[str, Any], *, filename: str | None = None) -> Snapshot:
    if not isinstance(record, dict):
        raise KernelError("generation record must be a JSON object")
    if record.get("schema") != GENERATION_SCHEMA:
        raise KernelError("invalid generation schema")
    expected = sha256_json(_payload_from_record(record))
    actual = str(record.get("generation_hash", ""))
    if actual != expected:
        raise KernelError("generation hash mismatch")
    try:
        generation = int(record.get("generation", 0))
    except (TypeError, ValueError) as exc:
        raise KernelError("invalid generation number") from exc
    if generation < 1:
        raise KernelError("invalid generation number")
    if filename:
        expected_prefix = f"g{generation:08d}-{actual[:16]}"
        if filename != f"{expected_prefix}.json":
            raise KernelError("generation filename does not match content")
    raw_state = record.get("state")
    raw_event = record.get("event")
    if not isinstance(raw_state, dict) or not isinstance(raw_event, dict):
        raise KernelError("generation state and event must be JSON objects")
    state = dict(raw_state)
    try:
        validate_state(state)
    except (TypeError, ValueError, AttributeError) as exc:
        if isinstance(exc, KernelError):
            raise
        raise KernelError("generation contains structurally invalid state") from exc
    operation = str(record.get("operation_id", ""))
    validate_operation_id(operation)
    intent = str(record.get("intent_hash", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", intent):
        raise KernelError("generation contains an invalid transition intent hash")
    return Snapshot(
        state=state,
        generation=generation,
        generation_hash=actual,
        filename=filename or "",
        operation_id=operation,
        intent_hash=intent,
        event=dict(raw_event),
    )


def read_generation(path: Path) -> Snapshot:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KernelError(f"invalid generation file: {path.name}") from exc
    return validate_record(record, filename=path.name)


def _current_pointer(snapshot: Snapshot) -> dict[str, Any]:
    return {
        "schema": CURRENT_SCHEMA,
        "generation": snapshot.generation,
        "generation_hash": snapshot.generation_hash,
        "file": snapshot.filename,
    }


def _receipt(snapshot: Snapshot) -> dict[str, Any]:
    pointer = _current_pointer(snapshot)
    return {**pointer, "schema": RECEIPT_SCHEMA}


def _write_receipt(p: StorePaths, snapshot: Snapshot) -> Path:
    """Persist an immutable recovery receipt after CURRENT is verified."""
    target = p.receipts / f"p{snapshot.generation:08d}-{snapshot.generation_hash[:16]}.json"
    expected = canonical_bytes(_receipt(snapshot))
    if target.is_file():
        if target.read_bytes().replace(b"\r\n", b"\n") != expected:
            raise RecoveryRequired("commit receipt path contains different content")
        return target
    temp = p.staging / f"receipt-{snapshot.generation}-{snapshot.generation_hash[:16]}-{time.time_ns()}.tmp"
    _write_fsynced(temp, expected, exclusive=True)
    publish_immutable(temp, target)
    return target


def _read_receipts(root: Path | str) -> tuple[list[Snapshot], list[str]]:
    p = paths(root)
    valid: list[Snapshot] = []
    invalid: list[str] = []
    for path in sorted(p.receipts.glob("p*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or value.get("schema") != RECEIPT_SCHEMA:
                raise KernelError("invalid receipt schema")
            filename = str(value.get("file", ""))
            if Path(filename).name != filename or not filename.endswith(".json"):
                raise KernelError("receipt filename is invalid")
            snapshot = read_generation(p.generations / filename)
            if snapshot.generation != int(value.get("generation", -1)) or snapshot.generation_hash != value.get("generation_hash"):
                raise KernelError("receipt does not match generation")
            _validate_chain_to(root, snapshot)
            valid.append(snapshot)
        except (OSError, ValueError, TypeError, AttributeError, KernelError):
            invalid.append(path.name)
    return valid, invalid


def _quarantine_invalid_receipts(p: StorePaths, names: Iterable[str]) -> list[str]:
    destination = p.control / "quarantine" / "receipts"
    destination.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    for name in names:
        if Path(name).name != name:
            raise RecoveryRequired("invalid receipt name cannot be quarantined safely")
        source = p.receipts / name
        if not source.exists():
            continue
        target = destination / f"{time.time_ns()}-{name}"
        os.replace(source, target)
        moved.append(target.relative_to(p.control).as_posix())
    if moved:
        _fsync_directory(destination)
        _fsync_directory(p.receipts)
    return moved


def _assert_current_receipt_consistency(root: Path | str, current: Snapshot | None) -> None:
    """Reject writers on stale or forked pointers; recovery owns reconciliation."""
    receipts, invalid = _read_receipts(root)
    if invalid:
        raise RecoveryRequired("invalid commit receipts block mutation; run recover")
    if not receipts:
        return
    if current is None:
        raise RecoveryRequired("CURRENT is missing behind a committed receipt; run recover")
    highest = max(item.generation for item in receipts)
    frontier = {item.generation_hash: item for item in receipts if item.generation == highest}
    if len(frontier) != 1:
        raise RecoveryRequired("ambiguous commit receipts block mutation; run recover")
    current_hashes = {item.generation_hash for item in current_chain(root, current)}
    if any(item.generation_hash not in current_hashes for item in receipts):
        winner = next(iter(frontier.values()))
        if winner.generation > current.generation:
            raise RecoveryRequired("CURRENT is older than the committed receipt frontier; run recover")
        raise RecoveryRequired("CURRENT conflicts with committed receipt history; run recover")


def read_current(root: Path | str, *, allow_uninitialized: bool = False) -> Snapshot | None:
    p = paths(root)
    if not p.current.is_file():
        if p.current.exists():
            raise RecoveryRequired("CURRENT exists but is not a regular file; run recover")
        if allow_uninitialized:
            return None
        has_prior_control = any(p.generations.glob("g*.json")) or any(p.receipts.glob("p*.json"))
        if has_prior_control:
            raise RecoveryRequired("CURRENT is missing while prior control records exist; run recover")
        raise KernelError("UNINITIALIZED: run bootstrap")
    try:
        pointer = json.loads(p.current.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecoveryRequired("CURRENT is unreadable; run recover") from exc
    if not isinstance(pointer, dict) or pointer.get("schema") != CURRENT_SCHEMA:
        raise RecoveryRequired("CURRENT schema is invalid; run recover")
    filename = str(pointer.get("file", ""))
    if Path(filename).name != filename or not filename.endswith(".json"):
        raise RecoveryRequired("CURRENT filename is invalid")
    target = p.generations / filename
    if not target.is_file():
        raise RecoveryRequired("CURRENT references a missing generation")
    try:
        snapshot = read_generation(target)
    except KernelError as exc:
        raise RecoveryRequired("CURRENT references an invalid generation") from exc
    try:
        pointer_generation = int(pointer.get("generation", -1))
    except (TypeError, ValueError) as exc:
        raise RecoveryRequired("CURRENT generation is invalid") from exc
    if snapshot.generation != pointer_generation or snapshot.generation_hash != pointer.get("generation_hash"):
        raise RecoveryRequired("CURRENT does not match its immutable generation")
    try:
        _validate_chain_to(root, snapshot)
    except RecoveryRequired:
        raise
    except (KernelError, OSError, ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError) as exc:
        raise RecoveryRequired("CURRENT generation chain is invalid; run recover") from exc
    return snapshot


def scan_generations(root: Path | str) -> tuple[list[Snapshot], list[str]]:
    p = paths(root)
    good: list[Snapshot] = []
    invalid: list[str] = []
    for candidate in sorted(p.generations.glob("g*.json")):
        try:
            good.append(read_generation(candidate))
        except (KernelError, OSError, ValueError, TypeError, AttributeError):
            invalid.append(candidate.name)
    return good, invalid


def _snapshot_record(root: Path | str, snapshot: Snapshot) -> dict[str, Any]:
    return json.loads((paths(root).generations / snapshot.filename).read_text(encoding="utf-8"))


def _validate_chain_to(root: Path | str, tip: Snapshot) -> None:
    records, _ = scan_generations(root)
    by_hash = {item.generation_hash: item for item in records}
    current = tip
    seen: set[str] = set()
    while True:
        if current.generation_hash in seen:
            raise RecoveryRequired("generation chain contains a cycle")
        seen.add(current.generation_hash)
        record = _snapshot_record(root, current)
        previous = record.get("previous_hash")
        if current.generation == 1:
            if previous not in {None, ""}:
                raise RecoveryRequired("genesis generation has a previous hash")
            return
        parent = by_hash.get(str(previous))
        if parent is None or parent.generation != current.generation - 1:
            raise RecoveryRequired("generation chain is incomplete")
        current = parent


def current_chain(root: Path | str, tip: Snapshot | None = None) -> list[Snapshot]:
    tip = tip or read_current(root)
    assert tip is not None
    records, _ = scan_generations(root)
    by_hash = {item.generation_hash: item for item in records}
    chain: list[Snapshot] = []
    current = tip
    while True:
        chain.append(current)
        if current.generation == 1:
            break
        record = _snapshot_record(root, current)
        current = by_hash[str(record["previous_hash"])]
    return list(reversed(chain))


def task_snapshots(root: Path | str, task_id: str) -> list[Snapshot]:
    """Return canonical-chain snapshots for one durable task identity."""
    task_id = str(task_id).strip()
    tip = read_current(root, allow_uninitialized=True)
    if tip is None:
        return []
    return [item for item in current_chain(root, tip) if item.state.get("task_id") == task_id]


def task_id_exists(root: Path | str, task_id: str) -> bool:
    return bool(task_snapshots(root, task_id))


def find_task_revision(root: Path | str, task_id: str, revision: int | None = None) -> Snapshot:
    """Select the latest canonical snapshot for an exact task revision.

    Historical generations remain immutable; this helper never makes the
    selected snapshot current and therefore cannot create a second authority.
    """
    candidates = task_snapshots(root, task_id)
    if not candidates:
        raise KernelError(f"historical task not found: {task_id}")
    if revision is None:
        selected_revision = max(int(item.state.get("revision", 0)) for item in candidates)
    else:
        selected_revision = int(revision)
        if selected_revision < 1:
            raise KernelError("source revision must be positive")
    matches = [item for item in candidates if int(item.state.get("revision", 0)) == selected_revision]
    if not matches:
        raise KernelError(f"historical task revision not found: {task_id}@r{selected_revision:03d}")
    return max(matches, key=lambda item: item.generation)


def find_operation(root: Path | str, operation_id: str, *, committed_only: bool = False) -> list[Snapshot]:
    if not operation_id:
        return []
    if committed_only:
        tip = read_current(root, allow_uninitialized=True)
        candidates = current_chain(root, tip) if tip else []
    else:
        candidates, _ = scan_generations(root)
    return [item for item in candidates if item.operation_id == operation_id]


def _intent_hash(event: Mapping[str, Any], state: Mapping[str, Any]) -> str:
    # Event audit data may contain fresh telemetry observations.  Facades can
    # provide a stable semantic intent for retry binding while retaining the
    # full observation in the immutable event record.
    event_intent = (
        {"kind": event.get("kind"), "intent": event.get("intent")}
        if "intent" in event
        else dict(event)
    )
    return sha256_json({
        "event": event_intent,
        "task_id": state.get("task_id"),
        "revision": state.get("revision"),
        "phase": state.get("phase"),
        "risk": state.get("risk"),
        "contract_hash": state.get("contract_hash"),
    })


def _build_record(*, generation: int, previous_hash: str | None, operation_id: str, intent_hash: str, event: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    validate_state(state)
    payload = {
        "schema": GENERATION_SCHEMA,
        "generation": generation,
        "previous_hash": previous_hash,
        "operation_id": operation_id,
        "intent_hash": intent_hash,
        "committed_at": now_iso(),
        "event": dict(event),
        "state": dict(state),
    }
    return {**payload, "generation_hash": sha256_json(payload)}


def _publish_record(p: StorePaths, record: Mapping[str, Any], operation_id: str, configured_failures: str | None) -> Snapshot:
    generation = int(record["generation"])
    digest = str(record["generation_hash"])
    filename = f"g{generation:08d}-{digest[:16]}.json"
    final = p.generations / filename
    if final.is_file():
        return read_generation(final)
    safe_op = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in operation_id)[:96] or "op"
    temp = p.staging / f"{safe_op}-{time.time_ns()}.generation.tmp"
    failpoint("before_generation_write", configured_failures)
    _write_fsynced(temp, canonical_bytes(record), exclusive=True)
    failpoint("after_generation_write", configured_failures)
    publish_immutable(temp, final)
    failpoint("after_generation_publish", configured_failures)
    return read_generation(final)


def commit_candidate(
    root: Path | str,
    *,
    expected_hash: str | None,
    candidate_state: Mapping[str, Any],
    event: Mapping[str, Any],
    operation_id: str,
    configured_failures: str | None = None,
    projector: Callable[[Snapshot], None] | None = None,
    precommit_validator: Callable[[], None] | None = None,
) -> CommitResult:
    """Commit a complete candidate with CURRENT as the sole linearization point."""
    operation_id = validate_operation_id(operation_id)
    validate_state(candidate_state)
    requested_intent = _intent_hash(event, candidate_state)
    failpoint("before_lock", configured_failures)
    with writer_lock(root):
        failpoint("after_lock", configured_failures)
        p = ensure_layout(root)
        current = read_current(root, allow_uninitialized=True)
        _assert_current_receipt_consistency(root, current)
        current_hash = current.generation_hash if current else None
        all_operation_records = find_operation(root, operation_id)
        if any(item.intent_hash != requested_intent for item in all_operation_records):
            raise KernelError("operation_id was reused with different transition intent")
        # A retry after a post-commit response failure returns the committed
        # result and never appends a duplicate transition.
        for existing in find_operation(root, operation_id, committed_only=True):
            if current and existing.generation <= current.generation:
                if existing.intent_hash != requested_intent:
                    raise KernelError("operation_id was reused with different transition intent")
                _write_receipt(p, current)
                if projector:
                    projector(current)
                return CommitResult(current, committed=False, idempotent=True)
        if current is None:
            prepared_records, invalid_records = scan_generations(root)
            same_operation = [item for item in prepared_records if item.operation_id == operation_id and item.generation == 1]
            receipt_files = list(p.receipts.glob("p*.json"))
            raw_generation_files = list(p.generations.glob("g*.json"))
            compatible_prepared_genesis = (
                bool(prepared_records)
                and all(
                    item.generation == 1
                    and item.state.get("task_id") == candidate_state.get("task_id")
                    and item.state.get("contract_hash") == candidate_state.get("contract_hash")
                    for item in prepared_records
                )
                and len(prepared_records) == len(raw_generation_files)
                and not invalid_records
                and not receipt_files
            )
            if (raw_generation_files or receipt_files) and not compatible_prepared_genesis:
                raise RecoveryRequired("CURRENT is missing while prior control generations exist; run recover instead of bootstrapping a competing task")
        if current_hash != expected_hash:
            raise KernelError("compare-and-swap failed: canonical generation changed; reload and retry")
        generation = (current.generation if current else 0) + 1
        failpoint("before_prepare", configured_failures)
        record = _build_record(
            generation=generation,
            previous_hash=current_hash,
            operation_id=operation_id,
            intent_hash=requested_intent,
            event=event,
            state=candidate_state,
        )
        failpoint("after_prepare", configured_failures)
        # A retry after generation publication but before CURRENT can safely
        # adopt the one matching orphan.  Other orphans remain noncanonical.
        matching = [s for s in find_operation(root, operation_id) if s.generation == generation]
        if any(item.generation != generation for item in all_operation_records):
            raise KernelError("operation_id is already bound to another generation")
        if len(matching) > 1:
            raise RecoveryRequired("multiple prepared generations share one operation id")
        if matching:
            published = matching[0]
            prepared_record = _snapshot_record(root, published)
            if prepared_record.get("previous_hash") != current_hash:
                raise RecoveryRequired("operation id was reused from a different canonical parent")
            if published.intent_hash != requested_intent:
                raise KernelError("operation_id was reused with different transition intent")
            recovered_orphan = True
        else:
            published = _publish_record(p, record, operation_id, configured_failures)
            recovered_orphan = False
        if precommit_validator:
            precommit_validator()
        failpoint("before_pointer_swap", configured_failures)
        atomic_json(p.current, _current_pointer(published))
        failpoint("after_pointer_swap", configured_failures)
        verified = read_current(root)
        assert verified is not None
        if verified.generation_hash != published.generation_hash:
            raise RecoveryRequired("post-commit verification selected a different generation")
        failpoint("before_commit_receipt", configured_failures)
        _write_receipt(p, verified)
        failpoint("after_commit_receipt", configured_failures)
        failpoint("after_verify", configured_failures)
        if projector:
            projector(verified)
        failpoint("after_projection", configured_failures)
        return CommitResult(verified, committed=True, idempotent=False, recovered_orphan=recovered_orphan)


def confirm_committed(root: Path | str, snapshot: Snapshot) -> Snapshot:
    """Finish post-CURRENT receipt durability for a facade-level retry."""
    with writer_lock(root):
        current = read_current(root)
        assert current is not None
        _assert_current_receipt_consistency(root, current)
        if current.generation_hash != snapshot.generation_hash:
            raise KernelError("canonical generation changed while confirming an idempotent retry")
        _write_receipt(ensure_layout(root), current)
        return current


def _recover_once(root: Path | str, *, repair_pointer: bool, configured_failures: str | None = None) -> dict[str, Any]:
    p = ensure_layout(root)
    records, invalid = scan_generations(root)
    receipts, invalid_receipts = _read_receipts(root)
    try:
        current = read_current(root, allow_uninitialized=True)
    except RecoveryRequired as error:
        current = None
        pointer_error = str(error)
    else:
        pointer_error = None
    if current is None and invalid_receipts:
        raise RecoveryRequired("invalid commit receipts prevent deterministic recovery; no state was guessed")
    quarantined_receipts: list[str] = []
    if current is not None and invalid_receipts:
        if not repair_pointer:
            return {
                "status": "RECOVERABLE",
                "generation": current.generation,
                "generation_hash": current.generation_hash,
                "invalid_generations": invalid,
                "invalid_receipts": invalid_receipts,
                "quarantined_receipts": [],
                "orphan_generations": [],
                "pointer_repaired": False,
                "pointer_error": "invalid noncanonical receipts require quarantine",
            }
        quarantined_receipts = _quarantine_invalid_receipts(p, invalid_receipts)
    receipt_winner: Snapshot | None = None
    if receipts:
        highest = max(item.generation for item in receipts)
        distinct = {item.generation_hash: item for item in receipts if item.generation == highest}
        if len(distinct) != 1:
            raise RecoveryRequired("ambiguous commit receipts; no state was guessed")
        receipt_winner = next(iter(distinct.values()))
        winner_chain = {item.generation_hash for item in current_chain(root, receipt_winner)}
        if any(item.generation_hash not in winner_chain for item in receipts):
            raise RecoveryRequired("ambiguous commit receipts span competing histories; no state was guessed")
    if current is not None:
        pointer_repaired = False
        if receipt_winner and (
            receipt_winner.generation > current.generation
            or (receipt_winner.generation == current.generation and receipt_winner.generation_hash != current.generation_hash)
        ):
            if not repair_pointer:
                return {
                    "status": "RECOVERABLE",
                    "generation": receipt_winner.generation,
                    "generation_hash": receipt_winner.generation_hash,
                    "invalid_generations": invalid,
                    "invalid_receipts": invalid_receipts,
                    "orphan_generations": [],
                    "pointer_repaired": False,
                    "pointer_error": "CURRENT is older than the latest committed receipt",
                }
            failpoint("before_recovery_pointer_swap", configured_failures)
            atomic_json(p.current, _current_pointer(receipt_winner))
            failpoint("after_recovery_pointer_swap", configured_failures)
            current = read_current(root)
            assert current is not None
            pointer_repaired = True
        if repair_pointer:
            failpoint("before_recovery_receipt", configured_failures)
            _write_receipt(p, current)
            failpoint("after_recovery_receipt", configured_failures)
        all_hashes = {item.generation_hash for item in current_chain(root, current)}
        orphans = [item.filename for item in records if item.generation_hash not in all_hashes]
        return {
            "status": "RECOVERED" if pointer_repaired or quarantined_receipts else "OK",
            "generation": current.generation,
            "generation_hash": current.generation_hash,
            "invalid_generations": invalid,
            "invalid_receipts": invalid_receipts,
            "quarantined_receipts": quarantined_receipts,
            "orphan_generations": orphans,
            "pointer_repaired": pointer_repaired,
        }
    if not records:
        if pointer_error:
            raise RecoveryRequired(f"{pointer_error}; no valid generation exists")
        return {"status": "UNINITIALIZED", "invalid_generations": invalid, "invalid_receipts": invalid_receipts, "orphan_generations": [], "pointer_repaired": False}
    if receipt_winner is None:
        raise RecoveryRequired("CURRENT is unavailable and no committed generation receipt exists; prepared generations were not promoted")
    winner = receipt_winner
    if repair_pointer:
        failpoint("before_recovery_pointer_swap", configured_failures)
        atomic_json(p.current, _current_pointer(winner))
        failpoint("after_recovery_pointer_swap", configured_failures)
        checked = read_current(root)
        assert checked and checked.generation_hash == winner.generation_hash
        failpoint("before_recovery_receipt", configured_failures)
        _write_receipt(p, checked)
        failpoint("after_recovery_receipt", configured_failures)
    chain_hashes = {item.generation_hash for item in current_chain(root, winner)}
    return {
        "status": "RECOVERED" if repair_pointer else "RECOVERABLE",
        "generation": winner.generation,
        "generation_hash": winner.generation_hash,
        "invalid_generations": invalid,
        "invalid_receipts": invalid_receipts,
        "quarantined_receipts": quarantined_receipts,
        "orphan_generations": [item.filename for item in records if item.generation_hash not in chain_hashes],
        "pointer_repaired": repair_pointer,
        "pointer_error": pointer_error,
    }


def recover(root: Path | str, *, repair_pointer: bool = True, configured_failures: str | None = None) -> dict[str, Any]:
    """Validate state and repair CURRENT only from immutable commit receipts.

    Prepared generations without a receipt are never promoted.  Repair holds
    the same single-writer lock from observation through pointer replacement,
    so it cannot roll back a concurrent committed writer.
    """
    if repair_pointer:
        with writer_lock(root):
            return _recover_once(root, repair_pointer=True, configured_failures=configured_failures)
    return _recover_once(root, repair_pointer=False, configured_failures=configured_failures)


def operation_id(kind: str, *parts: Any) -> str:
    payload = {"kind": kind, "parts": list(parts)}
    return f"{kind.lower()}-{sha256_json(payload)[:24]}"
