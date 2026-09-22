from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DesignCompilationBoundaryTests(unittest.TestCase):
    def test_decision_is_active_and_keeps_spec_substrate_replaceable(self):
        index = (ROOT / "docs/decisions/README.md").read_text(encoding="utf-8")
        record = (
            ROOT / "docs/decisions/0012-design-compilation-and-replaceable-spec-substrate.md"
        ).read_text(encoding="utf-8")

        self.assertIn("DR-0012", index)
        for term in (
            "Design Compilation",
            "worker-ready Design Baseline",
            "DESIGN_GAP",
            "OpenSpec",
            "Spec Kit",
            "replaceable",
        ):
            self.assertIn(term, record)
        self.assertIn("not a sixth CADS control", record)
        self.assertIn("does not mandate MAR", record)

    def test_material_design_compiles_before_execution_but_trivial_work_can_bypass(self):
        framing = (ROOT / "skills/core/product-goal-framing.md").read_text(
            encoding="utf-8"
        )
        execution = (ROOT / "skills/core/goal-execution.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Design Compilation when material", framing)
        self.assertIn("worker-ready Design Baseline", framing)
        self.assertIn("skip this", framing)
        self.assertIn("artifact entirely", framing)
        self.assertIn("DESIGN_GAP", execution)
        self.assertIn("Do not escalate normal code choices", execution)
        self.assertIn("small coherent slices", execution)

    def test_optional_design_baseline_is_worker_ready_not_implementation_prescriptive(self):
        baseline = (ROOT / "templates/project/DESIGN_BASELINE.md").read_text(
            encoding="utf-8"
        )
        for heading in (
            "# Product Outcome / Non-goals",
            "# Material Journeys / Actions",
            "# Domain / State Semantics",
            "# Required System Behavior",
            "# Acceptance / Oracle Map",
            "# Design Gap Rule",
        ):
            self.assertIn(heading, baseline)
        self.assertIn("not a mandatory", baseline)
        self.assertIn("Do not prescribe classes", baseline)

    def test_bootstrap_does_not_make_design_baseline_universal_ceremony(self):
        bootstrap_test = (ROOT / "tests/test_bootstrap_project.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn('"DESIGN_BASELINE.md",\n)', bootstrap_test)

    def test_architecture_separates_design_semantics_from_execution_runtime_lifecycle(self):
        architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
        for term in (
            "Design Compilation",
            "DESIGN_GAP",
            "Execution substrate is separate",
            "Direct repository execution remains valid",
        ):
            self.assertIn(term, architecture)
        self.assertIn("not CADS development phases", architecture)


if __name__ == "__main__":
    unittest.main()
