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
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        env=environment,
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


def _dirty_entries(root: Path) -> list[dict[str, str]]:
    proc = _run(
        root, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "git status observation failed").strip())
    result: list[dict[str, str]] = []
    for record in proc.stdout.split("\0"):
        if len(record) < 4:
            continue
        result.append({"status": record[:2], "path": record[3:].replace("\\", "/")})
    return sorted(result, key=lambda row: (row["path"], row["status"]))


def _path_identity(root: Path, path: str) -> dict[str, Any]:
    target = root / path
    try:
        if target.is_symlink():
            payload = os.readlink(target).encode("utf-8", "surrogatepass")
            return {"kind": "SYMLINK", "sha256": hashlib.sha256(payload).hexdigest(), "size": len(payload)}
        if target.is_file():
            digest = hashlib.sha256()
            size = 0
            with target.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
                    size += len(chunk)
            return {"kind": "FILE", "sha256": digest.hexdigest(), "size": size}
        if target.is_dir():
            return {"kind": "DIRECTORY", "sha256": None, "size": None}
        if not target.exists():
            return {"kind": "ABSENT", "sha256": None, "size": None}
        return {"kind": "SPECIAL", "sha256": None, "size": None}
    except OSError as exc:
        raise RuntimeError(f"cannot fingerprint in-progress product path: {path}") from exc


def _worktree_fingerprint(
    root: Path,
    entries: list[dict[str, str]],
    *,
    include_control: bool = False,
) -> str:
    payload = {
        "entries": [
            {**entry, "identity": _path_identity(root, entry["path"])}
            for entry in entries
            if include_control or not _control_path(entry["path"])
        ],
    }
    return hashlib.sha256(
        (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    ).hexdigest()


def _worktree_changed_paths(root: Path, *, diff_filter: str) -> list[str]:
    proc = _run(
        root, "diff", "--name-only", "--no-renames", f"--diff-filter={diff_filter}", "HEAD", "--",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "git worktree diff observation failed").strip())
    return sorted({line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()})


def _raw_type_changed_paths(root: Path, *comparison: str) -> list[str]:
    """Read Git mode changes directly, including staged index-only changes.

    Filesystem symlink support differs by platform. Git's raw old/new modes are
    the portable authority for an index or worktree type transition.
    """
    proc = _run(
        root, "diff", "--raw", "-z", "--no-renames", *comparison,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "git type-change observation failed").strip())
    tokens = proc.stdout.split("\0")
    result: set[str] = set()
    index = 0
    while index + 1 < len(tokens):
        metadata = tokens[index]
        path = tokens[index + 1]
        index += 2
        if not metadata.startswith(":") or not path:
            continue
        fields = metadata[1:].split()
        if len(fields) < 5:
            raise RuntimeError("git raw type-change observation is malformed")
        old_mode, new_mode, _old_blob, _new_blob, status = fields[:5]
        mode_changed = (
            old_mode != new_mode
            and old_mode != "000000"
            and new_mode != "000000"
        )
        if status.startswith("T") or mode_changed:
            result.add(path.replace("\\", "/"))
    return sorted(result)


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


