from __future__ import annotations
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE / "xp003_oracle.mjs"
RUNTIME = HERE / "xp003_browser_acceptance_runtime.mjs"
FIXTURE = HERE / "xp003_fixture.py"

def git_state(root: Path) -> str:
    parts = []
    for args in (
        ["status", "--porcelain=v1", "-uall"],
        ["diff", "--binary", "HEAD"],
        ["diff", "--cached", "--binary", "HEAD"],
    ):
        cp = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8", check=False)
        if cp.returncode:
            raise RuntimeError("git state failed: " + cp.stderr.strip())
        parts.append(cp.stdout)
    return "\n---\n".join(parts)

def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)

def evaluate(data: dict) -> dict:
    initial = data.get("initial") or {}
    locked = data.get("lockedVoiceStep") or {}
    pending = data.get("speakerFinalizePending") or {}
    complete = data.get("reviewCompletion") or {}
    voice = data.get("voiceSaveState") or {}
    draft = data.get("castingDraftState") or {}
    approved = data.get("castingApprovedState") or {}
    ready = data.get("readyNavigation") or {}

    require(data.get("ok") is True, "browser journey did not complete")
    require(initial.get("reviewOpen") is True and initial.get("voicesOpen") is False, "speaker review is not the clear initial step")
    require(initial.get("unresolvedNotice") is True, "remaining speaker blocker is not visible")
    require(locked.get("locked") is True and str(locked.get("ariaDisabled")) == "true", "voice step is not truthfully locked while speaker review remains")
    require(int(locked.get("voiceRows", -1)) == 0 and int(locked.get("voiceActions", -1)) == 0, "voice controls leak through a speaker-review blocker")
    require(pending.get("voiceLocked") is True and bool(str(pending.get("label") or "").strip()), "speaker-review completion has no clear pending action")
    require(complete.get("reviewComplete") is True, "speaker review never reaches a complete state")
    require(complete.get("voiceOpen") is True and complete.get("voiceEmphasized") is True, "completed speaker review does not lead into voice assignment")
    require(int(complete.get("unresolvedRows", -1)) == 0 and int(complete.get("characterRows", 0)) >= 1, "voice assignment state is inconsistent after speaker review")
    require(voice.get("preflightEnabled") is False, "flow skips required voice-map work")
    require(bool(str(voice.get("step3Action") or "").strip()), "saving voice assignment exposes no clear next action")
    require(bool(str(draft.get("label") or "").strip()), "generated voice map exposes no review/approval action")
    route = str(ready.get("hash") or "")
    require("book=1" in route and "from=1" in route and "to=10" in route, "continue action loses the selected production scope")
    require(data.get("renderCommands") == [], "assignment journey silently starts render")
    return {
        "initial_review_open": True,
        "voice_locked_until_review_complete": True,
        "review_complete": True,
        "voice_step_open_after_review": True,
        "voice_next_action": voice.get("step3Action"),
        "casting_review_action": draft.get("label"),
        "continue_route": route,
        "silent_render": False,
        "approved_state_present": bool(approved),
    }

def main() -> int:
    if len(sys.argv) != 2:
        print(json.dumps({"status":"FAIL","reason":"usage: xp003_oracle_runner.py <candidate-dir>"}))
        return 2
    candidate = Path(sys.argv[1]).resolve()
    probe_target = candidate / "scripts" / "_xp003_oracle.mjs"
    runtime_target = candidate / "scripts" / "_xp003_browser_acceptance_runtime.mjs"
    old_cwd = Path.cwd()
    server = None
    thread = None
    temp_root = None
    before = ""
    result = {"status": "FAIL", "reason": "oracle did not run"}
    code = 1
    try:
        before = git_state(candidate)
        sys.path.insert(0, str(candidate))
        os.chdir(candidate)
        spec = importlib.util.spec_from_file_location("xp003_hidden_fixture", FIXTURE)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load hidden fixture")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        handler = module.AssignmentWorkflowFixtureHandler
        handler.reset()

        shutil.copyfile(PROBE, probe_target)
        shutil.copyfile(RUNTIME, runtime_target)
        temp_root = Path(tempfile.mkdtemp(prefix="xp003-oracle-"))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        env = os.environ.copy()
        env["STORY_AUDIO_ASSIGNMENT_TEST_ROOT"] = str(temp_root)
        cp = subprocess.run(
            ["node", "scripts/_xp003_oracle.mjs", f"http://127.0.0.1:{server.server_port}"],
            cwd=candidate, env=env, capture_output=True, text=True, encoding="utf-8",
            timeout=150, check=False,
        )
        if cp.returncode != 0:
            raise RuntimeError("browser probe failed: " + (cp.stderr.strip() or cp.stdout.strip())[-2000:])
        data = json.loads(cp.stdout)
        evidence = evaluate(data)
        result = {"status": "PASS", "evidence": evidence}
        code = 0
    except Exception as exc:
        result = {"status": "FAIL", "reason": f"{type(exc).__name__}: {exc}"}
        code = 1
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=5)
        probe_target.unlink(missing_ok=True)
        runtime_target.unlink(missing_ok=True)
        if temp_root is not None:
            shutil.rmtree(temp_root, ignore_errors=True)
        os.chdir(old_cwd)
        try:
            after = git_state(candidate)
            if before and after != before:
                result = {"status": "FAIL", "reason": "oracle mutated candidate worktree"}
                code = 1
        except Exception as exc:
            result = {"status": "FAIL", "reason": f"post-oracle state check failed: {exc}"}
            code = 1
    print(json.dumps(result, ensure_ascii=True))
    return code

if __name__ == "__main__":
    raise SystemExit(main())