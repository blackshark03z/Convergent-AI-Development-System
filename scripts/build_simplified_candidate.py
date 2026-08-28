#!/usr/bin/env python3
"""Build one deterministic simplified candidate from an exact clean Git HEAD."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "CANDIDATE_MANIFEST.json"
EXCLUDED_PREFIXES = ("legacy/",)
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{24,}"),
    re.compile(
        rb"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"\r\n]{12,}['\"]",
    ),
)


class CandidateError(RuntimeError):
    pass


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=root, text=True, encoding="utf-8",
        errors="replace", capture_output=True, timeout=60,
    )
    if proc.returncode:
        raise CandidateError((proc.stderr or proc.stdout).strip())
    return proc.stdout.strip()


def source_files(root: Path, head: str) -> list[str]:
    tracked = [
        path.replace("\\", "/")
        for path in git(root, "ls-tree", "-r", "--name-only", head).splitlines()
        if path
    ]
    if MANIFEST_NAME in tracked:
        raise CandidateError(
            "source checkout must not track an embedded candidate manifest",
        )
    result = [
        path for path in tracked if not path.startswith(EXCLUDED_PREFIXES)
    ]
    if not result or any(path.startswith(".git/") or "../" in path for path in result):
        raise CandidateError("candidate source file set is invalid")
    return sorted(result)


def git_blob(root: Path, head: str, path: str) -> bytes:
    proc = subprocess.run(
        ["git", "show", f"{head}:{path}"], cwd=root,
        capture_output=True, timeout=60,
    )
    if proc.returncode:
        raise CandidateError(proc.stderr.decode("utf-8", "replace").strip())
    return proc.stdout


def secret_findings(files: dict[str, bytes]) -> list[str]:
    findings: list[str] = []
    for path, data in files.items():
        for index, pattern in enumerate(SECRET_PATTERNS, start=1):
            if pattern.search(data):
                findings.append(f"{path}:pattern-{index}")
    return sorted(findings)


def build(root: Path, output_dir: Path) -> dict:
    root = root.resolve()
    output_dir = output_dir.resolve(strict=False)
    try:
        if os.path.commonpath([str(root), str(output_dir)]) == str(root):
            raise CandidateError("candidate output directory must be outside the source worktree")
    except ValueError as exc:
        raise CandidateError("candidate output directory is incompatible with source worktree") from exc
    if git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise CandidateError("candidate source worktree must be clean")
    head = git(root, "rev-parse", "HEAD")
    tree = git(root, "rev-parse", "HEAD^{tree}")
    version = git_blob(root, head, "VERSION").decode("utf-8").strip()
    paths = source_files(root, head)
    files = {path: git_blob(root, head, path) for path in paths}
    findings = secret_findings(files)
    if findings:
        raise CandidateError(f"candidate secret scan failed: {findings}")
    rows = {
        path: {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
        for path, data in files.items()
    }
    manifest = {
        "format": "buildos.simplified-candidate.v1",
        "version": version,
        "source_head": head,
        "source_tree": tree,
        "excluded_prefixes": list(EXCLUDED_PREFIXES),
        "secret_scan": "PASS",
        "files": rows,
    }
    manifest_bytes = (json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ) + "\n").encode("utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_version = re.sub(r"[^A-Za-z0-9_.-]+", "-", version)
    archive = output_dir / f"build-os-{safe_version}-{head[:12]}.zip"
    receipt = archive.with_suffix(".receipt.json")
    existing = sorted(output_dir.glob("build-os-simplified-rc1-*.zip"))
    if existing or archive.exists() or receipt.exists():
        raise CandidateError(f"candidate already exists: {[str(path) for path in existing] or [str(archive)]}")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path, data in [*(files.items()), (MANIFEST_NAME, manifest_bytes)]:
            info = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data)
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    receipt_value = {
        "format": "buildos.simplified-candidate-receipt.v1",
        "archive": archive.name,
        "archive_sha256": archive_sha,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "source_head": head,
        "source_tree": tree,
        "file_count": len(files),
    }
    receipt.write_text(json.dumps(
        receipt_value, ensure_ascii=False, sort_keys=True, indent=2,
    ) + "\n", encoding="utf-8", newline="\n")
    return {**receipt_value, "archive_path": str(archive), "receipt_path": str(receipt)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build(args.root, args.output_dir), sort_keys=True, indent=2))
        return 0
    except (CandidateError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(json.dumps({"result": "BLOCK", "message": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
