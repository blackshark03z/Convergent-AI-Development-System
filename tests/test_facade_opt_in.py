from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


PACKAGE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("buildos_worker_facade", PACKAGE / "scripts" / "ai.py")
assert SPEC is not None and SPEC.loader is not None
FACADE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FACADE)
ADMIN_SPEC = importlib.util.spec_from_file_location("buildos_admin_facade", PACKAGE / "scripts" / "ai_os.py")
assert ADMIN_SPEC is not None and ADMIN_SPEC.loader is not None
ADMIN_FACADE = importlib.util.module_from_spec(ADMIN_SPEC)
ADMIN_SPEC.loader.exec_module(ADMIN_FACADE)


class FacadeOptInTests(unittest.TestCase):
    def test_unenrolled_project_skips_context_epoch_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with patch.object(FACADE.subprocess, "run") as run:
                self.assertEqual(FACADE._epoch_preflight(["--root", str(root), "validate"]), 0)
            run.assert_not_called()

    def test_enrolled_project_runs_context_epoch_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".buildos-policy.json").write_text(json.dumps({"context_epoch": {"enabled": True}}), encoding="utf-8")
            result = SimpleNamespace(returncode=0, stdout="")
            with patch.object(FACADE.subprocess, "run", return_value=result) as run:
                self.assertEqual(FACADE._epoch_preflight(["--root", str(root), "validate"]), 0)
            self.assertIn("context_epoch.py", str(run.call_args.args[0][1]))

    def test_environment_override_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with patch.dict("os.environ", {"BUILDOS_CONTEXT_EPOCH_PREFLIGHT": "1"}):
                self.assertTrue(FACADE._context_epoch_preflight_enabled(root))
            with patch.dict("os.environ", {"BUILDOS_CONTEXT_EPOCH_PREFLIGHT": "0"}):
                self.assertFalse(FACADE._context_epoch_preflight_enabled(root))

    def test_v124_policy_composes_authority_and_lifecycle_behind_one_facade(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".buildos-policy.json").write_text(json.dumps({
                "execution_admission": {"enabled": True, "require_authority_record": True},
            }), encoding="utf-8")
            result = SimpleNamespace(returncode=0, stdout="")
            with patch.object(FACADE.subprocess, "run", return_value=result) as run:
                self.assertEqual(FACADE._adoption_preflight(["--root", str(root), "bootstrap"]), 0)
            commands = [str(call.args[0][1]) for call in run.call_args_list]
            self.assertTrue(any("execution_authority.py" in item for item in commands))
            self.assertTrue(any("project_lifecycle.py" in item for item in commands))

    def test_legacy_policy_does_not_silently_opt_in_to_new_admission(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".buildos-policy.json").write_text(json.dumps({"context_epoch": {"enabled": True}}), encoding="utf-8")
            with patch.object(FACADE.subprocess, "run") as run:
                self.assertEqual(FACADE._adoption_preflight(["--root", str(root), "bootstrap"]), 0)
            run.assert_not_called()

    def test_admin_facade_delegates_to_shared_admission_filter(self) -> None:
        with patch.object(ADMIN_FACADE, "_adoption_preflight", return_value=7) as preflight:
            self.assertEqual(
                ADMIN_FACADE._admin_preflight(["--root", "project", "adopt-existing-change"]),
                7,
            )
        preflight.assert_called_once()

    def test_admin_adoption_is_guarded_but_break_glass_abort_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".buildos-policy.json").write_text(json.dumps({
                "execution_admission": {"enabled": True, "require_authority_record": False},
            }), encoding="utf-8")
            self.assertEqual(
                FACADE._adoption_preflight(["--root", str(root), "adopt-existing-change"]),
                2,
            )
            self.assertEqual(FACADE._adoption_preflight(["--root", str(root), "abort"]), 0)


if __name__ == "__main__":
    unittest.main()
