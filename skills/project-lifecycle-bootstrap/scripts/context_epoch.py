#!/usr/bin/env python3
"""Fail-closed Codex context-epoch orchestration.

This is deliberately an adoption-layer runtime adapter.  It does not alter the
frozen Build OS kernel: rollover remains the sole lifecycle CAS.  The adapter
only creates/fences Codex execution contexts and publishes a bounded immutable
receipt binding that external execution identity to the committed generation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from typing import Any, Mapping


SCHEMA = "buildos.context-epoch-receipt.v1"
RUNTIME_CAPABILITY = "codex-app-server-context-epoch.v1"
RUNTIME_VERSION = "1.0.1"
SAFE_CLOSEOUT_ELIGIBILITY = "CONTEXT_EPOCH_ELIGIBLE_FOR_SAFE_CLOSEOUT"
MAX_RECEIPT_BYTES = 8192
MAX_CAPSULE_BYTES = 8192
MUTATING_COMMANDS = {"record-commit", "validate", "close", "rollover"}


class ContextEpochError(RuntimeError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def digest(value: bytes | Mapping[str, Any]) -> str:
    data = canonical(value) if isinstance(value, Mapping) else value
    return hashlib.sha256(data).hexdigest()


def objective_hash(objective: str) -> str:
    normalized = "\n".join(line.rstrip() for line in str(objective).strip().splitlines())
    if not normalized or len(normalized.encode("utf-8")) > 4096:
        raise ContextEpochError("Goal objective is missing or exceeds the bounded transfer limit")
    return digest(normalized.encode("utf-8"))


def _json_output(command: list[str], *, cwd: Path, timeout: int = 90, accepted_statuses: set[str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout)
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ContextEpochError("expected JSON from a required portable facade") from exc
    accepted = accepted_statuses or {"PASS", "OK", "RECOVERED"}
    if proc.returncode or value.get("status") not in accepted:
        raise ContextEpochError(str(value.get("message") or value.get("error") or "required facade action failed"))
    return value


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=30)
    if proc.returncode:
        raise ContextEpochError("Git identity observation failed")
    return proc.stdout.strip()


def _worktree(root: Path) -> dict[str, str]:
    path = str(root.resolve())
    return {"path_hash": digest(path.encode("utf-8")), "branch": _git(root, "branch", "--show-current") or "DETACHED"}


class Rpc:
    """Minimal newline-delimited JSON-RPC client for the installed app server."""

    def __init__(self) -> None:
        self.proc: subprocess.Popen[str] | None = None
        self.counter = 0

    def __enter__(self) -> "Rpc":
        # cmd.exe makes this work when the npm installation exposes codex.ps1.
        self.proc = subprocess.Popen(
            ["cmd.exe", "/d", "/s", "/c", "codex app-server --stdio"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", errors="replace",
        )
        self.call("initialize", {"clientInfo": {"name": "buildos-context-epoch", "version": "1.0.0"}, "capabilities": {}})
        return self

    def __exit__(self, *_: object) -> None:
        if self.proc is not None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def call(self, method: str, params: Mapping[str, Any]) -> dict[str, Any]:
        if self.proc is None or self.proc.stdin is None or self.proc.stdout is None:
            raise ContextEpochError("Codex app-server is not available")
        self.counter += 1
        request_id = self.counter
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}) + "\n")
        self.proc.stdin.flush()
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                raise ContextEpochError("Codex app-server closed before replying")
            try:
                response = json.loads(line)
            except json.JSONDecodeError:
                continue
            if response.get("id") != request_id:
                continue
            if "error" in response:
                raise ContextEpochError(f"Codex runtime rejected {method}: {response['error'].get('message', 'unknown error')}")
            result = response.get("result")
            if not isinstance(result, dict):
                raise ContextEpochError(f"Codex runtime returned an invalid {method} result")
            return result
        raise ContextEpochError(f"Codex app-server timed out during {method}")


def _sidecar_capsule(package: Path, root: Path, task_id: str) -> dict[str, Any]:
    command = [sys.executable, str(package / "skills" / "documentation-handoff-continuity" / "scripts" / "continuity.py"), "--root", str(root), "--task-id", task_id, "working-set"]
    value = _json_output(command, cwd=root, accepted_statuses={"SAFE_TO_CONTINUE", "TARGETED_READ_REQUIRED"})
    sidecar_path = Path(str(value.get("sidecar") or ""))
    if not sidecar_path.is_file():
        raise ContextEpochError("context epoch requires an active verified Continuity sidecar")
    # Continuity's CAS expects its canonical self_hash, while the epoch receipt
    # binds raw bytes. Keep both meanings explicit without writing new state.
    sidecar_value = json.loads(sidecar_path.read_text(encoding="utf-8"))
    self_hash = sidecar_value.get("self_hash")
    if not isinstance(self_hash, str):
        raise ContextEpochError("active Continuity sidecar has no canonical self hash")
    value["sidecar_hash"] = self_hash
    value["sidecar_content_sha256"] = digest(sidecar_path.read_bytes())
    return value


def _bootstrap_text(*, capsule: Mapping[str, Any], receipt_path: Path, next_action: str) -> str:
    """The only successor model-visible handoff payload; never a transcript."""
    capsule_text = str(capsule.get("capsule") or "")
    targeted = [line.removeprefix("targeted_reads=") for line in capsule_text.splitlines() if line.startswith("targeted_reads=")]
    payload = "\n".join([
        "CONTEXT_EPOCH_SUCCESSOR_BOOTSTRAP_V1",
        f"receipt={receipt_path}",
        f"next_action={next_action}",
        f"capsule_sha256={digest(capsule_text.encode('utf-8'))}",
        *(targeted or ["targeted_reads=NONE"]),
        "capsule_begin",
        capsule_text.rstrip(),
        "capsule_end",
        "Do not request or replay predecessor conversation, tool output, full evidence, or Knowledge Pack.",
    ])
    if len(payload.encode("utf-8")) > MAX_CAPSULE_BYTES:
        raise ContextEpochError("successor bootstrap exceeds the existing 8 KiB bound")
    return payload


def _inject_bootstrap(rpc: "Rpc", thread_id: str, payload: str) -> None:
    # This is a single bounded fresh-thread input, not copied predecessor history.
    rpc.call("thread/inject_items", {"threadId": thread_id, "items": [{
        "type": "message", "role": "user", "content": [{"type": "input_text", "text": payload}],
    }]})


def _checkpoint(package: Path, root: Path, task_id: str, capsule: Mapping[str, Any]) -> dict[str, Any]:
    sidecar_hash = str(capsule.get("sidecar_hash") or "")
    if not sidecar_hash:
        raise ContextEpochError("context epoch requires an active verified Continuity sidecar")
    command = [
        sys.executable, str(package / "skills" / "documentation-handoff-continuity" / "scripts" / "continuity.py"),
        "--root", str(root), "--task-id", task_id, "checkpoint", "--kind", "context-epoch",
        "--expected-sidecar-hash", sidecar_hash, "--operational-status", "HANDOFF",
        "--next-safe-action", "verify immutable context-epoch receipt then activate the bound successor",
        "--documentation-impact", "NO", "--category", "IMPLEMENTATION_ONLY",
        "--documentation-rationale", "execution-context transition only",
        "--decision", "context epoch committed through existing rollover CAS",
    ]
    return _json_output(command, cwd=root)


def _receipt_path(root: Path, task_id: str, revision: int, epoch: int, operation_id: str) -> Path:
    safe = operation_id.replace("/", "_").replace("\\", "_")
    return root / ".buildos" / "runtime" / "context_epoch_receipts" / task_id / f"r{revision:03d}" / f"e{epoch:03d}-{safe}.json"


def _publish_receipt(path: Path, receipt: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in receipt.items() if key != "self_hash"}
    receipt["self_hash"] = digest(unsigned)
    data = canonical(receipt)
    if len(data) > MAX_RECEIPT_BYTES:
        raise ContextEpochError("context-epoch receipt exceeds its hard bound")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
    except FileExistsError:
        existing = json.loads(path.read_text(encoding="utf-8"))
        if canonical(existing) != data:
            raise ContextEpochError("duplicate context-epoch receipt operation conflicts")
    if path.read_bytes() != data:
        raise ContextEpochError("immutable context-epoch receipt read-back failed")
    return receipt["self_hash"]


def _canonical_state(package: Path, root: Path) -> tuple[dict[str, Any], str]:
    """Read the immutable-current state without extending the frozen kernel.

    The public ``status`` facade intentionally returns a compact work packet.
    A context receipt also needs the canonical lease and context bindings, so
    this adoption-layer reader uses the kernel's read-only CURRENT verifier.
    """
    package_text = str(package)
    inserted = package_text not in sys.path
    if inserted:
        sys.path.insert(0, package_text)
    try:
        from buildos.store import read_current
        snapshot = read_current(root)
    finally:
        if inserted:
            sys.path.remove(package_text)
    if snapshot is None or not isinstance(snapshot.state, dict):
        raise ContextEpochError("Build OS CURRENT has no canonical state")
    return snapshot.state, snapshot.generation_hash


def _continuity_dirty_fingerprint(package: Path, root: Path) -> str:
    """Reuse the sidecar's complete dirty-state algorithm for receipt fencing."""
    script = package / "skills" / "documentation-handoff-continuity" / "scripts" / "continuity.py"
    spec = importlib.util.spec_from_file_location(f"buildos_continuity_{uuid.uuid4().hex}", script)
    if spec is None or spec.loader is None:
        raise ContextEpochError("cannot load the Continuity dirty-state verifier")
    module = importlib.util.module_from_spec(spec)
    package_text = str(package)
    inserted = package_text not in sys.path
    if inserted:
        sys.path.insert(0, package_text)
    try:
        spec.loader.exec_module(module)
        observed = module.dirty(root)
    finally:
        if inserted:
            sys.path.remove(package_text)
    fingerprint = observed.get("fingerprint") if isinstance(observed, Mapping) else None
    if not observed.get("complete") or not isinstance(fingerprint, str):
        raise ContextEpochError("context epoch dirty-state observation is incomplete")
    return fingerprint


