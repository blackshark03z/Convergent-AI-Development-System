"""Pure v1.22 lifecycle model.

The model deliberately knows nothing about the filesystem or Git.  A
transition receives a validated observation and returns a complete candidate
state.  The store is responsible for making that candidate durable.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import fnmatch
import json
import re
import uuid
from typing import Any, Mapping


SCHEMA = "buildos.state.v1.22"
GENERATION_SCHEMA = "buildos.generation.v1"
PHASES = {"ACTIVE", "PRODUCT_COMMITTED", "ASSURANCE_READY", "CLOSED", "ABORTED"}
RISKS = {"R0", "R1", "R2", "R3"}
AUTH_REQUIRED = {"R3"}
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")


class KernelError(ValueError):
    """A fail-closed, user-actionable kernel rejection."""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def new_id(prefix: str = "id") -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _clean_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    return [str(v).strip() for v in values if str(v).strip()]


def resolve_risk(request: Mapping[str, Any]) -> str:
    requested = str(request.get("risk", "auto")).upper()
    side_effect = str(request.get("side_effect", "READ_ONLY")).upper()
    floors = {
        "READ_ONLY": "R0",
        "WRITE": "R1",
        "READ_WRITE": "R1",
        "CREATE_NEW_VERSION": "R1",
        "MUTATE_IN_PLACE": "R2",
        "OVERWRITE": "R2",
        "DELETE": "R3",
    }
    if side_effect not in floors:
        raise KernelError(f"invalid side effect: {side_effect}")
    floor = "R3" if bool(request.get("authorization_required")) else floors[side_effect]
    if requested == "AUTO":
        return floor
    if requested not in RISKS:
        raise KernelError(f"invalid risk tier: {requested}")
    # Explicit declarations may tighten but can never downgrade the observable
    # side-effect floor.
    return requested if RISKS_ORDER[requested] >= RISKS_ORDER[floor] else floor


def validate_task_request(request: Mapping[str, Any]) -> dict[str, Any]:
    task_id = str(request.get("task_id", "")).strip()
    if not TASK_ID_RE.fullmatch(task_id):
        raise KernelError("task_id must be 1-96 chars of letters, digits, '.', '_' or '-'")
    outcome = str(request.get("outcome", "")).strip()
    if not outcome:
        raise KernelError("outcome is required")
    acceptance = _clean_list(request.get("acceptance") or request.get("accept") or [outcome])
    if not acceptance:
        raise KernelError("at least one acceptance criterion is required")
    risk = resolve_risk(request)
    worker = str(request.get("worker_id", "WORKER")).strip() or "WORKER"
    enforcement = str(request.get("enforcement", "SUPERVISORY")).upper()
    if enforcement not in {"SUPERVISORY", "BOUNDARY"}:
        raise KernelError("invalid enforcement level")
    auth_status = str(request.get("owner_authorization", "NONE")).upper().strip() or "NONE"
    auth_ref = str(request.get("authorization_reference", "")).strip()
    auth_actor = str(request.get("authorization_actor", "OWNER" if auth_status == "APPROVED" else "NONE")).strip() or "NONE"
    if risk in AUTH_REQUIRED:
        if auth_status != "APPROVED" or not auth_ref:
            raise KernelError("R3 requires explicit owner authorization APPROVED and a non-empty authorization reference")
        if auth_actor.casefold() == worker.casefold() or auth_actor.upper() in {"WORKER", "AUTO", "SELF"}:
            raise KernelError("worker cannot self-approve R3 work")
    allowed = _clean_list(request.get("allowed_paths") or request.get("modify") or [])
    prohibited = _clean_list(request.get("prohibited_paths") or request.get("prohibited") or [])
    side_effect = str(request.get("side_effect", "READ_ONLY")).upper()
    if side_effect == "READ_ONLY" and allowed:
        raise KernelError("READ_ONLY tasks cannot declare writable allowed paths")
    if not allowed and side_effect != "READ_ONLY":
        raise KernelError("write-capable tasks require at least one allowed path")
    if not allowed:
        allowed = ["<none-read-only>"]
    raw_skill = request.get("skill")
    return {
        "task_id": task_id,
        "outcome": outcome,
        "acceptance": acceptance,
        "risk": risk,
        "side_effect": side_effect,
        "allowed_paths": allowed,
        "prohibited_paths": prohibited,
        "worker_id": worker,
        "owner_authorization": auth_status,
        "authorization_reference": auth_ref if auth_ref else None,
        "authorization_actor": auth_actor,
        "skill": str(raw_skill).strip() if raw_skill is not None and str(raw_skill).strip() else None,
        "enforcement": enforcement,
        "acceptance_commands": _clean_list(request.get("acceptance_commands")),
        "created_at": str(request.get("created_at") or now_iso()),
    }


def _git_anchor(git: Mapping[str, Any] | None) -> dict[str, Any]:
    git = git or {}
    return {
        "available": bool(git.get("available", False)),
        "root": git.get("root"),
        "branch": git.get("branch"),
        "head": git.get("head"),
        "tree": git.get("tree"),
        "dirty": bool(git.get("dirty", False)),
    }


def initial_state(request: Mapping[str, Any], git: Mapping[str, Any] | None, *, at: str | None = None) -> dict[str, Any]:
    req = validate_task_request(request)
    stamp = at or req["created_at"]
    epoch_id = new_id("epoch")
    contract = {
        "task_id": req["task_id"],
        "outcome": req["outcome"],
        "acceptance": req["acceptance"],
        "acceptance_commands": req["acceptance_commands"],
        "risk": req["risk"],
        "side_effect": req["side_effect"],
        "allowed_paths": req["allowed_paths"],
        "prohibited_paths": req["prohibited_paths"],
        "worker_id": req["worker_id"],
        "enforcement": req["enforcement"],
        "authorization": {
            "status": req["owner_authorization"],
            "reference": req["authorization_reference"],
            "actor": req["authorization_actor"],
        },
        "skill": req["skill"],
    }
    state: dict[str, Any] = {
        "schema": SCHEMA,
        "task_id": req["task_id"],
        "revision": 1,
        "phase": "ACTIVE",
        "lifecycle_ready": True,
        "outcome": req["outcome"],
        "acceptance": req["acceptance"],
        "acceptance_commands": req["acceptance_commands"],
        "risk": req["risk"],
        "side_effect": req["side_effect"],
        "allowed_paths": req["allowed_paths"],
        "prohibited_paths": req["prohibited_paths"],
        "worker_id": req["worker_id"],
        "enforcement": req["enforcement"],
        "authorization": {
            "status": req["owner_authorization"],
            "reference": req["authorization_reference"],
            "actor": req["authorization_actor"],
        },
        "skill": req["skill"],
        "contract_hash": sha256_json(contract),
        "lease": {"status": "CLAIMED", "holder": req["worker_id"]},
        "base_git": _git_anchor(git),
        "product_commit": None,
        "assurance": None,
        "evidence": [],
        "context": {
            "epoch": 1,
            "epoch_id": epoch_id,
            "thread_id": None,
            "requests_in_epoch": 0,
            "projected_prompt_tokens": None,
            "last_signal": "UNMEASURED",
        },
        "created_at": stamp,
        "updated_at": stamp,
        "next_action": (
            "run deterministic read-only validation; product changes are forbidden"
            if req["side_effect"] == "READ_ONLY"
            else "implement product change, then run record-commit"
        ),
        "history": [],
    }
    validate_state(state)
    return state


def validate_state(state: Mapping[str, Any]) -> None:
    if state.get("schema") != SCHEMA:
        raise KernelError("unsupported state schema")
    if not TASK_ID_RE.fullmatch(str(state.get("task_id", ""))):
        raise KernelError("canonical state has invalid task_id")
    if int(state.get("revision", 0)) < 1:
        raise KernelError("canonical state has invalid revision")
    phase = state.get("phase")
    if phase not in PHASES:
        raise KernelError(f"invalid lifecycle phase: {phase}")
    risk = state.get("risk")
    if risk not in RISKS:
        raise KernelError("canonical state has invalid risk")
    auth = state.get("authorization") or {}
    if risk in AUTH_REQUIRED and (auth.get("status") != "APPROVED" or not auth.get("reference")):
        raise KernelError("canonical R3 state is missing owner authorization")
    lease = state.get("lease") or {}
    if phase == "CLOSED" and lease.get("status") != "RELEASED":
        raise KernelError("closed state must release its lease")
    if phase in {"ACTIVE", "PRODUCT_COMMITTED", "ASSURANCE_READY"} and lease.get("status") != "CLAIMED":
        raise KernelError("live state must have a claimed lease")
    if phase == "PRODUCT_COMMITTED" and not (state.get("product_commit") or {}).get("sha"):
        raise KernelError("PRODUCT_COMMITTED requires a product commit anchor")
    if phase == "ASSURANCE_READY" and not (state.get("assurance") or {}).get("evidence_sha"):
        raise KernelError("ASSURANCE_READY requires immutable evidence")
    if phase == "CLOSED" and not (state.get("assurance") or {}).get("evidence_sha"):
        raise KernelError("CLOSED requires immutable evidence")


def _next(prev: Mapping[str, Any], *, phase: str | None = None, at: str | None = None) -> dict[str, Any]:
    result = deepcopy(dict(prev))
    if phase:
        result["phase"] = phase
    result["updated_at"] = at or now_iso()
    return result


def transition_rollover(prev: Mapping[str, Any], signal: Mapping[str, Any], *, thread_id: str | None = None, at: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_state(prev)
    if prev["phase"] not in {"ACTIVE", "PRODUCT_COMMITTED"}:
        raise KernelError("context rollover is only valid while work is live")
    action = str(signal.get("action", "")).upper()
    if action not in {"ROLLOVER_REQUIRED", "HARD_STOP", "PREPARE_COMPACT"} and not signal.get("force"):
        raise KernelError("rollover requires a governor signal or --force")
    thread_id = str(thread_id or "").strip()
    if not thread_id:
        raise KernelError("rollover requires an explicit fresh thread_id")
    if thread_id == str((prev.get("context") or {}).get("thread_id") or ""):
        raise KernelError("rollover thread_id must identify a fresh disposable context")
    result = _next(prev, at=at)
    old = result["context"]
    result["context"] = {
        "epoch": int(old.get("epoch", 1)) + 1,
        "epoch_id": new_id("epoch"),
        "thread_id": thread_id,
        "requests_in_epoch": 0,
        "projected_prompt_tokens": None,
        "last_signal": "ROLLOVER_COMPLETE",
    }
    result["next_action"] = "continue implementation from generated WORK_PACKET"
    validate_state(result)
    return result, {"kind": "ROLLOVER", "from_epoch": old.get("epoch"), "to_epoch": result["context"]["epoch"], "thread_id": thread_id, "signal": dict(signal)}


def transition_record_commit(prev: Mapping[str, Any], git: Mapping[str, Any], *, at: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_state(prev)
    if prev["phase"] != "ACTIVE":
        if prev["phase"] == "PRODUCT_COMMITTED" and (prev.get("product_commit") or {}).get("sha") == git.get("head"):
            return deepcopy(dict(prev)), {"kind": "COMMIT_ALREADY_RECORDED", "sha": git.get("head")}
        raise KernelError("record-commit requires ACTIVE lifecycle state")
    if prev.get("side_effect") == "READ_ONLY":
        raise KernelError("READ_ONLY tasks cannot record a product commit; validate the unchanged baseline directly")
    if not git.get("available") or not git.get("head"):
        raise KernelError("record-commit requires an observable Git HEAD (use --sha only with an explicit adapter)")
    if git.get("tracked_control_paths"):
        raise KernelError("record-commit refuses tracked .buildos control files")
    if git.get("product_dirty"):
        raise KernelError("record-commit requires a clean product tree; .buildos control files are excluded")
    base = (prev.get("base_git") or {}).get("head")
    head = str(git["head"])
    if base and head == base:
        raise KernelError("product commit must advance HEAD beyond the bootstrap anchor")
    relation = str(git.get("relation_to_base", "UNKNOWN")).upper()
    if base and relation != "DESCENDANT":
        raise KernelError("current HEAD is not a descendant of the task base; create an explicit new revision")
    changed = list(git.get("changes_since_base") or [])
    if not changed:
        raise KernelError("write-capable tasks require at least one committed product path change")
    _validate_change_kinds(prev, git)
    _validate_scope(prev, changed, case_insensitive=bool(git.get("case_insensitive_paths")))
    result = _next(prev, phase="PRODUCT_COMMITTED", at=at)
    result["product_commit"] = {
        "sha": head,
        "tree": git.get("tree"),
        "branch": git.get("branch"),
        "recorded_at": result["updated_at"],
        "relation_to_base": relation,
    }
    result["next_action"] = "run validation and attach immutable evidence"
    validate_state(result)
    return result, {"kind": "PRODUCT_COMMIT", "sha": head, "tree": git.get("tree"), "relation_to_base": relation}


def _relation_allowed(relation: str) -> bool:
    return relation.upper() in {"SAME", "DESCENDANT"}


def _matches_path(path: str, pattern: str, *, case_insensitive: bool = False) -> bool:
    path = path.replace("\\", "/")
    pattern = pattern.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    while pattern.startswith("./"):
        pattern = pattern[2:]
    if case_insensitive:
        path = path.casefold()
        pattern = pattern.casefold()
    return fnmatch.fnmatchcase(path, pattern) or path == pattern.rstrip("/") or path.startswith(pattern.rstrip("/") + "/")


def _validate_scope(state: Mapping[str, Any], changed_paths: list[str], *, case_insensitive: bool = False) -> None:
    allowed = [str(item) for item in state.get("allowed_paths") or []]
    prohibited = [str(item) for item in state.get("prohibited_paths") or []]
    blocked = [path for path in changed_paths if any(_matches_path(path, pattern, case_insensitive=case_insensitive) for pattern in prohibited)]
    outside = [path for path in changed_paths if not any(_matches_path(path, pattern, case_insensitive=case_insensitive) for pattern in allowed)]
    if blocked:
        raise KernelError(f"product commit touches prohibited paths: {', '.join(blocked)}")
    if outside:
        raise KernelError(f"product commit exceeds allowed paths: {', '.join(outside)}")


def _validate_change_kinds(state: Mapping[str, Any], git: Mapping[str, Any]) -> None:
    deletions = [str(path) for path in git.get("deletions_since_base") or []]
    if deletions and not (state.get("risk") == "R3" and state.get("side_effect") == "DELETE"):
        raise KernelError(f"product deletion requires an authorized R3 DELETE contract: {', '.join(deletions)}")
    type_changes = [str(path) for path in git.get("type_changes_since_base") or []]
    if type_changes and RISKS_ORDER.get(str(state.get("risk")), -1) < RISKS_ORDER["R2"]:
        raise KernelError(f"product file type changes require at least R2: {', '.join(type_changes)}")


def transition_validate(prev: Mapping[str, Any], git: Mapping[str, Any], evidence: Mapping[str, Any], *, at: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_state(prev)
    read_only = prev.get("side_effect") == "READ_ONLY"
    if prev["phase"] != "PRODUCT_COMMITTED" and not (read_only and prev["phase"] == "ACTIVE"):
        raise KernelError("validate requires PRODUCT_COMMITTED lifecycle state")
    target = ((prev.get("base_git") or {}).get("head") if read_only else (prev.get("product_commit") or {}).get("sha"))
    relation = str(git.get("relation_to_base" if read_only else "relation_to_product", "UNKNOWN"))
    if not target or not git.get("head"):
        raise KernelError("validation requires a current Git HEAD and product anchor")
    if git.get("tracked_control_paths"):
        raise KernelError("validation refuses tracked .buildos control files")
    if git.get("product_dirty"):
        raise KernelError("validation requires a clean product tree")
    if read_only and (git.get("head") != target or relation.upper() != "SAME" or git.get("changes_since_base")):
        raise KernelError("READ_ONLY validation requires the unchanged bootstrap Git baseline")
    if not _relation_allowed(relation):
        raise KernelError("current HEAD diverged from product anchor; create an explicit new revision")
    _validate_change_kinds(prev, git)
    _validate_scope(prev, git.get("changes_since_base") or [], case_insensitive=bool(git.get("case_insensitive_paths")))
    if not evidence.get("path") or not evidence.get("sha256"):
        raise KernelError("validation requires an immutable evidence reference and hash")
    if evidence.get("target_sha") and evidence.get("target_sha") != git.get("head"):
        raise KernelError("evidence target no longer matches current HEAD; preserve it and validate the new target")
    result = _next(prev, phase="ASSURANCE_READY", at=at)
    result["evidence"] = [*deepcopy(prev.get("evidence") or []), dict(evidence)]
    result["assurance"] = {
        "product_anchor_sha": target,
        "target_sha": git.get("head"),
        "validated_head": git.get("head"),
        "validated_tree": git.get("tree"),
        "relation_to_product": relation,
        "evidence_sha": evidence["sha256"],
        "validated_at": result["updated_at"],
    }
    result["next_action"] = "close task; later descendant commits are refreshed, never reopened"
    validate_state(result)
    return result, {"kind": "VALIDATION", "product_anchor_sha": target, "target_sha": git.get("head"), "relation": relation, "evidence": dict(evidence)}


def transition_close(prev: Mapping[str, Any], git: Mapping[str, Any] | None, *, at: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_state(prev)
    if prev["phase"] != "ASSURANCE_READY":
        raise KernelError("close requires ASSURANCE_READY lifecycle state")
    result = _next(prev, phase="CLOSED", at=at)
    observed = dict(git or {})
    assurance = deepcopy(result["assurance"] or {})
    target = assurance.get("target_sha")
    if not observed.get("available") or not observed.get("head") or not target:
        raise KernelError("close requires observable Git ancestry for the validated target")
    if observed.get("tracked_control_paths"):
        raise KernelError("close refuses tracked .buildos control files")
    if observed.get("available") and observed.get("head") and target:
        relation = str(observed.get("relation_to_validated", observed.get("relation_to_product", "UNKNOWN"))).upper()
        if not _relation_allowed(relation):
            raise KernelError("close refuses a divergent HEAD; preserve evidence and create an explicit new revision")
        if observed.get("product_dirty"):
            raise KernelError("close requires a clean product tree")
        if relation == "DESCENDANT" and observed.get("changes_since_validated"):
            raise KernelError("product files changed after validation; preserve evidence and validate a new revision")
        assurance["close_head"] = observed.get("head")
        assurance["close_tree"] = observed.get("tree")
        assurance["close_relation"] = relation
        if relation == "DESCENDANT":
            assurance["head_refresh"] = "LEGITIMATE_DESCENDANT"
    result["assurance"] = assurance
    result["lease"] = {"status": "RELEASED", "holder": result.get("worker_id")}
    result["lifecycle_ready"] = False
    result["next_action"] = "none; start a new task or explicit revision for further product scope"
    validate_state(result)
    return result, {"kind": "CLOSE", "target_sha": target, "observed_head": observed.get("head"), "relation": assurance.get("close_relation", "UNMEASURED")}


def transition_abort(prev: Mapping[str, Any], *, reason: str, at: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_state(prev)
    if prev["phase"] in {"CLOSED", "ABORTED"}:
        raise KernelError("task is already terminal")
    if not str(reason).strip():
        raise KernelError("abort requires a reason")
    result = _next(prev, phase="ABORTED", at=at)
    result["lease"] = {"status": "RELEASED", "holder": result.get("worker_id")}
    result["lifecycle_ready"] = False
    result["next_action"] = "none; preserve evidence and start a new task if needed"
    result["abort_reason"] = str(reason).strip()
    validate_state(result)
    return result, {"kind": "ABORT", "reason": str(reason).strip()}


def transition_new_revision(
    prev: Mapping[str, Any],
    *,
    reason: str,
    risk: str | None = None,
    allowed_paths: list[str] | None = None,
    prohibited_paths: list[str] | None = None,
    owner_authorization: str | None = None,
    authorization_reference: str | None = None,
    authorization_actor: str | None = None,
    at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create an explicit new revision without deleting the prior proof."""
    validate_state(prev)
    if prev["phase"] not in {"PRODUCT_COMMITTED", "ASSURANCE_READY", "CLOSED", "ABORTED"}:
        raise KernelError("new revision requires a completed or committed prior revision")
    if not str(reason).strip():
        raise KernelError("new revision requires a reason")
    result = _next(prev, phase="ACTIVE", at=at)
    result["revision"] = int(prev.get("revision", 1)) + 1
    result["product_commit"] = None
    result["assurance"] = None
    result["evidence"] = []
    result["lease"] = {"status": "CLAIMED", "holder": prev.get("worker_id")}
    result["lifecycle_ready"] = True
    result["revision_reason"] = str(reason).strip()
    if risk:
        requested = str(risk).upper()
        if requested not in RISKS:
            raise KernelError("invalid revision risk")
        # Risk can escalate, never silently downgrade.
        if RISKS_ORDER[requested] < RISKS_ORDER[str(prev["risk"]).upper()]:
            raise KernelError("revision cannot downgrade risk")
        result["risk"] = requested
    if allowed_paths is not None:
        revised_allowed = _clean_list(allowed_paths)
        if not revised_allowed and result.get("side_effect") != "READ_ONLY":
            raise KernelError("write-capable revision requires at least one allowed path")
        result["allowed_paths"] = revised_allowed or ["<declared-by-worker>"]
    if prohibited_paths is not None:
        result["prohibited_paths"] = _clean_list(prohibited_paths)
    if owner_authorization is not None or authorization_reference is not None or authorization_actor is not None:
        prior_auth = result.get("authorization") or {}
        result["authorization"] = {
            "status": str(owner_authorization or prior_auth.get("status") or "NONE").upper(),
            "reference": str(authorization_reference or prior_auth.get("reference") or "").strip() or None,
            "actor": str(authorization_actor or prior_auth.get("actor") or "NONE").strip() or "NONE",
        }
    auth = result.get("authorization") or {}
    if result["risk"] == "R3":
        if auth.get("status") != "APPROVED" or not auth.get("reference"):
            raise KernelError("R3 revision requires explicit owner authorization and reference")
        actor = str(auth.get("actor", ""))
        if actor.casefold() == str(result.get("worker_id", "")).casefold() or actor.upper() in {"WORKER", "AUTO", "SELF"}:
            raise KernelError("worker cannot self-approve an R3 revision")
    result["context"] = {
        "epoch": 1,
        "epoch_id": new_id("epoch"),
        "thread_id": None,
        "requests_in_epoch": 0,
        "projected_prompt_tokens": None,
        "last_signal": "NEW_REVISION",
    }
    result["next_action"] = "implement the revised scope, then record-commit"
    # Prior revision state/evidence is already immutable in the parent
    # generation chain.  Do not copy full history into every new snapshot.
    result["history"] = []
    result["contract_hash"] = sha256_json({
        "task_id": result["task_id"],
        "outcome": result["outcome"],
        "acceptance": result["acceptance"],
        "acceptance_commands": result.get("acceptance_commands") or [],
        "risk": result["risk"],
        "side_effect": result["side_effect"],
        "allowed_paths": result["allowed_paths"],
        "prohibited_paths": result["prohibited_paths"],
        "worker_id": result["worker_id"],
        "enforcement": result["enforcement"],
        "authorization": result["authorization"],
        "skill": result.get("skill"),
    })
    validate_state(result)
    return result, {
        "kind": "NEW_REVISION",
        "revision": result["revision"],
        "reason": str(reason).strip(),
        "risk": result["risk"],
        "allowed_paths": result["allowed_paths"],
        "prohibited_paths": result["prohibited_paths"],
        "authorization_reference": (result.get("authorization") or {}).get("reference"),
    }


RISKS_ORDER = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}


def state_hash(state: Mapping[str, Any]) -> str:
    return sha256_json(state)
