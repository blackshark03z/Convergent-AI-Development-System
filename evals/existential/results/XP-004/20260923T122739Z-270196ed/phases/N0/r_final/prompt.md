You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-004 Reasoning Lead Prompt - N0 / No CADS

You are R, the Reasoning Lead. You do not edit product code.

## Frozen Raw Owner Goal

Close the product-verification and lineage gap for the canonical five video
formats so that acceptance proves the selected format and the resulting product
state rather than relying on internally consistent implementation claims.

The system must be able to verify that the chosen F1-F5 format semantics flow
through the real product plan/timeline/compose/render path and that the final
accepted result can be attributed to the exact source/product state that was
verified.

## Fixed intent and constraints

- The selected canonical F1-F5 format must retain its legal source semantics through the real plan, timeline, compose, and render path.
- Final acceptance must identify the exact selected format, source assets, and verified product/output lineage.
- Preserve one canonical product truth across CLI and Web.
- Do not silently substitute a different source class or format when required media or verification is missing.
- Judge observable product behavior, not a prescribed implementation shape.
- Do not call paid/external providers or the canonical production runtime.
- The historical implementation and held-out evaluator are hidden.
- Do not inspect sibling benchmark workspaces or results.
- You may inspect the assigned neutral repository, but must not edit product code.

## Common R-to-I rule

Produce the smallest Implementation Brief that makes the outcome testable.
SPEC UNTIL TESTABLE, NOT SPEC UNTIL COMPLETE.
Stop specifying once multiple implementations could satisfy the brief, PASS/FAIL
can be judged from observable outcome, and I need not invent a material product
preference or consequence boundary.

Your brief may use Outcome, Acceptance, Constraints / Non-goals, Effects /
Authority, and material assumptions/open questions only if needed. Do not add
design/architecture/task artifacts unless they solve a concrete ambiguity or risk.

## Arm treatment

Use your normal reasoning from the Raw Owner Goal and neutral repository. Do not use CADS concepts/templates or a prescribed spec workflow.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.


IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** Product acceptance for the canonical RC4 F1–F5 formats proves that the selected format’s legal sources survive the real plan → timeline → compose → render path, and binds the accepted master to the exact product state and media used.

**Acceptance:**

- Offline, distinguishable fixtures exercise each format through the CLI and Web product paths without hand-built schedules or external providers. Both paths apply the same format rules and report the same acceptance outcome.
- Verification checks the rendered result as well as its plan and timeline: F1 has a generated-video opening and generated-image body; F2 has a generated-video opening plus both stock and generated video afterward; F3 uses generated images throughout; F4 visibly combines the original video inset with an online-stock background; F5 uses online-stock footage throughout. Source class must be supported by the selected asset’s provenance, not merely its label.
- A missing, substituted, ambiguous, or changed required asset; a changed plan or timeline; or a stale or changed output prevents Product Accepted. Failure remains attributed to the selected format unless an explicit, authorized format change creates a newly verified run.
- The final acceptance evidence identifies the selected format, exact input assets and content, relevant product code/configuration state, verified plan/timeline/compose state, and final output content. It can be checked against those states and fails if any bound state changes.

**Constraints:** Use the current RC4 canonical format meanings. Verification must run locally without paid providers or the canonical production runtime. Implementation shape and evidence serialization are open.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: The verifier can return `PRODUCT_ACCEPTED` for arbitrary output bytes because source provenance, render observations, and stage hashes are supplied by the caller. The fixtures never exercise the real product path.

Connect acceptance to actual offline CLI and Web runs for each F1–F5 format. Verify the selected format and source provenance through the produced plan, timeline, compose state, and decoded rendered output, including F4’s visible inset and background. Bind the result to the exact assets, relevant code and configuration, stage artifacts, and output used by that run. Tests must show both paths agree and that substitution or changes to any bound state reject acceptance, even if caller-supplied evidence is rewritten. Keep the selected format on failure; use no paid providers or canonical production runtime.

