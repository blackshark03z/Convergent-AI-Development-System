#!/usr/bin/env python3
"""Fail-closed accepted-baseline failure comparison for Build OS v1.22.

This module deliberately does not change pytest's exit status.  It captures
the normal result of the canonical command at two exact Git objects and may
only emit a disposition when every candidate failure has the same stable
identity and normalized failure signature as an accepted-baseline failure.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Mapping, Sequence


class DispositionError(ValueError):
    """A comparison precondition or fail-closed safety rule was not met."""


CANONICAL_PYTEST_COMMAND = "python -m pytest -q"
RELEVANT_ENVIRONMENT = ("PYTEST_ADDOPTS", "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "PYTHONPATH", "PYTHONHOME")
TEST_POLICY_NAMES = {".buildos-policy.json", "pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg", "conftest.py"}
NODE_RE = re.compile(r"^FAILED\s+(?P<nodeid>.+?)(?:\s+-\s+(?P<summary>.+))?$")
FAILURE_SECTION_RE = re.compile(r"^_+\s+(?P<label>\S(?:.*?\S)?)\s+_+$")
EXCEPTION_RE = re.compile(r"\b([A-Za-z_][\w.]*(?:Error|Exception|Failure))\b")
ABS_TEMP_RE = re.compile(r"(?i)(?:[A-Z]:)?[/\\](?:[^\s:/\\]+[/\\])*(?:tmp|temp|pytest-of-[^/\\\s]+)[^\s:]*")
HEX_ADDRESS_RE = re.compile(r"0x[0-9a-fA-F]+")
TIME_RE = re.compile(r"\b\d+(?:\.\d+)?s\b")


@dataclass(frozen=True)
class Failure:
    nodeid: str
    failure_class: str
    summary: str
    fingerprint: str

    def as_json(self) -> dict[str, str]:
        return {"nodeid": self.nodeid, "failure_class": self.failure_class, "summary": self.summary, "fingerprint": self.fingerprint}


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalize_failure_summary(value: str) -> str:
    """Remove runtime-only detail, retaining the failure's meaningful cause."""
    text = " ".join(str(value).split())
    text = ABS_TEMP_RE.sub("<TEMP_PATH>", text)
    text = HEX_ADDRESS_RE.sub("<ADDRESS>", text)
    return TIME_RE.sub("<DURATION>", text)


def failure_from_summary(nodeid: str, summary: str) -> Failure:
    normalized = normalize_failure_summary(summary)
    found = EXCEPTION_RE.search(normalized)
    failure_class = found.group(1) if found else "SUMMARY_ONLY"
    fingerprint = sha256_bytes(_canonical_json({"nodeid": nodeid, "failure_class": failure_class, "summary": normalized}))
    return Failure(nodeid=nodeid, failure_class=failure_class, summary=normalized, fingerprint=fingerprint)


def _failure_section_labels(nodeid: str) -> set[str]:
    """Return pytest's exact decorative-header identities for a nodeid."""
    parts = nodeid.split("::")
    if len(parts) < 2:
        return set()
    labels = {parts[-1], ".".join(parts[1:])}
    if len(parts) >= 3:
        labels.add(".".join(parts[-2:]))
    return labels


def _failure_sections(output: str) -> list[tuple[str, list[str]]]:
    """Parse pytest failure blocks without assigning them by global position."""
    sections: list[tuple[str, list[str]]] = []
    current_label: str | None = None
    current_lines: list[str] = []
    for raw in output.splitlines():
        stripped = raw.strip()
        if "short test summary info" in stripped:
            break
        match = FAILURE_SECTION_RE.match(stripped)
        if match and any(character.isalnum() for character in match.group("label")):
            if current_label is not None:
                sections.append((current_label, current_lines))
            current_label = match.group("label")
            current_lines = []
        elif current_label is not None:
            current_lines.append(stripped)
    if current_label is not None:
        sections.append((current_label, current_lines))
    return sections


def _section_failure_detail(lines: Sequence[str]) -> str | None:
    details = [line[1:].strip() for line in lines if line.startswith("E ")]
    if not details:
        return None
    classified = [detail for detail in details if EXCEPTION_RE.search(detail)]
    return classified[-1] if classified else details[-1]


