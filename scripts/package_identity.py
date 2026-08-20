#!/usr/bin/env python3
"""Deterministically prove that portable package identities agree."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

INVARIANT = "PACKAGE_IDENTITY_CONSISTENT"
KERNEL_VERSION = "1.23"
KERNEL_COMMIT = "80be38bf18c559c528477bf7cb7356d340b061a7"


def invoke(path: Path) -> dict[str, object]:
    completed = subprocess.run([sys.executable, str(path), "--version"], text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=30)
    if completed.returncode:
        raise ValueError(f"identity command failed: {path.relative_to(path.parents[3])}")
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise ValueError("identity command did not return an object")
    return value


def validate(root: Path) -> tuple[bool, list[str], dict[str, object]]:
    errors: list[str] = []
    try:
        manifest = json.loads((root / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return False, [f"MANIFEST_INVALID:{exc}"], {}
    lifecycle = manifest.get("project_lifecycle_kit") or {}
    continuity = manifest.get("continuity_skill") or {}
    runtime = manifest.get("runtime_context_epoch_capability") or {}
    expected = {
        "kernel_version": KERNEL_VERSION, "kernel_commit": KERNEL_COMMIT,
        "lifecycle_version": lifecycle.get("version"), "continuity_version": continuity.get("version"),
        "runtime_capability": runtime.get("identity"), "runtime_version": runtime.get("version"),
    }
    if manifest.get("frozen_kernel_version") != "1.23-candidate": errors.append("MANIFEST_KERNEL_VERSION_MISMATCH")
    if manifest.get("frozen_kernel_commit") != KERNEL_COMMIT: errors.append("MANIFEST_KERNEL_COMMIT_MISMATCH")
    if lifecycle.get("bootstrap_skill", {}).get("version") != expected["lifecycle_version"]: errors.append("MANIFEST_LIFECYCLE_SKILL_MISMATCH")
    if continuity.get("name") != "documentation-handoff-continuity" or not expected["continuity_version"]: errors.append("MANIFEST_CONTINUITY_IDENTITY_MISMATCH")
    if lifecycle.get("bootstrap_skill", {}).get("name") != "project-lifecycle-bootstrap" or not expected["lifecycle_version"]: errors.append("MANIFEST_LIFECYCLE_IDENTITY_MISMATCH")
    if runtime.get("name") != "codex-app-server-context-epoch" or not expected["runtime_capability"] or not expected["runtime_version"]:
        errors.append("MANIFEST_RUNTIME_CONTEXT_EPOCH_IDENTITY_MISMATCH")
    scripts = {
        "lifecycle": root / "skills" / "project-lifecycle-bootstrap" / "scripts" / "project_lifecycle.py",
        "continuity": root / "skills" / "documentation-handoff-continuity" / "scripts" / "continuity.py",
        "authority": root / "skills" / "project-lifecycle-bootstrap" / "scripts" / "execution_authority.py",
        "context_epoch": root / "skills" / "project-lifecycle-bootstrap" / "scripts" / "context_epoch.py",
    }
    lifecycle_skill = root / "skills" / "project-lifecycle-bootstrap" / "SKILL.md"
    if not lifecycle_skill.is_file() or "documentation-handoff-continuity v1.1.0" not in lifecycle_skill.read_text(encoding="utf-8", errors="replace"):
        errors.append("LIFECYCLE_SKILL_GUIDANCE_IDENTITY_MISMATCH")
    observed: dict[str, object] = {"manifest": manifest}
    for name, script in scripts.items():
        if not script.is_file():
            errors.append(f"PACKAGED_COMPONENT_MISSING:{name}")
            continue
        try:
            observed[name] = invoke(script)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"COMPONENT_IDENTITY_UNREADABLE:{name}:{exc}")
    lifecycle_identity = observed.get("lifecycle") or {}
    continuity_identity = observed.get("continuity") or {}
    authority_identity = observed.get("authority") or {}
    context_epoch_identity = observed.get("context_epoch") or {}
    if lifecycle_identity.get("component") != "project-lifecycle-kit" or lifecycle_identity.get("version") != expected["lifecycle_version"]:
        errors.append("LIFECYCLE_EXECUTABLE_IDENTITY_MISMATCH")
    if continuity_identity.get("component") != "documentation-handoff-continuity" or continuity_identity.get("version") != expected["continuity_version"]:
        errors.append("CONTINUITY_EXECUTABLE_IDENTITY_MISMATCH")
    if any(authority_identity.get(key) != expected[key] for key in ("kernel_version", "kernel_commit")):
        errors.append("AUTHORITY_KERNEL_IDENTITY_MISMATCH")
    if authority_identity.get("project_lifecycle_kit_version") != expected["lifecycle_version"]:
        errors.append("AUTHORITY_LIFECYCLE_IDENTITY_MISMATCH")
    if authority_identity.get("continuity_skill_version") != expected["continuity_version"]:
        errors.append("AUTHORITY_CONTINUITY_IDENTITY_MISMATCH")
    if context_epoch_identity.get("component") != "context-epoch-runtime" or context_epoch_identity.get("capability") != expected["runtime_capability"] or context_epoch_identity.get("version") != expected["runtime_version"]:
        errors.append("RUNTIME_CONTEXT_EPOCH_EXECUTABLE_IDENTITY_MISMATCH")
    return not errors, errors, observed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify portable package component identity consistency")
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    ok, errors, observed = validate(Path(args.root).resolve())
    print(json.dumps({"status": "PASS" if ok else "FAIL", "invariant": INVARIANT, "errors": errors, "observed_components": sorted(key for key in observed if key != "manifest")}, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
