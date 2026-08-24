"""Read-only Worker grounding and typed Decision Request derivation.

The Worker owns repository interpretation.  Build OS verifies that the report
is bound to the exact observed worktree and that repository evidence still
matches, then classifies conflicts from declared authority metadata.  It does
not interpret product meaning or let a Worker resolution rewrite canonical
Tech Lead claims.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .work_contract import ID_RE, SHA_RE, WorkContractError


SCHEMA = "buildos.grounding-report.v1"
PROJECTION_SCHEMA = "buildos.grounding-projection.v1"
MAX_REPORT_BYTES = 256 * 1024
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


def _repo_file(root: Path, locator: str) -> Path:
    relative = Path(locator.replace("\\", "/"))
    if relative.is_absolute() or ".." in relative.parts:
        raise GroundingError(f"repository evidence path escapes the target repository: {locator}")
    if relative.parts and relative.parts[0].casefold() == ".buildos":
        raise GroundingError(
            f"repository evidence cannot cite Build OS control state: {locator}"
        )
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise GroundingError(f"repository evidence path escapes the target repository: {locator}") from exc
    if not target.is_file():
        raise GroundingError(f"repository evidence file is missing: {locator}")
    return target


def _evidence(
    value: Any, *, root: Path, observed: Mapping[str, Any],
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
            if _sha256_file(_repo_file(root, locator)) != digest:
                raise GroundingError(f"repository evidence changed: {evidence_id}")
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
    if target_repository and Path(target_repository).is_absolute() and Path(target_repository).resolve() != root:
        raise GroundingError("Work Contract target names a different repository root")

    repository = _object(
        report["repository"], label="repository",
        keys={"root", "head", "tree", "product_state_digest"},
    )
    normalized_repository: dict[str, str] = {}
    for key in ("root", "head", "tree", "product_state_digest"):
        value_text = _text(repository[key], label=f"repository.{key}", maximum=2_048 if key == "root" else 128)
        assert isinstance(value_text, str)
        normalized_repository[key] = value_text
    if Path(normalized_repository["root"]).resolve() != root:
        raise GroundingError("grounding report names a different repository root")
    for key in ("head", "tree", "product_state_digest"):
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
    evidence_rows, evidence_by_id = _evidence(report["evidence"], root=root, observed=observed_repository)
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
        if outcome in {"VERIFIED", "CONTRADICTED"}:
            _require_local_repo_evidence(refs, evidence=evidence_by_id, label=f"result {claim_id}")
        claim = claims[claim_id]
        if outcome == "CONTRADICTED":
            if claim["binding"] == "CANONICAL" or claim["kind"] in CANONICAL_DECISION_TYPES:
                decisions.append(_decision_request(
                    contract_hash=contract_hash, claim=claim, evidence_refs=refs, source="GROUNDING_RESULT",
                ))
            else:
                local_adaptations.append(claim_id)
        elif outcome == "UNKNOWN" and claim["kind"] == "OPEN_QUESTION":
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
        for claim_id in conflicts:
            claim = claims[claim_id]
            if claim["binding"] == "CANONICAL" or claim["kind"] in CANONICAL_DECISION_TYPES:
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


def work_loop_binding(
    contract: Mapping[str, Any], contract_hash: str, report: Mapping[str, Any], *,
    contract_evidence: Mapping[str, Any], grounding_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    return {
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


def validate_work_loop_binding(value: Any) -> None:
    """Validate the compact canonical binding stored in each generation."""
    root = _object(
        value, label="work_loop",
        keys={"schema", "work_contract", "grounding", "action_rights"},
    )
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
        keys={"root", "head", "tree", "product_state_digest"},
    )
    for key in ("root", "head", "tree", "product_state_digest"):
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


def verify_work_loop_evidence(root: Path | str, binding: Mapping[str, Any]) -> None:
    """Re-read immutable handoff artifacts before lifecycle operations."""
    validate_work_loop_binding(binding)
    root = Path(root).resolve()
    pairs = (
        ("contract", binding["work_contract"]["evidence"]),
        ("grounding", binding["grounding"]["evidence"]),
    )
    for label, reference in pairs:
        locator = str(reference["path"])
        target = (root / locator).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise GroundingError(f"work_loop {label} evidence escapes repository root") from exc
        if not target.is_file() or _sha256_file(target) != reference["sha256"]:
            raise GroundingError(f"work_loop {label} evidence is missing or changed")


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