def parse_failures(output: str) -> list[Failure]:
    summary_rows: list[tuple[str, str | None]] = []
    in_summary = False
    for raw in output.splitlines():
        line = raw.strip()
        if "short test summary info" in line:
            in_summary = True
            continue
        if not in_summary:
            continue
        match = NODE_RE.match(line)
        if match:
            summary_rows.append((match.group("nodeid"), match.group("summary")))
        elif line.startswith("="):
            break
    sections = _failure_sections(output)
    parsed: list[Failure] = []
    for nodeid, summary in summary_rows:
        detail = summary
        if not detail:
            labels = _failure_section_labels(nodeid)
            matches = [lines for label, lines in sections if label in labels]
            if len(matches) != 1:
                return []
            detail = _section_failure_detail(matches[0])
            if not detail:
                return []
        parsed.append(failure_from_summary(nodeid, detail))
    return parsed


def parse_collection(output: str) -> list[str]:
    nodes: list[str] = []
    for raw in output.splitlines():
        line = raw.strip()
        if not line or line.startswith("=") or line.endswith("collected"):
            continue
        # pytest --collect-only -q emits nodeids, not a stable decorative tree.
        if line.startswith(("tests/", "test_", "src/")) and ("::" in line or line.endswith(".py")):
            nodes.append(line)
    return sorted(set(nodes))


def _validate_command(command: str) -> str:
    if str(command).strip() != CANONICAL_PYTEST_COMMAND:
        raise DispositionError("baseline-equivalent disposition supports only the full canonical command: python -m pytest -q")
    return CANONICAL_PYTEST_COMMAND


def environment_policy(environment: Mapping[str, str] | None = None) -> dict[str, str]:
    values = environment or os.environ
    policy = {name: str(values.get(name, "")) for name in RELEVANT_ENVIRONMENT}
    if policy["PYTEST_ADDOPTS"] or policy["PYTEST_DISABLE_PLUGIN_AUTOLOAD"]:
        raise DispositionError("pytest environment policy may not add options or suppress plugin loading")
    return policy


