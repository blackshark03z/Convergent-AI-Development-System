from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
LIFECYCLE = PACKAGE / "skills" / "project-lifecycle-bootstrap" / "scripts" / "project_lifecycle.py"
CONTINUITY = PACKAGE / "skills" / "documentation-handoff-continuity" / "scripts" / "continuity.py"
AI = PACKAGE / "scripts" / "ai.py"


def git(root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, timeout=45)
    if check and proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


def policy(*, profile: str = "small-tool", custom_paths: bool = False, modules: dict | None = None) -> dict:
    pack = {
        "readme": "README.md", "project_status": "PROJECT_STATUS.md", "architecture": "ARCHITECTURE.md",
        "engineering": "ENGINEERING.md", "roadmap": "ROADMAP.md", "changelog": "CHANGELOG.md",
    }
    if custom_paths:
        pack = {
            "readme": "guide/START.md", "project_status": "guide/STATUS.md", "architecture": "guide/ARCH.md",
            "engineering": "guide/ENGINEERING.md", "roadmap": "guide/PLAN.md", "changelog": "guide/HISTORY.md",
        }
    enabled = {"operations": False, "adr": False, "security": False, "migrations": False, "project_closure": False, "project_brief": False}
    enabled.update(modules or {})
    return {
        "schema": "buildos.project-policy.v1.22",
        "documentation_handoff": {
            "accepted_ref": "accepted",
            "category_authorities": {
                "USER_BEHAVIOR": pack["readme"], "ARCHITECTURE_OWNERSHIP_BOUNDARY": pack["architecture"],
                "API_CONFIG_SCHEMA": pack["project_status"], "DEVELOPER_WORKFLOW": pack["engineering"],
                "FEATURE_PRESET_INVENTORY": pack["project_status"],
            },
            "continuity": {"mandatory_operational_skill": "documentation-handoff-continuity", "max_sidecar_bytes": 16384, "field_study": "EXTERNAL_APPEND_ONLY_NON_AUTHORITATIVE"},
        },
        "project_lifecycle": {
            "project_profile": profile,
            "project_intent": {"name": "Fixture", "purpose": "Prove portable lifecycle behavior.", "intended_use": "Fixture users.", "success_definition": "Tests pass.", "non_goals": "No production service.", "constraints": "Local Git only."},
            "knowledge_pack": pack,
            "quality_gates": [{"id": "python-smoke", "command": f'"{sys.executable}" -c "print(\'quality gate\')"'}],
            "testing_strategy": "Run focused deterministic tests and relevant regression.",
            "engineering_conventions": "Keep boundaries explicit and dependencies minimal.",
            "safety_boundaries": {"runtime": "Local process only.", "production": "No production runtime.", "data": "Fixture data only.", "secrets": "No secrets in source."},
            "modules": enabled,
        },
    }


def trusted_policy() -> dict:
    value = policy()
    value["project_lifecycle"]["quality_gates"] = [{
        "id": "python-smoke", "argv": [sys.executable, "-c", "print('trusted quality gate')"],
        "provenance": "OWNER_AUTHORED",
    }]
    return value


@contextmanager
def fixture(name: str = "lifecycle"):
    with tempfile.TemporaryDirectory(prefix=f"{name}-") as raw:
        root = Path(raw)
        git(root, "init", "-q"); git(root, "config", "user.email", "fixture@example.invalid"); git(root, "config", "user.name", "Fixture")
        (root / "app.txt").write_text("baseline\n", encoding="utf-8")
        git(root, "add", "app.txt"); git(root, "commit", "-qm", "baseline"); git(root, "branch", "accepted")
        yield root


def invoke(root: Path, command: str, *args: str, check: bool = True) -> tuple[int, dict]:
    proc = subprocess.run([sys.executable, str(LIFECYCLE), "--root", str(root), command, *args], text=True, capture_output=True, timeout=240)
    try: data = json.loads(proc.stdout)
    except ValueError as exc: raise AssertionError(proc.stdout + proc.stderr) from exc
    if check and proc.returncode: raise AssertionError(data)
    return proc.returncode, data


