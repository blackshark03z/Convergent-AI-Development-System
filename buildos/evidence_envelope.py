"""Deterministic, read-only evaluation of identity-bound acceptance evidence."""
from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any


class EvidenceEnvelopeError(ValueError):
    """Raised when an evidence envelope violates the bounded prototype schema."""


_VERDICTS = {"PASS", "FAIL", "UNKNOWN"}
_AUTHORITY = {"NOT_REQUIRED", "AUTHORIZED", "MISSING", "DENIED"}
_REVIEW = {"NOT_REQUIRED", "PASS", "BLOCK", "UNKNOWN"}
_ORACLE_CHANGE = {
    "UNCHANGED",
    "CLARIFICATION",
    "REGRESSION_COVERAGE",
    "WEAKENED",
    "IMPLEMENTATION_COUPLED",
}
_ALLOWED_TOP_LEVEL = {
    "goal_ref",
    "candidate",
    "criteria",
    "invariants",
    "authority",
    "review",
    "provenance",
}
_ALLOWED_CANDIDATE = {"base_revision", "candidate_revision"}
_ALLOWED_PROVENANCE = {"execution_environment", "evidence_producer"}
_ALLOWED_CRITERION = {
    "criterion_id",
    "oracle_type",
    "oracle_identity",
    "verifier_identity",
    "verifier_version",
    "result",
    "evidence_refs",
    "independent_evidence_refs",
    "oracle_changed",
    "oracle_change_kind",
    "oracle_change_authorized",
}
_ALLOWED_INVARIANT = {"invariant_id", "result", "evidence_refs"}
_ALLOWED_AUTHORITY = {"required", "status"}
_ALLOWED_REVIEW = {"required", "result", "blocking_findings"}
_FORBIDDEN_KEYS = {
    "phase",
    "retry_history",
    "planner_state",
    "chain_of_thought",
    "subagent_graph",
    "model_routing",
    "session_history",
    "task_lifecycle",
    "workflow_state",
}


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EvidenceEnvelopeError(f"{name} must be an object")
    return value


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceEnvelopeError(f"{name} must be a non-empty string")
    return value.strip()


def _bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise EvidenceEnvelopeError(f"{name} must be boolean")
    return value


def _refs(value: object, name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise EvidenceEnvelopeError(f"{name} must be a list")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_string(item, f"{name}[{index}]"))
    return result


def _choice(value: object, name: str, allowed: set[str]) -> str:
    text = _string(value, name)
    if text not in allowed:
        raise EvidenceEnvelopeError(
            f"{name} must be one of {', '.join(sorted(allowed))}",
        )
    return text


