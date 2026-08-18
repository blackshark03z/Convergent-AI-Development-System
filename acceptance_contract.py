"""Canonical acceptance/Capsule boundary contract for the portable adoption layer.

The frozen Build OS kernel intentionally keeps acceptance criteria verbatim and
does not impose a length limit.  This module is the single source of truth for
the downstream projection semantics: long criteria are represented by a
deterministic hash-and-pointer token, never silently truncated.
"""
from __future__ import annotations

import hashlib
from typing import Any, Iterable


CONTRACT_ID = "ACCEPTANCE_CAPSULE_CONTRACT_CONSISTENT"
CANONICAL_ACCEPTANCE_LIMIT: int | None = None
CAPSULE_ACCEPTANCE_ITEM_LIMIT = 120
CAPSULE_NORMAL_BYTES = 4096
CAPSULE_HARD_MAX_BYTES = 8192
TARGETED_READ_REQUIRED = "TARGETED_READ_REQUIRED"
CANONICAL_ACCEPTANCE_SOURCE = ".buildos/control/CURRENT -> generations/<file>.json state.acceptance"


def _clean(value: Any) -> str:
    return str(value or "").strip()


def validate_bootstrap_acceptance(items: Iterable[Any]) -> list[str]:
    """Validate the kernel-compatible acceptance shape without narrowing it."""
    result = [_clean(item) for item in items]
    result = [item for item in result if item]
    if not result:
        raise ValueError("at least one acceptance criterion is required")
    return result


def acceptance_projection(item: Any, index: int, *, source: str = ".buildos/control/CURRENT") -> tuple[str, bool]:
    """Return ``(projection, targeted_read_required)`` for one criterion."""
    value = _clean(item)
    if len(value) <= CAPSULE_ACCEPTANCE_ITEM_LIMIT:
        return value, False
    fingerprint = hashlib.sha256(value.encode("utf-8")).hexdigest()
    projection = f"{TARGETED_READ_REQUIRED} acceptance[{index}] sha256={fingerprint}"
    if len(projection) > CAPSULE_ACCEPTANCE_ITEM_LIMIT:
        raise ValueError("canonical acceptance projection exceeds its item bound")
    return projection, True


def project_acceptance(items: Iterable[Any], *, source: str = ".buildos/control/CURRENT") -> tuple[list[str], list[str]]:
    """Project criteria and return targeted-read pointers for long criteria."""
    projected: list[str] = []
    targeted: list[str] = []
    for index, item in enumerate(items):
        value, needs_read = acceptance_projection(item, index, source=source)
        projected.append(value)
        if needs_read:
            targeted.append(f"{value} source={source}")
    return projected, targeted
