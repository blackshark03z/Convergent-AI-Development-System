#!/usr/bin/env python3
"""Create only missing canonical project-context files from static templates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SOURCE_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SOURCE_ROOT / "templates" / "project"
CANONICAL_FILES = ("AGENTS.md", "TASK.md", "ARCHITECTURE.md")


class BootstrapError(RuntimeError):
    """A safe bootstrap precondition was not met."""


def validate_root(root: Path) -> Path:
    try:
        resolved = root.expanduser().resolve(strict=True)
    except OSError as exc:
        raise BootstrapError(f"target root does not exist: {root}") from exc
    if not resolved.is_dir():
        raise BootstrapError(f"target root is not a directory: {resolved}")
    return resolved


def template_bytes(name: str) -> bytes:
    path = TEMPLATE_ROOT / name
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise BootstrapError(f"template is unavailable: {path}") from exc
    if not data:
        raise BootstrapError(f"template is empty: {path}")
    return data


def inspect(root: Path) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    preserved: list[str] = []
    for name in CANONICAL_FILES:
        target = root / name
        if target.exists():
            if not target.is_file():
                raise BootstrapError(f"canonical path is not a file: {target}")
            preserved.append(name)
        else:
            missing.append(name)
    return missing, preserved


def run(root: Path, *, check: bool = False) -> tuple[dict[str, object], int]:
    resolved = validate_root(root)
    missing, preserved = inspect(resolved)
    if check:
        result = "READY" if not missing else "BOOTSTRAP_REQUIRED"
        return {
            "result": result,
            "root": str(resolved),
            "missing": missing,
            "preserved": preserved,
            "created": [],
        }, 0 if result == "READY" else 1

    created: list[str] = []
    for name in missing:
        target = resolved / name
        data = template_bytes(name)
        try:
            with target.open("xb") as stream:
                stream.write(data)
        except FileExistsError:
            preserved.append(name)
        except OSError as exc:
            raise BootstrapError(f"could not create {target}: {exc}") from exc
        else:
            created.append(name)

    remaining, _ = inspect(resolved)
    return {
        "result": "READY" if not remaining else "BOOTSTRAP_REQUIRED",
        "root": str(resolved),
        "missing": remaining,
        "preserved": [name for name in CANONICAL_FILES if name in preserved],
        "created": created,
    }, 0 if not remaining else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safely initialize or inspect canonical project context files.",
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--check", action="store_true",
        help="inspect only; create no files",
    )
    args = parser.parse_args(argv)
    try:
        summary, returncode = run(args.root, check=args.check)
    except (BootstrapError, ValueError) as exc:
        print(json.dumps({"result": "BLOCK", "message": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(summary, sort_keys=True))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
