"""Pure lifecycle model for the v1.24 candidate.

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


# v1.24 adds only optional lineage/provenance/execution fields. Keeping the v1.22 state
# schema is deliberate backward compatibility: existing immutable generations
# remain readable without an in-place migration.  A future incompatible shape
# must use the explicit migration contract documented by the lifecycle kit.
SCHEMA = "buildos.state.v1.22"
GENERATION_SCHEMA = "buildos.generation.v1"
PHASES = {"ACTIVE", "PRODUCT_COMMITTED", "ASSURANCE_READY", "BLOCKED_SOURCE_FIX", "CLOSED", "ABORTED"}
RISKS = {"R0", "R1", "R2", "R3"}
PRODUCT_CHANGE_MODES = {"PRODUCT_DELTA", "NO_SOURCE_DELTA"}
EXECUTION_CLASSES = {"LOCAL_REVERSIBLE", "LOCAL_HIGH_COST", "EXTERNAL_EFFECT"}
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
    side_effect = str(request.get("side_effect", "READ_ONLY")).upper()
    raw_change_mode = str(request.get("product_change_mode") or "").upper().strip()
    product_change_mode = raw_change_mode or ("NO_SOURCE_DELTA" if side_effect == "READ_ONLY" else "PRODUCT_DELTA")
    if product_change_mode not in PRODUCT_CHANGE_MODES:
        raise KernelError("product_change_mode must be PRODUCT_DELTA or NO_SOURCE_DELTA")
    allowed = _clean_list(request.get("allowed_paths") or request.get("modify") or [])
    prohibited = _clean_list(request.get("prohibited_paths") or request.get("prohibited") or [])
    if side_effect == "READ_ONLY" and allowed:
        raise KernelError("READ_ONLY tasks cannot declare writable allowed paths")
    if product_change_mode == "NO_SOURCE_DELTA" and allowed:
        raise KernelError("NO_SOURCE_DELTA tasks cannot declare writable product paths")
    if not allowed and side_effect != "READ_ONLY" and product_change_mode == "PRODUCT_DELTA":
        raise KernelError("write-capable tasks require at least one allowed path")
    if not allowed:
        allowed = ["<none-read-only>" if side_effect == "READ_ONLY" else "<none-no-source-delta>"]
    execution_class = str(request.get("execution_class") or "LOCAL_REVERSIBLE").upper().strip()
    if execution_class not in EXECUTION_CLASSES:
        raise KernelError(f"execution_class must be one of {sorted(EXECUTION_CLASSES)}")
    raw_skill = request.get("skill")
    return {
        "task_id": task_id,
        "outcome": outcome,
        "acceptance": acceptance,
        "risk": risk,
        "side_effect": side_effect,
        "product_change_mode": product_change_mode,
        "execution_class": execution_class,
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


def _validate_lineage(lineage: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if lineage is None:
        return None
    value = dict(lineage)
    required = {
        "kind", "source_task_id", "source_revision", "source_phase",
        "source_generation", "source_generation_hash", "reason", "resolution_reference",
    }
    if set(value) != required or value.get("kind") != "CONTINUATION":
        raise KernelError("continuation lineage has an invalid shape")
    if not TASK_ID_RE.fullmatch(str(value.get("source_task_id", ""))):
        raise KernelError("continuation lineage has an invalid source task")
    if int(value.get("source_revision", 0)) < 1 or int(value.get("source_generation", 0)) < 1:
        raise KernelError("continuation lineage has an invalid source revision or generation")
    if value.get("source_phase") not in {"CLOSED", "ABORTED", "BLOCKED_SOURCE_FIX"}:
        raise KernelError("continuation lineage must reference a released source")
    if not re.fullmatch(r"[0-9a-f]{64}", str(value.get("source_generation_hash", ""))):
        raise KernelError("continuation lineage has an invalid source generation hash")
    if not str(value.get("reason", "")).strip():
        raise KernelError("continuation lineage requires a reason")
    resolution = str(value.get("resolution_reference") or "").strip() or None
    if value.get("source_phase") == "BLOCKED_SOURCE_FIX" and not resolution:
        raise KernelError("continuation of a source-fix block requires a resolution reference")
    value["source_revision"] = int(value["source_revision"])
    value["source_generation"] = int(value["source_generation"])
    value["reason"] = str(value["reason"]).strip()
    value["resolution_reference"] = resolution
    return value


def initial_state(
    request: Mapping[str, Any],
    git: Mapping[str, Any] | None,
    *,
    lineage: Mapping[str, Any] | None = None,
    execution: Mapping[str, Any] | None = None,
    at: str | None = None,
) -> dict[str, Any]:
    req = validate_task_request(request)
    normalized_lineage = _validate_lineage(lineage)
    if req["product_change_mode"] == "NO_SOURCE_DELTA" and req["side_effect"] != "READ_ONLY" and (not (git or {}).get("available") or not (git or {}).get("head")):
        raise KernelError("NO_SOURCE_DELTA tasks require a known baseline product HEAD")
    stamp = at or req["created_at"]
    epoch_id = new_id("epoch")
    contract = {
        "task_id": req["task_id"],
        "outcome": req["outcome"],
        "acceptance": req["acceptance"],
        "acceptance_commands": req["acceptance_commands"],
        "risk": req["risk"],
        "side_effect": req["side_effect"],
        "product_change_mode": req["product_change_mode"],
        "execution_class": req["execution_class"],
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
        "lineage": normalized_lineage,
        "execution_envelope_hash": (execution or {}).get("envelope_hash"),
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
        "product_change_mode": req["product_change_mode"],
        "execution_class": req["execution_class"],
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
        "lineage": normalized_lineage,
        "execution": deepcopy(dict(execution)) if execution is not None else None,
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
            else (
                "complete runtime acceptance evidence, then validate the unchanged product baseline"
                if req["product_change_mode"] == "NO_SOURCE_DELTA"
                else "implement product change, then run record-commit"
            )
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
    _validate_lineage(state.get("lineage"))
    phase = state.get("phase")
    if phase not in PHASES:
        raise KernelError(f"invalid lifecycle phase: {phase}")
    risk = state.get("risk")
    if risk not in RISKS:
        raise KernelError("canonical state has invalid risk")
    change_mode = _product_change_mode(state)
    if change_mode not in PRODUCT_CHANGE_MODES:
        raise KernelError("canonical state has invalid product_change_mode")
    execution_class = str(state.get("execution_class") or "LOCAL_REVERSIBLE").upper()
    if execution_class not in EXECUTION_CLASSES:
        raise KernelError("canonical state has invalid execution_class")
    if state.get("execution") is not None:
        from .execution import validate_runtime_state
        validate_runtime_state(state["execution"])
    auth = state.get("authorization") or {}
    if risk in AUTH_REQUIRED and (auth.get("status") != "APPROVED" or not auth.get("reference")):
        raise KernelError("canonical R3 state is missing owner authorization")
    lease = state.get("lease") or {}
    if phase in {"CLOSED", "ABORTED", "BLOCKED_SOURCE_FIX"} and lease.get("status") != "RELEASED":
        raise KernelError("non-live state must release its lease")
    if phase in {"ACTIVE", "PRODUCT_COMMITTED", "ASSURANCE_READY"} and lease.get("status") != "CLAIMED":
        raise KernelError("live state must have a claimed lease")
    if phase == "PRODUCT_COMMITTED" and not (state.get("product_commit") or {}).get("sha"):
        raise KernelError("PRODUCT_COMMITTED requires a product commit anchor")
    commit = state.get("product_commit") or {}
    if change_mode == "NO_SOURCE_DELTA" and commit:
        raise KernelError("NO_SOURCE_DELTA state cannot contain a product commit anchor")
    if phase == "PRODUCT_COMMITTED" and change_mode != "PRODUCT_DELTA":
        raise KernelError("PRODUCT_COMMITTED is forbidden for NO_SOURCE_DELTA tasks")
    origin = commit.get("origin", "NATIVE")
    if commit and origin not in {"NATIVE", "EXTERNAL_PREEXISTING"}:
        raise KernelError("canonical product commit has an invalid provenance origin")
    if origin == "EXTERNAL_PREEXISTING" and not str(commit.get("adoption_reason", "")).strip():
        raise KernelError("externally adopted product commit requires an adoption reason")
    if phase == "ASSURANCE_READY" and not (state.get("assurance") or {}).get("evidence_sha"):
        raise KernelError("ASSURANCE_READY requires immutable evidence")
    if phase == "CLOSED" and not (state.get("assurance") or {}).get("evidence_sha"):
        raise KernelError("CLOSED requires immutable evidence")
    assurance = state.get("assurance") or {}
    if phase in {"ASSURANCE_READY", "CLOSED"} and assurance.get("mode", change_mode) != change_mode:
        raise KernelError("assurance mode does not match the task product_change_mode")
    if phase in {"ASSURANCE_READY", "CLOSED"} and change_mode == "NO_SOURCE_DELTA" and state.get("side_effect") != "READ_ONLY":
        if not str(assurance.get("runtime_acceptance_reference") or "").strip():
            raise KernelError("NO_SOURCE_DELTA runtime assurance requires a runtime acceptance reference")


def _product_change_mode(state: Mapping[str, Any]) -> str:
    """Read additive v1.24 mode while preserving legacy READ_ONLY generations."""
    explicit = str(state.get("product_change_mode") or "").upper().strip()
    return explicit or ("NO_SOURCE_DELTA" if state.get("side_effect") == "READ_ONLY" else "PRODUCT_DELTA")


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
    policy_authorized = action == "ROLLOVER_REQUIRED" or (
        action == "HARD_STOP" and bool(signal.get("rollover_fallback_eligible"))
    )
    if not policy_authorized and not signal.get("force"):
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
    if _product_change_mode(prev) == "NO_SOURCE_DELTA":
        label = "READ_ONLY" if prev.get("side_effect") == "READ_ONLY" else "NO_SOURCE_DELTA"
        raise KernelError(f"{label} tasks cannot record a product commit; validate the unchanged baseline directly")
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
        "origin": "NATIVE",
    }
    result["next_action"] = "run validation and attach immutable evidence"
    validate_state(result)
    return result, {"kind": "PRODUCT_COMMIT", "sha": head, "tree": git.get("tree"), "relation_to_base": relation}


def transition_adopt_existing_change(
    prev: Mapping[str, Any],
    git: Mapping[str, Any],
    *,
    reason: str,
    at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Record a pre-existing clean HEAD without claiming supervised creation."""
    reason = str(reason).strip()
    if not reason:
        raise KernelError("adopt-existing-change requires a reason")
    result, event = transition_record_commit(prev, git, at=at)
    result["product_commit"]["origin"] = "EXTERNAL_PREEXISTING"
    result["product_commit"]["adoption_reason"] = reason
    result["next_action"] = "validate the externally pre-existing change and attach immutable evidence"
    validate_state(result)
    return result, {
        "kind": "ADOPT_EXISTING_CHANGE",
        "sha": event["sha"],
        "tree": event.get("tree"),
        "relation_to_base": event.get("relation_to_base"),
        "origin": "EXTERNAL_PREEXISTING",
        "reason": reason,
    }


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
    deletions = sorted({
        *[str(path) for path in git.get("deletions_since_base") or []],
        *[str(path) for path in git.get("worktree_deletions") or []],
    })
    if deletions and not (state.get("risk") == "R3" and state.get("side_effect") == "DELETE"):
        raise KernelError(f"product deletion requires an authorized R3 DELETE contract: {', '.join(deletions)}")
    type_changes = sorted({
        *[str(path) for path in git.get("type_changes_since_base") or []],
        *[str(path) for path in git.get("worktree_type_changes") or []],
    })
    if type_changes and RISKS_ORDER.get(str(state.get("risk")), -1) < RISKS_ORDER["R2"]:
        raise KernelError(f"product file type changes require at least R2: {', '.join(type_changes)}")


