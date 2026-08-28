#!/usr/bin/env python3
"""Read back a simplified candidate and verify exact Git/package identity."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from build_simplified_candidate import (
    MANIFEST_NAME,
    CandidateError,
    git,
    git_blob,
    secret_findings,
)


def verify(archive: Path, source_root: Path) -> dict:
    archive = archive.resolve()
    source_root = source_root.resolve()
    if git(source_root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise CandidateError("candidate source worktree is not clean")
    with zipfile.ZipFile(archive, "r") as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)) or MANIFEST_NAME not in names:
            raise CandidateError("candidate member set is duplicate or lacks its manifest")
        if any(name.startswith("/") or ".." in Path(name).parts for name in names):
            raise CandidateError("candidate contains unsafe member path")
        manifest_bytes = bundle.read(MANIFEST_NAME)
        manifest = json.loads(manifest_bytes)
        if manifest.get("format") != "buildos.simplified-candidate.v1":
            raise CandidateError("candidate manifest format is invalid")
        if manifest.get("excluded_prefixes") != ["legacy/"]:
            raise CandidateError("candidate legacy exclusion declaration is invalid")
        if any(name.startswith("legacy/") for name in manifest["files"]):
            raise CandidateError("candidate contains legacy production members")
        expected_names = sorted([*manifest["files"], MANIFEST_NAME])
        if sorted(names) != expected_names:
            raise CandidateError("candidate members do not match manifest")
        payloads = {name: bundle.read(name) for name in manifest["files"]}
    for name, expected in manifest["files"].items():
        data = payloads[name]
        if len(data) != expected["size"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
            raise CandidateError(f"candidate member checksum mismatch: {name}")
    if secret_findings(payloads):
        raise CandidateError("candidate readback secret scan failed")
    head = git(source_root, "rev-parse", "HEAD")
    tree = git(source_root, "rev-parse", "HEAD^{tree}")
    if head != manifest["source_head"] or tree != manifest["source_tree"]:
        raise CandidateError("candidate source identity does not match current source")
    for name, data in payloads.items():
        if git_blob(source_root, head, name) != data:
            raise CandidateError(f"candidate member differs from exact Git blob: {name}")
    return {
        "result": "PASS",
        "archive": str(archive),
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "source_head": head,
        "source_tree": tree,
        "file_count": len(payloads),
        "member_count": len(payloads) + 1,
        "secret_scan": "PASS",
        "git_blob_readback": "PASS",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(verify(args.archive, args.source_root), sort_keys=True, indent=2))
        return 0
    except (CandidateError, OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(json.dumps({"result": "BLOCK", "message": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
