#!/usr/bin/env python3
"""Fail-closed Build OS execution-authority preflight for portable adoption."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

KERNEL_VERSION = "1.24"
KERNEL_COMMIT = "955d0710fe0913d1fc0c37496bc217298e5e2299"
LIFECYCLE_KIT_VERSION = "1.3.0"
CONTINUITY_SKILL_VERSION = "1.1.0"
RECORD = ".buildos-authority.json"
LEGACY_EXECUTABLES = ("scripts/ai.py", "scripts/ai_os.py")
EXECUTOR_FILENAMES = {"ai.py", "ai_os.py", "buildos.py", "build_os.py"}
LEGACY_STATE = (".ai/ACTIVE_TASK.md", ".ai/GOAL_STATE.json", ".ai/STATE.md", ".ai/runtime")
WORKER_FILES = ("AGENTS.md", "WORKER_INSTRUCTIONS.md", "prompts/03_WORKER.md")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(errors: list[str], **extra: object) -> int:
    print(json.dumps({"status": "FAIL", "invariant": "SINGLE_ACTIVE_EXECUTION_AUTHORITY", "errors": errors, **extra}, sort_keys=True))
    return 2


def expected_record(package_root: Path) -> dict[str, object]:
    executor = (package_root / "scripts" / "ai.py").resolve()
    admin = (package_root / "scripts" / "ai_os.py").resolve()
    return {
        "schema": "buildos.execution-authority.v1",
        "invariant": "SINGLE_ACTIVE_EXECUTION_AUTHORITY",
        "kernel_version": KERNEL_VERSION,
        "kernel_commit": KERNEL_COMMIT,
        "project_lifecycle_kit_version": LIFECYCLE_KIT_VERSION,
        "continuity_skill_version": CONTINUITY_SKILL_VERSION,
        "package_root": str(package_root.resolve()),
        "canonical_executor": str(executor),
        "canonical_admin_executor": str(admin),
        "canonical_executor_sha256": sha256(executor),
        "resolution_rule": "python <package_root>/scripts/ai.py --root <project-root> <lifecycle-command>; never fall back to project-local or PATH executors",
        "legacy_archive_is_provenance_only": True,
    }


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
        expected = expected_record(package_root)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return fail([f"AUTHORITY_RECORD_INVALID: {exc}"])
    errors: list[str] = []
    for key in expected:
        if record.get(key) != expected[key]:
            errors.append(f"AUTHORITY_IDENTITY_MISMATCH: {key}")
    executors: set[str] = set()
    for item in LEGACY_EXECUTABLES:
        if (root / item).is_file():
            executors.add(item)
    for item in root.rglob("*"):
        relative = item.relative_to(root)
        if not item.is_file() or item.name not in EXECUTOR_FILENAMES or any(part in {".git", "archive", "archives"} for part in relative.parts):
            continue
        executors.add(relative.as_posix())
    for item in sorted(executors):
        errors.append(f"LEGACY_EXECUTABLE_CALLABLE: {item}")
    for item in LEGACY_STATE:
        if (root / item).exists():
            errors.append(f"LEGACY_STATE_AUTHORITATIVE: {item}")
    legacy_version = re.compile(r"(?i)build\s*os\s*v1\.(?:[0-9]|1[0-9]|20|21)\b")
    for relative in WORKER_FILES:
        path = root / relative
        if path.is_file() and legacy_version.search(path.read_text(encoding="utf-8", errors="replace")):
            errors.append(f"CONFLICTING_WORKER_INSTRUCTION: {relative}")
    if errors:
        return fail(errors, canonical_executor=expected["canonical_executor"], cleanup_required=any(error.startswith(("LEGACY_EXECUTABLE_CALLABLE", "LEGACY_STATE_AUTHORITATIVE", "CONFLICTING_WORKER_INSTRUCTION")) for error in errors))
    print(json.dumps({"status": "PASS", "invariant": "SINGLE_ACTIVE_EXECUTION_AUTHORITY", "canonical_executor": expected["canonical_executor"], "kernel_commit": KERNEL_COMMIT, "legacy_archive_ignored": True}, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--version"]:
        print(json.dumps({"component": "execution-authority", "kernel_commit": KERNEL_COMMIT, "kernel_version": KERNEL_VERSION, "project_lifecycle_kit_version": LIFECYCLE_KIT_VERSION, "continuity_skill_version": CONTINUITY_SKILL_VERSION}, sort_keys=True))
        return 0
    parser = argparse.ArgumentParser(description="Build OS v1.24 execution authority preflight")
    parser.add_argument("--root", required=True)
    parser.add_argument("--package-root")
    parser.add_argument("command", choices=("write-record", "check"))
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.command == "write-record":
        if not args.package_root:
            return fail(["PACKAGE_ROOT_REQUIRED"])
        record = expected_record(Path(args.package_root))
        (root / RECORD).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "record": str(root / RECORD), "invariant": "SINGLE_ACTIVE_EXECUTION_AUTHORITY"}, sort_keys=True))
        return 0
    return check(root)


if __name__ == "__main__":
    raise SystemExit(main())
