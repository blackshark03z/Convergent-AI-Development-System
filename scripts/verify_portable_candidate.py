#!/usr/bin/env python3
"""Verify extracted candidate bytes from their embedded manifest, without Git."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

from build_simplified_candidate import MANIFEST_NAME, CandidateError, secret_findings


def verify_extracted(root: Path) -> dict:
    root = root.resolve()
    manifest_path = root / MANIFEST_NAME
    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateError("extracted candidate manifest is unavailable or invalid") from exc
    expected = {
        "format", "version", "source_head", "source_tree",
        "excluded_prefixes", "secret_scan", "files",
    }
    if not isinstance(manifest, dict) or set(manifest) != expected:
        raise CandidateError("extracted candidate manifest fields are invalid")
    if manifest["format"] != "buildos.simplified-candidate.v1":
        raise CandidateError("extracted candidate manifest format is invalid")
    if manifest["excluded_prefixes"] != ["legacy/"] or manifest["secret_scan"] != "PASS":
        raise CandidateError("extracted candidate manifest policy is invalid")
    if (root / "legacy").exists():
        raise CandidateError("extracted candidate contains excluded legacy content")
    files = manifest["files"]
    if not isinstance(files, dict) or not files:
        raise CandidateError("extracted candidate manifest has no files")
    payloads: dict[str, bytes] = {}
    for name, expected_file in files.items():
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts or name.startswith("legacy/"):
            raise CandidateError(f"unsafe extracted candidate member: {name}")
        if not isinstance(expected_file, dict) or set(expected_file) != {"sha256", "size"}:
            raise CandidateError(f"invalid extracted candidate checksum row: {name}")
        path = root.joinpath(*pure.parts)
        if not path.is_file():
            raise CandidateError(f"extracted candidate member is missing: {name}")
        data = path.read_bytes()
        if len(data) != expected_file["size"] or hashlib.sha256(data).hexdigest() != expected_file["sha256"]:
            raise CandidateError(f"extracted candidate member checksum mismatch: {name}")
        payloads[name] = data
    if secret_findings(payloads):
        raise CandidateError("extracted candidate secret scan failed")
    return {
        "result": "PASS",
        "manifest_readback": "PASS",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "source_head": manifest["source_head"],
        "source_tree": manifest["source_tree"],
        "file_count": len(payloads),
        "secret_scan": "PASS",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        print(json.dumps(verify_extracted(args.root), sort_keys=True, indent=2))
        return 0
    except (CandidateError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"result": "BLOCK", "message": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
