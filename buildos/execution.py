"""Integrated execution admission, effect and proportional-assurance runtime.

This module deliberately does not create another mutable authority.  Its
compiled envelope, blocker decisions, effect ledger and claim results live in
the immutable lifecycle generation selected by CURRENT.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import fnmatch
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Mapping, Sequence

from .model import KernelError, sha256_json


SPEC_SCHEMA = "buildos.execution-spec.v1"
RUNTIME_SCHEMA = "buildos.execution-runtime.v1"
SPEC_FIELDS = {
    "schema", "plan_id", "cost_class", "assumptions", "capabilities",
    "authorities", "commands", "claims", "effects", "steps", "recovery",
}
ID = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
COST_CLASSES = {"LOW", "MEDIUM", "HIGH", "EXTERNAL"}
ASSUMPTION_STATES = {"PROVEN", "BOUNDED", "UNKNOWN", "REJECTED"}
CAPABILITY_STATES = {"AVAILABLE", "UNAVAILABLE", "UNKNOWN", "DISCOVERABLE", "RESTRICTED"}
AUTHORITY_MODES = {"CANONICAL", "ADVISORY", "DERIVED", "EXECUTOR"}
OWNER_KINDS = {"PRODUCT", "LIFECYCLE", "DETERMINISTIC_COMPILER", "PROVIDER", "QC", "HUMAN", "LLM"}
COMMAND_PROVENANCE = {"OWNER_AUTHORED", "PACKAGE_OWNED", "MODEL_PROPOSED_APPROVED"}
COMMAND_SOURCE_KINDS = {"PROJECT_BASELINE", "PACKAGE_MANIFEST", "OWNER_APPROVAL"}
CLAIM_ROLES = {"ACCEPTANCE", "ROLLBACK_RECOVERY", "SECURITY", "QC"}
CLAIM_MODES = {"AFFECTED", "FINAL"}
STEP_KINDS = {"LOCAL", "EXTERNAL_EFFECT", "REVIEW", "PERSIST"}
RECOVERY_DISPOSITIONS = {"BOUNDED_FIX", "REPLAN", "RECONCILE", "STOP"}
EFFECT_STATES = {
    "INTENT_RECORDED", "DISPATCH_UNCONFIRMED", "DISPATCH_CONFIRMED",
    "OUTPUT_CONFIRMED", "COMMITTED", "RESOLVED_NO_EFFECT", "RETRY_AUTHORIZED",
}
TERMINAL_EFFECT_STATES = {"COMMITTED", "RESOLVED_NO_EFFECT"}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _deadline(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KernelError(f"execution spec {label} is required")
    return value.strip()


def _id(value: Any, label: str) -> str:
    result = _text(value, label)
    if not ID.fullmatch(result):
        raise KernelError(f"execution spec {label} must be a portable lowercase identifier")
    return result


def _rows(value: Any, label: str, *, allow_empty: bool = False) -> list[dict[str, Any]]:
    if not isinstance(value, list) or (not allow_empty and not value) or any(not isinstance(item, dict) for item in value):
        qualifier = "an object list" if allow_empty else "a non-empty object list"
        raise KernelError(f"execution spec {label} must be {qualifier}")
    return [dict(item) for item in value]


def _ids(value: Any, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise KernelError(f"execution spec {label} must be a list")
    result = [_id(item, label) for item in value]
    if len(set(result)) != len(result):
        raise KernelError(f"execution spec {label} must be unique")
    return result


def _safe_patterns(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise KernelError(f"execution spec {label} must contain path dependencies")
    result: list[str] = []
    for raw in value:
        pattern = _text(raw, label).replace("\\", "/")
        if pattern.startswith(("/", "../")) or "/../" in f"/{pattern}/" or pattern.startswith(".buildos"):
            raise KernelError(f"execution spec {label} contains an unsafe product path pattern")
        if pattern not in result:
            result.append(pattern)
    return result


def _safe_source_path(value: Any, label: str) -> str:
    path = _text(value, label).replace("\\", "/")
    parsed = Path(path)
    if parsed.is_absolute() or parsed.drive or ".." in parsed.parts or path.startswith("/"):
        raise KernelError(f"execution spec {label} must be a safe relative path")
    return path


def _registry_entry(data: bytes, *, command_id: str, argv: list[str], label: str) -> None:
    try:
        value = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KernelError(f"{label} is not a readable command registry") from exc
    if not isinstance(value, dict) or set(value) != {"schema", "commands"} or value.get("schema") != "buildos.command-registry.v1":
        raise KernelError(f"{label} has an invalid command-registry schema")
    rows = value.get("commands")
    if not isinstance(rows, list) or any(not isinstance(row, dict) or set(row) != {"id", "argv"} for row in rows):
        raise KernelError(f"{label} has invalid command entries")
    matches = [row for row in rows if row.get("id") == command_id]
    if len(matches) != 1 or matches[0].get("argv") != argv:
        raise KernelError(f"command {command_id} does not match its trusted registry entry")


def _approval_registry_entry(data: bytes, *, reference: str, command_hash: str, label: str) -> None:
    try:
        value = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KernelError(f"{label} is not a readable command approval registry") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"schema", "approvals"}
        or value.get("schema") != "buildos.command-approval-registry.v1"
    ):
        raise KernelError(f"{label} has an invalid command-approval-registry schema")
    rows = value.get("approvals")
    if not isinstance(rows, list) or any(
        not isinstance(row, dict) or set(row) != {"reference", "command_sha256"}
        for row in rows
    ):
        raise KernelError(f"{label} has invalid command approval entries")
    matches = [
        row for row in rows
        if row.get("reference") == reference and row.get("command_sha256") == command_hash
    ]
    if len(matches) != 1:
        raise KernelError("model-proposed command does not match one exact baseline owner approval")


def _baseline_source_bytes(
    *, root: Path, git_head: str, path: str, expected: str, label: str,
) -> bytes:
    proc = subprocess.run(
        ["git", "show", f"{git_head}:{path}"], cwd=root, capture_output=True,
        timeout=30, check=False,
    )
    if proc.returncode or hashlib.sha256(proc.stdout).hexdigest() != expected:
        raise KernelError(f"{label} is not bound to the current Git baseline")
    current = root / path
    if not current.is_file() or current.read_bytes() != proc.stdout:
        raise KernelError(f"{label} differs from the current Git baseline")
    return proc.stdout


def _bind_command_source(
    row: Mapping[str, Any], request: Mapping[str, Any], *,
    root: Path, package_root: Path, git_head: str,
) -> dict[str, Any]:
    identifier = str(row["id"])
    argv = list(row["argv"])
    provenance = str(row["provenance"])
    source = row.get("source")
    if not isinstance(source, Mapping) or str(source.get("kind") or "").upper() not in COMMAND_SOURCE_KINDS:
        raise KernelError(f"execution command {identifier} requires a deterministic provenance source")
    kind = str(source["kind"]).upper()
    command_hash = sha256_json({"id": identifier, "argv": argv})

    if provenance == "MODEL_PROPOSED_APPROVED":
        if set(source) != {"kind", "path", "sha256", "reference", "command_sha256"} or kind != "OWNER_APPROVAL":
            raise KernelError(f"model-proposed command {identifier} requires exact baseline owner-approval binding")
        approval = request.get("authorization") or {
            "status": request.get("owner_authorization"),
            "reference": request.get("authorization_reference"),
            "actor": request.get("authorization_actor"),
        }
        path = _safe_source_path(source.get("path"), f"command {identifier}.source.path")
        expected = str(source.get("sha256") or "").lower()
        reference = _text(source.get("reference"), f"command {identifier}.source.reference")
        if (
            approval.get("status") != "APPROVED"
            or approval.get("reference") != reference
            or str(source.get("command_sha256") or "").lower() != command_hash
            or not re.fullmatch(r"[0-9a-f]{64}", expected)
        ):
            raise KernelError(f"model-proposed command {identifier} is not bound to explicit owner approval and its exact argv hash")
        data = _baseline_source_bytes(
            root=root, git_head=git_head, path=path, expected=expected,
            label=f"model-proposed command {identifier} approval registry",
        )
        _approval_registry_entry(data, reference=reference, command_hash=command_hash, label=path)
        return {
            "kind": kind, "path": path, "sha256": expected,
            "reference": reference, "command_sha256": command_hash,
        }

    if set(source) != {"kind", "path", "sha256"}:
        raise KernelError(f"trusted command {identifier} requires exact registry path/hash binding")
    path = _safe_source_path(source.get("path"), f"command {identifier}.source.path")
    expected = str(source.get("sha256") or "").lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise KernelError(f"trusted command {identifier} registry SHA-256 is invalid")

    if provenance == "OWNER_AUTHORED":
        if kind != "PROJECT_BASELINE":
            raise KernelError(f"owner-authored command {identifier} must come from the Git baseline")
        data = _baseline_source_bytes(
            root=root, git_head=git_head, path=path, expected=expected,
            label=f"owner-authored command {identifier} registry",
        )
    elif provenance == "PACKAGE_OWNED":
        if kind != "PACKAGE_MANIFEST":
            raise KernelError(f"package-owned command {identifier} must come from a package-manifest registry")
        registry = package_root / path
        manifest_path = package_root / "PACKAGE_MANIFEST.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise KernelError("package-owned command registry requires a readable package manifest") from exc
        declared = manifest.get("trusted_command_registries") or {}
        if not isinstance(declared, Mapping):
            raise KernelError("package manifest trusted command registries must be a path/hash object")
        if declared.get(path) != expected or not registry.is_file() or hashlib.sha256(registry.read_bytes()).hexdigest() != expected:
            raise KernelError(f"package-owned command {identifier} registry is not bound by the package manifest")
        data = registry.read_bytes()
    else:
        raise KernelError(f"command {identifier} provenance/source combination is invalid")
    _registry_entry(data, command_id=identifier, argv=argv, label=path)
    return {"kind": kind, "path": path, "sha256": expected, "command_sha256": command_hash}


def _acyclic(steps: Mapping[str, Mapping[str, Any]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(step_id: str) -> None:
        if step_id in visiting:
            raise KernelError("execution plan step dependencies contain a cycle")
        if step_id in visited:
            return
        visiting.add(step_id)
        for parent in steps[step_id]["after"]:
            visit(parent)
        visiting.remove(step_id)
        visited.add(step_id)

    for identifier in steps:
        visit(identifier)


def execution_required(request: Mapping[str, Any]) -> bool:
    execution_class = str(request.get("execution_class") or "LOCAL_REVERSIBLE").upper()
    # Existing callers remain readable/runnable as LEGACY_LOCAL.  A caller
    # opts into a high-cost or external execution class explicitly; those
    # classes cannot start without the stronger envelope.
    return execution_class != "LOCAL_REVERSIBLE" or bool(request.get("requires_execution_envelope"))


def legacy_runtime(request: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": RUNTIME_SCHEMA,
        "mode": "LEGACY_LOCAL",
        "plan_validity": "VALID",
        "plan_revision": 0,
        "envelope_hash": None,
        "envelope": None,
        "blockers": [],
        "effect_ledger": {},
        "effect_history": [],
        "reviews": [],
        "claim_results": {},
        "enhanced_guarantees": False,
    }


def load_spec(path: Path | str) -> dict[str, Any]:
    source = Path(path).resolve()
    try:
        value = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise KernelError(f"execution spec is not readable JSON: {source}") from exc
    if not isinstance(value, dict):
        raise KernelError("execution spec must be a JSON object")
    return value


def compile_spec(
    value: Mapping[str, Any], request: Mapping[str, Any], *, plan_revision: int = 1,
    root: Path, package_root: Path, git_head: str,
) -> dict[str, Any]:
    """Compile one task plan into a deterministic fail-closed envelope."""
    if not isinstance(value, Mapping) or value.get("schema") != SPEC_SCHEMA:
        raise KernelError(f"execution spec schema must be {SPEC_SCHEMA}")
    if set(value) != SPEC_FIELDS:
        raise KernelError(f"execution spec fields must be exactly {sorted(SPEC_FIELDS)}")
    if request.get("acceptance_commands"):
        raise KernelError("enhanced execution uses the trusted command registry; bootstrap --check strings are not allowed")
    plan_id = _id(value.get("plan_id"), "plan_id")
    cost_class = str(value.get("cost_class") or "").upper()
    if cost_class not in COST_CLASSES:
        raise KernelError(f"execution spec cost_class must be one of {sorted(COST_CLASSES)}")

    blockers: list[dict[str, str]] = []

    assumptions: dict[str, dict[str, Any]] = {}
    for row in _rows(value.get("assumptions"), "assumptions"):
        if set(row) != {"id", "statement", "status", "critical", "evidence", "fallback"}:
            raise KernelError("execution spec assumption has an invalid shape")
        identifier = _id(row.get("id"), "assumption id")
        if identifier in assumptions or not isinstance(row.get("critical"), bool):
            raise KernelError("execution spec assumptions must have unique ids and boolean critical")
        status = str(row.get("status") or "").upper()
        if status not in ASSUMPTION_STATES:
            raise KernelError(f"execution assumption {identifier} has invalid status")
        evidence = str(row.get("evidence") or "").strip() or None
        fallback = str(row.get("fallback") or "").strip() or None
        if status == "PROVEN" and not evidence:
            blockers.append({"code": "ASSUMPTION_PROOF_MISSING", "subject": identifier})
        if status == "BOUNDED" and not fallback:
            blockers.append({"code": "ASSUMPTION_FALLBACK_MISSING", "subject": identifier})
        if row["critical"] and status in {"UNKNOWN", "REJECTED"}:
            blockers.append({"code": "CRITICAL_ASSUMPTION_UNRESOLVED", "subject": identifier})
        assumptions[identifier] = {
            "id": identifier, "statement": _text(row.get("statement"), f"assumption {identifier}.statement"),
            "status": status, "critical": row["critical"], "evidence": evidence, "fallback": fallback,
        }

    capabilities: dict[str, dict[str, Any]] = {}
    for row in _rows(value.get("capabilities"), "capabilities"):
        if set(row) != {"id", "status", "source", "evidence", "constraints"}:
            raise KernelError("execution spec capability has an invalid shape")
        identifier = _id(row.get("id"), "capability id")
        if identifier in capabilities:
            raise KernelError("execution capability ids must be unique")
        status = str(row.get("status") or "").upper()
        if status not in CAPABILITY_STATES:
            raise KernelError(f"execution capability {identifier} has invalid status")
        source = str(row.get("source") or "").upper()
        if source not in {"OWNER", "DETERMINISTIC_PROBE", "PROVIDER_CONTRACT", "PACKAGE"}:
            raise KernelError(f"execution capability {identifier} has invalid source authority")
        evidence = str(row.get("evidence") or "").strip() or None
        constraints = row.get("constraints")
        if not isinstance(constraints, dict):
            raise KernelError(f"execution capability {identifier}.constraints must be an object")
        if status in {"AVAILABLE", "RESTRICTED"} and not evidence:
            blockers.append({"code": "CAPABILITY_EVIDENCE_MISSING", "subject": identifier})
        capabilities[identifier] = {
            "id": identifier, "status": status, "source": source,
            "evidence": evidence, "constraints": dict(constraints),
        }

    authorities: dict[str, dict[str, Any]] = {}
    for row in _rows(value.get("authorities"), "authorities"):
        if set(row) != {"field", "owner", "owner_kind", "mode", "evidence"}:
            raise KernelError("execution authority row has an invalid shape")
        field = _id(row.get("field"), "authority field")
        mode = str(row.get("mode") or "").upper()
        owner_kind = str(row.get("owner_kind") or "").upper()
        if field in authorities or mode not in AUTHORITY_MODES or owner_kind not in OWNER_KINDS:
            raise KernelError(f"execution authority {field} is invalid or duplicated")
        if owner_kind == "LLM" and mode != "ADVISORY":
            blockers.append({"code": "LLM_CANNOT_BE_CANONICAL_AUTHORITY", "subject": field})
        evidence = str(row.get("evidence") or "").strip() or None
        if mode == "CANONICAL" and not evidence:
            blockers.append({"code": "CANONICAL_AUTHORITY_EVIDENCE_MISSING", "subject": field})
        authorities[field] = {
            "field": field, "owner": _text(row.get("owner"), f"authority {field}.owner"),
            "owner_kind": owner_kind, "mode": mode, "evidence": evidence,
        }

    commands: dict[str, dict[str, Any]] = {}
    for row in _rows(value.get("commands"), "commands"):
        if set(row) != {"id", "argv", "provenance", "source"}:
            raise KernelError("execution command has an invalid shape")
        identifier = _id(row.get("id"), "command id")
        argv = row.get("argv")
        provenance = str(row.get("provenance") or "").upper()
        if identifier in commands or not isinstance(argv, list) or not argv or any(not isinstance(arg, str) or not arg for arg in argv):
            raise KernelError(f"execution command {identifier} requires a unique id and non-empty argv")
        if provenance not in COMMAND_PROVENANCE:
            raise KernelError(f"execution command {identifier} has invalid provenance")
        normalized_command = {"id": identifier, "argv": list(argv), "provenance": provenance}
        normalized_command["source"] = _bind_command_source(
            {**normalized_command, "source": row.get("source")}, request,
            root=root, package_root=package_root, git_head=git_head,
        )
        normalized_command["command_hash"] = sha256_json({"id": identifier, "argv": list(argv)})
        commands[identifier] = normalized_command

    claims: dict[str, dict[str, Any]] = {}
    for row in _rows(value.get("claims"), "claims"):
        if set(row) != {"id", "description", "command_id", "dependencies", "mode", "role", "acceptance"}:
            raise KernelError("execution claim has an invalid shape")
        identifier = _id(row.get("id"), "claim id")
        command_id = _id(row.get("command_id"), f"claim {identifier}.command_id")
        mode = str(row.get("mode") or "").upper()
        role = str(row.get("role") or "").upper()
        if identifier in claims or command_id not in commands or mode not in CLAIM_MODES or role not in CLAIM_ROLES:
            raise KernelError(f"execution claim {identifier} is invalid")
        acceptance = row.get("acceptance")
        if not isinstance(acceptance, list) or not acceptance or any(not isinstance(item, str) or not item.strip() for item in acceptance):
            raise KernelError(f"execution claim {identifier}.acceptance must bind one or more acceptance criteria")
        unknown_acceptance = sorted(set(acceptance) - set(request.get("acceptance") or []))
        if unknown_acceptance:
            raise KernelError(f"execution claim {identifier} binds unknown acceptance criteria: {unknown_acceptance}")
        normalized = {
            "id": identifier, "description": _text(row.get("description"), f"claim {identifier}.description"),
            "command_id": command_id, "dependencies": _safe_patterns(row.get("dependencies"), f"claim {identifier}.dependencies"),
            "mode": mode, "role": role,
            "acceptance": list(dict.fromkeys(acceptance)),
            "command_hash": commands[command_id]["command_hash"],
        }
        normalized["semantic_hash"] = sha256_json(normalized)
        claims[identifier] = normalized
    if not any(row["mode"] == "FINAL" for row in claims.values()):
        blockers.append({"code": "FINAL_ASSURANCE_CLAIM_MISSING", "subject": plan_id})
    uncovered_acceptance = sorted(set(request.get("acceptance") or []) - {item for claim in claims.values() for item in claim["acceptance"]})
    for criterion in uncovered_acceptance:
        blockers.append({"code": "ACCEPTANCE_NOT_OPERATIONALLY_BOUND", "subject": criterion})
    if str(request.get("risk") or "").upper() == "R3" and not any(row["role"] == "ROLLBACK_RECOVERY" for row in claims.values()):
        blockers.append({"code": "R3_ROLLBACK_CLAIM_MISSING", "subject": plan_id})

    effects: dict[str, dict[str, Any]] = {}
    for row in _rows(value.get("effects"), "effects", allow_empty=True):
        if set(row) != {"id", "idempotency", "idempotency_key", "no_effect_predicate", "provider_capability", "deadline_seconds", "required", "effect_input_sha256", "adapter_contract_sha256"}:
            raise KernelError("execution effect has an invalid shape")
        identifier = _id(row.get("id"), "effect id")
        idempotency = str(row.get("idempotency") or "").upper()
        provider = _id(row.get("provider_capability"), f"effect {identifier}.provider_capability")
        if identifier in effects or idempotency not in {"IDEMPOTENT_WITH_KEY", "NON_IDEMPOTENT"} or provider not in capabilities:
            raise KernelError(f"execution effect {identifier} is invalid")
        try:
            deadline = int(row.get("deadline_seconds"))
        except (TypeError, ValueError) as exc:
            raise KernelError(f"execution effect {identifier} deadline must be an integer") from exc
        if deadline <= 0 or deadline > 86400 or not isinstance(row.get("required"), bool):
            raise KernelError(f"execution effect {identifier} has an invalid deadline or required flag")
        key = str(row.get("idempotency_key") or "").strip() or None
        proof = str(row.get("no_effect_predicate") or "").strip() or None
        effect_input = str(row.get("effect_input_sha256") or "").lower()
        adapter_contract = str(row.get("adapter_contract_sha256") or "").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", effect_input) or not re.fullmatch(r"[0-9a-f]{64}", adapter_contract):
            raise KernelError(f"execution effect {identifier} requires exact effect input and adapter contract SHA-256 bindings")
        if idempotency == "IDEMPOTENT_WITH_KEY" and not key:
            blockers.append({"code": "IDEMPOTENCY_KEY_MISSING", "subject": identifier})
        if idempotency == "NON_IDEMPOTENT" and not proof:
            blockers.append({"code": "NO_EFFECT_PREDICATE_MISSING", "subject": identifier})
        if proof and not ID.fullmatch(proof):
            raise KernelError(f"execution effect {identifier}.no_effect_predicate must be a canonical predicate id")
        effects[identifier] = {
            "id": identifier, "idempotency": idempotency, "idempotency_key": key,
            "no_effect_predicate": proof, "provider_capability": provider,
            "deadline_seconds": deadline, "required": row["required"],
            "effect_input_sha256": effect_input, "adapter_contract_sha256": adapter_contract,
        }

    recoveries: dict[str, dict[str, Any]] = {}
    for row in _rows(value.get("recovery"), "recovery"):
        if set(row) != {"family", "disposition", "max_bounded_occurrences", "evidence_required"}:
            raise KernelError("execution recovery row has an invalid shape")
        family = _id(row.get("family"), "recovery family")
        disposition = str(row.get("disposition") or "").upper()
        try:
            maximum = int(row.get("max_bounded_occurrences"))
        except (TypeError, ValueError) as exc:
            raise KernelError(f"execution recovery {family} has invalid occurrence limit") from exc
        if family in recoveries or disposition not in RECOVERY_DISPOSITIONS or maximum < 0 or maximum > 1 or not isinstance(row.get("evidence_required"), bool):
            raise KernelError(f"execution recovery {family} is invalid")
        recoveries[family] = {
            "family": family, "disposition": disposition,
            "max_bounded_occurrences": maximum, "evidence_required": row["evidence_required"],
        }

    steps: dict[str, dict[str, Any]] = {}
    referenced_families: set[str] = set()
    for row in _rows(value.get("steps"), "steps"):
        if set(row) != {"id", "kind", "after", "requires_assumptions", "requires_capabilities", "capability_constraints", "reads", "writes", "effect_id", "failure_families"}:
            raise KernelError("execution step has an invalid shape")
        identifier = _id(row.get("id"), "step id")
        kind = str(row.get("kind") or "").upper()
        after = _ids(row.get("after"), f"step {identifier}.after")
        required_assumptions = _ids(row.get("requires_assumptions"), f"step {identifier}.requires_assumptions")
        required_capabilities = _ids(row.get("requires_capabilities"), f"step {identifier}.requires_capabilities")
        capability_constraints = row.get("capability_constraints")
        if not isinstance(capability_constraints, dict) or any(not isinstance(requirements, dict) for requirements in capability_constraints.values()):
            raise KernelError(f"execution step {identifier}.capability_constraints must map capability ids to constraints")
        if set(capability_constraints) - set(required_capabilities):
            raise KernelError(f"execution step {identifier} constrains a capability it does not require")
        reads = _ids(row.get("reads"), f"step {identifier}.reads")
        writes = _ids(row.get("writes"), f"step {identifier}.writes")
        families = _ids(row.get("failure_families"), f"step {identifier}.failure_families", allow_empty=False)
        effect_id = str(row.get("effect_id") or "").strip() or None
        if identifier in steps or kind not in STEP_KINDS:
            raise KernelError(f"execution step {identifier} is invalid or duplicated")
        for assumption in required_assumptions:
            if assumption not in assumptions:
                raise KernelError(f"execution step {identifier} references unknown assumption: {assumption}")
        for capability in required_capabilities:
            if capability not in capabilities:
                raise KernelError(f"execution step {identifier} references unknown capability: {capability}")
            if capabilities[capability]["status"] not in {"AVAILABLE", "RESTRICTED"}:
                blockers.append({"code": "REQUIRED_CAPABILITY_NOT_READY", "subject": capability})
            available_constraints = capabilities[capability]["constraints"]
            for key, expected in (capability_constraints.get(capability) or {}).items():
                if key not in available_constraints or available_constraints[key] != expected:
                    blockers.append({
                        "code": "CAPABILITY_CONSTRAINT_UNSATISFIED",
                        "subject": f"{identifier}:{capability}:{key}",
                    })
        for field in [*reads, *writes]:
            if field not in authorities:
                blockers.append({"code": "FIELD_AUTHORITY_UNRESOLVED", "subject": field})
        if kind == "EXTERNAL_EFFECT" and (not effect_id or effect_id not in effects):
            blockers.append({"code": "EXTERNAL_EFFECT_CONTRACT_MISSING", "subject": identifier})
        if kind != "EXTERNAL_EFFECT" and effect_id:
            raise KernelError(f"non-external step {identifier} cannot bind an effect")
        referenced_families.update(families)
        steps[identifier] = {
            "id": identifier, "kind": kind, "after": after,
            "requires_assumptions": required_assumptions, "requires_capabilities": required_capabilities,
            "capability_constraints": deepcopy(capability_constraints),
            "reads": reads, "writes": writes, "effect_id": effect_id, "failure_families": families,
        }
    for step in steps.values():
        unknown = sorted(set(step["after"]) - set(steps))
        if unknown:
            raise KernelError(f"execution step {step['id']} references unknown predecessors: {unknown}")
    _acyclic(steps)
    for family in sorted(referenced_families - set(recoveries)):
        blockers.append({"code": "RECOVERY_POLICY_MISSING", "subject": family})
    for effect in effects.values():
        capability = capabilities[effect["provider_capability"]]
        if capability["status"] not in {"AVAILABLE", "RESTRICTED"}:
            blockers.append({"code": "PROVIDER_CAPABILITY_NOT_READY", "subject": effect["provider_capability"]})
        bound_steps = [step for step in steps.values() if step.get("effect_id") == effect["id"]]
        if not bound_steps:
            blockers.append({"code": "EFFECT_NOT_BOUND_TO_PLAN_STEP", "subject": effect["id"]})
        semantic_steps = []
        for step in bound_steps:
            fields = sorted(set(step["reads"] + step["writes"]))
            semantic_steps.append({
                "kind": step["kind"], "after": step["after"],
                "assumptions": {key: assumptions[key] for key in sorted(step["requires_assumptions"])},
                "capabilities": {
                    key: {
                        "id": key, "constraints": capabilities[key]["constraints"],
                        "required_constraints": step["capability_constraints"].get(key) or {},
                    }
                    for key in sorted(step["requires_capabilities"])
                },
                "reads": step["reads"], "writes": step["writes"],
                "authorities": {key: authorities[key] for key in fields if key in authorities},
                "failure_families": {
                    key: recoveries[key] for key in sorted(step["failure_families"])
                    if key in recoveries
                },
            })
        provider_contract = {
            "id": capability["id"], "source": capability["source"],
            "constraints": capability["constraints"],
        }
        effect_semantics = {
            "id": effect["id"], "idempotency": effect["idempotency"],
            "idempotency_key": effect["idempotency_key"],
            "no_effect_predicate": effect["no_effect_predicate"],
            "provider_capability": provider_contract,
            "deadline_seconds": effect["deadline_seconds"],
            "effect_input_sha256": effect["effect_input_sha256"],
            "adapter_contract_sha256": effect["adapter_contract_sha256"],
            "steps": sorted(semantic_steps, key=sha256_json),
        }
        effect["effect_contract_hash"] = sha256_json(effect_semantics)
    execution_class = str(request.get("execution_class") or "LOCAL_REVERSIBLE").upper()
    has_external_work = bool(effects) or any(step["kind"] == "EXTERNAL_EFFECT" for step in steps.values())
    if has_external_work and execution_class != "EXTERNAL_EFFECT":
        blockers.append({"code": "EXECUTION_CLASS_UNDERDECLARED", "subject": plan_id})
    if execution_class == "EXTERNAL_EFFECT" and (cost_class != "EXTERNAL" or not effects or not any(step["kind"] == "EXTERNAL_EFFECT" for step in steps.values())):
        blockers.append({"code": "EXTERNAL_EXECUTION_MODEL_INCOMPLETE", "subject": plan_id})
    if execution_class == "LOCAL_HIGH_COST" and cost_class not in {"HIGH", "EXTERNAL"}:
        blockers.append({"code": "HIGH_COST_TASK_UNDERDECLARED", "subject": plan_id})
    if execution_class == "LOCAL_REVERSIBLE" and cost_class in {"HIGH", "EXTERNAL"}:
        blockers.append({"code": "LOCAL_REVERSIBLE_COST_UNDERDECLARED", "subject": plan_id})

    normalized = {
        "schema": SPEC_SCHEMA, "plan_id": plan_id, "cost_class": cost_class,
        "assumptions": assumptions, "capabilities": capabilities, "authorities": authorities,
        "commands": commands, "claims": claims, "effects": effects, "steps": steps,
        "recovery": recoveries,
        "blocker_policy": {
            "same_family_replan_at": 2,
            "distinct_family_replan_at": 2,
            "critical_assumption_failure": "REPLAN_REQUIRED",
        },
    }
    envelope_hash = sha256_json(normalized)
    return {
        "schema": RUNTIME_SCHEMA,
        "mode": "ENHANCED",
        "plan_validity": "VALID" if not blockers else "ADMISSION_BLOCKED",
        "plan_revision": int(plan_revision),
        "envelope_hash": envelope_hash,
        "envelope": normalized,
        "admission_blockers": blockers,
        "blockers": [],
        "effect_ledger": {},
        "effect_history": [],
        "reviews": [],
        "claim_results": {},
        "envelope_history": [],
        "enhanced_guarantees": True,
    }


def validate_runtime_state(runtime: Mapping[str, Any]) -> None:
    if not isinstance(runtime, Mapping) or runtime.get("schema") != RUNTIME_SCHEMA:
        raise KernelError("canonical execution runtime is invalid")
    mode = runtime.get("mode")
    if mode not in {"LEGACY_LOCAL", "ENHANCED"}:
        raise KernelError("canonical execution runtime has invalid mode")
    if runtime.get("plan_validity") not in {"VALID", "ADMISSION_BLOCKED", "REPLAN_REQUIRED", "STOP_REQUIRED"}:
        raise KernelError("canonical execution runtime has invalid plan validity")
    if mode == "ENHANCED":
        envelope = runtime.get("envelope")
        if not isinstance(envelope, Mapping) or sha256_json(envelope) != runtime.get("envelope_hash"):
            raise KernelError("canonical execution envelope hash is invalid")
        if runtime.get("admission_blockers") and runtime.get("plan_validity") == "VALID":
            raise KernelError("blocked execution envelope cannot be marked valid")
    ledger = runtime.get("effect_ledger") or {}
    if not isinstance(ledger, Mapping) or len(ledger) > 64:
        raise KernelError("canonical effect ledger is invalid or exceeds its bound")
    for effect_id, record in ledger.items():
        if not ID.fullmatch(str(effect_id)) or not isinstance(record, Mapping) or record.get("state") not in EFFECT_STATES:
            raise KernelError("canonical effect ledger contains an invalid record")
        action_id = record.get("action_id")
        action = ((runtime.get("envelope") or {}).get("effects") or {}).get(action_id)
        if mode != "ENHANCED" or not isinstance(action, Mapping):
            raise KernelError("canonical effect ledger references an unknown admitted action")
        if record.get("idempotency") != action.get("idempotency") or int(record.get("attempt", 0)) < 1:
            raise KernelError("canonical effect ledger identity or attempt is invalid")
        bound_hash = record.get("effect_contract_hash")
        if bound_hash is not None and (
            bound_hash != action.get("effect_contract_hash")
            or record.get("effect_input_sha256") != action.get("effect_input_sha256")
            or record.get("adapter_contract_sha256") != action.get("adapter_contract_sha256")
            or record.get("idempotency_key") != action.get("idempotency_key")
            or record.get("no_effect_predicate") != action.get("no_effect_predicate")
        ):
            raise KernelError("canonical active effect is not bound to the exact admitted semantic contract")
        state = record.get("state")
        if state in {"DISPATCH_UNCONFIRMED", "DISPATCH_CONFIRMED", "OUTPUT_CONFIRMED", "COMMITTED"} and not record.get("dispatch_boundary_at"):
            raise KernelError("canonical dispatched effect lacks a durable boundary marker")
        if state in {"DISPATCH_CONFIRMED", "OUTPUT_CONFIRMED", "COMMITTED"} and not record.get("provider_reference"):
            raise KernelError("canonical confirmed effect lacks a provider reference")
        if state in {"OUTPUT_CONFIRMED", "COMMITTED"} and (
            not record.get("result_reference") or not re.fullmatch(r"[0-9a-f]{64}", str(record.get("result_sha256") or ""))
        ):
            raise KernelError("canonical output-confirmed effect lacks content-bound output")
        if state == "COMMITTED" and not record.get("local_commit_reference"):
            raise KernelError("canonical committed effect lacks local persistence proof")
        if state == "RESOLVED_NO_EFFECT" and (record.get("reconciliation") or {}).get("outcome") not in {"NO_EFFECT", "NO_DISPATCH_TIMEOUT", "PRE_PROVIDER_FAILURE"}:
            raise KernelError("canonical no-effect resolution lacks positive reconciliation evidence")
    history = runtime.get("effect_history") or []
    if not isinstance(history, list) or len(history) > 128 or any(
        not isinstance(row, Mapping)
        or row.get("state") not in TERMINAL_EFFECT_STATES
        or not ID.fullmatch(str(row.get("effect_id") or ""))
        for row in history
    ):
        raise KernelError("canonical historical effect lineage is invalid or exceeds its bound")
    if not isinstance(runtime.get("blockers") or [], list) or len(runtime.get("blockers") or []) > 32:
        raise KernelError("canonical blocker history exceeds its bound")
    if not isinstance(runtime.get("reviews") or [], list) or len(runtime.get("reviews") or []) > 64:
        raise KernelError("canonical review history exceeds its bound")


def reset_for_lifecycle_revision(runtime: Mapping[str, Any]) -> dict[str, Any]:
    """Start a product revision with fresh dynamic execution state.

    The prior generation remains the immutable source for proportional claim
    reuse.  Effects, blockers and reviews are revision-scoped and must never
    satisfy a later revision merely because the plan envelope is unchanged.
    """
    result = deepcopy(dict(runtime))
    if result.get("mode") != "ENHANCED":
        return result
    if result.get("plan_validity") != "VALID":
        raise KernelError("a new lifecycle revision cannot inherit an invalid execution plan")
    result["blockers"] = []
    result["effect_ledger"] = {}
    result["reviews"] = []
    result["claim_results"] = {}
    result.pop("last_assurance_plan", None)
    validate_runtime_state(result)
    return result


def assert_plan_valid(state: Mapping[str, Any], action: str) -> None:
    runtime = state.get("execution")
    if not runtime:
        return
    validate_runtime_state(runtime)
    if runtime.get("plan_validity") != "VALID":
        raise KernelError(f"{action} is blocked because execution plan validity is {runtime.get('plan_validity')}")


def assert_effects_resolved(state: Mapping[str, Any]) -> None:
    runtime = state.get("execution") or {}
    if runtime.get("mode") != "ENHANCED":
        return
    envelope = runtime["envelope"]
    ledger = runtime.get("effect_ledger") or {}
    unresolved = [effect_id for effect_id, row in ledger.items() if row.get("state") not in TERMINAL_EFFECT_STATES]
    if unresolved:
        raise KernelError(f"external effects require reconciliation before assurance: {sorted(unresolved)}")
    for action_id, action in envelope["effects"].items():
        if action.get("required") and not any(
            row.get("action_id") == action_id
            and row.get("state") == "COMMITTED"
            and row.get("effect_contract_hash") == action.get("effect_contract_hash")
            for row in ledger.values()
        ):
            raise KernelError(f"required external effect is not durably committed: {action_id}")


def report_blocker(state: Mapping[str, Any], *, family: str, evidence: str, assumption_id: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    assert_plan_valid(state, "report-blocker")
    family = _id(family, "blocker family")
    evidence = _text(evidence, "blocker evidence")
    result = deepcopy(dict(state))
    runtime = result.get("execution") or {}
    if runtime.get("mode") != "ENHANCED":
        raise KernelError("blocker pattern semantics require an enhanced execution envelope")
    recovery = runtime["envelope"]["recovery"].get(family)
    if not recovery:
        raise KernelError(f"blocker family is not represented in the recovery model: {family}")
    assumption = str(assumption_id or "").strip() or None
    if assumption and assumption not in runtime["envelope"]["assumptions"]:
        raise KernelError(f"blocker references unknown plan assumption: {assumption}")
    prior = [row for row in runtime["blockers"] if row.get("family") == family]
    occurrence = len(prior) + 1
    distinct = len({row.get("family") for row in runtime["blockers"]} | {family})
    decision = "BOUNDED_CORRECTION_ALLOWED"
    if recovery["evidence_required"] and not evidence:
        raise KernelError("blocker recovery requires evidence")
    if assumption and runtime["envelope"]["assumptions"][assumption]["critical"]:
        decision = "REPLAN_REQUIRED"
    elif recovery["disposition"] in {"REPLAN", "STOP"}:
        decision = "REPLAN_REQUIRED" if recovery["disposition"] == "REPLAN" else "STOP_REQUIRED"
    elif occurrence > recovery["max_bounded_occurrences"] or occurrence >= 2 or distinct >= 2:
        decision = "REPLAN_REQUIRED"
    elif recovery["disposition"] == "RECONCILE":
        decision = "RECONCILIATION_REQUIRED"
    row = {
        "family": family, "occurrence": occurrence, "evidence": evidence,
        "assumption_id": assumption, "decision": decision, "recorded_at": _now(),
    }
    runtime["blockers"] = [*runtime["blockers"], row]
    if decision in {"REPLAN_REQUIRED", "STOP_REQUIRED"}:
        runtime["plan_validity"] = decision
        result["lifecycle_ready"] = False
    result["execution"] = runtime
    result["next_action"] = {
        "BOUNDED_CORRECTION_ALLOWED": "perform the one bounded correction defined by the execution envelope",
        "RECONCILIATION_REQUIRED": "reconcile the affected external effect before any retry or continuation",
        "REPLAN_REQUIRED": "replace the invalid plan before further implementation or dispatch",
        "STOP_REQUIRED": "stop; the execution envelope forbids autonomous continuation",
    }[decision]
    validate_runtime_state(runtime)
    return result, {"kind": "BLOCKER_REPORTED", **row}


def apply_replan(state: Mapping[str, Any], runtime: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if state.get("phase") != "ACTIVE":
        raise KernelError("replan is allowed only before a product commit or assurance; use a new revision afterward")
    prior = state.get("execution") or {}
    if prior.get("mode") != "ENHANCED" or prior.get("plan_validity") not in {"REPLAN_REQUIRED", "STOP_REQUIRED"}:
        raise KernelError("replan requires an invalid enhanced execution plan")
    if any(row.get("state") not in TERMINAL_EFFECT_STATES for row in (prior.get("effect_ledger") or {}).values()):
        raise KernelError("replan cannot bypass an unresolved external effect")
    if runtime.get("plan_validity") != "VALID":
        raise KernelError("replacement execution plan did not pass admission")
    result = deepcopy(dict(state))
    replacement = deepcopy(dict(runtime))
    replacement["plan_revision"] = int(prior.get("plan_revision", 1)) + 1
    replacement["envelope_history"] = [
        *(prior.get("envelope_history") or []),
        {"plan_revision": prior.get("plan_revision"), "envelope_hash": prior.get("envelope_hash"), "blockers": prior.get("blockers") or []},
    ][-16:]
    active: dict[str, Any] = {}
    retired: list[dict[str, Any]] = []
    carried: list[str] = []
    for effect_id, source_record in (prior.get("effect_ledger") or {}).items():
        record = deepcopy(dict(source_record))
        action = replacement["envelope"]["effects"].get(record.get("action_id"))
        compatible = bool(
            action
            and record.get("effect_contract_hash")
            and record.get("effect_contract_hash") == action.get("effect_contract_hash")
            and record.get("effect_input_sha256") == action.get("effect_input_sha256")
            and record.get("adapter_contract_sha256") == action.get("adapter_contract_sha256")
        )
        if compatible:
            record["carry_forward"] = [
                *(record.get("carry_forward") or []),
                {
                    "from_envelope_hash": prior.get("envelope_hash"),
                    "from_plan_revision": prior.get("plan_revision"),
                    "to_envelope_hash": replacement.get("envelope_hash"),
                    "to_plan_revision": replacement["plan_revision"],
                    "basis": record.get("effect_contract_hash"),
                    "at": _now(),
                },
            ][-16:]
            active[effect_id] = record
            carried.append(effect_id)
        else:
            record.update({
                "retired_from_envelope_hash": prior.get("envelope_hash"),
                "retired_from_plan_revision": prior.get("plan_revision"),
                "retired_at_replan": _now(),
                "retired_reason": "EFFECT_CONTRACT_NOT_IDENTICAL",
            })
            retired.append(record)
    replacement["effect_ledger"] = active
    replacement["effect_history"] = [
        *(deepcopy(prior.get("effect_history") or [])), *retired,
    ][-128:]
    replacement["reviews"] = deepcopy(prior.get("reviews") or [])
    result["execution"] = replacement
    result["lifecycle_ready"] = True
    result["next_action"] = "execute the newly admitted plan inside its compiled envelope"
    validate_runtime_state(replacement)
    return result, {
        "kind": "PLAN_REPLACED", "from_envelope_hash": prior.get("envelope_hash"),
        "to_envelope_hash": replacement.get("envelope_hash"), "plan_revision": replacement["plan_revision"],
        "effects_carried": sorted(carried),
        "effects_retired": sorted(row["effect_id"] for row in retired),
    }


def prepare_effect(state: Mapping[str, Any], *, action_id: str, effect_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    assert_plan_valid(state, "effect prepare")
    action_id = _id(action_id, "effect action_id")
    effect_id = _id(effect_id, "effect_id")
    result = deepcopy(dict(state))
    runtime = result.get("execution") or {}
    if runtime.get("mode") != "ENHANCED" or action_id not in runtime["envelope"]["effects"]:
        raise KernelError(f"effect action is not admitted by the execution envelope: {action_id}")
    prior_for_action = next(
        (row for key, row in runtime["effect_ledger"].items() if key != effect_id and row.get("action_id") == action_id),
        None,
    )
    if prior_for_action:
        raise KernelError("an admitted action already has a stable effect identity; resume or reconcile that effect instead")
    if effect_id in runtime["effect_ledger"]:
        prior = runtime["effect_ledger"][effect_id]
        if prior.get("action_id") == action_id:
            return result, {"kind": "EFFECT_INTENT_ALREADY_RECORDED", "effect_id": effect_id}
        raise KernelError("effect_id is already bound to another action")
    if any(row.get("effect_id") == effect_id for row in runtime.get("effect_history") or []):
        raise KernelError("effect_id is immutable historical lineage; use a fresh effect identity")
    action = runtime["envelope"]["effects"][action_id]
    record = {
        "effect_id": effect_id, "action_id": action_id, "state": "INTENT_RECORDED",
        "attempt": 1, "idempotency": action["idempotency"],
        "idempotency_key": action.get("idempotency_key"), "prepared_at": _now(),
        "no_effect_predicate": action.get("no_effect_predicate"),
        "effect_contract_hash": action["effect_contract_hash"],
        "effect_input_sha256": action["effect_input_sha256"],
        "adapter_contract_sha256": action["adapter_contract_sha256"],
        "originating_envelope_hash": runtime.get("envelope_hash"),
        "originating_plan_revision": runtime.get("plan_revision"),
        "deadline_seconds": action["deadline_seconds"], "deadline_at": _deadline(action["deadline_seconds"]),
        "provider_reference": None,
        "result_reference": None, "result_sha256": None, "reconciliation": None,
    }
    runtime["effect_ledger"][effect_id] = record
    result["execution"] = runtime
    result["next_action"] = "persist the dispatch-boundary marker immediately before the one provider call"
    return result, {"kind": "EFFECT_INTENT_RECORDED", "effect_id": effect_id, "action_id": action_id}


def transition_effect(state: Mapping[str, Any], *, effect_id: str, transition: str, reference: str | None = None, sha256: str | None = None, predicate: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    effect_id = _id(effect_id, "effect_id")
    transition = str(transition).upper().strip()
    if transition in {"DISPATCH", "AUTHORIZE_RETRY"}:
        assert_plan_valid(state, f"effect {transition}")
    elif state.get("execution"):
        validate_runtime_state(state["execution"])
    result = deepcopy(dict(state))
    runtime = result.get("execution") or {}
    ledger = runtime.get("effect_ledger") or {}
    if effect_id not in ledger:
        raise KernelError(f"effect intent is not recorded: {effect_id}")
    record = ledger[effect_id]
    action = runtime["envelope"]["effects"][record["action_id"]]
    if transition in {"DISPATCH", "AUTHORIZE_RETRY"} and record.get("effect_contract_hash") != action.get("effect_contract_hash"):
        raise KernelError("unbound or semantically stale effect cannot be dispatched or retried; reconcile existing provider uncertainty first")
    current = record["state"]
    event: dict[str, Any] = {"kind": "EFFECT_TRANSITION", "effect_id": effect_id, "from": current, "transition": transition}
    ref = str(reference or "").strip() or None
    proof = str(predicate or "").strip() or None
    digest = str(sha256 or "").strip().lower() or None
    if transition == "DISPATCH":
        if current not in {"INTENT_RECORDED", "RETRY_AUTHORIZED"}:
            raise KernelError("effect dispatch requires durable intent or retry authority")
        record["state"] = "DISPATCH_UNCONFIRMED"
        record["dispatch_boundary_at"] = _now()
        record["deadline_at_offset_seconds"] = action["deadline_seconds"]
        result["next_action"] = "call the provider once; any crash now requires reconciliation, never inferred no-dispatch"
    elif transition == "ACK":
        if current != "DISPATCH_UNCONFIRMED" or not ref:
            raise KernelError("effect acknowledgement requires an uncertain dispatch and provider reference")
        record["state"] = "DISPATCH_CONFIRMED"
        record["provider_reference"] = ref
        record["acknowledged_at"] = _now()
        result["next_action"] = "observe provider output without changing effect identity"
    elif transition == "RESULT":
        if current not in {"DISPATCH_UNCONFIRMED", "DISPATCH_CONFIRMED"} or not ref or not digest or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise KernelError("effect result requires a dispatched effect, durable result reference and SHA-256")
        record["state"] = "OUTPUT_CONFIRMED"
        record["result_reference"] = ref
        record["result_sha256"] = digest
        record["result_recorded_at"] = _now()
        result["next_action"] = "persist canonical local provenance, then commit the effect record"
    elif transition == "COMMIT":
        if current != "OUTPUT_CONFIRMED" or not ref:
            raise KernelError("effect commit requires confirmed output and a durable local persistence reference")
        record["state"] = "COMMITTED"
        record["local_commit_reference"] = ref
        record["committed_at"] = _now()
        result["next_action"] = "continue within the admitted plan; the effect is durably reconciled"
    elif transition == "RECONCILE_NO_EFFECT":
        expected = action.get("no_effect_predicate")
        if current not in {"DISPATCH_UNCONFIRMED", "DISPATCH_CONFIRMED"} or not ref or not expected or proof != expected:
            raise KernelError("no-effect reconciliation requires the action's canonical predicate and positive evidence")
        record["state"] = "RESOLVED_NO_EFFECT"
        record["reconciliation"] = {"outcome": "NO_EFFECT", "predicate": proof, "evidence": ref, "at": _now()}
        result["next_action"] = "retry may be authorized as a new attempt because positive no-effect proof exists"
    elif transition == "RECONCILE_CONFIRMED":
        if current != "DISPATCH_UNCONFIRMED" or not ref:
            raise KernelError("confirmed reconciliation requires an uncertain dispatch and provider evidence")
        record["state"] = "DISPATCH_CONFIRMED"
        record["provider_reference"] = ref
        record["reconciliation"] = {"outcome": "CONFIRMED", "evidence": ref, "at": _now()}
        result["next_action"] = "observe or recover the already-confirmed provider output; do not redispatch"
    elif transition in {"TIMEOUT_NO_DISPATCH", "FAIL_BEFORE_DISPATCH"}:
        if current != "INTENT_RECORDED" or not ref:
            raise KernelError("pre-provider resolution requires durable intent, no dispatch marker and evidence")
        if transition == "TIMEOUT_NO_DISPATCH":
            deadline = datetime.fromisoformat(str(record["deadline_at"]).replace("Z", "+00:00"))
            if datetime.now(timezone.utc) < deadline:
                raise KernelError("pre-provider deadline has not expired")
        outcome = "NO_DISPATCH_TIMEOUT" if transition == "TIMEOUT_NO_DISPATCH" else "PRE_PROVIDER_FAILURE"
        record["state"] = "RESOLVED_NO_EFFECT"
        record["reconciliation"] = {"outcome": outcome, "evidence": ref, "at": _now()}
        result["next_action"] = "the provider boundary was not crossed; authorize a retry on this same stable effect identity only if the plan still permits it"
    elif transition == "AUTHORIZE_RETRY":
        safe_idempotent_retry = current == "DISPATCH_UNCONFIRMED" and action["idempotency"] == "IDEMPOTENT_WITH_KEY" and bool(action.get("idempotency_key"))
        safe_no_effect_retry = current == "RESOLVED_NO_EFFECT"
        if not (safe_idempotent_retry or safe_no_effect_retry):
            raise KernelError("effect retry requires provider-enforced idempotency with the same key or positive no-effect reconciliation")
        record["state"] = "RETRY_AUTHORIZED"
        record["attempt"] = int(record.get("attempt", 1)) + 1
        record["retry_basis"] = "SAME_IDEMPOTENCY_KEY" if safe_idempotent_retry else "POSITIVE_NO_EFFECT_PROOF"
        record["retry_authorized_at"] = _now()
        result["next_action"] = "persist a new dispatch-boundary marker before the single authorized retry"
    else:
        raise KernelError(f"unsupported effect transition: {transition}")
    event.update({"to": record["state"], "reference": ref, "sha256": digest, "predicate": proof})
    ledger[effect_id] = record
    runtime["effect_ledger"] = ledger
    result["execution"] = runtime
    validate_runtime_state(runtime)
    return result, event


def record_review(
    state: Mapping[str, Any], *, review_id: str, asset_id: str,
    content_sha256: str, outcome: str, evidence: str,
    supersedes: str | None = None, derived_from_review: str | None = None,
    transformation_reference: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    assert_plan_valid(state, "review")
    review_id = _id(review_id, "review_id")
    asset_id = _id(asset_id, "asset_id")
    digest = str(content_sha256).lower().strip()
    outcome = str(outcome).upper().strip()
    evidence = _text(evidence, "review evidence")
    if not re.fullmatch(r"[0-9a-f]{64}", digest) or outcome not in {"PASS", "SALVAGEABLE", "REJECT"}:
        raise KernelError("review requires a content SHA-256 and PASS, SALVAGEABLE or REJECT outcome")
    result = deepcopy(dict(state))
    runtime = result.get("execution") or {}
    reviews = runtime.get("reviews") or []
    if any(row.get("review_id") == review_id for row in reviews):
        raise KernelError("review_id is already used")
    prior = next((row for row in reviews if row.get("review_id") == supersedes), None) if supersedes else None
    source = next((row for row in reviews if row.get("review_id") == derived_from_review), None) if derived_from_review else None
    transform = str(transformation_reference or "").strip() or None
    if supersedes and derived_from_review:
        raise KernelError("review can supersede the same bytes or derive salvaged bytes, never both")
    if supersedes and not prior:
        raise KernelError("review supersession must reference an existing immutable review")
    if prior and (prior.get("asset_id") != asset_id or prior.get("content_sha256") != digest):
        raise KernelError("review supersession must bind the same asset identity and content hash")
    if derived_from_review and not source:
        raise KernelError("salvage lineage must reference an existing immutable review")
    if source and (
        source.get("outcome") != "SALVAGEABLE" or source.get("asset_id") == asset_id
        or source.get("content_sha256") == digest or not transform
    ):
        raise KernelError("salvage lineage requires SALVAGEABLE source review, new asset bytes/identity and transformation evidence")
    same_asset = next((row for row in reviews if row.get("asset_id") == asset_id), None)
    if same_asset and same_asset.get("content_sha256") != digest:
        raise KernelError("one asset identity cannot name different content bytes")
    epoch = 1 + max([int(row.get("epoch", 0)) for row in reviews if row.get("asset_id") == asset_id] or [0])
    row = {
        "review_id": review_id, "asset_id": asset_id, "content_sha256": digest,
        "epoch": epoch, "outcome": outcome, "evidence": evidence,
        "supersedes": supersedes, "derived_from_review": derived_from_review,
        "transformation_reference": transform, "recorded_at": _now(),
    }
    runtime["reviews"] = [*reviews, row]
    result["execution"] = runtime
    result["next_action"] = {
        "PASS": "use this exact reviewed asset only where the plan permits",
        "SALVAGEABLE": "perform only the admitted deterministic salvage, then create a fresh review epoch",
        "REJECT": "do not use this asset; follow the admitted recovery or replan policy",
    }[outcome]
    return result, {"kind": "REVIEW_RECORDED", **row}


def _run_argv(root: Path, command: Mapping[str, Any], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    argv = list(command["argv"])
    proc = subprocess.run(argv, cwd=root, shell=False, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    return {
        "command_id": command["id"], "argv": argv, "command": json.dumps(argv, ensure_ascii=False),
        "command_provenance": command["provenance"], "returncode": proc.returncode,
        "duration_ms": int((time.monotonic() - started) * 1000),
        "stdout_sha256": hashlib.sha256(stdout.encode("utf-8", "replace")).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.encode("utf-8", "replace")).hexdigest(),
        "stdout_excerpt": stdout[-16000:], "stderr_excerpt": stderr[-16000:],
    }


def claim_plan(root: Path, state: Mapping[str, Any], *, target_sha: str, previous_state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    runtime = state.get("execution") or {}
    if runtime.get("mode") != "ENHANCED":
        return {"mode": "LEGACY", "claims": []}
    from .git_adapter import dependency_fingerprint

    envelope = runtime["envelope"]
    prior_results = ((previous_state or {}).get("execution") or {}).get("claim_results") or {}
    rows: list[dict[str, Any]] = []
    for claim_id in sorted(envelope["claims"]):
        claim = envelope["claims"][claim_id]
        digest = dependency_fingerprint(root, target_sha, claim["dependencies"])
        prior = prior_results.get(claim_id) or {}
        prior_evidence = prior.get("evidence") or {}
        prior_evidence_path = root / str(prior_evidence.get("path") or "<missing>")
        prior_evidence_intact = bool(
            prior_evidence.get("path")
            and prior_evidence.get("sha256")
            and prior_evidence_path.is_file()
            and hashlib.sha256(prior_evidence_path.read_bytes()).hexdigest() == prior_evidence.get("sha256")
        )
        reusable = (
            claim["mode"] == "AFFECTED"
            and prior.get("status") == "PASS"
            and prior.get("semantic_hash") == claim["semantic_hash"]
            and prior.get("dependency_digest") == digest
            and prior_evidence_intact
        )
        rows.append({
            "claim_id": claim_id, "role": claim["role"], "mode": claim["mode"],
            "semantic_hash": claim["semantic_hash"], "dependency_digest": digest,
            "command_id": claim["command_id"], "disposition": "REUSE" if reusable else "EXECUTE",
            "previous_evidence": deepcopy(prior_evidence) if reusable else None,
        })
    return {
        "mode": "DEPENDENCY_AWARE", "target_sha": target_sha, "claims": rows,
        "execute": [row["claim_id"] for row in rows if row["disposition"] == "EXECUTE"],
        "reuse": [row["claim_id"] for row in rows if row["disposition"] == "REUSE"],
    }


def execute_claim_plan(root: Path, state: Mapping[str, Any], plan: Mapping[str, Any], *, timeout: int) -> list[dict[str, Any]]:
    runtime = state["execution"]
    envelope = runtime["envelope"]
    results: list[dict[str, Any]] = []
    for row in plan["claims"]:
        if row["disposition"] == "REUSE":
            results.append({
                "claim_id": row["claim_id"], "role": row["role"], "returncode": 0,
                "reused": True, "reused_evidence": deepcopy(row["previous_evidence"]),
                "command_id": row["command_id"], "command": f"REUSED:{row['command_id']}",
                "dependency_digest": row["dependency_digest"], "semantic_hash": row["semantic_hash"],
            })
            continue
        result = _run_argv(root, envelope["commands"][row["command_id"]], timeout)
        result.update({
            "claim_id": row["claim_id"], "role": row["role"], "reused": False,
            "dependency_digest": row["dependency_digest"], "semantic_hash": row["semantic_hash"],
        })
        results.append(result)
    return results


def attach_claim_results(state: Mapping[str, Any], plan: Mapping[str, Any], results: Sequence[Mapping[str, Any]], *, evidence: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(state))
    runtime = result.get("execution") or {}
    bound: dict[str, dict[str, Any]] = {}
    for row in results:
        evidence_ref = deepcopy(row.get("reused_evidence")) if row.get("reused") else {
            "path": evidence.get("path"), "sha256": evidence.get("sha256"),
        }
        bound[str(row["claim_id"])] = {
            "status": "PASS", "semantic_hash": row["semantic_hash"],
            "dependency_digest": row["dependency_digest"],
            "evidence": evidence_ref,
            "last_assured_target": plan.get("target_sha"), "reused": bool(row.get("reused")),
        }
    runtime["claim_results"] = bound
    runtime["last_assurance_plan"] = {
        "target_sha": plan.get("target_sha"), "executed": list(plan.get("execute") or []),
        "reused": list(plan.get("reuse") or []), "evidence": {"path": evidence.get("path"), "sha256": evidence.get("sha256")},
    }
    result["execution"] = runtime
    validate_runtime_state(runtime)
    return result
