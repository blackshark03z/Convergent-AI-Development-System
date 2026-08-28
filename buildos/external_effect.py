"""Explicit external boundary built from Thin Guard and Effect Safety."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable, Mapping

from .effect_safety import (
    EffectSafetyError,
    apply_verified_retry_proof,
    mark_dispatch_uncertain,
    normalize_intent,
    reconcile as reconcile_record,
    record_dispatch_outcome,
    retry_safety,
    verify_retry_proof,
)
from . import effect_store
from .git_adapter import boundary_snapshot
from .thin_guard import check


Dispatcher = Callable[[dict], Mapping[str, object]]


def _guard_evidence(evaluated: Mapping[str, object]) -> dict:
    return {
        "guard_result": evaluated["result"],
        "reason_codes": evaluated["reason_codes"],
        "evaluated_head": evaluated["observed_head"],
        "evaluated_tree": evaluated["observed_tree"],
        "evaluated_observation_digest": evaluated["observed_state_digest"],
        "pre_dispatch_head": None,
        "pre_dispatch_tree": None,
        "pre_dispatch_observation_digest": None,
        "dispatched": False,
        "effect_state": None,
    }


def execute_external_effect(
    root: Path | str,
    *,
    base: str,
    intent: Mapping[str, object],
    dispatcher: Dispatcher,
    expected_paths: Iterable[str] = (),
    strict_paths: Iterable[str] = (),
    prohibited_paths: Iterable[str] = (),
) -> dict:
    """Persist exact intent, cross one explicit dispatch seam once, and reconcile."""
    normalized_intent = normalize_intent(intent)
    evaluated = check(
        root,
        base=base,
        boundary="EXTERNAL",
        expected_paths=expected_paths,
        strict_paths=strict_paths,
        prohibited_paths=prohibited_paths,
    )
    evidence = _guard_evidence(evaluated)
    if evaluated["result"] == "BLOCK":
        return evidence

    try:
        record, created = effect_store.create(
            evaluated["observed_root"], normalized_intent,
        )
    except effect_store.EffectStoreError as exc:
        evidence.update({
            "guard_result": "BLOCK",
            "reason_codes": ["EFFECT_INTENT_MISMATCH"],
            "effect_error": str(exc),
        })
        return evidence
    evidence["effect_state"] = record["state"]
    evidence["effect_identity"] = record["effect_identity"]
    if not created:
        if record["intent"] != normalized_intent:
            evidence.update({
                "guard_result": "BLOCK",
                "reason_codes": ["EFFECT_INTENT_MISMATCH"],
                "retry_safety": {
                    "safe": False,
                    "reason_code": "EXACT_INTENT_MISMATCH",
                },
            })
            return evidence
        if record["state"] != "PREPARED":
            safety = retry_safety(record)
            evidence.update({
                "guard_result": "BLOCK",
                "reason_codes": ["BLIND_RETRY_BLOCKED"],
                "retry_safety": safety,
            })
            return evidence

    try:
        pre_dispatch = boundary_snapshot(
            evaluated["observed_root"], evaluated["base_commit"],
        )
    except (OSError, RuntimeError) as exc:
        evidence.update({
            "guard_result": "BLOCK",
            "reason_codes": ["BLOCK_STALE_STATE"],
            "pre_dispatch_error": str(exc),
        })
        return evidence
    evidence.update({
        "pre_dispatch_head": pre_dispatch["head"],
        "pre_dispatch_tree": pre_dispatch["tree"],
        "pre_dispatch_observation_digest": pre_dispatch["observed_state_digest"],
    })
    if pre_dispatch["observed_state_digest"] != evaluated["observed_state_digest"]:
        evidence.update({
            "guard_result": "BLOCK",
            "reason_codes": ["BLOCK_STALE_STATE"],
        })
        return evidence

    uncertain = effect_store.update(
        evaluated["observed_root"],
        normalized_intent["effect_id"],
        expected_state="PREPARED",
        transition=mark_dispatch_uncertain,
    )
    evidence["effect_state"] = uncertain["state"]
    try:
        outcome = dispatcher(dict(normalized_intent))
    except Exception as exc:
        evidence.update({
            "dispatched": True,
            "effect_state": "DISPATCH_UNCERTAIN",
            "dispatch_error": f"{type(exc).__name__}: {exc}",
            "reason_codes": ["DISPATCH_UNCERTAIN"],
        })
        return evidence

    evidence["dispatched"] = True
    try:
        resolved = effect_store.update(
            evaluated["observed_root"],
            normalized_intent["effect_id"],
            expected_state="DISPATCH_UNCERTAIN",
            transition=lambda current: record_dispatch_outcome(current, outcome),
        )
    except (EffectSafetyError, effect_store.EffectStoreError) as exc:
        evidence.update({
            "effect_state": "DISPATCH_UNCERTAIN",
            "outcome_error": str(exc),
            "reason_codes": ["DISPATCH_UNCERTAIN"],
        })
        return evidence
    evidence.update({
        "effect_state": resolved["state"],
        "provider_reference": resolved["provider_reference"],
        "outcome_evidence": resolved["outcome_evidence"],
    })
    return evidence


def inspect_effect(root: Path | str, effect_id: str) -> dict:
    record = effect_store.load(root, effect_id)
    return {**record, "retry_safety": retry_safety(record)}


def list_effects(root: Path | str) -> list[dict]:
    return [
        {**record, "retry_safety": retry_safety(record)}
        for record in effect_store.list_records(root)
    ]


def reconcile_effect(
    root: Path | str,
    effect_id: str,
    *,
    outcome: str,
    evidence: str,
    reference: str | None = None,
) -> dict:
    return effect_store.update(
        root,
        effect_id,
        expected_state="DISPATCH_UNCERTAIN",
        transition=lambda current: reconcile_record(
            current, outcome=outcome, evidence=evidence, reference=reference,
        ),
    )


def verify_effect_retry_proof(
    root: Path | str,
    effect_id: str,
    *,
    kind: str,
    verifier: Callable[[dict], Mapping[str, object]] | None,
) -> dict:
    """Persist proof only after an explicit trusted verifier checks exact binding."""
    current = effect_store.load(root, effect_id)
    proof = verify_retry_proof(current, kind=kind, verifier=verifier)
    return effect_store.update(
        root,
        effect_id,
        expected_state="DISPATCH_UNCERTAIN",
        transition=lambda record: apply_verified_retry_proof(record, proof),
    )


def effect_retry_safety(root: Path | str, effect_id: str) -> dict:
    return retry_safety(effect_store.load(root, effect_id))
