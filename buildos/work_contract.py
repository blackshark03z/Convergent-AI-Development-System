"""Read-only evidence-carrying Work Contract validation and projection.

This module deliberately owns no lifecycle transition and performs no
repository mutation.  It validates Tech Lead intent/evidence input and derives
a bounded Worker-facing projection.  Repository grounding and progressive
action rights are added by later vNext milestones.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


SCHEMA = "buildos.work-contract.v1"
CAPSULE_SCHEMA = "buildos.worker-contract-capsule.v1"
MAX_CONTRACT_BYTES = 256 * 1024
MAX_CAPSULE_BYTES = 8 * 1024
MAX_STATEMENT_CHARS = 4_000
CAPSULE_TEXT_CHARS = 512
CAPSULE_LIST_LIMIT = 4

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_RE = re.compile(r"^[0-9a-f]{40,64}$")

CLAIM_KINDS = {
    "INTENT", "CONSTRAINT", "DECISION", "ACCEPTANCE", "REPO_CLAIM",
    "EXTERNAL_FACT", "ARTIFACT", "HYPOTHESIS", "OPEN_QUESTION",
}
AUTHORITIES = {
    "OWNER", "TECH_LEAD", "REPOSITORY", "PROVIDER", "DETERMINISTIC_TOOL",
    "WORKER", "ADVISORY_MODEL",
}
BINDINGS = {"CANONICAL", "CONSTRAINT", "ADVISORY", "VERIFY_IN_REPO"}
STATUSES = {
    "DECIDED", "VERIFIED", "SUPPORTED", "HYPOTHESIS", "UNKNOWN",
    "CONTRADICTED", "SUPERSEDED",
}
VERIFICATION_OWNERS = {"NONE", "WORKER", "DETERMINISTIC_TOOL", "TECH_LEAD", "OWNER"}
SOURCE_KINDS = {"FILE", "URL", "EVIDENCE", "REPOSITORY", "PROVIDER"}
SHIP_MODES = {
    "HANDOFF_ONLY", "COMMIT_ONLY", "PULL_REQUEST", "MERGE", "RELEASE",
    "DEPLOY", "RUNTIME_ACTIVATION",
}
AUTH_REQUIRED_SHIP_MODES = {"MERGE", "RELEASE", "DEPLOY", "RUNTIME_ACTIVATION"}


class WorkContractError(ValueError):
    """Raised when a Work Contract cannot safely enter Build OS."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def canonical_contract_bytes(contract: Mapping[str, Any]) -> bytes:
    """Return the exact bytes whose SHA-256 is the validated contract hash."""
    return _canonical_bytes(contract)


