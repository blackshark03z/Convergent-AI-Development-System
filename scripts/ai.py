#!/usr/bin/env python3
"""Worker facade with an opt-in context-epoch adoption preflight."""
import json
import os
from pathlib import Path
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parents[1]
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))

from buildos.cli import main


MUTATING_COMMANDS = {
    "record-commit", "validate", "rollover", "close", "block-for-source-fix",
    "continue-task", "report-blocker", "replan", "effect", "review",
}
ADMISSION_COMMANDS = {
    "admit", "bootstrap", "record-commit", "validate", "rollover", "close",
    "block-for-source-fix", "continue-task", "report-blocker", "replan", "effect", "review",
}


def _requested_root(argv: list[str]) -> Path:
    for index, value in enumerate(argv[:-1]):
        if value == "--root":
            return Path(argv[index + 1]).resolve()
    return Path.cwd().resolve()


def _requested_command(argv: list[str]) -> str | None:
    known = {
        "admit", "bootstrap", "status", "next", "record-commit", "validate",
        "rollover", "close", "recover", "block-for-source-fix", "continue-task",
        "report-blocker", "replan", "effect", "review", "assurance-plan",
    }
    return next((value for value in argv if value in known), None)


def _context_epoch_preflight_enabled(root: Path) -> bool:
    """Enable the adoption-layer guard only for an explicitly enrolled project."""
    override = os.environ.get("BUILDOS_CONTEXT_EPOCH_PREFLIGHT", "").strip().lower()
    if override in {"1", "true", "yes", "on"}:
        return True
    if override in {"0", "false", "no", "off"}:
        return False
    try:
        policy = json.loads((root / ".buildos-policy.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    context_epoch = policy.get("context_epoch") if isinstance(policy, dict) else None
    return isinstance(context_epoch, dict) and context_epoch.get("enabled") is True


def _policy(root: Path) -> dict:
    try:
        value = json.loads((root / ".buildos-policy.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _integrated_admission_enabled(root: Path) -> bool:
    value = _policy(root).get("execution_admission")
    return isinstance(value, dict) and value.get("enabled") is True


def _run_preflight(command: list[str], *, root: Path) -> int:
    proc = subprocess.run(command, cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True)
    if proc.returncode:
        print(proc.stdout.strip() or json.dumps({
            "status": "ACTION_REQUIRED", "message": "integrated execution admission failed",
        }, sort_keys=True))
    return proc.returncode


def _adoption_preflight(argv: list[str]) -> int:
    """Compose opt-in adoption checks behind the one public facade."""
    command = _requested_command(argv)
    if command not in ADMISSION_COMMANDS:
        return 0
    root = _requested_root(argv)
    if not _integrated_admission_enabled(root):
        return 0
    policy = _policy(root).get("execution_admission") or {}
    if policy.get("require_authority_record") is not True:
        print(json.dumps({
            "status": "ACTION_REQUIRED",
            "message": "execution_admission.require_authority_record must remain true",
        }, sort_keys=True))
        return 2
    authority = PACKAGE / "skills" / "project-lifecycle-bootstrap" / "scripts" / "execution_authority.py"
    code = _run_preflight([sys.executable, str(authority), "--root", str(root), "check"], root=root)
    if code:
        return code
    lifecycle = PACKAGE / "skills" / "project-lifecycle-bootstrap" / "scripts" / "project_lifecycle.py"
    return _run_preflight([sys.executable, str(lifecycle), "--root", str(root), "check"], root=root)


def _epoch_preflight(argv: list[str]) -> int:
    if _requested_command(argv) not in MUTATING_COMMANDS:
        return 0
    root = _requested_root(argv)
    if not _context_epoch_preflight_enabled(root):
        return 0
    script = PACKAGE / "skills" / "project-lifecycle-bootstrap" / "scripts" / "context_epoch.py"
    proc = subprocess.run([sys.executable, str(script), "--root", str(root), "preflight"], text=True, capture_output=True)
    if proc.returncode:
        # Keep the public facade JSON-only and fail closed before the kernel mutation.
        print(proc.stdout.strip() or '{"status":"ACTION_REQUIRED","message":"context epoch ownership preflight failed"}')
    return proc.returncode


if __name__ == "__main__":
    preflight = _adoption_preflight(sys.argv[1:]) or _epoch_preflight(sys.argv[1:])
    raise SystemExit(preflight or main(admin=False))
