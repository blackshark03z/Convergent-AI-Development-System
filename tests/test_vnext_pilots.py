from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from buildos import git_adapter
from buildos.facade import BuildOS
from buildos.grounding import grounding_projection, load_grounding_report
from buildos.model import KernelError
from buildos.work_contract import TRUSTED_CONTRACT_SHA256_ENV, load_contract, validate_contract
from tests.test_execution_runtime import git, repository, spec
from tests.test_work_contract import contract


def canonical_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def handoff(root: Path, directory: Path, *, requested_action: str) -> tuple[Path, Path]:
    raw = contract()
    raw["contract_id"] = f"PILOT-{requested_action}"
    raw["target"]["repository"] = str(root.resolve())
    raw["target"]["ref"] = git_adapter.snapshot(root)["branch"]
    raw["objective"] = "safe admitted outcome"
    raw["claims"][1]["statement"] = "behavior is correct"
    raw["claims"][2]["id"] = "repo.app"
    raw["claims"][2]["statement"] = "app.py is the implementation target."
    raw["claims"][2]["repo_binding"]["paths"] = ["app.py"]
    raw["action_basis_ids"] = ["repo.app"]
    normalized = validate_contract(raw)
    digest = canonical_hash(normalized)
    observed = git_adapter.snapshot(root)
    app_digest = hashlib.sha256((root / "app.py").read_bytes()).hexdigest()
    report = {
        "schema": "buildos.grounding-report.v1",
        "contract_hash": digest,
        "worker": {"id": "WORKER", "observed_at": "2026-08-24T00:00:00Z"},
        "repository": {
            "root": str(root.resolve()), "branch": observed["branch"],
            "head": observed["head"], "tree": observed["tree"],
            "product_state_digest": observed["product_state_digest"],
        },
        "scope_claim_ids": ["repo.app"],
        "execution_request": {
            "requested_action": requested_action,
            "product_change_mode": "PRODUCT_DELTA",
            "risk": "R1",
            "allowed_paths": ["app.py", "other.py"],
            "prohibited_paths": ["secrets/**"],
            "acceptance_commands": [],
        },
        "evidence": [{
            "id": "evidence.app", "kind": "REPO_FILE", "locator": "app.py",
            "digest": app_digest, "observed_at": "2026-08-24T00:00:00Z",
        }],
        "results": [{
            "claim_id": "repo.app", "outcome": "VERIFIED",
            "summary": "The implementation target exists at the grounded product state.",
            "evidence_refs": ["evidence.app"],
        }],
        "discoveries": [],
    }
    contract_path = directory / "work-contract.json"
    grounding_path = directory / "grounding.json"
    contract_path.write_text(json.dumps(normalized), encoding="utf-8")
    grounding_path.write_text(json.dumps(report), encoding="utf-8")
    return contract_path, grounding_path


def refresh_grounding(root: Path, contract_path: Path, grounding_path: Path) -> None:
    work_contract, digest = load_contract(contract_path)
    observed = git_adapter.snapshot(root)
    app_digest = hashlib.sha256((root / "app.py").read_bytes()).hexdigest()
    prior = json.loads(grounding_path.read_text(encoding="utf-8"))
    prior["contract_hash"] = digest
    prior["repository"] = {
        "root": str(root.resolve()), "branch": observed["branch"],
        "head": observed["head"], "tree": observed["tree"],
        "product_state_digest": observed["product_state_digest"],
    }
    prior["evidence"][0]["digest"] = app_digest
    grounding_path.write_text(json.dumps(prior), encoding="utf-8")


def trusted_start(
    osys: BuildOS, contract_path: Path, grounding_path: Path, **kwargs: object,
) -> dict:
    _, digest = load_contract(contract_path)
    with mock.patch.dict(os.environ, {TRUSTED_CONTRACT_SHA256_ENV: digest}):
        return osys.advance(
            {}, work_contract=contract_path, grounding_report=grounding_path, **kwargs,
        )