def _object(value: Any, *, label: str, keys: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise WorkContractError(f"{label} must be an object")
    observed = set(value)
    if observed != keys:
        missing = sorted(keys - observed)
        unexpected = sorted(observed - keys)
        raise WorkContractError(
            f"{label} fields are invalid; missing={missing} unexpected={unexpected}"
        )
    return value


def _text(value: Any, *, label: str, maximum: int = MAX_STATEMENT_CHARS, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        raise WorkContractError(f"{label} must be a string")
    result = value.strip()
    if not result:
        if nullable:
            return None
        raise WorkContractError(f"{label} must not be empty")
    if len(result) > maximum:
        raise WorkContractError(f"{label} exceeds {maximum} characters")
    return result


def _identifier(value: Any, *, label: str) -> str:
    result = _text(value, label=label, maximum=128)
    assert isinstance(result, str)
    if not ID_RE.fullmatch(result):
        raise WorkContractError(f"{label} is not a portable identifier")
    return result


def _enum(value: Any, *, label: str, allowed: set[str]) -> str:
    result = _text(value, label=label, maximum=64)
    assert isinstance(result, str)
    result = result.upper()
    if result not in allowed:
        raise WorkContractError(f"{label} must be one of {sorted(allowed)}")
    return result


def _strings(value: Any, *, label: str, maximum_items: int = 128, item_maximum: int = 512) -> list[str]:
    if not isinstance(value, list):
        raise WorkContractError(f"{label} must be an array")
    if len(value) > maximum_items:
        raise WorkContractError(f"{label} exceeds {maximum_items} items")
    result = []
    for index, item in enumerate(value):
        text = _text(item, label=f"{label}[{index}]", maximum=item_maximum)
        assert isinstance(text, str)
        result.append(text)
    if len(set(result)) != len(result):
        raise WorkContractError(f"{label} contains duplicates")
    return result


def _source_refs(value: Any, *, claim_id: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise WorkContractError(f"claim {claim_id}.source_refs must be an array")
    if len(value) > 64:
        raise WorkContractError(f"claim {claim_id}.source_refs exceeds 64 items")
    result: list[dict[str, Any]] = []
    ids: set[str] = set()
    keys = {"id", "kind", "locator", "sha256", "observed_at"}
    for index, raw in enumerate(value):
        row = _object(raw, label=f"claim {claim_id}.source_refs[{index}]", keys=keys)
        source_id = _identifier(row["id"], label=f"claim {claim_id}.source_refs[{index}].id")
        if source_id in ids:
            raise WorkContractError(f"claim {claim_id}.source_refs contains duplicate id {source_id}")
        ids.add(source_id)
        sha = _text(row["sha256"], label=f"source {source_id}.sha256", maximum=64, nullable=True)
        if sha is not None and not SHA_RE.fullmatch(sha):
            raise WorkContractError(f"source {source_id}.sha256 must be lowercase SHA-256")
        result.append({
            "id": source_id,
            "kind": _enum(row["kind"], label=f"source {source_id}.kind", allowed=SOURCE_KINDS),
            "locator": _text(row["locator"], label=f"source {source_id}.locator", maximum=2_048),
            "sha256": sha,
            "observed_at": _text(row["observed_at"], label=f"source {source_id}.observed_at", maximum=128, nullable=True),
        })
    return result


def _repo_binding(value: Any, *, claim_id: str) -> dict[str, Any] | None:
    if value is None:
        return None
    row = _object(
        value,
        label=f"claim {claim_id}.repo_binding",
        keys={"head", "tree", "paths"},
    )
    head = _text(row["head"], label=f"claim {claim_id}.repo_binding.head", maximum=64, nullable=True)
    tree = _text(row["tree"], label=f"claim {claim_id}.repo_binding.tree", maximum=64, nullable=True)
    for label, observed in (("head", head), ("tree", tree)):
        if observed is not None and not GIT_RE.fullmatch(observed):
            raise WorkContractError(f"claim {claim_id}.repo_binding.{label} must be a Git object id")
    paths = _strings(row["paths"], label=f"claim {claim_id}.repo_binding.paths", maximum_items=128, item_maximum=512)
    if head is None and tree is None and not paths:
        raise WorkContractError(f"claim {claim_id}.repo_binding must bind a Git object or path")
    return {"head": head, "tree": tree, "paths": paths}


def _claim(value: Any, *, index: int) -> dict[str, Any]:
    keys = {
        "id", "kind", "statement", "authority", "binding", "status",
        "source_refs", "repo_binding", "observed_at", "invalidators",
        "verification_owner",
    }
    row = _object(value, label=f"claims[{index}]", keys=keys)
    claim_id = _identifier(row["id"], label=f"claims[{index}].id")
    kind = _enum(row["kind"], label=f"claim {claim_id}.kind", allowed=CLAIM_KINDS)
    authority = _enum(row["authority"], label=f"claim {claim_id}.authority", allowed=AUTHORITIES)
    binding = _enum(row["binding"], label=f"claim {claim_id}.binding", allowed=BINDINGS)
    status = _enum(row["status"], label=f"claim {claim_id}.status", allowed=STATUSES)
    verification_owner = _enum(
        row["verification_owner"],
        label=f"claim {claim_id}.verification_owner",
        allowed=VERIFICATION_OWNERS,
    )
    source_refs = _source_refs(row["source_refs"], claim_id=claim_id)
    repo_binding = _repo_binding(row["repo_binding"], claim_id=claim_id)

    if authority == "ADVISORY_MODEL" and binding in {"CANONICAL", "CONSTRAINT"}:
        raise WorkContractError(f"claim {claim_id}: advisory model cannot own canonical meaning")
    if binding == "CANONICAL" and authority not in {"OWNER", "TECH_LEAD"}:
        raise WorkContractError(f"claim {claim_id}: canonical claim requires OWNER or TECH_LEAD authority")
    if binding == "CANONICAL" and kind not in {"INTENT", "DECISION", "ACCEPTANCE"}:
        raise WorkContractError(f"claim {claim_id}: {kind} cannot be a canonical intent claim")
    if kind == "REPO_CLAIM":
        if binding != "VERIFY_IN_REPO":
            raise WorkContractError(f"claim {claim_id}: repository claims must be VERIFY_IN_REPO")
        if verification_owner not in {"WORKER", "DETERMINISTIC_TOOL"}:
            raise WorkContractError(f"claim {claim_id}: repository claim needs Worker/tool verification")
        if status == "VERIFIED" and (repo_binding is None or not source_refs):
            raise WorkContractError(f"claim {claim_id}: verified repository claim needs bound evidence")
    if binding == "VERIFY_IN_REPO" and verification_owner not in {"WORKER", "DETERMINISTIC_TOOL"}:
        raise WorkContractError(f"claim {claim_id}: repo verification must be owned by Worker/tool")
    if kind == "OPEN_QUESTION" and status not in {"UNKNOWN", "HYPOTHESIS"}:
        raise WorkContractError(f"claim {claim_id}: open question must remain UNKNOWN or HYPOTHESIS")
    if kind == "ACCEPTANCE" and binding != "CANONICAL":
        raise WorkContractError(f"claim {claim_id}: acceptance must be canonical")

    return {
        "id": claim_id,
        "kind": kind,
        "statement": _text(row["statement"], label=f"claim {claim_id}.statement"),
        "authority": authority,
        "binding": binding,
        "status": status,
        "source_refs": source_refs,
        "repo_binding": repo_binding,
        "observed_at": _text(row["observed_at"], label=f"claim {claim_id}.observed_at", maximum=128, nullable=True),
        "invalidators": _strings(row["invalidators"], label=f"claim {claim_id}.invalidators", maximum_items=64, item_maximum=512),
        "verification_owner": verification_owner,
    }


def validate_contract(value: Any) -> dict[str, Any]:
    """Validate and normalize one Work Contract without external reads/writes."""
    if len(_canonical_bytes(value)) > MAX_CONTRACT_BYTES:
        raise WorkContractError(f"Work Contract exceeds {MAX_CONTRACT_BYTES} bytes")
    keys = {
        "schema", "contract_id", "revision", "issuer", "target", "objective",
        "non_goals", "claims", "acceptance_ids", "open_question_ids", "ship",
        "metadata",
    }
    root = _object(value, label="Work Contract", keys=keys)
    if root["schema"] != SCHEMA:
        raise WorkContractError(f"Work Contract schema must be {SCHEMA}")

    issuer = _object(
        root["issuer"], label="issuer",
        keys={"role", "identity", "authority_reference", "issued_at"},
    )
    role = _enum(issuer["role"], label="issuer.role", allowed={"OWNER", "TECH_LEAD"})
    authority_reference = _text(
        issuer["authority_reference"], label="issuer.authority_reference", maximum=2_048,
    )
    target = _object(root["target"], label="target", keys={"repository", "ref", "head", "tree"})
    target_head = _text(target["head"], label="target.head", maximum=64, nullable=True)
    target_tree = _text(target["tree"], label="target.tree", maximum=64, nullable=True)
    for label, observed in (("head", target_head), ("tree", target_tree)):
        if observed is not None and not GIT_RE.fullmatch(observed):
            raise WorkContractError(f"target.{label} must be a Git object id")
    if (target_head is None) != (target_tree is None):
        raise WorkContractError("target.head and target.tree must be declared together")

    if not isinstance(root["revision"], int) or isinstance(root["revision"], bool) or root["revision"] < 1:
        raise WorkContractError("revision must be a positive integer")
    if not isinstance(root["claims"], list) or not root["claims"]:
        raise WorkContractError("claims must be a non-empty array")
    if len(root["claims"]) > 256:
        raise WorkContractError("claims exceeds 256 items")
    claims = [_claim(item, index=index) for index, item in enumerate(root["claims"])]
    claim_map = {claim["id"]: claim for claim in claims}
    if len(claim_map) != len(claims):
        raise WorkContractError("claims contains duplicate ids")

    acceptance_ids = _strings(root["acceptance_ids"], label="acceptance_ids", maximum_items=64, item_maximum=128)
    if not acceptance_ids:
        raise WorkContractError("acceptance_ids must not be empty")
    for claim_id in acceptance_ids:
        if claim_id not in claim_map or claim_map[claim_id]["kind"] != "ACCEPTANCE":
            raise WorkContractError(f"acceptance_ids references non-acceptance claim {claim_id}")
    open_question_ids = _strings(root["open_question_ids"], label="open_question_ids", maximum_items=64, item_maximum=128)
    for claim_id in open_question_ids:
        if claim_id not in claim_map or claim_map[claim_id]["kind"] != "OPEN_QUESTION":
            raise WorkContractError(f"open_question_ids references non-question claim {claim_id}")
    undeclared_questions = sorted(
        claim["id"] for claim in claims
        if claim["kind"] == "OPEN_QUESTION" and claim["id"] not in open_question_ids
    )
    if undeclared_questions:
        raise WorkContractError(f"open questions missing from open_question_ids: {undeclared_questions}")

    ship = _object(root["ship"], label="ship", keys={"mode", "authority_reference"})
    ship_mode = _enum(ship["mode"], label="ship.mode", allowed=SHIP_MODES)
    ship_authority = _text(
        ship["authority_reference"], label="ship.authority_reference", maximum=2_048, nullable=True,
    )
    if ship_mode in AUTH_REQUIRED_SHIP_MODES and ship_authority is None:
        raise WorkContractError(f"ship mode {ship_mode} requires authority_reference")

    metadata = _object(
        root["metadata"], label="metadata",
        keys={"parent_contract_hash", "source_context_refs"},
    )
    parent_hash = _text(
        metadata["parent_contract_hash"], label="metadata.parent_contract_hash", maximum=64, nullable=True,
    )
    if parent_hash is not None and not SHA_RE.fullmatch(parent_hash):
        raise WorkContractError("metadata.parent_contract_hash must be lowercase SHA-256")

    normalized = {
        "schema": SCHEMA,
        "contract_id": _identifier(root["contract_id"], label="contract_id"),
        "revision": root["revision"],
        "issuer": {
            "role": role,
            "identity": _text(issuer["identity"], label="issuer.identity", maximum=256),
            "authority_reference": authority_reference,
            "issued_at": _text(issuer["issued_at"], label="issuer.issued_at", maximum=128),
        },
        "target": {
            "repository": _text(target["repository"], label="target.repository", maximum=2_048),
            "ref": _text(target["ref"], label="target.ref", maximum=512, nullable=True),
            "head": target_head,
            "tree": target_tree,
        },
        "objective": _text(root["objective"], label="objective"),
        "non_goals": _strings(root["non_goals"], label="non_goals", maximum_items=64, item_maximum=512),
        "claims": claims,
        "acceptance_ids": acceptance_ids,
        "open_question_ids": open_question_ids,
        "ship": {"mode": ship_mode, "authority_reference": ship_authority},
        "metadata": {
            "parent_contract_hash": parent_hash,
            "source_context_refs": _strings(
                metadata["source_context_refs"], label="metadata.source_context_refs",
                maximum_items=64, item_maximum=2_048,
            ),
        },
    }
    return normalized


def load_contract(path: Path | str) -> tuple[dict[str, Any], str]:
    """Read, validate and hash a Work Contract without touching product state."""
    source = Path(path)
    try:
        payload = source.read_bytes()
    except OSError as exc:
        raise WorkContractError(f"cannot read Work Contract: {exc}") from exc
    if len(payload) > MAX_CONTRACT_BYTES:
        raise WorkContractError(f"Work Contract exceeds {MAX_CONTRACT_BYTES} bytes")
    try:
        raw = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkContractError(f"Work Contract JSON is invalid: {exc}") from exc
    normalized = validate_contract(raw)
    return normalized, _digest(normalized)


def validation_projection(contract: Mapping[str, Any], contract_hash: str) -> dict[str, Any]:
    claims = list(contract["claims"])
    repo_pending = [
        claim["id"] for claim in claims
        if claim["binding"] == "VERIFY_IN_REPO" and claim["status"] != "VERIFIED"
    ]
    return {
        "status": "PASS",
        "schema": SCHEMA,
        "contract_id": contract["contract_id"],
        "revision": contract["revision"],
        "contract_hash": contract_hash,
        "issuer_role": contract["issuer"]["role"],
        "claim_count": len(claims),
        "acceptance_count": len(contract["acceptance_ids"]),
        "repo_verification_pending": repo_pending,
        "open_question_ids": list(contract["open_question_ids"]),
        "ship_mode": contract["ship"]["mode"],
        "mutation_authority": "NONE_READ_ONLY_INTAKE",
    }


def _capsule_text(value: str, *, targeted: list[str], pointer: str) -> str:
    if len(value) <= CAPSULE_TEXT_CHARS:
        return value
    targeted.append(pointer)
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _capsule_claims(
    claims: Sequence[Mapping[str, Any]], *, targeted: list[str], label: str,
) -> tuple[list[dict[str, Any]], int]:
    rows = []
    for claim in claims[:CAPSULE_LIST_LIMIT]:
        rows.append({
            "id": claim["id"],
            "status": claim["status"],
            "statement": _capsule_text(
                str(claim["statement"]), targeted=targeted, pointer=f"claim:{claim['id']}",
            ),
        })
    overflow = max(0, len(claims) - len(rows))
    if overflow:
        targeted.append(f"{label}:overflow:{overflow}")
    return rows, overflow


def worker_capsule(contract: Mapping[str, Any], contract_hash: str) -> dict[str, Any]:
    """Derive a bounded, non-authoritative Worker intake projection."""
    claim_map = {claim["id"]: claim for claim in contract["claims"]}
    targeted: list[str] = []
    acceptance, acceptance_overflow = _capsule_claims(
        [claim_map[claim_id] for claim_id in contract["acceptance_ids"]],
        targeted=targeted, label="acceptance",
    )
    decisions, decision_overflow = _capsule_claims(
        [
            claim for claim in contract["claims"]
            if claim["binding"] == "CANONICAL" and claim["kind"] != "ACCEPTANCE"
        ],
        targeted=targeted, label="canonical_decisions",
    )
    repo_claims, repo_overflow = _capsule_claims(
        [
            claim for claim in contract["claims"]
            if claim["binding"] == "VERIFY_IN_REPO" and claim["status"] != "VERIFIED"
        ],
        targeted=targeted, label="repo_verification",
    )
    questions, question_overflow = _capsule_claims(
        [claim_map[claim_id] for claim_id in contract["open_question_ids"]],
        targeted=targeted, label="open_questions",
    )
    non_goals = list(contract["non_goals"][:CAPSULE_LIST_LIMIT])
    non_goal_overflow = max(0, len(contract["non_goals"]) - len(non_goals))
    if non_goal_overflow:
        targeted.append(f"non_goals:overflow:{non_goal_overflow}")

    capsule = {
        "schema": CAPSULE_SCHEMA,
        "projection": "READ_ONLY_DERIVED",
        "status": "READY_FOR_REPOSITORY_GROUNDING" if repo_claims or repo_overflow else "CONTRACT_INPUT_AVAILABLE",
        "contract_id": contract["contract_id"],
        "revision": contract["revision"],
        "contract_hash": contract_hash,
        "target": dict(contract["target"]),
        "objective": _capsule_text(str(contract["objective"]), targeted=targeted, pointer="objective"),
        "non_goals": non_goals,
        "non_goal_overflow": non_goal_overflow,
        "canonical_decisions": decisions,
        "canonical_decision_overflow": decision_overflow,
        "acceptance": acceptance,
        "acceptance_overflow": acceptance_overflow,
        "repo_verification_required": repo_claims,
        "repo_verification_overflow": repo_overflow,
        "open_questions": questions,
        "open_question_overflow": question_overflow,
        "ship_mode": contract["ship"]["mode"],
        "current_action_right": "READ_AND_VERIFY",
        "mutation_authority": "NONE_READ_ONLY_INTAKE",
        "targeted_reads": sorted(set(targeted)),
    }
    if len(_canonical_bytes(capsule)) > MAX_CAPSULE_BYTES:
        raise WorkContractError("Worker Contract Capsule exceeds 8 KiB projection bound")
    return capsule
