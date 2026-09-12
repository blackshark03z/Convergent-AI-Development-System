#!/usr/bin/env python3
"""Deterministically project canonical CADS skills to Agent Skills SKILL.md files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "skills" / "agent-skills.json"
SKILL_ROOT = (ROOT / "skills").resolve()
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class ProjectionError(RuntimeError):
    pass


def load_manifest() -> list[dict[str, str]]:
    try:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectionError(f"portable skill manifest unavailable/invalid: {exc}") from exc
    if payload.get("schema_version") != 1 or not isinstance(payload.get("skills"), list):
        raise ProjectionError("portable skill manifest schema is invalid")
    entries = payload["skills"]
    seen_names: set[str] = set()
    seen_sources: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ProjectionError("portable skill entry must be an object")
        source = entry.get("source")
        name = entry.get("name")
        description = entry.get("description")
        if not isinstance(source, str) or not source.startswith("skills/"):
            raise ProjectionError(f"invalid source: {source!r}")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            raise ProjectionError(f"invalid Agent Skill name: {name!r}")
        if not isinstance(description, str) or not description.strip() or "\n" in description:
            raise ProjectionError(f"invalid description for {name}")
        if name in seen_names or source in seen_sources:
            raise ProjectionError(f"duplicate portable skill mapping: {name} / {source}")
        seen_names.add(name)
        seen_sources.add(source)
        path = (ROOT / source).resolve()
        try:
            path.relative_to(SKILL_ROOT)
        except ValueError as exc:
            raise ProjectionError(f"skill source escapes canonical skill root: {source}") from exc
        if not path.is_file():
            raise ProjectionError(f"canonical skill source missing: {source}")
    return entries


def render(entry: dict[str, str]) -> bytes:
    source = (ROOT / entry["source"]).read_bytes()
    header = (
        "---\n"
        f"name: {entry['name']}\n"
        f"description: {json.dumps(entry['description'], ensure_ascii=False)}\n"
        "---\n\n"
    ).encode("utf-8")
    return header + source


def run(output_dir: Path, *, check: bool) -> tuple[dict[str, object], int]:
    entries = load_manifest()
    output = output_dir.expanduser().resolve(strict=False)
    try:
        output.relative_to(SKILL_ROOT)
    except ValueError:
        pass
    else:
        raise ProjectionError("projection output must not be inside canonical skills/")

    mismatches: list[str] = []
    generated: list[str] = []
    if not check:
        output.mkdir(parents=True, exist_ok=True)

    for entry in entries:
        target = output / entry["name"] / "SKILL.md"
        expected = render(entry)
        if check:
            try:
                actual = target.read_bytes()
            except OSError:
                mismatches.append(entry["name"])
            else:
                if actual != expected:
                    mismatches.append(entry["name"])
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(expected)
        generated.append(entry["name"])

    if check:
        result = "PASS" if not mismatches else "MISMATCH"
        return {
            "result": result,
            "output_dir": str(output),
            "checked": len(entries),
            "mismatches": mismatches,
        }, 0 if not mismatches else 1
    return {
        "result": "GENERATED",
        "output_dir": str(output),
        "generated": generated,
        "count": len(generated),
    }, 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Project canonical CADS skills into Agent Skills-compatible SKILL.md files.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="compare only; write nothing")
    args = parser.parse_args(argv)
    try:
        payload, code = run(args.output_dir, check=args.check)
    except (ProjectionError, OSError, ValueError) as exc:
        print(json.dumps({"result": "BLOCK", "message": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