def _state(package: Path, root: Path) -> dict[str, Any]:
    value = _json_output([sys.executable, str(package / "scripts" / "ai.py"), "--root", str(root), "status"], cwd=root)
    state, canonical_generation_hash = _canonical_state(package, root)
    packet = value.get("work_packet") or {}
    for key, expected in (("task_id", state.get("task_id")), ("revision", state.get("revision")), ("phase", state.get("phase"))):
        reported = value.get(key) or packet.get({"phase": "lifecycle_state"}.get(key, key))
        if reported is not None and expected is not None and reported != expected:
            raise ContextEpochError(f"status facade disagrees with canonical state for {key}")
    reported_hash = value.get("generation_hash") or packet.get("state_hash")
    if reported_hash is not None and reported_hash != canonical_generation_hash:
        raise ContextEpochError("status facade disagrees with canonical state for generation_hash")
    value["task_id"] = state.get("task_id")
    value["revision"] = state.get("revision")
    value["phase"] = state.get("phase")
    value["state"] = state
    value["generation_hash"] = canonical_generation_hash
    return value


def _context(status: Mapping[str, Any]) -> Mapping[str, Any]:
    state = status.get("state") or status.get("canonical_state") or {}
    context = state.get("context") if isinstance(state, Mapping) else None
    if not isinstance(context, Mapping):
        packet = status.get("work_packet") or {}
        context = {key: packet.get(key) for key in ("epoch", "epoch_id", "thread_id")} if packet else None
    if not isinstance(context, Mapping) or context.get("epoch") is None:
        raise ContextEpochError("Build OS status did not expose canonical context identity")
    return context


