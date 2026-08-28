"""Read-only Worker grounding and typed Decision Request derivation.

The Worker owns repository interpretation.  Build OS verifies that the report
is bound to the exact observed worktree and that repository evidence still
matches, then classifies conflicts from declared authority metadata.  It does
not interpret product meaning or let a Worker resolution rewrite canonical
Tech Lead claims.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from fnmatch import fnmatchcase
import os
from pathlib import Path
import re
from typing import Any, Mapping

from .work_contract import (
    ID_RE, SHA_RE, WorkContractError, canonical_contract_bytes, validate_contract,
)


SCHEMA = "buildos.grounding-report.v1"
PROJECTION_SCHEMA = "buildos.grounding-projection.v1"
DECISION_RESOLUTION_SCHEMA = "buildos.decision-resolution.v1"
DECISION_HISTORY_SCHEMA = "buildos.decision-history.v1"
TRUSTED_DECISION_RESOLUTION_SHA256_ENV = "BUILDOS_TRUSTED_DECISION_RESOLUTION_SHA256"
MAX_REPORT_BYTES = 256 * 1024
MAX_DECISION_RESOLUTION_BYTES = 64 * 1024
MAX_ITEMS = 256
GIT_OBJECT_RE = re.compile(r"^[0-9a-f]{40,64}$")
OUTCOMES = {"VERIFIED", "CONTRADICTED", "UNKNOWN"}
DISCOVERY_STATUSES = {"VERIFIED", "HYPOTHESIS", "UNKNOWN"}
EVIDENCE_KINDS = {"REPO_FILE", "REPO_OBSERVATION", "EXTERNAL_REFERENCE"}
REPO_OBSERVATIONS = {"HEAD", "TREE", "PRODUCT_STATE_DIGEST"}
REQUESTED_ACTIONS = {"READ_ONLY", "LOCAL_MUTATION", "LOCAL_HIGH_COST", "EXTERNAL_EFFECT"}
PRODUCT_CHANGE_MODES = {"PRODUCT_DELTA", "NO_SOURCE_DELTA"}
RISKS = {"AUTO", "R0", "R1", "R2", "R3"}
CANONICAL_DECISION_TYPES = {
    "INTENT": "PRODUCT_INTENT",
    "ACCEPTANCE": "PRODUCT_INTENT",
    "DECISION": "CANONICAL_ARCHITECTURE",
    "CONSTRAINT": "BUSINESS_CONSTRAINT",
}


class GroundingError(WorkContractError):
    """Raised when Worker grounding is stale, unbound, or malformed."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def _object(value: Any, *, label: str, keys: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise GroundingError(f"{label} must be an object")
    observed = set(value)
    if observed != keys:
        raise GroundingError(
            f"{label} fields are invalid; missing={sorted(keys - observed)} "
            f"unexpected={sorted(observed - keys)}"
        )
    return value


def _text(value: Any, *, label: str, maximum: int = 4_000, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        raise GroundingError(f"{label} must be a string")
    result = value.strip()
    if not result:
        if nullable:
            return None
        raise GroundingError(f"{label} must not be empty")
    if len(result) > maximum:
        raise GroundingError(f"{label} exceeds {maximum} characters")
    return result


def _identifier(value: Any, *, label: str) -> str:
    result = _text(value, label=label, maximum=128)
    assert isinstance(result, str)
    if not ID_RE.fullmatch(result):
        raise GroundingError(f"{label} is not a portable identifier")
    return result


def _enum(value: Any, *, label: str, allowed: set[str]) -> str:
    result = _text(value, label=label, maximum=64)
    assert isinstance(result, str)
    result = result.upper()
    if result not in allowed:
        raise GroundingError(f"{label} must be one of {sorted(allowed)}")
    return result


def _ids(value: Any, *, label: str, maximum: int = MAX_ITEMS) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum:
        raise GroundingError(f"{label} must be an array of at most {maximum} identifiers")
    result = [_identifier(item, label=f"{label}[{index}]") for index, item in enumerate(value)]
    if len(result) != len(set(result)):
        raise GroundingError(f"{label} contains duplicates")
    return result


def _strings(value: Any, *, label: str, maximum: int = MAX_ITEMS, item_maximum: int = 2_048) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum:
        raise GroundingError(f"{label} must be an array of at most {maximum} strings")
    result: list[str] = []
    for index, item in enumerate(value):
        text = _text(item, label=f"{label}[{index}]", maximum=item_maximum)
        assert isinstance(text, str)
        result.append(text)
    if len(result) != len(set(result)):
        raise GroundingError(f"{label} contains duplicates")
    return result


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decision_request_hash(request: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(dict(request))).hexdigest()


def decision_request_source_reference(request: Mapping[str, Any]) -> str:
    return (
        f"buildos-decision-request:{request['request_id']}:"
        f"sha256:{decision_request_hash(request)}"
    )


def canonical_decision_resolution_bytes(value: Mapping[str, Any]) -> bytes:
    return _canonical_bytes(dict(value))


def validate_decision_resolution(
    value: Any, request: Mapping[str, Any], *, require_transport: bool = False,
) -> dict[str, Any]:
    """Validate one authority decision against the exact immutable open request."""
    row = _object(
        value, label="Decision resolution",
        keys={
            "schema", "request_id", "request_sha256", "contract_hash",
            "claim_id", "decision_type", "decision", "authority",
        },
    )
    if row["schema"] != DECISION_RESOLUTION_SCHEMA:
        raise GroundingError(f"Decision resolution schema must be {DECISION_RESOLUTION_SCHEMA}")
    expected_request_hash = decision_request_hash(request)
    exact = {
        "request_id": request.get("request_id"),
        "request_sha256": expected_request_hash,
        "contract_hash": request.get("contract_hash"),
        "claim_id": request.get("claim_id"),
        "decision_type": request.get("decision_type"),
    }
    for key, expected in exact.items():
        if row[key] != expected:
            raise GroundingError(f"Decision resolution {key} does not match the exact open request")
    decision = _enum(
        row["decision"], label="Decision resolution.decision",
        allowed={"CONFIRM_CANONICAL", "PROVIDE_DECISION"},
    )
    if decision not in set(request.get("options") or []):
        raise GroundingError("Decision resolution is not an allowed option for the open request")
    authority = _object(
        row["authority"], label="Decision resolution.authority",
        keys={"role", "identity", "authority_reference", "decided_at"},
    )
    role = _enum(authority["role"], label="Decision resolution.authority.role", allowed={"OWNER", "TECH_LEAD"})
    if role != request.get("requested_from"):
        raise GroundingError("Decision resolution was not issued by the authority named by the request")
    normalized = {
        "schema": DECISION_RESOLUTION_SCHEMA,
        **exact,
        "decision": decision,
        "authority": {
            "role": role,
            "identity": _text(authority["identity"], label="Decision resolution.authority.identity", maximum=256),
            "authority_reference": _text(
                authority["authority_reference"],
                label="Decision resolution.authority.authority_reference", maximum=2_048,
            ),
            "decided_at": _text(authority["decided_at"], label="Decision resolution.authority.decided_at", maximum=128),
        },
    }
    if require_transport:
        digest = hashlib.sha256(canonical_decision_resolution_bytes(normalized)).hexdigest()
        supplied = str(os.environ.get(TRUSTED_DECISION_RESOLUTION_SHA256_ENV) or "").strip().lower()
        if not SHA_RE.fullmatch(supplied):
            raise GroundingError(
                "Decision resolution requires trusted launcher binding in "
                f"{TRUSTED_DECISION_RESOLUTION_SHA256_ENV}"
            )
        if not hmac.compare_digest(supplied, digest):
            raise GroundingError("trusted launcher Decision resolution hash does not match validated evidence")
    return normalized


def load_decision_resolution(
    path: Path | str, requests: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], str, bytes]:
    source = Path(path)
    try:
        payload = source.read_bytes()
    except OSError as exc:
        raise GroundingError(f"Decision resolution is unreadable: {source}") from exc
    if len(payload) > MAX_DECISION_RESOLUTION_BYTES:
        raise GroundingError(
            f"Decision resolution exceeds {MAX_DECISION_RESOLUTION_BYTES} bytes"
        )
    try:
        raw = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GroundingError("Decision resolution is not valid JSON") from exc
    request_id = str(raw.get("request_id") or "") if isinstance(raw, Mapping) else ""
    request = requests.get(request_id)
    if request is None:
        raise GroundingError("Decision resolution does not target an open canonical request")
    normalized = validate_decision_resolution(raw, request, require_transport=True)
    canonical = canonical_decision_resolution_bytes(normalized)
    digest = hashlib.sha256(canonical).hexdigest()
    return normalized, digest, canonical