def _run(cwd: Path, command: str, timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=cwd, shell=True, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise DispositionError(f"canonical validation exceeded finite timeout ({timeout}s)") from exc
    output = (completed.stdout or "") + (completed.stderr or "")
    return {
        "command": command,
        "returncode": completed.returncode,
        "duration_ms": int((time.monotonic() - started) * 1000),
        "stdout_sha256": sha256_bytes((completed.stdout or "").encode("utf-8", "replace")),
        "stderr_sha256": sha256_bytes((completed.stderr or "").encode("utf-8", "replace")),
        "output_sha256": sha256_bytes(output.encode("utf-8", "replace")),
        "failures": [item.as_json() for item in parse_failures(output)],
        "output_excerpt": output[-16000:],
    }


def _collect(cwd: Path, timeout: int) -> dict[str, Any]:
    # This is collection metadata, not an alternative acceptance command.
    command = "python -m pytest --collect-only -q"
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=cwd, shell=True, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise DispositionError(f"test collection exceeded finite timeout ({timeout}s)") from exc
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        raise DispositionError(f"test collection failed (rc={completed.returncode})")
    nodes = parse_collection(output)
    if not nodes:
        raise DispositionError("test collection produced no parseable node identities")
    return {"command": command, "returncode": completed.returncode, "duration_ms": int((time.monotonic() - started) * 1000), "output_sha256": sha256_bytes(output.encode("utf-8", "replace")), "nodes": nodes, "node_count": len(nodes)}


def compare_results(baseline: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Return a strict mapping or raise without ever treating pytest as green."""
    if baseline.get("returncode") not in {0, 1} or candidate.get("returncode") not in {0, 1}:
        raise DispositionError("pytest must finish with its normal 0/1 result; collection or execution error is not dispositionable")
    baseline_failures = [Failure(**{key: item[key] for key in ("nodeid", "failure_class", "summary", "fingerprint")}) for item in baseline.get("failures") or []]
    candidate_failures = [Failure(**{key: item[key] for key in ("nodeid", "failure_class", "summary", "fingerprint")}) for item in candidate.get("failures") or []]
    if candidate.get("returncode") == 0:
        raise DispositionError("candidate suite is green; use normal validation rather than a baseline-equivalent disposition")
    if not candidate_failures:
        raise DispositionError("candidate pytest failure result has no stable failure identities")
    by_node = {item.nodeid: item for item in baseline_failures}
    mapping: list[dict[str, str]] = []
    new: list[dict[str, str]] = []
    changed: list[dict[str, str]] = []
    for item in candidate_failures:
        prior = by_node.get(item.nodeid)
        if prior is None:
            new.append(item.as_json())
        elif prior.fingerprint != item.fingerprint:
            changed.append({"nodeid": item.nodeid, "baseline_fingerprint": prior.fingerprint, "candidate_fingerprint": item.fingerprint})
        else:
            mapping.append({"candidate_nodeid": item.nodeid, "baseline_nodeid": prior.nodeid, "fingerprint": item.fingerprint})
    if new or changed:
        raise DispositionError("candidate has new or materially changed failures; baseline-equivalent disposition is forbidden")
    baseline_nodes = set((baseline.get("collection") or {}).get("nodes") or [])
    candidate_nodes = set((candidate.get("collection") or {}).get("nodes") or [])
    if not baseline_nodes or not candidate_nodes:
        raise DispositionError("both test universes require immutable collection identities")
    missing_nodes = sorted(baseline_nodes - candidate_nodes)
    if missing_nodes:
        raise DispositionError("candidate test universe omits accepted-baseline nodeids; suppression/removal is forbidden")
    return {
        "baseline_failure_count": len(baseline_failures),
        "candidate_failure_count": len(candidate_failures),
        "equivalence_mapping": mapping,
        "new_failures": [],
        "changed_failures": [],
        "missing_baseline_nodeids": [],
        "candidate_test_universe_expanded_by": len(candidate_nodes - baseline_nodes),
    }


def changed_test_policy_paths(repo: Path, baseline_sha: str, candidate_sha: str) -> list[str]:
    completed = subprocess.run(["git", "diff", "--name-only", baseline_sha, candidate_sha], cwd=repo, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=30, check=False)
    if completed.returncode:
        raise DispositionError("unable to inspect candidate test-policy changes")
    blocked: list[str] = []
    for raw in completed.stdout.splitlines():
        path = raw.strip().replace("\\", "/")
        name = path.rsplit("/", 1)[-1]
        if name in TEST_POLICY_NAMES or name == "conftest.py":
            blocked.append(path)
    return sorted(set(blocked))


def _clone_at(repo: Path, sha: str, destination: Path) -> Path:
    created = subprocess.run(["git", "clone", "--no-checkout", "--shared", str(repo), str(destination)], text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=90, check=False)
    if created.returncode:
        raise DispositionError("unable to create isolated validation checkout")
    checkout = subprocess.run(["git", "checkout", "--detach", sha], cwd=destination, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=90, check=False)
    if checkout.returncode:
        raise DispositionError("unable to resolve exact validation Git object")
    actual = subprocess.run(["git", "rev-parse", "HEAD"], cwd=destination, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=30, check=False)
    if actual.returncode or actual.stdout.strip() != sha:
        raise DispositionError("isolated validation checkout does not match requested SHA")
    return destination


def execute_comparison(repo: Path, *, baseline_sha: str, candidate_sha: str, command: str, timeout: int, policy_sha256: str, environment: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Run collection and the exact full suite at immutable baseline/candidate objects."""
    if int(timeout) <= 0:
        raise DispositionError("validation timeout must be a positive finite number of seconds")
    command = _validate_command(command)
    policy = environment_policy(environment)
    changed_policy = changed_test_policy_paths(repo, baseline_sha, candidate_sha)
    if changed_policy:
        raise DispositionError("candidate changes pytest policy or collection hooks: " + ", ".join(changed_policy))
    with tempfile.TemporaryDirectory(prefix="buildos-baseline-equivalence-") as raw:
        temp = Path(raw)
        baseline_root = _clone_at(repo, baseline_sha, temp / "baseline")
        candidate_root = _clone_at(repo, candidate_sha, temp / "candidate")
        baseline_collection = _collect(baseline_root, timeout)
        candidate_collection = _collect(candidate_root, timeout)
        baseline = _run(baseline_root, command, timeout)
        candidate = _run(candidate_root, command, timeout)
    baseline["collection"] = baseline_collection
    candidate["collection"] = candidate_collection
    comparison = compare_results(baseline, candidate)
    return {
        "schema": "buildos.baseline-equivalent-disposition.v1",
        "canonical_command": command,
        "timeout_seconds": int(timeout),
        "policy_sha256": policy_sha256,
        "environment_policy": policy,
        "baseline": {"sha": baseline_sha, "suite_result": "PASSED" if baseline["returncode"] == 0 else "FAILED", **baseline},
        "candidate": {"sha": candidate_sha, "suite_result": "PASSED" if candidate["returncode"] == 0 else "FAILED_WITH_BASELINE_EQUIVALENT_FAILURES", **candidate},
        "comparison": comparison,
        "final_disposition": "BASELINE_EQUIVALENT_FAILURES_AUTHORIZED",
    }