class ProjectLifecycleTests(unittest.TestCase):
    def write_policy(self, root: Path, value: dict) -> None:
        (root / ".buildos-policy.json").write_text(json.dumps(value, indent=2), encoding="utf-8")

    def test_greenfield_small_profile_creates_only_core_and_validates_gate(self):
        with fixture("greenfield") as root:
            self.write_policy(root, policy())
            result = invoke(root, "bootstrap", "--mode", "greenfield", "--verify-gates")[1]
            self.assertEqual(result["profile"], "small-tool")
            self.assertTrue((root / "README.md").is_file())
            for item in ("PROJECT_STATUS.md", "ARCHITECTURE.md", "ENGINEERING.md", "ROADMAP.md", "CHANGELOG.md"):
                self.assertTrue((root / item).is_file())
            for forbidden in ("OPERATIONS.md", "SECURITY.md", "MIGRATIONS.md", "PROJECT_BRIEF.md", "PROJECT_CLOSURE.md"):
                self.assertFalse((root / forbidden).exists())
            self.assertEqual(result["quality_gates"][0]["exit_code"], 0)
            self.assertEqual(invoke(root, "check")[1]["status"], "PASS")

    def test_trusted_argv_gate_avoids_shell_and_preserves_provenance(self):
        with fixture("trusted-gate") as root:
            self.write_policy(root, trusted_policy())
            gate = invoke(root, "bootstrap", "--mode", "greenfield", "--verify-gates")[1]["quality_gates"][0]
            self.assertEqual(gate["execution"], "ARGV_NO_SHELL")
            self.assertEqual(gate["provenance"], "OWNER_AUTHORED")
            self.assertEqual(gate["argv"][0], sys.executable)

    def test_existing_adoption_preserves_docs_and_marks_unknown(self):
        with fixture("existing") as root:
            (root / "README.md").write_text("# Existing reality\n", encoding="utf-8")
            self.write_policy(root, policy())
            invoke(root, "bootstrap", "--mode", "existing")
            self.assertEqual((root / "README.md").read_text(encoding="utf-8"), "# Existing reality\n")
            self.assertIn("UNKNOWN", (root / "PROJECT_STATUS.md").read_text(encoding="utf-8"))
            self.assertIn("UNKNOWN", (root / "ROADMAP.md").read_text(encoding="utf-8"))

    def test_custom_paths_and_enabled_production_modules(self):
        with fixture("custom") as root:
            self.write_policy(root, policy(profile="production-app", custom_paths=True, modules={"operations": True, "adr": True, "security": True, "migrations": True, "project_brief": True, "project_closure": True}))
            invoke(root, "bootstrap", "--mode", "greenfield")
            for item in ("guide/START.md", "guide/STATUS.md", "guide/ARCH.md", "guide/ENGINEERING.md", "guide/PLAN.md", "guide/HISTORY.md", "OPERATIONS.md", "SECURITY.md", "MIGRATIONS.md", "PROJECT_BRIEF.md", "docs/adr/README.md"):
                self.assertTrue((root / item).is_file(), item)
            self.assertFalse((root / "PROJECT_CLOSURE.md").exists())

    def test_mandatory_invariants_reject_common_weakening_attempts(self):
        cases = []
        no_gate = policy(); no_gate["project_lifecycle"]["quality_gates"] = []; cases.append((no_gate, "quality gate"))
        no_ref = policy(); no_ref["documentation_handoff"]["accepted_ref"] = "missing-ref"; cases.append((no_ref, "accepted_ref"))
        no_continuity = policy(); no_continuity["documentation_handoff"]["continuity"]["mandatory_operational_skill"] = "disabled"; cases.append((no_continuity, "continuity"))
        no_study = policy(); no_study["documentation_handoff"]["continuity"]["field_study"] = "DISABLED"; cases.append((no_study, "Field Study"))
        no_map = policy(); del no_map["documentation_handoff"]["category_authorities"]["API_CONFIG_SCHEMA"]; cases.append((no_map, "category_authorities"))
        no_boundary = policy(); no_boundary["project_lifecycle"]["safety_boundaries"]["data"] = ""; cases.append((no_boundary, "safety_boundaries.data"))
        weak_admission = policy(); weak_admission["execution_admission"] = {"enabled": True, "require_authority_record": False}; cases.append((weak_admission, "cannot weaken"))
        for value, expected in cases:
            with self.subTest(expected=expected), fixture("reject") as root:
                self.write_policy(root, value)
                code, result = invoke(root, "check", check=False)
                self.assertEqual(code, 2); self.assertIn(expected, result["message"])

    def test_enabled_side_effect_contract_is_validated_by_policy_check(self):
        with fixture("side-effect") as root:
            value = policy()
            value["side_effect_contract"] = {"enabled": True, "path": "SIDE_EFFECT_CONTRACT.json"}
            template = (PACKAGE / "templates" / "project-lifecycle" / "SIDE_EFFECT_CONTRACT.json.tmpl").read_text(encoding="utf-8")
            (root / "SIDE_EFFECT_CONTRACT.json").write_text(template, encoding="utf-8")
            self.write_policy(root, value)
            checked = invoke(root, "check")[1]
            self.assertEqual(checked["side_effect_contract"]["status"], "PASS")

            contract = json.loads((root / "SIDE_EFFECT_CONTRACT.json").read_text(encoding="utf-8"))
            contract["dangerous_actions"][0]["unknown_is_barrier"] = False
            (root / "SIDE_EFFECT_CONTRACT.json").write_text(json.dumps(contract), encoding="utf-8")
            code, failed = invoke(root, "check", check=False)
            self.assertEqual(code, 2)
            self.assertIn("unknown a queue barrier", failed["message"])

    def test_reconciliation_distinguishes_closed_candidate_from_accepted_baseline(self):
        with fixture("reconcile") as root:
            self.write_policy(root, policy()); invoke(root, "bootstrap", "--mode", "greenfield")
            git(root, "add", "."); git(root, "commit", "-qm", "adoption"); git(root, "branch", "-f", "accepted", "HEAD")
            (root / "app.txt").write_text("candidate\n", encoding="utf-8"); git(root, "add", "app.txt"); git(root, "commit", "-qm", "candidate")
            candidate = git(root, "rev-parse", "HEAD")
            pending = invoke(root, "reconcile", "--candidate-sha", candidate)[1]
            self.assertEqual(pending["state"], "CLOSED_PENDING_BASELINE_ADVANCE")
            git(root, "branch", "-f", "accepted", "HEAD")
            accepted = invoke(root, "reconcile", "--candidate-sha", candidate)[1]
            self.assertEqual(accepted["state"], "ACCEPTED_BASELINE_RECONCILIATION_REQUIRED")
            self.assertFalse(accepted["semantic_prose_generated"])
            self.assertFalse(accepted["tracked_docs_self_sha_required"])
            self.assertFalse(accepted["sha_only_documentation_churn_required"])
            self.assertIn("CHANGELOG", " ".join(accepted["required_actions"]))

    def test_baseline_advancement_converges_without_sha_only_documentation_churn(self):
        with fixture("converges") as root:
            self.write_policy(root, policy()); invoke(root, "bootstrap", "--mode", "greenfield")
            git(root, "add", "."); git(root, "commit", "-qm", "adopt lifecycle"); git(root, "branch", "-f", "accepted", "HEAD")
            (root / "app.txt").write_text("candidate\n", encoding="utf-8"); git(root, "add", "app.txt"); git(root, "commit", "-qm", "candidate")
            candidate = git(root, "rev-parse", "HEAD"); old = git(root, "rev-parse", "accepted")
            advanced = invoke(root, "advance", "--expected-old-sha", old, "--target-sha", candidate)[1]
            self.assertEqual(advanced["new_sha"], candidate)
            first = invoke(root, "reconcile", "--candidate-sha", candidate)[1]
            self.assertFalse(first["tracked_docs_self_sha_required"])
            self.assertFalse(first["sha_only_documentation_churn_required"])
            (root / "PROJECT_STATUS.md").write_text((root / "PROJECT_STATUS.md").read_text(encoding="utf-8") + "\nSemantic capability accepted.\n", encoding="utf-8")
            git(root, "add", "PROJECT_STATUS.md"); git(root, "commit", "-qm", "semantic reconciliation")
            docs_commit = git(root, "rev-parse", "HEAD"); old = git(root, "rev-parse", "accepted")
            invoke(root, "advance", "--expected-old-sha", old, "--target-sha", docs_commit)
            second = invoke(root, "reconcile", "--candidate-sha", candidate)[1]
            self.assertFalse(second["tracked_docs_self_sha_required"])
            self.assertFalse(second["sha_only_documentation_churn_required"])

    def test_guarded_advance_rejects_stale_expected_old_sha(self):
        with fixture("guard") as root:
            self.write_policy(root, policy()); invoke(root, "bootstrap", "--mode", "greenfield")
            git(root, "add", "."); git(root, "commit", "-qm", "adopt lifecycle"); git(root, "branch", "-f", "accepted", "HEAD")
            old = git(root, "rev-parse", "accepted")
            (root / "app.txt").write_text("candidate\n", encoding="utf-8"); git(root, "add", "app.txt"); git(root, "commit", "-qm", "candidate")
            candidate = git(root, "rev-parse", "HEAD"); invoke(root, "advance", "--expected-old-sha", old, "--target-sha", candidate)
            code, result = invoke(root, "advance", "--expected-old-sha", old, "--target-sha", old, check=False)
            self.assertEqual(code, 2); self.assertIn("moved concurrently", result["message"])

    def test_project_closure_is_explicit_only(self):
        with fixture("closure") as root:
            self.write_policy(root, policy(modules={"project_closure": True})); invoke(root, "bootstrap", "--mode", "greenfield")
            self.assertFalse((root / "PROJECT_CLOSURE.md").exists())
            code, refused = invoke(root, "retire-project", check=False)
            self.assertEqual(code, 2); self.assertIn("explicit", refused["message"])
            result = invoke(root, "retire-project", "--confirm")[1]
            self.assertTrue((root / result["closure_record"]).is_file())

    def test_generic_greenfield_flow_reaches_closed_pending_then_reconciliation(self):
        with fixture("e2e") as root:
            self.write_policy(root, policy()); invoke(root, "bootstrap", "--mode", "greenfield")
            git(root, "add", "."); git(root, "commit", "-qm", "adopt lifecycle"); git(root, "branch", "-f", "accepted", "HEAD")
            check = f'"{sys.executable}" "{CONTINUITY}" --root "{root}" --task-id FLOW-1 docs-check'
            boot = subprocess.run([sys.executable, str(AI), "--root", str(root), "bootstrap", "--task-id", "FLOW-1", "--outcome", "flow works", "--allow", "app.txt", "--check", check], text=True, capture_output=True, timeout=90)
            self.assertEqual(boot.returncode, 0, boot.stdout + boot.stderr)
            sidecar = subprocess.run([sys.executable, str(CONTINUITY), "--root", str(root), "--task-id", "FLOW-1", "bootstrap", "--next-safe-action", "change fixture", "--documentation-impact", "NO", "--category", "IMPLEMENTATION_ONLY", "--documentation-rationale", "implementation only"], text=True, capture_output=True, timeout=60)
            self.assertEqual(sidecar.returncode, 0, sidecar.stdout + sidecar.stderr)
            (root / "app.txt").write_text("product change\n", encoding="utf-8"); git(root, "add", "app.txt"); git(root, "commit", "-qm", "product change")
            self.assertEqual(subprocess.run([sys.executable, str(AI), "--root", str(root), "record-commit"], text=True, capture_output=True, timeout=60).returncode, 0)
            validated = subprocess.run([sys.executable, str(AI), "--root", str(root), "validate", "--inspected-by", "fixture-worker"], text=True, capture_output=True, timeout=90)
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            self.assertEqual(subprocess.run([sys.executable, str(AI), "--root", str(root), "close"], text=True, capture_output=True, timeout=90).returncode, 0)
            candidate = git(root, "rev-parse", "HEAD")
            self.assertEqual(invoke(root, "reconcile", "--candidate-sha", candidate)[1]["state"], "CLOSED_PENDING_BASELINE_ADVANCE")
            git(root, "branch", "-f", "accepted", "HEAD")
            accepted = invoke(root, "reconcile", "--candidate-sha", candidate)[1]
            self.assertEqual(accepted["state"], "ACCEPTED_BASELINE_RECONCILIATION_REQUIRED")


