from __future__ import annotations

import hashlib
import unittest

from acceptance_contract import (
    CAPSULE_ACCEPTANCE_ITEM_LIMIT,
    CAPSULE_HARD_MAX_BYTES,
    CAPSULE_NORMAL_BYTES,
    CANONICAL_ACCEPTANCE_LIMIT,
    CONTRACT_ID,
    TARGETED_READ_REQUIRED,
    project_acceptance,
    validate_bootstrap_acceptance,
)


class AcceptanceContractTests(unittest.TestCase):
    def test_contract_has_one_unbounded_canonical_authority_and_preserves_shape(self):
        self.assertEqual(CONTRACT_ID, "ACCEPTANCE_CAPSULE_CONTRACT_CONSISTENT")
        self.assertIsNone(CANONICAL_ACCEPTANCE_LIMIT)
        self.assertEqual(validate_bootstrap_acceptance(["ok"]), ["ok"])
        with self.assertRaises(ValueError):
            validate_bootstrap_acceptance([])

    def test_exact_boundary_passes_and_boundary_plus_one_is_targeted(self):
        exact = "x" * CAPSULE_ACCEPTANCE_ITEM_LIMIT
        projected, targeted = project_acceptance([exact])
        self.assertEqual(projected, [exact]); self.assertEqual(targeted, [])
        longer = exact + "x"
        projected, targeted = project_acceptance([longer])
        self.assertEqual(len(projected[0]), len("TARGETED_READ_REQUIRED acceptance[0] sha256=") + 64)
        self.assertIn(TARGETED_READ_REQUIRED, projected[0])
        self.assertEqual(targeted[0], projected[0] + " source=.buildos/control/CURRENT")
        self.assertIn(hashlib.sha256(longer.encode()).hexdigest(), projected[0])
        self.assertNotIn(longer, projected[0])

    def test_long_projection_is_deterministic_and_capsule_bounds_are_unchanged(self):
        item = "safety blocker " + "z" * 5000
        self.assertEqual(project_acceptance([item]), project_acceptance([item]))
        self.assertEqual(CAPSULE_NORMAL_BYTES, 4096)
        self.assertEqual(CAPSULE_HARD_MAX_BYTES, 8192)


if __name__ == "__main__":
    unittest.main()
