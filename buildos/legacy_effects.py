"""Read-only detection of unresolved v1.25 external-effect evidence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TERMINAL = {"COMMITTED", "RESOLVED_NO_EFFECT"}
MAX_JSON_BYTES = 8 * 1024 * 1024


def _safe_file(path: Path, *, parent: Path) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"legacy control file is not a regular file: {path.name}")
    resolved = path.resolve(strict=True)
    resolved.relative_to(parent.resolve(strict=True))
    if resolved.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"legacy control file is too large: {path.name}")
    return resolved


def _json(path: Path, *, parent: Path) -> dict[str, Any]:
    value = json.loads(_safe_file(path, parent=parent).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"legacy control file is not an object: {path.name}")
    return value


def inspect_legacy_effects(root: Path | str) -> dict:
    """Return unresolved effects from CURRENT without mutating legacy state."""
    repository = Path(root).resolve()
    control = repository / ".buildos" / "control"
    current = control / "CURRENT"
    if not current.exists():
        return {"status": "ABSENT", "unresolved": []}
    try:
        pointer = _json(current, parent=control)
        filename = str(pointer.get("file") or "")
        if Path(filename).name != filename or not filename.endswith(".json"):
            raise ValueError("legacy CURRENT filename is invalid")
        generation = _json(control / "generations" / filename, parent=control / "generations")
        state = generation.get("state") or {}
        ledger = ((state.get("execution") or {}).get("effect_ledger") or {})
        if not isinstance(ledger, dict):
            raise ValueError("legacy effect ledger is invalid")
        unresolved = []
        for effect_id, record in sorted(ledger.items()):
            if not isinstance(record, dict):
                raise ValueError("legacy effect record is invalid")
            if record.get("state") not in TERMINAL:
                unresolved.append({
                    "effect_id": str(effect_id),
                    "state": record.get("state"),
                    "action_id": record.get("action_id"),
                    "effect_contract_hash": record.get("effect_contract_hash"),
                    "effect_input_sha256": record.get("effect_input_sha256"),
                    "idempotency_key": record.get("idempotency_key"),
                    "provider_reference": record.get("provider_reference"),
                    "reconciliation": record.get("reconciliation"),
                })
        return {
            "status": "UNRESOLVED" if unresolved else "HISTORICAL_ONLY",
            "current_generation": filename,
            "unresolved": unresolved,
        }
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return {
            "status": "UNREADABLE",
            "unresolved": [],
            "error": str(exc),
        }
