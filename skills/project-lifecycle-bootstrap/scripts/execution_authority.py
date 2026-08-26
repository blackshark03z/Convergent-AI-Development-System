#!/usr/bin/env python3
"""Fail-closed Build OS execution-authority preflight for portable adoption."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from legacy_authority_bridge import (
    BridgeError as LegacyBridgeError,
    authority_binding,
    identify_legacy_executors,
)

KERNEL_VERSION = "1.25"
LIFECYCLE_KIT_VERSION = "1.4.1"
CONTINUITY_SKILL_VERSION = "1.1.0"
RECORD = ".buildos-authority.json"
LEGACY_STATE = (".ai/ACTIVE_TASK.md", ".ai/GOAL_STATE.json", ".ai/STATE.md", ".ai/runtime")
WORKER_FILES = ("AGENTS.md", "WORKER_INSTRUCTIONS.md", "prompts/03_WORKER.md")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def kernel_commit(package_root: Path) -> str:
    manifest = json.loads((package_root / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    value = manifest.get("frozen_kernel_commit") if isinstance(manifest, dict) else None
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("package manifest frozen_kernel_commit is invalid")
    return value


def fail(errors: list[str], **extra: object) -> int:
    print(json.dumps({"status": "FAIL", "invariant": "SINGLE_ACTIVE_EXECUTION_AUTHORITY", "errors": errors, **extra}, sort_keys=True))
    return 2


def expected_record(root: Path, package_root: Path) -> dict[str, object]:
    executor = (package_root / "scripts" / "ai.py").resolve()
    admin = (package_root / "scripts" / "ai_os.py").resolve()
    record: dict[str, object] = {
        "schema": "buildos.execution-authority.v1",
        "invariant": "SINGLE_ACTIVE_EXECUTION_AUTHORITY",
        "kernel_version": KERNEL_VERSION,
        "kernel_commit": kernel_commit(package_root),
        "project_lifecycle_kit_version": LIFECYCLE_KIT_VERSION,
        "continuity_skill_version": CONTINUITY_SKILL_VERSION,
        "package_root": str(package_root.resolve()),
        "canonical_executor": str(executor),
        "canonical_admin_executor": str(admin),
        "canonical_executor_sha256": sha256(executor),
        "resolution_rule": "python <package_root>/scripts/ai.py --root <project-root> <lifecycle-command>; never fall back to project-local or PATH executors",
        "legacy_archive_is_provenance_only": True,
    }
    transition = authority_binding(root, package_root)
    if transition is not None:
        record["legacy_transition"] = transition
    return record


def load_record(root: Path) -> dict[str, object]:
    path = root / RECORD
    if not path.is_file():
        raise ValueError(f"missing authority record: {RECORD}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("authority record must be a JSON object")
    return value


def check(root: Path) -> int:
    try:
        record = load_record(root)
        package_root = Path(str(record["package_root"])).resolve()
        expected = expected_record(root, package_root)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, LegacyBridgeError) as exc:
        return fail([f"AUTHORITY_RECORD_INVALID: {exc}"])
    errors: list[str] = []
    if set(record) != set(expected):
        errors.append("AUTHORITY_RECORD_FIELD_SET_MISMATCH")
    for key in expected:
        if record.get(key) != expected[key]:
            errors.append(f"AUTHORITY_IDENTITY_MISMATCH: {key}")
    executor_inventory = identify_legacy_executors(root)
    for item in executor_inventory["executors"]:
        errors.append(f"LEGACY_EXECUTABLE_CALLABLE: {item}")
    for item in executor_inventory["ambiguous"]:
        errors.append(f"AMBIGUOUS_EXECUTOR_CANDIDATE: {item}")
    for item in LEGACY_STATE:
        if (root / item).exists():
            errors.append(f"LEGACY_STATE_AUTHORITATIVE: {item}")
    legacy_version = re.compile(r"(?i)build\s*os\s*v1\.(?:[0-9]|1[0-9]|20|21)\b")
    for relative in WORKER_FILES:
        path = root / relative
        if path.is_file() and legacy_version.search(path.read_text(encoding="utf-8", errors="replace")):
            errors.append(f"CONFLICTING_WORKER_INSTRUCTION: {relative}")
    if errors:
        return fail(errors, canonical_executor=expected["canonical_executor"], cleanup_required=any(error.startswith(("LEGACY_EXECUTABLE_CALLABLE", "AMBIGUOUS_EXECUTOR_CANDIDATE", "LEGACY_STATE_AUTHORITATIVE", "CONFLICTING_WORKER_INSTRUCTION")) for error in errors))
    print(json.dumps({"status": "PASS", "invariant": "SINGLE_ACTIVE_EXECUTION_AUTHORITY", "canonical_executor": expected["canonical_executor"], "kernel_commit": expected["kernel_commit"], "legacy_archive_ignored": True}, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--version"]:
        try:
            commit = kernel_commit(Path(__file__).resolve().parents[3])
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return fail([f"PACKAGE_MANIFEST_INVALID: {exc}"])
        print(json.dumps({"component": "execution-authority", "kernel_commit": commit, "kernel_version": KERNEL_VERSION, "project_lifecycle_kit_version": LIFECYCLE_KIT_VERSION, "continuity_skill_version": CONTINUITY_SKILL_VERSION}, sort_keys=True))
        return 0
    parser = argparse.ArgumentParser(description="Build OS v1.25 execution authority preflight")
    parser.add_argument("--root", required=True)
    parser.add_argument("--package-root")
    parser.add_argument("command", choices=("write-record", "check"))
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.command == "write-record":
        if not args.package_root:
            return fail(["PACKAGE_ROOT_REQUIRED"])
        try:
            record = expected_record(root, Path(args.package_root))
        except (OSError, ValueError, KeyError, json.JSONDecodeError, LegacyBridgeError) as exc:
            return fail([f"LEGACY_TRANSITION_INVALID: {exc}"])
        (root / RECORD).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "record": str(root / RECORD), "invariant": "SINGLE_ACTIVE_EXECUTION_AUTHORITY"}, sort_keys=True))
        return 0
    return check(root)


if __name__ == "__main__":
    raise SystemExit(main())
