from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


PACKAGE = Path(__file__).resolve().parents[1]
SCRIPTS = PACKAGE / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_simplified_candidate import CandidateError, build, secret_findings
from verify_simplified_candidate import verify
from tests.test_thin_guard import run_git


def copy_source(target: Path) -> None:
    shutil.copytree(
        PACKAGE,
        target,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
    )
    run_git(target, "init", "-q")
    run_git(target, "config", "user.name", "Candidate Test")
    run_git(target, "config", "user.email", "candidate@example.invalid")
    run_git(target, "add", ".")
    run_git(target, "commit", "-qm", "candidate source")


class SimplifiedCandidateTests(unittest.TestCase):
    def test_build_and_readback_match_exact_git_blobs_and_exclude_legacy(self):
        with tempfile.TemporaryDirectory(prefix="buildos-candidate-") as raw:
            container = Path(raw)
            source = container / "source"
            output = container / "output"
            copy_source(source)

            built = build(source, output)
            verified = verify(Path(built["archive_path"]), source)

            self.assertEqual(verified["result"], "PASS")
            self.assertEqual(verified["archive_sha256"], built["archive_sha256"])
            self.assertEqual(verified["source_head"], built["source_head"])
            with zipfile.ZipFile(built["archive_path"], "r") as archive:
                names = archive.namelist()
            self.assertFalse(any(name.startswith("legacy/") for name in names))
            self.assertIn("ARCHITECTURE.md", names)
            self.assertIn("tests/test_effect_safety.py", names)
            for name in (
                "scripts/bootstrap_project.py",
                "docs/CONVERGENT_AI_DEVELOPMENT_STANDARD.md",
                "skills/core/project-cold-start.md",
                "skills/core/product-goal-framing.md",
                "skills/core/goal-execution.md",
                "skills/core/systematic-debugging.md",
                "skills/core/product-acceptance.md",
                "skills/core/workspace-hygiene.md",
                "skills/product/user-facing-workflow.md",
                "skills/product/frontend-design.md",
                "skills/product/ui-quality-review.md",
                "templates/project/AGENTS.md",
                "templates/project/TASK.md",
                "templates/project/ARCHITECTURE.md",
            ):
                self.assertIn(name, names)

    def test_archive_is_deterministic_for_same_exact_source(self):
        with tempfile.TemporaryDirectory(prefix="buildos-candidate-") as raw:
            container = Path(raw)
            source = container / "source"
            copy_source(source)

            first = build(source, container / "first")
            second = build(source, container / "second")

            self.assertEqual(first["archive_sha256"], second["archive_sha256"])
            self.assertEqual(
                hashlib.sha256(Path(first["archive_path"]).read_bytes()).hexdigest(),
                first["archive_sha256"],
            )

    def test_secret_scan_rejects_common_private_key_and_token_shapes(self):
        findings = secret_findings({
            "private.pem": b"-----BEGIN " + b"PRIVATE KEY-----\nnot-real\n",
            "config.py": b"api_" + b"key = 'this-is-a-long-fake-key'\n",
        })
        self.assertEqual(findings, ["config.py:pattern-4", "private.pem:pattern-1"])

    def test_extracted_candidate_has_distinct_green_portable_self_test(self):
        with tempfile.TemporaryDirectory(prefix="buildos-portable-candidate-") as raw:
            container = Path(raw)
            source = container / "source"
            output = container / "output"
            extracted = container / "extracted"
            copy_source(source)
            built = build(source, output)
            with zipfile.ZipFile(built["archive_path"], "r") as archive:
                archive.extractall(extracted)

            source_only = subprocess.run(
                [sys.executable, "scripts/self_test.py"],
                cwd=extracted, text=True, capture_output=True, timeout=30,
            )
            portable = subprocess.run(
                [sys.executable, "scripts/portable_self_test.py"],
                cwd=extracted, text=True, capture_output=True, timeout=30,
            )

            self.assertEqual(source_only.returncode, 2)
            self.assertIn("SOURCE_CHECKOUT_REQUIRED", source_only.stdout)
            self.assertEqual(portable.returncode, 0, portable.stdout + portable.stderr)
            self.assertIn("SIMPLIFIED_PORTABLE_SUITE=PASS", portable.stdout)

    def test_tracked_embedded_manifest_fails_closed_instead_of_repackaging(self):
        with tempfile.TemporaryDirectory(prefix="buildos-manifest-source-") as raw:
            container = Path(raw)
            source = container / "source"
            copy_source(source)
            (source / "CANDIDATE_MANIFEST.json").write_text("{}\n", encoding="utf-8")
            run_git(source, "add", "CANDIDATE_MANIFEST.json")
            run_git(source, "commit", "-qm", "embedded package manifest")

            with self.assertRaisesRegex(CandidateError, "embedded candidate manifest"):
                build(source, container / "output")


if __name__ == "__main__":
    unittest.main()
