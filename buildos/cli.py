"""Command-line interface for the thin v1.23 candidate facade."""
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


def _governor_args(command: argparse.ArgumentParser) -> None:
    command.add_argument("--projected-prompt-tokens", type=int)
    command.add_argument("--requests-in-epoch", type=int, help="observational only; never an action trigger")
    command.add_argument("--model-context-window", type=int)
    command.add_argument("--known-payload-output-reserve-tokens", type=int)
    command.add_argument("--runtime-overflow", action="store_true")
    command.add_argument(
        "--compaction-status",
        choices=["NOT_ATTEMPTED", "UNAVAILABLE", "ATTEMPTED_INEFFECTIVE"],
    )
    command.add_argument(
        "--persistent-post-compaction-loss",
        choices=[
            "VERIFIED_STALE_CONTEXT_CONTRADICTION",
            "MATERIAL_TASK_OUTCOME_RESET",
            "DEMONSTRABLE_STATE_LOSS",
        ],
    )
    command.add_argument("--compaction-evidence", help="reference proving compact failure or persistent post-compact loss")


def _task_args(command: argparse.ArgumentParser) -> None:
    command.add_argument("--task-id", required=True)
    command.add_argument("--outcome", required=True)
    command.add_argument("--accept", action="append", default=[])
    command.add_argument("--check", action="append", default=[])
    command.add_argument("--risk", default="auto", choices=["auto", "R0", "R1", "R2", "R3"])
    command.add_argument("--side-effect", default="WRITE", choices=["READ_ONLY", "WRITE", "CREATE_NEW_VERSION", "MUTATE_IN_PLACE", "OVERWRITE", "DELETE"])
    command.add_argument("--allow", action="append", default=[])
    command.add_argument("--prohibit", action="append", default=[])
    command.add_argument("--worker-id", default="WORKER")
    command.add_argument("--owner-authorization", default="NONE", choices=["NONE", "APPROVED"])
    command.add_argument("--authorization-reference", default="")
    command.add_argument("--authorization-actor", default="OWNER")
    command.add_argument("--enforcement", default="SUPERVISORY", choices=["SUPERVISORY", "BOUNDARY"])
    command.add_argument("--skill")


def _task_request(args: argparse.Namespace) -> dict[str, Any]:
    return {
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
    }


def parser(*, admin: bool = False) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build OS v1.23 candidate transactional facade")
    p.add_argument("--root", type=Path, default=Path.cwd(), help="target repository")
    commands = p.add_subparsers(dest="command", required=True)

    bootstrap = commands.add_parser("bootstrap", help="materialize one task atomically")
    _task_args(bootstrap)
    _failure_arg(bootstrap)

    status = commands.add_parser("status", help="derive status, governor, telemetry and packet")
    _governor_args(status)

    nxt = commands.add_parser("next", help="print the minimal generated continuation packet")
    _governor_args(nxt)

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
    _governor_args(rollover)
    rollover.add_argument("--thread-id", required=True, help="fresh disposable Codex thread/epoch identity")
    rollover.add_argument("--force", action="store_true")
    _failure_arg(rollover)

    close = commands.add_parser("close", help="close an assured task without destructive invalidation")
    _failure_arg(close)

    recover = commands.add_parser("recover", help="validate/repair pointer and regenerate projections")
    recover.add_argument("--check-only", action="store_true")
    recover.add_argument("--failure-at", help=argparse.SUPPRESS)

    block = commands.add_parser("block-for-source-fix", help="release a live task for a bounded source repair")
    block.add_argument("--reason", required=True)
    block.add_argument("--defect-reference", required=True)
    _failure_arg(block)

    continuation = commands.add_parser("continue-task", help="start a fresh task with immutable released-task lineage")
    _task_args(continuation)
    continuation.add_argument("--from-task", required=True)
    continuation.add_argument("--from-revision", type=int)
    continuation.add_argument("--reason", required=True)
    continuation.add_argument("--resolution-reference")
    _failure_arg(continuation)

    if admin:
        adopt = commands.add_parser("adopt-existing-change", help="record a pre-existing clean HEAD without claiming supervised creation")
        _task_args(adopt)
        adopt.add_argument("--base", required=True)
        adopt.add_argument("--target", required=True)
        adopt.add_argument("--reason", required=True)
        _failure_arg(adopt)

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
                _task_request(args),
                op_id=args.operation_id,
                configured_failures=args.failure_at,
            )
            _json(_result(value))
        elif args.command in {"status", "next"}:
            usage = {
                key: value for key, value in {
                    "projected_prompt_tokens": args.projected_prompt_tokens,
                    "requests_in_epoch": args.requests_in_epoch,
                    "model_context_window": args.model_context_window,
                    "known_payload_output_reserve_tokens": args.known_payload_output_reserve_tokens,
                    "runtime_overflow": args.runtime_overflow or None,
                    "compaction_status": args.compaction_status,
                    "persistent_post_compaction_loss": args.persistent_post_compaction_loss,
                    "compaction_evidence": args.compaction_evidence,
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
                model_context_window=args.model_context_window,
                known_payload_output_reserve_tokens=args.known_payload_output_reserve_tokens,
                runtime_overflow=args.runtime_overflow,
                compaction_status=args.compaction_status,
                persistent_post_compaction_loss=args.persistent_post_compaction_loss,
                compaction_evidence=args.compaction_evidence,
                thread_id=args.thread_id,
                force=args.force,
                op_id=args.operation_id,
                configured_failures=args.failure_at,
            )))
        elif args.command == "close":
            _json(_result(os.close(op_id=args.operation_id, configured_failures=args.failure_at)))
        elif args.command == "recover":
            _json(os.recover(repair_pointer=not args.check_only, configured_failures=args.failure_at))
        elif args.command == "block-for-source-fix":
            _json(_result(os.block_for_source_fix(
                reason=args.reason,
                defect_reference=args.defect_reference,
                op_id=args.operation_id,
                configured_failures=args.failure_at,
            )))
        elif args.command == "continue-task":
            _json(_result(os.continue_task(
                _task_request(args),
                source_task_id=args.from_task,
                source_revision=args.from_revision,
                reason=args.reason,
                resolution_reference=args.resolution_reference,
                op_id=args.operation_id,
                configured_failures=args.failure_at,
            )))
        elif args.command == "adopt-existing-change":
            _json(_result(os.adopt_existing_change(
                _task_request(args),
                base=args.base,
                target=args.target,
                reason=args.reason,
                op_id=args.operation_id,
                configured_failures=args.failure_at,
            )))
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
