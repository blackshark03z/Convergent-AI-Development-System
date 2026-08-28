"""Atomic durable storage only for external-effect ambiguity."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Callable, Iterator, Mapping

from . import git_adapter
from .effect_safety import EffectSafetyError, normalize_intent, prepare, validate_record


class EffectStoreError(RuntimeError):
    """Durable effect state is unavailable, corrupt, or concurrently changed."""


def _runtime_root(root: Path | str) -> Path:
    repository = Path(root).resolve()
    top = git_adapter._run(repository, "rev-parse", "--show-toplevel", check=False)
    if top.returncode != 0:
        raise EffectStoreError("effect storage requires an observable Git repository")
    git_top = Path(top.stdout.strip()).resolve()
    if os.path.normcase(str(repository)) != os.path.normcase(str(git_top)):
        raise EffectStoreError(f"repository root must be the Git top-level: {git_top}")
    raw = git_adapter._run(repository, "rev-parse", "--git-common-dir").stdout.strip()
    common = Path(raw)
    if not common.is_absolute():
        common = repository / common
    return (common / "buildos" / "effects").resolve(strict=False)


def _is_reparse(path: Path) -> bool:
    try:
        stat = path.lstat()
    except OSError:
        return False
    return path.is_symlink() or bool(getattr(stat, "st_file_attributes", 0) & 0x400)


def _ensure_directory(root: Path | str) -> Path:
    target = _runtime_root(root)
    current = target.anchor and Path(target.anchor) or Path()
    for part in target.parts[1:] if target.anchor else target.parts:
        current = current / part
        if current.exists() and _is_reparse(current):
            raise EffectStoreError(f"effect storage cannot traverse a link or reparse point: {current}")
    target.mkdir(parents=True, exist_ok=True)
    if _is_reparse(target):
        raise EffectStoreError("effect storage directory cannot be a link or reparse point")
    return target


def _record_path(root: Path | str, effect_id: str) -> Path:
    normalized = normalize_intent({
        "effect_id": effect_id,
        "operation": "locator",
        "target": "locator",
        "request_digest": "0" * 64,
    })["effect_id"]
    return _runtime_root(root) / f"{normalized}.json"


def _digest(value: Mapping[str, object]) -> str:
    data = (json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ) + "\n").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


@contextmanager
def _locked(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"\0")
            handle.flush()
            os.fsync(handle.fileno())
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _read(path: Path) -> dict:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EffectStoreError(f"effect record is unreadable: {path.name}") from exc
    try:
        return validate_record(raw)
    except EffectSafetyError as exc:
        raise EffectStoreError(f"effect record is invalid: {path.name}: {exc}") from exc


def _atomic_write(path: Path, value: Mapping[str, object]) -> None:
    payload = (json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.stem}-", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def load(root: Path | str, effect_id: str) -> dict:
    path = _record_path(root, effect_id)
    if not path.is_file():
        raise EffectStoreError(f"effect record does not exist: {effect_id}")
    return _read(path)


def list_records(root: Path | str) -> list[dict]:
    directory = _runtime_root(root)
    if not directory.exists():
        return []
    if not directory.is_dir() or _is_reparse(directory):
        raise EffectStoreError("effect storage is not a safe directory")
    return [_read(path) for path in sorted(directory.glob("*.json"))]


def create(root: Path | str, intent: Mapping[str, object]) -> tuple[dict, bool]:
    record = prepare(intent)
    directory = _ensure_directory(root)
    path = directory / f"{record['intent']['effect_id']}.json"
    with _locked(directory / ".store.lock"):
        for candidate in sorted(directory.glob("*.json")):
            existing = _read(candidate)
            if existing["effect_identity"] == record["effect_identity"]:
                return existing, False
        if path.exists():
            existing = _read(path)
            if existing["effect_identity"] != record["effect_identity"]:
                raise EffectStoreError("effect_id is already bound to different exact intent")
            return existing, False
        _atomic_write(path, record)
        return record, True


def update(
    root: Path | str,
    effect_id: str,
    *,
    expected_state: str,
    transition: Callable[[Mapping[str, object]], dict],
) -> dict:
    path = _record_path(root, effect_id)
    directory = _ensure_directory(root)
    with _locked(directory / ".store.lock"):
        if not path.is_file():
            raise EffectStoreError(f"effect record does not exist: {effect_id}")
        current = _read(path)
        if current["state"] != expected_state:
            raise EffectStoreError(
                f"effect state changed concurrently: expected {expected_state}, observed {current['state']}",
            )
        before = _digest(current)
        result = validate_record(transition(current))
        if _digest(_read(path)) != before:
            raise EffectStoreError("effect record changed concurrently")
        _atomic_write(path, result)
        return result