I completion report:
Implemented a shared offline RC4 acceptance verifier in [product_acceptance.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T122739Z-270196ed/arms/N0/videopipeline/product_acceptance.py). It checks format grammar, asset hashes and provenance, plan and timeline hashes, output hash, F4 layout evidence, render observations, and product-state file hashes. Added the `verify-format` CLI command and `POST /api/format/verify`, both using the same verifier. Added synthetic fixtures for F1–F5 and changed-asset/timeline rejection cases in [test_product_acceptance.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T122739Z-270196ed/arms/N0/tests/test_product_acceptance.py).

**Checks run:** `python -m pytest tests/test_product_acceptance.py tests/test_format_grammar.py tests/test_golden_fixtures.py videopipeline/tests/test_web_server.py -q` passed (31 tests); `python -m compileall -q videopipeline` passed; `python -m videopipeline.cli --help` lists `verify-format`.

**Limitations:** Fixtures use synthetic files and render observations supplied as evidence; they do not render video or independently inspect pixels. I did not run the exact same evidence through both CLI and Web endpoints as an integration check. The existing pipeline’s compose/render flow is not yet wired to generate this acceptance evidence automatically, so this adds a shared verification gate rather than proving full product-path acceptance.

No material owner decision was needed. I cannot claim Product Acceptance.
Repair report:
I wasn’t able to complete the repair. The existing verifier still trusts caller-supplied provenance and render observations, and I did not connect acceptance to artifacts from actual offline CLI and Web runs.

I inspected the format validator, timeline builder, CLI, and Web compose handlers. The current pipeline has separate compose paths, and its render path uses the NVENC engine; the required offline fixtures and shared path need further implementation before this candidate can be reviewed against the repair brief. No checks were run.

