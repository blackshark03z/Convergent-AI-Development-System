#!/usr/bin/env python3
"""Explicit lifecycle action for proven accepted-baseline-equivalent failures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from buildos import git_adapter
from buildos.facade import BuildOS
from buildos.model import KernelError, now_iso, sha256_bytes, transition_validate
from buildos.store import commit_candidate, operation_id, paths, publish_immutable

from baseline_equivalence import DispositionError, execute_comparison


AUTHORITY_DELTA = ".buildos-authority.json"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=45, check=False)
    if result.returncode:
        raise KernelError(result.stderr.strip() or result.stdout.strip() or "Git command failed")
    return result.stdout.strip()


def _canonical_record(root: Path, package_root: Path) -> dict[str, Any]:
    path = root / ".buildos-authority.json"
    try:
        record = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise KernelError("baseline-equivalent disposition requires a readable canonical authority record") from exc
    executor = (package_root / "scripts" / "ai.py").resolve()
    if record.get("package_root") != str(package_root.resolve()) or record.get("canonical_executor") != str(executor):
        raise KernelError("baseline-equivalent disposition must be invoked through the bound corrected package")
    if record.get("canonical_executor_sha256") != hashlib.sha256(executor.read_bytes()).hexdigest():
        raise KernelError("bound canonical executor does not match corrected package bytes")
    return record


def _authority_only_head(root: Path, candidate_sha: str) -> None:
    head = _git(root, "rev-parse", "HEAD")
    if head == candidate_sha:
        return
    if subprocess.run(["git", "merge-base", "--is-ancestor", candidate_sha, head], cwd=root, capture_output=True, timeout=30).returncode:
        raise KernelError("authority binding HEAD diverged from recorded product candidate")
    names = [line.strip() for line in _git(root, "diff", "--name-only", candidate_sha, head).splitlines() if line.strip()]
    if names != [AUTHORITY_DELTA]:
        raise KernelError("authority binding descendant may change only .buildos-authority.json")


def _candidate_observation(root: Path, state: Mapping[str, Any], candidate_sha: str) -> dict[str, Any]:
    # Ask Git for the exact product object rather than validating the authority
    # binding descendant.  The object is the recorded PRODUCT_COMMITTED anchor.
    base = (state.get("base_git") or {}).get("head")
    if not base:
        raise KernelError("recorded task has no accepted baseline anchor")
    tree = _git(root, "rev-parse", f"{candidate_sha}^{{tree}}")
    changed = [line.strip() for line in _git(root, "diff", "--name-only", base, candidate_sha).splitlines() if line.strip()]
    status = _git(root, "diff", "--name-status", base, candidate_sha).splitlines()
    deletions = [line.split("\t", 1)[1] for line in status if line.startswith("D\t")]
    type_changes = [line.split("\t", 1)[1] for line in status if line.startswith("T\t")]
    return {
        "available": True, "root": str(root.resolve()), "branch": _git(root, "branch", "--show-current"),
        "head": candidate_sha, "tree": tree, "dirty": False, "product_dirty": False,
        "product_dirty_paths": [], "tracked_control_paths": [], "relation_to_base": "DESCENDANT",
        "relation_to_product": "SAME", "relation_to_validated": "UNKNOWN",
        "changes_since_base": changed, "changes_since_product": [], "changes_since_validated": [],
        "deletions_since_base": deletions, "type_changes_since_base": type_changes,
        "case_insensitive_paths": bool(git_adapter.snapshot(root).get("case_insensitive_paths")),
    }


def _accepted_sha(root: Path) -> tuple[str, str, bytes]:
    policy_path = root / ".buildos-policy.json"
    raw = policy_path.read_bytes()
    try:
        policy = json.loads(raw.decode("utf-8-sig"))
        selector = str(((policy.get("documentation_handoff") or {}).get("accepted_ref")) or "").strip()
    except (UnicodeDecodeError, ValueError) as exc:
        raise KernelError("project policy is unreadable") from exc
    if not selector:
        raise KernelError("project policy has no accepted baseline selector")
    return selector, _git(root, "rev-parse", selector), raw


def _authority_provenance(root: Path, candidate_sha: str) -> dict[str, Any]:
    prior_raw = _git(root, "show", f"{candidate_sha}:.buildos-authority.json").encode("utf-8")
    try:
        prior = json.loads(prior_raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise KernelError("recorded candidate has no readable prior authority record") from exc
    current_raw = (root / ".buildos-authority.json").read_bytes()
    try:
        current = json.loads(current_raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise KernelError("corrected authority record is unreadable") from exc
    return {
        "prior_record_sha256": sha256_bytes(prior_raw), "prior_record": prior,
        "current_record_sha256": sha256_bytes(current_raw), "current_record": current,
        "rollback": {"selector": "recorded-candidate-authority-record", "candidate_sha": candidate_sha, "prior_package_root": prior.get("package_root")},
    }


def _publish(root: Path, state: Mapping[str, Any], operation: str, payload: Mapping[str, Any]) -> dict[str, str]:
    rel = Path(".buildos") / "evidence" / str(state["task_id"]) / f"r{int(state['revision']):03d}" / f"baseline-equivalent-{hashlib.sha256(operation.encode()).hexdigest()[:24]}.json"
    target = root / rel
    data = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if target.exists():
        existing = target.read_bytes()
        if existing != data:
            raise KernelError("existing immutable baseline-equivalent evidence belongs to another disposition")
        return {"kind": "BASELINE_EQUIVALENT_FAILURE_DISPOSITION", "path": rel.as_posix(), "sha256": sha256_bytes(existing), "target_sha": payload["candidate_sha"]}
    stage = paths(root).staging / f"{operation}.baseline-equivalent.tmp"
    stage.parent.mkdir(parents=True, exist_ok=True)
    stage.write_bytes(data)
    publish_immutable(stage, target)
    published = target.read_bytes()
    if published != data:
        raise KernelError("immutable disposition evidence publication selected different bytes")
    return {"kind": "BASELINE_EQUIVALENT_FAILURE_DISPOSITION", "path": rel.as_posix(), "sha256": sha256_bytes(published), "target_sha": payload["candidate_sha"]}


def disposition(
    root: Path,
    *,
    package_root: Path,
    expected_baseline_sha: str,
    timeout: int,
    authorization_actor: str,
    authorization_reference: str,
    inspected_by: str,
    op_id: str | None = None,
) -> dict[str, Any]:
    """Create immutable truthful evidence and advance only to ASSURANCE_READY."""
    if int(timeout) <= 0:
        raise KernelError("validation timeout must be a positive finite number of seconds")
    actor = str(authorization_actor).strip()
    reference = str(authorization_reference).strip()
    if not actor or actor.upper() in {"WORKER", "AUTO", "SELF"} or not reference:
        raise KernelError("baseline-equivalent disposition requires explicit non-worker authorization actor and reference")
    _canonical_record(root, package_root)
    osys = BuildOS(root, package_root=package_root)
    previous = osys._snapshot()
    state = previous.state
    if state.get("phase") != "PRODUCT_COMMITTED":
        raise KernelError("baseline-equivalent disposition requires PRODUCT_COMMITTED lifecycle state")
    candidate_sha = str((state.get("product_commit") or {}).get("sha") or "")
    if not candidate_sha:
        raise KernelError("baseline-equivalent disposition requires a recorded product candidate")
    _authority_only_head(root, candidate_sha)
    selector, baseline_sha, policy_bytes = _accepted_sha(root)
    if baseline_sha != str(expected_baseline_sha):
        raise KernelError("accepted baseline selector changed or does not match the explicitly authorized baseline")
    operation = op_id or operation_id("BASELINE_EQUIVALENT_FAILURE_DISPOSITION", state["task_id"], state["revision"], baseline_sha, candidate_sha, timeout, actor, reference)
    result = execute_comparison(root, baseline_sha=baseline_sha, candidate_sha=candidate_sha, command="python -m pytest -q", timeout=int(timeout), policy_sha256=sha256_bytes(policy_bytes))
    # Re-resolve dynamic Git authority after all expensive commands, before the
    # immutable proof and transition are committed.
    after_selector, after_baseline, after_policy = _accepted_sha(root)
    if after_selector != selector or after_baseline != baseline_sha or sha256_bytes(after_policy) != sha256_bytes(policy_bytes):
        raise KernelError("accepted selector or validation policy changed during comparison")
    _authority_only_head(root, candidate_sha)
    observed = _candidate_observation(root, state, candidate_sha)
    payload = {
        **result,
        "task_id": state["task_id"], "revision": state["revision"], "candidate_sha": candidate_sha,
        "accepted_baseline_selector": selector, "accepted_baseline_sha": baseline_sha,
        "product_anchor_sha": candidate_sha, "authority": _authority_provenance(root, candidate_sha),
        "authorization": {"actor": actor, "reference": reference}, "inspected_by": str(inspected_by).strip(),
        "operation_id": operation, "created_at": now_iso(),
    }
    evidence = _publish(root, state, operation, payload)
    candidate_state, event = transition_validate(state, observed, evidence)

    def precommit() -> None:
        check_selector, check_baseline, check_policy = _accepted_sha(root)
        if check_selector != selector or check_baseline != baseline_sha or sha256_bytes(check_policy) != sha256_bytes(policy_bytes):
            raise KernelError("accepted selector or validation policy changed before disposition commit")
        _authority_only_head(root, candidate_sha)

    committed = commit_candidate(root, expected_hash=previous.generation_hash, candidate_state=candidate_state, event=event, operation_id=operation, configured_failures=None, projector=osys.project, precommit_validator=precommit)
    return {"status": "PASS", "disposition": "BASELINE_EQUIVALENT_FAILURES_AUTHORIZED", "evidence": evidence, "generation": committed.snapshot.generation, "generation_hash": committed.snapshot.generation_hash, "candidate_sha": candidate_sha, "baseline_sha": baseline_sha, "pytest_candidate_returncode": result["candidate"]["returncode"], "pytest_baseline_returncode": result["baseline"]["returncode"]}
