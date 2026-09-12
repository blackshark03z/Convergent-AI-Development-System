from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ExternalSkillAcquisitionTests(unittest.TestCase):
    def test_method_is_narrow_non_authoritative_and_docs_only(self):
        text = (ROOT / "skills/core/external-skill-acquisition.md").read_text(encoding="utf-8")
        self.assertIn("Ordinary targeted repository/runtime/web research remains the default", text)
        self.assertIn("untrusted advisory engineering inputs", text)
        self.assertIn("Stack/technology detection is a weak discovery signal", text)
        self.assertIn("docs-only", text)
        self.assertIn("do not persistently activate", text)
        self.assertIn("Do not background-update", text)
        self.assertIn("does not become a CADS-wide recommended skill", text)
        self.assertIn(
            "creates no capability subsystem, lifecycle phase, registry, package manager, trust score",
            text,
        )

    def test_lock_schema_is_provenance_not_execution_state(self):
        schema = json.loads((ROOT / "skills/external-skills-lock.schema.json").read_text(encoding="utf-8"))
        item = schema["properties"]["skills"]["items"]
        required = set(item["required"])
        for field in (
            "id", "source", "source_revision", "source_path", "bundle_sha256",
            "license", "content_class", "selected_for", "reviewed_at", "review_method",
        ):
            self.assertIn(field, required)
        self.assertEqual(item["properties"]["content_class"]["const"], "docs-only")
        rendered = json.dumps(schema, sort_keys=True).lower()
        for forbidden in ("trust_score", "task_state", "lifecycle_state", "update_status"):
            self.assertNotIn(forbidden, rendered)

    def test_manifest_covers_all_canonical_internal_skills(self):
        manifest = json.loads((ROOT / "skills/agent-skills.json").read_text(encoding="utf-8"))
        mapped = {entry["source"] for entry in manifest["skills"]}
        actual = {
            path.relative_to(ROOT).as_posix()
            for directory in (ROOT / "skills/core", ROOT / "skills/product")
            for path in directory.glob("*.md")
        }
        self.assertEqual(mapped, actual)
        names = [entry["name"] for entry in manifest["skills"]]
        self.assertEqual(len(names), len(set(names)))
        for entry in manifest["skills"]:
            self.assertTrue(entry["description"].startswith("Use "))

    def test_agent_skills_projection_is_deterministic_and_checkable(self):
        script = ROOT / "scripts/project_agent_skills.py"
        manifest = json.loads((ROOT / "skills/agent-skills.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "projected"
            first = subprocess.run(
                [sys.executable, str(script), "--output-dir", str(output)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr or first.stdout)
            first_hashes = {
                entry["name"]: hashlib.sha256((output / entry["name"] / "SKILL.md").read_bytes()).hexdigest()
                for entry in manifest["skills"]
            }
            second = subprocess.run(
                [sys.executable, str(script), "--output-dir", str(output)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
            second_hashes = {
                entry["name"]: hashlib.sha256((output / entry["name"] / "SKILL.md").read_bytes()).hexdigest()
                for entry in manifest["skills"]
            }
            self.assertEqual(first_hashes, second_hashes)

            for entry in manifest["skills"]:
                projected = (output / entry["name"] / "SKILL.md").read_bytes()
                canonical = (ROOT / entry["source"]).read_bytes()
                self.assertTrue(projected.endswith(canonical))
                head = projected[: -len(canonical)].decode("utf-8")
                self.assertIn(f"name: {entry['name']}", head)
                self.assertIn("description:", head)

            check = subprocess.run(
                [sys.executable, str(script), "--output-dir", str(output), "--check"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(check.returncode, 0, check.stderr or check.stdout)
            payload = json.loads(check.stdout)
            self.assertEqual(payload["result"], "PASS")

            victim = output / manifest["skills"][0]["name"] / "SKILL.md"
            victim.write_text("drift", encoding="utf-8")
            mismatch = subprocess.run(
                [sys.executable, str(script), "--output-dir", str(output), "--check"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(mismatch.returncode, 1)
            self.assertEqual(json.loads(mismatch.stdout)["result"], "MISMATCH")

    def test_routing_is_discoverable_without_bloating_activation_contract(self):
        root_agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        project_agents = (ROOT / "templates/project/AGENTS.md").read_text(encoding="utf-8")
        framing = (ROOT / "skills/core/product-goal-framing.md").read_text(encoding="utf-8")
        self.assertIn("external-skill-acquisition.md", root_agents)
        self.assertIn("external-skill-acquisition.md", framing)
        self.assertIn("external specialist instructions", project_agents)
        self.assertLess(len(root_agents), 4_000)

    def test_standard_is_not_extended_with_external_skill_runtime(self):
        standard = (ROOT / "docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md").read_text(encoding="utf-8").lower()
        self.assertNotIn("external specialist skill acquisition", standard)
        self.assertNotIn("skill registry", standard)


if __name__ == "__main__":
    unittest.main()
