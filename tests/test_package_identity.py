from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
GUARD = PACKAGE / "scripts" / "package_identity.py"


def invoke(root: Path) -> tuple[int, dict]:
    result = subprocess.run([sys.executable, str(GUARD), "--root", str(root)], text=True, capture_output=True, timeout=45)
    return result.returncode, json.loads(result.stdout)


class PackageIdentityTests(unittest.TestCase):
    def test_active_package_identity_is_consistent(self):
        code, payload = invoke(PACKAGE)
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["invariant"], "PACKAGE_IDENTITY_CONSISTENT")

    def test_deliberate_manifest_executable_version_mismatch_fails(self):
        with tempfile.TemporaryDirectory(prefix="package-identity-") as raw:
            root = Path(raw) / "package"
            for name in ("PACKAGE_MANIFEST.json", "skills"):
                source = PACKAGE / name
                if source.is_dir(): shutil.copytree(source, root / name)
                else:
                    root.mkdir(parents=True, exist_ok=True); shutil.copy2(source, root / name)
            manifest_path = root / "PACKAGE_MANIFEST.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["project_lifecycle_kit"]["version"] = "1.0.3"
            manifest["project_lifecycle_kit"]["bootstrap_skill"]["version"] = "1.0.3"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            code, payload = invoke(root)
            self.assertEqual(code, 2)
            self.assertIn("LIFECYCLE_EXECUTABLE_IDENTITY_MISMATCH", payload["errors"])
            self.assertIn("AUTHORITY_LIFECYCLE_IDENTITY_MISMATCH", payload["errors"])

    def test_runtime_context_epoch_capability_identity_is_checked(self):
        with tempfile.TemporaryDirectory(prefix="package-runtime-identity-") as raw:
            root = Path(raw) / "package"
            for name in ("PACKAGE_MANIFEST.json", "skills"):
                source = PACKAGE / name
                if source.is_dir(): shutil.copytree(source, root / name)
                else:
                    root.mkdir(parents=True, exist_ok=True); shutil.copy2(source, root / name)
            manifest_path = root / "PACKAGE_MANIFEST.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["runtime_context_epoch_capability"]["identity"] = "wrong-runtime.v1"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            code, payload = invoke(root)
            self.assertEqual(code, 2)
            self.assertIn("RUNTIME_CONTEXT_EPOCH_EXECUTABLE_IDENTITY_MISMATCH", payload["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
