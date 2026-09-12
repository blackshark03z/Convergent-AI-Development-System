from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseQualificationTests(unittest.TestCase):
    def test_release_method_is_conditional_and_distinguishes_claims(self):
        text = (ROOT / "skills/core/release-qualification.md").read_text(encoding="utf-8")
        self.assertIn("material release boundary", text)
        self.assertIn("Product Acceptance", text)
        self.assertIn("Release Qualification", text)
        self.assertIn("Runtime Activation", text)
        self.assertIn("None implies the next", text)
        self.assertIn("creates no release lifecycle", text)
        self.assertIn("NOT_APPLICABLE", text)

    def test_evidence_continuity_is_criterion_scoped_and_fail_closed(self):
        text = (ROOT / "skills/core/release-qualification.md").read_text(encoding="utf-8")
        self.assertIn("criterion-by-criterion", text)
        self.assertIn("Unknown or unresolved impact is not preservation", text)
        self.assertIn("Do not infer neutrality from filenames or labels", text)
        self.assertIn("changed harness cannot independently self-prove", text)
        self.assertIn("Do not invalidate unrelated criteria merely because the commit SHA changed", text)

    def test_qualification_composes_existing_methods_and_avoids_fixed_pipeline(self):
        text = (ROOT / "skills/core/release-qualification.md").read_text(encoding="utf-8")
        self.assertIn("product-acceptance.md", text)
        self.assertIn("goal-execution.md", text)
        self.assertIn("systematic-debugging.md", text)
        self.assertIn("cheapest check", text)
        self.assertIn("not a mandatory fixed order", text)
        self.assertIn("stop treating each leaf failure as an independent patch target", text)

    def test_product_acceptance_no_longer_equates_product_with_release_ready(self):
        text = (ROOT / "skills/core/product-acceptance.md").read_text(encoding="utf-8")
        self.assertIn("does not by itself establish", text)
        self.assertIn("release-qualification.md", text)
        self.assertIn("changed SHA alone does not invalidate", text)

    def test_routing_and_agent_skill_projection_include_release_qualification(self):
        root_agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        project_agents = (ROOT / "templates/project/AGENTS.md").read_text(encoding="utf-8")
        manifest = json.loads((ROOT / "skills/agent-skills.json").read_text(encoding="utf-8"))
        self.assertIn("release-qualification.md", root_agents)
        self.assertIn("skills/core/release-qualification.md", project_agents)
        entry = next(x for x in manifest["skills"] if x["source"] == "skills/core/release-qualification.md")
        self.assertEqual(entry["name"], "cads-release-qualification")
        self.assertLess(len(root_agents), 4_000)

    def test_eval_and_decision_record_cover_real_failure_class_without_new_runtime(self):
        data = json.loads((ROOT / "evals/autonomy/cases.json").read_text(encoding="utf-8"))
        case = next(x for x in data["cases"] if x["id"] == "AE-021")
        self.assertEqual(case["failure_class"], "release-evidence-continuity")
        joined = " ".join(case["failure_signals"] + case["anti_shortcuts"])
        self.assertIn("old HEAD", joined)
        self.assertIn("Product Acceptance", joined)
        dr = (ROOT / "docs/decisions/0008-release-qualification-evidence-continuity.md").read_text(encoding="utf-8")
        self.assertIn("no release database", dr)
        self.assertIn("frozen Standard unchanged", dr)

    def test_frozen_standard_is_not_extended_with_release_state_machine(self):
        standard = (ROOT / "docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md").read_text(encoding="utf-8").lower()
        self.assertNotIn("release_qualified", standard)
        self.assertNotIn("release qualification", standard)


if __name__ == "__main__":
    unittest.main()