def _assert_phase(status: Mapping[str, Any]) -> None:
    phase = status.get("phase") or (status.get("work_packet") or {}).get("lifecycle_state")
    if phase not in {"ACTIVE", "PRODUCT_COMMITTED"}:
        raise ContextEpochError("context epoch is only legal at a coherent ACTIVE or PRODUCT_COMMITTED boundary")


def _runtime_goal_hash(thread_id: str, *, rpc: "Rpc | None" = None) -> str:
    """Read the live Goal directly; never infer it from an old thread payload."""
    if rpc is not None:
        goal = rpc.call("thread/goal/get", {"threadId": thread_id}).get("goal")
    else:
        with Rpc() as client:
            goal = client.call("thread/goal/get", {"threadId": thread_id}).get("goal")
    if not isinstance(goal, Mapping) or not isinstance(goal.get("objective"), str):
        raise ContextEpochError("bound successor has no readable Goal objective")
    return objective_hash(str(goal["objective"]))


def _post_compaction_observation(package: Path, root: Path, args: argparse.Namespace) -> dict[str, Any]:
    """Require one real, non-zero post-compaction observation before a cut."""
    if args.projected_prompt_tokens is None or args.projected_prompt_tokens <= 0:
        raise ContextEpochError("context epoch requires a non-zero real post-compaction prompt measurement")
    if args.model_context_window is None or args.model_context_window <= 0:
        raise ContextEpochError("context epoch requires the measured model context window")
    command = [
        sys.executable, str(package / "scripts" / "ai.py"), "--root", str(root), "status",
        "--projected-prompt-tokens", str(args.projected_prompt_tokens),
        "--model-context-window", str(args.model_context_window),
        "--compaction-status", args.compaction_status,
        "--compaction-evidence", args.compaction_evidence,
    ]
    if args.persistent_post_compaction_loss:
        command += ["--persistent-post-compaction-loss", args.persistent_post_compaction_loss]
    observed = _json_output(command, cwd=root)
    governor = observed.get("governor")
    if not isinstance(governor, Mapping):
        raise ContextEpochError("existing governor did not return a post-compaction observation")
    action = str(governor.get("action") or "")
    if action not in {"COMPACT_REQUIRED", "HARD_STOP", "ROLLOVER_REQUIRED"}:
        raise ContextEpochError(f"post-compaction governor requires staying in-context: {action or 'UNKNOWN'}")
    if governor.get("measurement") != "MEASURED" or governor.get("latest_prompt_tokens") != args.projected_prompt_tokens:
        raise ContextEpochError("post-compaction measurement is not the required latest real prompt footprint")
    return {
        "action": action, "reason": governor.get("reason"), "measurement": governor.get("measurement"),
        "latest_prompt_tokens": governor.get("latest_prompt_tokens"),
        "model_context_window": governor.get("model_context_window"),
        "compaction_status": governor.get("compaction_status"),
        "compaction_evidence": args.compaction_evidence,
        "post_compaction_evidence": args.post_compaction_evidence,
    }


