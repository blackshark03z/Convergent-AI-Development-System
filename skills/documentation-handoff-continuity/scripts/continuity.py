#!/usr/bin/env python3
"""Bounded, non-authoritative continuity sidecar for portable Build OS adoption."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any

SCHEMA = "buildos.continuity-sidecar.v1"
SKILL_VERSION = "1.0.4"
QUARANTINE_SCHEMA = "buildos.continuity-legacy-quarantine.v1"
LEGACY_SKILL_VERSIONS = {"1.0.0", "1.0.1"}
MAX_BYTES = 16 * 1024
CAPSULE_SCHEMA = "buildos.working-state-capsule.v1"
CAPSULE_MAX_BYTES = 8 * 1024
CAPSULE_NORMAL_BYTES = 4 * 1024
CAPSULE_LIST_LIMIT = 6
TASK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CATEGORIES = {
    "USER_BEHAVIOR", "ARCHITECTURE_OWNERSHIP_BOUNDARY", "API_CONFIG_SCHEMA",
    "DEVELOPER_WORKFLOW", "FEATURE_PRESET_INVENTORY", "IMPLEMENTATION_ONLY",
}
YES_CATEGORIES = CATEGORIES - {"IMPLEMENTATION_ONLY"}
SECRET_RE = re.compile(r"(?i)(?:password|secret|api[_-]?key|access[_-]?token|bearer\s+|authorization\s*:|://[^/\s:@]+:[^/\s@]+@)")


class ContinuityError(RuntimeError):
    pass


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(root: Path, *args: str, allow_fail: bool = False) -> str:
    proc = subprocess.run(["git", *args], cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=30)
    if proc.returncode and not allow_fail:
        raise ContinuityError(f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout.strip()


def git_root(root: Path) -> Path:
    return Path(run(root, "rev-parse", "--show-toplevel")).resolve()


def common_dir(root: Path) -> Path:
    value = Path(run(root, "rev-parse", "--git-common-dir"))
    return (root / value).resolve() if not value.is_absolute() else value.resolve()


def canonical_revision(value: Any) -> int:
    """Return the one logical revision identity used by every command.

    The CLI accepts the documented numeric form and the equivalent canonical
    sidecar form (for example, ``1`` and ``r001``), but stores and resolves an
    integer everywhere internally.
    """
    text = str(value).strip()
    if text.lower().startswith("r"):
        text = text[1:]
    if not re.fullmatch(r"[0-9]+", text):
        raise argparse.ArgumentTypeError("revision must be a positive integer or rNNN")
    revision = int(text)
    if revision < 1:
        raise argparse.ArgumentTypeError("revision must be positive")
    return revision


def revision_from_kernel(root: Path, requested: int | str | None) -> tuple[int, dict[str, Any]]:
    current = root / ".buildos" / "control" / "CURRENT"
    if not current.is_file():
        observed = 1
        if requested is not None and canonical_revision(requested) != observed:
            raise ContinuityError(f"requested revision r{canonical_revision(requested):03d} does not match Build OS revision r{observed:03d}")
        return observed, {"generation": None, "generation_hash": None, "phase": "UNINITIALIZED"}
    try:
        pointer = json.loads(current.read_text(encoding="utf-8"))
        filename = str(pointer.get("file") or "")
        if Path(filename).name != filename or not filename.endswith(".json"):
            raise ValueError("invalid CURRENT pointer")
        payload = json.loads((root / ".buildos" / "control" / "generations" / filename).read_text(encoding="utf-8"))
        state = payload.get("state") or {}
        observed = int(state.get("revision", 1))
        kernel = {
            "generation": pointer.get("generation"), "generation_hash": pointer.get("generation_hash"),
            "phase": state.get("phase", "UNKNOWN"), "product_sha": (state.get("product_commit") or {}).get("sha"),
            "task_id": state.get("task_id"), "lease_status": (state.get("lease") or {}).get("status"),
        }
        if requested is not None:
            requested = canonical_revision(requested)
            if requested != observed:
                raise ContinuityError(f"requested revision r{requested:03d} does not match Build OS revision r{observed:03d}")
        return observed, kernel
    except (OSError, ValueError, TypeError) as exc:
        raise ContinuityError("Build OS CURRENT is unreadable; run recover before continuity writes") from exc


def kernel_state(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read the current immutable Build OS generation without changing it."""
    current = root / ".buildos" / "control" / "CURRENT"
    if not current.is_file():
        return {}, {"generation": None, "generation_hash": None, "phase": "UNINITIALIZED"}
    try:
        pointer = json.loads(current.read_text(encoding="utf-8"))
        filename = str(pointer.get("file") or "")
        if Path(filename).name != filename or not filename.endswith(".json"):
            raise ValueError("invalid CURRENT pointer")
        payload = json.loads((root / ".buildos" / "control" / "generations" / filename).read_text(encoding="utf-8"))
        state = payload.get("state") or {}
        if not isinstance(state, dict):
            raise ValueError("invalid Build OS state")
        return state, {
            "generation": pointer.get("generation"), "generation_hash": pointer.get("generation_hash"),
            "phase": state.get("phase", "UNKNOWN"), "product_sha": (state.get("product_commit") or {}).get("sha"),
            "task_id": state.get("task_id"), "lease_status": (state.get("lease") or {}).get("status"),
        }
    except (OSError, ValueError, TypeError) as exc:
        raise ContinuityError("Build OS CURRENT is unreadable; run recover before using the working-state capsule") from exc