def validate_in_progress_product_state(state: Mapping[str, Any], git: Mapping[str, Any]) -> None:
    """Admit a stable product observation without treating it as trust or a product commit."""
    validate_state(state)
    if state.get("phase") != "ACTIVE":
        raise KernelError("in-progress product preservation requires ACTIVE lifecycle state")
    if not git.get("available") or not git.get("head"):
        raise KernelError("in-progress product preservation requires observable Git state")
    if git.get("tracked_control_paths"):
        raise KernelError("in-progress product preservation refuses tracked .buildos control paths")
    base = (state.get("base_git") or {}).get("head")
    relation = str(git.get("relation_to_base") or "UNKNOWN").upper()
    if base and relation not in {"SAME", "DESCENDANT"}:
        raise KernelError("in-progress product HEAD must remain the task baseline or its descendant")
    changed = sorted({
        *[str(path) for path in git.get("changes_since_base") or []],
        *[str(path) for path in git.get("product_dirty_paths") or []],
    })
    if _product_change_mode(state) == "NO_SOURCE_DELTA" and changed:
        raise KernelError("NO_SOURCE_DELTA task cannot preserve in-progress product mutation")
    _validate_change_kinds(state, git)
    _validate_scope(state, changed, case_insensitive=bool(git.get("case_insensitive_paths")))