def _assert_cut_safety(args: argparse.Namespace) -> str:
    if args.atomic_operation_complete != "YES":
        raise ContextEpochError("context epoch requires a completed atomic operation boundary")
    if args.closeout_only == "YES":
        if args.material_work_remains != "NO":
            raise ContextEpochError("closeout-only context epoch requires no material work remaining")
        if args.would_continuing_same_context_violate_headroom_safety != "YES":
            raise ContextEpochError("bounded closeout stays in the current context while same-context continuation is safe")
        if args.context_epoch_available != "YES":
            raise ContextEpochError("safe stop: Context Epoch capability is unavailable for unsafe bounded closeout")
        return SAFE_CLOSEOUT_ELIGIBILITY
    if args.material_work_remains != "YES":
        raise ContextEpochError("context epoch is forbidden when material work does not remain outside bounded closeout")
    return "CONTEXT_EPOCH_ELIGIBLE_FOR_MATERIAL_WORK"


def _prior_closeout_epoch_exists(root: Path, task_id: str, revision: int) -> bool:
    """A bounded closeout may use one recovery epoch, never a chain of them."""
    directory = root / ".buildos" / "runtime" / "context_epoch_receipts" / task_id / f"r{revision:03d}"
    if not directory.is_dir():
        return False
    for receipt_path in directory.glob("e*.json"):
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            # A malformed receipt is handled by normal fail-closed recovery;
            # it must not be treated as permission for another successor.
            return True
        if (receipt.get("cut_safety") or {}).get("closeout_only") is True:
            return True
    return False