def validate_contract_supersession(
    source_contract: Mapping[str, Any], requests: list[Mapping[str, Any]],
    contract: Mapping[str, Any], contract_hash: str,
) -> None:
    """Require an exact authority-linked next Contract revision for open requests."""
    if not requests:
        raise GroundingError("Work Contract supersession requires an open Decision Request")
    if contract.get("contract_id") != source_contract.get("contract_id"):
        raise GroundingError("superseding Work Contract must retain contract_id")
    if int(contract.get("revision", 0)) != int(source_contract.get("revision", 0)) + 1:
        raise GroundingError("superseding Work Contract must be the next Contract revision")
    if (contract.get("metadata") or {}).get("parent_contract_hash") != source_contract.get("hash"):
        raise GroundingError("superseding Work Contract must bind the active parent_contract_hash")
    references = set((contract.get("metadata") or {}).get("source_context_refs") or [])
    issuer_role = (contract.get("issuer") or {}).get("role")
    for request in requests:
        if issuer_role != request.get("requested_from"):
            raise GroundingError("superseding Work Contract lacks the authority named by an open request")
        if decision_request_source_reference(request) not in references:
            raise GroundingError("superseding Work Contract does not link the exact open Decision Request")
    if not SHA_RE.fullmatch(str(contract_hash)):
        raise GroundingError("superseding Work Contract hash is invalid")


def decision_history_entry(
    request: Mapping[str, Any], source_contract: Mapping[str, Any], *,
    resolution_kind: str, resolution_hash: str,
    resolution_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema": DECISION_HISTORY_SCHEMA,
        "request": dict(request),
        "request_sha256": decision_request_hash(request),
        "source_contract": {
            "contract_id": source_contract["contract_id"],
            "revision": source_contract["revision"],
            "hash": source_contract["hash"],
        },
        "resolution_kind": resolution_kind,
        "resolution_hash": resolution_hash,
        "resolution_evidence": dict(resolution_evidence),
    }