def transition_validate(prev: Mapping[str, Any], git: Mapping[str, Any], evidence: Mapping[str, Any], *, at: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_state(prev)
    read_only = prev.get("side_effect") == "READ_ONLY"
    change_mode = _product_change_mode(prev)
    no_source_delta = change_mode == "NO_SOURCE_DELTA"
    runtime_no_source_delta = no_source_delta and not read_only
    if prev["phase"] != "PRODUCT_COMMITTED" and not (no_source_delta and prev["phase"] == "ACTIVE"):
        raise KernelError("validate requires PRODUCT_COMMITTED lifecycle state")
    target = ((prev.get("base_git") or {}).get("head") if no_source_delta else (prev.get("product_commit") or {}).get("sha"))
    relation = str(git.get("relation_to_base" if no_source_delta else "relation_to_product", "UNKNOWN"))
    if not target or not git.get("head"):
        raise KernelError("validation requires a current Git HEAD and product anchor")
    if git.get("tracked_control_paths"):
        raise KernelError("validation refuses tracked .buildos control files")
    if git.get("product_dirty"):
        raise KernelError("validation requires a clean product tree")
    if no_source_delta and (git.get("head") != target or relation.upper() != "SAME" or git.get("changes_since_base")):
        label = "READ_ONLY" if read_only else "NO_SOURCE_DELTA"
        raise KernelError(f"{label} validation requires the unchanged bootstrap Git baseline")
    if not _relation_allowed(relation):
        raise KernelError("current HEAD diverged from product anchor; create an explicit new revision")
    _validate_change_kinds(prev, git)
    _validate_scope(prev, git.get("changes_since_base") or [], case_insensitive=bool(git.get("case_insensitive_paths")))
    if not evidence.get("path") or not evidence.get("sha256"):
        raise KernelError("validation requires an immutable evidence reference and hash")
    runtime_acceptance_reference = str(evidence.get("runtime_acceptance_reference") or "").strip() or None
    if runtime_no_source_delta and not runtime_acceptance_reference:
        raise KernelError("NO_SOURCE_DELTA runtime validation requires a runtime acceptance reference")
    if evidence.get("target_sha") and evidence.get("target_sha") != git.get("head"):
        raise KernelError("evidence target no longer matches current HEAD; preserve it and validate the new target")
    if evidence.get("target_tree") and evidence.get("target_tree") != git.get("tree"):
        raise KernelError("evidence target tree no longer matches current product bytes; validate the frozen target again")
    if (
        ((prev.get("execution") or {}).get("mode") == "ENHANCED")
        and not evidence.get("target_tree")
    ):
        raise KernelError("enhanced validation evidence must bind the exact target tree")
    result = _next(prev, phase="ASSURANCE_READY", at=at)
    result["evidence"] = [*deepcopy(prev.get("evidence") or []), dict(evidence)]
    result["assurance"] = {
        "mode": change_mode,
        "product_anchor_sha": target,
        "target_sha": git.get("head"),
        "validated_head": git.get("head"),
        "validated_tree": git.get("tree"),
        "relation_to_product": relation,
        "evidence_sha": evidence["sha256"],
        "runtime_acceptance_reference": runtime_acceptance_reference,
        "validated_at": result["updated_at"],
    }
    result["next_action"] = (
        "close task while product HEAD remains exactly at the validated baseline"
        if runtime_no_source_delta
        else "close task; later descendant commits are refreshed, never reopened"
    )
    validate_state(result)
    return result, {"kind": "VALIDATION", "mode": change_mode, "product_anchor_sha": target, "target_sha": git.get("head"), "relation": relation, "evidence": dict(evidence)}


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
        if assurance.get("mode") == "NO_SOURCE_DELTA" and prev.get("side_effect") != "READ_ONLY" and (observed.get("head") != target or relation != "SAME"):
            raise KernelError("NO_SOURCE_DELTA close requires HEAD to remain exactly equal to the validated baseline")
        if not _relation_allowed(relation):
            raise KernelError("close refuses a divergent HEAD; preserve evidence and create an explicit new revision")
        if observed.get("product_dirty"):
            raise KernelError("close requires a clean product tree")
        if relation == "DESCENDANT" and observed.get("changes_since_validated"):
            raise KernelError("product files changed after validation; preserve evidence and validate a new revision")
        if relation == "DESCENDANT" and observed.get("tree") != assurance.get("validated_tree"):
            raise KernelError("close permits only a tree-equivalent descendant of the validated target")
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


def transition_block_for_source_fix(
    prev: Mapping[str, Any],
    *,
    reason: str,
    defect_reference: str,
    at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Release a live task without misclassifying a source defect as an abort."""
    validate_state(prev)
    if prev["phase"] not in {"ACTIVE", "PRODUCT_COMMITTED", "ASSURANCE_READY"}:
        raise KernelError("block-for-source-fix requires a live task state")
    reason = str(reason).strip()
    defect_reference = str(defect_reference).strip()
    if not reason or not defect_reference:
        raise KernelError("block-for-source-fix requires a reason and defect reference")
    result = _next(prev, phase="BLOCKED_SOURCE_FIX", at=at)
    result["lease"] = {"status": "RELEASED", "holder": result.get("worker_id")}
    result["lifecycle_ready"] = False
    result["source_defect"] = {
        "reason": reason,
        "reference": defect_reference,
        "blocked_at": result["updated_at"],
    }
    result["next_action"] = "complete a bounded source repair task, then continue via immutable lineage"
    validate_state(result)
    return result, {
        "kind": "BLOCK_FOR_SOURCE_FIX",
        "reason": reason,
        "defect_reference": defect_reference,
    }


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
        if _product_change_mode(result) == "NO_SOURCE_DELTA" and revised_allowed:
            raise KernelError("NO_SOURCE_DELTA revision cannot declare writable product paths")
        if not revised_allowed and result.get("side_effect") != "READ_ONLY" and _product_change_mode(result) == "PRODUCT_DELTA":
            raise KernelError("write-capable revision requires at least one allowed path")
        result["allowed_paths"] = revised_allowed or (["<none-no-source-delta>"] if _product_change_mode(result) == "NO_SOURCE_DELTA" else ["<declared-by-worker>"])
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
    if result.get("execution") is not None:
        from .execution import reset_for_lifecycle_revision
        result["execution"] = reset_for_lifecycle_revision(result["execution"])
    result["next_action"] = (
        "complete runtime acceptance evidence, then validate the unchanged product baseline"
        if _product_change_mode(result) == "NO_SOURCE_DELTA" and result.get("side_effect") != "READ_ONLY"
        else "implement the revised scope, then record-commit"
    )
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
        "product_change_mode": _product_change_mode(result),
        "execution_class": str(result.get("execution_class") or "LOCAL_REVERSIBLE"),
        "allowed_paths": result["allowed_paths"],
        "prohibited_paths": result["prohibited_paths"],
        "worker_id": result["worker_id"],
        "enforcement": result["enforcement"],
        "authorization": result["authorization"],
        "skill": result.get("skill"),
        "execution_envelope_hash": ((result.get("execution") or {}).get("envelope_hash")),
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
