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

    def test_command_classification_consumes_root_values_before_selecting_subcommand(self) -> None:
        for name in ("work", "contract", "inspect", "recover"):
            with self.subTest(relative=name):
                argv = ["--root", name, "inspect"]
                self.assertEqual(FACADE._requested_command(argv), "inspect")
                with patch.object(FACADE.subprocess, "run") as run:
                    self.assertEqual(FACADE._epoch_preflight(argv), 0)
                    self.assertEqual(FACADE._adoption_preflight(argv), 0)
                    self.assertEqual(ADMIN_FACADE._admin_preflight(argv), 0)
                run.assert_not_called()

        with tempfile.TemporaryDirectory() as raw:
            for name in ("work", "contract", "inspect", "recover"):
                absolute = str(Path(raw) / name)
                with self.subTest(absolute=absolute):
                    self.assertEqual(
                        FACADE._requested_command(["--root", absolute, "inspect"]),
                        "inspect",
                    )

    def test_option_values_after_the_command_cannot_reclassify_the_route(self) -> None:
        argv = ["--root", "project", "work", "--work-contract", "recover", "--grounding", "inspect"]
        self.assertEqual(FACADE._requested_command(argv), "work")

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

    def test_admin_new_revision_is_guarded_by_integrated_admission(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".buildos-policy.json").write_text(json.dumps({
                "execution_admission": {"enabled": True, "require_authority_record": False},
            }), encoding="utf-8")
            self.assertEqual(
                FACADE._adoption_preflight(["--root", str(root), "new-revision"]),
                2,
            )

    def test_admin_command_semantics_keep_only_true_break_glass_unguarded(self) -> None:
        self.assertIn("new-revision", FACADE.EXECUTION_AUTHORITY_MUTATORS)
        self.assertIn("adopt-existing-change", FACADE.EXECUTION_AUTHORITY_CREATORS)
        self.assertEqual(FACADE.BREAK_GLASS_COMMANDS, {"abort", "recover"})
        self.assertEqual(
            FACADE.DIAGNOSTIC_TELEMETRY_COMMANDS,
            {"status", "next", "assurance-plan", "telemetry-ingest"},
        )
        self.assertNotIn("abort", FACADE.ADMISSION_COMMANDS)
        self.assertNotIn("recover", FACADE.ADMISSION_COMMANDS)

    def test_valid_enrolled_admin_new_revision_composes_all_preflights(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".buildos-policy.json").write_text(json.dumps({
                "execution_admission": {"enabled": True, "require_authority_record": True},
                "context_epoch": {"enabled": True},
            }), encoding="utf-8")
            result = SimpleNamespace(returncode=0, stdout="")
            with patch.object(FACADE.subprocess, "run", return_value=result) as run:
                self.assertEqual(
                    ADMIN_FACADE._admin_preflight(["--root", str(root), "new-revision"]),
                    0,
                )
            commands = [str(call.args[0][1]) for call in run.call_args_list]
            self.assertEqual(len(commands), 3)
            self.assertIn("execution_authority.py", commands[0])
            self.assertIn("project_lifecycle.py", commands[1])
            self.assertIn("context_epoch.py", commands[2])

    def test_invalid_authority_or_policy_blocks_before_context_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".buildos-policy.json").write_text(json.dumps({
                "execution_admission": {"enabled": True, "require_authority_record": True},
                "context_epoch": {"enabled": True},
            }), encoding="utf-8")
            failed = SimpleNamespace(returncode=2, stdout='{"status":"FAIL"}')
            with patch.object(FACADE.subprocess, "run", return_value=failed) as run:
                self.assertEqual(
                    ADMIN_FACADE._admin_preflight(["--root", str(root), "new-revision"]),
                    2,
                )
            self.assertEqual(run.call_count, 1)

            invalid_policy = {"execution_admission": {"enabled": True, "require_authority_record": False}}
            (root / ".buildos-policy.json").write_text(json.dumps(invalid_policy), encoding="utf-8")
            with patch.object(FACADE.subprocess, "run") as run:
                self.assertEqual(
                    ADMIN_FACADE._admin_preflight(["--root", str(root), "new-revision"]),
                    2,
                )
            run.assert_not_called()

    def test_admin_break_glass_and_telemetry_remain_available(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".buildos-policy.json").write_text(json.dumps({
                "execution_admission": {"enabled": True, "require_authority_record": False},
                "context_epoch": {"enabled": True},
            }), encoding="utf-8")
            with patch.object(FACADE.subprocess, "run") as run:
                for command in ("abort", "recover", "telemetry-ingest"):
                    self.assertEqual(
                        ADMIN_FACADE._admin_preflight(["--root", str(root), command]),
                        0,
                    )
            run.assert_not_called()

    def test_legacy_unenrolled_admin_new_revision_remains_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with patch.object(FACADE.subprocess, "run") as run:
                self.assertEqual(
                    ADMIN_FACADE._admin_preflight(["--root", str(root), "new-revision"]),
                    0,
                )
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