def _check_fields(value: Mapping[str, Any], allowed: set[str], name: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise EvidenceEnvelopeError(
            f"{name} contains unsupported field(s): {', '.join(unknown)}",
        )


def _reject_forbidden(value: object, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise EvidenceEnvelopeError(f"{path} contains a non-string key")
            if key.lower() in _FORBIDDEN_KEYS:
                raise EvidenceEnvelopeError(
                    f"{path}.{key} is orchestration/lifecycle state and is not allowed",
                )
            _reject_forbidden(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_forbidden(nested, f"{path}[{index}]")


def _criterion(entry: object, index: int) -> dict[str, Any]:
    item = _mapping(entry, f"criteria[{index}]")
    _check_fields(item, _ALLOWED_CRITERION, f"criteria[{index}]")
    criterion_id = _string(item.get("criterion_id"), f"criteria[{index}].criterion_id")
    declared = _choice(item.get("result"), f"criteria[{index}].result", _VERDICTS)
    _string(item.get("oracle_type"), f"criteria[{index}].oracle_type")
    _string(item.get("oracle_identity"), f"criteria[{index}].oracle_identity")
    _string(item.get("verifier_identity"), f"criteria[{index}].verifier_identity")
    verifier_version = item.get("verifier_version")
    if verifier_version is not None:
        _string(verifier_version, f"criteria[{index}].verifier_version")

    evidence_refs = _refs(item.get("evidence_refs"), f"criteria[{index}].evidence_refs")
    independent_refs = _refs(
        item.get("independent_evidence_refs"),
        f"criteria[{index}].independent_evidence_refs",
    )
    changed = item.get("oracle_changed", False)
    _bool(changed, f"criteria[{index}].oracle_changed")
    change_kind = item.get("oracle_change_kind", "UNCHANGED")
    change_kind = _choice(
        change_kind,
        f"criteria[{index}].oracle_change_kind",
        _ORACLE_CHANGE,
    )
    change_authorized = item.get("oracle_change_authorized", False)
    _bool(change_authorized, f"criteria[{index}].oracle_change_authorized")

    if not changed and change_kind != "UNCHANGED":
        raise EvidenceEnvelopeError(
            f"criteria[{index}].oracle_change_kind must be UNCHANGED when oracle_changed is false",
        )
    if changed and change_kind == "UNCHANGED":
        raise EvidenceEnvelopeError(
            f"criteria[{index}].oracle_change_kind must describe the oracle change",
        )

    reasons: list[str] = []
    effective = declared
    if declared in {"PASS", "FAIL"} and not evidence_refs:
        effective = "UNKNOWN"
        reasons.append("CRITERION_EVIDENCE_MISSING")

    if changed:
        if change_kind in {"WEAKENED", "IMPLEMENTATION_COUPLED"}:
            effective = "UNKNOWN"
            reasons.append("ORACLE_INTEGRITY_UNPROVEN")
        elif change_kind == "CLARIFICATION":
            if not change_authorized or not independent_refs:
                effective = "UNKNOWN"
                reasons.append("ORACLE_CLARIFICATION_UNPROVEN")
        elif change_kind == "REGRESSION_COVERAGE" and not independent_refs:
            effective = "UNKNOWN"
            reasons.append("REGRESSION_SELF_PROOF_ONLY")

    return {
        "criterion_id": criterion_id,
        "declared_result": declared,
        "effective_result": effective,
        "reason_codes": sorted(set(reasons)),
    }


def _invariant(entry: object, index: int) -> dict[str, Any]:
    item = _mapping(entry, f"invariants[{index}]")
    _check_fields(item, _ALLOWED_INVARIANT, f"invariants[{index}]")
    invariant_id = _string(item.get("invariant_id"), f"invariants[{index}].invariant_id")
    declared = _choice(item.get("result"), f"invariants[{index}].result", _VERDICTS)
    evidence_refs = _refs(item.get("evidence_refs"), f"invariants[{index}].evidence_refs")
    reasons: list[str] = []
    effective = declared
    if declared in {"PASS", "FAIL"} and not evidence_refs:
        effective = "UNKNOWN"
        reasons.append("INVARIANT_EVIDENCE_MISSING")
    return {
        "invariant_id": invariant_id,
        "declared_result": declared,
        "effective_result": effective,
        "reason_codes": reasons,
    }


def evaluate_envelope(value: object) -> dict[str, Any]:
    """Validate an envelope and derive a verdict without mutating external state."""
    envelope = _mapping(value, "envelope")
    _reject_forbidden(envelope)
    unknown_top = sorted(set(envelope) - _ALLOWED_TOP_LEVEL)
    if unknown_top:
        raise EvidenceEnvelopeError(
            f"unsupported top-level field(s): {', '.join(unknown_top)}",
        )

    goal_ref = _string(envelope.get("goal_ref"), "goal_ref")
    candidate = _mapping(envelope.get("candidate"), "candidate")
    _check_fields(candidate, _ALLOWED_CANDIDATE, "candidate")
    base_revision = _string(candidate.get("base_revision"), "candidate.base_revision")
    candidate_revision = _string(
        candidate.get("candidate_revision"),
        "candidate.candidate_revision",
    )

    provenance = _mapping(envelope.get("provenance"), "provenance")
    _check_fields(provenance, _ALLOWED_PROVENANCE, "provenance")
    execution_environment = _string(
        provenance.get("execution_environment"),
        "provenance.execution_environment",
    )
    evidence_producer = _string(
        provenance.get("evidence_producer"),
        "provenance.evidence_producer",
    )

    raw_criteria = envelope.get("criteria")
    if not isinstance(raw_criteria, list) or not raw_criteria:
        raise EvidenceEnvelopeError("criteria must be a non-empty list")
    criteria = [_criterion(item, index) for index, item in enumerate(raw_criteria)]

    raw_invariants = envelope.get("invariants", [])
    if not isinstance(raw_invariants, list):
        raise EvidenceEnvelopeError("invariants must be a list")
    invariants = [_invariant(item, index) for index, item in enumerate(raw_invariants)]

    authority = _mapping(envelope.get("authority", {"required": False, "status": "NOT_REQUIRED"}), "authority")
    _check_fields(authority, _ALLOWED_AUTHORITY, "authority")
    authority_required = authority.get("required", False)
    _bool(authority_required, "authority.required")
    authority_status = _choice(authority.get("status", "NOT_REQUIRED"), "authority.status", _AUTHORITY)

    review = _mapping(
        envelope.get("review", {"required": False, "result": "NOT_REQUIRED", "blocking_findings": []}),
        "review",
    )
    _check_fields(review, _ALLOWED_REVIEW, "review")
    review_required = review.get("required", False)
    _bool(review_required, "review.required")
    review_result = _choice(review.get("result", "NOT_REQUIRED"), "review.result", _REVIEW)
    blocking_findings = _refs(review.get("blocking_findings"), "review.blocking_findings")

    not_verified: list[str] = []
    unknown: list[str] = []

    for result in criteria:
        if result["effective_result"] == "FAIL":
            not_verified.append(f"CRITERION_FAILED:{result['criterion_id']}")
        elif result["effective_result"] == "UNKNOWN":
            unknown.append(f"CRITERION_UNKNOWN:{result['criterion_id']}")
        unknown.extend(result["reason_codes"])

    for result in invariants:
        if result["effective_result"] == "FAIL":
            not_verified.append(f"INVARIANT_FAILED:{result['invariant_id']}")
        elif result["effective_result"] == "UNKNOWN":
            unknown.append(f"INVARIANT_UNKNOWN:{result['invariant_id']}")
        unknown.extend(result["reason_codes"])

    if authority_required:
        if authority_status == "DENIED":
            not_verified.append("REQUIRED_AUTHORITY_DENIED")
        elif authority_status != "AUTHORIZED":
            unknown.append("REQUIRED_AUTHORITY_MISSING")

    if blocking_findings or review_result == "BLOCK":
        not_verified.append("BLOCKING_REVIEW_FINDING")
    elif review_required and review_result != "PASS":
        unknown.append("REQUIRED_REVIEW_INCOMPLETE")

    if not_verified:
        verdict = "NOT_VERIFIED"
    elif unknown:
        verdict = "UNKNOWN"
    else:
        verdict = "VERIFIED"

    return {
        "goal_ref": goal_ref,
        "candidate": {
            "base_revision": base_revision,
            "candidate_revision": candidate_revision,
        },
        "provenance": {
            "execution_environment": execution_environment,
            "evidence_producer": evidence_producer,
        },
        "criterion_results": criteria,
        "invariant_results": invariants,
        "authority": {
            "required": authority_required,
            "status": authority_status,
        },
        "review": {
            "required": review_required,
            "result": review_result,
            "blocking_findings": blocking_findings,
        },
        "verdict": verdict,
        "reason_codes": sorted(set(not_verified + unknown)),
        "read_only": True,
    }


def evaluate_file(root: Path, path: Path) -> dict[str, Any]:
    """Load one repo-local JSON envelope and derive its verdict read-only."""
    root = root.resolve()
    candidate = path if path.is_absolute() else root / path
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise EvidenceEnvelopeError("evidence envelope input must stay inside repository root") from exc
    try:
        value = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceEnvelopeError(f"cannot read evidence envelope: {exc}") from exc
    return evaluate_envelope(value)
