from __future__ import annotations

from pathlib import Path
import sys
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
SCRIPTS = PACKAGE / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from verify_portable_candidate import verify_extracted


class PortableCandidateTests(unittest.TestCase):
    def test_embedded_manifest_matches_all_packaged_source_bytes(self):
        result = verify_extracted(PACKAGE)

        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["manifest_readback"], "PASS")
        self.assertEqual(result["secret_scan"], "PASS")
        self.assertEqual(len(result["source_head"]), 40)
        self.assertEqual(len(result["source_tree"]), 40)


if __name__ == "__main__":
    unittest.main()