def merge_decision_history(
    prior: list[Mapping[str, Any]], additions: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for raw in [*prior, *additions]:
        item = dict(raw)
        key = (
            str(item.get("request_sha256") or ""),
            str(item.get("resolution_kind") or ""),
            str(item.get("resolution_hash") or ""),
        )
        existing = merged.get(key)
        if existing is not None and existing != item:
            raise GroundingError("Decision history identity is bound to conflicting evidence")
        merged[key] = item
    return [merged[key] for key in sorted(merged)]


def _safe_repo_locator(locator: str) -> Path:
    relative = Path(locator.replace("\\", "/"))
    if relative.is_absolute() or ".." in relative.parts:
        raise GroundingError(f"repository evidence path escapes the target repository: {locator}")
    relative_parts = [part.casefold() for part in relative.parts]
    if relative_parts and (relative_parts[0] == ".buildos" or ".git" in relative_parts):
        raise GroundingError(
            f"repository evidence cannot cite repository control state: {locator}"
        )
    return relative


def _repo_file(root: Path, locator: str) -> Path:
    relative = _safe_repo_locator(locator)
    target = (root / relative).resolve()
    try:
        resolved_relative = target.relative_to(root)
    except ValueError as exc:
        raise GroundingError(f"repository evidence path escapes the target repository: {locator}") from exc
    resolved_parts = [part.casefold() for part in resolved_relative.parts]
    if resolved_parts and (resolved_parts[0] == ".buildos" or ".git" in resolved_parts):
        raise GroundingError(
            f"repository evidence cannot resolve into repository control state: {locator}"
        )
    if not target.is_file():
        raise GroundingError(f"repository evidence file is missing: {locator}")
    return target


def _evidence(
    value: Any, *, root: Path, observed: Mapping[str, Any], verify_live: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    if not isinstance(value, list) or len(value) > MAX_ITEMS:
        raise GroundingError(f"evidence must be an array of at most {MAX_ITEMS} items")
    rows: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    keys = {"id", "kind", "locator", "digest", "observed_at"}
    for index, raw in enumerate(value):
        row = _object(raw, label=f"evidence[{index}]", keys=keys)
        evidence_id = _identifier(row["id"], label=f"evidence[{index}].id")
        if evidence_id in by_id:
            raise GroundingError(f"duplicate grounding evidence id: {evidence_id}")
        kind = _enum(row["kind"], label=f"evidence {evidence_id}.kind", allowed=EVIDENCE_KINDS)
        locator = _text(row["locator"], label=f"evidence {evidence_id}.locator", maximum=2_048)
        digest = _text(row["digest"], label=f"evidence {evidence_id}.digest", maximum=128, nullable=True)
        assert isinstance(locator, str)
        verified = False
        if kind == "REPO_FILE":
            if digest is None or not SHA_RE.fullmatch(digest):
                raise GroundingError(f"repository evidence {evidence_id} requires lowercase SHA-256")
            if verify_live:
                if _sha256_file(_repo_file(root, locator)) != digest:
                    raise GroundingError(f"repository evidence changed: {evidence_id}")
            else:
                _safe_repo_locator(locator)
            verified = True
        elif kind == "REPO_OBSERVATION":
            locator = locator.upper()
            if locator not in REPO_OBSERVATIONS:
                raise GroundingError(f"repository observation {evidence_id} has invalid locator")
            expected = {
                "HEAD": observed.get("head"),
                "TREE": observed.get("tree"),
                "PRODUCT_STATE_DIGEST": observed.get("product_state_digest"),
            }[locator]
            if not digest or digest != expected:
                raise GroundingError(f"repository observation changed: {evidence_id}")
            verified = True
        normalized = {
            "id": evidence_id,
            "kind": kind,
            "locator": locator,
            "digest": digest,
            "observed_at": _text(row["observed_at"], label=f"evidence {evidence_id}.observed_at", maximum=128),
            "locally_verified": verified,
        }
        rows.append(normalized)
        by_id[evidence_id] = normalized
    return rows, by_id


def _bound_evidence(
    raw: Any, *, label: str, evidence: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    refs = _ids(raw, label=label, maximum=64)
    unknown = [item for item in refs if item not in evidence]
    if unknown:
        raise GroundingError(f"{label} references unknown evidence: {unknown}")
    return refs


def _require_local_repo_evidence(
    refs: list[str], *, evidence: Mapping[str, Mapping[str, Any]], label: str,
) -> None:
    if not any(evidence[item]["locally_verified"] for item in refs):
        raise GroundingError(f"{label} requires at least one locally verified repository evidence item")


def _requires_material_decision(claim: Mapping[str, Any]) -> bool:
    return (
        claim.get("binding") in {"CANONICAL", "CONSTRAINT"}
        and claim.get("authority") in {"OWNER", "TECH_LEAD"}
    )


def _require_claim_bound_evidence(
    claim: Mapping[str, Any], outcome: str, refs: list[str], *,
    evidence: Mapping[str, Mapping[str, Any]], observed: Mapping[str, Any], label: str,
) -> None:
    """Require repository proof to cover the exact claim binding, not any repo byte."""
    _require_local_repo_evidence(refs, evidence=evidence, label=label)
    binding = claim.get("repo_binding")
    if claim.get("binding") != "VERIFY_IN_REPO":
        return
    if not isinstance(binding, Mapping):
        raise GroundingError(f"{label} lacks an explicit repository binding")
    rows = [evidence[item] for item in refs]
    file_rows = [row for row in rows if row.get("kind") == "REPO_FILE"]
    observation_rows = {
        str(row.get("locator")): row for row in rows
        if row.get("kind") == "REPO_OBSERVATION"
    }
    for pattern in binding.get("paths") or []:
        normalized = str(pattern).replace("\\", "/")
        if not any(
            fnmatchcase(str(row.get("locator")).replace("\\", "/"), normalized)
            for row in file_rows
        ):
            raise GroundingError(f"{label} does not cover repository binding path {normalized}")
    for key, locator in (("head", "HEAD"), ("tree", "TREE")):
        expected = binding.get(key)
        if expected is None:
            continue
        if locator not in observation_rows:
            raise GroundingError(f"{label} does not cover repository binding {locator}")
        if outcome == "VERIFIED" and expected != observed.get(key):
            raise GroundingError(f"{label} cannot verify stale repository binding {locator}")
    for source in claim.get("source_refs") or []:
        if source.get("kind") != "REPOSITORY":
            continue
        locator = str(source.get("locator") or "").replace("\\", "/")
        if locator.upper() in REPO_OBSERVATIONS:
            candidates = [observation_rows.get(locator.upper())]
        else:
            candidates = [
                row for row in file_rows
                if str(row.get("locator")).replace("\\", "/") == locator
            ]
        candidates = [row for row in candidates if row is not None]
        if not candidates:
            raise GroundingError(f"{label} does not cover repository source {locator}")
        expected_digest = source.get("sha256")
        if outcome == "VERIFIED" and expected_digest and not any(
            row.get("digest") == expected_digest for row in candidates
        ):
            raise GroundingError(f"{label} does not reproduce repository source {locator}")


def _decision_request(
    *, contract_hash: str, claim: Mapping[str, Any], evidence_refs: list[str], source: str,
) -> dict[str, Any]:
    claim_id = str(claim["id"])
    decision_type = CANONICAL_DECISION_TYPES.get(str(claim["kind"]), "CANONICAL_PREMISE")
    digest = hashlib.sha256(
        _canonical_bytes({
            "contract_hash": contract_hash,
            "claim_id": claim_id,
            "decision_type": decision_type,
        })
    ).hexdigest()
    return {
        "schema": "buildos.decision-request.v1",
        "request_id": f"decision-{digest[:20]}",
        "status": "OPEN",
        "contract_hash": contract_hash,
        "claim_id": claim_id,
        "decision_type": decision_type,
        "requested_from": claim["authority"],
        "question": f"Repository evidence contradicts canonical claim {claim_id}; confirm, replace, or supersede it.",
        "options": ["CONFIRM_CANONICAL", "REPLACE_CANONICAL", "SUPERSEDE_WORK_CONTRACT"],
        "evidence_refs": list(evidence_refs),
        "trigger_sources": [source],
        "blocking_scope": "ACTIONS_DEPENDENT_ON_CLAIM",
    }


def _open_question_request(
    *, contract_hash: str, claim: Mapping[str, Any], evidence_refs: list[str],
) -> dict[str, Any]:
    claim_id = str(claim["id"])
    digest = hashlib.sha256(_canonical_bytes({
        "contract_hash": contract_hash, "claim_id": claim_id, "decision_type": "OPEN_QUESTION",
    })).hexdigest()
    verification_owner = str(claim.get("verification_owner") or "")
    requested_from = verification_owner if verification_owner in {"OWNER", "TECH_LEAD"} else claim["authority"]
    return {
        "schema": "buildos.decision-request.v1",
        "request_id": f"decision-{digest[:20]}",
        "status": "OPEN",
        "contract_hash": contract_hash,
        "claim_id": claim_id,
        "decision_type": "OPEN_QUESTION",
        "requested_from": requested_from,
        "question": claim["statement"],
        "options": ["PROVIDE_DECISION", "DEFER_AND_REMOVE_DEPENDENCY", "SUPERSEDE_WORK_CONTRACT"],
        "evidence_refs": list(evidence_refs),
        "trigger_sources": ["SCOPED_OPEN_QUESTION"],
        "blocking_scope": "ACTIONS_DEPENDENT_ON_CLAIM",
    }


def validate_grounding_report(
    contract: Mapping[str, Any], contract_hash: str, value: Any, *,
    root: Path | str, observed_repository: Mapping[str, Any],
    verify_live_evidence: bool = True,
) -> dict[str, Any]:
    """Validate one report against the exact current repository observation."""
    if len(_canonical_bytes(value)) > MAX_REPORT_BYTES:
        raise GroundingError(f"grounding report exceeds {MAX_REPORT_BYTES} bytes")
    keys = {
        "schema", "contract_hash", "worker", "repository", "scope_claim_ids",
        "execution_request", "evidence", "results", "discoveries",
    }
    report = _object(value, label="grounding report", keys=keys)
    if report["schema"] != SCHEMA:
        raise GroundingError(f"grounding report schema must be {SCHEMA}")
    if report["contract_hash"] != contract_hash:
        raise GroundingError("grounding report is bound to a different Work Contract")

    root = Path(root).resolve()
    if not observed_repository.get("available"):
        raise GroundingError("repository grounding requires an observable Git repository")
    observed_root = Path(str(observed_repository.get("root") or "")).resolve()
    if observed_root != root:
        raise GroundingError("repository grounding root must be the Git worktree top-level")
    target_repository = str((contract.get("target") or {}).get("repository") or "").strip()
    if not Path(target_repository).is_absolute() or Path(target_repository).resolve() != root:
        raise GroundingError("Work Contract target names a different repository root")
    target_ref = str((contract.get("target") or {}).get("ref") or "").strip()
    if target_ref:
        expected_branch = target_ref.removeprefix("refs/heads/")
        if str(observed_repository.get("branch") or "") != expected_branch:
            raise GroundingError(
                f"Work Contract target ref {target_ref} does not match the active branch"
            )

    repository = _object(
        report["repository"], label="repository",
        keys={"root", "branch", "head", "tree", "product_state_digest"},
    )
    normalized_repository: dict[str, str] = {}
    for key in ("root", "branch", "head", "tree", "product_state_digest"):
        value_text = _text(repository[key], label=f"repository.{key}", maximum=2_048 if key == "root" else 128)
        assert isinstance(value_text, str)
        normalized_repository[key] = value_text
    if Path(normalized_repository["root"]).resolve() != root:
        raise GroundingError("grounding report names a different repository root")
    for key in ("branch", "head", "tree", "product_state_digest"):
        if normalized_repository[key] != observed_repository.get(key):
            raise GroundingError(f"grounding report is stale: repository.{key} changed")
    if not GIT_OBJECT_RE.fullmatch(normalized_repository["head"]) or not GIT_OBJECT_RE.fullmatch(normalized_repository["tree"]):
        raise GroundingError("grounding repository head/tree are invalid Git object ids")
    if not SHA_RE.fullmatch(normalized_repository["product_state_digest"]):
        raise GroundingError("grounding repository product_state_digest is invalid")

    worker = _object(report["worker"], label="worker", keys={"id", "observed_at"})
    normalized_worker = {
        "id": _identifier(worker["id"], label="worker.id"),
        "observed_at": _text(worker["observed_at"], label="worker.observed_at", maximum=128),
    }
    execution_request = _object(
        report["execution_request"], label="execution_request",
        keys={
            "requested_action", "product_change_mode", "risk", "allowed_paths",
            "prohibited_paths", "acceptance_commands",
        },
    )
    requested_action = _enum(
        execution_request["requested_action"], label="execution_request.requested_action",
        allowed=REQUESTED_ACTIONS,
    )
    product_change_mode = _enum(
        execution_request["product_change_mode"], label="execution_request.product_change_mode",
        allowed=PRODUCT_CHANGE_MODES,
    )
    allowed_paths = _strings(execution_request["allowed_paths"], label="execution_request.allowed_paths", maximum=256, item_maximum=512)
    prohibited_paths = _strings(execution_request["prohibited_paths"], label="execution_request.prohibited_paths", maximum=256, item_maximum=512)
    acceptance_commands = _strings(
        execution_request["acceptance_commands"], label="execution_request.acceptance_commands",
        maximum=64, item_maximum=2_048,
    )
    if requested_action == "READ_ONLY" and (product_change_mode != "NO_SOURCE_DELTA" or allowed_paths):
        raise GroundingError("READ_ONLY execution request must be NO_SOURCE_DELTA with no allowed paths")
    if requested_action in {"LOCAL_MUTATION", "LOCAL_HIGH_COST"} and (product_change_mode != "PRODUCT_DELTA" or not allowed_paths):
        raise GroundingError(f"{requested_action} execution request requires PRODUCT_DELTA and allowed paths")
    if product_change_mode == "NO_SOURCE_DELTA" and allowed_paths:
        raise GroundingError("NO_SOURCE_DELTA execution request cannot grant writable product paths")
    normalized_execution_request = {
        "requested_action": requested_action,
        "product_change_mode": product_change_mode,
        "risk": _enum(execution_request["risk"], label="execution_request.risk", allowed=RISKS),
        "allowed_paths": allowed_paths,
        "prohibited_paths": prohibited_paths,
        "acceptance_commands": acceptance_commands,
    }
    claims = {str(claim["id"]): claim for claim in contract["claims"]}
    scope_claim_ids = _ids(report["scope_claim_ids"], label="scope_claim_ids")
    if not scope_claim_ids:
        raise GroundingError("scope_claim_ids must not be empty")
    unknown_scope = [item for item in scope_claim_ids if item not in claims]
    if unknown_scope:
        raise GroundingError(f"scope_claim_ids references unknown claims: {unknown_scope}")
    required_scope = set(contract.get("action_basis_ids") or [])
    if requested_action != "READ_ONLY":
        omitted_basis = sorted(required_scope - set(scope_claim_ids))
        if omitted_basis:
            raise GroundingError(
                f"mutation grounding omits required action-basis claims: {omitted_basis}"
            )
    evidence_rows, evidence_by_id = _evidence(
        report["evidence"], root=root, observed=observed_repository,
        verify_live=verify_live_evidence,
    )
    if not isinstance(report["results"], list) or len(report["results"]) > MAX_ITEMS:
        raise GroundingError(f"results must be an array of at most {MAX_ITEMS} items")
    results: list[dict[str, Any]] = []
    seen_results: set[str] = set()
    local_adaptations: list[str] = []
    decisions: list[dict[str, Any]] = []
    result_keys = {"claim_id", "outcome", "summary", "evidence_refs"}
    for index, raw in enumerate(report["results"]):
        row = _object(raw, label=f"results[{index}]", keys=result_keys)
        claim_id = _identifier(row["claim_id"], label=f"results[{index}].claim_id")
        if claim_id not in scope_claim_ids or claim_id in seen_results:
            raise GroundingError(f"result claim is outside scope or duplicated: {claim_id}")
        seen_results.add(claim_id)
        outcome = _enum(row["outcome"], label=f"result {claim_id}.outcome", allowed=OUTCOMES)
        refs = _bound_evidence(row["evidence_refs"], label=f"result {claim_id}.evidence_refs", evidence=evidence_by_id)
        claim = claims[claim_id]
        if outcome in {"VERIFIED", "CONTRADICTED"}:
            _require_claim_bound_evidence(
                claim, outcome, refs, evidence=evidence_by_id,
                observed=observed_repository, label=f"result {claim_id}",
            )
        if claim["kind"] == "OPEN_QUESTION" and outcome != "UNKNOWN":
            raise GroundingError(
                f"result {claim_id}: Worker grounding cannot resolve a material open question"
            )
        if outcome == "CONTRADICTED":
            if _requires_material_decision(claim):
                decisions.append(_decision_request(
                    contract_hash=contract_hash, claim=claim, evidence_refs=refs, source="GROUNDING_RESULT",
                ))
            else:
                local_adaptations.append(claim_id)
        elif claim["kind"] == "OPEN_QUESTION":
            decisions.append(_open_question_request(
                contract_hash=contract_hash, claim=claim, evidence_refs=refs,
            ))
        results.append({
            "claim_id": claim_id,
            "outcome": outcome,
            "summary": _text(row["summary"], label=f"result {claim_id}.summary"),
            "evidence_refs": refs,
        })
    missing = sorted(set(scope_claim_ids) - seen_results)
    if missing:
        raise GroundingError(f"grounding results are missing scoped claims: {missing}")

    if not isinstance(report["discoveries"], list) or len(report["discoveries"]) > MAX_ITEMS:
        raise GroundingError(f"discoveries must be an array of at most {MAX_ITEMS} items")
    discoveries: list[dict[str, Any]] = []
    discovery_ids: set[str] = set()
    discovery_keys = {"id", "statement", "status", "conflicts_with", "evidence_refs"}
    for index, raw in enumerate(report["discoveries"]):
        row = _object(raw, label=f"discoveries[{index}]", keys=discovery_keys)
        discovery_id = _identifier(row["id"], label=f"discoveries[{index}].id")
        if discovery_id in discovery_ids:
            raise GroundingError(f"duplicate discovery id: {discovery_id}")
        discovery_ids.add(discovery_id)
        status = _enum(row["status"], label=f"discovery {discovery_id}.status", allowed=DISCOVERY_STATUSES)
        conflicts = _ids(row["conflicts_with"], label=f"discovery {discovery_id}.conflicts_with", maximum=64)
        if any(item not in claims for item in conflicts):
            raise GroundingError(f"discovery {discovery_id} conflicts with an unknown claim")
        refs = _bound_evidence(row["evidence_refs"], label=f"discovery {discovery_id}.evidence_refs", evidence=evidence_by_id)
        if status == "VERIFIED":
            _require_local_repo_evidence(refs, evidence=evidence_by_id, label=f"discovery {discovery_id}")
        if status == "VERIFIED":
            for claim_id in conflicts:
                claim = claims[claim_id]
                if claim.get("binding") == "VERIFY_IN_REPO":
                    _require_claim_bound_evidence(
                        claim, "CONTRADICTED", refs, evidence=evidence_by_id,
                        observed=observed_repository, label=f"discovery {discovery_id}",
                    )
                if _requires_material_decision(claim):
                    decisions.append(_decision_request(
                        contract_hash=contract_hash, claim=claim, evidence_refs=refs, source=f"DISCOVERY:{discovery_id}",
                    ))
                else:
                    local_adaptations.append(claim_id)
        discoveries.append({
            "id": discovery_id,
            "statement": _text(row["statement"], label=f"discovery {discovery_id}.statement"),
            "status": status,
            "conflicts_with": conflicts,
            "evidence_refs": refs,
        })

    unique_decisions: dict[str, dict[str, Any]] = {}
    for item in decisions:
        request_id = str(item["request_id"])
        existing = unique_decisions.get(request_id)
        if existing is None:
            unique_decisions[request_id] = item
            continue
        existing["evidence_refs"] = sorted(set(existing["evidence_refs"]) | set(item["evidence_refs"]))
        existing["trigger_sources"] = sorted(set(existing["trigger_sources"]) | set(item["trigger_sources"]))
    target = contract.get("target") or {}
    target_drift = bool(
        (target.get("head") and target.get("head") != normalized_repository["head"])
        or (target.get("tree") and target.get("tree") != normalized_repository["tree"])
    )
    return {
        "schema": SCHEMA,
        "contract_hash": contract_hash,
        "worker": normalized_worker,
        "repository": normalized_repository,
        "execution_request": normalized_execution_request,
        "scope_claim_ids": scope_claim_ids,
        "evidence": evidence_rows,
        "results": results,
        "discoveries": discoveries,
        "contract_target_drift": target_drift,
        "local_adaptation_claim_ids": sorted(set(local_adaptations)),
        "decision_requests": [unique_decisions[key] for key in sorted(unique_decisions)],
    }


def load_grounding_report(
    path: Path | str, contract: Mapping[str, Any], contract_hash: str, *,
    root: Path | str, observed_repository: Mapping[str, Any],
) -> dict[str, Any]:
    source = Path(path)
    try:
        payload = source.read_bytes()
    except OSError as exc:
        raise GroundingError(f"cannot read grounding report: {exc}") from exc
    if len(payload) > MAX_REPORT_BYTES:
        raise GroundingError(f"grounding report exceeds {MAX_REPORT_BYTES} bytes")
    try:
        value = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GroundingError(f"grounding report JSON is invalid: {exc}") from exc
    return validate_grounding_report(
        contract, contract_hash, value, root=root, observed_repository=observed_repository,
    )


def grounding_projection(report: Mapping[str, Any]) -> dict[str, Any]:
    outcomes = {str(row["claim_id"]): str(row["outcome"]) for row in report["results"]}
    decisions = list(report["decision_requests"])
    adaptations = list(report["local_adaptation_claim_ids"])
    status = (
        "DECISION_REQUIRED" if decisions else
        "GROUNDED_WITH_LOCAL_ADAPTATION" if adaptations else
        "PARTIALLY_GROUNDED" if any(value == "UNKNOWN" for value in outcomes.values()) else
        "GROUNDED"
    )
    return {
        "schema": PROJECTION_SCHEMA,
        "status": status,
        "contract_hash": report["contract_hash"],
        "repository": dict(report["repository"]),
        "execution_request": dict(report["execution_request"]),
        "contract_target_drift": bool(report["contract_target_drift"]),
        "scope_claim_ids": list(report["scope_claim_ids"]),
        "outcomes": outcomes,
        "local_adaptation_claim_ids": adaptations,
        "decision_requests": decisions,
        "action_rights": derive_action_rights(report),
        "unscoped_claims_remain_non_blocking": True,
        "mutation_authority": "NONE_READ_ONLY_GROUNDING",
    }


def canonical_grounding_bytes(report: Mapping[str, Any]) -> bytes:
    return _canonical_bytes(report)


def grounding_hash(report: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_grounding_bytes(report)).hexdigest()


def grounding_claim_freshness(
    report: Mapping[str, Any], *, root: Path | str,
    observed_repository: Mapping[str, Any],
) -> dict[str, list[str]]:
    """Classify VERIFIED results by whether their repository dependencies remain exact."""
    root = Path(root).resolve()
    evidence = {str(row["id"]): row for row in report.get("evidence") or []}
    stale_evidence: set[str] = set()
    branch_changed = (
        str((report.get("repository") or {}).get("branch") or "")
        != str(observed_repository.get("branch") or "")
    )
    for evidence_id, row in evidence.items():
        kind = row.get("kind")
        if kind == "REPO_FILE":
            try:
                target = _repo_file(root, str(row.get("locator") or ""))
                if _sha256_file(target) != row.get("digest"):
                    stale_evidence.add(evidence_id)
            except (GroundingError, OSError):
                stale_evidence.add(evidence_id)
        elif kind == "REPO_OBSERVATION":
            locator = str(row.get("locator") or "").upper()
            current = {
                "HEAD": observed_repository.get("head"),
                "TREE": observed_repository.get("tree"),
                "PRODUCT_STATE_DIGEST": observed_repository.get("product_state_digest"),
            }.get(locator)
            if current is None or current != row.get("digest"):
                stale_evidence.add(evidence_id)
    reused: list[str] = []
    reexecute: list[str] = []
    for result in report.get("results") or []:
        if result.get("outcome") not in {"VERIFIED", "CONTRADICTED"}:
            continue
        claim_id = str(result.get("claim_id") or "")
        refs = [str(item) for item in result.get("evidence_refs") or []]
        if branch_changed or any(item in stale_evidence for item in refs):
            reexecute.append(claim_id)
        else:
            reused.append(claim_id)
    for discovery in report.get("discoveries") or []:
        if discovery.get("status") != "VERIFIED":
            continue
        refs = [str(item) for item in discovery.get("evidence_refs") or []]
        targets = [str(item) for item in discovery.get("conflicts_with") or []]
        destination = reexecute if branch_changed or any(item in stale_evidence for item in refs) else reused
        destination.extend(targets)
    return {"reused": sorted(set(reused)), "reexecute": sorted(set(reexecute))}


def work_loop_binding(
    contract: Mapping[str, Any], contract_hash: str, report: Mapping[str, Any], *,
    contract_evidence: Mapping[str, Any], grounding_evidence: Mapping[str, Any],
    decision_history: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    binding = {
        "schema": "buildos.work-loop.v1",
        "work_contract": {
            "contract_id": contract["contract_id"],
            "revision": contract["revision"],
            "hash": contract_hash,
            "evidence": dict(contract_evidence),
            "ship_mode": contract["ship"]["mode"],
            "ship_authority_reference": contract["ship"]["authority_reference"],
        },
        "grounding": {
            "hash": grounding_hash(report),
            "evidence": dict(grounding_evidence),
            "repository": dict(report["repository"]),
            "scope_claim_ids": list(report["scope_claim_ids"]),
            "outcomes": {
                str(row["claim_id"]): str(row["outcome"]) for row in report["results"]
            },
            "local_adaptation_claim_ids": list(report["local_adaptation_claim_ids"]),
            "decision_requests": list(report["decision_requests"]),
            "contract_target_drift": bool(report["contract_target_drift"]),
        },
        "action_rights": derive_action_rights(report),
    }
    if decision_history is not None:
        binding["decision_history"] = [dict(item) for item in decision_history]
    return binding


def replay_canonical_grounding(
    contract: Mapping[str, Any], contract_hash: str, value: Any, *, root: Path | str,
) -> dict[str, Any]:
    """Re-derive a published normalized report without requiring old worktree bytes.

    Live repository evidence was checked before publication. Replay checks the
    immutable artifact's complete schema and deterministic semantic derivation
    against its recorded repository observation; current freshness is enforced
    separately before action boundaries.
    """
    normalized = _object(
        value, label="canonical grounding evidence",
        keys={
            "schema", "contract_hash", "worker", "repository", "execution_request",
            "scope_claim_ids", "evidence", "results", "discoveries",
            "contract_target_drift", "local_adaptation_claim_ids", "decision_requests",
        },
    )
    if not isinstance(normalized["evidence"], list):
        raise GroundingError("canonical grounding evidence rows must be an array")
    raw_evidence: list[dict[str, Any]] = []
    for index, row in enumerate(normalized["evidence"]):
        item = _object(
            row, label=f"canonical grounding evidence[{index}]",
            keys={"id", "kind", "locator", "digest", "observed_at", "locally_verified"},
        )
        if not isinstance(item["locally_verified"], bool):
            raise GroundingError("canonical grounding locally_verified must be boolean")
        raw_evidence.append({
            key: item[key] for key in ("id", "kind", "locator", "digest", "observed_at")
        })
    repository = normalized["repository"]
    if not isinstance(repository, Mapping):
        raise GroundingError("canonical grounding repository must be an object")
    target_ref = str((contract.get("target") or {}).get("ref") or "")
    recorded_observation = {
        "available": True,
        "root": repository.get("root"),
        "branch": repository.get("branch"),
        "head": repository.get("head"),
        "tree": repository.get("tree"),
        "product_state_digest": repository.get("product_state_digest"),
    }
    raw = {
        key: normalized[key]
        for key in (
            "schema", "contract_hash", "worker", "repository", "scope_claim_ids",
            "execution_request", "results", "discoveries",
        )
    }
    raw["evidence"] = raw_evidence
    replayed = validate_grounding_report(
        contract, contract_hash, raw, root=root,
        observed_repository=recorded_observation, verify_live_evidence=False,
    )
    if replayed != dict(normalized):
        raise GroundingError("canonical grounding evidence does not match deterministic replay")
    return replayed


def _validated_decision_request(
    value: Any, *, label: str, expected_contract_hash: str | None = None,
    scope: set[str] | None = None,
) -> dict[str, Any]:
    request = _object(
        value, label=label,
        keys={
            "schema", "request_id", "status", "contract_hash", "claim_id",
            "decision_type", "requested_from", "question", "options",
            "evidence_refs", "trigger_sources", "blocking_scope",
        },
    )
    if request["schema"] != "buildos.decision-request.v1" or request["status"] != "OPEN":
        raise GroundingError(f"{label} state is invalid")
    request_id = _identifier(request["request_id"], label=f"{label} id")
    contract_hash = _text(request["contract_hash"], label=f"{label} contract_hash", maximum=64)
    if not isinstance(contract_hash, str) or not SHA_RE.fullmatch(contract_hash):
        raise GroundingError(f"{label} contract hash is invalid")
    if expected_contract_hash is not None and contract_hash != expected_contract_hash:
        raise GroundingError(f"{label} is bound to another Contract")
    claim_id = _identifier(request["claim_id"], label=f"{label} claim_id")
    if scope is not None and claim_id not in scope:
        raise GroundingError(f"{label} claim is outside grounding scope")
    if request["decision_type"] not in {
        "PRODUCT_INTENT", "CANONICAL_ARCHITECTURE", "BUSINESS_CONSTRAINT",
        "CANONICAL_PREMISE", "OPEN_QUESTION",
    }:
        raise GroundingError(f"{label} type is invalid")
    if request["requested_from"] not in {"OWNER", "TECH_LEAD"}:
        raise GroundingError(f"{label} has invalid authority destination")
    _text(request["question"], label=f"{label} question")
    _strings(request["options"], label=f"{label} options", maximum=8)
    _ids(request["evidence_refs"], label=f"{label} evidence_refs", maximum=64)
    _strings(request["trigger_sources"], label=f"{label} trigger_sources", maximum=64)
    if request["blocking_scope"] != "ACTIONS_DEPENDENT_ON_CLAIM":
        raise GroundingError(f"{label} has invalid blocking scope")
    return dict(request) | {"request_id": request_id, "claim_id": claim_id}


def validate_work_loop_binding(value: Any) -> None:
    """Validate the compact canonical binding stored in each generation."""
    if not isinstance(value, Mapping):
        raise GroundingError("work_loop must be an object")
    base_keys = {"schema", "work_contract", "grounding", "action_rights"}
    if frozenset(value) not in {frozenset(base_keys), frozenset(base_keys | {"decision_history"})}:
        raise GroundingError("work_loop fields are invalid")
    root = value
    if root["schema"] != "buildos.work-loop.v1":
        raise GroundingError("work_loop schema is invalid")
    contract = _object(
        root["work_contract"], label="work_loop.work_contract",
        keys={
            "contract_id", "revision", "hash", "evidence", "ship_mode",
            "ship_authority_reference",
        },
    )
    _identifier(contract["contract_id"], label="work_loop.work_contract.contract_id")
    if not isinstance(contract["revision"], int) or isinstance(contract["revision"], bool) or contract["revision"] < 1:
        raise GroundingError("work_loop Work Contract revision is invalid")
    contract_hash = _text(contract["hash"], label="work_loop.work_contract.hash", maximum=64)
    if not isinstance(contract_hash, str) or not SHA_RE.fullmatch(contract_hash):
        raise GroundingError("work_loop Work Contract hash is invalid")
    if contract["ship_mode"] not in {
        "HANDOFF_ONLY", "COMMIT_ONLY", "PULL_REQUEST", "MERGE", "RELEASE",
        "DEPLOY", "RUNTIME_ACTIVATION",
    }:
        raise GroundingError("work_loop ship mode is invalid")
    _text(
        contract["ship_authority_reference"],
        label="work_loop.work_contract.ship_authority_reference",
        maximum=2_048, nullable=True,
    )
    grounding = _object(
        root["grounding"], label="work_loop.grounding",
        keys={
            "hash", "evidence", "repository", "scope_claim_ids", "outcomes",
            "local_adaptation_claim_ids", "decision_requests", "contract_target_drift",
        },
    )
    grounding_digest = _text(grounding["hash"], label="work_loop.grounding.hash", maximum=64)
    if not isinstance(grounding_digest, str) or not SHA_RE.fullmatch(grounding_digest):
        raise GroundingError("work_loop grounding hash is invalid")
    for label, evidence, expected in (
        ("contract", contract["evidence"], contract_hash),
        ("grounding", grounding["evidence"], grounding_digest),
    ):
        ref = _object(evidence, label=f"work_loop {label} evidence", keys={"path", "sha256"})
        path = _text(ref["path"], label=f"work_loop {label} evidence.path", maximum=2_048)
        digest = _text(ref["sha256"], label=f"work_loop {label} evidence.sha256", maximum=64)
        if not isinstance(path, str) or not path.replace("\\", "/").startswith(".buildos/evidence/"):
            raise GroundingError(f"work_loop {label} evidence must use the reserved evidence tree")
        if digest != expected:
            raise GroundingError(f"work_loop {label} evidence hash does not match its semantic binding")
    repository = _object(
        grounding["repository"], label="work_loop.grounding.repository",
        keys={"root", "branch", "head", "tree", "product_state_digest"},
    )
    for key in ("root", "branch", "head", "tree", "product_state_digest"):
        _text(repository[key], label=f"work_loop.grounding.repository.{key}", maximum=2_048 if key == "root" else 128)
    scope = _ids(grounding["scope_claim_ids"], label="work_loop.grounding.scope_claim_ids")
    if not scope:
        raise GroundingError("work_loop grounding scope must not be empty")
    if not isinstance(grounding["outcomes"], Mapping) or set(grounding["outcomes"]) != set(scope):
        raise GroundingError("work_loop grounding outcomes must exactly cover its scope")
    if any(value not in OUTCOMES for value in grounding["outcomes"].values()):
        raise GroundingError("work_loop grounding contains an invalid outcome")
    _ids(grounding["local_adaptation_claim_ids"], label="work_loop.grounding.local_adaptation_claim_ids")
    if not isinstance(grounding["decision_requests"], list):
        raise GroundingError("work_loop decision_requests must be an array")
    decision_claim_ids: list[str] = []
    seen_requests: set[str] = set()
    for index, raw_request in enumerate(grounding["decision_requests"]):
        request = _validated_decision_request(
            raw_request, label=f"work_loop decision_requests[{index}]",
            expected_contract_hash=contract_hash, scope=set(scope),
        )
        request_id = request["request_id"]
        if request_id in seen_requests:
            raise GroundingError("work_loop decision request ids must be unique")
        seen_requests.add(request_id)
        decision_claim_ids.append(request["claim_id"])
    history = root.get("decision_history", [])
    if not isinstance(history, list):
        raise GroundingError("work_loop decision_history must be an array")
    seen_history: set[tuple[str, str, str]] = set()
    for index, raw_entry in enumerate(history):
        entry = _object(
            raw_entry, label=f"work_loop decision_history[{index}]",
            keys={
                "schema", "request", "request_sha256", "source_contract",
                "resolution_kind", "resolution_hash", "resolution_evidence",
            },
        )
        if entry["schema"] != DECISION_HISTORY_SCHEMA:
            raise GroundingError("work_loop Decision history schema is invalid")
        historical_request = _validated_decision_request(
            entry["request"], label=f"work_loop decision_history[{index}].request",
        )
        request_digest = _text(
            entry["request_sha256"], label=f"work_loop decision_history[{index}].request_sha256", maximum=64,
        )
        if request_digest != decision_request_hash(historical_request):
            raise GroundingError("work_loop Decision history request hash does not match its request")
        source_contract = _object(
            entry["source_contract"], label=f"work_loop decision_history[{index}].source_contract",
            keys={"contract_id", "revision", "hash"},
        )
        _identifier(source_contract["contract_id"], label="work_loop Decision history contract_id")
        if not isinstance(source_contract["revision"], int) or isinstance(source_contract["revision"], bool) or source_contract["revision"] < 1:
            raise GroundingError("work_loop Decision history Contract revision is invalid")
        source_hash = _text(source_contract["hash"], label="work_loop Decision history Contract hash", maximum=64)
        if not isinstance(source_hash, str) or not SHA_RE.fullmatch(source_hash):
            raise GroundingError("work_loop Decision history Contract hash is invalid")
        if historical_request["contract_hash"] != source_hash:
            raise GroundingError("work_loop Decision history request is bound to another source Contract")
        resolution_kind = _enum(
            entry["resolution_kind"], label="work_loop Decision history resolution_kind",
            allowed={"DIRECT_AUTHORITY_DECISION", "WORK_CONTRACT_SUPERSESSION"},
        )
        resolution_hash = _text(entry["resolution_hash"], label="work_loop Decision history resolution_hash", maximum=64)
        if not isinstance(resolution_hash, str) or not SHA_RE.fullmatch(resolution_hash):
            raise GroundingError("work_loop Decision history resolution hash is invalid")
        reference = _object(
            entry["resolution_evidence"], label="work_loop Decision history resolution evidence",
            keys={"path", "sha256"},
        )
        evidence_path = _text(reference["path"], label="work_loop Decision history evidence.path", maximum=2_048)
        evidence_hash = _text(reference["sha256"], label="work_loop Decision history evidence.sha256", maximum=64)
        if not isinstance(evidence_path, str) or not evidence_path.replace("\\", "/").startswith(".buildos/evidence/"):
            raise GroundingError("work_loop Decision history evidence must use the reserved evidence tree")
        if evidence_hash != resolution_hash:
            raise GroundingError("work_loop Decision history evidence hash does not match its resolution")
        identity = (str(request_digest), resolution_kind, resolution_hash)
        if identity in seen_history:
            raise GroundingError("work_loop Decision history entries must be unique")
        seen_history.add(identity)
    if not isinstance(grounding["contract_target_drift"], bool):
        raise GroundingError("work_loop contract_target_drift must be boolean")
    rights = _object(
        root["action_rights"], label="work_loop.action_rights",
        keys={
            "schema", "read_and_verify", "requested_action", "requested_action_status",
            "blockers", "blocked_claim_ids", "external_dispatch", "ship",
        },
    )
    if rights["schema"] != "buildos.action-rights.v1":
        raise GroundingError("work_loop action rights schema is invalid")
    if rights["requested_action"] not in REQUESTED_ACTIONS:
        raise GroundingError("work_loop requested action is invalid")
    if rights["requested_action_status"] not in {"GRANTED", "BLOCKED"}:
        raise GroundingError("work_loop requested action status is invalid")
    if rights["read_and_verify"] != "GRANTED" or rights["ship"] != "REQUIRES_CANONICAL_ASSURANCE":
        raise GroundingError("work_loop action rights bypass a progressive boundary")
    _strings(rights["blockers"], label="work_loop.action_rights.blockers", maximum=16, item_maximum=128)
    _ids(rights["blocked_claim_ids"], label="work_loop.action_rights.blocked_claim_ids")
    expected_rights = derive_action_rights({
        "decision_requests": list(grounding["decision_requests"]),
        "results": [
            {"claim_id": claim_id, "outcome": outcome}
            for claim_id, outcome in grounding["outcomes"].items()
        ],
        "execution_request": {"requested_action": rights["requested_action"]},
    })
    if dict(rights) != expected_rights:
        raise GroundingError("work_loop action rights do not match compact grounding outcomes")
    adaptations = set(grounding["local_adaptation_claim_ids"])
    if not adaptations.issubset(set(scope)) or adaptations.intersection(decision_claim_ids):
        raise GroundingError("work_loop local adaptations are inconsistent with decision routing")


def verify_work_loop_evidence(root: Path | str, binding: Mapping[str, Any]) -> None:
    """Re-read immutable handoff artifacts before lifecycle operations."""
    validate_work_loop_binding(binding)
    root = Path(root).resolve()
    pairs = (
        ("contract", binding["work_contract"]["evidence"]),
        ("grounding", binding["grounding"]["evidence"]),
    )
    payloads: dict[str, bytes] = {}
    for label, reference in pairs:
        locator = str(reference["path"])
        target = (root / locator).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise GroundingError(f"work_loop {label} evidence escapes repository root") from exc
        if not target.is_file() or _sha256_file(target) != reference["sha256"]:
            raise GroundingError(f"work_loop {label} evidence is missing or changed")
        payloads[label] = target.read_bytes()
    try:
        raw_contract = json.loads(payloads["contract"].decode("utf-8"))
        raw_grounding = json.loads(payloads["grounding"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GroundingError("work_loop evidence JSON is invalid") from exc
    contract = validate_contract(raw_contract)
    if canonical_contract_bytes(contract) != payloads["contract"]:
        raise GroundingError("work_loop Contract evidence is not canonical validated bytes")
    contract_hash = str(binding["work_contract"]["hash"])
    report = replay_canonical_grounding(contract, contract_hash, raw_grounding, root=root)
    if canonical_grounding_bytes(report) != payloads["grounding"]:
        raise GroundingError("work_loop grounding evidence is not canonical replay bytes")
    for entry in binding.get("decision_history") or []:
        reference = entry["resolution_evidence"]
        target = (root / str(reference["path"])).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise GroundingError("work_loop Decision history evidence escapes repository root") from exc
        if not target.is_file() or _sha256_file(target) != reference["sha256"]:
            raise GroundingError("work_loop Decision history evidence is missing or changed")
        try:
            raw_resolution = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GroundingError("work_loop Decision history evidence is invalid JSON") from exc
        if entry["resolution_kind"] == "DIRECT_AUTHORITY_DECISION":
            resolution = validate_decision_resolution(raw_resolution, entry["request"])
            if canonical_decision_resolution_bytes(resolution) != target.read_bytes():
                raise GroundingError("work_loop Decision resolution evidence is not canonical bytes")
        else:
            superseding_contract = validate_contract(raw_resolution)
            if canonical_contract_bytes(superseding_contract) != target.read_bytes():
                raise GroundingError("work_loop superseding Contract evidence is not canonical bytes")
            validate_contract_supersession(
                entry["source_contract"], [entry["request"]],
                superseding_contract, entry["resolution_hash"],
            )
    replayed_binding = work_loop_binding(
        contract, contract_hash, report,
        contract_evidence=binding["work_contract"]["evidence"],
        grounding_evidence=binding["grounding"]["evidence"],
        decision_history=(
            list(binding["decision_history"]) if "decision_history" in binding else None
        ),
    )
    if replayed_binding != dict(binding):
        raise GroundingError("canonical Work Loop binding does not match immutable evidence replay")


def assert_decision_authority_progression(
    previous: Mapping[str, Any], current: Mapping[str, Any],
) -> None:
    """Prevent a same-Contract grounding refresh from erasing authority debt."""
    prior_history = list(previous.get("decision_history") or [])
    current_history = list(current.get("decision_history") or [])
    current_identities = {
        (
            item.get("request_sha256"), item.get("resolution_kind"),
            item.get("resolution_hash"),
        )
        for item in current_history
    }
    for item in prior_history:
        identity = (
            item.get("request_sha256"), item.get("resolution_kind"),
            item.get("resolution_hash"),
        )
        if identity not in current_identities:
            raise GroundingError("grounding refresh cannot discard immutable Decision history")
    prior_open = {
        str(item["request_id"]): item
        for item in (previous.get("grounding") or {}).get("decision_requests") or []
    }
    current_open = {
        str(item["request_id"])
        for item in (current.get("grounding") or {}).get("decision_requests") or []
    }
    resolved = {
        str((item.get("request") or {}).get("request_id")): item
        for item in current_history
        if item.get("resolution_kind") == "DIRECT_AUTHORITY_DECISION"
    }
    for request_id, request in prior_open.items():
        if request_id in current_open:
            continue
        entry = resolved.get(request_id)
        if entry is None or entry.get("request_sha256") != decision_request_hash(request):
            raise GroundingError(
                "same-Contract grounding refresh cannot clear an unresolved Decision Request"
            )


def derive_action_rights(report: Mapping[str, Any]) -> dict[str, Any]:
    """Derive progressive rights from typed state, never semantic model output."""
    decisions = list(report.get("decision_requests") or [])
    unknown = sorted(
        str(row["claim_id"]) for row in report.get("results") or []
        if row.get("outcome") == "UNKNOWN"
    )
    requested = str((report.get("execution_request") or {}).get("requested_action") or "")
    blockers: list[str] = []
    if decisions:
        blockers.append("OPEN_DECISION_REQUEST")
    unresolved_non_question = [
        claim_id for claim_id in unknown
        if not any(item.get("claim_id") == claim_id for item in decisions)
    ]
    if unresolved_non_question:
        blockers.append("UNKNOWN_SCOPED_REPOSITORY_PREMISE")
    granted = not blockers
    return {
        "schema": "buildos.action-rights.v1",
        "read_and_verify": "GRANTED",
        "requested_action": requested,
        "requested_action_status": "GRANTED" if granted else "BLOCKED",
        "blockers": blockers,
        "blocked_claim_ids": sorted(set(unknown) | {str(item["claim_id"]) for item in decisions}),
        "external_dispatch": "REQUIRES_DURABLE_EFFECT_INTENT" if requested == "EXTERNAL_EFFECT" and granted else "NOT_GRANTED",
        "ship": "REQUIRES_CANONICAL_ASSURANCE",
    }


def task_request_from_work_loop(
    contract: Mapping[str, Any], report: Mapping[str, Any], *,
    owner_authorization: str = "NONE", authorization_reference: str = "",
    authorization_actor: str = "OWNER",
) -> dict[str, Any]:
    """Compile the legacy-compatible lifecycle request from transferred evidence."""
    action = report["execution_request"]
    requested = action["requested_action"]
    side_effect = "READ_ONLY" if requested == "READ_ONLY" else "WRITE"
    execution_class = {
        "EXTERNAL_EFFECT": "EXTERNAL_EFFECT",
        "LOCAL_HIGH_COST": "LOCAL_HIGH_COST",
    }.get(requested, "LOCAL_REVERSIBLE")
    claims = {str(item["id"]): item for item in contract["claims"]}
    acceptance = [str(claims[item]["statement"]) for item in contract["acceptance_ids"]]
    return {
        "task_id": f"{contract['contract_id']}-r{int(contract['revision'])}",
        "outcome": contract["objective"],
        "acceptance": acceptance,
        "acceptance_commands": list(action["acceptance_commands"]),
        "risk": action["risk"],
        "side_effect": side_effect,
        "product_change_mode": action["product_change_mode"],
        "execution_class": execution_class,
        "allowed_paths": list(action["allowed_paths"]),
        "prohibited_paths": list(action["prohibited_paths"]),
        "worker_id": report["worker"]["id"],
        "owner_authorization": owner_authorization,
        "authorization_reference": authorization_reference,
        "authorization_actor": authorization_actor,
        "skill": None,
        "enforcement": "BOUNDARY",
        "created_at": contract["issuer"]["issued_at"],
    }
