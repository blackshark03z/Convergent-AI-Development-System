"""Run a qualified, isolated four-arm R->I existential benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "existential" / "cases"
ARMS = ("N0", "N1", "CMIN", "CCURRENT")
AUTH_PATTERN = re.compile(r"(quota exceeded|rate.limit|usage.limit|insufficient.credits|authentication failed|unauthorized|not logged in|sign in to codex|login required|http (401|429))", re.I)
OWNER_PATTERN = re.compile(r"OWNER_INPUT_REQUIRED\s*:\s*yes|NEEDS_OWNER|MATERIAL_OWNER_AMBIGUITY", re.I)
MARKER = ".cads-existential-run"


class RunError(Exception):
    def __init__(self, status: str, detail: str):
        super().__init__(detail)
        self.status = status


def command(args: list[str], cwd: Path | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)


def git(args: list[str], cwd: Path, timeout: int = 30) -> str:
    p = command(["git", *args], cwd, timeout)
    if p.returncode:
        raise RunError("HARNESS_INVALID", f"git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout.strip()


def git_state(workspace: Path) -> tuple:
    """Capture Git HEAD/index entries and exact non-.git worktree file contents."""
    head = git(["rev-parse", "HEAD"], workspace)
    index = subprocess.run(["git", "ls-files", "--stage", "-z"], cwd=workspace,
                           capture_output=True, timeout=30, check=False)
    flags = subprocess.run(["git", "ls-files", "-v", "-z"], cwd=workspace,
                           capture_output=True, timeout=30, check=False)
    if index.returncode or flags.returncode:
        raise RunError("HARNESS_INVALID", "cannot capture Git index state")
    files = []

    def visit(directory: Path) -> None:
        for entry in sorted(os.scandir(directory), key=lambda item: item.name):
            if directory == workspace and entry.name == ".git":
                continue
            path = Path(entry.path)
            relative = path.relative_to(workspace).as_posix()
            if entry.is_symlink():
                files.append((relative, "symlink", os.readlink(path)))
            elif entry.is_dir(follow_symlinks=False):
                visit(path)
            elif entry.is_file(follow_symlinks=False):
                mode = stat.S_IMODE(entry.stat(follow_symlinks=False).st_mode)
                files.append((relative, mode, hashlib.sha256(path.read_bytes()).hexdigest()))
            else:
                raise RunError("HARNESS_INVALID", f"unsupported worktree entry: {relative}")

    visit(workspace)
    return head, index.stdout, flags.stdout, tuple(files)


def state_digest(state: tuple) -> str:
    return hashlib.sha256(repr(state).encode("utf-8")).hexdigest()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("expected object")
        return value
    except (OSError, ValueError) as exc:
        raise RunError("CASE_NOT_READY", f"invalid {path}: {exc}") from exc


def resolve_executable(candidates: list[str]) -> str | None:
    for item in candidates:
        found = shutil.which(item)
        if found:
            return found
        if Path(item).is_file():
            return str(Path(item).resolve())
    return None


def preflight(case_id: str, cli_override: str | None = None) -> tuple[dict, Path, Path, str]:
    case = CASES / case_id
    manifest = read_json(case / "RUNNER.json")
    if manifest.get("case_id") != case_id or manifest.get("schema_version") != 1:
        raise RunError("CASE_NOT_READY", "manifest identity/schema mismatch")
    if manifest.get("status") != "ORACLE_QUALIFIED" or manifest.get("qualification_status") != "ORACLE_QUALIFIED":
        raise RunError("CASE_NOT_READY", f"{case_id}: oracle/projection not qualified")
    qualification_name = manifest.get("qualification_file")
    if not isinstance(qualification_name, str) or Path(qualification_name).name != qualification_name:
        raise RunError("CASE_NOT_READY", "invalid qualification file")
    qualification = read_json(case / qualification_name)
    if qualification.get("case_id") != case_id or qualification.get("status") != "ORACLE_QUALIFIED":
        raise RunError("CASE_NOT_READY", "qualification mismatch")
    if qualification.get("base_preflight", {}).get("actual") != "FAIL" or qualification.get("reference_preflight", {}).get("actual") != "PASS":
        raise RunError("CASE_NOT_READY", "oracle has no qualified base/reference discrimination")
    if not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("qualified_neutral_tree", ""))):
        raise RunError("CASE_NOT_READY", "missing qualified neutral tree")
    base = manifest.get("pinned_base")
    if not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{40}", base) or qualification.get("base_preflight", {}).get("source_revision") != base:
        raise RunError("CASE_NOT_READY", "pinned base mismatch")
    oracle = manifest.get("oracle_command")
    if not isinstance(oracle, list) or not oracle or not all(isinstance(x, str) for x in oracle):
        raise RunError("CASE_NOT_READY", "missing oracle command")
    # The qualified oracle identity is checked before any model call, without revealing it to R/I.
    oracle_name = manifest.get("qualified_oracle_file")
    if not isinstance(oracle_name, str) or Path(oracle_name).name != oracle_name:
        raise RunError("CASE_NOT_READY", "missing qualified oracle file")
    oracle_path = case / oracle_name
    if not oracle_path.is_file() or digest(oracle_path) != qualification.get("heldout_oracle_sha256"):
        raise RunError("CASE_NOT_READY", "held-out oracle digest differs from qualification")
    for part in oracle:
        if part.startswith("{case_dir}/") and not (case / part.split("/", 1)[1]).is_file():
            raise RunError("CASE_NOT_READY", f"missing oracle runner: {part}")
    for name in (*ARMS, "I_COMMON"):
        if not (case / "prompts" / f"{name}.txt").is_file():
            raise RunError("CASE_NOT_READY", f"missing prompt: {name}")
    if not (case / "GOAL.md").is_file():
        raise RunError("CASE_NOT_READY", "missing frozen goal")
    neutralization = manifest.get("neutralization", {})
    for key in ("files", "directories"):
        paths = neutralization.get(key)
        if not isinstance(paths, list) or any(not isinstance(p, str) or Path(p).is_absolute() or ".." in Path(p).parts for p in paths):
            raise RunError("CASE_NOT_READY", f"unsafe neutralization {key}")
    sources = [Path(x) for x in manifest.get("source_candidates", [])]
    source = next((p.resolve() for p in sources if p.is_dir() and command(["git", "-C", str(p), "cat-file", "-e", f"{base}^{{commit}}"], timeout=15).returncode == 0), None)
    if source is None:
        raise RunError("CASE_NOT_READY", "no source candidate contains pinned base")
    cli = resolve_executable([cli_override] if cli_override else manifest.get("environment", {}).get("codex_cli_candidates", []))
    if cli is None:
        raise RunError("HARNESS_INVALID", "Codex CLI executable unavailable")
    return manifest, case, source, cli


def prepare_run(out: Path, force: bool) -> None:
    if out.exists():
        if not force or not (out / MARKER).is_file():
            raise RunError("HARNESS_INVALID", f"output exists (use --force only for a marked runner directory): {out}")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / MARKER).write_text("CADS existential runner v1\n", encoding="utf-8")


def project(manifest: dict, source: Path, out: Path) -> str:
    neutral = out / "neutral"
    neutral.mkdir()
    archive = out / "base.zip"
    git(["-C", str(source), "archive", "--format=zip", "-o", str(archive), manifest["pinned_base"]], source, 120)
    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            destination = (neutral / member.filename).resolve()
            if not destination.is_relative_to(neutral.resolve()):
                raise RunError("HARNESS_INVALID", "unsafe archive member")
        zf.extractall(neutral)
    for name in manifest["neutralization"]["files"]:
        (neutral / name).unlink(missing_ok=True)
    for name in manifest["neutralization"]["directories"]:
        shutil.rmtree(neutral / name, ignore_errors=True)
    git(["init", "--quiet"], neutral)
    git(["add", "-A"], neutral)
    git(["-c", "user.name=CADS Benchmark", "-c", "user.email=benchmark@local.invalid", "commit", "--quiet", "-m", "neutral projection"], neutral, 120)
    tree = git(["rev-parse", "HEAD^{tree}"], neutral)
    if tree != manifest.get("qualified_neutral_tree"):
        raise RunError("CASE_NOT_READY", f"neutral projection differs from qualified tree: {tree}")
    for arm in ARMS:
        target = out / "arms" / arm
        target.parent.mkdir(exist_ok=True)
        git(["clone", "--quiet", str(neutral), str(target)], out, 120)
        if git(["rev-parse", "HEAD^{tree}"], target) != tree:
            raise RunError("HARNESS_INVALID", f"projection mismatch: {arm}")
    return tree


def codex(cli: str, workspace: Path, prompt: str, model: str, effort: str, seconds: int, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    (output / "prompt.md").write_text(prompt, encoding="utf-8")
    args = [cli, "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral", "--json", "-m", model,
            "-c", f'model_reasoning_effort="{effort}"', "-C", str(workspace), "-o", str(output / "last.md")]
    args.append("--dangerously-bypass-approvals-and-sandbox")
    args.append("-")
    started = time.monotonic()
    with (output / "events.jsonl").open("w", encoding="utf-8") as stdout, (output / "stderr.txt").open("w", encoding="utf-8") as stderr:
        process = subprocess.Popen(args, cwd=workspace, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True, encoding="utf-8", errors="replace")
        try:
            process.communicate(prompt, timeout=seconds)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                command(["taskkill", "/PID", str(process.pid), "/T", "/F"], timeout=20)
            else:
                process.kill()
            process.communicate()
            timed_out = True
        else:
            timed_out = False
    last = (output / "last.md").read_text(encoding="utf-8", errors="replace") if (output / "last.md").exists() else ""
    stderr_text = (output / "stderr.txt").read_text(encoding="utf-8", errors="replace")
    event_text = (output / "events.jsonl").read_text(encoding="utf-8", errors="replace")
    usage = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}
    for line in event_text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            observed = event["usage"]
            for key in usage:
                usage[key] += int(observed.get(key) or 0)
    if AUTH_PATTERN.search(last + stderr_text + event_text):
        raise RunError("NEEDS_AUTH", f"Codex auth/quota failure; see {output}")
    if process.returncode not in (0, None) and not timed_out:
        raise RunError("HARNESS_INVALID", f"Codex exit {process.returncode}; see {output}")
    if not last.strip() and not timed_out:
        raise RunError("HARNESS_INVALID", f"Codex returned no final message; see {output}")
    return {"seconds": round(time.monotonic() - started, 2), "timed_out": timed_out, "exit_code": process.returncode,
            "usage": usage,
            "last": last, "output": str(output)}


def run_r(cli: str, workspace: Path, prompt: str, model: str, effort: str, seconds: int, output: Path) -> dict:
    prompt = ("You are R. Inspect only the assigned disposable repository. Do not edit, stage, "
              "delete, or create any file. Do not cause external or production effects. "
              "Do not inspect the hidden oracle, historical reference, sibling arms, or their results.\n\n" + prompt)
    before = git_state(workspace)
    try:
        return codex(cli, workspace, prompt, model, effort, seconds, output)
    finally:
        if git_state(workspace) != before:
            raise RunError("HARNESS_INVALID", f"R changed Git worktree/index: {workspace}; see {output}")


def candidate(workspace: Path, output: Path) -> dict:
    git(["add", "-A"], workspace, 120)
    diff = git(["diff", "--cached", "--binary", "HEAD"], workspace, 120)
    status = git(["status", "--short"], workspace)
    (output / "candidate.diff").write_text(diff + "\n", encoding="utf-8")
    (output / "candidate.status").write_text(status + "\n", encoding="utf-8")
    tree = git(["write-tree"], workspace, 120)
    return {"tree": tree, "diff": diff, "status": status, "state": state_digest(git_state(workspace))}


def review_prompt(goal: str, brief: str, implementation: str, snapshot: dict, repair: bool) -> str:
    instruction = "Return exactly READY or NOT_READY with a brief reason. No more repair is allowed." if repair else "Return exactly READY or REPAIR: followed by one bounded repair brief. If no safe repair is possible, return NOT_READY with a reason."
    return f"You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.\n\n{goal}\n\nIMPLEMENTATION_BRIEF\n{brief}\n\nI completion report:\n{implementation}\n\nCandidate tree: {snapshot['tree']}\nCandidate status:\n{snapshot['status']}\nCandidate diff:\n{snapshot['diff']}\n\n{instruction}\n"


def judgment(text: str, repair_allowed: bool) -> str:
    match = re.search(r"(?m)^\s*(READY|NOT_READY|REPAIR)\b", text)
    if not match or (match.group(1) == "REPAIR" and not repair_allowed):
        raise RunError("HARNESS_INVALID", "R review did not give a valid READY/NOT_READY/REPAIR verdict")
    return match.group(1)


def run_arm(arm: str, case: Path, out: Path, cli: str, ns: argparse.Namespace) -> dict:
    workspace = out / "arms" / arm
    phases = out / "phases" / arm
    r_prompt = (case / "prompts" / f"{arm}.txt").read_text(encoding="utf-8")
    first = run_r(cli, workspace, r_prompt, ns.r_model, ns.r_effort, ns.r_seconds, phases / "r_brief")
    if first["timed_out"]:
        raise RunError("HARNESS_INVALID", f"R brief timed out: {arm}")
    if OWNER_PATTERN.search(first["last"]):
        raise RunError("NEEDS_OWNER", f"R found material Owner ambiguity in {arm}; see {first['output']}")
    brief = first["last"]
    if "IMPLEMENTATION_BRIEF" not in brief:
        raise RunError("HARNESS_INVALID", f"R omitted IMPLEMENTATION_BRIEF: {arm}")
    common = (case / "prompts" / "I_COMMON.txt").read_text(encoding="utf-8")
    i_prompt = f"{common}\n\nIMPLEMENTATION_BRIEF\n{brief}\n\nWork only inside this disposable clone. Do not call external or production services, paid providers, or mutate any path outside this clone. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report NEEDS_OWNER if material Owner intent or authority is missing.\n"
    initial = codex(cli, workspace, i_prompt, ns.i_model, ns.i_effort, ns.i_seconds, phases / "i_initial")
    if OWNER_PATTERN.search(initial["last"]):
        raise RunError("NEEDS_OWNER", f"I found material Owner ambiguity in {arm}; see {initial['output']}")
    snapshot = candidate(workspace, phases / "i_initial")
    review = run_r(cli, workspace, review_prompt(r_prompt, brief, initial["last"], snapshot, False), ns.r_model, ns.r_effort, ns.r_seconds, phases / "r_review")
    if review["timed_out"]:
        raise RunError("HARNESS_INVALID", f"R review timed out: {arm}")
    if OWNER_PATTERN.search(review["last"]):
        raise RunError("NEEDS_OWNER", f"R found material Owner ambiguity in {arm}; see {review['output']}")
    verdict = judgment(review["last"], True)
    repair = None
    final_review = None
    if verdict == "REPAIR":
        repair_prompt = f"{common}\n\nOriginal IMPLEMENTATION_BRIEF:\n{brief}\n\nYour previous completion report:\n{initial['last']}\n\nCurrent candidate tree: {snapshot['tree']}\nCurrent diff:\n{snapshot['diff']}\n\nR repair brief:\n{review['last']}\n\nThis is the sole repair. Work only in this disposable clone. No external or production effects. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report checks actually run and remaining limits.\n"
        repair = codex(cli, workspace, repair_prompt, ns.i_model, ns.i_effort, ns.i_seconds, phases / "i_repair")
        if OWNER_PATTERN.search(repair["last"]):
            raise RunError("NEEDS_OWNER", f"I repair found material Owner ambiguity in {arm}")
        snapshot = candidate(workspace, phases / "i_repair")
        final_review = run_r(cli, workspace, review_prompt(r_prompt, brief + "\nR repair brief:\n" + review["last"], initial["last"] + "\nRepair report:\n" + repair["last"], snapshot, True), ns.r_model, ns.r_effort, ns.r_seconds, phases / "r_final")
        if final_review["timed_out"]:
            raise RunError("HARNESS_INVALID", f"final R review timed out: {arm}")
        if OWNER_PATTERN.search(final_review["last"]):
            raise RunError("NEEDS_OWNER", f"R found material Owner ambiguity in {arm}")
        verdict = judgment(final_review["last"], False)
    return {"brief": brief, "brief_words": len(brief.split()), "r_brief": {k: v for k, v in first.items() if k != "last"},
            "i_initial": {k: v for k, v in initial.items() if k != "last"}, "r_review": {k: v for k, v in review.items() if k != "last"},
            "i_repair": {k: v for k, v in repair.items() if k != "last"} if repair else None,
            "r_final": {k: v for k, v in final_review.items() if k != "last"} if final_review else None,
            "repair_count": int(repair is not None), "verdict": verdict, "candidate_tree": snapshot["tree"], "candidate_state": snapshot["state"]}


def evaluate(manifest: dict, case: Path, out: Path, results: dict) -> None:
    # Freeze and verify every arm before exposing any candidate to the oracle.
    for arm in ARMS:
        frozen = out / "arms" / arm
        if state_digest(git_state(frozen)) != results[arm]["candidate_state"]:
            raise RunError("HARNESS_INVALID", f"candidate changed before oracle: {arm}")
    for arm in ARMS:
        frozen = out / "arms" / arm
        if state_digest(git_state(frozen)) != results[arm]["candidate_state"]:
            raise RunError("HARNESS_INVALID", f"candidate changed before oracle: {arm}")
        evaluation = out / "evaluation" / arm
        shutil.copytree(frozen, evaluation, ignore=shutil.ignore_patterns(".git"))
        replacements = {"{python}": sys.executable, "{case_dir}": str(case), "{candidate_dir}": str(evaluation)}
        args = [next((part.replace(key, value) for key, value in replacements.items() if key in part), part) for part in manifest["oracle_command"]]
        p = command(args, cwd=evaluation, timeout=180)
        log = out / "phases" / arm / "oracle.txt"
        log.write_text(f"exit={p.returncode}\n{p.stdout}\n{p.stderr}", encoding="utf-8")
        results[arm]["oracle"] = "PASS" if p.returncode == 0 else "FAIL" if p.returncode == 1 else "HARNESS_INVALID"
        results[arm]["oracle_log"] = str(log)
        if p.returncode not in (0, 1):
            raise RunError("HARNESS_INVALID", f"oracle failed to run for {arm}: exit {p.returncode}")
        results[arm]["false_done"] = results[arm]["verdict"] == "READY" and p.returncode != 0
        if state_digest(git_state(frozen)) != results[arm]["candidate_state"]:
            raise RunError("HARNESS_INVALID", f"oracle mutated frozen candidate: {arm}")


def save_result(out: Path, result: dict, record_sot: bool) -> None:
    destinations = [out / "result"]
    if record_sot:
        destinations.append(ROOT / "evals" / "existential" / "results" / result["case_id"] / result["run_id"])
    for destination in destinations:
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        lines = [f"# {result['case_id']} existential run", "", f"Status: {result['status']}", f"Run ID: {result['run_id']}", f"Artifacts: {out}", "",
                 "| Arm | R verdict | Candidate tree | Oracle | False DONE |", "| --- | --- | --- | --- | --- |"]
        for arm, data in result.get("arms", {}).items():
            lines.append(f"| {arm} | {data['verdict']} | `{data['candidate_tree']}` | {data.get('oracle', 'NOT_RUN')} | {data.get('false_done', 'N/A')} |")
        if result.get("error"):
            lines += ["", f"Error: {result['error']}"]
        (destination / "result.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def probe(cli: str, ns: argparse.Namespace) -> None:
    with tempfile.TemporaryDirectory(prefix="cads-model-probe-") as directory:
        workspace = Path(directory)
        git(["init", "--quiet"], workspace)
        for role, model, effort, seconds in (("R", ns.r_model, ns.r_effort, ns.r_seconds), ("I", ns.i_model, ns.i_effort, ns.i_seconds)):
            response = codex(cli, workspace, "Reply only MODEL_PROBE_OK. Do not use tools or edit files.", model, effort, min(seconds, 45), workspace / role)
            if response["timed_out"] or "MODEL_PROBE_OK" not in response["last"]:
                raise RunError("HARNESS_INVALID", f"{role} model probe failed; see {response['output']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_id")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--probe-models", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--record-sot", action="store_true")
    parser.add_argument("--r-model", default="gpt-6-sol")
    parser.add_argument("--i-model", default="gpt-6-luna")
    parser.add_argument("--r-effort", default="high", choices=("low", "medium", "high", "xhigh"))
    parser.add_argument("--i-effort", default="medium", choices=("low", "medium", "high", "xhigh"))
    parser.add_argument("--r-seconds", type=int, default=240)
    parser.add_argument("--i-seconds", type=int, default=600)
    parser.add_argument("--codex-cli")
    parser.add_argument("--out", type=Path)
    ns = parser.parse_args()
    if ns.r_seconds < 1 or ns.i_seconds < 1:
        parser.error("timeouts must be positive")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    result = {"schema": "cads-existential-runner-v1", "case_id": ns.case_id, "run_id": run_id, "status": "RUNNING",
              "models": {"R": {"model": ns.r_model, "effort": ns.r_effort, "seconds": ns.r_seconds}, "I": {"model": ns.i_model, "effort": ns.i_effort, "seconds": ns.i_seconds}}, "arms": {}}
    out = ns.out.resolve() if ns.out else Path(tempfile.gettempdir()) / "cads-existential" / ns.case_id / run_id
    prepared = False
    try:
        manifest, case, source, cli = preflight(ns.case_id, ns.codex_cli)
        result.update({"source": str(source), "pinned_base": manifest["pinned_base"], "qualification": str(case / manifest["qualification_file"]), "codex_cli": cli})
        if ns.preflight:
            print(json.dumps({"status": "PREFLIGHT_OK", "case_id": ns.case_id, "source": str(source), "codex_cli": cli}))
            return 0
        if ns.probe_models:
            probe(cli, ns)
            print(json.dumps({"status": "MODELS_OK", "case_id": ns.case_id, "scope": "model availability/quota only; repository read capability untested"}))
            return 0
        if out.is_relative_to(ROOT) or out.is_relative_to(source):
            raise RunError("HARNESS_INVALID", "run output must be outside CADS and source repositories")
        prepare_run(out, ns.force)
        prepared = True
        result["neutral_tree"] = project(manifest, source, out)
        for arm in ARMS:
            result["arms"][arm] = run_arm(arm, case, out, cli, ns)
            save_result(out, result, False)
        evaluate(manifest, case, out, result["arms"])
        result["status"] = "COMPLETE"
    except RunError as exc:
        result["status"] = exc.status
        result["error"] = str(exc)
    except (OSError, subprocess.TimeoutExpired, zipfile.BadZipFile, KeyError, TypeError, ValueError) as exc:
        result["status"] = "HARNESS_INVALID"
        result["error"] = str(exc)
    if prepared:
        save_result(out, result, ns.record_sot)
    print(json.dumps({"status": result["status"], "case_id": ns.case_id, "run_id": run_id, "output": str(out) if prepared else None, "error": result.get("error")}, ensure_ascii=False))
    return 0 if result["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
