from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from buildos.git_adapter import boundary_snapshot
from buildos.guarded_local import execute_high_cost
from tests.test_thin_guard import AI, append, repository, run_git


def native_result(code: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["native-tool"], returncode=code,
        stdout="native stdout\n", stderr="native stderr\n" if code else "",
    )


class GuardedLocalTests(unittest.TestCase):
    def execute(self, root: Path, base: str, **values) -> dict:
        return execute_high_cost(
            root, base=base, command=["native-tool"], **values,
        )

    def test_compliant_exact_state_executes_native_command_once(self):
        with repository() as (root, base):
            append(root / "app.py")
            with patch("buildos.guarded_local._spawn", return_value=native_result()) as spawn:
                result = self.execute(root, base, strict_paths=["app.py"])

            self.assertEqual(result["guard_result"], "PASS")
            self.assertTrue(result["executed"])
            self.assertEqual(result["command_exit_code"], 0)
            self.assertEqual(
                result["evaluated_observation_digest"],
                result["pre_spawn_observation_digest"],
            )
            spawn.assert_called_once()

    def test_hard_scope_violation_never_executes(self):
        with repository() as (root, base):
            append(root / "outside.txt")
            with patch("buildos.guarded_local._spawn") as spawn:
                result = self.execute(root, base, strict_paths=["app.py"])

            self.assertEqual(result["guard_result"], "BLOCK")
            self.assertIn("STRICT_PATH_VIOLATION", result["reason_codes"])
            self.assertFalse(result["executed"])
            spawn.assert_not_called()

    def test_committed_state_drift_before_spawn_blocks(self):
        with repository() as (root, base):
            real_observer = boundary_snapshot

            def commit_drift(observed_root: Path | str, observed_base: str) -> dict:
                append(root / "app.py", "committed drift\n")
                run_git(root, "add", "app.py")
                run_git(root, "commit", "-qm", "between-check commit drift")
                return real_observer(observed_root, observed_base)

            with (
                patch("buildos.guarded_local.boundary_snapshot", side_effect=commit_drift),
                patch("buildos.guarded_local._spawn") as spawn,
            ):
                result = self.execute(root, base, strict_paths=["app.py"])

            self.assertEqual(result["guard_result"], "BLOCK")
            self.assertEqual(result["reason_codes"], ["BLOCK_STALE_STATE"])
            self.assertNotEqual(result["evaluated_head"], result["pre_spawn_head"])
            self.assertFalse(result["executed"])
            spawn.assert_not_called()

    def test_dirty_state_drift_before_spawn_blocks(self):
        with repository() as (root, base):
            real_observer = boundary_snapshot

            def dirty_drift(observed_root: Path | str, observed_base: str) -> dict:
                append(root / "app.py", "dirty drift\n")
                return real_observer(observed_root, observed_base)

            with (
                patch("buildos.guarded_local.boundary_snapshot", side_effect=dirty_drift),
                patch("buildos.guarded_local._spawn") as spawn,
            ):
                result = self.execute(root, base, strict_paths=["app.py"])

            self.assertEqual(result["guard_result"], "BLOCK")
            self.assertEqual(result["reason_codes"], ["BLOCK_STALE_STATE"])
            self.assertNotEqual(
                result["evaluated_observation_digest"],
                result["pre_spawn_observation_digest"],
            )
            self.assertFalse(result["executed"])
            spawn.assert_not_called()

    def test_prohibited_path_delta_never_executes(self):
        with repository() as (root, base):
            (root / "secrets").mkdir()
            (root / "secrets" / "leak.txt").write_text(
                "not a real secret\n", encoding="utf-8",
            )
            with patch("buildos.guarded_local._spawn") as spawn:
                result = self.execute(
                    root, base, prohibited_paths=["secrets/**"],
                )

            self.assertEqual(result["guard_result"], "BLOCK")
            self.assertIn("PROHIBITED_PATH_CHANGED", result["reason_codes"])
            spawn.assert_not_called()

    def test_tracked_control_delta_never_executes_without_scope_policy(self):
        with repository() as (root, base):
            append(root / ".buildos" / "owned.txt")
            with patch("buildos.guarded_local._spawn") as spawn:
                result = self.execute(root, base)

            self.assertEqual(result["guard_result"], "BLOCK")
            self.assertIn("CONTROL_PATH_CHANGED", result["reason_codes"])
            spawn.assert_not_called()

    def test_warn_only_expected_deviation_preserves_warn_and_executes(self):
        with repository() as (root, base):
            append(root / "outside.txt")
            with patch("buildos.guarded_local._spawn", return_value=native_result()) as spawn:
                result = self.execute(root, base, expected_paths=["app.py"])

            self.assertEqual(result["guard_result"], "WARN")
            self.assertIn("EXPECTED_PATH_DEVIATION", result["reason_codes"])
            self.assertTrue(result["executed"])
            spawn.assert_called_once()

    def test_native_nonzero_exit_is_returned_once_without_lifecycle_block(self):
        with repository() as (root, base):
            with patch("buildos.guarded_local._spawn", return_value=native_result(7)) as spawn:
                result = self.execute(root, base)

            self.assertEqual(result["guard_result"], "PASS")
            self.assertTrue(result["executed"])
            self.assertEqual(result["command_exit_code"], 7)
            self.assertEqual(result["command_stderr"], "native stderr\n")
            spawn.assert_called_once()

    def test_cli_invokes_native_argv_and_returns_json_evidence(self):
        with repository() as (root, base):
            proc = subprocess.run(
                [
                    sys.executable, str(AI), "--root", str(root), "high-cost",
                    "--base", base, "--strict", "app.py", "--",
                    sys.executable, "-c", "print('native-ok')",
                ],
                text=True, encoding="utf-8", errors="replace",
                capture_output=True, timeout=30,
            )

            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            result = json.loads(proc.stdout)
            self.assertEqual(result["guard_result"], "PASS")
            self.assertTrue(result["executed"])
            self.assertEqual(result["command_exit_code"], 0)
            self.assertEqual(result["command_stdout"], "native-ok\n")

    def test_cli_returns_native_nonzero_exit_without_retry(self):
        with repository() as (root, base):
            proc = subprocess.run(
                [
                    sys.executable, str(AI), "--root", str(root), "high-cost",
                    "--base", base, "--", sys.executable, "-c",
                    "import sys; print('native-failed'); sys.exit(7)",
                ],
                text=True, encoding="utf-8", errors="replace",
                capture_output=True, timeout=30,
            )

            self.assertEqual(proc.returncode, 7, proc.stdout + proc.stderr)
            result = json.loads(proc.stdout)
            self.assertEqual(result["guard_result"], "PASS")
            self.assertTrue(result["executed"])
            self.assertEqual(result["command_exit_code"], 7)
            self.assertEqual(result["command_stdout"], "native-failed\n")


if __name__ == "__main__":
    unittest.main()
