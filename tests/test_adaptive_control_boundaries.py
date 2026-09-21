from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AdaptiveControlBoundaryContractTests(unittest.TestCase):
    def test_decision_is_active_and_does_not_add_a_sixth_control(self):
        index = (ROOT / "docs/decisions/README.md").read_text(encoding="utf-8")
        record = (ROOT / "docs/decisions/0011-adaptive-control-boundaries.md").read_text(encoding="utf-8")
        architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")

        self.assertIn("DR-0011", index)
        for term in (
            "Intent Boundary",
            "Risk Envelope",
            "Execution Authority",
            "Versioned Acceptance",
            "Canonical Promotion",
        ):
            self.assertIn(term, record)
        self.assertIn("Existing Five Controls remain", record)
        self.assertIn("five controls", architecture.lower())

    def test_framing_carries_adaptive_intent_and_risk_semantics(self):
        framing = (ROOT / "skills/core/product-goal-framing.md").read_text(encoding="utf-8")
        for term in (
            "Intent Boundary",
            "Risk Envelope",
            "reversibility",
            "observability",
            "blast radius",
        ):
            self.assertIn(term, framing)
        self.assertIn("pass-through", framing)

    def test_acceptance_binds_oracle_candidate_and_system_fitness(self):
        acceptance = (ROOT / "skills/core/product-acceptance.md").read_text(encoding="utf-8")
        for term in (
            "Versioned acceptance",
            "oracle identity",
            "System-fitness trigger",
            "canonical promotion",
            "continuity commitment",
        ):
            self.assertIn(term, acceptance)

    def test_templates_expose_only_optional_material_context(self):
        task = (ROOT / "templates/project/TASK.md").read_text(encoding="utf-8")
        architecture = (ROOT / "templates/project/ARCHITECTURE.md").read_text(encoding="utf-8")
        self.assertIn("Acceptance Baseline / Oracle Identity", task)
        self.assertIn("Deferred Assurance Triggers", task)
        self.assertIn("system-fitness", architecture.lower())


if __name__ == "__main__":
    unittest.main()