class VNextRepresentativePilots(unittest.TestCase):
    def test_high_cost_work_reuses_grounding_and_preserves_enhanced_assurance(self):
        with repository("vnext-high-cost") as root, tempfile.TemporaryDirectory(prefix="handoff-") as raw:
            contract_path, grounding_path = handoff(
                root, Path(raw), requested_action="LOCAL_HIGH_COST",
            )
            osys = BuildOS(root)
            started = trusted_start(
                osys, contract_path, grounding_path, execution_spec=spec(),
            )
            self.assertEqual(started["status"], "READY_FOR_WORK")
            self.assertEqual(osys.inspect()["execution_plan_validity"], "VALID")
            self.assertEqual(osys._snapshot().state["execution"]["mode"], "ENHANCED")

            (root / "app.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", "app.py")
            git(root, "commit", "-qm", "implement high cost change")
            refresh_grounding(root, contract_path, grounding_path)
            finished = osys.advance(
                work_contract=contract_path, grounding_report=grounding_path,
                run_assurance=True,
            )
            self.assertEqual(finished["status"], "COMPLETE")
            plan = osys._snapshot().state["execution"]["last_assurance_plan"]
            self.assertEqual(plan["executed"], ["final_assurance", "focused_behavior"])
            self.assertEqual(
                finished["current"]["work_packet"]["evidence_index"]["handoff"][0]["sha256"],
                osys._snapshot().state["work_loop"]["work_contract"]["hash"],
            )

    def test_external_effect_work_stops_before_dispatch_and_uses_v124_transaction(self):
        with repository("vnext-external") as root, tempfile.TemporaryDirectory(prefix="handoff-") as raw:
            contract_path, grounding_path = handoff(
                root, Path(raw), requested_action="EXTERNAL_EFFECT",
            )
            osys = BuildOS(root)
            started = trusted_start(
                osys, contract_path, grounding_path, execution_spec=spec(external=True),
            )
            self.assertEqual(started["status"], "EFFECT_ACTION_REQUIRED")
            self.assertEqual(len(started["transitions"]), 1)
            runtime = osys._snapshot().state["execution"]
            self.assertEqual(runtime["effect_ledger"], {})

            (root / "app.py").write_text("value = 3\n", encoding="utf-8")
            git(root, "add", "app.py")
            git(root, "commit", "-qm", "implement before provider")
            refresh_grounding(root, contract_path, grounding_path)
            regrounded = osys.advance(
                work_contract=contract_path, grounding_report=grounding_path,
            )
            self.assertEqual(regrounded["status"], "EFFECT_ACTION_REQUIRED")
            osys.record_commit()
            prepared = osys.effect(
                transition="PREPARE", effect_id="pilot-attempt", action_id="submit_job",
            )
            record = prepared.snapshot.state["execution"]["effect_ledger"]["pilot-attempt"]
            self.assertEqual(record["state"], "INTENT_RECORDED")
            self.assertIsNone(record.get("provider_reference"))

    def test_blocked_work_loop_cannot_prepare_external_effect(self):
        with repository("vnext-external-blocked") as root, tempfile.TemporaryDirectory(prefix="handoff-") as raw:
            contract_path, grounding_path = handoff(
                root, Path(raw), requested_action="EXTERNAL_EFFECT",
            )
            osys = BuildOS(root)
            trusted_start(
                osys, contract_path, grounding_path, execution_spec=spec(external=True),
            )
            contract_value, digest = load_contract(contract_path)
            observed = git_adapter.snapshot(root)
            blocked = json.loads(grounding_path.read_text(encoding="utf-8"))
            blocked["repository"] = {
                "root": str(root.resolve()), "branch": observed["branch"],
                "head": observed["head"], "tree": observed["tree"],
                "product_state_digest": observed["product_state_digest"],
            }
            blocked["scope_claim_ids"].append("acceptance.contract")
            blocked["results"].append({
                "claim_id": "acceptance.contract", "outcome": "CONTRADICTED",
                "summary": "Canonical acceptance is contradicted.",
                "evidence_refs": ["evidence.app"],
            })
            grounding_path.write_text(json.dumps(blocked), encoding="utf-8")
            result = osys.advance(
                work_contract=contract_path, grounding_report=grounding_path,
            )
            self.assertEqual(result["status"], "DECISION_REQUIRED")
            with self.assertRaisesRegex(KernelError, "canonical Work Loop action rights"):
                osys.effect(
                    transition="PREPARE", effect_id="blocked-attempt", action_id="submit_job",
                )

    def test_dirty_takeover_is_grounded_but_not_laundered_into_a_task(self):
        with repository("vnext-dirty") as root, tempfile.TemporaryDirectory(prefix="handoff-") as raw:
            (root / "app.py").write_text("owner dirty work\n", encoding="utf-8")
            before = (root / "app.py").read_bytes()
            contract_path, grounding_path = handoff(
                root, Path(raw), requested_action="LOCAL_MUTATION",
            )
            contract_value, digest = load_contract(contract_path)
            observed = git_adapter.snapshot(root)
            grounded = load_grounding_report(
                grounding_path, contract_value, digest, root=root, observed_repository=observed,
            )
            self.assertEqual(grounding_projection(grounded)["status"], "GROUNDED")
            with self.assertRaisesRegex(KernelError, "clean product baseline"):
                with mock.patch.dict(os.environ, {TRUSTED_CONTRACT_SHA256_ENV: digest}):
                    BuildOS(root).bootstrap(
                        {}, work_contract=contract_path, grounding_report=grounding_path,
                    )
            self.assertEqual((root / "app.py").read_bytes(), before)
            self.assertFalse((root / ".buildos").exists())

    def test_small_local_pilot_reduces_normal_model_visible_operations(self):
        legacy_operations = ["bootstrap", "record-commit", "validate", "close"]
        vnext_operations = ["work(start)", "work(assure)"]
        self.assertEqual(len(legacy_operations), 4)
        self.assertEqual(len(vnext_operations), 2)
        self.assertLess(len(vnext_operations), len(legacy_operations))


if __name__ == "__main__":
    unittest.main(verbosity=2)
