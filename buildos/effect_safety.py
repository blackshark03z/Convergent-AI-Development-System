"""Pure safety semantics for one explicit external effect identity."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Callable, Mapping


FORMAT = "buildos.effect-safety.v2"
STATES = {
    "PREPARED",
    "NOT_DISPATCHED",
    "DISPATCH_UNCERTAIN",
    "CONFIRMED",
    "NO_EFFECT_CONFIRMED",
}
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
INTENT_FIELDS = {
    "effect_id", "operation", "target", "request_digest",
    "idempotency_key", "provider_idempotency_enforced",
    "idempotency_evidence",
}
PROOF_KINDS = {"NO_EFFECT_CONFIRMED", "PROVIDER_IDEMPOTENCY"}
_TRUSTED_PROOF_SEAL = object()


class EffectSafetyError(ValueError):
    """An effect record or transition is unsafe or malformed."""


@dataclass(frozen=True)
class VerifiedRetryProof:
    """Opaque result produced only by the explicit trusted-verifier seam."""

    value: dict
    _seal: object


def _text(value: object, *, label: str, maximum: int = 1_024) -> str:
    result = str(value or "").strip()
    if not result or len(result) > maximum or "\0" in result:
        raise EffectSafetyError(f"{label} must be non-empty and at most {maximum} characters")
    return result


def _canonical(value: object) -> bytes:
    return (json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ) + "\n").encode("utf-8")


def normalize_intent(value: Mapping[str, object]) -> dict:
    if not isinstance(value, Mapping):
        raise EffectSafetyError("effect intent must be an object")
    unknown = set(value) - INTENT_FIELDS
    if unknown:
        raise EffectSafetyError(f"effect intent contains unsupported fields: {sorted(unknown)}")
    effect_id = _text(value.get("effect_id"), label="effect_id", maximum=128)
    if not ID_RE.fullmatch(effect_id):
        raise EffectSafetyError("effect_id must use letters, digits, dot, underscore or hyphen")
    request_digest = str(value.get("request_digest") or "").strip().lower()
    if not SHA256_RE.fullmatch(request_digest):
        raise EffectSafetyError("request_digest must be a lowercase SHA-256")
    key = str(value.get("idempotency_key") or "").strip() or None
    evidence = str(value.get("idempotency_evidence") or "").strip() or None
    enforced = value.get("provider_idempotency_enforced", False)
    if not isinstance(enforced, bool):
        raise EffectSafetyError("provider_idempotency_enforced must be boolean")
    if key is not None and (len(key) > 512 or "\0" in key):
        raise EffectSafetyError("idempotency_key is invalid")
    if evidence is not None and (len(evidence) > 2_048 or "\0" in evidence):
        raise EffectSafetyError("idempotency_evidence is invalid")
    if enforced and (not key or not evidence):
        raise EffectSafetyError(
            "provider-enforced idempotency requires the exact key and canonical evidence",
        )
    return {
        "effect_id": effect_id,
        "operation": _text(value.get("operation"), label="operation"),
        "target": _text(value.get("target"), label="target", maximum=2_048),
        "request_digest": request_digest,
        "idempotency_key": key,
        "provider_idempotency_enforced": enforced,
        "idempotency_evidence": evidence,
    }


def effect_identity(intent: Mapping[str, object]) -> str:
    normalized = normalize_intent(intent)
    identity = {
        key: normalized[key] for key in (
            "operation", "target", "request_digest",
        )
    }
    return hashlib.sha256(_canonical(identity)).hexdigest()


def _proof_binding(intent: Mapping[str, object], identity: str) -> dict:
    normalized = normalize_intent(intent)
    return {
        "effect_identity": identity,
        "operation": normalized["operation"],
        "target": normalized["target"],
        "request_digest": normalized["request_digest"],
        "idempotency_key": normalized["idempotency_key"],
    }


def _normalize_proof(value: Mapping[str, object], binding: Mapping[str, object]) -> dict:
    expected = {
        "kind", "effect_identity", "operation", "target", "request_digest",
        "idempotency_key", "evidence", "reference",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise EffectSafetyError("verified retry proof fields are invalid")
    kind = str(value.get("kind") or "").strip().upper()
    if kind not in PROOF_KINDS:
        raise EffectSafetyError("verified retry proof kind is invalid")
    for field in (
        "effect_identity", "operation", "target", "request_digest",
        "idempotency_key",
    ):
        if value.get(field) != binding.get(field):
            raise EffectSafetyError(f"verified retry proof does not match exact {field}")
    if kind == "PROVIDER_IDEMPOTENCY" and not binding.get("idempotency_key"):
        raise EffectSafetyError("provider idempotency proof requires the exact intent key")
    evidence = _text(value.get("evidence"), label="verified retry evidence", maximum=2_048)
    reference = _text(value.get("reference"), label="verified retry reference", maximum=2_048)
    return {
        "kind": kind,
        **dict(binding),
        "evidence": evidence,
        "reference": reference,
    }


def prepare(intent: Mapping[str, object]) -> dict:
    normalized = normalize_intent(intent)
    return {
        "format": FORMAT,
        "effect_identity": effect_identity(normalized),
        "intent": normalized,
        "state": "PREPARED",
        "dispatch_count": 0,
        "provider_reference": None,
        "outcome_evidence": None,
        "verified_retry_proof": None,
    }


def validate_record(value: Mapping[str, object]) -> dict:
    if not isinstance(value, Mapping) or value.get("format") != FORMAT:
        raise EffectSafetyError("effect record format is invalid")
    expected = {
        "format", "effect_identity", "intent", "state", "dispatch_count",
        "provider_reference", "outcome_evidence", "verified_retry_proof",
    }
    if set(value) != expected:
        raise EffectSafetyError("effect record fields are invalid")
    intent = normalize_intent(value.get("intent") or {})
    if value.get("effect_identity") != effect_identity(intent):
        raise EffectSafetyError("effect identity does not match the exact intent")
    state = str(value.get("state") or "")
    if state not in STATES:
        raise EffectSafetyError("effect state is invalid")
    count = value.get("dispatch_count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0 or count > 1:
        raise EffectSafetyError("effect dispatch_count must be zero or one")
    if state in {"PREPARED", "NOT_DISPATCHED"} and count != 0:
        raise EffectSafetyError("non-dispatched effect cannot have a dispatch count")
    if state in {"DISPATCH_UNCERTAIN", "CONFIRMED", "NO_EFFECT_CONFIRMED"} and count != 1:
        raise EffectSafetyError("dispatched effect must retain its one dispatch crossing")
    reference = value.get("provider_reference")
    evidence = value.get("outcome_evidence")
    if reference is not None and not isinstance(reference, str):
        raise EffectSafetyError("provider_reference must be text or null")
    if evidence is not None and not isinstance(evidence, str):
        raise EffectSafetyError("outcome_evidence must be text or null")
    if state == "CONFIRMED" and (not reference or not evidence):
        raise EffectSafetyError("confirmed effect requires provider reference and evidence")
    if state in {"NOT_DISPATCHED", "NO_EFFECT_CONFIRMED"} and not evidence:
        raise EffectSafetyError("no-effect state requires positive evidence")
    raw_proof = value.get("verified_retry_proof")
    proof = None
    if raw_proof is not None:
        proof = _normalize_proof(
            raw_proof, _proof_binding(intent, str(value["effect_identity"])),
        )
        if dict(raw_proof) != proof:
            raise EffectSafetyError("verified retry proof is not canonical")
        if proof["kind"] == "NO_EFFECT_CONFIRMED":
            if state != "NO_EFFECT_CONFIRMED" or evidence != proof["evidence"]:
                raise EffectSafetyError("verified no-effect proof does not match record state")
        elif state != "DISPATCH_UNCERTAIN":
            raise EffectSafetyError("verified idempotency proof requires uncertain dispatch")
    if state == "NO_EFFECT_CONFIRMED" and (
        proof is None or proof["kind"] != "NO_EFFECT_CONFIRMED"
    ):
        raise EffectSafetyError("no-effect confirmation requires trusted verified proof")
    return deepcopy(dict(value))


def verify_retry_proof(
    record: Mapping[str, object],
    *,
    kind: str,
    verifier: Callable[[dict], Mapping[str, object]] | None,
) -> VerifiedRetryProof:
    """Ask one explicit trusted integration to verify an exact retry proof.

    Raw mappings and CLI evidence never become authority. If no trusted
    verifier is supplied, or its response differs from the exact binding, this
    seam fails closed.
    """
    current = validate_record(record)
    if current["state"] != "DISPATCH_UNCERTAIN":
        raise EffectSafetyError("retry proof verification requires uncertain dispatch")
    normalized_kind = str(kind or "").strip().upper()
    if normalized_kind not in PROOF_KINDS:
        raise EffectSafetyError("retry proof verification kind is invalid")
    if verifier is None or not callable(verifier):
        raise EffectSafetyError("trusted retry verifier is required")
    challenge = {
        "kind": normalized_kind,
        **_proof_binding(current["intent"], current["effect_identity"]),
    }
    response = verifier(deepcopy(challenge))
    proof = _normalize_proof(response, challenge)
    if proof["kind"] != normalized_kind:
        raise EffectSafetyError("verified retry proof kind does not match request")
    return VerifiedRetryProof(proof, _TRUSTED_PROOF_SEAL)


def apply_verified_retry_proof(
    record: Mapping[str, object], proof: VerifiedRetryProof,
) -> dict:
    current = validate_record(record)
    if current["state"] != "DISPATCH_UNCERTAIN":
        raise EffectSafetyError("verified retry proof requires uncertain dispatch")
    if not isinstance(proof, VerifiedRetryProof) or proof._seal is not _TRUSTED_PROOF_SEAL:
        raise EffectSafetyError("trusted verified retry proof is required")
    normalized = _normalize_proof(
        proof.value, _proof_binding(current["intent"], current["effect_identity"]),
    )
    current["verified_retry_proof"] = normalized
    if normalized["kind"] == "NO_EFFECT_CONFIRMED":
        current["state"] = "NO_EFFECT_CONFIRMED"
        current["outcome_evidence"] = normalized["evidence"]
    return validate_record(current)


def mark_dispatch_uncertain(record: Mapping[str, object]) -> dict:
    result = validate_record(record)
    if result["state"] != "PREPARED":
        raise EffectSafetyError("dispatch requires a freshly prepared effect intent")
    result["state"] = "DISPATCH_UNCERTAIN"
    result["dispatch_count"] = 1
    return validate_record(result)


def record_dispatch_outcome(record: Mapping[str, object], outcome: Mapping[str, object]) -> dict:
    result = validate_record(record)
    if result["state"] != "DISPATCH_UNCERTAIN":
        raise EffectSafetyError("dispatch outcome requires an uncertain dispatch")
    if not isinstance(outcome, Mapping) or set(outcome) != {"status", "evidence", "reference"}:
        raise EffectSafetyError("dispatch outcome fields are invalid")
    status = str(outcome.get("status") or "").upper()
    evidence = _text(outcome.get("evidence"), label="dispatch outcome evidence", maximum=2_048)
    reference = str(outcome.get("reference") or "").strip() or None
    if status == "CONFIRMED":
        if not reference:
            raise EffectSafetyError("confirmed dispatch requires a provider reference")
        result["state"] = "CONFIRMED"
        result["provider_reference"] = reference
    elif status == "NOT_DISPATCHED":
        if reference is not None:
            raise EffectSafetyError("not-dispatched outcome cannot carry a provider reference")
        result["state"] = "NOT_DISPATCHED"
        result["dispatch_count"] = 0
    else:
        raise EffectSafetyError("dispatch outcome must be CONFIRMED or NOT_DISPATCHED")
    result["outcome_evidence"] = evidence
    return validate_record(result)


def reconcile(
    record: Mapping[str, object],
    *,
    outcome: str,
    evidence: str,
    reference: str | None = None,
    verified_proof: VerifiedRetryProof | None = None,
) -> dict:
    result = validate_record(record)
    if result["state"] != "DISPATCH_UNCERTAIN":
        raise EffectSafetyError("only an uncertain dispatch can be reconciled")
    normalized = str(outcome).strip().upper()
    proof = _text(evidence, label="reconciliation evidence", maximum=2_048)
    provider_reference = str(reference or "").strip() or None
    if normalized == "CONFIRMED":
        if not provider_reference:
            raise EffectSafetyError("confirmed reconciliation requires provider reference")
        result["state"] = "CONFIRMED"
        result["provider_reference"] = provider_reference
    elif normalized == "NO_EFFECT_CONFIRMED":
        if provider_reference is not None:
            raise EffectSafetyError("no-effect reconciliation cannot carry a provider reference")
        if verified_proof is None:
            raise EffectSafetyError(
                "NO_EFFECT_CONFIRMED requires an explicit trusted verifier",
            )
        return apply_verified_retry_proof(result, verified_proof)
    else:
        raise EffectSafetyError("reconciliation outcome must be CONFIRMED or NO_EFFECT_CONFIRMED")
    result["outcome_evidence"] = proof
    return validate_record(result)


def retry_safety(record: Mapping[str, object]) -> dict:
    value = validate_record(record)
    state = value["state"]
    if state == "PREPARED":
        return {"safe": True, "reason_code": "DISPATCH_NOT_CROSSED"}
    if state in {"NOT_DISPATCHED", "NO_EFFECT_CONFIRMED"}:
        return {"safe": True, "reason_code": "POSITIVE_NO_EFFECT_PROOF"}
    if (
        state == "DISPATCH_UNCERTAIN"
        and value["verified_retry_proof"] is not None
        and value["verified_retry_proof"]["kind"] == "PROVIDER_IDEMPOTENCY"
    ):
        return {"safe": True, "reason_code": "EXACT_PROVIDER_IDEMPOTENCY"}
    if state == "CONFIRMED":
        return {"safe": False, "reason_code": "EFFECT_ALREADY_CONFIRMED"}
    return {"safe": False, "reason_code": "AMBIGUOUS_DISPATCH_NO_RETRY_PROOF"}
