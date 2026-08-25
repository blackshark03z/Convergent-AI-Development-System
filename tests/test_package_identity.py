from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

import scripts.build_portable_package as package_builder
from scripts.build_portable_package import (
    contains_secret_like, parse_frozen_kernel, strict_json_loads,
    validate_archive_names, verify_checksum_index,
)


PACKAGE = Path(__file__).resolve().parents[1]
GUARD = PACKAGE / "scripts" / "package_identity.py"


def invoke(root: Path) -> tuple[int, dict]:
    result = subprocess.run([sys.executable, str(GUARD), "--root", str(root)], text=True, capture_output=True, timeout=45)
    return result.returncode, json.loads(result.stdout)


class PackageIdentityTests(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args], cwd=root, text=True, encoding="utf-8", errors="replace",
            capture_output=True, timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        return completed.stdout.strip()

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

    def test_work_loop_schema_identity_is_checked(self):
        with tempfile.TemporaryDirectory(prefix="package-work-loop-identity-") as raw:
            root = Path(raw) / "package"
            for name in ("PACKAGE_MANIFEST.json", "skills"):
                source = PACKAGE / name
                if source.is_dir(): shutil.copytree(source, root / name)
                else:
                    root.mkdir(parents=True, exist_ok=True); shutil.copy2(source, root / name)
            manifest_path = root / "PACKAGE_MANIFEST.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["work_loop"]["grounding_schema"] = "wrong.grounding.v0"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            code, payload = invoke(root)
            self.assertEqual(code, 2)
            self.assertIn("MANIFEST_WORK_LOOP_IDENTITY_MISMATCH", payload["errors"])

    def test_library_version_is_bound_to_manifest_identity(self):
        with tempfile.TemporaryDirectory(prefix="package-library-identity-") as raw:
            root = Path(raw) / "package"
            for name in ("PACKAGE_MANIFEST.json", "skills", "buildos"):
                source = PACKAGE / name
                if source.is_dir(): shutil.copytree(source, root / name)
                else:
                    root.mkdir(parents=True, exist_ok=True); shutil.copy2(source, root / name)
            init = root / "buildos" / "__init__.py"
            init.write_text('__version__ = "1.24-candidate"\n', encoding="utf-8")
            code, payload = invoke(root)
            self.assertEqual(code, 2)
            self.assertIn("BUILDOS_LIBRARY_IDENTITY_MISMATCH", payload["errors"])

    def test_package_effect_adapter_contract_must_be_content_bound(self):
        with tempfile.TemporaryDirectory(prefix="package-adapter-identity-") as raw:
            root = Path(raw) / "package"
            for name in ("PACKAGE_MANIFEST.json", "skills"):
                source = PACKAGE / name
                if source.is_dir(): shutil.copytree(source, root / name)
                else:
                    root.mkdir(parents=True, exist_ok=True); shutil.copy2(source, root / name)
            manifest_path = root / "PACKAGE_MANIFEST.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["trusted_effect_adapter_contracts"] = {"missing-adapter.json": "0" * 64}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            code, payload = invoke(root)
            self.assertEqual(code, 2)
            self.assertIn(
                "MANIFEST_TRUSTED_EFFECT_ADAPTER_CONTRACT_INVALID:missing-adapter.json",
                payload["errors"],
            )

    def test_package_checksum_index_must_cover_every_member(self):
        with tempfile.TemporaryDirectory(prefix="package-checksums-") as raw:
            archive_path = Path(raw) / "missing-row.zip"
            payload = b"immutable package member"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("one.txt", payload)
                archive.writestr("two.txt", b"not indexed")
                archive.writestr(
                    "PACKAGE_CONTENTS.sha256",
                    f"{hashlib.sha256(payload).hexdigest()}  one.txt\n",
                )
            with zipfile.ZipFile(archive_path, "r") as archive:
                with self.assertRaisesRegex(RuntimeError, "does not exactly cover"):
                    verify_checksum_index(archive)

    def test_package_checksum_index_detects_member_tampering(self):
        with tempfile.TemporaryDirectory(prefix="package-checksums-") as raw:
            archive_path = Path(raw) / "tampered.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("one.txt", b"tampered")
                archive.writestr(
                    "PACKAGE_CONTENTS.sha256",
                    f"{hashlib.sha256(b'expected').hexdigest()}  one.txt\n",
                )
            with zipfile.ZipFile(archive_path, "r") as archive:
                with self.assertRaisesRegex(RuntimeError, "content checksum mismatch"):
                    verify_checksum_index(archive)

    def test_zip_member_aliases_and_case_collisions_fail_before_extraction(self):
        for names in (
            ["scripts/package_identity.py", "scripts/./package_identity.py"],
            ["Docs/Report.md", "docs/report.md"],
            ["C:a.txt"],
            ["docs/report."],
        ):
            with self.subTest(names=names):
                with self.assertRaisesRegex(RuntimeError, "noncanonical|colliding"):
                    validate_archive_names(names)

    def test_frozen_kernel_index_rejects_duplicate_paths(self):
        payload = (
            f"{'0' * 64}  buildos/kernel.py\n"
            f"{'1' * 64}  buildos/kernel.py\n"
        ).encode("ascii")
        with self.assertRaisesRegex(RuntimeError, "duplicate path"):
            parse_frozen_kernel(payload)

    def test_release_json_rejects_duplicate_keys_and_nonfinite_constants(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON object key"):
            strict_json_loads('{"package_id":"forged","package_id":"trusted"}')
        with self.assertRaisesRegex(ValueError, "non-finite JSON constant"):
            strict_json_loads('{"value":NaN}')

    def test_bounded_secret_scan_covers_hyphenated_provider_token_families(self):
        self.assertTrue(contains_secret_like(b"credential=" + b"s" + b"k-proj-" + b"A" * 24))
        self.assertTrue(contains_secret_like(b"credential=" + b"s" + b"k-svcacct-" + b"B" * 24))
        self.assertFalse(contains_secret_like(b"documentation mentions a redacted provider token"))

    def test_manifest_package_id_and_included_allowlist_are_identity_bound(self):
        with tempfile.TemporaryDirectory(prefix="package-manifest-identity-") as raw:
            root = Path(raw) / "package"
            for name in ("PACKAGE_MANIFEST.json", "VERSION", "docs", "skills", "buildos"):
                source = PACKAGE / name
                if source.is_dir():
                    shutil.copytree(source, root / name)
                else:
                    root.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, root / name)
            manifest_path = root / "PACKAGE_MANIFEST.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["package_id"] = "forged-package"
            manifest["included"] = ["buildos"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            code, payload = invoke(root)
            self.assertEqual(code, 2)
            self.assertIn("MANIFEST_PACKAGE_ID_MISMATCH", payload["errors"])
            self.assertIn("MANIFEST_INCLUDED_ALLOWLIST_MISMATCH", payload["errors"])

    def test_manifest_release_evidence_path_must_exist_and_bind_reference(self):
        with tempfile.TemporaryDirectory(prefix="package-release-evidence-") as raw:
            root = Path(raw) / "package"
            for name in ("PACKAGE_MANIFEST.json", "VERSION", "skills", "buildos"):
                source = PACKAGE / name
                if source.is_dir():
                    shutil.copytree(source, root / name)
                else:
                    root.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, root / name)
            code, payload = invoke(root)
            self.assertEqual(code, 2)
            self.assertIn("MANIFEST_RELEASE_EVIDENCE_UNBOUND", payload["errors"])

    def test_manifest_authority_flags_and_runtime_schema_are_exact(self):
        with tempfile.TemporaryDirectory(prefix="package-authority-flags-") as raw:
            root = Path(raw) / "package"
            for name in ("PACKAGE_MANIFEST.json", "VERSION", "docs", "skills", "buildos"):
                source = PACKAGE / name
                if source.is_dir():
                    shutil.copytree(source, root / name)
                else:
                    root.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, root / name)
            manifest_path = root / "PACKAGE_MANIFEST.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["project_lifecycle_kit"]["mandatory_by_adoption_contract"] = False
            manifest["continuity_skill"]["kernel_enforced"] = True
            manifest["execution_runtime"]["runtime_schema"] = "forged.runtime.v0"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            code, payload = invoke(root)
            self.assertEqual(code, 2)
            self.assertIn("MANIFEST_LIFECYCLE_AUTHORITY_FLAGS_INVALID", payload["errors"])
            self.assertIn("MANIFEST_CONTINUITY_AUTHORITY_FLAGS_INVALID", payload["errors"])
            self.assertIn("MANIFEST_EXECUTION_RUNTIME_IDENTITY_MISMATCH", payload["errors"])

    def test_package_source_snapshot_requires_clean_git_and_ignores_uncommitted_bytes(self):
        with tempfile.TemporaryDirectory(prefix="package-source-snapshot-") as raw:
            root = Path(raw)
            self._git(root, "init")
            self._git(root, "config", "user.name", "Package Test")
            self._git(root, "config", "user.email", "package@example.invalid")
            (root / "payload.txt").write_text("committed\n", encoding="utf-8")
            (root / "PACKAGE_VALIDATION.json").write_text("{}\n", encoding="utf-8")
            (root / "PACKAGE_CONTENTS.sha256").write_text("placeholder\n", encoding="utf-8")
            manifest = {
                "frozen_kernel_commit": "0" * 40,
                "included": [
                    "PACKAGE_CONTENTS.sha256", "PACKAGE_MANIFEST.json",
                    "PACKAGE_VALIDATION.json", "payload.txt",
                ],
            }
            (root / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "frozen package source")
            frozen_commit = self._git(root, "rev-parse", "HEAD")
            manifest["frozen_kernel_commit"] = frozen_commit
            manifest["release_evidence"] = {"review_target": frozen_commit}
            (root / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
            self._git(root, "add", "PACKAGE_MANIFEST.json")
            self._git(root, "commit", "-m", "bind release metadata")
            with mock.patch.object(package_builder, "ROOT", root):
                commit, _, paths, frozen_manifest = package_builder.source_snapshot()
                self.assertEqual(frozen_manifest, manifest)
                (root / "payload.txt").write_text("uncommitted owner bytes\n", encoding="utf-8")
                payloads = package_builder.build_payloads(
                    paths, commit, {"schema": "test.validation.v1"},
                )
                self.assertEqual(payloads["payload.txt"], b"committed\n")
                with self.assertRaisesRegex(RuntimeError, "clean Git worktree"):
                    package_builder.source_snapshot()

    def test_package_source_rejects_unreviewed_post_review_content_delta(self):
        with tempfile.TemporaryDirectory(prefix="package-post-freeze-delta-") as raw:
            root = Path(raw)
            self._git(root, "init")
            self._git(root, "config", "user.name", "Package Test")
            self._git(root, "config", "user.email", "package@example.invalid")
            (root / "payload.txt").write_text("reviewed\n", encoding="utf-8")
            manifest = {
                "frozen_kernel_commit": "0" * 40,
                "included": [
                    "PACKAGE_CONTENTS.sha256", "PACKAGE_MANIFEST.json",
                    "PACKAGE_VALIDATION.json", "payload.txt",
                ],
            }
            (root / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "reviewed freeze")
            frozen_commit = self._git(root, "rev-parse", "HEAD")
            manifest["frozen_kernel_commit"] = frozen_commit
            manifest["release_evidence"] = {"review_target": frozen_commit}
            (root / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
            (root / "payload.txt").write_text("unreviewed executable/content change\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "unreviewed descendant")
            with mock.patch.object(package_builder, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "unreviewed post-review"):
                    package_builder.source_snapshot()

    def test_failed_staged_verification_never_publishes_release_named_zip(self):
        with tempfile.TemporaryDirectory(prefix="package-staging-") as raw:
            store = Path(raw)
            manifest = {"archive_name": "candidate.zip", "package_id": "candidate"}
            validation = {
                "manifest_sha256": "0" * 64, "frozen_kernel_commit": "1" * 40,
                "package_source_commit": "2" * 40, "package_source_tree": "3" * 40,
                "schema": "test.validation.v1",
            }
            with (
                mock.patch.object(package_builder, "PACKAGE_STORE", store),
                mock.patch.object(
                    package_builder, "verify_zip",
                    side_effect=RuntimeError("adversarial verification failure"),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "adversarial verification failure"):
                    package_builder.publish(
                        manifest, validation, {"PACKAGE_CONTENTS.sha256": b""},
                    )
            self.assertFalse((store / "candidate.zip").exists())
            self.assertFalse((store / "candidate.zip.validation.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
