"""Carry one unresolved legacy provider ambiguity, without migrating its task."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from . import effect_store
from .effect_safety import mark_dispatch_uncertain
from .legacy_effects import unresolved_legacy_effect


def carry_legacy_ambiguity(root: Path | str, legacy_effect_id: str) -> dict:
    legacy = unresolved_legacy_effect(root, legacy_effect_id)
    request_digest = str(legacy.get("effect_input_sha256") or "")
    contract_digest = str(legacy.get("effect_contract_hash") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", request_digest):
        raise ValueError("legacy effect lacks an exact request digest")
    if not re.fullmatch(r"[0-9a-f]{64}", contract_digest):
        raise ValueError("legacy effect lacks an exact contract digest")
    safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", legacy_effect_id).strip("-.")
    if not safe_id:
        raise ValueError("legacy effect identity cannot be represented safely")
    if len(safe_id) > 100:
        suffix = hashlib.sha256(legacy_effect_id.encode("utf-8")).hexdigest()[:16]
        safe_id = f"{safe_id[:83]}.{suffix}"
    intent = {
        "effect_id": f"legacy.{safe_id}",
        "operation": f"legacy-reconcile:{legacy.get('action_id') or 'external-effect'}",
        "target": f"legacy-effect-contract:{contract_digest}",
        "request_digest": request_digest,
        "idempotency_key": legacy.get("idempotency_key"),
        "provider_idempotency_enforced": False,
        "idempotency_evidence": None,
    }
    record, created = effect_store.create(root, intent)
    if created:
        record = effect_store.update(
            root,
            record["intent"]["effect_id"],
            expected_state="PREPARED",
            transition=mark_dispatch_uncertain,
        )
    return {
        "legacy_effect_id": legacy_effect_id,
        "legacy_state": legacy["state"],
        "effect": record,
    }
