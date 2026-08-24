"""Read-only evidence-carrying Work Contract validation and projection.

This module deliberately owns no lifecycle transition and performs no
repository mutation.  It validates Tech Lead intent/evidence input and derives
a bounded Worker-facing projection.  Repository grounding and progressive
action rights are added by later vNext milestones.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


SCHEMA = "buildos.work-contract.v1"
CAPSULE_SCHEMA = "buildos.worker-contract-capsule.v1"
MAX_CONTRACT_BYTES = 256 * 1024
MAX_CAPSULE_BYTES = 8 * 1024
MAX_STATEMENT_CHARS = 4_000
CAPSULE_TEXT_CHARS = 192
CAPSULE_LIST_LIMIT = 1

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
TRUSTED_CONTRACT_SHA256_ENV = "BUILDOS_TRUSTED_CONTRACT_SHA256"


class WorkContractError(ValueError):
    """Raised when a Work Contract cannot safely enter Build OS."""


def require_trusted_contract_transport(contract_hash: str) -> None:
    """Bind initial canonicalization to an exact trusted-launcher handoff.

    This is a transport trust boundary for the cooperative local-agent threat
    model, not authentication against a hostile process running as the same OS
    identity.  The launcher must set the value before Worker execution.
    """
    expected = str(contract_hash).strip().lower()
    supplied = str(os.environ.get(TRUSTED_CONTRACT_SHA256_ENV) or "").strip().lower()
    if not SHA_RE.fullmatch(supplied):
        raise WorkContractError(
            f"initial Work Contract requires trusted launcher binding in {TRUSTED_CONTRACT_SHA256_ENV}"
        )
    if not hmac.compare_digest(supplied, expected):
        raise WorkContractError("trusted launcher Work Contract hash does not match validated handoff")


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


def _exact_repo_path(value: str, *, label: str) -> str:
    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    if (
        normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized)
        or ".." in parts or not parts or not parts[0]
        or parts[0].casefold() == ".buildos"
        or any(part.casefold() == ".git" for part in parts)
    ):
        raise WorkContractError(f"{label} must name a product-repository file")
    if any(character in normalized for character in "*?["):
        raise WorkContractError(f"{label} must name an exact file, not a glob pattern")
    return normalized


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
        kind = _enum(row["kind"], label=f"source {source_id}.kind", allowed=SOURCE_KINDS)
        locator = _text(row["locator"], label=f"source {source_id}.locator", maximum=2_048)
        assert isinstance(locator, str)
        if kind == "REPOSITORY" and locator.upper() not in {"HEAD", "TREE", "PRODUCT_STATE_DIGEST"}:
            locator = _exact_repo_path(locator, label=f"source {source_id}.locator")
        result.append({
            "id": source_id,
            "kind": kind,
            "locator": locator,
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
    normalized_paths: list[str] = []
    for path in paths:
        normalized = _exact_repo_path(
            path, label=f"claim {claim_id}.repo_binding.paths",
        )
        normalized_paths.append(normalized)
    if len(normalized_paths) != len(set(normalized_paths)):
        raise WorkContractError(f"claim {claim_id}.repo_binding.paths contains duplicates")
    if head is None and tree is None and not paths:
        raise WorkContractError(f"claim {claim_id}.repo_binding must bind a Git object or path")
    return {"head": head, "tree": tree, "paths": normalized_paths}


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
    if binding == "CONSTRAINT" and authority not in {"OWNER", "TECH_LEAD"}:
        raise WorkContractError(f"claim {claim_id}: binding constraint requires OWNER or TECH_LEAD authority")
    if binding == "CANONICAL" and kind not in {"INTENT", "DECISION", "ACCEPTANCE"}:
        raise WorkContractError(f"claim {claim_id}: {kind} cannot be a canonical intent claim")
    if binding in {"CANONICAL", "CONSTRAINT"} and status != "DECIDED":
        raise WorkContractError(
            f"claim {claim_id}: active canonical meaning must have DECIDED status"
        )
    if kind == "REPO_CLAIM":
        if binding != "VERIFY_IN_REPO":
            raise WorkContractError(f"claim {claim_id}: repository claims must be VERIFY_IN_REPO")
        if verification_owner not in {"WORKER", "DETERMINISTIC_TOOL"}:
            raise WorkContractError(f"claim {claim_id}: repository claim needs Worker/tool verification")
        if status == "VERIFIED" and (repo_binding is None or not source_refs):
            raise WorkContractError(f"claim {claim_id}: verified repository claim needs bound evidence")
    if binding == "VERIFY_IN_REPO" and verification_owner not in {"WORKER", "DETERMINISTIC_TOOL"}:
        raise WorkContractError(f"claim {claim_id}: repo verification must be owned by Worker/tool")
    if binding == "VERIFY_IN_REPO" and repo_binding is None:
        raise WorkContractError(f"claim {claim_id}: repo verification requires an explicit repository binding")
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
        "non_goals", "claims", "acceptance_ids", "open_question_ids", "action_basis_ids", "ship",
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
    target_repository = _text(target["repository"], label="target.repository", maximum=2_048)
    assert isinstance(target_repository, str)
    if not Path(target_repository).is_absolute():
        raise WorkContractError("target.repository must be an absolute local repository path")
    target_head = _text(target["head"], label="target.head", maximum=64, nullable=True)
    target_tree = _text(target["tree"], label="target.tree", maximum=64, nullable=True)
    for label, observed in (("head", target_head), ("tree", target_tree)):
        if observed is not None and not GIT_RE.fullmatch(observed):
            raise WorkContractError(f"target.{label} must be a Git object id")
    if (target_head is None) != (target_tree is None):
        raise WorkContractError("target.head and target.tree must be declared together")

    if not isinstance(root["revision"], int) or isinstance(root["revision"], bool) or root["revision"] < 1:
        raise WorkContractError("revision must be a positive integer")
    contract_id = _identifier(root["contract_id"], label="contract_id")
    if len(f"{contract_id}-r{root['revision']}") > 96:
        raise WorkContractError("contract_id and revision exceed the canonical task identity limit")
    if not isinstance(root["claims"], list) or not root["claims"]:
        raise WorkContractError("claims must be a non-empty array")
    if len(root["claims"]) > 256:
        raise WorkContractError("claims exceeds 256 items")
    claims = [_claim(item, index=index) for index, item in enumerate(root["claims"])]
    claim_map = {claim["id"]: claim for claim in claims}
    if len(claim_map) != len(claims):
        raise WorkContractError("claims contains duplicate ids")
    repository_dependencies = {
        path
        for claim in claims
        for path in (
            list((claim.get("repo_binding") or {}).get("paths") or [])
            + [
                str(source["locator"])
                for source in claim.get("source_refs") or []
                if source.get("kind") == "REPOSITORY"
            ]
        )
    }
    if len(repository_dependencies) > 256:
        raise WorkContractError(
            "Work Contract requires more than 256 distinct repository evidence rows"
        )

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
    action_basis_ids = _strings(
        root["action_basis_ids"], label="action_basis_ids", maximum_items=256, item_maximum=128,
    )
    for claim_id in action_basis_ids:
        if claim_id not in claim_map:
            raise WorkContractError(f"action_basis_ids references unknown claim {claim_id}")
        claim = claim_map[claim_id]
        if claim["binding"] != "VERIFY_IN_REPO" and claim["kind"] != "OPEN_QUESTION":
            raise WorkContractError(
                f"action_basis_ids may contain only repository verification or open-question claims: {claim_id}"
            )
        if claim["kind"] == "OPEN_QUESTION" and (
            claim["authority"] not in {"OWNER", "TECH_LEAD"}
            or claim["verification_owner"] not in {"OWNER", "TECH_LEAD"}
        ):
            raise WorkContractError(
                f"action-basis open question requires OWNER or TECH_LEAD decision authority: {claim_id}"
            )
    omitted_repo_claims = sorted(
        claim["id"] for claim in claims
        if claim["binding"] == "VERIFY_IN_REPO" and claim["id"] not in action_basis_ids
    )
    if omitted_repo_claims:
        raise WorkContractError(
            f"all repository verification claims must be in action_basis_ids: {omitted_repo_claims}"
        )

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
        "contract_id": contract_id,
        "revision": root["revision"],
        "issuer": {
            "role": role,
            "identity": _text(issuer["identity"], label="issuer.identity", maximum=256),
            "authority_reference": authority_reference,
            "issued_at": _text(issuer["issued_at"], label="issuer.issued_at", maximum=128),
        },
        "target": {
            "repository": target_repository,
            "ref": _text(target["ref"], label="target.ref", maximum=512, nullable=True),
            "head": target_head,
            "tree": target_tree,
        },
        "objective": _text(root["objective"], label="objective"),
        "non_goals": _strings(root["non_goals"], label="non_goals", maximum_items=64, item_maximum=512),
        "claims": claims,
        "acceptance_ids": acceptance_ids,
        "open_question_ids": open_question_ids,
        "action_basis_ids": action_basis_ids,
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
        "action_basis_ids": list(contract["action_basis_ids"]),
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
            "kind": claim["kind"],
            "authority": claim["authority"],
            "binding": claim["binding"],
            "status": claim["status"],
            "statement": _capsule_text(
                str(claim["statement"]), targeted=targeted, pointer=f"claim:{claim['id']}",
            ),
        })
        if claim.get("source_refs"):
            targeted.append(f"claim:{claim['id']}:source_refs")
    overflow = max(0, len(claims) - len(rows))
    if overflow:
        targeted.append(f"{label}:overflow:{overflow}")
    return rows, overflow


def _capsule_repo_claims(
    claims: Sequence[Mapping[str, Any]], *, targeted: list[str],
) -> tuple[list[dict[str, Any]], int]:
    rows, overflow = _capsule_claims(claims, targeted=targeted, label="repo_verification")
    for row, claim in zip(rows, claims[:CAPSULE_LIST_LIMIT]):
        binding = claim.get("repo_binding") or {}
        raw_paths = list((binding.get("paths") or [])[:CAPSULE_LIST_LIMIT])
        paths = [
            _capsule_text(
                str(path), targeted=targeted,
                pointer=f"claim:{claim['id']}:repo_binding:path:{index}",
            )
            for index, path in enumerate(raw_paths)
        ]
        path_overflow = max(0, len(binding.get("paths") or []) - len(paths))
        row["repo_binding"] = {
            "head": binding.get("head"), "tree": binding.get("tree"),
            "paths": paths, "path_overflow": path_overflow,
        }
        if path_overflow:
            targeted.append(f"claim:{claim['id']}:repo_binding:overflow:{path_overflow}")
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
    constraints, constraint_overflow = _capsule_claims(
        [claim for claim in contract["claims"] if claim["binding"] == "CONSTRAINT"],
        targeted=targeted, label="constraints",
    )
    transferred, transferred_overflow = _capsule_claims(
        [
            claim for claim in contract["claims"]
            if claim["binding"] == "ADVISORY"
            and claim["kind"] != "OPEN_QUESTION"
            and claim["status"] in {"DECIDED", "VERIFIED", "SUPPORTED"}
        ],
        targeted=targeted, label="transferred_advisory_evidence",
    )
    repo_claims, repo_overflow = _capsule_repo_claims(
        [
            claim for claim in contract["claims"]
            if claim["binding"] == "VERIFY_IN_REPO"
        ],
        targeted=targeted,
    )
    questions, question_overflow = _capsule_claims(
        [claim_map[claim_id] for claim_id in contract["open_question_ids"]],
        targeted=targeted, label="open_questions",
    )
    non_goals = [
        _capsule_text(
            str(item), targeted=targeted, pointer=f"non_goal:{index}",
        )
        for index, item in enumerate(contract["non_goals"][:CAPSULE_LIST_LIMIT])
    ]
    non_goal_overflow = max(0, len(contract["non_goals"]) - len(non_goals))
    if non_goal_overflow:
        targeted.append(f"non_goals:overflow:{non_goal_overflow}")
    action_basis = list(contract["action_basis_ids"][:CAPSULE_LIST_LIMIT])
    action_basis_overflow = max(0, len(contract["action_basis_ids"]) - len(action_basis))
    if action_basis_overflow:
        targeted.append(f"action_basis:overflow:{action_basis_overflow}")

    capsule = {
        "schema": CAPSULE_SCHEMA,
        "projection": "READ_ONLY_DERIVED",
        "status": "READY_FOR_REPOSITORY_GROUNDING" if repo_claims or repo_overflow else "CONTRACT_INPUT_AVAILABLE",
        "contract_id": contract["contract_id"],
        "revision": contract["revision"],
        "contract_hash": contract_hash,
        "target": {
            "repository": _capsule_text(
                str(contract["target"]["repository"]), targeted=targeted,
                pointer="target.repository",
            ),
            "ref": (
                _capsule_text(str(contract["target"]["ref"]), targeted=targeted, pointer="target.ref")
                if contract["target"]["ref"] is not None else None
            ),
            "head": contract["target"]["head"],
            "tree": contract["target"]["tree"],
        },
        "objective": _capsule_text(str(contract["objective"]), targeted=targeted, pointer="objective"),
        "non_goals": non_goals,
        "non_goal_overflow": non_goal_overflow,
        "canonical_decisions": decisions,
        "canonical_decision_overflow": decision_overflow,
        "constraints": constraints,
        "constraint_overflow": constraint_overflow,
        "transferred_advisory_evidence": transferred,
        "transferred_advisory_evidence_overflow": transferred_overflow,
        "acceptance": acceptance,
        "acceptance_overflow": acceptance_overflow,
        "repo_verification_required": repo_claims,
        "repo_verification_overflow": repo_overflow,
        "action_basis_ids": action_basis,
        "action_basis_overflow": action_basis_overflow,
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
