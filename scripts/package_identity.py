#!/usr/bin/env python3
"""Deterministically prove that portable package identities agree."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

INVARIANT = "PACKAGE_IDENTITY_CONSISTENT"
KERNEL_VERSION = "1.25"
PACKAGE_ID = "build-os-v1.25-rc4-work-loop-execution-runtime-1.0.3-project-lifecycle-kit-1.3.1-continuity-1.1.0-context-epoch-1.0.1"
ARCHIVE_NAME = "Senior_AI_Build_OS_Reusable_v1.25_rc4_work_loop_v1.0.1_execution_runtime_v1.0.3_project_lifecycle_kit_v1.3.1_continuity_v1.1.0_context_epoch_v1.0.1.zip"
RELEASE_EVIDENCE_PATH = "docs/V1.25_RC4_REPORT.md"
RELEASE_REFERENCE = "BUILDOS-V1.25-WORK-LOOP-RC4"
EXPECTED_TEST_COUNT = 307
EXPECTED_TEST_MODULES = [
    "test_acceptance_contract.py", "test_adversarial.py", "test_candidate.py",
    "test_context_epoch.py", "test_continuity_sidecar.py", "test_execution_authority.py",
    "test_execution_runtime.py", "test_facade_opt_in.py", "test_grounding.py",
    "test_lifecycle_lineage.py", "test_package_identity.py", "test_project_lifecycle.py",
    "test_runtime_no_source_delta.py", "test_side_effect_contract.py",
    "test_telemetry_binding.py", "test_vnext_pilots.py", "test_work_contract.py",
    "test_work_loop.py",
]
ALLOWED_SKIP_TESTS = [
    "tests.test_grounding.GroundingTests.test_repo_evidence_alias_cannot_resolve_into_buildos_control_state",
    "tests.test_telemetry_binding.DesktopBindingTests.test_failed_rollover_field_trace_would_bind_via_read_only_handoff_proof",
    "tests.test_telemetry_binding.DesktopBindingTests.test_recovered_field_trace_is_parsed_read_only_with_exact_full_turn_usage",
    "tests.test_telemetry_binding.DesktopBindingTests.test_editorial_request_twenty_replays_without_request_count_rollover",
]
MANIFEST_KEYS = {
    "schema", "package_id", "archive_name", "frozen_kernel_commit",
    "frozen_kernel_version", "release_evidence", "continuity_skill",
    "project_lifecycle_kit", "execution_runtime", "work_loop",
    "trusted_command_registries", "trusted_effect_adapter_contracts",
    "runtime_context_epoch_capability", "field_study", "release_assurance",
    "included",
}
INCLUDED = [
    ".gitattributes", ".gitignore", "FROZEN_KERNEL.sha256",
    "PACKAGE_CONTENTS.sha256", "PACKAGE_MANIFEST.json", "PACKAGE_VALIDATION.json",
    "README.md", "VERSION", "acceptance_contract.py", "adoption", "buildos",
    "config", "docs", "schemas", "scripts", "skills", "templates", "tests",
]


def strict_json_loads(payload: str | bytes) -> object:
    def pairs(rows: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in rows:
            if key in result:
                raise ValueError(f"duplicate JSON object key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise ValueError(f"non-finite JSON constant is forbidden: {value}")

    return json.loads(payload, object_pairs_hook=pairs, parse_constant=reject_constant)


def invoke(path: Path) -> dict[str, object]:
    completed = subprocess.run([sys.executable, str(path), "--version"], text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=30)
    if completed.returncode:
        raise ValueError(f"identity command failed: {path.relative_to(path.parents[3])}")
    value = strict_json_loads(completed.stdout)
    if not isinstance(value, dict):
        raise ValueError("identity command did not return an object")
    return value


def exact_fields(value: object, fields: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == fields


def validate(root: Path) -> tuple[bool, list[str], dict[str, object]]:
    errors: list[str] = []
    try:
        manifest = strict_json_loads((root / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return False, [f"MANIFEST_INVALID:{exc}"], {}
    if not isinstance(manifest, dict):
        return False, ["MANIFEST_SCHEMA_FIELDS_INVALID"], {}
    if set(manifest) != MANIFEST_KEYS:
        errors.append("MANIFEST_SCHEMA_FIELDS_INVALID")
    if manifest.get("schema") != "buildos.portable-package.v1":
        errors.append("MANIFEST_SCHEMA_INVALID")
    if manifest.get("package_id") != PACKAGE_ID:
        errors.append("MANIFEST_PACKAGE_ID_MISMATCH")
    if manifest.get("archive_name") != ARCHIVE_NAME:
        errors.append("MANIFEST_ARCHIVE_NAME_MISMATCH")
    if manifest.get("included") != INCLUDED:
        errors.append("MANIFEST_INCLUDED_ALLOWLIST_MISMATCH")
    kernel_commit = manifest.get("frozen_kernel_commit")
    if not isinstance(kernel_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", kernel_commit):
        errors.append("MANIFEST_KERNEL_COMMIT_INVALID")
        kernel_commit = "INVALID"
    lifecycle_raw = manifest.get("project_lifecycle_kit")
    continuity_raw = manifest.get("continuity_skill")
    runtime_raw = manifest.get("runtime_context_epoch_capability")
    lifecycle = lifecycle_raw if isinstance(lifecycle_raw, dict) else {}
    continuity = continuity_raw if isinstance(continuity_raw, dict) else {}
    runtime = runtime_raw if isinstance(runtime_raw, dict) else {}
    if not exact_fields(lifecycle, {"version", "bootstrap_skill", "mandatory_by_adoption_contract", "kernel_enforced"}):
        errors.append("MANIFEST_LIFECYCLE_FIELDS_INVALID")
    if not exact_fields(lifecycle.get("bootstrap_skill"), {"name", "version"}):
        errors.append("MANIFEST_LIFECYCLE_BOOTSTRAP_FIELDS_INVALID")
    if not exact_fields(continuity, {"name", "version", "mandatory_by_adoption_contract", "kernel_enforced"}):
        errors.append("MANIFEST_CONTINUITY_FIELDS_INVALID")
    if not exact_fields(runtime, {"name", "version", "identity"}):
        errors.append("MANIFEST_RUNTIME_CONTEXT_FIELDS_INVALID")
    if lifecycle.get("mandatory_by_adoption_contract") is not True or lifecycle.get("kernel_enforced") is not False:
        errors.append("MANIFEST_LIFECYCLE_AUTHORITY_FLAGS_INVALID")
    if continuity.get("mandatory_by_adoption_contract") is not True or continuity.get("kernel_enforced") is not False:
        errors.append("MANIFEST_CONTINUITY_AUTHORITY_FLAGS_INVALID")
    expected = {
        "kernel_version": KERNEL_VERSION, "kernel_commit": kernel_commit,
        "lifecycle_version": lifecycle.get("version"), "continuity_version": continuity.get("version"),
        "runtime_capability": runtime.get("identity"), "runtime_version": runtime.get("version"),
    }
    if manifest.get("frozen_kernel_version") != "1.25-rc4": errors.append("MANIFEST_KERNEL_VERSION_MISMATCH")
    try:
        packaged_version = (root / "VERSION").read_text(encoding="ascii").strip()
    except OSError:
        packaged_version = None
    if packaged_version != manifest.get("frozen_kernel_version"):
        errors.append("VERSION_FILE_IDENTITY_MISMATCH")
    try:
        library_source = (root / "buildos" / "__init__.py").read_text(encoding="utf-8")
        version_match = re.search(r'^__version__\s*=\s*"([^"]+)"\s*$', library_source, re.MULTILINE)
        library_version = version_match.group(1) if version_match else None
    except OSError:
        library_version = None
    if library_version != manifest.get("frozen_kernel_version"):
        errors.append("BUILDOS_LIBRARY_IDENTITY_MISMATCH")
    if lifecycle.get("bootstrap_skill", {}).get("version") != expected["lifecycle_version"]: errors.append("MANIFEST_LIFECYCLE_SKILL_MISMATCH")
    if continuity.get("name") != "documentation-handoff-continuity" or expected["continuity_version"] != "1.1.0": errors.append("MANIFEST_CONTINUITY_IDENTITY_MISMATCH")
    if lifecycle.get("bootstrap_skill", {}).get("name") != "project-lifecycle-bootstrap" or expected["lifecycle_version"] != "1.3.1": errors.append("MANIFEST_LIFECYCLE_IDENTITY_MISMATCH")
    if runtime.get("name") != "codex-app-server-context-epoch" or expected["runtime_capability"] != "codex-app-server-context-epoch.v1" or expected["runtime_version"] != "1.0.1":
        errors.append("MANIFEST_RUNTIME_CONTEXT_EPOCH_IDENTITY_MISMATCH")
    execution_runtime_raw = manifest.get("execution_runtime")
    execution_runtime = execution_runtime_raw if isinstance(execution_runtime_raw, dict) else {}
    if not exact_fields(execution_runtime, {"version", "spec_schema", "runtime_schema", "canonical_authority"}):
        errors.append("MANIFEST_EXECUTION_RUNTIME_FIELDS_INVALID")
    if execution_runtime.get("version") != "1.0.3" or execution_runtime.get("spec_schema") != "buildos.execution-spec.v1" or execution_runtime.get("runtime_schema") != "buildos.execution-runtime.v1" or execution_runtime.get("canonical_authority") != "CURRENT_SELECTED_IMMUTABLE_GENERATION":
        errors.append("MANIFEST_EXECUTION_RUNTIME_IDENTITY_MISMATCH")
    work_loop_raw = manifest.get("work_loop")
    work_loop = work_loop_raw if isinstance(work_loop_raw, dict) else {}
    if not exact_fields(work_loop, {"version", "contract_schema", "grounding_schema", "canonical_authority"}):
        errors.append("MANIFEST_WORK_LOOP_FIELDS_INVALID")
    if (
        work_loop.get("version") != "1.0.1"
        or work_loop.get("contract_schema") != "buildos.work-contract.v1"
        or work_loop.get("grounding_schema") != "buildos.grounding-report.v1"
        or work_loop.get("canonical_authority") != "CURRENT_SELECTED_IMMUTABLE_GENERATION"
    ):
        errors.append("MANIFEST_WORK_LOOP_IDENTITY_MISMATCH")
    registries = manifest.get("trusted_command_registries")
    if not isinstance(registries, dict):
        errors.append("MANIFEST_TRUSTED_COMMAND_REGISTRIES_INVALID")
    else:
        for relative, digest in registries.items():
            registry = root / str(relative)
            if (
                not isinstance(relative, str) or not relative
                or Path(relative).is_absolute() or ".." in Path(relative).parts
                or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or not registry.is_file()
                or hashlib.sha256(registry.read_bytes()).hexdigest() != digest
            ):
                errors.append(f"MANIFEST_TRUSTED_COMMAND_REGISTRY_INVALID:{relative}")
    adapter_contracts = manifest.get("trusted_effect_adapter_contracts")
    if not isinstance(adapter_contracts, dict):
        errors.append("MANIFEST_TRUSTED_EFFECT_ADAPTER_CONTRACTS_INVALID")
    else:
        for relative, digest in adapter_contracts.items():
            contract = root / str(relative)
            if (
                not isinstance(relative, str) or not relative
                or Path(relative).is_absolute() or ".." in Path(relative).parts
                or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or not contract.is_file()
                or hashlib.sha256(contract.read_bytes()).hexdigest() != digest
            ):
                errors.append(f"MANIFEST_TRUSTED_EFFECT_ADAPTER_CONTRACT_INVALID:{relative}")
    field_study_raw = manifest.get("field_study")
    field_study = field_study_raw if isinstance(field_study_raw, dict) else {}
    if not exact_fields(field_study, {"version", "authority"}) or field_study.get("authority") != "NON_AUTHORITATIVE":
        errors.append("MANIFEST_FIELD_STUDY_INVALID")
    release_raw = manifest.get("release_evidence")
    release = release_raw if isinstance(release_raw, dict) else {}
    if not isinstance(release, dict) or set(release) != {"path", "status", "reference", "review_target"}:
        errors.append("MANIFEST_RELEASE_EVIDENCE_FIELDS_INVALID")
    if (
        release.get("status") != "CANDIDATE_AWAITING_INDEPENDENT_R3"
        or release.get("review_target") != kernel_commit
        or release.get("path") != RELEASE_EVIDENCE_PATH
        or release.get("reference") != RELEASE_REFERENCE
    ):
        errors.append("MANIFEST_RELEASE_STATUS_UNTRUTHFUL")
    release_path_value = release.get("path")
    release_path = Path(str(release_path_value or ""))
    if (
        not isinstance(release_path_value, str) or not release_path_value
        or release_path.is_absolute() or ".." in release_path.parts
    ):
        errors.append("MANIFEST_RELEASE_EVIDENCE_PATH_INVALID")
    else:
        release_file = root / release_path
        try:
            release_text = release_file.read_text(encoding="utf-8")
        except OSError:
            release_text = ""
        release_lines = release_text.splitlines()
        required_lines = {
            0: "# Build OS v1.25 Work Loop RC4 report",
            2: "Status: `CANDIDATE_AWAITING_INDEPENDENT_R3`",
            4: "Frozen kernel target:",
            5: f"`{kernel_commit}`",
            7: "Package identity:",
            8: f"`{PACKAGE_ID}`",
            10: f"Release evidence reference: `{RELEASE_REFERENCE}`",
        }
        if any(
            len(release_lines) <= index or release_lines[index] != expected_line
            for index, expected_line in required_lines.items()
        ):
            errors.append("MANIFEST_RELEASE_EVIDENCE_UNBOUND")
    assurance_raw = manifest.get("release_assurance")
    assurance = assurance_raw if isinstance(assurance_raw, dict) else {}
    if (
        not isinstance(assurance, dict)
        or set(assurance) != {"expected_test_count", "expected_test_modules", "allowed_skip_tests"}
        or not isinstance(assurance.get("expected_test_count"), int)
        or assurance.get("expected_test_count", 0) < 1
        or not isinstance(assurance.get("expected_test_modules"), list)
        or not assurance.get("expected_test_modules")
        or len(assurance.get("expected_test_modules")) != len(set(assurance.get("expected_test_modules")))
        or not isinstance(assurance.get("allowed_skip_tests"), list)
        or len(assurance.get("allowed_skip_tests")) != len(set(assurance.get("allowed_skip_tests")))
    ):
        errors.append("MANIFEST_RELEASE_ASSURANCE_INVALID")
    elif (
        assurance.get("expected_test_count") != EXPECTED_TEST_COUNT
        or assurance.get("expected_test_modules") != EXPECTED_TEST_MODULES
        or assurance.get("allowed_skip_tests") != ALLOWED_SKIP_TESTS
    ):
        errors.append("MANIFEST_RELEASE_ASSURANCE_IDENTITY_MISMATCH")
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
