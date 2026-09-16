from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ArchitectureDescriptionProfileTests(unittest.TestCase):
    def test_project_template_exposes_lean_architecture_profile(self):
        text = (ROOT / "templates/project/ARCHITECTURE.md").read_text(encoding="utf-8")
        headings = (
            "# System Purpose & Scope",
            "# Stakeholders / Architecture Concerns",
            "# Architecture Drivers",
            "# Solution Strategy / Technology Stack",
            "# System Context",
            "# Components / Building Blocks / Ownership",
            "# Data / Control Flow",
            "# Authority / State Boundaries",
            "# Deployment / Runtime Topology",
            "# External Boundaries / Trust Boundaries",
            "# Stable Invariants / Architecture Invariants",
            "# Important Tradeoffs / Decisions",
            "# Known Risks / Technical Debt / Revisit Triggers",
        )
        for heading in headings:
            self.assertIn(heading, text)
        self.assertIn("CADS does not prescribe one universal stack", text)
        self.assertIn("no diagram notation or complete view set is mandatory", text)
        self.assertIn("actual current Git/runtime reality", text)

    def test_architecture_method_is_conditional_and_scenario_based(self):
        text = (ROOT / "skills/core/architecture-description.md").read_text(encoding="utf-8")
        self.assertIn("conditional CADS method", text)
        self.assertIn("CADS does not prescribe React", text)
        self.assertIn("driver -> architecture decision -> expected property/scenario -> evidence/risk/trade-off", text)
        self.assertIn("No complete set is mandatory", text)
        self.assertIn("not persisted process state", text)

    def test_routing_and_framing_make_architecture_profile_discoverable(self):
        root_agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        project_agents = (ROOT / "templates/project/AGENTS.md").read_text(encoding="utf-8")
        framing = (ROOT / "skills/core/product-goal-framing.md").read_text(encoding="utf-8")
        for text in (root_agents, project_agents, framing):
            self.assertIn("architecture-description.md", text)
        self.assertIn("architecture drivers", framing)
        self.assertIn("### Architecture / structure", framing)
        self.assertIn("scenario/evidence reasoning", framing)

    def test_material_research_is_trajectory_aware_without_new_ceremony(self):
        framing = (ROOT / "skills/core/product-goal-framing.md").read_text(encoding="utf-8")
        architecture = (ROOT / "skills/core/architecture-description.md").read_text(encoding="utf-8")
        continuity = (ROOT / "docs/DECISION_CONTINUITY.md").read_text(encoding="utf-8")
        self.assertIn("Research durability for material knowledge gaps", framing)
        self.assertIn("industry and technology trajectory", framing)
        self.assertIn("replacement/portability cost", framing)
        self.assertIn("cheap, local", framing)
        self.assertIn("credible industry/technology trajectory", architecture)
        self.assertIn("unnecessary model/provider/framework lock-in", architecture)
        self.assertIn("Research durability in material decisions", continuity)
        self.assertIn("Do not record forecasts as facts", continuity)

    def test_core_standard_remains_five_control_compatible(self):
        task = (ROOT / "TASK.md").read_text(encoding="utf-8")
        self.assertIn("Reality -> Intent / Design -> Change -> Acceptance -> Consequence", task)
        self.assertIn("No sixth CADS control", task)


if __name__ == "__main__":
    unittest.main()
