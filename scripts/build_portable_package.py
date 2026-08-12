#!/usr/bin/env python3
"""Create a new, provenance-labelled portable export without replacing prior ZIPs."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "PACKAGE_MANIFEST.json"
PACKAGE_STORE = Path(os.environ.get("BUILDOS_PACKAGE_STORE", r"D:\Youtube\_packages"))
OUT = PACKAGE_STORE / "Senior_AI_Build_OS_Reusable_v1.22_project_lifecycle_kit_v1.0.4_continuity_v1.0.4_working_state_capsule_r2.zip"
EXCLUDE = {"__pycache__", ".git", ".buildos", "_proof_tmp"}
VALIDATION = ROOT / "PACKAGE_VALIDATION.json"
CONTENTS = ROOT / "PACKAGE_CONTENTS.sha256"
FROZEN_KERNEL_COMMIT = "e41ca10826b32b2d46a3b859345f734c113e00ae"
FROZEN_KERNEL = ROOT / "FROZEN_KERNEL.sha256"


def eligible(path: Path) -> bool:
    return path.is_file() and path not in {VALIDATION, CONTENTS} and not any(part in EXCLUDE for part in path.relative_to(ROOT).parts)


def _run(command: list[str], *, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout)


def frozen_kernel_matches() -> bool:
    try:
        expected = {
            line.split("  ", 1)[1]: line.split("  ", 1)[0]
            for line in FROZEN_KERNEL.read_text(encoding="ascii").splitlines() if line
        }
        observed = {
            path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (ROOT / "buildos").rglob("*") if path.is_file() and "__pycache__" not in path.parts
        }
    except (OSError, IndexError):
        return False
    return observed == expected


def validate() -> dict:
    command = [sys.executable, "-m", "unittest", "tests.test_project_lifecycle", "tests.test_continuity_sidecar"]
    completed = _run(command)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    result = {
        "schema": "buildos.portable-validation-evidence.v1", "command": command,
        "exit_code": completed.returncode, "output_tail": (completed.stdout + completed.stderr)[-4000:],
        "frozen_kernel_byte_identical": frozen_kernel_matches(),
        "manifest_valid": manifest.get("frozen_kernel_commit") == FROZEN_KERNEL_COMMIT
            and manifest.get("project_lifecycle_kit", {}).get("version") == "1.0.4"
            and manifest.get("continuity_skill", {}).get("version") == "1.0.4",
    }
    VALIDATION.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if completed.returncode or not result["frozen_kernel_byte_identical"] or not result["manifest_valid"]:
        raise RuntimeError("portable validation failed; inspect PACKAGE_VALIDATION.json")
    return result


def content_checksums() -> None:
    rows = []
    for path in sorted(ROOT.rglob("*")):
        if eligible(path):
            rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}")
    CONTENTS.write_text("\n".join(rows) + "\n", encoding="utf-8")


def verify_zip(manifest: dict) -> dict:
    if not OUT.parent.is_dir():
        raise RuntimeError(f"durable package store does not exist: {OUT.parent}")
    with zipfile.ZipFile(OUT, "r") as archive:
        names = archive.namelist()
        if any(any(part in EXCLUDE for part in Path(name).parts) for name in names):
            raise RuntimeError("ZIP contains excluded runtime or transient content")
        if "PACKAGE_MANIFEST.json" not in names or "PACKAGE_CONTENTS.sha256" not in names:
            raise RuntimeError("ZIP is missing manifest or checksum index")
        zipped_manifest = json.loads(archive.read("PACKAGE_MANIFEST.json"))
        if zipped_manifest != manifest:
            raise RuntimeError("ZIP manifest does not match package manifest")
        kernel_hashes = {
            line.split("  ", 1)[1]: line.split("  ", 1)[0]
            for line in FROZEN_KERNEL.read_text(encoding="ascii").splitlines() if line
        }
        for name, expected_hash in kernel_hashes.items():
            if name not in names:
                raise RuntimeError(f"ZIP missing frozen kernel file: {name}")
            if hashlib.sha256(archive.read(name)).hexdigest() != expected_hash:
                raise RuntimeError(f"ZIP frozen kernel mismatch: {name}")
        for name in names:
            if name == "scripts/build_portable_package.py":
                continue  # The verifier carries its own detector signatures as source literals.
            payload = archive.read(name)
            if (b"-----BEGIN " in payload and b"PRIVATE KEY-----" in payload) or re.search(rb"\b(?:sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b", payload):
                raise RuntimeError(f"ZIP contains secret-like material: {name}")
    return {"zip_opens": True, "manifest_valid": True, "frozen_kernel_byte_identical": True, "excluded_runtime_content": True, "secret_scan": True}


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    validation = validate()
    content_checksums()
    if OUT.exists():
        raise RuntimeError(f"refusing to overwrite previous package: {OUT}")
    with zipfile.ZipFile(OUT, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or any(part in EXCLUDE for part in path.relative_to(ROOT).parts):
                continue
            archive.write(path, path.relative_to(ROOT).as_posix())
    checks = verify_zip(manifest)
    print(json.dumps({"status": "PASS", "zip": str(OUT), "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(), "package_id": manifest["package_id"], "frozen_kernel_commit": manifest["frozen_kernel_commit"], "validation_exit_code": validation["exit_code"], "content_checksums": str(CONTENTS), **checks}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
