from __future__ import annotations

from contextlib import contextmanager
import hashlib
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1]
SCRIPT = PACKAGE / "skills" / "documentation-handoff-continuity" / "scripts" / "continuity.py"
AI = PACKAGE / "scripts" / "ai.py"
AI_OS = PACKAGE / "scripts" / "ai_os.py"


def git(root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, timeout=30)
    if check and proc.returncode:
        raise AssertionError(proc.stderr)
    return proc.stdout.strip()


@contextmanager
def fixture(name: str = "sidecar"):
    with tempfile.TemporaryDirectory(prefix=f"continuity-{name}-") as raw:
        root = Path(raw); git(root, "init", "-q"); git(root, "config", "user.email", "fixture@example.invalid"); git(root, "config", "user.name", "Fixture")
        (root / "app.py").write_text("x = 1\n", encoding="utf-8"); (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
        git(root, "add", "app.py", "README.md"); git(root, "commit", "-qm", "baseline")
        yield root


def invoke(root: Path, task: str, command: str, *args: str, check: bool = True) -> tuple[int, dict]:
    proc = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--task-id", task, command, *args], text=True, capture_output=True, timeout=45)
    try: payload = json.loads(proc.stdout)
    except ValueError as exc: raise AssertionError(proc.stdout + proc.stderr) from exc
    if check and proc.returncode: raise AssertionError(payload)
    return proc.returncode, payload


def invoke_revision(root: Path, task: str, revision: str, command: str, *args: str, check: bool = True) -> tuple[int, dict]:
    proc = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--task-id", task, "--revision", revision, command, *args], text=True, capture_output=True, timeout=45)
    try: payload = json.loads(proc.stdout)
    except ValueError as exc: raise AssertionError(proc.stdout + proc.stderr) from exc
    if check and proc.returncode: raise AssertionError(payload)
    return proc.returncode, payload


def no_docs(root: Path, task: str = "SIDE-1") -> dict:
    _, value = invoke(root, task, "bootstrap", "--next-safe-action", "edit fixture", "--documentation-impact", "NO", "--category", "IMPLEMENTATION_ONLY", "--documentation-rationale", "implementation only")
    return value


def legacy_ready(root: Path, task: str = "LEGACY-1") -> tuple[Path, bytes]:
    """Build a disposable pre-1.0.2 sidecar with a closed r002 successor."""
    git(root, "branch", "accepted")
    (root / ".buildos-policy.json").write_text(json.dumps({"documentation_handoff": {"accepted_ref": "accepted", "category_authorities": {}}}), encoding="utf-8")
    git(root, "add", ".buildos-policy.json"); git(root, "commit", "-qm", "policy"); git(root, "branch", "-f", "accepted", "HEAD")
    created = no_docs(root, task)
    path = Path(created["sidecar"]); value = json.loads(path.read_text(encoding="utf-8"))
    value["skill"]["version"] = "1.0.1"; value["kernel"]["phase"] = "UNOBSERVED"
    without = {k: v for k, v in value.items() if k != "self_hash"}
    value["self_hash"] = hashlib.sha256(json.dumps(without, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    original = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    path.write_bytes(original)
    successor_sidecar = no_docs(root, "SUCCESSOR-1")
    successor_check = f'"{sys.executable}" -c "print(1)"'
    boot = subprocess.run([sys.executable, str(AI), "--root", str(root), "bootstrap", "--task-id", "SUCCESSOR-1", "--outcome", "successor", "--allow", "app.py", "--check", successor_check], text=True, capture_output=True, timeout=60)
    if boot.returncode: raise AssertionError(boot.stdout + boot.stderr)
    (root / "app.py").write_text("x = 2\n", encoding="utf-8"); git(root, "add", "app.py"); git(root, "commit", "-qm", "successor r1")
    for command in (["record-commit"], ["validate", "--inspected-by", "fixture-worker"], ["close"]):
        result = subprocess.run([sys.executable, str(AI), "--root", str(root), *command], text=True, capture_output=True, timeout=60)
        if result.returncode: raise AssertionError(result.stdout + result.stderr)
    revised = subprocess.run([sys.executable, str(AI_OS), "--root", str(root), "new-revision", "--reason", "supersede legacy fixture"], text=True, capture_output=True, timeout=60)
    if revised.returncode: raise AssertionError(revised.stdout + revised.stderr)
    (root / "app.py").write_text("x = 3\n", encoding="utf-8"); git(root, "add", "app.py"); git(root, "commit", "-qm", "successor r2")
    for command in (["record-commit"], ["validate", "--inspected-by", "fixture-worker"], ["close"]):
        result = subprocess.run([sys.executable, str(AI), "--root", str(root), *command], text=True, capture_output=True, timeout=60)
        if result.returncode: raise AssertionError(result.stdout + result.stderr)
    git(root, "branch", "-f", "accepted", "HEAD")
    return path, original


class ContinuitySidecarTests(unittest.TestCase):
    def test_legacy_quarantine_is_explicit_immutable_and_not_retirement(self):
        with fixture("legacy-quarantine") as root:
            path, original = legacy_ready(root)
            code, missing = invoke_revision(root, "LEGACY-1", "r001", "quarantine-legacy", "--tech-lead-authority", "", check=False)
            self.assertEqual(code, 2); self.assertIn("authority", missing["message"])
            code, normal = invoke_revision(root, "LEGACY-1", "r001", "retire", check=False)
            self.assertEqual(code, 2); self.assertIn("does not match Build OS revision", normal["message"])
            result = invoke_revision(root, "LEGACY-1", "1", "quarantine-legacy", "--tech-lead-authority", "TECH_LEAD_APPROVED migration")[1]
            archive = Path(result["archive"])
            self.assertEqual(result["status"], "QUARANTINED_LEGACY")
            self.assertEqual((archive / "original.sidecar.json").read_bytes(), original)
            record = json.loads((archive / "quarantine.json").read_text(encoding="utf-8"))
            self.assertEqual(record["classification"], "QUARANTINED_LEGACY"); self.assertEqual(record["revision"], 1)
            self.assertFalse(path.exists())
            takeover = invoke(root, "LEGACY-1", "takeover", check=False)[1]
            self.assertEqual(takeover["status"], "HISTORICAL_QUARANTINED")

    def test_legacy_quarantine_rejects_unknown_provenance_integrity_dirty_and_cross_task(self):
        with fixture("legacy-quarantine-rejections") as root:
            path, original = legacy_ready(root, "LEGACY-REJECT")
            path.write_bytes(b"{}")
            code, invalid = invoke_revision(root, "LEGACY-REJECT", "1", "quarantine-legacy", "--tech-lead-authority", "TECH_LEAD_APPROVED migration", check=False)
            self.assertEqual(code, 2); self.assertIn("sidecar", invalid["message"])
            path.write_bytes(original)
            value = json.loads(original); value["skill"]["version"] = "1.0.3"; value["self_hash"] = hashlib.sha256(json.dumps({k: v for k, v in value.items() if k != "self_hash"}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest(); path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
            code, provenance = invoke_revision(root, "LEGACY-REJECT", "1", "quarantine-legacy", "--tech-lead-authority", "TECH_LEAD_APPROVED migration", check=False)
            self.assertEqual(code, 2); self.assertIn("malformed", provenance["message"])
            path.write_bytes(original)
            (root / "app.py").write_text("dirty\n", encoding="utf-8")
            code, dirty_state = invoke_revision(root, "LEGACY-REJECT", "1", "quarantine-legacy", "--tech-lead-authority", "TECH_LEAD_APPROVED migration", check=False)
            self.assertEqual(code, 2); self.assertIn("clean worktree", dirty_state["message"])
            code, cross_task = invoke_revision(root, "OTHER-LEGACY", "1", "quarantine-legacy", "--tech-lead-authority", "TECH_LEAD_APPROVED migration", check=False)
            self.assertEqual(code, 2); self.assertIn("missing", cross_task["message"])

    def test_explicit_revision_canonicalizes_across_lifecycle_and_retires_only_closed(self):
        ai = PACKAGE / "scripts" / "ai.py"
        with fixture("revision-convergence") as root:
            git(root, "branch", "accepted")
            (root / ".buildos-policy.json").write_text(json.dumps({"documentation_handoff": {"accepted_ref": "accepted", "category_authorities": {}}}), encoding="utf-8")
            git(root, "add", ".buildos-policy.json"); git(root, "commit", "-qm", "policy"); git(root, "branch", "-f", "accepted", "HEAD")
            check = f'"{sys.executable}" "{SCRIPT}" --root "{root}" --task-id REV-1 docs-check'
            boot = subprocess.run([sys.executable, str(ai), "--root", str(root), "bootstrap", "--task-id", "REV-1", "--outcome", "revision fixture", "--allow", "app.py", "--check", check], text=True, capture_output=True, timeout=60)
            self.assertEqual(boot.returncode, 0, boot.stdout + boot.stderr)

            numeric = invoke_revision(root, "REV-1", "1", "bootstrap", "--next-safe-action", "continue", "--documentation-impact", "NO", "--category", "IMPLEMENTATION_ONLY", "--documentation-rationale", "implementation only")[1]
            canonical = invoke_revision(root, "REV-1", "r001", "checkpoint", "--expected-sidecar-hash", numeric["sidecar_hash"], "--next-safe-action", "continue", "--documentation-impact", "NO", "--category", "IMPLEMENTATION_ONLY", "--documentation-rationale", "implementation only")[1]
            self.assertEqual(Path(numeric["sidecar"]).resolve(), Path(canonical["sidecar"]).resolve())
            self.assertTrue(str(Path(canonical["sidecar"])).replace("\\", "/").endswith("/r001/" + json.loads(Path(canonical["sidecar"]).read_text())["worktree"]["id"] + ".json"))
            self.assertEqual(invoke_revision(root, "REV-1", "r001", "verify")[1]["status"], "SAFE_TO_CONTINUE")
            self.assertEqual(invoke_revision(root, "REV-1", "1", "takeover")[1]["status"], "SAFE_TO_CONTINUE")
            self.assertEqual(invoke_revision(root, "REV-1", "r001", "docs-check")[1]["status"], "PASS")

            code, active = invoke_revision(root, "REV-1", "1", "retire", check=False)
            self.assertEqual(code, 2); self.assertIn("retirement requires Build OS CLOSED", active["message"])
            code, wrong = invoke_revision(root, "REV-1", "2", "verify", check=False)
            self.assertEqual(code, 2); self.assertIn("does not match Build OS revision", wrong["message"])
            code, missing = invoke(root, "MISSING-REVISION", "verify", check=False)
            self.assertEqual(code, 2); self.assertIn("sidecar", missing["message"])
            code, cross_task = invoke(root, "OTHER-TASK", "retire", check=False)
            self.assertEqual(code, 2); self.assertIn("sidecar", cross_task["message"])

            (root / "app.py").write_text("x = 2\n", encoding="utf-8"); git(root, "add", "app.py"); git(root, "commit", "-qm", "product")
            self.assertEqual(subprocess.run([sys.executable, str(ai), "--root", str(root), "record-commit"], text=True, capture_output=True, timeout=60).returncode, 0)
            self.assertEqual(subprocess.run([sys.executable, str(ai), "--root", str(root), "validate", "--inspected-by", "fixture-worker"], text=True, capture_output=True, timeout=60).returncode, 0)
            self.assertEqual(subprocess.run([sys.executable, str(ai), "--root", str(root), "close"], text=True, capture_output=True, timeout=60).returncode, 0)
            self.assertEqual(invoke_revision(root, "REV-1", "r001", "retire")[1]["status"], "CLOSED_PENDING_BASELINE_ADVANCE")
            git(root, "branch", "-f", "accepted", "HEAD")
            retired = invoke_revision(root, "REV-1", "1", "retire")[1]
            self.assertEqual(retired["status"], "RETIRED")
            archive = Path(retired["archive"])
            self.assertTrue((archive / "terminal.json").is_file()); self.assertTrue((archive / "receipt.json").is_file())
            self.assertFalse(Path(canonical["sidecar"]).exists())

    def test_retirement_cannot_cross_worktree_identity(self):
        with fixture("cross-worktree") as root:
            no_docs(root, "CROSS-WORKTREE")
            sibling = root.parent / (root.name + "-sibling")
            git(root, "worktree", "add", "-q", str(sibling), "HEAD")
            try:
                code, result = invoke(sibling, "CROSS-WORKTREE", "retire", check=False)
                self.assertEqual(code, 2)
                self.assertIn("sidecar", result["message"])
            finally:
                git(root, "worktree", "remove", "--force", str(sibling), check=False)

    def test_generic_adoption_smoke_through_close_and_baseline_retirement(self):
        ai = PACKAGE / "scripts" / "ai.py"
        with fixture("full-flow") as root:
            git(root, "branch", "accepted")
            (root / ".buildos-policy.json").write_text(json.dumps({"documentation_handoff": {"accepted_ref": "accepted", "category_authorities": {}}}), encoding="utf-8")
            git(root, "add", ".buildos-policy.json"); git(root, "commit", "-qm", "adopt policy")
            git(root, "branch", "-f", "accepted", "HEAD")
            check = f'"{sys.executable}" "{SCRIPT}" --root "{root}" --task-id FLOW-1 docs-check'
            boot = subprocess.run([sys.executable, str(ai), "--root", str(root), "bootstrap", "--task-id", "FLOW-1", "--outcome", "flow works", "--allow", "app.py", "--check", check], text=True, capture_output=True, timeout=45)
            self.assertEqual(boot.returncode, 0, boot.stdout + boot.stderr)
            no_docs(root, "FLOW-1")
            (root / "app.py").write_text("x = 2\n", encoding="utf-8"); git(root, "add", "app.py"); git(root, "commit", "-qm", "product")
            self.assertEqual(subprocess.run([sys.executable, str(ai), "--root", str(root), "record-commit"], text=True, capture_output=True, timeout=45).returncode, 0)
            validated = subprocess.run([sys.executable, str(ai), "--root", str(root), "validate", "--inspected-by", "fixture-worker"], text=True, capture_output=True, timeout=45)
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            self.assertEqual(subprocess.run([sys.executable, str(ai), "--root", str(root), "close"], text=True, capture_output=True, timeout=45).returncode, 0)
            pending = invoke(root, "FLOW-1", "retire")[1]
            self.assertEqual(pending["status"], "CLOSED_PENDING_BASELINE_ADVANCE")
            git(root, "branch", "-f", "accepted", "HEAD")
            retired = invoke(root, "FLOW-1", "retire")[1]
            self.assertEqual(retired["status"], "RETIRED")

    def test_clean_bootstrap_self_hash_size_and_common_git_dir(self):
        with fixture() as root:
            result = no_docs(root)
            path = Path(result["sidecar"]); data = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(str(path).startswith(str(root / ".git" / "buildos-continuity")))
            self.assertLessEqual(result["bytes"], 16 * 1024)
            self.assertEqual(data["self_hash"], hashlib.sha256(json.dumps({k: v for k, v in data.items() if k != "self_hash"}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest())
            self.assertEqual(invoke(root, "SIDE-1", "verify")[1]["status"], "SAFE_TO_CONTINUE")

    def test_working_set_is_read_only_bounded_and_surfaces_live_mismatches(self):
        with fixture("capsule") as root:
            check = f'"{sys.executable}" "{SCRIPT}" --root "{root}" --task-id CAPSULE-1 docs-check'
            boot = subprocess.run([sys.executable, str(AI), "--root", str(root), "bootstrap", "--task-id", "CAPSULE-1", "--outcome", "capsule objective", "--accept", "fixture acceptance", "--allow", "app.py", "--check", check], text=True, capture_output=True, timeout=60)
            self.assertEqual(boot.returncode, 0, boot.stdout + boot.stderr)
            sidecar = no_docs(root, "CAPSULE-1")
            before = Path(sidecar["sidecar"]).read_bytes()
            result = invoke(root, "CAPSULE-1", "working-set")[1]
            self.assertEqual(result["status"], "SAFE_TO_CONTINUE")
            self.assertLessEqual(result["bytes"], 4 * 1024)
            self.assertLessEqual(result["bytes"], 8 * 1024)
            self.assertIn("projection=READ_ONLY_DERIVED", result["capsule"])
            self.assertIn("current_objective=capsule objective", result["capsule"])
            self.assertIn("unresolved_acceptance=fixture acceptance", result["capsule"])
            self.assertIn("accepted_ref=HEAD", result["capsule"])
            self.assertEqual(Path(sidecar["sidecar"]).read_bytes(), before)
            alias = invoke(root, "CAPSULE-1", "capsule")[1]
            self.assertEqual(alias["status"], "SAFE_TO_CONTINUE")
            (root / "app.py").write_text("dirty capsule\n", encoding="utf-8")
            stale = invoke(root, "CAPSULE-1", "working-set")[1]
            self.assertEqual(stale["status"], "NEEDS_RECONCILIATION")
            self.assertIn("dirty state changed", stale["problems"])
            self.assertIn("mismatches=dirty state changed", stale["capsule"])

    def test_working_set_declares_bounded_overflow_without_evidence_bodies(self):
        with fixture("capsule-overflow") as root:
            decisions = []
            for index in range(16):
                decisions.extend(["--decision", f"decision-{index}-" + "x" * 100])
            invoke(root, "CAPSULE-OVERFLOW", "bootstrap", "--next-safe-action", "continue", "--documentation-impact", "NO", "--category", "IMPLEMENTATION_ONLY", "--documentation-rationale", "implementation only", *decisions)
            result = invoke(root, "CAPSULE-OVERFLOW", "working-set")[1]
            self.assertEqual(result["status"], "SAFE_TO_CONTINUE")
            self.assertLessEqual(result["bytes"], 4 * 1024)
            self.assertIn("additional_decisions=12", result["capsule"])
            self.assertNotIn("decision-15-", result["capsule"])

    def test_bootstrap_long_acceptance_is_capsule_representable_without_abort(self):
        """Reproduce CINEMATIC-COLOR-GRADE-V1's former 120-char failure."""
        with fixture("acceptance-bound") as root:
            long_acceptance = "Safety validation preserves the production boundary and proves the unresolved failure path remains blocked: " + "x" * 180
            check = f'"{sys.executable}" -c "print(1)"'
            boot = subprocess.run(
                [sys.executable, str(AI), "--root", str(root), "bootstrap", "--task-id", "CINEMATIC-COLOR-GRADE-V1", "--outcome", "candidate passes", "--accept", long_acceptance, "--allow", "app.py", "--check", check],
                text=True, capture_output=True, timeout=60,
            )
            self.assertEqual(boot.returncode, 0, boot.stdout + boot.stderr)
            no_docs(root, "CINEMATIC-COLOR-GRADE-V1")
            result = invoke(root, "CINEMATIC-COLOR-GRADE-V1", "working-set")[1]
            self.assertEqual(result["status"], "TARGETED_READ_REQUIRED")
            self.assertLessEqual(result["bytes"], 4 * 1024)
            self.assertLessEqual(result["bytes"], 8 * 1024)
            self.assertIn("TARGETED_READ_REQUIRED acceptance[0] sha256=", result["capsule"])
            self.assertIn(".buildos/control/CURRENT", result["capsule"])
            self.assertNotIn(long_acceptance, result["capsule"])

    def test_atomic_cas_corruption_and_size_rejections(self):
        with fixture() as root:
            first = no_docs(root); expected = first["sidecar_hash"]
            _, second = invoke(root, "SIDE-1", "checkpoint", "--expected-sidecar-hash", expected, "--kind", "decision", "--next-safe-action", "continue", "--documentation-impact", "NO", "--category", "IMPLEMENTATION_ONLY", "--documentation-rationale", "still implementation only")
            self.assertNotEqual(expected, second["sidecar_hash"])
            code, conflict = invoke(root, "SIDE-1", "checkpoint", "--expected-sidecar-hash", expected, "--next-safe-action", "continue", "--documentation-impact", "NO", "--category", "IMPLEMENTATION_ONLY", "--documentation-rationale", "still implementation only", check=False)
            self.assertEqual(code, 2); self.assertIn("compare-and-swap", conflict["message"])
            Path(second["sidecar"]).write_text("{}", encoding="utf-8")
            code, corrupt = invoke(root, "SIDE-1", "verify", check=False)
            self.assertEqual(code, 2); self.assertIn("schema", corrupt["message"])
        with fixture("large") as root:
            code, large = invoke(root, "SIDE-LARGE", "bootstrap", "--next-safe-action", "x" * 300, "--completed-summary", "x" * 800, "--documentation-impact", "NO", "--category", "IMPLEMENTATION_ONLY", "--documentation-rationale", "x" * 800, check=False)
            self.assertEqual(code, 2); self.assertIn("exceeds", large["message"])

    def test_dirty_fingerprints_and_secret_rejection_fail_closed(self):
        with fixture() as root:
            first = no_docs(root); path = Path(first["sidecar"])
            (root / "app.py").write_text("changed\n", encoding="utf-8")
            verify = invoke(root, "SIDE-1", "verify", check=False)[1]
            self.assertEqual(verify["status"], "NEEDS_RECONCILIATION"); self.assertIn("dirty state changed", verify["problems"])
            git(root, "add", "app.py")
            self.assertIn("dirty state changed", invoke(root, "SIDE-1", "verify", check=False)[1]["problems"])
            git(root, "reset", "--", "app.py")
            (root / "untracked.txt").write_text("untracked", encoding="utf-8")
            self.assertIn("dirty state changed", invoke(root, "SIDE-1", "verify", check=False)[1]["problems"])
            code, secret = invoke(root, "SIDE-SECRET", "bootstrap", "--next-safe-action", "Bearer abc", "--documentation-impact", "NO", "--category", "IMPLEMENTATION_ONLY", "--documentation-rationale", "implementation only", check=False)
            self.assertEqual(code, 2); self.assertIn("secret-like", secret["message"])
            self.assertTrue(path.is_file())

    def test_docs_unknown_yes_stale_and_semantic_declaration(self):
        with fixture("docs") as root:
            code, unknown = invoke(root, "SIDE-UNKNOWN", "bootstrap", "--next-safe-action", "classify", "--documentation-impact", "UNKNOWN", "--documentation-rationale", "pending", check=False)
            self.assertEqual(code, 0); self.assertEqual(invoke(root, "SIDE-UNKNOWN", "docs-check", check=False)[0], 2)
            policy = {"documentation_handoff": {"accepted_ref": "HEAD", "category_authorities": {"DEVELOPER_WORKFLOW": "README.md"}}}
            (root / ".buildos-policy.json").write_text(json.dumps(policy), encoding="utf-8")
            code, missing = invoke(root, "SIDE-YES-MISSING", "bootstrap", "--next-safe-action", "document", "--documentation-impact", "YES", "--category", "DEVELOPER_WORKFLOW", check=False)
            self.assertEqual(code, 2); self.assertIn("semantic", missing["message"])
            yes = invoke(root, "SIDE-YES", "bootstrap", "--next-safe-action", "commit", "--documentation-impact", "YES", "--category", "DEVELOPER_WORKFLOW", "--semantic-inspection", "worker verified implemented behavior") [1]
            self.assertEqual(invoke(root, "SIDE-YES", "docs-check")[1]["status"], "PASS")
            (root / "README.md").write_text("# stale\n", encoding="utf-8")
            stale = invoke(root, "SIDE-YES", "docs-check", check=False)[1]
            self.assertEqual(stale["status"], "FAIL"); self.assertTrue(any("stale" in p for p in stale["problems"]))
            self.assertTrue(Path(yes["sidecar"]).is_file())

    def test_moved_accepted_ref_and_takeover_are_reconciled(self):
        with fixture("ref") as root:
            git(root, "branch", "accepted")
            result = invoke(root, "SIDE-REF", "bootstrap", "--accepted-ref", "accepted", "--next-safe-action", "hold", "--documentation-impact", "NO", "--category", "IMPLEMENTATION_ONLY", "--documentation-rationale", "implementation only")[1]
            (root / "app.py").write_text("advance\n", encoding="utf-8"); git(root, "add", "app.py"); git(root, "commit", "-qm", "advance"); git(root, "branch", "-f", "accepted", "HEAD")
            self.assertIn("accepted ref moved", invoke(root, "SIDE-REF", "verify", check=False)[1]["problems"])
            takeover = invoke(root, "SIDE-REF", "takeover", check=False)[1]
            self.assertIn(takeover["status"], {"NEEDS_RECONCILIATION", "RECOVERY_REQUIRED"})
            self.assertTrue(Path(result["sidecar"]).is_file())


class PortablePackageContractTests(unittest.TestCase):
    def test_manifest_skill_policy_and_frozen_kernel_contract(self):
        manifest = json.loads((PACKAGE / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["frozen_kernel_commit"], "01e68e86d67e974dd50573127baa78060bfcfafa")
        self.assertTrue(manifest["continuity_skill"]["mandatory_by_adoption_contract"])
        self.assertFalse(manifest["continuity_skill"]["kernel_enforced"])
        self.assertTrue((PACKAGE / "adoption" / "initialize.ps1").is_file())
        self.assertTrue((PACKAGE / "skills" / "documentation-handoff-continuity" / "references" / "handoff.schema.json").is_file())
        expected = {
            line.split("  ", 1)[1]: line.split("  ", 1)[0]
            for line in (PACKAGE / "FROZEN_KERNEL.sha256").read_text(encoding="ascii").splitlines() if line
        }
        observed = {
            item.relative_to(PACKAGE).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest()
            for item in (PACKAGE / "buildos").rglob("*") if item.is_file() and "__pycache__" not in item.parts
        }
        self.assertEqual(observed, expected)

    def test_continuity_skill_version_and_bounded_checkpoint_guidance(self):
        source = (PACKAGE / "skills" / "documentation-handoff-continuity" / "scripts" / "continuity.py").read_text(encoding="utf-8")
        guide = (PACKAGE / "skills" / "documentation-handoff-continuity" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('SKILL_VERSION = "1.1.0"', source)
        self.assertIn("Do not checkpoint every tool call", guide)
        self.assertIn("Field Study measurement", guide)
        self.assertIn("working-set", guide)


if __name__ == "__main__":
    unittest.main(verbosity=2)
