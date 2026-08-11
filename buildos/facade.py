"""Small orchestration facade over the pure model and transactional store."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import uuid
from typing import Any, Iterable, Mapping, Sequence

from . import git_adapter
from .governor import decide as governor_decide, load_policy
from .model import (
    KernelError,
    initial_state,
    now_iso,
    sha256_bytes,
    transition_abort,
    transition_close,
    transition_new_revision,
    transition_record_commit,
    transition_rollover,
    transition_validate,
    validate_task_request,
)
from .store import (
    CommitResult,
    Snapshot,
    atomic_json,
    atomic_write,
    commit_candidate,
    confirm_committed,
    failpoint,
    operation_id,
    paths,
    publish_immutable,
    read_current,
    recover as recover_store,
    validate_operation_id,
)
from .telemetry import auto_refresh, ingest as telemetry_ingest


SKILL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
MAX_EVIDENCE_OUTPUT = 16_000


def _normalized_commands(commands: Sequence[str], *, label: str) -> list[str]:
    normalized: list[str] = []
    for command in commands:
        value = str(command).strip()
        if not value:
            raise KernelError(f"{label} commands must be non-empty")
        if value not in normalized:
            normalized.append(value)
    return normalized


def _assert_git_unchanged(
    root: Path,
    expected: Mapping[str, Any],
    *,
    base_sha: str | None = None,
    product_sha: str | None = None,
    validated_sha: str | None = None,
) -> None:
    actual = git_adapter.snapshot(root, base_sha=base_sha, product_sha=product_sha, validated_sha=validated_sha)
    fields = (
        "available", "root", "head", "tree", "product_dirty", "product_dirty_paths",
        "tracked_control_paths", "relation_to_base", "relation_to_product",
        "relation_to_validated", "changes_since_base", "changes_since_product",
        "changes_since_validated", "deletions_since_base", "type_changes_since_base",
        "case_insensitive_paths",
    )
    if any(actual.get(field) != expected.get(field) for field in fields):
        raise KernelError("Git product observation changed before canonical commit; retry from fresh status")


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _skill_reference(root: Path, package_root: Path, skill_id: str | None) -> dict[str, Any] | None:
    if not skill_id:
        return None
    if not SKILL_ID_RE.fullmatch(skill_id):
        raise KernelError("skill id must use lowercase letters, digits, '_' or '-'")
    candidates = [
        root / ".buildos" / "skills" / skill_id / "SKILL.md",
        package_root / "skills" / skill_id / "SKILL.md",
    ]
    selected = next((path for path in candidates if path.is_file()), None)
    if selected is None:
        raise KernelError(f"explicit skill not found: {skill_id}; the generic lifecycle works without a skill")
    data = selected.read_bytes()
    if len(data) > 32_000:
        raise KernelError("skill exceeds the 32KB guidance limit")
    return {
        "id": skill_id,
        "path": _relative(root, selected),
        "sha256": sha256_bytes(data),
        "authority": "GUIDANCE_ONLY",
    }


def _rollover_binding_blocked(state: Mapping[str, Any], telemetry: Mapping[str, Any]) -> bool:
    context = state.get("context") or {}
    return bool(
        int(context.get("epoch", 1)) > 1
        and (
            telemetry.get("binding_status") == "TELEMETRY_UNBOUND"
            or telemetry.get("binding_reason") in {"SOURCE_UNAVAILABLE", "ADAPTER_BLOCKED"}
        )
    )


def _packet(snapshot: Snapshot, telemetry: Mapping[str, Any], governor: Mapping[str, Any], skill: Mapping[str, Any] | None) -> dict[str, Any]:
    state = snapshot.state
    commit = state.get("product_commit") or {}
    assurance = state.get("assurance") or {}
    next_action = state["next_action"]
    context = state.get("context") or {}
    rollover_binding_blocked = _rollover_binding_blocked(state, telemetry)
    if state["phase"] in {"ACTIVE", "PRODUCT_COMMITTED"}:
        if rollover_binding_blocked:
            next_action = "stop model work; restore the expected rollover telemetry binding"
        elif governor.get("action") in {"ROLLOVER_REQUIRED", "HARD_STOP"}:
            next_action = "run rollover before further model work"
        elif governor.get("action") == "PREPARE_COMPACT":
            next_action = "prepare a compact continuation and monitor for rollover"
    return {
        "schema": "buildos.work_packet.v1.22",
        "task_id": state["task_id"],
        "revision": state["revision"],
        "lifecycle_state": state["phase"],
        "next_action": next_action,
        "risk": state["risk"],
        "authorization_state": (state.get("authorization") or {}).get("status", "NONE"),
        "base_sha": (state.get("base_git") or {}).get("head"),
        "product_commit_sha": commit.get("sha"),
        "target_sha": assurance.get("target_sha"),
        "evidence_refs": [
            {"path": item.get("path"), "sha256": item.get("sha256"), "kind": item.get("kind")}
            for item in state.get("evidence") or []
        ],
        "epoch": context.get("epoch"),
        "epoch_id": context.get("epoch_id"),
        "thread_id": context.get("thread_id"),
        "rollover_decision": governor.get("action"),
        "telemetry_availability": (
            "UNMEASURED" if rollover_binding_blocked else governor.get("measurement", "UNMEASURED")
        ),
        "telemetry_binding_status": telemetry.get("binding_status"),
        "telemetry_binding_reason": telemetry.get("binding_reason"),
        "state_generation": snapshot.generation,
        "state_hash": snapshot.generation_hash,
        "skill": skill,
    }


def _run_check(root: Path, command: str, timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    proc = subprocess.run(command, cwd=root, shell=True, text=True, capture_output=True, timeout=timeout, check=False)
    elapsed_ms = int((time.monotonic() - started) * 1000)
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    return {
        "command": command,
        "returncode": proc.returncode,
        "duration_ms": elapsed_ms,
        "stdout_sha256": hashlib.sha256(stdout.encode("utf-8", "replace")).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.encode("utf-8", "replace")).hexdigest(),
        "stdout_excerpt": stdout[-MAX_EVIDENCE_OUTPUT:],
        "stderr_excerpt": stderr[-MAX_EVIDENCE_OUTPUT:],
    }


def _prepare_evidence(
    root: Path,
    snapshot: Snapshot,
    *,
    operation: str,
    git: Mapping[str, Any],
    checks: Sequence[str],
    inspected_by: str,
    reviewer: str | None,
    review_reference: str | None,
    rollback_check: str | None,
    timeout: int,
    configured_failures: str | None,
) -> dict[str, Any]:
    state = snapshot.state
    operation = validate_operation_id(operation)
    checks = _normalized_commands(checks, label="validation")
    inspected_by = str(inspected_by).strip()
    reviewer = str(reviewer).strip() if reviewer is not None else None
    reviewer = reviewer or None
    review_reference = str(review_reference).strip() if review_reference is not None else None
    review_reference = review_reference or None
    rollback_check = str(rollback_check).strip() if rollback_check is not None else None
    rollback_check = rollback_check or None
    if not checks:
        raise KernelError("validation requires at least one deterministic check")
    if not inspected_by:
        raise KernelError("validation requires output/diff inspection identity")
    if state["risk"] == "R3":
        if not reviewer or not review_reference:
            raise KernelError("R3 validation requires an independent reviewer and review reference")
        if reviewer.strip().casefold() == str(state.get("worker_id", "")).strip().casefold():
            raise KernelError("R3 reviewer must be independent from the Worker")
        if reviewer.upper() in {"WORKER", "AUTO", "SELF"}:
            raise KernelError("R3 reviewer identity cannot be WORKER, AUTO, or SELF")
        if not rollback_check:
            raise KernelError("R3 validation requires a rollback/recovery check")
    commands = list(dict.fromkeys(checks))
    if rollback_check and rollback_check in commands:
        raise KernelError("rollback/recovery check must be distinct from acceptance checks")
    evidence_key = hashlib.sha256(operation.encode("utf-8")).hexdigest()[:24]
    rel = Path(".buildos") / "evidence" / state["task_id"] / f"r{int(state['revision']):03d}" / f"validation-{evidence_key}.json"
    final = root / rel
    # Retry after evidence publication but before CURRENT reuses exactly the
    # immutable proof.  It never regenerates or overwrites historical evidence.
    if final.is_file():
        data = final.read_bytes()
        try:
            prior = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise KernelError("existing immutable evidence is unreadable") from exc
        if not isinstance(prior, dict):
            raise KernelError("existing immutable evidence has invalid structure")
        prior_checks = prior.get("checks") or []
        if not isinstance(prior_checks, list):
            raise KernelError("existing immutable evidence has invalid check structure")
        prior_commands = [item.get("command") for item in prior_checks if isinstance(item, dict)]
        prior_rollback = prior.get("rollback_check")
        prior_review = prior.get("review") or {}
        if not isinstance(prior_review, dict):
            raise KernelError("existing immutable evidence has invalid review structure")
        try:
            prior_revision = int(prior.get("revision", 0))
        except (TypeError, ValueError) as exc:
            raise KernelError("existing immutable evidence has invalid revision") from exc
        structurally_valid = (
            prior.get("schema") == "buildos.evidence.v1.22"
            and prior.get("operation_id") == operation
            and prior.get("task_id") == state["task_id"]
            and prior_revision == int(state["revision"])
            and prior.get("risk") == state["risk"]
            and prior.get("target_sha") == git.get("head")
            and prior.get("acceptance") == (state.get("acceptance") or [])
            and prior.get("inspected_by") == inspected_by
            and prior_commands == commands
            and all(
                item.get("returncode") == 0 and item.get("role") == "ACCEPTANCE"
                for item in prior_checks if isinstance(item, dict)
            )
            and (
                (rollback_check is None and prior_rollback is None)
                or (
                    isinstance(prior_rollback, dict)
                    and prior_rollback.get("command") == rollback_check
                    and prior_rollback.get("returncode") == 0
                    and prior_rollback.get("role") == "ROLLBACK_RECOVERY"
                )
            )
            and (state["risk"] != "R3" or (prior_review.get("reviewer") == reviewer and prior_review.get("reference") == review_reference))
        )
        if not structurally_valid:
            raise KernelError("existing immutable evidence path belongs to another transition")
        return {"kind": "VALIDATION", "path": rel.as_posix(), "sha256": sha256_bytes(data), "target_sha": prior.get("target_sha")}
    results = []
    for command in commands:
        result = _run_check(root, command, timeout)
        result["role"] = "ACCEPTANCE"
        results.append(result)
    rollback_result = None
    if rollback_check:
        rollback_result = _run_check(root, rollback_check, timeout)
        rollback_result["role"] = "ROLLBACK_RECOVERY"
    failures = [item for item in [*results, *([rollback_result] if rollback_result else [])] if item["returncode"] != 0]
    if failures:
        raise KernelError(f"validation command failed: {failures[0]['command']} (rc={failures[0]['returncode']})")
    after_checks = git_adapter.snapshot(
        root,
        base_sha=(state.get("base_git") or {}).get("head"),
        product_sha=(state.get("product_commit") or {}).get("sha"),
    )
    if after_checks.get("product_dirty"):
        raise KernelError("validation commands left product files dirty; evidence cannot bind an ambiguous tree")
    payload = {
        "schema": "buildos.evidence.v1.22",
        "kind": "VALIDATION",
        "task_id": state["task_id"],
        "revision": state["revision"],
        "risk": state["risk"],
        "product_anchor_sha": (state.get("product_commit") or {}).get("sha"),
        "target_sha": after_checks.get("head"),
        "target_tree": after_checks.get("tree"),
        "acceptance": state.get("acceptance") or [],
        "checks": results,
        "rollback_check": rollback_result,
        "inspected_by": inspected_by,
        "review": {"reviewer": reviewer, "reference": review_reference} if reviewer else None,
        "created_at": now_iso(),
        "operation_id": operation,
    }
    data = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    final.parent.mkdir(parents=True, exist_ok=True)
    stage = paths(root).staging / f"{operation}-{uuid.uuid4().hex}.evidence.tmp"
    failpoint("before_evidence_prepare", configured_failures)
    atomic_write(stage, data)
    failpoint("after_evidence_prepare", configured_failures)
    failpoint("before_evidence_publish", configured_failures)
    publish_immutable(stage, final)
    failpoint("after_evidence_publish", configured_failures)
    published = final.read_bytes()
    if published != data:
        raise KernelError("immutable evidence publication selected different bytes")
    digest = sha256_bytes(published)
    return {"kind": "VALIDATION", "path": rel.as_posix(), "sha256": digest, "target_sha": after_checks.get("head")}


class BuildOS:
    def __init__(self, root: Path | str, *, package_root: Path | str | None = None):
        self.root = Path(root).resolve()
        self.package_root = Path(package_root).resolve() if package_root else Path(__file__).resolve().parents[1]

    def _snapshot(self) -> Snapshot:
        value = read_current(self.root)
        assert value is not None
        return value

    def _skill(self, state: Mapping[str, Any]) -> dict[str, Any] | None:
        return _skill_reference(self.root, self.package_root, state.get("skill"))

    def _idempotent(self, snapshot: Snapshot) -> CommitResult:
        confirmed = confirm_committed(self.root, snapshot)
        self.project(confirmed)
        return CommitResult(confirmed, committed=False, idempotent=True)

    def _usage(
        self,
        snapshot: Snapshot,
        override: Mapping[str, Any] | None = None,
        *,
        rollover_thread_id: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        telemetry = auto_refresh(
            self.root,
            snapshot.state,
            rollover_thread_id=rollover_thread_id,
        )
        epoch_measured = telemetry.get("current_epoch_measurement") == "MEASURED"
        requests_measured = telemetry.get("current_epoch_requests_measurement") == "MEASURED"
        usage = {
            "projected_prompt_tokens": telemetry.get("current_epoch_max_projected_prompt_tokens") if epoch_measured else None,
            "requests_in_epoch": telemetry.get("current_epoch_model_requests") if requests_measured else None,
        }
        for key, value in dict(override or {}).items():
            if value is not None:
                usage[key] = max(int(value), int(usage.get(key) or 0)) if usage.get(key) is not None else int(value)
        policy = load_policy(self.root)
        policy["enforcement"] = snapshot.state.get("enforcement", "SUPERVISORY")
        governor = governor_decide(usage, policy)
        return telemetry, governor

    def project(self, snapshot: Snapshot, *, usage: Mapping[str, Any] | None = None) -> dict[str, Any]:
        p = paths(self.root)
        for _ in range(4):
            current = read_current(self.root)
            assert current is not None
            if current.generation_hash != snapshot.generation_hash:
                snapshot = current
            telemetry, governor = self._usage(snapshot, usage)
            packet = _packet(snapshot, telemetry, governor, self._skill(snapshot.state))
            atomic_json(p.runtime / "WORK_PACKET.json", packet)
            after = read_current(self.root)
            assert after is not None
            if after.generation_hash == snapshot.generation_hash:
                return packet
            snapshot = after
        raise KernelError("canonical state changed repeatedly while deriving WORK_PACKET; retry status")

    def bootstrap(self, request: Mapping[str, Any], *, op_id: str | None = None, configured_failures: str | None = None) -> CommitResult:
        # Validate authorization/risk before touching runtime or Git excludes.
        validated = validate_task_request(request)
        if validated.get("skill"):
            _skill_reference(self.root, self.package_root, validated["skill"])
        existing = read_current(self.root, allow_uninitialized=True)
        observed = git_adapter.snapshot(self.root)
        if observed.get("tracked_control_paths"):
            raise KernelError("bootstrap refuses a tracked .buildos control path; migrate or untrack that reserved path first")
        if observed.get("product_dirty"):
            raise KernelError("bootstrap requires a clean product baseline; generated .buildos files are excluded")
        if not observed.get("available"):
            raise KernelError("bootstrap requires a Git repository so product identity and ancestry are observable")
        if Path(str(observed.get("root"))).resolve() != self.root:
            raise KernelError("bootstrap --root must name the Git worktree top-level directory")
        state = initial_state(request, observed)
        if existing:
            if existing.state.get("contract_hash") == state.get("contract_hash"):
                return self._idempotent(existing)
            if existing.state.get("phase") not in {"CLOSED", "ABORTED"}:
                raise KernelError("a different live canonical task already exists")
            if existing.state.get("task_id") == state.get("task_id"):
                raise KernelError("reuse of a terminal task id requires explicit new-revision semantics")
        failpoint("before_git_exclude", configured_failures)
        git_adapter.ensure_control_excluded(self.root)
        failpoint("after_git_exclude", configured_failures)
        operation = op_id or operation_id(
            "BOOTSTRAP", state["task_id"], state["outcome"], state["risk"], observed.get("head"), observed.get("tree")
        )
        return commit_candidate(
            self.root,
            expected_hash=existing.generation_hash if existing else None,
            candidate_state=state,
            event={
                "kind": "NEW_TASK" if existing else "BOOTSTRAP",
                "task_id": state["task_id"],
                "risk": state["risk"],
                "base_sha": observed.get("head"),
                "base_tree": observed.get("tree"),
            },
            operation_id=operation,
            configured_failures=configured_failures,
            projector=self.project,
            precommit_validator=lambda: _assert_git_unchanged(self.root, observed),
        )

    def status(self, *, usage: Mapping[str, Any] | None = None) -> dict[str, Any]:
        # Derive the Git-aware packet optimistically, then verify CURRENT did
        # not move before returning.  This prevents a concurrent transition
        # from being followed by a stale status/next packet overwrite.
        for _ in range(4):
            snapshot = self._snapshot()
            telemetry, governor = self._usage(snapshot, usage)
            state = snapshot.state
            observed = git_adapter.snapshot(
                self.root,
                base_sha=(state.get("base_git") or {}).get("head"),
                product_sha=(state.get("product_commit") or {}).get("sha"),
                validated_sha=(state.get("assurance") or {}).get("target_sha"),
            )
            head_advanced = observed.get("head") != (state.get("base_git") or {}).get("head")
            read_only_violation = state["phase"] == "ACTIVE" and state.get("side_effect") == "READ_ONLY" and (head_advanced or observed.get("product_dirty"))
            unadopted = (
                state["phase"] == "ACTIVE"
                and state.get("side_effect") != "READ_ONLY"
                and head_advanced
                and observed.get("relation_to_base") == "DESCENDANT"
            )
            relation_key = {
                "ACTIVE": "relation_to_base",
                "PRODUCT_COMMITTED": "relation_to_product",
                "ASSURANCE_READY": "relation_to_validated",
            }.get(state["phase"])
            relation_problem = bool(
                relation_key
                and observed.get("available")
                and observed.get(relation_key) not in {"SAME", "DESCENDANT"}
            )
            late_validated_change = bool(
                state["phase"] in {"ASSURANCE_READY", "CLOSED"}
                and observed.get("changes_since_validated")
            )
            packet = _packet(snapshot, telemetry, governor, self._skill(state))
            next_action = packet["next_action"]
            if not observed.get("available") and state["phase"] not in {"CLOSED", "ABORTED"}:
                next_action = "restore observable Git repository state before the next lifecycle action"
            elif read_only_violation:
                next_action = "READ_ONLY baseline changed; restore it or abort without adopting product mutation"
            elif _rollover_binding_blocked(state, telemetry) and state["phase"] in {"ACTIVE", "PRODUCT_COMMITTED"}:
                next_action = "stop model work; restore the expected rollover telemetry binding"
            elif state["phase"] in {"ACTIVE", "PRODUCT_COMMITTED"} and governor["action"] in {"ROLLOVER_REQUIRED", "HARD_STOP"}:
                next_action = "run rollover before further model work"
            elif relation_problem:
                next_action = "Git ancestry diverged from the task proof; preserve evidence and create an explicit revision"
            elif late_validated_change:
                next_action = "current product changes are not covered by evidence; create a new revision and validate again"
            elif unadopted:
                next_action = "run record-commit to adopt the successful Git product commit"
            packet = {**packet, "next_action": next_action}
            atomic_json(paths(self.root).runtime / "WORK_PACKET.json", packet)
            after = self._snapshot()
            if after.generation_hash != snapshot.generation_hash:
                continue
            return {
                "status": "OK",
                "task_id": state["task_id"],
                "revision": state["revision"],
                "phase": state["phase"],
                "risk": state["risk"],
                "generation": snapshot.generation,
                "generation_hash": snapshot.generation_hash,
                "next_action": next_action,
                "lifecycle_ready": state.get("lifecycle_ready", False),
                "unadopted_product_commit": unadopted,
                "read_only_baseline_violation": read_only_violation,
                "git_relation_problem": relation_problem,
                "unvalidated_product_change": late_validated_change,
                "git": observed,
                "governor": governor,
                "telemetry": telemetry,
                "work_packet": packet,
            }
        raise KernelError("canonical state changed repeatedly while deriving status; retry")

    def record_commit(self, *, op_id: str | None = None, configured_failures: str | None = None) -> CommitResult:
        previous = self._snapshot()
        state = previous.state
        observed = git_adapter.snapshot(self.root, base_sha=(state.get("base_git") or {}).get("head"))
        if state.get("phase") == "PRODUCT_COMMITTED":
            same_head = (state.get("product_commit") or {}).get("sha") == observed.get("head")
            if same_head and observed.get("available") and not observed.get("product_dirty") and not observed.get("tracked_control_paths"):
                return self._idempotent(previous)
            raise KernelError("a product commit is already recorded; changed or dirty HEAD requires an explicit new revision")
        candidate, event = transition_record_commit(state, observed)
        operation = op_id or operation_id("PRODUCT_COMMIT", state["task_id"], state["revision"], observed.get("head"))
        return commit_candidate(
            self.root,
            expected_hash=previous.generation_hash,
            candidate_state=candidate,
            event=event,
            operation_id=operation,
            configured_failures=configured_failures,
            projector=self.project,
            precommit_validator=lambda: _assert_git_unchanged(
                self.root, observed, base_sha=(state.get("base_git") or {}).get("head")
            ),
        )

    def validate(
        self,
        *,
        checks: Sequence[str],
        inspected_by: str,
        reviewer: str | None = None,
        review_reference: str | None = None,
        rollback_check: str | None = None,
        timeout: int = 120,
        op_id: str | None = None,
        configured_failures: str | None = None,
    ) -> CommitResult:
        if int(timeout) <= 0:
            raise KernelError("validation timeout must be a positive number of seconds")
        previous = self._snapshot()
        state = previous.state
        requested_checks = _normalized_commands(checks, label="validation")
        combined = _normalized_commands([*(state.get("acceptance_commands") or []), *requested_checks], label="validation")
        inspected_by = str(inspected_by).strip()
        reviewer = str(reviewer).strip() if reviewer is not None else None
        reviewer = reviewer or None
        review_reference = str(review_reference).strip() if review_reference is not None else None
        review_reference = review_reference or None
        rollback_check = str(rollback_check).strip() if rollback_check is not None else None
        rollback_check = rollback_check or None
        if state.get("phase") == "ASSURANCE_READY" and previous.event.get("kind") == "VALIDATION":
            if op_id is not None and previous.operation_id != op_id:
                raise KernelError("task is already assured under a different validation operation")
            observed_ready = git_adapter.snapshot(
                self.root,
                base_sha=(state.get("base_git") or {}).get("head"),
                product_sha=(state.get("product_commit") or {}).get("sha"),
            )
            _prepare_evidence(
                self.root,
                previous,
                operation=previous.operation_id,
                git=observed_ready,
                checks=combined,
                inspected_by=inspected_by,
                reviewer=reviewer,
                review_reference=review_reference,
                rollback_check=rollback_check,
                timeout=timeout,
                configured_failures=configured_failures,
            )
            return self._idempotent(previous)
        observed = git_adapter.snapshot(
            self.root,
            base_sha=(state.get("base_git") or {}).get("head"),
            product_sha=(state.get("product_commit") or {}).get("sha"),
        )
        # Execute every Git/scope precondition before commands or evidence are
        # prepared.  The real transition is recomputed against a refreshed
        # observation after checks complete.
        transition_validate(
            state,
            observed,
            {"path": "PRECONDITION_ONLY", "sha256": "PRECONDITION_ONLY", "target_sha": observed.get("head")},
        )
        operation = op_id or operation_id(
            "VALIDATE", state["task_id"], state["revision"], observed.get("head"), combined,
            inspected_by, reviewer, review_reference, rollback_check,
        )
        evidence = _prepare_evidence(
            self.root,
            previous,
            operation=operation,
            git=observed,
            checks=combined,
            inspected_by=inspected_by,
            reviewer=reviewer,
            review_reference=review_reference,
            rollback_check=rollback_check,
            timeout=timeout,
            configured_failures=configured_failures,
        )
        refreshed = git_adapter.snapshot(
            self.root,
            base_sha=(state.get("base_git") or {}).get("head"),
            product_sha=(state.get("product_commit") or {}).get("sha"),
        )
        candidate, event = transition_validate(state, refreshed, evidence)
        return commit_candidate(
            self.root,
            expected_hash=previous.generation_hash,
            candidate_state=candidate,
            event=event,
            operation_id=operation,
            configured_failures=configured_failures,
            projector=self.project,
            precommit_validator=lambda: _assert_git_unchanged(
                self.root,
                refreshed,
                base_sha=(state.get("base_git") or {}).get("head"),
                product_sha=(state.get("product_commit") or {}).get("sha"),
            ),
        )

    def close(self, *, op_id: str | None = None, configured_failures: str | None = None) -> CommitResult:
        previous = self._snapshot()
        state = previous.state
        if state.get("phase") == "CLOSED" and previous.event.get("kind") == "CLOSE" and (op_id is None or previous.operation_id == op_id):
            assurance = state.get("assurance") or {}
            observed_closed = git_adapter.snapshot(
                self.root,
                product_sha=assurance.get("target_sha"),
                validated_sha=assurance.get("target_sha"),
            )
            relation = str(observed_closed.get("relation_to_validated", "UNKNOWN")).upper()
            if (
                not observed_closed.get("available")
                or observed_closed.get("product_dirty")
                or relation not in {"SAME", "DESCENDANT"}
                or bool(observed_closed.get("changes_since_validated"))
            ):
                raise KernelError("closed proof does not cover the current product state; start an explicit new revision")
            return self._idempotent(previous)
        assurance = state.get("assurance") or {}
        for evidence in state.get("evidence") or []:
            evidence_path = self.root / str(evidence.get("path"))
            if not evidence_path.is_file() or sha256_bytes(evidence_path.read_bytes()) != evidence.get("sha256"):
                raise KernelError("close requires intact immutable evidence; no evidence was deleted")
        observed = git_adapter.snapshot(
            self.root,
            product_sha=assurance.get("target_sha"),
            validated_sha=assurance.get("target_sha"),
        )
        candidate, event = transition_close(state, observed)
        operation = op_id or operation_id(
            "CLOSE", state["task_id"], state["revision"], assurance.get("target_sha"),
            observed.get("head"), observed.get("tree"), observed.get("relation_to_validated"),
        )
        return commit_candidate(
            self.root,
            expected_hash=previous.generation_hash,
            candidate_state=candidate,
            event=event,
            operation_id=operation,
            configured_failures=configured_failures,
            projector=self.project,
            precommit_validator=lambda: _assert_git_unchanged(
                self.root,
                observed,
                product_sha=assurance.get("target_sha"),
                validated_sha=assurance.get("target_sha"),
            ),
        )

    def rollover(
        self,
        *,
        projected_prompt_tokens: int | None = None,
        requests_in_epoch: int | None = None,
        thread_id: str | None = None,
        force: bool = False,
        op_id: str | None = None,
        configured_failures: str | None = None,
    ) -> CommitResult:
        previous = self._snapshot()
        thread_id = str(thread_id or "").strip()
        if not thread_id:
            raise KernelError("rollover requires an explicit fresh thread_id")
        request_intent = {
            "projected_prompt_tokens": projected_prompt_tokens,
            "requests_in_epoch": requests_in_epoch,
            "thread_id": thread_id,
            "force": bool(force),
        }
        if previous.event.get("kind") == "ROLLOVER" and (op_id is None or previous.operation_id == op_id):
            prior_request = previous.event.get("request") or {}
            if prior_request == request_intent:
                return self._idempotent(previous)
            if op_id is not None and previous.operation_id == op_id:
                raise KernelError("operation_id was reused with a different rollover intent")
        usage = {key: value for key, value in request_intent.items() if key in {"projected_prompt_tokens", "requests_in_epoch"} and value is not None}
        _, signal = self._usage(
            previous,
            usage,
            rollover_thread_id=thread_id,
        )
        if force:
            signal["force"] = True
        candidate, event = transition_rollover(previous.state, signal, thread_id=thread_id)
        event["request"] = request_intent
        event["intent"] = {
            "source_epoch": int((previous.state.get("context") or {}).get("epoch", 1)),
            "request": request_intent,
        }
        operation = op_id or operation_id(
            "ROLLOVER", previous.state["task_id"], previous.state["revision"],
            (previous.state.get("context") or {}).get("epoch") + 1, thread_id, signal,
        )
        return commit_candidate(
            self.root,
            expected_hash=previous.generation_hash,
            candidate_state=candidate,
            event=event,
            operation_id=operation,
            configured_failures=configured_failures,
            projector=self.project,
        )

    def revise(
        self,
        *,
        reason: str,
        risk: str | None = None,
        allowed_paths: Sequence[str] | None = None,
        prohibited_paths: Sequence[str] | None = None,
        owner_authorization: str | None = None,
        authorization_reference: str | None = None,
        authorization_actor: str | None = None,
        op_id: str | None = None,
        configured_failures: str | None = None,
    ) -> CommitResult:
        previous = self._snapshot()
        request_intent = {
            "reason": str(reason).strip(),
            "risk": str(risk).upper() if risk else None,
            "allowed_paths": list(allowed_paths) if allowed_paths is not None else None,
            "prohibited_paths": list(prohibited_paths) if prohibited_paths is not None else None,
            "owner_authorization": str(owner_authorization).upper() if owner_authorization else None,
            "authorization_reference": authorization_reference,
            "authorization_actor": authorization_actor,
        }
        if previous.event.get("kind") == "NEW_REVISION" and (op_id is None or previous.operation_id == op_id):
            if previous.event.get("request") == request_intent:
                return self._idempotent(previous)
            if op_id is not None and previous.operation_id == op_id:
                raise KernelError("operation_id was reused with a different revision intent")
        candidate, event = transition_new_revision(
            previous.state,
            reason=reason,
            risk=risk,
            allowed_paths=list(allowed_paths) if allowed_paths is not None else None,
            prohibited_paths=list(prohibited_paths) if prohibited_paths is not None else None,
            owner_authorization=owner_authorization,
            authorization_reference=authorization_reference,
            authorization_actor=authorization_actor,
        )
        event["request"] = request_intent
        operation = op_id or operation_id("NEW_REVISION", previous.state["task_id"], candidate["revision"], request_intent)
        return commit_candidate(
            self.root,
            expected_hash=previous.generation_hash,
            candidate_state=candidate,
            event=event,
            operation_id=operation,
            configured_failures=configured_failures,
            projector=self.project,
        )

    def abort(self, *, reason: str, op_id: str | None = None, configured_failures: str | None = None) -> CommitResult:
        previous = self._snapshot()
        if previous.event.get("kind") == "ABORT" and previous.state.get("abort_reason") == reason and (op_id is None or previous.operation_id == op_id):
            return self._idempotent(previous)
        candidate, event = transition_abort(previous.state, reason=reason)
        operation = op_id or operation_id("ABORT", previous.state["task_id"], previous.state["revision"], reason)
        return commit_candidate(
            self.root,
            expected_hash=previous.generation_hash,
            candidate_state=candidate,
            event=event,
            operation_id=operation,
            configured_failures=configured_failures,
            projector=self.project,
        )

    def recover(self, *, repair_pointer: bool = True, configured_failures: str | None = None) -> dict[str, Any]:
        result = recover_store(self.root, repair_pointer=repair_pointer, configured_failures=configured_failures)
        if result["status"] in {"OK", "RECOVERED", "RECOVERABLE"} and repair_pointer:
            snapshot = self._snapshot()
            failpoint("before_recovery_projection", configured_failures)
            self.project(snapshot)
            failpoint("after_recovery_projection", configured_failures)
        return result

    def ingest_telemetry(self, payloads: Iterable[Mapping[str, Any]], *, source: str) -> int:
        return telemetry_ingest(self.root, self._snapshot().state, payloads, source=source)

    def record_control_action(self, command: str, outcome: str) -> bool:
        """Best-effort facade overhead accounting; never lifecycle authority."""
        try:
            snapshot = self._snapshot()
            context = snapshot.state.get("context") or {}
            telemetry_ingest(self.root, snapshot.state, [{
                "record_id": f"control-{time.time_ns()}-{hashlib.sha256(command.encode('utf-8')).hexdigest()[:12]}",
                "role": "CONTROL",
                "thread_id": context.get("thread_id"),
                "epoch_id": context.get("epoch_id"),
                "model_requests": 0,
                "model_requests_measured": False,
                "tool_actions": 1,
                "command": command,
                "outcome": outcome,
            }], source="BUILDOS_FACADE")
            return True
        except Exception:
            return False
