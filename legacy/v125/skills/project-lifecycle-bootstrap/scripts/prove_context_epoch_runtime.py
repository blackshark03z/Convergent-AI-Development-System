#!/usr/bin/env python3
"""Run a bounded disposable proof of the installed Codex epoch primitives."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import time
import uuid


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("context_epoch_runtime", HERE / "context_epoch.py")
assert SPEC is not None and SPEC.loader is not None
epoch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(epoch)


def thread_id(result: dict) -> str:
    value = str((result.get("thread") or {}).get("id") or "")
    if not value:
        raise epoch.ContextEpochError("runtime omitted a stable thread identifier")
    return value


def loaded(rpc: epoch.Rpc, value: str) -> dict:
    return (rpc.call("thread/read", {"threadId": value, "includeTurns": True}).get("thread") or {})


def wait_for_turn(rpc: epoch.Rpc, value: str, timeout_seconds: int) -> dict:
    deadline = time.monotonic() + timeout_seconds
    latest: dict = {}
    while time.monotonic() < deadline:
        latest = loaded(rpc, value)
        turns = latest.get("turns") or []
        if turns and all(turn.get("status") not in {"inProgress", "pending"} for turn in turns):
            return latest
        time.sleep(1)
    # A started input turn is still a non-empty history proof; interrupt it so
    # the disposal path cannot leave active work behind.
    for turn in latest.get("turns") or []:
        if turn.get("status") == "inProgress":
            rpc.call("turn/interrupt", {"threadId": value, "turnId": turn["id"]})
    return loaded(rpc, value)


def run(args: argparse.Namespace) -> dict:
    objective = f"disposable-context-epoch-proof-{uuid.uuid4().hex}"
    predecessor_marker = f"PREDECESSOR_ONLY_{uuid.uuid4().hex}"
    successor_marker = f"SUCCESSOR_BOOTSTRAP_{uuid.uuid4().hex}"
    created: list[str] = []
    try:
        with epoch.Rpc() as rpc:
            predecessor_id = thread_id(rpc.call("thread/start", {"cwd": str(args.cwd), "ephemeral": False}))
            created.append(predecessor_id)
            rpc.call("thread/goal/set", {"threadId": predecessor_id, "objective": objective, "status": "paused"})
            rpc.call("turn/start", {"threadId": predecessor_id, "input": [{"type": "text", "text": predecessor_marker}]})
            predecessor = wait_for_turn(rpc, predecessor_id, args.timeout_seconds)
            if not predecessor.get("turns"):
                raise epoch.ContextEpochError("predecessor did not retain a non-empty runtime turn")

            fork_id = thread_id(rpc.call("thread/fork", {"threadId": predecessor_id}))
            created.append(fork_id)
            fork = loaded(rpc, fork_id)
            if not fork.get("turns"):
                raise epoch.ContextEpochError("runtime fork did not expose copied history; proof is inconclusive")

            successor_started = rpc.call("thread/start", {"cwd": str(args.cwd), "ephemeral": False})
            successor_id = thread_id(successor_started)
            created.append(successor_id)
            # The actual runtime rejects includeTurns before a fresh thread has
            # its first user input. Its thread/start result is the authoritative
            # zero-history capability response at this point.
            successor_initial = successor_started.get("thread") or {}
            if successor_initial.get("turns") or successor_initial.get("forkedFromId"):
                raise epoch.ContextEpochError("fresh thread/start successor inherited history or fork ancestry")
            rpc.call("thread/goal/set", {"threadId": successor_id, "objective": objective, "status": "paused"})
            if epoch._runtime_goal_hash(successor_id, rpc=rpc) != epoch.objective_hash(objective):
                raise epoch.ContextEpochError("same Goal intent cannot be proven on the fresh successor")
            epoch._inject_bootstrap(rpc, successor_id, successor_marker)
            rpc.call("turn/start", {"threadId": successor_id, "input": [{"type": "text", "text": f"Reply exactly {successor_marker}"}]})
            successor = wait_for_turn(rpc, successor_id, args.timeout_seconds)
            successor_view = json.dumps(successor, sort_keys=True)
            if predecessor_marker in successor_view:
                raise epoch.ContextEpochError("successor runtime view inherited predecessor input/history")
            # The marker may be omitted from a read-only history view by the
            # runtime, but its turn is independently exercised after injection.
            if not successor.get("turns"):
                raise epoch.ContextEpochError("successor could not start a real post-bootstrap turn")
            rpc.call("thread/goal/set", {"threadId": predecessor_id, "objective": objective, "status": "paused"})
            rpc.call("thread/goal/set", {"threadId": successor_id, "objective": objective, "status": "active"})
            return {
                "status": "PASS", "capability": epoch.RUNTIME_CAPABILITY,
                "predecessor_turns": len(predecessor.get("turns") or []),
                "fork_copied_turns": len(fork.get("turns") or []),
                "successor_initial_turns": len(successor_initial.get("turns") or []),
                "successor_turns_after_bootstrap": len(successor.get("turns") or []),
                "same_goal_objective": True, "predecessor_history_in_successor": False,
                "predecessor_id": predecessor_id, "successor_id": successor_id,
            }
    finally:
        # Archive every disposable proof thread, including the rejected fork.
        try:
            with epoch.Rpc() as cleanup:
                for value in created:
                    try:
                        cleanup.call("thread/archive", {"threadId": value})
                    except epoch.ContextEpochError:
                        pass
        except epoch.ContextEpochError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="disposable Codex context-epoch runtime proof")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--timeout-seconds", type=int, default=45)
    args = parser.parse_args()
    if args.timeout_seconds < 1 or args.timeout_seconds > 120:
        parser.error("--timeout-seconds must be between 1 and 120")
    try:
        print(json.dumps(run(args), sort_keys=True))
        return 0
    except epoch.ContextEpochError as exc:
        print(json.dumps({"status": "FAIL", "capability": epoch.RUNTIME_CAPABILITY, "message": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
