"""Thin public CLI for explicit consequential boundaries."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any

from . import git_adapter
from .effect_safety import EffectSafetyError
from .effect_store import EffectStoreError
from .external_effect import (
    effect_retry_safety,
    inspect_effect,
    list_effects,
    reconcile_effect,
)
from .guarded_local import execute_high_cost
from .legacy_effects import inspect_legacy_effects
from .scope_policy import load_scope_policy
from .thin_guard import GuardInputError, check as check_boundary


def _json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _scope_args(command: argparse.ArgumentParser) -> None:
    command.add_argument("--policy", type=Path, help="repo-local JSON scope policy read on this invocation")
    command.add_argument("--expected", action="append", default=[], help="advisory expected path or glob")
    command.add_argument("--strict", action="append", default=[], help="hard allowed path or glob")
    command.add_argument("--prohibited", action="append", default=[], help="hard prohibited path or glob")


def _scope(args: argparse.Namespace) -> dict[str, list[str]]:
    explicit = {
        "expected_paths": list(args.expected),
        "strict_paths": list(args.strict),
        "prohibited_paths": list(args.prohibited),
    }
    if args.policy is None:
        return explicit
    if any(explicit.values()):
        raise GuardInputError("use either --policy or explicit path arguments, not both")
    return load_scope_policy(args.root, args.policy)


def parser(*, admin: bool = False) -> argparse.ArgumentParser:
    del admin
    result = argparse.ArgumentParser(
        description="Build OS: deterministic guards for explicit consequential boundaries",
    )
    result.add_argument("--root", type=Path, default=Path.cwd(), help="exact repository root")
    commands = result.add_subparsers(dest="command", required=True)

    commands.add_parser("inspect", help="read current Git/effect truth without writes")

    check = commands.add_parser("check", help="derive PASS/WARN/BLOCK from live Git and scope")
    check.add_argument("--base", required=True, help="relevant base commit or ref")
    check.add_argument("--boundary", required=True, help="caller-declared consequential boundary")
    _scope_args(check)

    high_cost = commands.add_parser(
        "high-cost",
        help="guard and invoke one explicitly declared high-cost local command",
    )
    high_cost.add_argument("--base", required=True, help="relevant base commit or ref")
    _scope_args(high_cost)
    high_cost.add_argument("native_command", nargs=argparse.REMAINDER, help="native argv after --")

    effect = commands.add_parser("effect", help="inspect durable external-effect safety state")
    effect_commands = effect.add_subparsers(dest="effect_command", required=True)
    effect_commands.add_parser("list", help="list all explicit effect identities")
    effect_inspect = effect_commands.add_parser("inspect", help="inspect one effect identity")
    effect_inspect.add_argument("--effect-id", required=True)
    effect_retry = effect_commands.add_parser("retry-check", help="evaluate retry safety without dispatch")
    effect_retry.add_argument("--effect-id", required=True)

    reconcile = commands.add_parser(
        "reconcile",
        help="record canonical evidence resolving one uncertain external dispatch",
    )
    reconcile.add_argument("--effect-id", required=True)
    reconcile.add_argument(
        "--outcome", required=True,
        choices=["CONFIRMED", "NO_EFFECT_CONFIRMED"],
    )
    reconcile.add_argument("--evidence", required=True)
    reconcile.add_argument("--reference", help="provider reference required for CONFIRMED")
    return result


def parse_invocation(argv: list[str] | None = None, *, admin: bool = False) -> argparse.Namespace:
    return parser(admin=admin).parse_args(argv)


def _inspect(root: Path) -> dict:
    observed = git_adapter.snapshot(root)
    if not observed.get("available"):
        raise RuntimeError("repository Git state is unavailable")
    effects = list_effects(root)
    return {
        "result": "PASS",
        "read_only": True,
        "architecture": "SIMPLIFIED_CONSEQUENTIAL_BOUNDARIES",
        "git": {
            "root": observed["root"],
            "branch": observed["branch"],
            "head": observed["head"],
            "tree": observed["tree"],
            "dirty": observed["dirty"],
            "dirty_paths": observed["dirty_paths"],
            "tracked_control_paths": observed["tracked_control_paths"],
        },
        "effects": effects,
        "unresolved_effect_ids": [
            record["intent"]["effect_id"]
            for record in effects
            if record["state"] in {"PREPARED", "DISPATCH_UNCERTAIN"}
        ],
        "legacy_effects": inspect_legacy_effects(root),
    }


def execute(args: argparse.Namespace) -> int:
    try:
        if args.command == "inspect":
            _json(_inspect(args.root.resolve()))
            return 0
        if args.command == "check":
            value = check_boundary(
                args.root,
                base=args.base,
                boundary=args.boundary,
                **_scope(args),
            )
            _json(value)
            return 2 if value["result"] == "BLOCK" else 0
        if args.command == "high-cost":
            value = execute_high_cost(
                args.root,
                base=args.base,
                command=args.native_command,
                **_scope(args),
            )
            _json(value)
            if not value["executed"]:
                return 2
            return int(value["command_exit_code"])
        if args.command == "effect":
            if args.effect_command == "list":
                value = {"result": "PASS", "effects": list_effects(args.root)}
            elif args.effect_command == "inspect":
                value = {"result": "PASS", "effect": inspect_effect(args.root, args.effect_id)}
            else:
                value = {
                    "result": "PASS",
                    "effect_id": args.effect_id,
                    "retry_safety": effect_retry_safety(args.root, args.effect_id),
                }
            _json(value)
            return 0
        if args.command == "reconcile":
            value = reconcile_effect(
                args.root,
                args.effect_id,
                outcome=args.outcome,
                evidence=args.evidence,
                reference=args.reference,
            )
            _json({"result": "PASS", "effect": value})
            return 0
        raise GuardInputError(f"unsupported command: {args.command}")
    except (
        GuardInputError,
        EffectSafetyError,
        EffectStoreError,
        OSError,
        RuntimeError,
        subprocess.SubprocessError,
    ) as exc:
        _json({
            "result": "BLOCK",
            "reason_codes": ["INVALID_OR_UNSAFE_REQUEST"],
            "error": type(exc).__name__,
            "message": str(exc),
        })
        return 2


def main(argv: list[str] | None = None, *, admin: bool = False) -> int:
    return execute(parse_invocation(argv, admin=admin))


if __name__ == "__main__":
    raise SystemExit(main())
