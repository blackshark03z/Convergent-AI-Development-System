"""Command-line interface for the thin v1.22 facade."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from .facade import BuildOS
from .model import KernelError
from .store import InjectedFailure, RecoveryRequired
from .telemetry import TelemetryError


def _json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _result(value) -> dict[str, Any]:
    snapshot = value.snapshot
    return {
        "status": "PASS",
        "committed": value.committed,
        "idempotent": value.idempotent,
        "recovered_orphan": value.recovered_orphan,
        "task_id": snapshot.state["task_id"],
        "revision": snapshot.state["revision"],
        "phase": snapshot.state["phase"],
        "generation": snapshot.generation,
        "generation_hash": snapshot.generation_hash,
        "next_action": snapshot.state["next_action"],
    }


def _failure_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--operation-id", help="stable retry key; normally generated deterministically")
    parser.add_argument("--failure-at", help=argparse.SUPPRESS)


def parser(*, admin: bool = False) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build OS v1.22 thin transactional facade")
    p.add_argument("--root", type=Path, default=Path.cwd(), help="target repository")
    commands = p.add_subparsers(dest="command", required=True)

    bootstrap = commands.add_parser("bootstrap", help="materialize one task atomically")
    bootstrap.add_argument("--task-id", required=True)
    bootstrap.add_argument("--outcome", required=True)
    bootstrap.add_argument("--accept", action="append", default=[])
    bootstrap.add_argument("--check", action="append", default=[])
    bootstrap.add_argument("--risk", default="auto", choices=["auto", "R0", "R1", "R2", "R3"])
    bootstrap.add_argument("--side-effect", default="WRITE", choices=["READ_ONLY", "WRITE", "CREATE_NEW_VERSION", "MUTATE_IN_PLACE", "OVERWRITE", "DELETE"])
    bootstrap.add_argument("--allow", action="append", default=[])
    bootstrap.add_argument("--prohibit", action="append", default=[])
    bootstrap.add_argument("--worker-id", default="WORKER")
    bootstrap.add_argument("--owner-authorization", default="NONE", choices=["NONE", "APPROVED"])
    bootstrap.add_argument("--authorization-reference", default="")
    bootstrap.add_argument("--authorization-actor", default="OWNER")
    bootstrap.add_argument("--enforcement", default="SUPERVISORY", choices=["SUPERVISORY", "BOUNDARY"])
    bootstrap.add_argument("--skill")
    _failure_arg(bootstrap)

    status = commands.add_parser("status", help="derive status, governor, telemetry and packet")
    status.add_argument("--projected-prompt-tokens", type=int)
    status.add_argument("--requests-in-epoch", type=int)

    nxt = commands.add_parser("next", help="print the minimal generated continuation packet")
    nxt.add_argument("--projected-prompt-tokens", type=int)
    nxt.add_argument("--requests-in-epoch", type=int)

    record = commands.add_parser("record-commit", help="adopt the normal Git product commit")
    _failure_arg(record)

    validate = commands.add_parser("validate", help="run checks and bind immutable evidence")
    validate.add_argument("--check", action="append", default=[])
    validate.add_argument("--inspected-by", required=True)
    validate.add_argument("--reviewer")
    validate.add_argument("--review-reference")
    validate.add_argument("--rollback-check")
    validate.add_argument("--timeout", type=int, default=120)
    _failure_arg(validate)

    rollover = commands.add_parser("rollover", help="start a disposable context epoch")
    rollover.add_argument("--projected-prompt-tokens", type=int)
    rollover.add_argument("--requests-in-epoch", type=int)
    rollover.add_argument("--thread-id", required=True, help="fresh disposable Codex thread/epoch identity")
    rollover.add_argument("--force", action="store_true")
    _failure_arg(rollover)

    close = commands.add_parser("close", help="close an assured task without destructive invalidation")
    _failure_arg(close)

    recover = commands.add_parser("recover", help="validate/repair pointer and regenerate projections")
    recover.add_argument("--check-only", action="store_true")
    recover.add_argument("--failure-at", help=argparse.SUPPRESS)

    if admin:
        revise = commands.add_parser("new-revision", help="explicitly revise scope; evidence remains immutable")
        revise.add_argument("--reason", required=True)
        revise.add_argument("--risk", choices=["R0", "R1", "R2", "R3"])
        revise.add_argument("--allow", action="append")
        revise.add_argument("--prohibit", action="append")
        revise.add_argument("--owner-authorization", choices=["NONE", "APPROVED"])
        revise.add_argument("--authorization-reference")
        revise.add_argument("--authorization-actor")
        _failure_arg(revise)

        abort = commands.add_parser("abort", help="terminal fail-closed stop")
        abort.add_argument("--reason", required=True)
        _failure_arg(abort)

        ingest = commands.add_parser("telemetry-ingest", help="optional normalized telemetry adapter")
        ingest.add_argument("--file", type=Path, required=True)
        ingest.add_argument("--source", default="MANUAL_NORMALIZED")
    return p


def main(argv: list[str] | None = None, *, admin: bool = False) -> int:
    args = parser(admin=admin).parse_args(argv)
    os = BuildOS(args.root)
    outcome = "ACTION_REQUIRED"
    try:
        if args.command == "bootstrap":
            value = os.bootstrap(
                {
                    "task_id": args.task_id,
                    "outcome": args.outcome,
                    "acceptance": args.accept or [args.outcome],
                    "acceptance_commands": args.check,
                    "risk": args.risk,
                    "side_effect": args.side_effect,
                    "allowed_paths": args.allow,
                    "prohibited_paths": args.prohibit,
                    "worker_id": args.worker_id,
                    "owner_authorization": args.owner_authorization,
                    "authorization_reference": args.authorization_reference,
                    "authorization_actor": args.authorization_actor,
                    "enforcement": args.enforcement,
                    "skill": args.skill,
                },
                op_id=args.operation_id,
                configured_failures=args.failure_at,
            )
            _json(_result(value))
        elif args.command in {"status", "next"}:
            usage = {
                key: value for key, value in {
                    "projected_prompt_tokens": args.projected_prompt_tokens,
                    "requests_in_epoch": args.requests_in_epoch,
                }.items() if value is not None
            }
            value = os.status(usage=usage)
            _json(value["work_packet"] if args.command == "next" else value)
        elif args.command == "record-commit":
            _json(_result(os.record_commit(op_id=args.operation_id, configured_failures=args.failure_at)))
        elif args.command == "validate":
            _json(_result(os.validate(
                checks=args.check,
                inspected_by=args.inspected_by,
                reviewer=args.reviewer,
                review_reference=args.review_reference,
                rollback_check=args.rollback_check,
                timeout=args.timeout,
                op_id=args.operation_id,
                configured_failures=args.failure_at,
            )))
        elif args.command == "rollover":
            _json(_result(os.rollover(
                projected_prompt_tokens=args.projected_prompt_tokens,
                requests_in_epoch=args.requests_in_epoch,
                thread_id=args.thread_id,
                force=args.force,
                op_id=args.operation_id,
                configured_failures=args.failure_at,
            )))
        elif args.command == "close":
            _json(_result(os.close(op_id=args.operation_id, configured_failures=args.failure_at)))
        elif args.command == "recover":
            _json(os.recover(repair_pointer=not args.check_only, configured_failures=args.failure_at))
        elif args.command == "new-revision":
            _json(_result(os.revise(
                reason=args.reason,
                risk=args.risk,
                allowed_paths=args.allow,
                prohibited_paths=args.prohibit,
                owner_authorization=args.owner_authorization,
                authorization_reference=args.authorization_reference,
                authorization_actor=args.authorization_actor,
                op_id=args.operation_id,
                configured_failures=args.failure_at,
            )))
        elif args.command == "abort":
            _json(_result(os.abort(reason=args.reason, op_id=args.operation_id, configured_failures=args.failure_at)))
        elif args.command == "telemetry-ingest":
            raw = json.loads(args.file.read_text(encoding="utf-8"))
            payloads = raw.get("records", [raw]) if isinstance(raw, dict) else raw
            _json({"status": "PASS", "ingested": os.ingest_telemetry(payloads, source=args.source)})
        outcome = "PASS"
        return 0
    except (KernelError, RecoveryRequired, InjectedFailure, TelemetryError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        _json({"status": "ACTION_REQUIRED", "error": type(exc).__name__, "message": str(exc)})
        return 2
    finally:
        os.record_control_action(args.command, outcome)


if __name__ == "__main__":
    raise SystemExit(main())