def policy(root: Path, supplied: str | None) -> tuple[dict[str, Any], str, Path | None]:
    path = Path(supplied).resolve() if supplied else root / ".buildos-policy.json"
    if path.is_file():
        data = path.read_bytes()
        try:
            value = json.loads(data)
        except ValueError as exc:
            raise ContinuityError("project policy is invalid JSON") from exc
        return value, digest(data), path
    return {"documentation_handoff": {"accepted_ref": "HEAD", "category_authorities": {}, "continuity": {}}}, digest(b"{}"), None


def dh_policy(value: dict[str, Any]) -> dict[str, Any]:
    result = value.get("documentation_handoff") or {}
    if not isinstance(result, dict):
        raise ContinuityError("documentation_handoff policy must be an object")
    return result


def ref_sha(root: Path, ref: str) -> str:
    sha = run(root, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if not re.fullmatch(r"[0-9a-f]{40,64}", sha):
        raise ContinuityError("accepted_ref did not resolve to a commit SHA")
    return sha


def skill_hash() -> str:
    root = Path(__file__).resolve().parents[1]
    components = [Path(__file__), root / "SKILL.md", root / "references" / "handoff.schema.json", root / "references" / "documentation-impact.md"]
    try:
        return digest(b"".join(item.read_bytes() for item in components))
    except OSError as exc:
        raise ContinuityError("continuity Skill assets are unreadable") from exc


def split_paths(root: Path) -> dict[str, list[str]]:
    raw = subprocess.run(["git", "status", "--porcelain=v1", "-z"], cwd=root, capture_output=True, timeout=30).stdout.decode("utf-8", "replace")
    staged: list[str] = []; unstaged: list[str] = []; untracked: list[str] = []
    fields = raw.split("\0")
    for field in fields:
        if not field:
            continue
        if len(field) < 4:
            raise ContinuityError("unable to parse Git status completely")
        code, path = field[:2], field[3:]
        if code == "??": untracked.append(path)
        else:
            if code[0] != " ": staged.append(path)
            if code[1] != " ": unstaged.append(path)
    return {"staged": sorted(set(staged)), "unstaged": sorted(set(unstaged)), "untracked": sorted(set(untracked))}


def bounded_paths(paths: list[str]) -> dict[str, Any]:
    return {"count": len(paths), "sample": paths[:24], "paths_hash": digest(canon(paths))}


def dirty(root: Path) -> dict[str, Any]:
    try:
        parts = split_paths(root)
        staged = subprocess.run(["git", "diff", "--cached", "--binary"], cwd=root, capture_output=True, timeout=30, check=True).stdout
        unstaged = subprocess.run(["git", "diff", "--binary"], cwd=root, capture_output=True, timeout=30, check=True).stdout
        untracked_rows = []
        for name in parts["untracked"]:
            path = root / name
            if not path.is_file() or path.is_symlink():
                raise ContinuityError(f"cannot completely fingerprint untracked path: {name}")
            untracked_rows.append([name, digest(path.read_bytes())])
        return {
            "complete": True,
            "staged": {**bounded_paths(parts["staged"]), "content_hash": digest(staged)},
            "unstaged": {**bounded_paths(parts["unstaged"]), "content_hash": digest(unstaged)},
            "untracked": {**bounded_paths(parts["untracked"]), "content_hash": digest(canon(untracked_rows))},
            "fingerprint": digest(canon({"staged": digest(staged), "unstaged": digest(unstaged), "untracked": untracked_rows})),
        }
    except (OSError, subprocess.SubprocessError, ContinuityError) as exc:
        return {"complete": False, "reason": str(exc), "fingerprint": None, "staged": {}, "unstaged": {}, "untracked": {}}


def worktree(root: Path) -> dict[str, Any]:
    top = git_root(root)
    return {"id": digest(str(top).lower().encode())[:24], "path_hash": digest(str(top).encode()), "branch": run(root, "branch", "--show-current") or "DETACHED"}


def sidecar_path(root: Path, task: str, revision: int) -> Path:
    return common_dir(root) / "buildos-continuity" / "active" / task / f"r{revision:03d}" / f"{worktree(root)['id']}.json"


def without_hash(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "self_hash"}


def reject_secrets(value: Any) -> None:
    if isinstance(value, str) and SECRET_RE.search(value):
        raise ContinuityError("secret-like material or credential-bearing URL is forbidden in the sidecar")
    if isinstance(value, dict):
        for key, item in value.items():
            reject_secrets(str(key)); reject_secrets(item)
    elif isinstance(value, list):
        for item in value: reject_secrets(item)


def validate_sidecar(value: dict[str, Any]) -> None:
    required = {"schema", "self_hash", "task_id", "revision", "accepted_ref", "resolved_accepted_sha", "task_base_sha", "policy_hash", "skill", "worktree", "git", "kernel", "checkpoint", "operational", "documentation", "evidence"}
    if set(value) != required or value.get("schema") != SCHEMA:
        raise ContinuityError("sidecar schema is invalid")
    if not TASK_RE.fullmatch(str(value.get("task_id", ""))) or not isinstance(value.get("revision"), int) or value["revision"] < 1:
        raise ContinuityError("sidecar task or revision is invalid")
    if value.get("self_hash") != digest(canon(without_hash(value))):
        raise ContinuityError("sidecar self-hash is invalid")
    encoded = canon(value)
    if len(encoded) > MAX_BYTES: raise ContinuityError("sidecar exceeds 16 KiB maximum")
    reject_secrets(value)


def load(path: Path) -> dict[str, Any]:
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc: raise ContinuityError("sidecar is unreadable") from exc
    validate_sidecar(value)
    return value


def atomic_replace(path: Path, value: dict[str, Any], expected: str | None) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = load(path)
        if not expected: raise ContinuityError("existing sidecar requires --expected-sidecar-hash for compare-and-swap")
        if existing["self_hash"] != expected: raise ContinuityError("sidecar compare-and-swap conflict")
    elif expected: raise ContinuityError("compare-and-swap expected a missing sidecar")
    value["self_hash"] = digest(canon(without_hash(value)))
    validate_sidecar(value)
    data = canon(value)
    fd, temp_name = tempfile.mkstemp(prefix=".sidecar-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name): os.unlink(temp_name)
    if load(path)["self_hash"] != value["self_hash"]: raise ContinuityError("atomic sidecar read-back verification failed")
    return value["self_hash"]


def atomic_bytes(path: Path, data: bytes) -> str:
    """Create an immutable artifact without overwriting an existing proof."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ContinuityError("quarantine proof already exists; refusing overwrite")
    fd, temp_name = tempfile.mkstemp(prefix=".quarantine-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name): os.unlink(temp_name)
    if path.read_bytes() != data:
        raise ContinuityError("quarantine artifact read-back verification failed")
    return digest(data)


def bounded(text: str, label: str, maximum: int = 768) -> str:
    result = str(text or "").strip()
    if len(result) > maximum: raise ContinuityError(f"{label} exceeds {maximum} characters")
    reject_secrets(result)
    return result


def parse_authorities(rows: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in rows:
        category, sep, path = row.partition("=")
        if not sep or category not in CATEGORIES or not path or category in result:
            raise ContinuityError("authority must be unique CATEGORY=relative/path")
        if Path(path).is_absolute() or ".." in Path(path).parts: raise ContinuityError("authority path must be a safe relative path")
        result[category] = path.replace("\\", "/")
    return result


def documentation(root: Path, p: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    state = args.documentation_impact
    categories = sorted(set(args.category or []))
    if any(item not in CATEGORIES for item in categories): raise ContinuityError("unknown documentation category")
    if state == "YES" and (not categories or any(item not in YES_CATEGORIES for item in categories)):
        raise ContinuityError("YES requires one or more non-implementation-only categories")
    if state == "NO" and categories != ["IMPLEMENTATION_ONLY"]:
        raise ContinuityError("NO requires exactly IMPLEMENTATION_ONLY")
    if state == "UNKNOWN" and categories: raise ContinuityError("UNKNOWN cannot claim categories")
    configured = dh_policy(p).get("category_authorities") or {}
    declared = parse_authorities(args.authority or [])
    authorities: dict[str, dict[str, str]] = {}
    for category in categories:
        if category in declared and category in configured:
            raise ContinuityError(f"multiple canonical authorities declared for {category}")
        path = declared.get(category) or configured.get(category)
        if state == "YES" and not isinstance(path, str): raise ContinuityError(f"no canonical authority is mapped for {category}")
        if path:
            target = root / path
            if not target.is_file(): raise ContinuityError(f"mapped documentation authority is missing: {path}")
            authorities[category] = {"path": path, "sha256": digest(target.read_bytes())}
    semantic = bounded(args.semantic_inspection or "", "semantic inspection")
    if state == "YES" and not semantic: raise ContinuityError("YES requires a semantic inspection declaration")
    rationale = bounded(args.documentation_rationale or "", "documentation rationale")
    if state in {"NO", "UNKNOWN"} and not rationale: raise ContinuityError(f"{state} requires a bounded rationale")
    return {"impact": state, "categories": categories, "authorities": authorities, "semantic_inspection": semantic or None, "rationale": rationale or None, "gate_state": "PRE_RECORD_READY" if state != "UNKNOWN" else "BLOCKED_UNKNOWN"}


def evidence(root: Path, rows: list[str]) -> list[dict[str, str]]:
    values = []
    for item in rows:
        path = Path(item)
        if path.is_absolute() or ".." in path.parts: raise ContinuityError("evidence pointer must be a safe relative path")
        target = root / path
        if not target.is_file(): raise ContinuityError(f"evidence is missing: {item}")
        values.append({"path": path.as_posix(), "sha256": digest(target.read_bytes())})
    if len(values) > 16: raise ContinuityError("too many evidence pointers")
    return values


def make_sidecar(root: Path, args: argparse.Namespace) -> tuple[dict[str, Any], Path]:
    task = args.task_id
    if not TASK_RE.fullmatch(task): raise ContinuityError("task-id must be a bounded portable identifier")
    revision, kernel = revision_from_kernel(root, args.revision)
    pol, policy_hash, _ = policy(root, args.policy)
    cfg = dh_policy(pol); accepted_ref = str(args.accepted_ref or cfg.get("accepted_ref") or "HEAD").strip()
    if not accepted_ref: raise ContinuityError("accepted_ref is required")
    head = run(root, "rev-parse", "HEAD"); tree = run(root, "rev-parse", "HEAD^{tree}")
    existing = sidecar_path(root, task, revision)
    old = load(existing) if existing.is_file() else None
    base = old.get("task_base_sha") if old else head
    value = {
        "schema": SCHEMA, "self_hash": "", "task_id": task, "revision": revision,
        "accepted_ref": accepted_ref, "resolved_accepted_sha": ref_sha(root, accepted_ref), "task_base_sha": base,
        "policy_hash": policy_hash, "skill": {"name": "documentation-handoff-continuity", "version": SKILL_VERSION, "schema_version": SCHEMA, "sha256": skill_hash()},
        "worktree": worktree(root),
        "git": {"head": head, "tree": tree, "dirty": dirty(root)},
        "kernel": kernel,
        "checkpoint": {"kind": args.kind, "time": now()},
        "operational": {"status": args.operational_status, "completed_summary": bounded(args.completed_summary, "completed summary"), "unproven_summary": bounded(args.unproven_summary, "unproven summary"), "dirty_intent_summary": bounded(args.dirty_intent_summary, "dirty intent summary"), "blocker_summary": bounded(args.blocker_summary, "blocker summary"), "next_safe_action": bounded(args.next_safe_action, "next safe action", 240), "decision_pointers": [bounded(x, "decision pointer", 240) for x in (args.decision or [])][:16], "safety_exceptions": [bounded(x, "safety exception", 240) for x in (args.safety_exception or [])][:8]},
        "documentation": documentation(root, pol, args), "evidence": evidence(root, args.evidence or []),
    }
    return value, existing


def verify_reality(root: Path, value: dict[str, Any]) -> tuple[str, list[str]]:
    problems: list[str] = []
    if value["worktree"]["id"] != worktree(root)["id"]: problems.append("wrong worktree")
    if value["accepted_ref"] and ref_sha(root, value["accepted_ref"]) != value["resolved_accepted_sha"]: problems.append("accepted ref moved")
    if value["git"]["head"] != run(root, "rev-parse", "HEAD"): problems.append("HEAD mismatch")
    live_state, kernel = kernel_state(root)
    revision = int(live_state.get("revision", 1)) if live_state else 1
    if revision != value["revision"] or any(kernel.get(key) != (value.get("kernel") or {}).get(key) for key in ("generation", "generation_hash", "phase")):
        problems.append("Build OS generation mismatch")
    if live_state and live_state.get("task_id") != value["task_id"]:
        problems.append("Build OS task mismatch")
    actual_dirty = dirty(root)
    if not actual_dirty.get("complete"): problems.append("dirty fingerprint incomplete")
    elif actual_dirty.get("fingerprint") != (value["git"].get("dirty") or {}).get("fingerprint"): problems.append("dirty state changed")
    try:
        _, policy_hash, _ = policy(root, None)
        if policy_hash != value["policy_hash"]: problems.append("policy changed")
    except ContinuityError: problems.append("policy unreadable")
    if value["skill"].get("sha256") != skill_hash(): problems.append("skill or schema changed")
    for item in value.get("evidence") or []:
        target = root / item["path"]
        if not target.is_file(): problems.append(f"missing evidence:{item['path']}")
        elif digest(target.read_bytes()) != item["sha256"]: problems.append(f"evidence hash mismatch:{item['path']}")
    docs = value["documentation"]
    for item in (docs.get("authorities") or {}).values():
        target = root / item["path"]
        if not target.is_file() or digest(target.read_bytes()) != item["sha256"]: problems.append(f"documentation authority stale:{item['path']}")
    if docs.get("impact") == "UNKNOWN": problems.append("documentation impact UNKNOWN")
    return ("SAFE_TO_CONTINUE" if not problems else "NEEDS_RECONCILIATION"), problems


def evidence_result(root: Path, item: dict[str, Any]) -> str:
    """Read only compact result metadata; never project evidence bodies."""
    target = root / str(item.get("path") or "")
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        checks = payload.get("checks")
        if isinstance(checks, list) and checks:
            passed = sum(1 for check in checks if int(check.get("returncode", 1)) == 0)
            return f"{'PASS' if passed == len(checks) else 'FAIL'} {passed}/{len(checks)}"
        return "BOUND"
    except (OSError, ValueError, TypeError):
        return "TARGETED_READ_REQUIRED"


def capsule_text(root: Path, value: dict[str, Any], live_state: dict[str, Any], kernel: dict[str, Any], state: str, problems: list[str]) -> str:
    """Render the bounded model-facing projection; source state remains canonical."""
    def text(item: Any, label: str, maximum: int = 480) -> str:
        return bounded(str(item or ""), label, maximum).replace("\n", " ") or "NONE"

    def limited(items: list[str], label: str, maximum: int = CAPSULE_LIST_LIMIT, item_maximum: int = 160) -> tuple[list[str], int]:
        clean = [text(item, label, item_maximum) for item in items if str(item or "").strip()]
        return clean[:maximum], max(0, len(clean) - maximum)

    operational = value["operational"]
    documentation_state = value["documentation"]
    git = value["git"]
    dirty_state = git.get("dirty") or {}
    dirty_sections = []
    dirty_paths: list[str] = []
    for name in ("staged", "unstaged", "untracked"):
        section = dirty_state.get(name) or {}
        count = int(section.get("count", 0))
        dirty_sections.append(f"{name}={count}")
        dirty_paths.extend(str(path) for path in (section.get("sample") or []))
    touched, additional_touched = limited(sorted(set(dirty_paths)), "touched path", 6, 160)
    decisions, additional_decisions = limited(list(operational.get("decision_pointers") or []), "decision pointer", 4, 120)
    authorities = [f"{category}:{item.get('path')}" for category, item in sorted((documentation_state.get("authorities") or {}).items())]
    authorities, additional_authorities = limited(authorities, "documentation authority", 4, 160)
    acceptance, additional_acceptance = limited(list(live_state.get("acceptance") or []), "acceptance item", 4, 120)
    sidecar_evidence = [
        f"continuity:{item.get('path')} sha256={item.get('sha256')} result=REFERENCED"
        for item in value.get("evidence") or []
    ]
    validation_results = [evidence_result(root, item) for item in live_state.get("evidence") or []]
    kernel_evidence = [
        f"buildos:{item.get('kind', 'EVIDENCE')}:{item.get('path')} sha256={item.get('sha256')} result={evidence_result(root, item)}"
        for item in live_state.get("evidence") or []
    ]
    evidence_rows, additional_evidence = limited(kernel_evidence + sidecar_evidence, "evidence pointer", 4, 220)
    phase = str(kernel.get("phase") or value["kernel"].get("phase") or "UNKNOWN")
    unresolved = acceptance if phase not in {"ASSURANCE_READY", "CLOSED"} else []
    targeted = []
    if problems:
        targeted.extend([".buildos/control/CURRENT", "continuity sidecar (reported path)"])
    if documentation_state.get("impact") == "YES":
        targeted.extend(item.split(":", 1)[1] for item in authorities if ":" in item)
    if phase in {"PRODUCT_COMMITTED", "ASSURANCE_READY", "CLOSED"} and evidence_rows:
        targeted.append("Build OS validation evidence pointer listed below")
    targeted, additional_targeted = limited(targeted, "targeted read", 4, 180)
    lines = [
        f"schema={CAPSULE_SCHEMA}",
        "projection=READ_ONLY_DERIVED",
        f"status={state}",
        f"continuity_classification={state}",
        f"task_id={text(value['task_id'], 'task id', 128)}",
        f"revision=r{int(value['revision']):03d}",
        f"lifecycle_phase={text(phase, 'lifecycle phase', 80)}",
        f"accepted_ref={text(value['accepted_ref'], 'accepted ref', 240)}",
        f"resolved_accepted_sha={text(value['resolved_accepted_sha'], 'accepted SHA', 128)}",
        f"task_base_sha={text(value['task_base_sha'], 'task base SHA', 128)}",
        f"current_head={text(git.get('head'), 'HEAD', 128)}",
        f"current_tree={text(git.get('tree'), 'tree', 128)}",
        f"worktree_id={text((value.get('worktree') or {}).get('id'), 'worktree id', 128)}",
        f"worktree_branch={text((value.get('worktree') or {}).get('branch'), 'worktree branch', 240)}",
        f"git_cleanliness={'clean' if all(part.endswith('=0') for part in dirty_sections) else 'dirty'} {' '.join(dirty_sections)}",
        f"touched_paths={','.join(touched) if touched else 'NONE'}",
        f"additional_touched_paths={additional_touched}",
        f"current_objective={text(live_state.get('outcome') or operational.get('completed_summary'), 'current objective', 240)}",
        f"current_phase_action={text(live_state.get('next_action') or operational.get('next_safe_action'), 'next action', 240)}",
        f"material_decisions={' | '.join(decisions) if decisions else 'NONE'}",
        f"additional_decisions={additional_decisions}",
        f"current_blockers={text(operational.get('blocker_summary'), 'blocker summary', 240)}",
        f"documentation_impact={text(documentation_state.get('impact'), 'documentation impact', 80)} gate={text(documentation_state.get('gate_state'), 'documentation gate', 80)}",
        f"documentation_authorities={' | '.join(authorities) if authorities else 'NONE'}",
        f"additional_documentation_authorities={additional_authorities}",
        f"validation_status=phase:{phase} evidence_bound={len(kernel_evidence)}",
        f"validation_result={' | '.join(validation_results) if validation_results else 'NOT_RUN'}",
        f"unresolved_acceptance={' | '.join(unresolved) if unresolved else 'NONE'}",
        f"additional_unresolved_acceptance={additional_acceptance if unresolved else 0}",
        f"evidence_pointers={' | '.join(evidence_rows) if evidence_rows else 'NONE'}",
        f"additional_evidence={additional_evidence}",
        f"next_action={text(operational.get('next_safe_action') or live_state.get('next_action'), 'next action', 240)}",
        f"targeted_reads={' | '.join(targeted) if targeted else 'NONE'}",
        f"additional_targeted_reads={additional_targeted}",
        f"mismatches={' | '.join(text(problem, 'mismatch', 240) for problem in problems) if problems else 'NONE'}",
    ]
    return "\n".join(lines) + "\n"


def command_working_set(args: argparse.Namespace) -> dict[str, Any]:
    root, path, value = target(args)
    live_state, kernel = kernel_state(root)
    state, problems = verify_reality(root, value)
    try:
        rendered = capsule_text(root, value, live_state, kernel, state, problems)
    except ContinuityError:
        # Do not risk printing a credential-bearing or otherwise unsafe source field.
        rendered = "\n".join([
            f"schema={CAPSULE_SCHEMA}", "projection=READ_ONLY_DERIVED",
            "status=TARGETED_READ_REQUIRED", "continuity_classification=TARGETED_READ_REQUIRED",
            "reason=CAPSULE_SOURCE_REQUIRES_SAFE_TARGETED_READ",
            "targeted_reads=.buildos/control/CURRENT | continuity sidecar",
        ]) + "\n"
        state = "TARGETED_READ_REQUIRED"; problems = ["capsule source requires safe targeted read"]
    size = len(rendered.encode("utf-8"))
    if size > CAPSULE_MAX_BYTES:
        rendered = "\n".join([
            f"schema={CAPSULE_SCHEMA}", "projection=READ_ONLY_DERIVED",
            "status=TARGETED_READ_REQUIRED", "continuity_classification=TARGETED_READ_REQUIRED",
            "reason=CAPSULE_SIZE_BOUND_REQUIRES_TARGETED_READ",
            "targeted_reads=.buildos/control/CURRENT | continuity sidecar | referenced evidence",
            f"additional_mismatches={len(problems)}",
        ]) + "\n"
        state = "TARGETED_READ_REQUIRED"; problems = ["capsule would exceed 8 KiB"]
        size = len(rendered.encode("utf-8"))
    return {
        "status": state, "sidecar": str(path), "capsule_schema": CAPSULE_SCHEMA,
        "bytes": size, "normal_size_target": CAPSULE_NORMAL_BYTES,
        "hard_max_bytes": CAPSULE_MAX_BYTES, "problems": problems, "capsule": rendered,
    }


def command_checkpoint(args: argparse.Namespace) -> dict[str, Any]:
    root = git_root(Path(args.root).resolve()); value, path = make_sidecar(root, args)
    result = atomic_replace(path, value, args.expected_sidecar_hash)
    return {"status": "PASS", "sidecar": str(path), "sidecar_hash": result, "bytes": path.stat().st_size, "documentation_gate": value["documentation"]["gate_state"]}


def target(args: argparse.Namespace) -> tuple[Path, Path, dict[str, Any]]:
    root = git_root(Path(args.root).resolve()); revision, _ = revision_from_kernel(root, args.revision)
    path = sidecar_path(root, args.task_id, revision)
    return root, path, load(path)


def command_verify(args: argparse.Namespace) -> dict[str, Any]:
    root, path, value = target(args); state, problems = verify_reality(root, value)
    return {"status": state, "sidecar": str(path), "problems": problems, "next_safe_action": value["operational"]["next_safe_action"]}


def command_docs_check(args: argparse.Namespace) -> dict[str, Any]:
    root, path, value = target(args); docs = value["documentation"]; problems: list[str] = []
    if docs["impact"] == "UNKNOWN": problems.append("documentation impact is UNKNOWN")
    if docs["impact"] == "YES" and not docs.get("semantic_inspection"): problems.append("semantic inspection declaration is missing")
    for category in docs.get("categories") or []:
        if docs["impact"] == "YES" and category not in (docs.get("authorities") or {}): problems.append(f"mapped authority missing:{category}")
    for item in (docs.get("authorities") or {}).values():
        doc_target = root / item["path"]
        if not doc_target.is_file(): problems.append(f"mapped authority missing:{item['path']}")
        elif digest(doc_target.read_bytes()) != item["sha256"]: problems.append(f"documentation authority stale:{item['path']}")
    return {"status": "PASS" if not problems else "FAIL", "sidecar": str(path), "documentation_impact": docs["impact"], "problems": sorted(set(problems)), "deterministic_scope": "declarations, hashes, paths and mappings only; semantic prose remains human evidence"}


def command_takeover(args: argparse.Namespace) -> dict[str, Any]:
    root = git_root(Path(args.root).resolve())
    try:
        _, path, value = target(args)
    except ContinuityError:
        historical = find_quarantine_records(root, args.task_id)
        if historical:
            return {"status": "HISTORICAL_QUARANTINED", "task_id": args.task_id, "quarantines": [str(path) for path, _ in historical], "takeover_checkpoint_required": False, "problems": ["active continuity sidecar was quarantined as malformed legacy state"]}
        raise
    # Build OS is checked, never changed, before trusting the projection.
    package = Path(args.package_root).resolve() if args.package_root else Path(__file__).resolve().parents[3]
    recover = subprocess.run([sys.executable, str(package / "scripts" / "ai.py"), "--root", str(root), "recover", "--check-only"], text=True, capture_output=True, timeout=45)
    state, problems = verify_reality(root, value)
    if recover.returncode: problems.append("Build OS recover --check-only failed")
    siblings = list(path.parent.glob("*.json"))
    for sibling in siblings:
        if sibling != path:
            try:
                competing = load(sibling)
                # Same task/revision can exist in isolated worktrees only when
                # they make separate branch claims. Same branch is a collision.
                if competing.get("worktree", {}).get("branch") == value.get("worktree", {}).get("branch"):
                    problems.append("duplicate same-task/revision sidecar")
            except ContinuityError: problems.append("invalid competing sidecar")
    if value["operational"]["status"] == "BLOCKED": classification = "BLOCKED"
    elif recover.returncode or any("invalid" in p or "recover" in p for p in problems): classification = "RECOVERY_REQUIRED"
    elif problems: classification = "NEEDS_RECONCILIATION"
    else: classification = "SAFE_TO_CONTINUE"
    return {"status": classification, "sidecar": str(path), "problems": problems, "takeover_checkpoint_required": classification == "SAFE_TO_CONTINUE", "buildos_recover": recover.stdout[-1000:]}


def command_retire(args: argparse.Namespace) -> dict[str, Any]:
    root, path, value = target(args); current_dirty = dirty(root)
    if not current_dirty.get("complete") or current_dirty.get("fingerprint") != value["git"]["dirty"].get("fingerprint"):
        raise ContinuityError("active dirty-worktree retirement fails closed")
    _, kernel = revision_from_kernel(root, args.revision)
    if kernel.get("phase") != "CLOSED": raise ContinuityError("retirement requires Build OS CLOSED")
    candidate = kernel.get("product_sha") or value["git"]["head"]
    accepted = ref_sha(root, value["accepted_ref"])
    contained = subprocess.run(["git", "merge-base", "--is-ancestor", candidate, accepted], cwd=root, timeout=30).returncode == 0
    if not contained:
        return {"status": "CLOSED_PENDING_BASELINE_ADVANCE", "candidate_sha": candidate, "resolved_accepted_sha": accepted, "sidecar": str(path)}
    archive = common_dir(root) / "buildos-continuity" / "archive" / value["task_id"] / f"r{value['revision']:03d}" / value["self_hash"][:16]
    archive.mkdir(parents=True, exist_ok=True)
    proof = {"schema": "buildos.continuity-terminal-proof.v1", "task_id": value["task_id"], "revision": value["revision"], "sidecar_hash": value["self_hash"], "candidate_sha": candidate, "accepted_ref": value["accepted_ref"], "resolved_accepted_sha": accepted, "retired_at": now()}
    atomic_replace(archive / "terminal.json", {**value, "operational": {**value["operational"], "completed_summary": "retired terminal proof", "unproven_summary": "", "dirty_intent_summary": "", "blocker_summary": "", "decision_pointers": [], "safety_exceptions": [], "next_safe_action": "terminal proof retained"}}, None)
    # terminal.json stays bounded; a minimal adjacent receipt is intentionally not a task authority.
    (archive / "receipt.json").write_bytes(canon(proof))
    path.unlink()
    return {"status": "RETIRED", "archive": str(archive), "accepted_sha": accepted}


def quarantine_root(root: Path, task: str) -> Path:
    return common_dir(root) / "buildos-continuity" / "quarantine" / task


def quarantine_path(root: Path, task: str, revision: int, sidecar_hash: str) -> Path:
    return quarantine_root(root, task) / f"r{revision:03d}" / sidecar_hash[:16]


def load_quarantine_record(path: Path) -> dict[str, Any]:
    try:
        value = json.loads((path / "quarantine.json").read_text(encoding="utf-8"))
        original = (path / "original.sidecar.json").read_bytes()
        receipt = json.loads((path / "receipt.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ContinuityError("quarantine proof is unreadable") from exc
    if value.get("schema") != QUARANTINE_SCHEMA or value.get("self_hash") != digest(canon({k: v for k, v in value.items() if k != "self_hash"})):
        raise ContinuityError("quarantine record self-hash is invalid")
    if digest(original) != value.get("original_sidecar_sha256"):
        raise ContinuityError("quarantine original sidecar hash is invalid")
    if receipt.get("schema") != "buildos.continuity-legacy-quarantine-receipt.v1" or receipt.get("quarantine_hash") != value["self_hash"]:
        raise ContinuityError("quarantine receipt is invalid")
    return value


def find_quarantine_records(root: Path, task: str) -> list[tuple[Path, dict[str, Any]]]:
    base = quarantine_root(root, task)
    results: list[tuple[Path, dict[str, Any]]] = []
    if not base.is_dir():
        return results
    for record in sorted(base.glob("r*/[0-9a-f]*/quarantine.json")):
        path = record.parent
        try:
            results.append((path, load_quarantine_record(path)))
        except ContinuityError:
            continue
    return results


def command_quarantine_legacy(args: argparse.Namespace) -> dict[str, Any]:
    root = git_root(Path(args.root).resolve())
    if args.revision is None:
        raise ContinuityError("legacy quarantine requires the explicit historical revision")
    revision = canonical_revision(args.revision)
    path = sidecar_path(root, args.task_id, revision)
    if not path.is_file():
        raise ContinuityError("legacy sidecar is missing from the expected active path")
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ContinuityError("legacy sidecar is not valid JSON") from exc
    validate_sidecar(value)
    if value.get("task_id") != args.task_id or value.get("revision") != revision:
        raise ContinuityError("legacy sidecar task/revision does not match the requested identity")
    if value.get("worktree", {}).get("id") != worktree(root)["id"]:
        raise ContinuityError("legacy sidecar belongs to a different worktree")
    skill = value.get("skill") or {}
    if skill.get("version") not in LEGACY_SKILL_VERSIONS or (value.get("kernel") or {}).get("phase") != "UNOBSERVED":
        raise ContinuityError("sidecar is not proven malformed by the known pre-1.0.2 defect")
    authority = bounded(args.tech_lead_authority or "", "Tech Lead migration authority", 512)
    if not re.search(r"(?i)tech[\s_-]*lead", authority) or not re.search(r"(?i)approved|authorized", authority):
        raise ContinuityError("explicit Tech Lead migration authority is invalid")
    recorded_dirty = value.get("git", {}).get("dirty") or {}
    live_dirty = dirty(root)
    if not live_dirty.get("complete") or live_dirty.get("fingerprint") != recorded_dirty.get("fingerprint"):
        raise ContinuityError("legacy quarantine requires the recorded clean worktree state")
    if any((recorded_dirty.get(section) or {}).get("count", 0) for section in ("staged", "unstaged", "untracked")):
        raise ContinuityError("legacy quarantine refuses dirty intent or in-flight work")
    observed_revision, kernel = revision_from_kernel(root, None)
    if observed_revision == revision:
        raise ContinuityError("current Build OS revision legitimately owns the legacy sidecar revision")
    if kernel.get("phase") != "CLOSED" or kernel.get("lease_status") not in {None, "RELEASED"}:
        raise ContinuityError("successor Build OS state is not terminal and released")
    package = Path(args.package_root).resolve() if args.package_root else Path(__file__).resolve().parents[3]
    recover = subprocess.run([sys.executable, str(package / "scripts" / "ai.py"), "--root", str(root), "recover", "--check-only"], text=True, capture_output=True, timeout=45)
    if recover.returncode:
        raise ContinuityError("canonical Build OS authority is not unambiguous")
    accepted = ref_sha(root, value["accepted_ref"])
    candidate = kernel.get("product_sha")
    if not candidate or subprocess.run(["git", "merge-base", "--is-ancestor", candidate, accepted], cwd=root, timeout=30).returncode != 0:
        raise ContinuityError("successor product state is not contained by the accepted baseline")
    archive = quarantine_path(root, args.task_id, revision, value["self_hash"])
    if archive.exists():
        record = load_quarantine_record(archive)
        if digest(raw) != record.get("original_sidecar_sha256"):
            raise ContinuityError("existing quarantine proof does not match the active sidecar")
    else:
        archive.mkdir(parents=True, exist_ok=False)
        original_sha = atomic_bytes(archive / "original.sidecar.json", raw)
        metadata = {
            "schema": QUARANTINE_SCHEMA, "self_hash": "", "classification": "QUARANTINED_LEGACY",
            "task_id": args.task_id, "revision": revision, "original_sidecar_sha256": original_sha,
            "original_sidecar_bytes": len(raw), "original_sidecar_path": str(path),
            "worktree": value["worktree"], "defect": "CONTINUITY-REVISION-RETIREMENT-CORRECTIVE-01",
            "affected_continuity_version": skill.get("version"), "migration_skill_version": SKILL_VERSION,
            "tech_lead_authority": authority, "observed_build_os": {"revision": observed_revision, **kernel},
            "accepted_ref": value["accepted_ref"], "resolved_accepted_sha": accepted,
            "normal_retirement_result": "FAIL: requested historical revision is not the observed Build OS revision",
            "quarantined_at": now(),
        }
        metadata["self_hash"] = digest(canon({k: v for k, v in metadata.items() if k != "self_hash"}))
        atomic_bytes(archive / "quarantine.json", canon(metadata))
        receipt = {"schema": "buildos.continuity-legacy-quarantine-receipt.v1", "classification": "QUARANTINED_LEGACY", "task_id": args.task_id, "revision": revision, "original_sidecar_sha256": original_sha, "quarantine_hash": metadata["self_hash"], "accepted_sha": accepted, "recorded_at": metadata["quarantined_at"]}
        atomic_bytes(archive / "receipt.json", canon(receipt))
        load_quarantine_record(archive)
    path.unlink()
    if path.exists():
        raise ContinuityError("legacy sidecar remained active after verified quarantine")
    return {"status": "QUARANTINED_LEGACY", "archive": str(archive), "original_sidecar_sha256": digest(raw), "revision": revision, "observed_build_os": {"revision": observed_revision, **kernel}}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Bounded Build OS continuity sidecar")
    p.add_argument("--root", default="."); p.add_argument("--task-id", required=True); p.add_argument("--revision", type=canonical_revision); p.add_argument("--policy"); p.add_argument("--package-root")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("checkpoint", "bootstrap"):
        x = sub.add_parser(name); x.add_argument("--kind", default="bootstrap" if name == "bootstrap" else "material")
        x.add_argument("--expected-sidecar-hash"); x.add_argument("--accepted-ref"); x.add_argument("--operational-status", default="ACTIVE", choices=["ACTIVE", "BLOCKED", "HANDOFF", "TERMINAL"])
        x.add_argument("--completed-summary", default=""); x.add_argument("--unproven-summary", default=""); x.add_argument("--dirty-intent-summary", default=""); x.add_argument("--blocker-summary", default=""); x.add_argument("--next-safe-action", required=True)
        x.add_argument("--decision", action="append"); x.add_argument("--safety-exception", action="append"); x.add_argument("--evidence", action="append")
        x.add_argument("--documentation-impact", default="UNKNOWN", choices=["YES", "NO", "UNKNOWN"]); x.add_argument("--category", action="append"); x.add_argument("--authority", action="append"); x.add_argument("--semantic-inspection"); x.add_argument("--documentation-rationale")
    sub.add_parser("verify"); sub.add_parser("takeover"); sub.add_parser("docs-check"); sub.add_parser("retire")
    sub.add_parser("working-set", aliases=["capsule"], help="render the bounded read-only model-facing task projection")
    quarantine = sub.add_parser("quarantine-legacy")
    quarantine.add_argument("--tech-lead-authority", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--version"]:
        print(json.dumps({"component": "documentation-handoff-continuity", "version": SKILL_VERSION}, sort_keys=True))
        return 0
    args = parser().parse_args(argv)
    try:
        if args.command in {"checkpoint", "bootstrap"}: result = command_checkpoint(args)
        elif args.command == "verify": result = command_verify(args)
        elif args.command == "takeover": result = command_takeover(args)
        elif args.command == "docs-check": result = command_docs_check(args)
        elif args.command in {"working-set", "capsule"}: result = command_working_set(args)
        elif args.command == "quarantine-legacy": result = command_quarantine_legacy(args)
        else: result = command_retire(args)
        print(json.dumps(result, sort_keys=True)); return 0 if result.get("status") in {"PASS", "SAFE_TO_CONTINUE", "NEEDS_RECONCILIATION", "TARGETED_READ_REQUIRED", "RETIRED", "CLOSED_PENDING_BASELINE_ADVANCE", "QUARANTINED_LEGACY", "HISTORICAL_QUARANTINED"} else 2
    except (ContinuityError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "FAIL", "error": type(exc).__name__, "message": str(exc)})); return 2


if __name__ == "__main__":
    raise SystemExit(main())
