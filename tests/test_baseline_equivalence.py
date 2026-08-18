from __future__ import annotations

from pathlib import Path
import sys
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "scripts"))
from baseline_equivalence import DispositionError, compare_results, environment_policy, failure_from_summary, parse_collection, parse_failures


def suite(*failures: tuple[str, str], collection: tuple[str, ...] = ("tests/test_a.py::test_a",)) -> dict:
    return {
        "returncode": 1 if failures else 0,
        "failures": [failure_from_summary(nodeid, summary).as_json() for nodeid, summary in failures],
        "collection": {"nodes": list(collection)},
    }


class BaselineEquivalentFailureTests(unittest.TestCase):
    def test_exact_baseline_equivalent_failures_are_authorized(self):
        baseline = suite(("tests/test_a.py::test_a", "AssertionError: expected one"))
        candidate = suite(("tests/test_a.py::test_a", "AssertionError: expected one"))
        result = compare_results(baseline, candidate)
        self.assertEqual(result["candidate_failure_count"], 1)
        self.assertEqual(len(result["equivalence_mapping"]), 1)

    def test_fewer_equivalent_candidate_failures_are_authorized(self):
        baseline = suite(("tests/test_a.py::test_a", "AssertionError: expected one"), ("tests/test_b.py::test_b", "ValueError: old"), collection=("tests/test_a.py::test_a", "tests/test_b.py::test_b"))
        candidate = suite(("tests/test_a.py::test_a", "AssertionError: expected one"), collection=("tests/test_a.py::test_a", "tests/test_b.py::test_b"))
        self.assertEqual(compare_results(baseline, candidate)["baseline_failure_count"], 2)

    def test_new_failure_fails_closed(self):
        baseline = suite(("tests/test_a.py::test_a", "AssertionError: expected one"), collection=("tests/test_a.py::test_a", "tests/test_b.py::test_b"))
        candidate = suite(("tests/test_b.py::test_b", "RuntimeError: new"), collection=("tests/test_a.py::test_a", "tests/test_b.py::test_b"))
        with self.assertRaisesRegex(DispositionError, "new or materially changed"):
            compare_results(baseline, candidate)

    def test_same_nodeid_materially_different_failure_fails_closed(self):
        baseline = suite(("tests/test_a.py::test_a", "AssertionError: expected one"))
        candidate = suite(("tests/test_a.py::test_a", "AssertionError: expected two"))
        with self.assertRaisesRegex(DispositionError, "new or materially changed"):
            compare_results(baseline, candidate)

    def test_missing_baseline_nodeid_fails_closed(self):
        baseline = suite(("tests/test_a.py::test_a", "AssertionError: expected one"), collection=("tests/test_a.py::test_a", "tests/test_guard.py::test_guard"))
        candidate = suite(("tests/test_a.py::test_a", "AssertionError: expected one"))
        with self.assertRaisesRegex(DispositionError, "omits accepted-baseline"):
            compare_results(baseline, candidate)

    def test_green_candidate_must_use_normal_validation(self):
        baseline = suite(("tests/test_a.py::test_a", "AssertionError: expected one"))
        with self.assertRaisesRegex(DispositionError, "suite is green"):
            compare_results(baseline, suite())

    def test_failure_parser_retains_nodeid_and_normalized_signature(self):
        output = "=== short test summary info ===\nFAILED tests/test_a.py::test_a - AssertionError: C:\\Temp\\pytest-of-me\\a 1.2s\n==== 1 failed ===="
        parsed = parse_failures(output)
        self.assertEqual(parsed[0].nodeid, "tests/test_a.py::test_a")
        self.assertIn("<TEMP_PATH>", parsed[0].summary)

    def test_failure_parser_binds_detail_by_section_identity_not_summary_order(self):
        output = "FAILURES\n_ Thing.test_a _\n_ _ _ _ _ _ _ _ _\nE       ValueError: one\n_ Other.test_b _\n_ _ _ _ _ _ _ _ _\nE       AssertionError: two\n=== short test summary info ===\nFAILED tests/test_b.py::Other::test_b\nFAILED tests/test_a.py::Thing::test_a\n=== 2 failed ==="
        parsed = parse_failures(output)
        self.assertEqual([item.nodeid for item in parsed], ["tests/test_b.py::Other::test_b", "tests/test_a.py::Thing::test_a"])
        self.assertEqual([item.failure_class for item in parsed], ["AssertionError", "ValueError"])

    def test_baseline_only_failure_section_cannot_shift_shared_failures(self):
        baseline_output = "FAILURES\n_ Thing.test_a _\nE       ValueError: shared one\n_ SceneEffectsTests.test_all_presets_validate _\nE       AssertionError: baseline only\n_ Other.test_b _\nE       RuntimeError: shared two\n=== short test summary info ===\nFAILED tests/test_a.py::Thing::test_a\nFAILED tests/test_scene_effects.py::SceneEffectsTests::test_all_presets_validate\nFAILED tests/test_b.py::Other::test_b\n=== 3 failed ==="
        candidate_output = "FAILURES\n_ Thing.test_a _\nE       ValueError: shared one\n_ Other.test_b _\nE       RuntimeError: shared two\n=== short test summary info ===\nFAILED tests/test_a.py::Thing::test_a\nFAILED tests/test_b.py::Other::test_b\n=== 2 failed ==="
        baseline = {item.nodeid: item for item in parse_failures(baseline_output)}
        candidate = {item.nodeid: item for item in parse_failures(candidate_output)}
        self.assertEqual(candidate["tests/test_a.py::Thing::test_a"].fingerprint, baseline["tests/test_a.py::Thing::test_a"].fingerprint)
        self.assertEqual(candidate["tests/test_b.py::Other::test_b"].fingerprint, baseline["tests/test_b.py::Other::test_b"].fingerprint)

    def test_unpaired_failure_detail_fails_closed(self):
        output = "=== short test summary info ===\nFAILED tests/test_a.py::test_a\n=== 1 failed ==="
        self.assertEqual(parse_failures(output), [])

    def test_ambiguous_failure_sections_fail_closed(self):
        output = "FAILURES\n_ Thing.test_a _\nE       ValueError: one\n_ Thing.test_a _\nE       ValueError: one\n=== short test summary info ===\nFAILED tests/test_a.py::Thing::test_a\n=== 1 failed ==="
        self.assertEqual(parse_failures(output), [])

    def test_collection_parser_uses_node_identity_only(self):
        output = "tests/test_a.py::test_a\ntests/test_b.py::Thing::test_b\n\n2 tests collected in 0.01s\n"
        self.assertEqual(parse_collection(output), ["tests/test_a.py::test_a", "tests/test_b.py::Thing::test_b"])

    def test_suppression_environment_fails_closed(self):
        with self.assertRaisesRegex(DispositionError, "may not add options"):
            environment_policy({"PYTEST_ADDOPTS": "--ignore=tests"})

    def test_zero_timeout_is_rejected_before_execution(self):
        # The public execution function checks timeout before it creates any checkout.
        from baseline_equivalence import execute_comparison
        with self.assertRaisesRegex(DispositionError, "positive finite"):
            execute_comparison(Path.cwd(), baseline_sha="a", candidate_sha="b", command="python -m pytest -q", timeout=0, policy_sha256="x")


if __name__ == "__main__":
    unittest.main(verbosity=2)