def _preflight_receipt(root: Path, status: Mapping[str, Any], thread_id: str, *, package: Path | None = None,
                       verify_runtime_goal: bool = False, rpc: "Rpc | None" = None) -> dict[str, Any]:
    state = status.get("state") or {}
    context = _context(status)
    task_id, revision, epoch = str(status.get("task_id") or state.get("task_id") or ""), int(status.get("revision") or state.get("revision") or 0), int(context.get("epoch") or 0)
    directory = root / ".buildos" / "runtime" / "context_epoch_receipts" / task_id / f"r{revision:03d}"
    candidates = sorted(directory.glob(f"e{epoch:03d}-*.json")) if directory.is_dir() else []
    if len(candidates) != 1:
        raise ContextEpochError("context epoch ownership requires exactly one immutable receipt")
    value = json.loads(candidates[0].read_text(encoding="utf-8"))
    unsigned = {key: item for key, item in value.items() if key != "self_hash"}
    if value.get("schema") != SCHEMA or value.get("self_hash") != digest(unsigned):
        raise ContextEpochError("context epoch receipt integrity failed")
    if value.get("successor", {}).get("thread_id") != thread_id or context.get("thread_id") != thread_id:
        raise ContextEpochError("current thread is not the bound context-epoch successor")
    if int(value.get("successor", {}).get("epoch") or 0) != epoch:
        raise ContextEpochError("context epoch binding failed")
    if value.get("successor", {}).get("generation_hash") != status.get("generation_hash"):
        raise ContextEpochError("context epoch generation binding failed")
    if value.get("lifecycle_phase") != status.get("phase"):
        raise ContextEpochError("context epoch lifecycle-phase binding failed")
    if value.get("worker") != (state.get("lease") or {}).get("holder"):
        raise ContextEpochError("context epoch Worker/lease binding failed")
    goal = value.get("goal") or {}
    if not isinstance(goal.get("objective_sha256"), str):
        raise ContextEpochError("context epoch Goal binding failed")
    if verify_runtime_goal and _runtime_goal_hash(thread_id, rpc=rpc) != goal["objective_sha256"]:
        raise ContextEpochError("context epoch Goal-objective hash binding failed")
    git = value.get("git") or {}
    if git.get("head") != _git(root, "rev-parse", "HEAD") or git.get("tree") != _git(root, "rev-parse", "HEAD^{tree}"):
        raise ContextEpochError("context epoch Git binding failed")
    if git.get("worktree") != _worktree(root):
        raise ContextEpochError("context epoch worktree binding failed")
    if not isinstance(git.get("accepted_ref"), str) or not isinstance(git.get("resolved_accepted_sha"), str) or _git(root, "rev-parse", git["accepted_ref"]) != git["resolved_accepted_sha"]:
        raise ContextEpochError("context epoch accepted-baseline binding failed")
    if not isinstance(git.get("dirty_fingerprint"), str):
        raise ContextEpochError("context epoch dirty-state binding failed")
    if package is not None and _continuity_dirty_fingerprint(package, root) != git["dirty_fingerprint"]:
        raise ContextEpochError("context epoch dirty-state binding failed")
    sidecar = value.get("continuity") or {}
    sidecar_path = Path(str(sidecar.get("path") or ""))
    if not sidecar_path.is_file() or digest(sidecar_path.read_bytes()) != sidecar.get("sha256"):
        raise ContextEpochError("context epoch Continuity binding failed")
    capsule = value.get("capsule") or {}
    if not isinstance(capsule.get("sha256"), str) or not isinstance(capsule.get("bytes"), int):
        raise ContextEpochError("context epoch Capsule binding failed")
    if package is not None:
        current_capsule = _sidecar_capsule(package, root, task_id)
        rendered = str(current_capsule.get("capsule") or "").encode("utf-8")
        if len(rendered) != capsule.get("bytes") or digest(rendered) != capsule.get("sha256"):
            raise ContextEpochError("context epoch Capsule hash binding failed")
    return value


