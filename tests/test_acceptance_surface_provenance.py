from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AcceptanceSurfaceProvenanceTests(unittest.TestCase):
    def test_product_acceptance_uses_existing_unverified_semantics(self):
        text = (ROOT / "skills/core/product-acceptance.md").read_text(encoding="utf-8")
        self.assertIn("## Acceptance Surface Provenance Invariant", text)
        self.assertIn("intended candidate", text)
        self.assertIn("remains `UNVERIFIED`", text)
        self.assertIn("materially ambiguous", text)
        self.assertIn("does not automatically prove a", text)
        self.assertIn("later integrated state H", text)
        self.assertIn("self-reported version string", text)
        self.assertNotIn("NOT_READY_FOR_PRODUCT_REVIEW", text)
        self.assertNotIn("BUILDING -> PROMOTING -> ACTIVE -> ACCEPTED", text)

    def test_architecture_guidance_is_conditional_not_deployment_schema(self):
        skill = (ROOT / "skills/core/architecture-description.md").read_text(encoding="utf-8")
        template = (ROOT / "templates/project/ARCHITECTURE.md").read_text(encoding="utf-8")
        for text in (skill, template):
            self.assertIn("provenance", text)
            self.assertIn("not a", text.lower())
        self.assertIn("not a mandatory deployment", skill)
        self.assertIn("not a required deployment schema", template)

    def test_ae003_covers_independent_review_falsifiers(self):
        data = json.loads((ROOT / "evals/autonomy/cases.json").read_text(encoding="utf-8"))
        case = next(case for case in data["cases"] if case["id"] == "AE-003")
        joined = " ".join(
            [case["title"], case["goal"], *case["required_evidence"], *case["failure_signals"], *case["anti_shortcuts"]]
        ).lower()
        for phrase in (
            "stale runtime/assets",
            "mixed old/new",
            "materially changed prior to review",
            "self-reported version",
            "materially different integrated state",
        ):
            self.assertIn(phrase, joined)
        self.assertEqual(case["expected_behavior"], "BLOCK_UNTIL_GROUNDED")

    def test_decision_record_preserves_anti_accretion(self):
        record = (ROOT / "docs/decisions/0006-acceptance-surface-provenance.md").read_text(encoding="utf-8")
        index = (ROOT / "docs/decisions/README.md").read_text(encoding="utf-8")
        self.assertIn("Acceptance Surface Provenance Invariant", record)
        self.assertIn("no deployment lifecycle", record)
        self.assertIn("frozen Standard unchanged", record)
        self.assertIn("DR-0006", index)


if __name__ == "__main__":
    unittest.main()
