#!/usr/bin/env python3
"""Validate provider-neutral authority, retry, recovery and schema contracts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping


VERSION = "1.0.0"
SCHEMA = "buildos.side-effect-contract.v1"
ID = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
RETRY_POLICIES = {"SAFE_IDEMPOTENT", "POSITIVE_NO_EFFECT_PROOF_ONLY", "NEVER"}
EFFECT_STATES = {"NOT_POSSIBLE", "POSSIBLE", "CONFIRMED"}
COMPATIBILITY = {"CURRENT_SCHEMA", "VERIFIED_LEGACY_EQUIVALENT", "UNMIGRATABLE"}
TOP_LEVEL_FIELDS = {
    "schema", "system_id", "state_dimensions", "canonical_predicates",
    "semantic_consumers", "dangerous_actions", "crash_recovery", "schema_compatibility",
}


class ContractError(ValueError):
    pass


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} is required")
    return value.strip()


def _id(value: Any, label: str) -> str:
    result = _text(value, label)
    if not ID.fullmatch(result):
        raise ContractError(f"{label} must be a portable lowercase identifier")
    return result


def _objects(value: Any, label: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or not value or any(not isinstance(item, Mapping) for item in value):
        raise ContractError(f"{label} must be a non-empty object list")
    return value


def validate_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or value.get("schema") != SCHEMA:
        raise ContractError(f"contract schema must be {SCHEMA}")
    if set(value) != TOP_LEVEL_FIELDS:
        raise ContractError(f"contract fields must be exactly {sorted(TOP_LEVEL_FIELDS)}")
    system_id = _id(value.get("system_id"), "system_id")

    dimension_ids: set[str] = set()
    for item in _objects(value.get("state_dimensions"), "state_dimensions"):
        identifier = _id(item.get("id"), "state dimension id")
        states = item.get("states")
        if identifier in dimension_ids:
            raise ContractError("state dimension ids must be unique")
        if not isinstance(states, list) or len(states) < 2 or any(not isinstance(state, str) or not state.strip() for state in states):
            raise ContractError(f"state dimension {identifier} requires at least two named states")
        if len(set(states)) != len(states):
            raise ContractError(f"state dimension {identifier} states must be unique")
        dimension_ids.add(identifier)

    predicate_ids: set[str] = set()
    for item in _objects(value.get("canonical_predicates"), "canonical_predicates"):
        identifier = _id(item.get("id"), "canonical predicate id")
        if set(item) != {"id", "semantics", "verifier"}:
            raise ContractError(f"canonical predicate {identifier} has an invalid shape")
        if identifier in predicate_ids:
            raise ContractError("canonical predicate ids must be unique")
        _text(item.get("semantics"), f"canonical predicate {identifier}.semantics")
        _text(item.get("verifier"), f"canonical predicate {identifier}.verifier")
        predicate_ids.add(identifier)

    consumer_ids: set[str] = set()
    consumed_predicates: set[str] = set()
    for item in _objects(value.get("semantic_consumers"), "semantic_consumers"):
        identifier = _id(item.get("id"), "semantic consumer id")
        if set(item) != {"id", "predicate_id", "purpose"}:
            raise ContractError(f"semantic consumer {identifier} has an invalid shape")
        predicate = _id(item.get("predicate_id"), f"semantic consumer {identifier}.predicate_id")
        if identifier in consumer_ids:
            raise ContractError("semantic consumer ids must be unique")
        if predicate not in predicate_ids:
            raise ContractError(f"semantic consumer {identifier} references unknown canonical predicate: {predicate}")
        _text(item.get("purpose"), f"semantic consumer {identifier}.purpose")
        consumer_ids.add(identifier)
        consumed_predicates.add(predicate)

    action_ids: set[str] = set()
    action_retry: dict[str, str] = {}
    for item in _objects(value.get("dangerous_actions"), "dangerous_actions"):
        identifier = _id(item.get("id"), "dangerous action id")
        if set(item) != {
            "id", "effect", "idempotency", "authority_predicate", "required_evidence",
            "unknown_is_barrier", "retry_policy", "positive_no_effect_proof",
        }:
            raise ContractError(f"dangerous action {identifier} has an invalid shape")
        if identifier in action_ids:
            raise ContractError("dangerous action ids must be unique")
        _text(item.get("effect"), f"dangerous action {identifier}.effect")
        authority_predicate = _id(item.get("authority_predicate"), f"dangerous action {identifier}.authority_predicate")
        if authority_predicate not in predicate_ids:
            raise ContractError(f"dangerous action {identifier} references unknown authority predicate: {authority_predicate}")
        evidence = item.get("required_evidence")
        if not isinstance(evidence, list) or not evidence or any(not isinstance(entry, str) or not entry.strip() for entry in evidence):
            raise ContractError(f"dangerous action {identifier} requires explicit evidence")
        if item.get("unknown_is_barrier") is not True:
            raise ContractError(f"dangerous action {identifier} must make unknown a queue barrier")
        retry = str(item.get("retry_policy") or "")
        if retry not in RETRY_POLICIES:
            raise ContractError(f"dangerous action {identifier} has an invalid retry policy")
        idempotency = str(item.get("idempotency") or "")
        if idempotency not in {"IDEMPOTENT", "NON_IDEMPOTENT"}:
            raise ContractError(f"dangerous action {identifier} must declare idempotency")
        if idempotency == "NON_IDEMPOTENT" and retry == "SAFE_IDEMPOTENT":
            raise ContractError(f"non-idempotent action {identifier} cannot use SAFE_IDEMPOTENT retry")
        proof = str(item.get("positive_no_effect_proof") or "").strip()
        if retry == "POSITIVE_NO_EFFECT_PROOF_ONLY" and not proof:
            raise ContractError(f"dangerous action {identifier} requires positive_no_effect_proof")
        if proof:
            proof = _id(proof, f"dangerous action {identifier}.positive_no_effect_proof")
            if proof not in predicate_ids:
                raise ContractError(f"dangerous action {identifier} references unknown no-effect predicate: {proof}")
        if retry != "POSITIVE_NO_EFFECT_PROOF_ONLY" and proof:
            raise ContractError(f"dangerous action {identifier} has no-effect proof without matching retry policy")
        action_ids.add(identifier)
        action_retry[identifier] = retry
        if authority_predicate not in consumed_predicates or (proof and proof not in consumed_predicates):
            raise ContractError(f"dangerous action {identifier} predicates must have named semantic consumers")

    covered: set[str] = set()
    for item in _objects(value.get("crash_recovery"), "crash_recovery"):
        action = _id(item.get("action_id"), "crash recovery action_id")
        if set(item) != {"action_id", "crash_point", "effect_state", "retry_authority", "proof_predicate", "recovery_action"}:
            raise ContractError(f"crash recovery for {action} has an invalid shape")
        if action not in action_ids:
            raise ContractError(f"crash recovery references unknown action: {action}")
        _id(item.get("crash_point"), "crash_point")
        effect_state = str(item.get("effect_state") or "")
        retry_authority = str(item.get("retry_authority") or "")
        if effect_state not in EFFECT_STATES:
            raise ContractError(f"crash recovery for {action} has an invalid effect_state")
        if retry_authority not in {"POSITIVE_NO_EFFECT_PROOF", "NEVER", "IDEMPOTENT"}:
            raise ContractError(f"crash recovery for {action} has an invalid retry_authority")
        if effect_state in {"POSSIBLE", "CONFIRMED"} and retry_authority != "NEVER":
            raise ContractError(f"crash recovery for {action} must forbid retry when the effect may exist")
        if effect_state == "NOT_POSSIBLE" and action_retry[action] == "POSITIVE_NO_EFFECT_PROOF_ONLY" and retry_authority != "POSITIVE_NO_EFFECT_PROOF":
            raise ContractError(f"crash recovery for {action} requires positive no-effect proof")
        proof_predicate = str(item.get("proof_predicate") or "").strip()
        action_row = next(row for row in value["dangerous_actions"] if row["id"] == action)
        expected_proof = str(action_row.get("positive_no_effect_proof") or "").strip()
        if retry_authority == "POSITIVE_NO_EFFECT_PROOF" and proof_predicate != expected_proof:
            raise ContractError(f"crash recovery for {action} must use the action's canonical no-effect predicate")
        if retry_authority != "POSITIVE_NO_EFFECT_PROOF" and proof_predicate:
            raise ContractError(f"crash recovery for {action} cannot declare proof without proof-based retry authority")
        _text(item.get("recovery_action"), f"crash recovery for {action}.recovery_action")
        covered.add(action)
    missing_recovery = sorted(action_ids - covered)
    if missing_recovery:
        raise ContractError(f"dangerous actions missing crash recovery coverage: {missing_recovery}")

    compatibility_rows = _objects(value.get("schema_compatibility"), "schema_compatibility")
    current = 0
    schemas: set[str] = set()
    for item in compatibility_rows:
        schema = _text(item.get("schema"), "schema compatibility schema")
        policy = str(item.get("policy") or "")
        if schema in schemas or policy not in COMPATIBILITY:
            raise ContractError("schema compatibility rows must be unique and use a supported policy")
        verifier = str(item.get("verifier") or "").strip()
        if policy == "CURRENT_SCHEMA":
            current += 1
        elif policy == "VERIFIED_LEGACY_EQUIVALENT" and not verifier:
            raise ContractError(f"legacy schema {schema} requires an explicit verifier")
        schemas.add(schema)
    if current != 1:
        raise ContractError("schema compatibility must declare exactly one CURRENT_SCHEMA")

    return {
        "status": "PASS",
        "schema": SCHEMA,
        "system_id": system_id,
        "state_dimensions": len(dimension_ids),
        "canonical_predicates": len(predicate_ids),
        "semantic_consumers": len(consumer_ids),
        "dangerous_actions": len(action_ids),
        "crash_recovery_rows": len(_objects(value.get("crash_recovery"), "crash_recovery")),
        "schema_compatibility_rows": len(compatibility_rows),
        "invariant": "SIDE_EFFECT_AUTHORITY_AND_RECOVERY_FORMALIZED",
    }


def validate_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ContractError(f"side-effect contract is not readable JSON: {path}") from exc
    return validate_contract(value)


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw == ["--version"]:
        print(json.dumps({"component": "side-effect-contract", "version": VERSION, "schema": SCHEMA}, sort_keys=True))
        return 0
    parser = argparse.ArgumentParser(description="Validate a provider-neutral side-effect authority contract")
    parser.add_argument("contract", type=Path)
    args = parser.parse_args(raw)
    try:
        print(json.dumps(validate_file(args.contract.resolve()), sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": type(exc).__name__, "message": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
