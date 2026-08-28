from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from buildos.external_effect import execute_external_effect
from tests.test_thin_guard import AI, append, repository, run_git, snapshot_files


def cli(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(AI), "--root", str(root), *args],
        text=True, encoding="utf-8", errors="replace",
        capture_output=True, timeout=30,
    )


def effect_intent() -> dict:
    return {
        "effect_id": "external-create",
        "operation": "create",
        "target": "provider://account/resource",
        "request_digest": hashlib.sha256(b"request").hexdigest(),
    }


class SimplifiedCliTests(unittest.TestCase):
    def test_inspect_is_read_only_and_reports_git_without_lifecycle_authority(self):
        with repository() as (root, _):
            before = snapshot_files(root)
            result = cli(root, "inspect")
            after = snapshot_files(root)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["read_only"])
            self.assertEqual(payload["architecture"], "SIMPLIFIED_CONSEQUENTIAL_BOUNDARIES")
            self.assertEqual(payload["legacy_effects"]["status"], "ABSENT")
            self.assertNotIn("generation", payload)
            self.assertEqual(before, after)

    def test_scope_policy_is_reread_on_every_invocation_without_migration(self):
        with repository() as (root, _):
            policy = root / ".buildos-scope.json"
            policy.write_text(json.dumps({
                "strict_paths": ["app.py", ".buildos-scope.json"],
            }), encoding="utf-8")
            run_git(root, "add", ".buildos-scope.json")
            run_git(root, "commit", "-qm", "add scope policy")
            base = run_git(root, "rev-parse", "HEAD")
            append(root / "outside.txt")

            blocked = cli(
                root, "check", "--base", base, "--boundary", "R3",
                "--policy", ".buildos-scope.json",
            )
            policy.write_text(json.dumps({
                "strict_paths": ["app.py", "outside.txt", ".buildos-scope.json"],
            }), encoding="utf-8")
            passed = cli(
                root, "check", "--base", base, "--boundary", "R3",
                "--policy", ".buildos-scope.json",
            )

            self.assertEqual(blocked.returncode, 2)
            self.assertEqual(json.loads(blocked.stdout)["result"], "BLOCK")
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
            self.assertEqual(json.loads(passed.stdout)["result"], "PASS")
            self.assertFalse((root / ".buildos" / "control" / "CURRENT").exists())

    def test_effect_retry_check_and_reconcile_use_durable_effect_only(self):
        with repository() as (root, base):
            execute_external_effect(
                root,
                base=base,
                intent=effect_intent(),
                dispatcher=lambda _: (_ for _ in ()).throw(RuntimeError("ambiguous")),
            )

            retry = cli(root, "effect", "retry-check", "--effect-id", "external-create")
            reconciled = cli(
                root, "reconcile", "--effect-id", "external-create",
                "--outcome", "NO_EFFECT_CONFIRMED",
                "--evidence", "canonical provider query proves resource absent",
            )
            inspected = cli(root, "effect", "inspect", "--effect-id", "external-create")

            self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
            self.assertFalse(json.loads(retry.stdout)["retry_safety"]["safe"])
            self.assertEqual(reconciled.returncode, 0, reconciled.stdout + reconciled.stderr)
            self.assertEqual(
                json.loads(inspected.stdout)["effect"]["state"],
                "NO_EFFECT_CONFIRMED",
            )
            self.assertEqual(run_git(root, "status", "--porcelain"), "")

    def test_inspect_detects_unresolved_legacy_effect_read_only(self):
        with repository() as (root, _):
            control = root / ".buildos" / "control"
            generations = control / "generations"
            generations.mkdir(parents=True)
            generation = {
                "state": {
                    "execution": {
                        "effect_ledger": {
                            "legacy-attempt": {
                                "state": "DISPATCH_UNCONFIRMED",
                                "action_id": "publish",
                                "effect_contract_hash": "1" * 64,
                                "effect_input_sha256": "2" * 64,
                                "idempotency_key": None,
                                "provider_reference": None,
                                "reconciliation": None,
                            },
                        },
                    },
                },
            }
            (generations / "g0001.json").write_text(json.dumps(generation), encoding="utf-8")
            (control / "CURRENT").write_text(json.dumps({"file": "g0001.json"}), encoding="utf-8")
            before = snapshot_files(root)

            result = cli(root, "inspect")
            after = snapshot_files(root)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            legacy = json.loads(result.stdout)["legacy_effects"]
            self.assertEqual(legacy["status"], "UNRESOLVED")
            self.assertEqual(legacy["unresolved"][0]["effect_id"], "legacy-attempt")
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
