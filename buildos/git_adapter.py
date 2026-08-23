"""Git observations used as evidence anchors, never lifecycle authority."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import fnmatch
import hashlib
import json
from typing import Any


CONTROL_PREFIXES = (".buildos/",)


def _run(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "git command failed").strip())
    return proc


def relation(root: Path | str, ancestor: str | None, descendant: str | None) -> str:
    if not ancestor or not descendant:
        return "UNKNOWN"
    if ancestor == descendant:
        return "SAME"
    proc = _run(Path(root), "merge-base", "--is-ancestor", ancestor, descendant, check=False)
    if proc.returncode == 0:
        return "DESCENDANT"
    if proc.returncode == 1:
        return "DIVERGED"
    return "UNKNOWN"


def resolve_commit(root: Path | str, value: str) -> str:
    """Resolve an explicit commit-ish to one full commit SHA or fail closed."""
    raw = str(value).strip()
    if not raw:
        raise RuntimeError("commit reference is required")
    proc = _run(Path(root), "rev-parse", "--verify", f"{raw}^{{commit}}", check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"commit reference does not resolve: {raw}")
    return proc.stdout.strip()


def commit_anchor(root: Path | str, commit: str) -> dict[str, Any]:
    """Return a bounded immutable Git anchor for a resolved commit."""
    root = Path(root).resolve()
    sha = resolve_commit(root, commit)
    top = _run(root, "rev-parse", "--show-toplevel", check=True).stdout.strip()
    tree = _run(root, "rev-parse", f"{sha}^{{tree}}", check=True).stdout.strip()
    return {
        "available": True,
        "root": str(Path(top).resolve()),
        "branch": None,
        "head": sha,
        "tree": tree,
        "dirty": False,
    }


def changed_paths(root: Path | str, older: str | None, newer: str | None, *, diff_filter: str | None = None) -> list[str]:
    if not older or not newer or older == newer:
        return []
    args = ["diff", "--name-only", "--no-renames"]
    if diff_filter:
        args.append(f"--diff-filter={diff_filter}")
    args.extend([f"{older}..{newer}", "--"])
    proc = _run(Path(root), *args, check=False)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "git diff observation failed").strip())
    return sorted({line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()})


def dependency_fingerprint(root: Path | str, commit: str, patterns: list[str]) -> str:
    """Hash exact Git blob identities selected by semantic claim patterns."""
    sha = resolve_commit(root, commit)
    proc = _run(Path(root), "ls-tree", "-r", "--full-tree", sha, check=True)
    selected: list[dict[str, str]] = []
    for line in proc.stdout.splitlines():
        metadata, separator, raw_path = line.partition("\t")
        if not separator:
            continue
        parts = metadata.split()
        if len(parts) != 3:
            continue
        mode, kind, blob = parts
        path = raw_path.replace("\\", "/")
        if path.startswith(".buildos/"):
            continue
        if any(fnmatch.fnmatchcase(path, pattern) or path == pattern.rstrip("/") or path.startswith(pattern.rstrip("/") + "/") for pattern in patterns):
            selected.append({"path": path, "mode": mode, "kind": kind, "blob": blob})
    payload = {"commit_tree_claim_patterns": list(patterns), "selected": sorted(selected, key=lambda row: row["path"])}
    return hashlib.sha256((json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")).hexdigest()


def _dirty_paths(root: Path) -> list[str]:
    proc = _run(root, "status", "--porcelain=v1", "--untracked-files=all", check=False)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "git status observation failed").strip())
    result: list[str] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        result.append(path.replace("\\", "/"))
    return sorted(set(result))


def _control_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in CONTROL_PREFIXES)


def tracked_control_paths(root: Path | str) -> list[str]:
    proc = _run(Path(root), "ls-files", "--", ".buildos", check=False)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "git tracked-control observation failed").strip())
    return sorted({line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()})


def snapshot(
    root: Path | str,
    *,
    base_sha: str | None = None,
    product_sha: str | None = None,
    validated_sha: str | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    top = _run(root, "rev-parse", "--show-toplevel", check=False)
    if top.returncode != 0:
        return {
            "available": False,
            "root": None,
            "branch": None,
            "head": None,
            "tree": None,
            "dirty": False,
            "product_dirty": False,
            "dirty_paths": [],
            "relation_to_base": "UNKNOWN",
            "relation_to_product": "UNKNOWN",
            "relation_to_validated": "UNKNOWN",
            "changes_since_validated": [],
        }
    git_root = Path(top.stdout.strip()).resolve()
    head_proc = _run(root, "rev-parse", "HEAD", check=False)
    if head_proc.returncode != 0:
        return {"available": False, "root": str(git_root), "head": None, "tree": None, "dirty": False, "product_dirty": False, "dirty_paths": []}
    head = head_proc.stdout.strip()
    branch_proc = _run(root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    ignorecase_proc = _run(root, "config", "--bool", "core.ignorecase", check=False)
    case_insensitive = (
        os.name == "nt"
        or sys.platform == "darwin"
        or (ignorecase_proc.returncode == 0 and ignorecase_proc.stdout.strip().lower() == "true")
    )
    tree = _run(root, "rev-parse", f"{head}^{{tree}}", check=True).stdout.strip()
    dirty_paths = _dirty_paths(root)
    product_dirty_paths = [path for path in dirty_paths if not _control_path(path)]
    since_validated = changed_paths(root, validated_sha, head)
    product_changes = [path for path in since_validated if not _control_path(path)]
    since_base = [path for path in changed_paths(root, base_sha, head) if not _control_path(path)]
    since_product = [path for path in changed_paths(root, product_sha, head) if not _control_path(path)]
    deletions_since_base = [path for path in changed_paths(root, base_sha, head, diff_filter="D") if not _control_path(path)]
    type_changes_since_base = [path for path in changed_paths(root, base_sha, head, diff_filter="T") if not _control_path(path)]
    tracked_control = tracked_control_paths(root)
    return {
        "available": True,
        "root": str(git_root),
        "branch": branch_proc.stdout.strip() if branch_proc.returncode == 0 else "DETACHED",
        "case_insensitive_paths": case_insensitive,
        "head": head,
        "tree": tree,
        "dirty": bool(dirty_paths),
        "product_dirty": bool(product_dirty_paths),
        "dirty_paths": dirty_paths,
        "product_dirty_paths": product_dirty_paths,
        "relation_to_base": relation(root, base_sha, head),
        "relation_to_product": relation(root, product_sha, head),
        "relation_to_validated": relation(root, validated_sha, head),
        "changes_since_base": since_base,
        "deletions_since_base": deletions_since_base,
        "type_changes_since_base": type_changes_since_base,
        "changes_since_product": since_product,
        "changes_since_validated": product_changes,
        "tracked_control_paths": tracked_control,
    }


def ensure_control_excluded(root: Path | str) -> dict[str, Any]:
    """Put generated control state in Git's local exclude, not product history."""
    root = Path(root).resolve()
    proc = _run(root, "rev-parse", "--git-path", "info/exclude", check=False)
    if proc.returncode != 0:
        return {"status": "GIT_UNAVAILABLE", "path": None, "changed": False}
    raw = proc.stdout.strip()
    exclude = Path(raw)
    if not exclude.is_absolute():
        exclude = (root / exclude).resolve()
    exclude.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    lines = [line.strip() for line in existing.splitlines()]
    if ".buildos/" in lines or "/.buildos/" in lines:
        return {"status": "EXCLUDED", "path": str(exclude), "changed": False}
    with exclude.open("a", encoding="utf-8", newline="\n") as handle:
        if existing and not existing.endswith(("\n", "\r")):
            handle.write("\n")
        handle.write(".buildos/\n")
        handle.flush()
        os.fsync(handle.fileno())
    return {"status": "EXCLUDED", "path": str(exclude), "changed": True}