def boundary_snapshot(root: Path | str, base: str) -> dict[str, Any]:
    """Observe the exact live Git delta used by the thin boundary guard.

    This is intentionally read-only.  It reports the immutable commit/tree
    identity plus fingerprints for the live index and dirty worktree; it does
    not create a grant, snapshot record, lock, or runtime directory.
    """
    requested_root = Path(root).resolve()
    top = _run(requested_root, "rev-parse", "--show-toplevel", check=False)
    if top.returncode != 0:
        raise RuntimeError("repository root is not an observable Git worktree")
    git_root = Path(top.stdout.strip()).resolve()
    if os.path.normcase(str(requested_root)) != os.path.normcase(str(git_root)):
        raise RuntimeError(f"repository root must be the Git top-level: {git_root}")

    base_sha = resolve_commit(git_root, base)
    observed = snapshot(git_root, base_sha=base_sha)
    if not observed.get("available") or not observed.get("head"):
        raise RuntimeError("current Git HEAD is not observable")

    committed_paths = changed_paths(git_root, base_sha, observed["head"])
    committed_deletions = changed_paths(
        git_root, base_sha, observed["head"], diff_filter="D",
    )
    committed_type_changes = changed_paths(
        git_root, base_sha, observed["head"], diff_filter="T",
    )
    dirty_entries = _dirty_entries(git_root)
    dirty_paths = sorted({entry["path"] for entry in dirty_entries})
    worktree_deletions = _worktree_changed_paths(git_root, diff_filter="D")
    index_type_changes = _raw_type_changed_paths(
        git_root, "--cached", "HEAD", "--",
    )
    worktree_type_changes = _raw_type_changed_paths(git_root, "--")

    index = _run(git_root, "ls-files", "--stage", "-z", check=True).stdout
    result = {
        "root": str(git_root),
        "branch": observed["branch"],
        "base": base_sha,
        "head": observed["head"],
        "tree": observed["tree"],
        "relation_to_base": observed["relation_to_base"],
        "case_insensitive_paths": observed["case_insensitive_paths"],
        "dirty": bool(dirty_entries),
        "dirty_entries": dirty_entries,
        "committed_paths": committed_paths,
        "dirty_paths": dirty_paths,
        "changed_paths": sorted({*committed_paths, *dirty_paths}),
        "deleted_paths": sorted({*committed_deletions, *worktree_deletions}),
        "type_changed_paths": sorted({
            *committed_type_changes, *index_type_changes, *worktree_type_changes,
        }),
        "index_type_changed_paths": index_type_changes,
        "worktree_type_changed_paths": worktree_type_changes,
        "tracked_control_paths": tracked_control_paths(git_root),
        "changed_control_paths": sorted({
            path for path in {*committed_paths, *dirty_paths}
            if _control_path(path)
        }),
        "index_fingerprint": hashlib.sha256(
            index.encode("utf-8", "surrogatepass")
        ).hexdigest(),
        "worktree_fingerprint": _worktree_fingerprint(
            git_root, dirty_entries, include_control=True,
        ),
    }
    identity = {
        key: result[key] for key in (
            "root", "branch", "base", "head", "tree", "relation_to_base",
            "dirty_entries", "committed_paths", "deleted_paths",
            "type_changed_paths", "tracked_control_paths",
            "index_fingerprint", "worktree_fingerprint",
        )
    }
    result["observed_state_digest"] = hashlib.sha256(
        (json.dumps(
            identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ) + "\n").encode("utf-8")
    ).hexdigest()
    return result


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
    dirty_entries = _dirty_entries(root)
    dirty_paths = [row["path"] for row in dirty_entries]
    product_dirty_paths = [path for path in dirty_paths if not _control_path(path)]
    product_worktree_fingerprint = _worktree_fingerprint(root, dirty_entries)
    since_validated = changed_paths(root, validated_sha, head)
    product_changes = [path for path in since_validated if not _control_path(path)]
    since_base = [path for path in changed_paths(root, base_sha, head) if not _control_path(path)]
    since_product = [path for path in changed_paths(root, product_sha, head) if not _control_path(path)]
    deletions_since_base = [path for path in changed_paths(root, base_sha, head, diff_filter="D") if not _control_path(path)]
    type_changes_since_base = [path for path in changed_paths(root, base_sha, head, diff_filter="T") if not _control_path(path)]
    worktree_deletions = [path for path in _worktree_changed_paths(root, diff_filter="D") if not _control_path(path)]
    index_type_changes = [path for path in _raw_type_changed_paths(root, "--cached", "HEAD", "--") if not _control_path(path)]
    worktree_type_changes = [path for path in _raw_type_changed_paths(root, "--") if not _control_path(path)]
    tracked_control = tracked_control_paths(root)
    result = {
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
        "product_worktree_fingerprint": product_worktree_fingerprint,
        "relation_to_base": relation(root, base_sha, head),
        "relation_to_product": relation(root, product_sha, head),
        "relation_to_validated": relation(root, validated_sha, head),
        "changes_since_base": since_base,
        "deletions_since_base": deletions_since_base,
        "type_changes_since_base": type_changes_since_base,
        "worktree_deletions": worktree_deletions,
        "worktree_type_changes": worktree_type_changes,
        "index_type_changes": index_type_changes,
        "changes_since_product": since_product,
        "changes_since_validated": product_changes,
        "tracked_control_paths": tracked_control,
    }
    product_state = {
        "head": result["head"], "tree": result["tree"],
        "relation_to_base": result["relation_to_base"],
        "changes_since_base": result["changes_since_base"],
        "product_dirty_paths": result["product_dirty_paths"],
        "product_worktree_fingerprint": result["product_worktree_fingerprint"],
        "deletions_since_base": result["deletions_since_base"],
        "type_changes_since_base": result["type_changes_since_base"],
        "worktree_deletions": result["worktree_deletions"],
        "worktree_type_changes": result["worktree_type_changes"],
        "index_type_changes": result["index_type_changes"],
    }
    result["product_state_digest"] = hashlib.sha256(
        (json.dumps(product_state, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    ).hexdigest()
    return result


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