Candidate tree: e163050f8076d46ce36e56fec5cc8d7de531ba00
Candidate status:
A  tests/test_product_acceptance.py
M  videopipeline/cli.py
A  videopipeline/product_acceptance.py
M  videopipeline/web/server.py
Candidate diff:
diff --git a/tests/test_product_acceptance.py b/tests/test_product_acceptance.py
new file mode 100644
index 0000000..a2a31d8
--- /dev/null
+++ b/tests/test_product_acceptance.py
@@ -0,0 +1,76 @@
+"""Offline acceptance fixtures exercise shared RC4 verification across formats."""
+import hashlib
+import json
+from pathlib import Path
+
+import pytest
+
+from videopipeline.product_acceptance import verify_evidence
+
+
+def digest(path):
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+def make_evidence(root, fmt):
+    classes = {
+        "F1": ["GENERATED_VIDEO", "GENERATED_IMAGE"],
+        "F2": ["GENERATED_VIDEO", "STOCK_ONLINE", "GENERATED_VIDEO"],
+        "F3": ["GENERATED_IMAGE", "GENERATED_IMAGE"],
+        "F4": ["STOCK_ONLINE", "ORIGINAL_REUP_VIDEO"],
+        "F5": ["STOCK_ONLINE", "STOCK_ONLINE"],
+    }[fmt]
+    assets, timeline = {}, []
+    for index, source in enumerate(classes):
+        asset_id = f"{fmt}-asset-{index}"
+        name = f"{asset_id}.bin"
+        path = root / name
+        path.write_bytes(f"distinguishable fixture {fmt} {index}".encode())
+        assets[asset_id] = {"path": name, "sha256": digest(path), "provenance": {
+            "issuer": "offline-fixture", "asset_id": asset_id, "source_class": source}}
+        row = {"index": index, "start": index * 2, "duration": 2, "type": "fixture",
+               "asset_id": asset_id, "source_class": source}
+        if fmt == "F1" and index == 0 or fmt == "F2" and index == 0:
+            row["type"] = "chap1_opening"
+        if fmt == "F4":
+            row["layout"] = "background" if index == 0 else "inset"
+        timeline.append(row)
+    plan = {"format_id": fmt}
+    output = root / f"{fmt}-render.bin"
+    output.write_bytes(f"rendered fixture output for {fmt}".encode())
+    observations = {
+        "F1": ["opening:GENERATED_VIDEO", "body:GENERATED_IMAGE"],
+        "F2": ["opening:GENERATED_VIDEO", "body:STOCK_ONLINE", "body:GENERATED_VIDEO"],
+        "F3": ["body:GENERATED_IMAGE"],
+        "F4": ["background:STOCK_ONLINE", "inset:ORIGINAL_REUP_VIDEO"],
+        "F5": ["body:STOCK_ONLINE"],
+    }[fmt]
+    canonical = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
+    source_file = Path(__file__).resolve().parents[1] / "videopipeline" / "format_validator.py"
+    product_file = root / "format_validator.py"
+    product_file.write_bytes(source_file.read_bytes())
+    return {"selected_format": fmt, "plan": plan, "timeline": timeline, "assets": assets,
+        "compose": {"plan_hash": canonical(plan), "timeline_hash": canonical(timeline)},
+        "render": {"output_path": output.name, "output_sha256": digest(output), "observations": observations},
+        "product_state": {"files": {"format_validator.py": digest(product_file)}}}
+
+
+@pytest.mark.parametrize("fmt", ["F1", "F2", "F3", "F4", "F5"])
+def test_offline_format_evidence_accepts(tmp_path, fmt):
+    evidence = make_evidence(tmp_path, fmt)
+    assert verify_evidence(evidence, tmp_path)["status"] == "PRODUCT_ACCEPTED"
+
+
+def test_changed_required_asset_rejects(tmp_path):
+    evidence = make_evidence(tmp_path, "F5")
+    (tmp_path / evidence["assets"]["F5-asset-0"]["path"]).write_bytes(b"substituted")
+    result = verify_evidence(evidence, tmp_path)
+    assert result["status"] == "REJECTED"
+    assert any("content changed" in error for error in result["errors"])
+
+
+def test_changed_timeline_rejects(tmp_path):
+    evidence = make_evidence(tmp_path, "F3")
+    evidence["timeline"][0]["asset_id"] = "missing"
+    result = verify_evidence(evidence, tmp_path)
+    assert result["status"] == "REJECTED"
diff --git a/videopipeline/cli.py b/videopipeline/cli.py
index b51124e..aa07fa7 100644
--- a/videopipeline/cli.py
+++ b/videopipeline/cli.py
@@ -268,6 +268,17 @@ def cmd_doctor(args):
             print(f"   -> {c['details']}")
     print("\n============================================================")
 
+def cmd_verify_format(args):
+    """Verify offline RC4 acceptance evidence."""
+    import json
+    from .product_acceptance import verify_evidence
+    evidence_path = Path(args.evidence).resolve()
+    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
+    result = verify_evidence(evidence, Path(args.root or evidence_path.parent).resolve())
+    print(json.dumps(result, indent=2, ensure_ascii=False))
+    if result["status"] != "PRODUCT_ACCEPTED":
+        raise SystemExit(2)
+
 def main():
     parser = argparse.ArgumentParser(description="videopipeline CLI (CADS Architecture)")
     subparsers = parser.add_subparsers(dest="command", help="Pipeline commands")
@@ -300,6 +311,9 @@ def main():
 
     # System Doctor
     subparsers.add_parser("doctor", help="Run comprehensive pre-flight system diagnostics")
+    verify_parser = subparsers.add_parser("verify-format", help="Verify offline RC4 acceptance evidence")
+    verify_parser.add_argument("--evidence", required=True)
+    verify_parser.add_argument("--root")
 
     args = parser.parse_args()
     if not args.command:
@@ -314,7 +328,8 @@ def main():
         "qa": cmd_qa,
         "run": cmd_run,
         "gui": cmd_gui,
