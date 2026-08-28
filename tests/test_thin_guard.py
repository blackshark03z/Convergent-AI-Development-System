from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from buildos.thin_guard import check


PACKAGE = Path(__file__).resolve().parents[1]
AI = PACKAGE / "scripts" / "ai.py"


def run_git(root: Path, *args: str, stdin: str | None = None) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=root, input=stdin, text=True, encoding="utf-8",
        errors="replace", capture_output=True, timeout=30,
    )
    if proc.returncode:
        raise AssertionError(proc.stdout + proc.stderr)
    return proc.stdout.strip()


@contextmanager
def repository():
    with tempfile.TemporaryDirectory(prefix="buildos-thin-guard-") as raw:
        root = Path(raw)
        run_git(root, "init", "-q")
        run_git(root, "config", "user.name", "Thin Guard Test")
        run_git(root, "config", "user.email", "thin-guard@example.invalid")
        (root / "app.py").write_text("print('baseline')\n", encoding="utf-8")
        (root / "outside.txt").write_text("outside baseline\n", encoding="utf-8")
        (root / "README.md").write_text("fixture\n", encoding="utf-8")
        (root / ".buildos").mkdir()
        (root / ".buildos" / "owned.txt").write_text("tracked control\n", encoding="utf-8")
        run_git(root, "add", ".")
        run_git(root, "commit", "-qm", "baseline")
        yield root, run_git(root, "rev-parse", "HEAD")


def append(path: Path, value: str = "change\n") -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(value)


def snapshot_files(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        result[relative] = (
            "DIRECTORY" if path.is_dir()
            else hashlib.sha256(path.read_bytes()).hexdigest()
        )
    return result


class ThinGuardRegressionTests(unittest.TestCase):
    def guard(self, root: Path, base: str, **policy) -> dict:
        return check(root, base=base, boundary="R3", **policy)

    def test_clean_descendant_outside_strict_scope_blocks(self):
        with repository() as (root, base):
            append(root / "outside.txt")
            run_git(root, "add", "outside.txt")
            run_git(root, "commit", "-qm", "outside pre-existing commit")

            result = self.guard(root, base, strict_paths=["app.py"])

            self.assertEqual(result["result"], "BLOCK")
            self.assertFalse(result["dirty"])
            self.assertEqual(result["relation_to_base"], "DESCENDANT")
            self.assertIn("outside.txt", result["committed_paths"])
            self.assertIn("STRICT_PATH_VIOLATION", result["reason_codes"])

    def test_dirty_outside_strict_scope_blocks(self):
        with repository() as (root, base):
            append(root / "outside.txt")

            result = self.guard(root, base, strict_paths=["app.py"])

            self.assertEqual(result["result"], "BLOCK")
            self.assertTrue(result["dirty"])
            self.assertIn("outside.txt", result["dirty_paths"])
            self.assertIn("STRICT_PATH_VIOLATION", result["reason_codes"])

    def test_clean_descendant_prohibited_path_blocks(self):
        with repository() as (root, base):
            (root / "secrets").mkdir()
            (root / "secrets" / "leak.txt").write_text("not a real secret\n", encoding="utf-8")
            run_git(root, "add", "secrets/leak.txt")
            run_git(root, "commit", "-qm", "pre-existing prohibited commit")

            result = self.guard(root, base, prohibited_paths=["secrets/**"])

            self.assertEqual(result["result"], "BLOCK")
            self.assertFalse(result["dirty"])
            self.assertIn("secrets/leak.txt", result["committed_paths"])
            self.assertIn("PROHIBITED_PATH_CHANGED", result["reason_codes"])

    def test_dirty_prohibited_path_blocks(self):
        with repository() as (root, base):
            (root / "secrets").mkdir()
            (root / "secrets" / "leak.txt").write_text("not a real secret\n", encoding="utf-8")

            result = self.guard(root, base, prohibited_paths=["secrets/**"])

            self.assertEqual(result["result"], "BLOCK")
            self.assertIn("secrets/leak.txt", result["dirty_paths"])
            self.assertIn("PROHIBITED_PATH_CHANGED", result["reason_codes"])

    def test_expected_deviation_without_hard_violation_warns(self):
        with repository() as (root, base):
            append(root / "outside.txt")

            result = self.guard(root, base, expected_paths=["app.py"])

            self.assertEqual(result["result"], "WARN")
            self.assertEqual(result["blocking_violations"], [])
            self.assertIn("EXPECTED_PATH_DEVIATION", result["reason_codes"])

    def test_expected_and_strict_compliant_delta_passes(self):
        with repository() as (root, base):
            append(root / "app.py")
            run_git(root, "add", "app.py")
            run_git(root, "commit", "-qm", "compliant change")

            result = self.guard(
                root, base,
                expected_paths=["app.py"],
                strict_paths=["app.py"],
                prohibited_paths=["secrets/**"],
            )

            self.assertEqual(result["result"], "PASS")
            self.assertEqual(result["reason_codes"], ["SCOPE_COMPLIANT"])
            self.assertEqual(result["changed_paths"], ["app.py"])

    def test_deletion_outside_strict_and_in_prohibited_scope_blocks(self):
        with repository() as (root, base):
            run_git(root, "rm", "outside.txt")
            run_git(root, "commit", "-qm", "delete outside")

            result = self.guard(
                root, base,
                strict_paths=["app.py"],
                prohibited_paths=["outside.txt"],
            )

            self.assertEqual(result["result"], "BLOCK")
            self.assertIn("outside.txt", result["deleted_paths"])
            self.assertIn("STRICT_PATH_VIOLATION", result["reason_codes"])
            self.assertIn("PROHIBITED_PATH_CHANGED", result["reason_codes"])

    def test_staged_index_type_change_outside_strict_scope_blocks_portably(self):
        with repository() as (root, base):
            blob = run_git(root, "hash-object", "-w", "--stdin", stdin="link-target\n")
            run_git(root, "update-index", "--cacheinfo", f"120000,{blob},outside.txt")

            result = self.guard(root, base, strict_paths=["app.py"])

            self.assertEqual(result["result"], "BLOCK")
            self.assertIn("outside.txt", result["dirty_paths"])
            self.assertIn("outside.txt", result["type_changed_paths"])
            violation = next(
                item for item in result["blocking_violations"]
                if item.get("path") == "outside.txt"
            )
            self.assertIn("TYPE_CHANGE", violation["change_kinds"])

    def test_tracked_control_delta_is_visible_and_guarded(self):
        with repository() as (root, base):
            append(root / ".buildos" / "owned.txt")

            result = self.guard(root, base)

            self.assertEqual(result["result"], "BLOCK")
            self.assertIn(".buildos/owned.txt", result["tracked_control_paths"])
            self.assertIn(".buildos/owned.txt", result["changed_control_paths"])
            self.assertIn("CONTROL_PATH_CHANGED", result["reason_codes"])

    def test_api_and_cli_checks_do_not_mutate_repository_or_control_state(self):
        with repository() as (root, base):
            append(root / "app.py")
            before = snapshot_files(root)

            direct = self.guard(root, base, strict_paths=["app.py"])
            cli = subprocess.run(
                [
                    sys.executable, str(AI), "--root", str(root), "check",
                    "--base", base, "--boundary", "R3", "--strict", "app.py",
                ],
                text=True, encoding="utf-8", errors="replace",
                capture_output=True, timeout=30,
            )
            after = snapshot_files(root)

            self.assertEqual(direct["result"], "PASS")
            self.assertEqual(cli.returncode, 0, cli.stdout + cli.stderr)
            self.assertEqual(json.loads(cli.stdout)["result"], "PASS")
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