def command_handoff(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve(); package = Path(args.package_root).resolve()
    before = _state(package, root); _assert_phase(before)
    eligibility = _assert_cut_safety(args)
    post_compaction = _post_compaction_observation(package, root, args)
    context = _context(before)
    predecessor_id = str(args.predecessor_thread_id or context.get("thread_id") or "").strip()
    if not predecessor_id:
        raise ContextEpochError("handoff requires the canonical predecessor thread identity")
    if context.get("thread_id") and predecessor_id != context.get("thread_id"):
        raise ContextEpochError("predecessor thread does not match canonical Build OS context")
    task_id, revision, old_epoch = str(before["task_id"]), int(before["revision"]), int(context.get("epoch", 1))
    if args.closeout_only == "YES" and _prior_closeout_epoch_exists(root, task_id, revision):
        raise ContextEpochError("bounded closeout permits only one controlled Context Epoch")
    # Capture the active verified sidecar before rollover.  After the CAS its
    # kernel generation intentionally differs, so asking it for a Capsule
    # before checkpoint would correctly report NEEDS_RECONCILIATION.
    predecessor_capsule = _sidecar_capsule(package, root, task_id)
    operation = args.operation_id or f"context-epoch-{uuid.uuid4().hex}"
    with Rpc() as rpc:
        predecessor = rpc.call("thread/resume", {"threadId": predecessor_id})
        goal = rpc.call("thread/goal/get", {"threadId": predecessor_id}).get("goal")
        if not isinstance(goal, Mapping) or not isinstance(goal.get("objective"), str):
            raise ContextEpochError("predecessor has no transferable bounded Goal intent")
        goal_digest = objective_hash(str(goal["objective"]))
        # Stop any active turn, then pause only the predecessor's goal.
        loaded = rpc.call("thread/read", {"threadId": predecessor_id, "includeTurns": True}).get("thread") or {}
        for turn in loaded.get("turns") or []:
            if turn.get("status") == "inProgress": rpc.call("turn/interrupt", {"threadId": predecessor_id, "turnId": turn["id"]})
        rpc.call("thread/goal/set", {"threadId": predecessor_id, "objective": goal["objective"], "status": "paused"})
        successor = rpc.call("thread/start", {"cwd": str(root), "ephemeral": False, "model": args.model or predecessor.get("model")})
        successor_id = str((successor.get("thread") or {}).get("id") or "")
        if not successor_id or successor_id == predecessor_id or (successor.get("thread") or {}).get("turns"):
            raise ContextEpochError("runtime did not create a fresh inactive zero-history successor")
        # Bind the exact same semantic Goal but keep it inactive until receipt
        # verification. This makes post-CAS crash recovery deterministic.
        try:
            rpc.call("thread/goal/set", {"threadId": successor_id, "objective": goal["objective"], "status": "paused"})
            if _runtime_goal_hash(successor_id, rpc=rpc) != goal_digest:
                raise ContextEpochError("successor Goal objective does not match the paused predecessor Goal")
        except Exception:
            rpc.call("thread/goal/set", {"threadId": predecessor_id, "objective": goal["objective"], "status": "active"})
            rpc.call("thread/archive", {"threadId": successor_id})
            raise
        try:
            rollover_command = [
                sys.executable, str(package / "scripts" / "ai.py"), "--root", str(root), "rollover",
                "--thread-id", successor_id, "--compaction-status", args.compaction_status,
                "--compaction-evidence", args.compaction_evidence, "--operation-id", operation,
            ]
            if args.projected_prompt_tokens is not None:
                rollover_command += ["--projected-prompt-tokens", str(args.projected_prompt_tokens)]
            if args.model_context_window is not None:
                rollover_command += ["--model-context-window", str(args.model_context_window)]
            if args.persistent_post_compaction_loss:
                rollover_command += ["--persistent-post-compaction-loss", args.persistent_post_compaction_loss]
            # The kernel retains its governor and CAS.  Its legacy rollover
            # threshold is narrower than the selected hybrid rule, so only a
            # verified post-compaction COMPACT_REQUIRED/HARD_STOP observation
            # uses the existing force path to commit that same CAS.
            if post_compaction["action"] in {"COMPACT_REQUIRED", "HARD_STOP"}:
                rollover_command += ["--force"]
            rollover = _json_output(rollover_command, cwd=root)
        except Exception:
            # Restore only when CURRENT still names the predecessor. A competing
            # rollover may have won the sole CAS while this attempt lost; waking
            # the old Goal in that case would create split-brain execution.
            try:
                current_context = _context(_state(package, root))
                predecessor_still_current = int(current_context.get("epoch", 0)) == old_epoch and current_context.get("thread_id") == context.get("thread_id")
            except Exception:
                predecessor_still_current = False
            if predecessor_still_current:
                rpc.call("thread/goal/set", {"threadId": predecessor_id, "objective": goal["objective"], "status": "active"})
            rpc.call("thread/archive", {"threadId": successor_id})
            raise
        after = _state(package, root); successor_context = _context(after)
        if int(successor_context.get("epoch", 0)) != old_epoch + 1 or successor_context.get("thread_id") != successor_id:
            raise ContextEpochError("existing rollover CAS did not commit the requested successor")
        checkpoint = _checkpoint(package, root, task_id, predecessor_capsule)
        capsule = _sidecar_capsule(package, root, task_id)
        capsule_text = str(capsule.get("capsule") or "")
        if not capsule_text or len(capsule_text.encode("utf-8")) > MAX_CAPSULE_BYTES:
            raise ContextEpochError("Working State Capsule is absent or exceeds its hard bound")
        sidecar_path = Path(str(capsule["sidecar"])).resolve()
        sidecar_value = json.loads(sidecar_path.read_text(encoding="utf-8"))
        next_action = (
            "perform only immediate validation, assurance, and close actions from Capsule-targeted reads"
            if args.closeout_only == "YES"
            else "verify receipt and continue only from Capsule-targeted reads"
        )
        receipt = {
            "schema": SCHEMA, "capability": RUNTIME_CAPABILITY, "self_hash": "", "task_id": task_id, "revision": revision,
            "operation_id": operation, "lifecycle_phase": after["phase"], "next_action": next_action, "worker": (after.get("state") or {}).get("lease", {}).get("holder"),
            "cut_safety": {
                "material_work_remains": args.material_work_remains == "YES",
                "atomic_operation_complete": True,
                "closeout_only": args.closeout_only == "YES",
                "would_continuing_same_context_violate_headroom_safety": args.would_continuing_same_context_violate_headroom_safety == "YES",
                "context_epoch_available": args.context_epoch_available == "YES",
                "eligibility": eligibility,
            },
            "post_compaction": post_compaction,
            "predecessor": {"epoch": old_epoch, "epoch_id": context.get("epoch_id"), "thread_id": predecessor_id, "generation_hash": before.get("generation_hash")},
            "successor": {"epoch": successor_context.get("epoch"), "epoch_id": successor_context.get("epoch_id"), "thread_id": successor_id, "generation_hash": after.get("generation_hash")},
            "goal": {"objective_sha256": goal_digest}, "continuity": {"path": str(sidecar_path), "sha256": digest(sidecar_path.read_bytes()), "checkpoint_hash": checkpoint.get("sidecar_hash")},
            "capsule": {"sha256": digest(capsule_text.encode("utf-8")), "bytes": len(capsule_text.encode("utf-8"))},
            "git": {"worktree": _worktree(root), "accepted_ref": sidecar_value.get("accepted_ref"), "resolved_accepted_sha": sidecar_value.get("resolved_accepted_sha"), "head": _git(root, "rev-parse", "HEAD"), "tree": _git(root, "rev-parse", "HEAD^{tree}"), "dirty_fingerprint": (sidecar_value.get("git") or {}).get("dirty", {}).get("fingerprint")},
        }
        receipt_path = _receipt_path(root, task_id, revision, int(successor_context["epoch"]), operation)
        _publish_receipt(receipt_path, receipt)
        _preflight_receipt(root, after, successor_id, package=package, verify_runtime_goal=True, rpc=rpc)
        _inject_bootstrap(rpc, successor_id, _bootstrap_text(capsule=capsule, receipt_path=receipt_path, next_action=next_action))
        rpc.call("thread/goal/set", {"threadId": successor_id, "objective": goal["objective"], "status": "active"})
        rpc.call("thread/archive", {"threadId": predecessor_id})
    return {"status": "PASS", "operation_id": operation, "receipt": str(receipt_path), "successor_thread_id": successor_id, "goal_objective_sha256": goal_digest, "rollover": rollover}


def command_preflight(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve(); package = Path(args.package_root).resolve(); thread = str(args.thread_id or os.environ.get("CODEX_THREAD_ID") or "").strip()
    observed = _state(package, root)
    if int(_context(observed).get("epoch", 1)) <= 1:
        return {"status": "PASS", "thread_id": thread, "context_epoch": False, "capability": RUNTIME_CAPABILITY}
    if not thread:
        raise ContextEpochError("context epoch preflight requires CODEX_THREAD_ID or --thread-id")
    receipt = _preflight_receipt(root, observed, thread, package=package, verify_runtime_goal=True)
    return {"status": "PASS", "thread_id": thread, "receipt": receipt["self_hash"], "capability": RUNTIME_CAPABILITY}


def command_recover(args: argparse.Namespace) -> dict[str, Any]:
    """Bounded crash classification; never guesses or activates two owners."""
    root = Path(args.root).resolve(); package = Path(args.package_root).resolve(); observed = _state(package, root); context = _context(observed)
    if int(context.get("epoch", 1)) <= 1:
        return {"status": "PREDECESSOR_CANONICAL", "capability": RUNTIME_CAPABILITY, "action": "resume or safely stop the predecessor Goal"}
    thread = str(context.get("thread_id") or "")
    try:
        receipt = _preflight_receipt(root, observed, thread, package=package, verify_runtime_goal=True)
    except ContextEpochError as exc:
        return {"status": "RECOVERY_REQUIRED", "capability": RUNTIME_CAPABILITY, "message": str(exc), "action": "do not activate any context; reconcile from CURRENT and immutable receipts"}
    return {"status": "SUCCESSOR_CANONICAL", "capability": RUNTIME_CAPABILITY, "thread_id": thread, "receipt": receipt["self_hash"], "action": "verify successor Goal objective hash then activate only that successor"}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Compact-then-context-epoch runtime adapter")
    p.add_argument("--root", required=True); p.add_argument("--package-root", default=str(Path(__file__).resolve().parents[3]))
    sub = p.add_subparsers(dest="command", required=True)
    handoff = sub.add_parser("handoff"); handoff.add_argument("--predecessor-thread-id"); handoff.add_argument("--model"); handoff.add_argument("--operation-id")
    handoff.add_argument("--compaction-status", required=True, choices=["UNAVAILABLE", "ATTEMPTED_INEFFECTIVE"]); handoff.add_argument("--compaction-evidence", required=True)
    handoff.add_argument("--post-compaction-evidence", required=True, help="bounded proof pointer for the one real post-compaction request")
    handoff.add_argument("--projected-prompt-tokens", type=int, required=True); handoff.add_argument("--model-context-window", type=int, required=True)
    handoff.add_argument("--material-work-remains", required=True, choices=["YES", "NO"]); handoff.add_argument("--atomic-operation-complete", required=True, choices=["YES", "NO"])
    handoff.add_argument("--closeout-only", default="NO", choices=["YES", "NO"])
    handoff.add_argument("--would-continuing-same-context-violate-headroom-safety", default="NO", choices=["YES", "NO"])
    handoff.add_argument("--context-epoch-available", default="YES", choices=["YES", "NO"])
    handoff.add_argument("--persistent-post-compaction-loss", choices=["VERIFIED_STALE_CONTEXT_CONTRADICTION", "MATERIAL_TASK_OUTCOME_RESET", "DEMONSTRABLE_STATE_LOSS"])
    preflight = sub.add_parser("preflight"); preflight.add_argument("--thread-id")
    sub.add_parser("recover")
    return p


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw == ["--version"]:
        print(json.dumps({"component": "context-epoch-runtime", "capability": RUNTIME_CAPABILITY, "version": RUNTIME_VERSION}, sort_keys=True))
        return 0
    args = parser().parse_args(raw)
    try:
        result = command_handoff(args) if args.command == "handoff" else command_preflight(args) if args.command == "preflight" else command_recover(args)
        print(json.dumps(result, sort_keys=True)); return 0
    except (ContextEpochError, OSError, subprocess.SubprocessError, ValueError) as exc:
        print(json.dumps({"status": "ACTION_REQUIRED", "error": type(exc).__name__, "message": str(exc)}, sort_keys=True)); return 2


if __name__ == "__main__": raise SystemExit(main())
