#!/usr/bin/env python3
"""Deterministic helpers for the portable Project Lifecycle Kit v1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Any

from side_effect_contract import ContractError, validate_file as validate_side_effect_contract

KIT_VERSION = "1.3.0"
POLICY_FILE = ".buildos-policy.json"
REQUIRED_CATEGORIES = {
    "USER_BEHAVIOR", "ARCHITECTURE_OWNERSHIP_BOUNDARY", "API_CONFIG_SCHEMA",
    "DEVELOPER_WORKFLOW", "FEATURE_PRESET_INVENTORY",
}
CORE_KEYS = {"readme", "project_status", "architecture", "engineering", "roadmap", "changelog"}
MODULES = {"operations", "adr", "security", "migrations", "project_closure", "project_brief"}
PROFILES = {"small-tool", "library", "desktop-app", "production-app", "service", "custom"}
SAFE_RELATIVE = re.compile(r"^(?!/)(?![A-Za-z]:)[^\\/]+(?:[\\/][^\\/]+)*$")


class LifecycleError(RuntimeError):
    pass


def emit(status: str, **payload: Any) -> int:
    print(json.dumps({"status": status, **payload}, sort_keys=True))
    return 0 if status == "PASS" else 2


def run(root: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(["git", *args], cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=45)
    if check and completed.returncode:
        raise LifecycleError(f"git {' '.join(args)} failed: {completed.stderr.strip() or completed.stdout.strip()}")
    return completed.stdout.strip()


def git_root(root: Path) -> Path:
    return Path(run(root, "rev-parse", "--show-toplevel")).resolve()


def read_policy(root: Path) -> tuple[dict[str, Any], Path]:
    path = root / POLICY_FILE
    if not path.is_file():
        raise LifecycleError(f"{POLICY_FILE} is required; use adoption/initialize.ps1 or copy the policy example deliberately")
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise LifecycleError(f"{POLICY_FILE} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise LifecycleError("project policy must be a JSON object")
    return value, path


def safe_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SAFE_RELATIVE.fullmatch(value) or ".." in Path(value).parts:
        raise LifecycleError(f"{label} must be a safe relative path")
    return value.replace("\\", "/")


def required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LifecycleError(f"{label} is required")
    return value.strip()


def accepted_sha(root: Path, accepted_ref: str) -> str:
    try:
        sha = run(root, "rev-parse", "--verify", f"{accepted_ref}^{{commit}}")
    except LifecycleError as exc:
        raise LifecycleError(f"accepted_ref does not resolve to a commit: {accepted_ref}") from exc
    if not re.fullmatch(r"[0-9a-f]{40,64}", sha):
        raise LifecycleError("accepted_ref did not resolve to a commit SHA")
    return sha


def advance_ref(root: Path, accepted_ref: str, expected_old_sha: str, target_sha: str) -> dict[str, str]:
    """Atomically advance the configured selector with an expected-old guard."""
    current = accepted_sha(root, accepted_ref)
    expected = run(root, "rev-parse", "--verify", f"{expected_old_sha}^{{commit}}")
    target = run(root, "rev-parse", "--verify", f"{target_sha}^{{commit}}")
    if current != expected:
        raise LifecycleError(f"accepted_ref moved concurrently: expected {expected}, observed {current}")
    full_ref = run(root, "rev-parse", "--symbolic-full-name", accepted_ref)
    if not full_ref or not full_ref.startswith("refs/"):
        raise LifecycleError("accepted_ref must resolve to a mutable full ref for guarded advancement")
    run(root, "update-ref", full_ref, target, expected)
    return {"accepted_ref": accepted_ref, "old_sha": expected, "new_sha": accepted_sha(root, accepted_ref), "guard": "expected-old-sha"}


def lifecycle(policy: dict[str, Any]) -> dict[str, Any]:
    value = policy.get("project_lifecycle")
    if not isinstance(value, dict):
        raise LifecycleError("project_lifecycle policy object is required")
    return value


def side_effect_contract(root: Path, policy: dict[str, Any]) -> dict[str, Any]:
    """Validate an optional, provider-neutral side-effect contract."""
    value = policy.get("side_effect_contract", {"enabled": False})
    if not isinstance(value, dict) or not isinstance(value.get("enabled"), bool):
        raise LifecycleError("side_effect_contract must declare enabled as a boolean")
    if not value["enabled"]:
        return {"enabled": False, "status": "NOT_CONFIGURED"}
    contract_path = safe_path(value.get("path"), "side_effect_contract.path")
    path = root / contract_path
    if not path.is_file():
        raise LifecycleError(f"enabled side-effect contract is missing: {contract_path}")
    try:
        result = validate_side_effect_contract(path)
    except ContractError as exc:
        raise LifecycleError(f"side-effect contract failed: {exc}") from exc
    return {"enabled": True, "path": contract_path, **result}


def validate_policy(root: Path, policy: dict[str, Any]) -> dict[str, Any]:
    admission = policy.get("execution_admission")
    if admission is not None:
        if not isinstance(admission, dict) or set(admission) != {"enabled", "require_authority_record"}:
            raise LifecycleError("execution_admission must use the exact enabled/require_authority_record shape")
        if not isinstance(admission.get("enabled"), bool) or not isinstance(admission.get("require_authority_record"), bool):
            raise LifecycleError("execution_admission values must be booleans")
        if admission["enabled"] and not admission["require_authority_record"]:
            raise LifecycleError("integrated execution admission cannot weaken the authority-record requirement")
    handoff = policy.get("documentation_handoff")
    if not isinstance(handoff, dict):
        raise LifecycleError("documentation_handoff policy object is required")
    accepted_ref = required_string(handoff.get("accepted_ref"), "documentation_handoff.accepted_ref")
    sha = accepted_sha(root, accepted_ref)
    categories = handoff.get("category_authorities")
    if not isinstance(categories, dict) or set(categories) != REQUIRED_CATEGORIES:
        missing = sorted(REQUIRED_CATEGORIES - set(categories or {}))
        extra = sorted(set(categories or {}) - REQUIRED_CATEGORIES)
        raise LifecycleError(f"documentation_handoff.category_authorities must map exactly the required categories; missing={missing}; extra={extra}")
    for category, target in categories.items():
        safe_path(target, f"authority mapping for {category}")
    continuity = handoff.get("continuity")
    if not isinstance(continuity, dict) or continuity.get("mandatory_operational_skill") != "documentation-handoff-continuity":
        raise LifecycleError("continuity must remain enabled as documentation-handoff-continuity")
    if continuity.get("field_study") != "EXTERNAL_APPEND_ONLY_NON_AUTHORITATIVE":
        raise LifecycleError("Field Study must remain default-on, external, append-only and non-authoritative")

    cfg = lifecycle(policy)
    profile = required_string(cfg.get("project_profile"), "project_lifecycle.project_profile")
    if profile not in PROFILES:
        raise LifecycleError(f"project_profile must be one of {sorted(PROFILES)}")
    pack = cfg.get("knowledge_pack")
    if not isinstance(pack, dict) or set(pack) != CORE_KEYS:
        raise LifecycleError("knowledge_pack must define exactly readme, project_status, architecture, engineering, roadmap and changelog")
    pack = {key: safe_path(value, f"knowledge_pack.{key}") for key, value in pack.items()}
    if len(set(pack.values())) != len(pack):
        raise LifecycleError("each core knowledge authority must have its own canonical path")
    gates = cfg.get("quality_gates")
    if not isinstance(gates, list) or not gates:
        raise LifecycleError("at least one executable quality gate is mandatory by adoption contract")
    gate_ids: set[str] = set()
    normalized_gates: list[dict[str, Any]] = []
    for gate in gates:
        if not isinstance(gate, dict): raise LifecycleError("quality gate must be an object")
        gate_id = required_string(gate.get("id"), "quality gate id")
        if gate_id in gate_ids: raise LifecycleError("quality gate ids must be unique")
        if set(gate) == {"id", "argv", "provenance"}:
            argv = gate.get("argv")
            provenance = str(gate.get("provenance") or "").upper()
            if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in argv):
                raise LifecycleError(f"quality gate {gate_id}.argv must be a non-empty argument list")
            if provenance not in {"OWNER_AUTHORED", "PACKAGE_OWNED"}:
                raise LifecycleError(f"quality gate {gate_id} has untrusted command provenance")
            normalized_gates.append({"id": gate_id, "argv": list(argv), "provenance": provenance, "execution": "ARGV_NO_SHELL"})
        elif set(gate) == {"id", "command"}:
            command = required_string(gate.get("command"), f"quality gate {gate_id}.command")
            if any(token in command for token in ("\n", "\r")): raise LifecycleError("quality gate commands must be one line")
            normalized_gates.append({"id": gate_id, "command": command, "provenance": "LEGACY_OWNER_POLICY", "execution": "LEGACY_SHELL"})
        else:
            raise LifecycleError(f"quality gate {gate_id} must use trusted argv or the exact legacy command shape")
        gate_ids.add(gate_id)
    boundaries = cfg.get("safety_boundaries")
    if not isinstance(boundaries, dict): raise LifecycleError("project_lifecycle.safety_boundaries is required")
    for name in ("runtime", "production", "data", "secrets"):
        required_string(boundaries.get(name), f"safety_boundaries.{name}")
    modules = cfg.get("modules")
    if not isinstance(modules, dict) or set(modules) != MODULES or any(not isinstance(value, bool) for value in modules.values()):
        raise LifecycleError(f"modules must define exactly {sorted(MODULES)} as booleans")
    intent = cfg.get("project_intent")
    if not isinstance(intent, dict): raise LifecycleError("project_intent is required; do not silently invent project purpose")
    for name in ("purpose", "intended_use", "success_definition", "non_goals", "constraints"):
        required_string(intent.get(name), f"project_intent.{name}")
    effect_contract = side_effect_contract(root, policy)
    return {"accepted_ref": accepted_ref, "accepted_sha": sha, "handoff": handoff, "profile": profile, "pack": pack, "gates": normalized_gates, "boundaries": boundaries, "modules": modules, "intent": intent, "side_effect_contract": effect_contract, "execution_admission": admission or {"enabled": False, "require_authority_record": False}, "testing_strategy": required_string(cfg.get("testing_strategy"), "testing_strategy"), "engineering_conventions": required_string(cfg.get("engineering_conventions"), "engineering_conventions")}


def package_root() -> Path:
    return Path(__file__).resolve().parents[3]


def render(text: str, values: dict[str, str]) -> str:
    for key, value in values.items(): text = text.replace("{{" + key + "}}", value)
    return text


def template_path(name: str) -> Path:
    return package_root() / "templates" / "project-lifecycle" / f"{name}.tmpl"


def write_missing(root: Path, target: str, template: str, values: dict[str, str]) -> bool:
    path = root / target
    if path.exists(): return False
    source = template_path(template)
    if not source.is_file(): raise LifecycleError(f"portable template is missing: {template}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(source.read_text(encoding="utf-8"), values), encoding="utf-8", newline="\n")
    return True


def template_values(facts: dict[str, Any], mode: str) -> dict[str, str]:
    unknown = "UNKNOWN — establish from verified accepted reality."
    intent = facts["intent"]
    pack = facts["pack"]
    boundaries = facts["boundaries"]
    return {
        "PROJECT_NAME": intent.get("name", "Project"), "PURPOSE": intent["purpose"], "INTENDED_USE": intent["intended_use"],
        "SUCCESS_DEFINITION": intent["success_definition"], "NON_GOALS": intent["non_goals"], "CONSTRAINTS": intent["constraints"],
        "GET_STARTED": "Document the smallest verified local setup command for this project.", "ACCEPTED_REF": facts["accepted_ref"],
        "PROJECT_STATUS_PATH": pack["project_status"], "ARCHITECTURE_PATH": pack["architecture"], "ENGINEERING_PATH": pack["engineering"], "ROADMAP_PATH": pack["roadmap"], "CHANGELOG_PATH": pack["changelog"],
        "ACCEPTED_CAPABILITIES": "- " + (unknown if mode == "existing" else "No accepted capabilities recorded yet."),
        "ACCEPTED_LIMITATIONS": "- " + (unknown if mode == "existing" else "No accepted limitations recorded yet."),
        "ACTIVE_INITIATIVE": unknown if mode == "existing" else "None yet.", "NEXT_MILESTONE": unknown if mode == "existing" else "See ROADMAP.",
        "ARCHITECTURE_SUMMARY": unknown if mode == "existing" else "Describe the smallest useful accepted component shape.",
        "RUNTIME_BOUNDARY": boundaries["runtime"], "DATA_BOUNDARY": boundaries["data"], "PRODUCTION_BOUNDARY": boundaries["production"], "SECRETS_BOUNDARY": boundaries["secrets"],
        "ARCHITECTURE_INVARIANTS": "- Preserve the documented runtime, data and authority boundaries.",
        "ADR_POINTER": "No ADR directory enabled." if not facts["modules"]["adr"] else "Accepted ADRs live in `docs/adr/`.",
        "ENGINEERING_CONVENTIONS": facts["engineering_conventions"], "TESTING_STRATEGY": facts["testing_strategy"], "ANTI_PATTERNS": "- Do not bypass configured quality gates or copy active state into canonical docs.",
        "ROADMAP_NOW": "- " + (unknown if mode == "existing" else "No initiative selected."), "ROADMAP_NEXT": "- " + (unknown if mode == "existing" else "No milestone selected."),
        "ROADMAP_LATER": "- None recorded.", "ROADMAP_RESEARCH": "- None recorded.", "ROADMAP_DROPPED": "- None recorded.", "ROADMAP_DONE": "- None recorded.",
        "OPERATIONS_BOUNDARY": boundaries["production"], "RECOVERY_GUIDANCE": "Document project-specific rollback, backup/restore and health verification here.",
    }


def bootstrap(root: Path, facts: dict[str, Any], mode: str, verify_gates: bool) -> dict[str, Any]:
    values = template_values(facts, mode); pack = facts["pack"]
    created: list[str] = []
    for key, target in pack.items():
        if write_missing(root, target, f"{key.upper()}.md", values): created.append(target)
    modules = facts["modules"]
    optional = {"operations": ("OPERATIONS.md", "OPERATIONS.md"), "security": ("SECURITY.md", "SECURITY.md"), "migrations": ("MIGRATIONS.md", "MIGRATIONS.md"), "project_brief": ("PROJECT_BRIEF.md", "PROJECT_BRIEF.md")}
    for name, (target, template) in optional.items():
        if modules[name] and write_missing(root, target, template, values): created.append(target)
    if modules["adr"]:
        adr = root / "docs" / "adr"
        adr.mkdir(parents=True, exist_ok=True)
        index = adr / "README.md"
        if not index.exists(): index.write_text("# Architecture Decision Records\n\nAccepted durable decision rationale lives here.\n", encoding="utf-8", newline="\n"); created.append("docs/adr/README.md")
    missing_authorities = [path for path in facts["handoff"]["category_authorities"].values() if not (root / path).is_file()]
    if missing_authorities:
        raise LifecycleError(f"documentation authority mappings point to missing files: {sorted(missing_authorities)}")
    gates = verify_gates_fn(root, facts["gates"]) if verify_gates else []
    return {"created": created, "quality_gates": gates, "accepted_ref": facts["accepted_ref"], "accepted_sha": facts["accepted_sha"], "profile": facts["profile"], "mode": mode}


def verify_gates_fn(root: Path, gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for gate in gates:
        if gate["execution"] == "ARGV_NO_SHELL":
            completed = subprocess.run(gate["argv"], cwd=root, shell=False, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=180)
            command = json.dumps(gate["argv"], ensure_ascii=False)
        else:
            completed = subprocess.run(gate["command"], cwd=root, shell=True, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=180)
            command = gate["command"]
        results.append({
            "id": gate["id"], "command": command, "argv": gate.get("argv"),
            "provenance": gate["provenance"], "execution": gate["execution"],
            "exit_code": completed.returncode, "output_tail": (completed.stdout + completed.stderr)[-500:],
        })
    failed = [item["id"] for item in results if item["exit_code"] != 0]
    if failed: raise LifecycleError(f"quality gates failed: {failed}")
    return results


def candidate_from_current(root: Path) -> str | None:
    current = root / ".buildos" / "control" / "CURRENT"
    try:
        pointer = json.loads(current.read_text(encoding="utf-8")); filename = str(pointer["file"])
        if Path(filename).name != filename: return None
        generation = json.loads((root / ".buildos" / "control" / "generations" / filename).read_text(encoding="utf-8"))
        state = generation.get("state") or {}
        return (state.get("product_commit") or {}).get("sha") if state.get("phase") == "CLOSED" else None
    except (OSError, ValueError, KeyError, TypeError): return None


def reconcile(root: Path, facts: dict[str, Any], candidate: str | None) -> dict[str, Any]:
    candidate = candidate or candidate_from_current(root)
    if not candidate: raise LifecycleError("candidate SHA is required unless Build OS CURRENT is CLOSED with a product commit")
    candidate = run(root, "rev-parse", "--verify", f"{candidate}^{{commit}}")
    contained = subprocess.run(["git", "merge-base", "--is-ancestor", candidate, facts["accepted_sha"]], cwd=root, timeout=45).returncode == 0
    if not contained:
        return {"state": "CLOSED_PENDING_BASELINE_ADVANCE", "candidate_sha": candidate, "product_feature_head": candidate, "accepted_ref": facts["accepted_ref"], "resolved_accepted_sha": facts["accepted_sha"], "accepted_sha_dynamic_git_authority": True, "required_actions": ["advance accepted_ref to a baseline containing the CLOSED candidate", "do not update accepted PROJECT_STATUS, CHANGELOG or ROADMAP DONE yet"]}
    return {
        "state": "ACCEPTED_BASELINE_RECONCILIATION_REQUIRED",
        "candidate_sha": candidate,
        "product_feature_head": candidate,
        "accepted_ref": facts["accepted_ref"],
        "resolved_accepted_sha": facts["accepted_sha"],
        "accepted_integration_sha": facts["accepted_sha"],
        "accepted_sha_dynamic_git_authority": True,
        "accepted_baseline_authority": "git rev-parse accepted_ref",
        "containment_proof": "git merge-base --is-ancestor candidate accepted_ref",
        "tracked_docs_self_sha_required": False,
        "project_status_self_sha_required": False,
        "changelog_self_sha_required": False,
        "roadmap_self_sha_required": False,
        "sha_only_documentation_churn_required": False,
        "required_actions": ["semantically update PROJECT_STATUS accepted capabilities/limitations if affected", "add concise CHANGELOG accepted-history entry if meaningful", "reconcile ROADMAP DONE only for accepted work", "checkpoint continuity after documentation reconciliation", "retire continuity only after the new checkpoint and successful deterministic checks"],
        "semantic_prose_generated": False,
    }


def retire_project(root: Path, facts: dict[str, Any], confirm: bool) -> dict[str, Any]:
    if not confirm: raise LifecycleError("project retirement is explicit; pass --confirm after Tech Lead review")
    target = root / "PROJECT_CLOSURE.md"
    if target.exists(): raise LifecycleError("PROJECT_CLOSURE.md already exists; update it deliberately rather than overwriting it")
    values = template_values(facts, "existing")
    write_missing(root, "PROJECT_CLOSURE.md", "PROJECT_CLOSURE.md", values)
    return {"closure_record": "PROJECT_CLOSURE.md", "final_accepted_sha": facts["accepted_sha"], "note": "Complete the bounded closure record from verified project reality; no secret material is recorded."}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Project Lifecycle Kit v1 deterministic helper")
    p.add_argument("--root", default=".")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    boot = sub.add_parser("bootstrap"); boot.add_argument("--mode", choices=["greenfield", "existing"], required=True); boot.add_argument("--verify-gates", action="store_true")
    sub.add_parser("verify-gates")
    rec = sub.add_parser("reconcile"); rec.add_argument("--candidate-sha")
    advance = sub.add_parser("advance", help="atomically advance accepted_ref with an expected-old-SHA guard")
    advance.add_argument("--expected-old-sha", required=True)
    advance.add_argument("--target-sha", required=True)
    retire = sub.add_parser("retire-project"); retire.add_argument("--confirm", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--version"]:
        print(json.dumps({"component": "project-lifecycle-kit", "version": KIT_VERSION}, sort_keys=True))
        return 0
    args = parser().parse_args(argv)
    try:
        root = git_root(Path(args.root).resolve()); policy, _ = read_policy(root); facts = validate_policy(root, policy)
        if args.command == "check": return emit("PASS", kit_version=KIT_VERSION, accepted_ref=facts["accepted_ref"], resolved_accepted_sha=facts["accepted_sha"], profile=facts["profile"], side_effect_contract=facts["side_effect_contract"], mandatory_by_adoption_contract=True, kernel_enforced=False)
        if args.command == "bootstrap": return emit("PASS", kit_version=KIT_VERSION, **bootstrap(root, facts, args.mode, args.verify_gates))
        if args.command == "verify-gates": return emit("PASS", kit_version=KIT_VERSION, quality_gates=verify_gates_fn(root, facts["gates"]))
        if args.command == "reconcile": return emit("PASS", kit_version=KIT_VERSION, **reconcile(root, facts, args.candidate_sha))
        if args.command == "advance": return emit("PASS", kit_version=KIT_VERSION, **advance_ref(root, facts["accepted_ref"], args.expected_old_sha, args.target_sha))
        return emit("PASS", kit_version=KIT_VERSION, **retire_project(root, facts, args.confirm))
    except (LifecycleError, OSError, subprocess.SubprocessError) as exc:
        return emit("FAIL", error=type(exc).__name__, message=str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