-        "doctor": cmd_doctor
+        "doctor": cmd_doctor,
+        "verify-format": cmd_verify_format
     }
     cmds[args.command](args)
 
diff --git a/videopipeline/product_acceptance.py b/videopipeline/product_acceptance.py
new file mode 100644
index 0000000..09ed041
--- /dev/null
+++ b/videopipeline/product_acceptance.py
@@ -0,0 +1,120 @@
+"""Offline, state-bound product acceptance for canonical RC4 format runs.
+
+Evidence is a JSON document with selected_format, plan, timeline, assets,
+compose, and render objects. Asset provenance and render observations are
+explicit inputs so this verifier never infers source class from a filename.
+"""
+import hashlib
+import json
+from pathlib import Path
+from typing import Any, Dict, List
+
+from .format_validator import FormatValidator
+from .models import FormatId, SourceClass, VisualSegment, create_default_format_plan
+
+
+def sha256_file(path: Path) -> str:
+    digest = hashlib.sha256()
+    with path.open("rb") as stream:
+        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
+            digest.update(chunk)
+    return digest.hexdigest()
+
+
+def _hash_json(value: Any) -> str:
+    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
+
+
+def verify_evidence(evidence: Dict[str, Any], root: Path) -> Dict[str, Any]:
+    """Return a reproducible acceptance result; malformed evidence fails closed."""
+    errors: List[str] = []
+    try:
+        fmt = FormatId(str(evidence["selected_format"]).upper())
+        plan = evidence["plan"]
+        timeline = evidence["timeline"]
+        assets = evidence["assets"]
+        compose = evidence["compose"]
+        render = evidence["render"]
+        if plan.get("format_id") != fmt.value:
+            errors.append("plan format does not match selected format")
+        segments = []
+        observed_classes: Dict[str, str] = {}
+        seen_paths = set()
+        for row in timeline:
+            asset_id = row["asset_id"]
+            asset = assets.get(asset_id)
+            if not asset:
+                errors.append(f"required asset missing: {asset_id}")
+                continue
+            path = (root / asset["path"]).resolve()
+            if not path.is_relative_to(root.resolve()):
+                errors.append(f"asset escapes evidence root: {asset_id}")
+                continue
+            if not path.is_file():
+                errors.append(f"required asset missing: {asset_id}")
+                continue
+            if str(path).casefold() in seen_paths:
+                errors.append(f"ambiguous duplicate asset path: {asset_id}")
+            seen_paths.add(str(path).casefold())
+            actual_hash = sha256_file(path)
+            if actual_hash != asset.get("sha256"):
+                errors.append(f"asset content changed: {asset_id}")
+            provenance = asset.get("provenance", {})
+            source = provenance.get("source_class")
+            if not provenance.get("issuer") or not provenance.get("asset_id") or not source:
+                errors.append(f"asset provenance incomplete: {asset_id}")
+                continue
+            if provenance.get("asset_id") != asset_id:
+                errors.append(f"asset provenance identity mismatch: {asset_id}")
+            if row.get("source_class") != source:
+                errors.append(f"asset provenance/source mismatch: {asset_id}")
+            observed_classes[asset_id] = source
+            segments.append(VisualSegment(index=int(row["index"]), start_time=float(row["start"]),
+                duration=float(row["duration"]), segment_type=str(row.get("type", "")),
+                source_path=path, source_class=SourceClass(source), description=str(row.get("description", ""))))
+
+        if not errors:
+            result = FormatValidator.validate_timeline(segments, create_default_format_plan(fmt))
+            if fmt == FormatId.F4:
+                for row in timeline:
+                    if row.get("layout") != "inset" and row.get("source_class") == SourceClass.ORIGINAL_REUP_VIDEO.value:
+                        errors.append("F4 original video must be rendered as inset")
+                if not any(row.get("source_class") == SourceClass.STOCK_ONLINE.value and row.get("layout") == "background" for row in timeline):
+                    errors.append("F4 requires visible online-stock background")
+        else:
+            result = {"valid": False}
+        if compose.get("plan_hash") != _hash_json(plan):
+            errors.append("plan changed since compose")
+        if compose.get("timeline_hash") != _hash_json(timeline):
+            errors.append("timeline changed since compose")
+        output_path = (root / render.get("output_path", "")).resolve()
+        if not output_path.is_relative_to(root.resolve()) or not output_path.is_file():
+            errors.append("rendered output missing or outside evidence root")
+        else:
+            if sha256_file(output_path) != render.get("output_sha256"):
+                errors.append("rendered output changed since verification")
+        observed = render.get("observations", [])
+        required = {
+            "F1": {"opening:GENERATED_VIDEO", "body:GENERATED_IMAGE"},
+            "F2": {"opening:GENERATED_VIDEO", "body:STOCK_ONLINE", "body:GENERATED_VIDEO"},
+            "F3": {"body:GENERATED_IMAGE"},
+            "F4": {"background:STOCK_ONLINE", "inset:ORIGINAL_REUP_VIDEO"},
+            "F5": {"body:STOCK_ONLINE"},
+        }[fmt.value]
+        if not required.issubset(set(observed)):
+            errors.append("render observations do not demonstrate required visual source classes")
+        code_state = evidence.get("product_state", {})
+        if not code_state.get("files"):
+            errors.append("product code/configuration state is unbound")
+        for rel, digest in code_state.get("files", {}).items():
+            p = (root / rel).resolve()
+            if not p.is_relative_to(root.resolve()) or not p.is_file() or sha256_file(p) != digest:
+                errors.append(f"product state changed: {rel}")
+        return {"status": "PRODUCT_ACCEPTED" if not errors and result.get("valid") else "REJECTED",
+                "selected_format": fmt.value, "grammar": result, "errors": errors,
+                "bound_hashes": {"plan": _hash_json(plan), "timeline": _hash_json(timeline),
+                                 "output": render.get("output_sha256"), "assets": observed_classes,
+                                 "product_state": code_state.get("files", {})}}
+    except Exception as exc:
+        return {"status": "REJECTED", "selected_format": evidence.get("selected_format"),
+                "errors": [f"invalid acceptance evidence: {exc}"], "bound_hashes": {}}
diff --git a/videopipeline/web/server.py b/videopipeline/web/server.py
index fee38ef..d3a2e35 100644
--- a/videopipeline/web/server.py
+++ b/videopipeline/web/server.py
@@ -1517,6 +1517,7 @@ def create_app() -> web.Application:
     app.router.add_get("/api/pipeline/status", handle_get_pipeline_status)
     app.router.add_post("/api/pipeline/cancel", handle_action_cancel_pipeline)
     app.router.add_post("/api/action/run_pipeline", handle_action_run_pipeline)
+    app.router.add_post("/api/format/verify", handle_format_verify)
     app.router.add_post("/api/action/ingest", handle_action_ingest)
     app.router.add_post("/api/action/compose", handle_action_compose)
     app.router.add_post("/api/action/qa", handle_action_qa)
@@ -1528,6 +1529,18 @@ def create_app() -> web.Application:
 
     return app
 
+async def handle_format_verify(request):
+    """Run the same local RC4 acceptance verifier used by the CLI."""
+    try:
+        payload = await request.json()
+        from ..product_acceptance import verify_evidence
+        root = Path(payload.get("root", ".")).resolve()
+        result = verify_evidence(payload["evidence"], root)
+        status = 200 if result["status"] == "PRODUCT_ACCEPTED" else 422
+        return web.json_response(result, status=status)
+    except Exception as exc:
+        return web.json_response({"status": "REJECTED", "errors": [str(exc)]}, status=400)
+
 def run_web_server(host: str = "127.0.0.1", port: int = 8080):
     """Starts the synchronous web server loop."""
     STATIC_DIR.mkdir(parents=True, exist_ok=True)

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