class ProjectLifecyclePackageTests(unittest.TestCase):
    def test_package_contains_lifecycle_assets_and_kernel_is_unchanged(self):
        manifest = json.loads((PACKAGE / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["project_lifecycle_kit"]["version"], "1.2.0")
        self.assertEqual(manifest["continuity_skill"]["version"], "1.1.0")
        self.assertTrue((PACKAGE / "templates" / "project-lifecycle" / "PROJECT_STATUS.md.tmpl").is_file())
        self.assertTrue((PACKAGE / "docs" / "PROJECT_LIFECYCLE_KIT.md").is_file())
        expected = {
            line.split("  ", 1)[1]: line.split("  ", 1)[0]
            for line in (PACKAGE / "FROZEN_KERNEL.sha256").read_text(encoding="ascii").splitlines() if line
        }
        observed = {
            item.relative_to(PACKAGE).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest()
            for item in (PACKAGE / "buildos").rglob("*") if item.is_file() and "__pycache__" not in item.parts
        }
        self.assertEqual(observed, expected)

    def test_worker_efficiency_guidance_is_bounded_and_uses_real_trace_labels(self):
        guide = (PACKAGE / "docs" / "PROJECT_LIFECYCLE_KIT.md").read_text(encoding="utf-8")
        bootstrap = (PACKAGE / "skills" / "project-lifecycle-bootstrap" / "SKILL.md").read_text(encoding="utf-8")
        continuity = (PACKAGE / "skills" / "documentation-handoff-continuity" / "SKILL.md").read_text(encoding="utf-8")
        required = (
            "Keep the active model working set bounded", "Persist detailed command output",
            "bounded summary plus a pointer", "Closeout is bounded", "same chat",
            "Field Study eligibility check", "UNKNOWN", "HIGH_CONTEXT/CLOSEOUT_OVERHEAD",
            "HEALTHY BOUNDED EXECUTION",
        )
        for item in required:
            self.assertIn(item, guide)
        self.assertIn("Read ROADMAP, CHANGELOG, OPERATIONS", bootstrap)
        self.assertIn("not reconstruct all history at closeout", continuity)
        self.assertNotIn("request-count trigger", guide.lower())
        self.assertNotIn("mandatory new skill", guide.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
