You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-004 Reasoning Lead Prompt - C-current / Current Thin CADS

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

Apply current Thin-CADS semantics relevant to this bounded Goal: reconstruct relevant product reality; keep Goal/journey authoritative; resolve only material design uncertainty; prefer reuse/fix over new machinery; require representative product-level evidence before READY; bind evidence to candidate; preserve consequence boundaries and canonical product truth. Use the fast path.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.


IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** Acceptance of a rendered master proves the selected canonical F1–F5 format, the media actually used, and the exact product state that produced it. CLI and Web apply the same format semantics.

**Acceptance:**

- Exercise each format through the real plan → timeline → compose → render path with local representative media. Verify the resulting output and asset lineage: F1 generated-video opening plus generated-image body; F2 generated-video opening plus intentional post-opening online stock and generated video; F3 generated images throughout; F4 readable original-video inset over visible online-stock background; F5 online-stock footage throughout. Use the current RC4 F1–F5 meanings.
- Acceptance independently checks the selected format against the actual timeline, source identities and classes, composed media, and rendered output. Metadata or a validator’s self-reported pass alone is insufficient.
- The accepted result identifies the exact candidate source state, resolved format and product settings, selected asset contents, plan/timeline/compose state, and output contents. Changing any material input, reusing a stale render, or presenting evidence from another candidate invalidates acceptance.
- CLI and Web selections produce the same canonical format decision and failure behavior. Missing, invalid, or unverifiable required media stops acceptance with a clear disposition; it never becomes a placeholder, black filler, another source class, or another format silently.

**Constraints / evidence:** Use local fixtures and local rendering only; do not call paid or external providers or the canonical production runtime. Provide candidate-bound, reproducible product-level evidence for all five positive paths and representative missing-media, illegal-source, and stale-lineage failures.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: Close the remaining acceptance gap for this candidate. The reported checks do not exercise all five formats through plan → timeline → compose → render. The existing golden tests construct timelines directly and check stream metadata, so they do not independently verify the media visible in the output. The render manifest also lacks an identifier for the candidate source tree, and its source classes are inherited from pipeline labels.

Using local fixtures and local rendering, provide reproducible evidence for F1–F5 through the real path. Independently check the selected format, asset identities and provenance, timeline, composed visuals, and rendered frames. Bind each accepted output to the exact candidate source state, resolved settings, input contents, and output hash. Demonstrate that CLI and Web reject representative missing media, illegal source classes, changed inputs, and stale renders with the same canonical format decision. Repair any behavior those checks expose; acceptance must fail when lineage or required media cannot be verified.

I completion report:
Implemented a fail closed candidate for the format and media boundaries. **This does not establish acceptance of all five rendered paths.**

- CLI and Web now resolve F1–F5 consistently, reject unsupported Web formats, and no longer silently fall back to F2. Missing required assets stop composition instead of becoming placeholder paths.
- Composed schedules record the selected format and hashes for media, narration, subtitles, and format settings. CLI render rejects missing digests, changed inputs, and format mismatches. Web rerenders the current schedule instead of reusing a master by filename.
- F4 rendering now composites the original video as an inset over a stock background. The renderer checks that both tracks cover the program.
- Updated [cli.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/videopipeline/cli.py), [server.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/videopipeline/web/server.py), [timeline_builder.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/videopipeline/stages/stage3_compose/timeline_builder.py), [nvenc_engine.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/videopipeline/stages/stage4_render/nvenc_engine.py), [format_validator.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/videopipeline/format_validator.py), and [models.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/videopipeline/models.py).

**Checks run:** `compileall` passed; the format grammar, timeline builder, and Web server tests passed (24 total); `git diff --check` passed. A local smoke check confirmed F1 schedule binding and rejection of changed media, missing images, and an illegal source class.

**Remaining acceptance gap:** I did not run plan → timeline → compose → render for all five formats with local representative media, or independently inspect those rendered outputs. Source class still comes from pipeline classification metadata; this work hashes the bytes but does not independently prove that the content’s origin matches its declared class. Treat this as a candidate for R review, not Product Acceptance.
Repair report:
Completed the repair in the disposable clone. Local F1–F5 renders pass independent frame checks; this is candidate evidence for R review, **not Product Acceptance**.

- Added a reproducible local render exercise and evidence report: [tools/xp004_local_acceptance.py](</C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/tools/xp004_local_acceptance.py>) and [xp004_local_acceptance_evidence.json](</C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/xp004_local_acceptance_evidence.json>). It records each format’s plan fingerprint, timeline assets and content hashes, rendered output hash, and pixel checks.
- Added a shared canonical format resolver for CLI, Web, and timeline building in [format_contract.py](</C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/videopipeline/format_contract.py>). The manifest binds output to a candidate source hash; the generated evidence report is excluded from that hash so recording evidence does not invalidate it.
- Fixed F1 to use available generated opening clips in 10 second intervals, retaining a single-clip fallback. This resolved the focused test failure.

**Checks run:** `python tools/xp004_local_acceptance.py` rendered all five formats locally and passed the frame checks. `python -m pytest tests/test_format_grammar.py tests/test_f4_flow_images.py -q` passed (19 tests). `compileall` and `git diff --check` passed. The evidence also records representative missing-media, illegal-source-class, changed-input, and unsupported-format failures.

**Limits:** I did not run full CLI and Web HTTP workflows against separate fixture stories; parity relies on their use of the shared format resolver and render gates. Source provenance in production still depends on pipeline classification metadata. The local fixtures verify their declared classes through fixture identity and visible output, but cannot establish external asset origin.

Candidate tree: 84063114cd17f5ecb08b907a91b71cdf97aa361a
Candidate status:
A  tools/xp004_local_acceptance.py
M  videopipeline/cli.py
A  videopipeline/format_contract.py
M  videopipeline/format_validator.py
M  videopipeline/models.py
M  videopipeline/stages/stage3_compose/motion_slideshow.py
M  videopipeline/stages/stage3_compose/timeline_builder.py
M  videopipeline/stages/stage4_render/nvenc_engine.py
M  videopipeline/web/server.py
A  xp004_local_acceptance_evidence.json
Candidate diff:
diff --git a/tools/xp004_local_acceptance.py b/tools/xp004_local_acceptance.py
new file mode 100644
index 0000000..64345a7
--- /dev/null
+++ b/tools/xp004_local_acceptance.py
@@ -0,0 +1,148 @@
+"""Local, provider-free rendered acceptance exercise for canonical formats."""
+import hashlib
+import json
+import shutil
+import subprocess
+import tempfile
+import sys
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT))
+
+
+def run(args):
+    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
+    if p.returncode:
+        raise RuntimeError(f"command failed: {args}\n{p.stderr[-2500:]}")
+    return p.stdout
+
+
+def sha(path):
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+def fixture_video(path, color, duration=1):
+    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s=320x180:r=6", "-t", str(duration), "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(path)])
+
+
+def fixture_image(path, color):
+    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s=320x180", "-frames:v", "1", str(path)])
+
+
+def sample_rgb(path, at, x, y):
+    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(at), "-i", str(path), "-vf", f"crop=1:1:{x}:{y},format=rgb24", "-frames:v", "1", "-f", "rawvideo", "-"], cwd=ROOT, capture_output=True)
+    if p.returncode or len(p.stdout) < 3:
+        raise RuntimeError(f"could not inspect rendered frame {path} at {at}s")
+    return tuple(p.stdout[:3])
+
+
+def near(rgb, color):
+    targets = {"red": (235, 20, 20), "green": (0, 128, 0), "blue": (20, 20, 235)}
+    return sum(abs(a - b) for a, b in zip(rgb, targets[color])) < 100
+
+
+def main():
+    from videopipeline.models import SourceClass, create_default_format_plan, FormatId
+    from videopipeline.stages.stage3_compose import timeline_builder as tbmod
+    from videopipeline.stages.stage4_render import nvenc_engine as engine_mod
+    from videopipeline.stages.stage4_render.nvenc_engine import NvencRenderEngine
+    from videopipeline.models import TimelineSchedule
+    from videopipeline.format_validator import FormatValidator
+
+    # Short local render profile; timelines and render entrypoint remain production code.
+    tbmod.F2_CHAPTER1_DURATION = 1.0
+    engine_mod.DEFAULT_WIDTH, engine_mod.DEFAULT_HEIGHT, engine_mod.DEFAULT_FPS = 320, 180, 6
+    engine_mod.DEFAULT_GOP = 6
+    engine_mod.NVENC_CODEC = "libx264"
+    engine_mod.NVENC_PRESET = "ultrafast"
+    engine_mod.NVENC_BITRATE = "250k"
+    engine_mod.NVENC_MAXRATE = "300k"
+    engine_mod.NVENC_AUDIO_BITRATE = "64k"
+    engine_mod.NVENC_AUDIO_SAMPLERATE = "22050"
+    report = {"profile": "local 320x180 @ 6fps, libx264; no network/provider", "formats": {}, "failures": {}}
+    with tempfile.TemporaryDirectory(prefix="xp004-accept-") as td:
+        base = Path(td)
+        audio = base / "narration.wav"
+        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=22050", "-t", "32", str(audio)])
+        ass = base / "subs.ass"
+        ass.write_text("[Script Info]\nScriptType: v4.00+\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,12,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,1,1,0,2,5,5,5,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n", encoding="utf-8")
+        # Distinctive source contents make visual source identity independently testable.
+        veo = base / "veo_clips"; stock = base / "stock"; images = base / "images"
+        for d in (veo, stock, images): d.mkdir()
+        fixture_video(veo / "open_blue.mp4", "blue")
+        fixture_video(veo / "body_green.mp4", "green")
+        fixture_video(stock / "stock_red.mp4", "red")
+        fixture_image(images / "scene_green.png", "green")
+        original = base / "original_blue.mp4"; fixture_video(original, "blue")
+
+        durations = {"F1": 4.0, "F2": 27.0, "F3": 3.0, "F4": 2.0, "F5": 2.0}
+        for fmt, duration in durations.items():
+            story = base / f"dummy_story_{fmt}"; story.mkdir()
+            work = story / "fast_pipeline"; work.mkdir()
+            plan = create_default_format_plan(FormatId(fmt))
+            kwargs = {"stock_clips": [stock / "stock_red.mp4"], "veo_clips": [veo / "open_blue.mp4", veo / "body_green.mp4"], "images": [images / "scene_green.png"], "format": fmt, "verify_media": True}
+            if fmt == "F4": kwargs["chap1_source"] = original
+            schedule = tbmod.TimelineBuilder(story, audio, duration).build_schedule(**kwargs)
+            schedule.product_state = {"format_plan_fingerprint": plan.fingerprint, "ass_sha256": sha(ass), "output_profile": {"width": 320, "height": 180, "fps": 6}}
+            FormatValidator.validate_timeline(schedule.segments, plan)
+            timeline_path = work / "video_schedule.json"
+            tbmod.TimelineBuilder(story, audio, duration).save_schedule_json(schedule, timeline_path)
+            output = base / f"{fmt}.mp4"
+            manifest = output.parent / "run_manifest.json"
+            print(f"Rendering {fmt}", flush=True)
+            metrics = NvencRenderEngine(work).render_master_video(schedule, ass, output, format=fmt, format_plan=plan)
+            m = json.loads(manifest.read_text(encoding="utf-8"))
+            if m["output_sha256"] != sha(output) or m["product_state"]["output_sha256"] != sha(output):
+                raise AssertionError(f"{fmt} manifest output hash mismatch")
+            if not m["product_state"].get("candidate_source_sha256"):
+                raise AssertionError("candidate source tree fingerprint absent")
+            if fmt == "F1": checks = {"opening_blue": near(sample_rgb(output, .5, 160, 90), "blue"), "body_green": near(sample_rgb(output, 2.5, 160, 90), "green")}
+            elif fmt == "F2": checks = {"opening_blue": near(sample_rgb(output, .5, 20, 20), "blue"), "stock_red": near(sample_rgb(output, 5, 20, 20), "red"), "body_green": near(sample_rgb(output, 26, 20, 20), "green")}
+            elif fmt == "F3": checks = {"generated_image_green": near(sample_rgb(output, 1.5, 20, 20), "green")}
+            elif fmt == "F4": checks = {"foreground_blue": near(sample_rgb(output, 1, 160, 90), "blue"), "visible_stock_red_edge": near(sample_rgb(output, 1, 20, 20), "red")}
+            else: checks = {"stock_red": near(sample_rgb(output, 1, 160, 90), "red")}
+            if not all(checks.values()): raise AssertionError(f"{fmt} rendered pixel checks failed: {checks}; samples={[sample_rgb(output, t, x, y) for t in (.5, 3, 26) for x,y in ((160,90),(280,150),(20,20))]}")
+            report["formats"][fmt] = {"duration_sec": metrics.duration_sec, "timeline_segments": len(schedule.segments), "format": fmt, "format_plan_fingerprint": plan.fingerprint, "selected_settings": schedule.product_state, "timeline": [{"index": s.index, "start": s.start_time, "duration": s.duration, "type": s.segment_type, "class": s.source_class.value, "path": str(s.source_path.resolve()), "sha256": sha(s.source_path)} for s in schedule.segments], "assets": [{"class": s.source_class.value, "path": str(s.source_path), "sha256": sha(s.source_path)} for s in schedule.segments], "output_sha256": sha(output), "candidate_source_sha256": m["product_state"]["candidate_source_sha256"], "frame_checks": checks}
+
+        # Representative negative acceptance checks against the same format resolver/validator/render gate.
+        try:
+            tbmod.TimelineBuilder(base / "missing", audio, 2).build_schedule(format="F1", verify_media=True)
+            raise AssertionError("missing F1 opening unexpectedly composed")
+        except FileNotFoundError as ex: report["failures"]["missing_media"] = str(ex)
+        try:
+            from videopipeline.models import VisualSegment
+            invalid = TimelineSchedule(base / "illegal", audio, 2, [VisualSegment(0, 0, 2, "stock", stock / "stock_red.mp4", source_class=SourceClass.STOCK_ONLINE)])
+            FormatValidator.validate_timeline(invalid.segments, create_default_format_plan(FormatId.F3))
+            raise AssertionError("illegal F3 source unexpectedly accepted")
+        except ValueError as ex: report["failures"]["illegal_source_class"] = str(ex)
+        try:
+            # A composed schedule cannot render after any selected source bytes change.
+            tampered = base / "changed.mp4"; fixture_video(tampered, "yellow")
+            s = TimelineSchedule(base / "stale", audio, 1, [])
+            s.format_id = "F5"; s.source_sha256s = {str(tampered.resolve()): "0" * 64}; s.audio_sha256 = sha(audio)
+            s.product_state = {"format_plan_fingerprint": create_default_format_plan(FormatId.F5).fingerprint, "ass_sha256": sha(ass)}
+            from videopipeline.models import VisualSegment
+            s.segments = [VisualSegment(0, 0, 1, "stock", tampered, source_class=SourceClass.STOCK_ONLINE)]
+            NvencRenderEngine(base / "stale_work").render_master_video(s, ass, base / "stale.mp4", format="F5", format_plan=create_default_format_plan(FormatId.F5))
+            raise AssertionError("stale source unexpectedly rendered")
+        except ValueError as ex: report["failures"]["changed_input_stale_lineage"] = str(ex)
+        from videopipeline.format_contract import resolve_format_id
+        from videopipeline.models import FormatId
+        try:
+            resolve_format_id("invalid")
+            raise AssertionError("unsupported format unexpectedly resolved")
+        except ValueError as ex:
+            report["failures"]["canonical_format_rejection"] = str(ex)
+        if resolve_format_id(" f2-l ") != FormatId.F2 or resolve_format_id("F5") != FormatId.F5:
+            raise AssertionError("shared canonical format resolution mismatch")
+        final_candidate_hash = __import__("videopipeline.models", fromlist=["candidate_source_fingerprint"]).candidate_source_fingerprint(ROOT)
+        if any(v["candidate_source_sha256"] != final_candidate_hash for v in report["formats"].values()):
+            raise AssertionError("candidate source changed during rendered evidence run")
+        report["candidate_source_sha256"] = final_candidate_hash
+        report_path = ROOT / "xp004_local_acceptance_evidence.json"
+        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
+        print(json.dumps(report, indent=2))
+
+
+if __name__ == "__main__": main()
diff --git a/videopipeline/cli.py b/videopipeline/cli.py
index b51124e..e39300e 100644
--- a/videopipeline/cli.py
+++ b/videopipeline/cli.py
@@ -21,6 +21,8 @@ from .stages.stage3_compose.timeline_builder import TimelineBuilder
 from .stages.stage3_compose.ass_karaoke import generate_karaoke_ass
 from .stages.stage4_render.nvenc_engine import NvencRenderEngine
 from .stages.stage4_render.qa_verifier import QAVerifier
+from .models import SourceClass
+from .format_contract import resolve_format_id
 
 def resolve_story_assets(story_dir: Path):
     """Finds audio and srt files inside the story folder."""
@@ -88,6 +90,8 @@ def cmd_compose(args):
     stock_mgr = StockManager(get_story_stock_dirs(story_dir))
     veo_client = GoogleFlowVeoClient()
     veo_clips = veo_client.get_existing_veo_clips(story_dir / "veo_clips")
+    image_dir = story_dir / "images"
+    body_images = sorted(p for p in image_dir.glob("scene_*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}) if image_dir.exists() else []
     chap1_candidate = story_dir / "Final_Video_Export" / "Phase1_Prototype_3M.mp4"
 
     fmt_str = getattr(args, "format", "f2").upper()
@@ -98,20 +102,32 @@ def cmd_compose(args):
     from .stages.stage3_compose.editorial_qc import EditorialQC
     import json
 
-    fmt_id = FormatId(fmt_str) if hasattr(FormatId, fmt_str) else FormatId.F2
+    fmt_id = resolve_format_id(fmt_str)
+    fmt_str = fmt_id.value
     format_plan = create_default_format_plan(fmt_id)
     run_req = RunRequest(story_dir=story_dir, format_id=fmt_id, format_plan=format_plan)
 
     tb = TimelineBuilder(story_dir, audio_path, total_dur)
     sched = tb.build_schedule(
-        chap1_source=chap1_candidate if chap1_candidate.exists() else None,
+        chap1_source=chap1_candidate if fmt_id == FormatId.F2 and chap1_candidate.exists() else None,
         stock_clips=stock_mgr.get_stock_pool(),
         veo_clips=veo_clips,
-        format=fmt_str.lower()
+        format=fmt_str.lower(),
+        images=body_images,
+        verify_media=True
     )
 
     # Format Grammar Validation
     FormatValidator.validate_timeline(sched.segments, format_plan)
+    sched.product_state = {
+        "format_plan_fingerprint": format_plan.fingerprint,
+        "effect_profile": vars(format_plan.effect_profile),
+        "layout_profile": vars(format_plan.layout_profile) if format_plan.layout_profile else None,
+        "output_profile": {"width": 1920, "height": 1080, "fps": 30},
+        "srt_path": str(srt_path.resolve()),
+        "srt_sha256": __import__("hashlib").sha256(srt_path.read_bytes()).hexdigest(),
+        "ass_sha256": __import__("hashlib").sha256(ass_path.read_bytes()).hexdigest(),
+    }
 
     # Stage 3 Editorial QC Gate
     qc_res = EditorialQC.evaluate_timeline(sched.segments, total_dur, format_plan)
@@ -164,16 +180,53 @@ def cmd_render(args):
             duration=s["duration"],
             segment_type=s["type"],
             source_path=Path(s["source"]),
-            description=s.get("description", "")
+            description=s.get("description", ""),
+            source_class=SourceClass(s["source_class"]) if s.get("source_class") else None,
+            asset_id=s.get("asset_id", "")
         )
         for s in data["segments"]
     ]
+    for item, segment in zip(data.get("segments", []), segments):
+        expected = item.get("source_sha256")
+        if not expected:
+            raise ValueError(f"Unverifiable timeline lineage: segment {segment.index} has no media digest")
+        actual = __import__("hashlib").sha256(segment.source_path.read_bytes()).hexdigest()
+        if actual != expected:
+            raise ValueError(f"Stale timeline lineage: source media changed for segment {segment.index}")
+    expected_audio_hash = data.get("audio_sha256")
+    if not expected_audio_hash:
+        raise ValueError("Unverifiable timeline lineage: narration audio digest is missing")
+    actual_audio_hash = __import__("hashlib").sha256(Path(data["audio_path"]).read_bytes()).hexdigest()
+    if actual_audio_hash != expected_audio_hash:
+        raise ValueError("Stale timeline lineage: narration audio changed since compose")
+    product_state = data.get("product_state", {})
+    if not product_state.get("srt_sha256") or not product_state.get("srt_path"):
+        raise ValueError("Unverifiable timeline lineage: subtitle/script digest is missing")
+    srt_path = Path(product_state["srt_path"])
+    if not srt_path.is_file() or __import__("hashlib").sha256(srt_path.read_bytes()).hexdigest() != product_state["srt_sha256"]:
+        raise ValueError("Stale timeline lineage: subtitle/script input changed since compose")
+    if not product_state.get("ass_sha256") or __import__("hashlib").sha256(ass_path.read_bytes()).hexdigest() != product_state["ass_sha256"]:
+        raise ValueError("Stale timeline lineage: composed subtitle/settings changed since compose")
     schedule = TimelineSchedule(
         story_dir=Path(data["story_dir"]),
         audio_path=Path(data["audio_path"]),
         total_duration=data["total_duration"],
         segments=segments
     )
+    from .models import FormatId, create_default_format_plan
+    requested = resolve_format_id(getattr(args, "format", "f2")).value
+    bound = data.get("format_id")
+    if not bound or bound != requested:
+        raise ValueError(f"Selected format {requested} does not match composed timeline format {bound}")
+    format_plan = create_default_format_plan(FormatId(requested))
+    schedule.format_id = bound
+    schedule.format_plan_fingerprint = data.get("format_plan_fingerprint", "")
+    schedule.source_sha256s = {str(seg.source_path.resolve()): item["source_sha256"] for item, seg in zip(data["segments"], segments)}
+    schedule.audio_sha256 = expected_audio_hash
+    if not product_state.get("format_plan_fingerprint") or product_state["format_plan_fingerprint"] != format_plan.fingerprint:
+        raise ValueError("Stale timeline lineage: resolved format settings changed since compose")
+    from .format_validator import FormatValidator
+    FormatValidator.validate_timeline(segments, format_plan)
 
     qc_verdict = data.get("editorial_qc_verdict", "PASS")
     owner_disp = data.get("owner_disposition", "AUTO")
@@ -193,7 +246,7 @@ def cmd_render(args):
     print(f"[Render] Starting NVENC Render Engine...")
     print(f"[Render] Target Output: {out_file}")
     engine = NvencRenderEngine(work_dir)
-    metrics = engine.render_master_video(schedule, ass_path, out_file, format=getattr(args, "format", "f2"))
+    metrics = engine.render_master_video(schedule, ass_path, out_file, format=requested, format_plan=format_plan)
     print(f"[Render] COMPLETE!")
     print(f"  Duration: {metrics.duration_sec:.2f}s")
     print(f"  File Size: {metrics.file_size_bytes:,} bytes")
diff --git a/videopipeline/format_contract.py b/videopipeline/format_contract.py
new file mode 100644
index 0000000..2d48427
--- /dev/null
+++ b/videopipeline/format_contract.py
@@ -0,0 +1,12 @@
+"""Shared canonical format decision for CLI and Web entry points."""
+from .models import FormatId
+
+
+def resolve_format_id(value):
+    raw = str(value or "").strip().upper()
+    if raw == "F2-L":
+        raw = "F2"
+    try:
+        return FormatId(raw)
+    except ValueError as exc:
+        raise ValueError(f"Unsupported format {raw!r}; expected F1-F5 (or legacy F2-L)") from exc
diff --git a/videopipeline/format_validator.py b/videopipeline/format_validator.py
index 9d5241b..a9a37bd 100644
--- a/videopipeline/format_validator.py
+++ b/videopipeline/format_validator.py
@@ -31,8 +31,13 @@ class FormatValidator:
 
         # Normalize segment source class mapping
         for seg in segments:
+            inferred = FormatValidator._infer_source_class(seg)
             if not seg.source_class:
-                seg.source_class = FormatValidator._infer_source_class(seg)
+                seg.source_class = inferred
+            elif seg.source_class != inferred:
+                raise FORMAT_GRAMMAR_VIOLATION(
+                    f"Source class {seg.source_class.value} conflicts with segment source role {seg.segment_type!r} at segment {seg.index}"
+                )
 
         if fmt == FormatId.F1:
             return FormatValidator._validate_f1(segments, format_plan)
@@ -58,7 +63,9 @@ class FormatValidator:
             return SourceClass.STOCK_ONLINE
         elif t in ("f1_framed", "reup", "original_source"):
             return SourceClass.ORIGINAL_REUP_VIDEO
-        return SourceClass.STOCK_ONLINE
+        raise FORMAT_GRAMMAR_VIOLATION(
+            f"Cannot verify source class for segment {seg.index} ({seg.segment_type})"
+        )
 
     @staticmethod
     def _validate_f1(segments: List[VisualSegment], plan: FormatPlan) -> Dict[str, Any]:
@@ -172,10 +179,12 @@ class FormatValidator:
                 f"F4 LayoutProfile geometry invalid: foreground_scale={layout.foreground_scale}. Must be between 0.1 and 0.95."
             )
 
-        has_original = any(seg.source_class == SourceClass.ORIGINAL_REUP_VIDEO for seg in segments)
-        if not has_original:
+        original_segments = [seg for seg in segments if seg.source_class == SourceClass.ORIGINAL_REUP_VIDEO]
+        stock_segments = [seg for seg in segments if seg.source_class == SourceClass.STOCK_ONLINE]
+        if not original_segments:
             raise FORMAT_GRAMMAR_VIOLATION("F4 Reup requires an ORIGINAL_REUP_VIDEO source file.")
-
+        if not stock_segments:
+            raise FORMAT_GRAMMAR_VIOLATION("F4 Reup requires visible STOCK_ONLINE background footage.")
         return {"valid": True, "format": "F4", "layout_id": layout.layout_id}
 
     @staticmethod
diff --git a/videopipeline/models.py b/videopipeline/models.py
index 989a603..74bfb21 100644
--- a/videopipeline/models.py
+++ b/videopipeline/models.py
@@ -5,12 +5,29 @@ specified in AUTOVIDEO_CREATIVE_PRODUCTION_SPEC_RC4 and AUTOVIDEO_PIPELINE_SPEC_
 """
 import hashlib
 import json
+import subprocess
 from dataclasses import dataclass, field, asdict
 from enum import Enum
 from pathlib import Path
 from typing import List, Optional, Dict, Any
 
 
+def candidate_source_fingerprint(root: Path) -> str:
+    """Hash exact candidate source contents, including local tracked edits."""
+    root = Path(root).resolve()
+    result = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=root, check=True, capture_output=True)
+    digest = hashlib.sha256()
+    for raw in sorted(item for item in result.stdout.split(b"\0") if item):
+        # The generated evidence report is an output of the run, not candidate source.
+        if raw.replace(b"\\", b"/").endswith(b"/xp004_local_acceptance_evidence.json") or raw == b"xp004_local_acceptance_evidence.json":
+            continue
+        path = root / Path(raw.decode("utf-8", errors="surrogateescape"))
+        if path.is_file():
+            digest.update(raw + b"\0")
+            digest.update(hashlib.sha256(path.read_bytes()).digest())
+    return digest.hexdigest()
+
+
 # ── Canonical Source Classes & Format IDs ──────────────────────────────────────
 
 class SourceClass(str, Enum):
@@ -348,12 +365,22 @@ class VisualSegment:
         return self.start_time + self.duration
 
     def to_dict(self) -> Dict[str, Any]:
+        digest = ""
+        try:
+            h = hashlib.sha256()
+            with open(self.source_path, "rb") as media:
+                for block in iter(lambda: media.read(1024 * 1024), b""):
+                    h.update(block)
+            digest = h.hexdigest()
+        except OSError:
+            pass
         return {
             "index": self.index,
             "start": round(self.start_time, 2),
             "duration": round(self.duration, 2),
             "type": self.segment_type,
             "source": str(self.source_path),
+            "source_sha256": digest,
             "description": self.description,
             "is_loop": self.is_loop,
             "speed_factor": self.speed_factor,
@@ -373,11 +400,20 @@ class TimelineSchedule:
     segments: List[VisualSegment] = field(default_factory=list)
 
     def to_dict(self) -> Dict[str, Any]:
+        audio_hash = ""
+        try:
+            audio_hash = hashlib.sha256(self.audio_path.read_bytes()).hexdigest()
+        except OSError:
+            pass
         return {
             "story_dir": str(self.story_dir),
             "audio_path": str(self.audio_path),
+            "audio_sha256": audio_hash,
             "total_duration": round(self.total_duration, 2),
             "segment_count": len(self.segments),
+            "format_id": getattr(self, "format_id", ""),
+            "format_plan_fingerprint": getattr(self, "format_plan_fingerprint", ""),
+            "product_state": getattr(self, "product_state", {}),
             "segments": [s.to_dict() for s in self.segments]
         }
 
@@ -485,6 +521,7 @@ class RunManifest:
     output_file: str = ""
     output_sha256: str = ""
     assets_used: List[Dict[str, Any]] = field(default_factory=list)
+    product_state: Dict[str, Any] = field(default_factory=dict)
     redacted: bool = True
 
     def to_dict(self) -> Dict[str, Any]:
diff --git a/videopipeline/stages/stage3_compose/motion_slideshow.py b/videopipeline/stages/stage3_compose/motion_slideshow.py
index a57a4b8..d8b3e9a 100644
--- a/videopipeline/stages/stage3_compose/motion_slideshow.py
+++ b/videopipeline/stages/stage3_compose/motion_slideshow.py
@@ -82,29 +82,35 @@ class CinematicMotionEngine:
 
     def create_radio_hud_overlay(self, output_png: Path) -> Path:
         """Generates vintage radio tuner glass banner overlay (PNG with alpha)."""
-        box_x1, box_y1 = self.width - 540, 32
-        box_x2, box_y2 = self.width - 32, 160
+        scale = min(self.width / 1920.0, self.height / 1080.0)
+        margin = max(4, int(32 * scale))
+        box_width = max(48, int(540 * scale))
+        box_height = max(24, int(128 * scale))
+        box_x1, box_y1 = self.width - margin - box_width, margin
+        box_x2, box_y2 = self.width - margin, margin + box_height
+        unit = min(box_width / 540.0, box_height / 128.0)
+        font_scale = max(0.22, 0.48 * unit)
 
         overlay = np.zeros((self.height, self.width, 4), dtype=np.uint8)
 
         # Dark glass panel with rounded aesthetic
         cv2.rectangle(overlay, (box_x1, box_y1), (box_x2, box_y2), (14, 16, 20, 215), -1)
-        cv2.rectangle(overlay, (box_x1, box_y1), (box_x2, box_y2), (255, 230, 0, 180), 2)
+        cv2.rectangle(overlay, (box_x1, box_y1), (box_x2, box_y2), (255, 230, 0, 180), max(1, int(2 * unit)))
 
         # Header
-        cv2.putText(overlay, "VINTAGE RADIO FM", (box_x1 + 18, box_y1 + 24), cv2.FONT_HERSHEY_DUPLEX, 0.48, (0, 230, 255, 255), 1, cv2.LINE_AA)
-        cv2.putText(overlay, "● ON AIR  |  STEREO", (box_x1 + 330, box_y1 + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 136, 240), 1, cv2.LINE_AA)
+        cv2.putText(overlay, "VINTAGE RADIO FM", (box_x1 + int(18 * unit), box_y1 + int(24 * unit)), cv2.FONT_HERSHEY_DUPLEX, font_scale, (0, 230, 255, 255), max(1, int(unit)), cv2.LINE_AA)
+        cv2.putText(overlay, "ON AIR | STEREO", (box_x1 + int(330 * unit), box_y1 + int(24 * unit)), cv2.FONT_HERSHEY_SIMPLEX, max(0.18, 0.38 * unit), (0, 255, 136, 240), max(1, int(unit)), cv2.LINE_AA)
 
         # Tuning dial scale
-        scale_y = box_y1 + 42
-        cv2.line(overlay, (box_x1 + 18, scale_y), (box_x2 - 18, scale_y), (120, 130, 140, 180), 1)
-        for x_tick in range(box_x1 + 20, box_x2 - 18, 18):
-            cv2.line(overlay, (x_tick, scale_y - 4), (x_tick, scale_y + 4), (160, 170, 180, 180), 1)
+        scale_y = box_y1 + int(42 * unit)
+        cv2.line(overlay, (box_x1 + int(18 * unit), scale_y), (box_x2 - int(18 * unit), scale_y), (120, 130, 140, 180), 1)
+        for x_tick in range(box_x1 + int(20 * unit), box_x2 - int(18 * unit), max(1, int(18 * unit))):
+            cv2.line(overlay, (x_tick, scale_y - max(1, int(4 * unit))), (x_tick, scale_y + max(1, int(4 * unit))), (160, 170, 180, 180), 1)
         
         # Red needle
-        needle_x = box_x1 + 240
-        cv2.line(overlay, (needle_x, scale_y - 7), (needle_x, scale_y + 7), (0, 0, 255, 255), 2)
-        cv2.putText(overlay, "98.5 MHz", (needle_x - 22, scale_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 230, 255, 240), 1, cv2.LINE_AA)
+        needle_x = box_x1 + int(240 * unit)
+        cv2.line(overlay, (needle_x, scale_y - max(1, int(7 * unit))), (needle_x, scale_y + max(1, int(7 * unit))), (0, 0, 255, 255), max(1, int(2 * unit)))
+        cv2.putText(overlay, "98.5 MHz", (needle_x - int(22 * unit), scale_y - max(2, int(10 * unit))), cv2.FONT_HERSHEY_SIMPLEX, max(0.18, 0.35 * unit), (0, 230, 255, 240), max(1, int(unit)), cv2.LINE_AA)
 
         output_png.parent.mkdir(parents=True, exist_ok=True)
         is_success, buffer = cv2.imencode(".png", overlay)
diff --git a/videopipeline/stages/stage3_compose/timeline_builder.py b/videopipeline/stages/stage3_compose/timeline_builder.py
index 6918171..bc8d068 100644
--- a/videopipeline/stages/stage3_compose/timeline_builder.py
+++ b/videopipeline/stages/stage3_compose/timeline_builder.py
@@ -43,7 +43,8 @@ class TimelineBuilder:
         images: Optional[List[Path]] = None,
         body_scenes: Optional[List[Dict[str, Any]]] = None,
         creative_plan: Optional[CreativePlan] = None,
-        validate: bool = True
+        validate: bool = True,
+        verify_media: bool = False
     ) -> TimelineSchedule:
         """
         Assembles all segments into a complete timeline matching total_duration.
@@ -57,13 +58,8 @@ class TimelineBuilder:
             format_plan = format
             fmt_id = format_plan.format_id
         else:
-            fmt_str = str(format).upper()
-            if fmt_str in ("F1", "F2", "F3", "F4", "F5"):
-                fmt_id = FormatId(fmt_str)
-            elif fmt_str == "F2-L":
-                fmt_id = FormatId.F2
-            else:
-                fmt_id = FormatId.F2
+            from ...format_contract import resolve_format_id
+            fmt_id = resolve_format_id(format)
             format_plan = create_default_format_plan(fmt_id)
 
         # ── Filter out globally-used clips ──
@@ -102,35 +98,29 @@ class TimelineBuilder:
         # ── 1. CANONICAL FORMAT F1: AI OPENING + AI IMAGES ──
         if fmt_id == FormatId.F1:
             opening_dur = min(self.total_duration, F2_CHAPTER1_DURATION)
-            if len(veo_sorted) > 1:
-                clip_dur = opening_dur / len(veo_sorted)
-                for i, v_clip in enumerate(veo_sorted):
-                    segments.append(VisualSegment(
-                        index=seg_idx,
-                        start_time=current_time,
-                        duration=clip_dur,
-                        segment_type="veo_opening",
-                        source_path=v_clip,
-                        description=f"F1 Opening Shot {i+1} ({clip_dur:.1f}s)",
-                        source_class=SourceClass.GENERATED_VIDEO,
-                        asset_id=v_clip.stem
-                    ))
-                    current_time += clip_dur
-                    seg_idx += 1
+            if chap1_source is not None:
+                opening_sources = [Path(chap1_source)]
             else:
-                open_src = chap1_source or (veo_queue.popleft() if veo_queue else Path("placeholder_opening_ai.mp4"))
+                opening_count = min(len(veo_queue), max(1, int((opening_dur + 9.999) // 10.0)))
+                opening_sources = [veo_queue.popleft() for _ in range(opening_count)]
+            if not opening_sources:
+                raise FileNotFoundError("F1 requires a generated-video opening asset")
+            opening_cursor = 0.0
+            for opening_index, open_src in enumerate(opening_sources):
+                dur = min(10.0, opening_dur - opening_cursor) if opening_index < len(opening_sources) - 1 else opening_dur - opening_cursor
                 segments.append(VisualSegment(
                     index=seg_idx,
-                    start_time=0.0,
-                    duration=opening_dur,
-                    segment_type="veo_opening" if "veo" in str(open_src).lower() else "chap1_opening",
+                    start_time=opening_cursor,
+                    duration=dur,
+                    segment_type="veo_opening",
                     source_path=open_src,
                     description="F1 AI Opening Video",
                     source_class=SourceClass.GENERATED_VIDEO,
                     asset_id=Path(open_src).stem
                 ))
-                current_time += opening_dur
+                opening_cursor += dur
                 seg_idx += 1
+            current_time += opening_dur
 
             img_cursor = 0
             if body_scenes:
@@ -139,7 +129,9 @@ class TimelineBuilder:
                     dur = min(s_dur, max(0.0, self.total_duration - current_time))
                     if dur <= 0:
                         break
-                    img_src = avail_images[img_cursor % len(avail_images)] if avail_images else Path("placeholder_scene.jpg")
+                    if not avail_images:
+                        raise FileNotFoundError("F1 requires generated-image body assets")
+                    img_src = avail_images[img_cursor % len(avail_images)]
                     img_cursor += 1
                     segments.append(VisualSegment(
                         index=seg_idx,
@@ -157,7 +149,9 @@ class TimelineBuilder:
                 while current_time < self.total_duration:
                     rem = self.total_duration - current_time
                     dur = min(rem, 45.0)
-                    img_src = avail_images[img_cursor % len(avail_images)] if avail_images else Path("placeholder_scene.jpg")
+                    if not avail_images:
+                        raise FileNotFoundError("F1 requires generated-image body assets")
+                    img_src = avail_images[img_cursor % len(avail_images)]
                     img_cursor += 1
                     segments.append(VisualSegment(
                         index=seg_idx,
@@ -178,7 +172,9 @@ class TimelineBuilder:
             while current_time < self.total_duration:
                 rem = self.total_duration - current_time
                 dur = min(rem, 45.0)
-                img_src = avail_images[img_cursor % len(avail_images)] if avail_images else Path("placeholder_scene.jpg")
+                if not avail_images:
+                    raise FileNotFoundError("F3 requires generated-image assets")
+                img_src = avail_images[img_cursor % len(avail_images)]
                 img_cursor += 1
                 segments.append(VisualSegment(
                     index=seg_idx,
@@ -196,12 +192,14 @@ class TimelineBuilder:
         # ── 3. CANONICAL FORMAT F4: REUP (ORIGINAL INSET + BACKGROUND STOCK) ──
         elif fmt_id == FormatId.F4:
             src_video = chap1_source
-            if not src_video or not Path(src_video).exists():
+            if not src_video:
                 candidates = list(self.story_dir.glob("source_video.mp4")) + \
                              list(self.story_dir.glob("full_video.mp4")) + \
                              list(self.story_dir.glob("reup_video.mp4")) + \
                              list(self.story_dir.glob("*.mp4"))
-                src_video = candidates[0] if candidates else Path("source_video.mp4")
+                src_video = candidates[0] if candidates else None
+            if src_video is None:
+                raise FileNotFoundError("F4 requires an original source video")
 
             # Inset foreground segment
             segments.append(VisualSegment(
@@ -215,7 +213,9 @@ class TimelineBuilder:
                 asset_id=Path(src_video).stem
             ))
             # Background stock interval
-            bg_stock = stock_queue.popleft() if stock_queue else Path("placeholder_bg_stock.mp4")
+            if not stock_queue:
+                raise FileNotFoundError("F4 requires online-stock background footage")
+            bg_stock = stock_queue.popleft()
             segments.append(VisualSegment(
                 index=1,
                 start_time=0.0,
@@ -237,7 +237,7 @@ class TimelineBuilder:
                     st_src = stock_queue.popleft()
                     newly_used.append(st_src)
                 else:
-                    st_src = Path(f"stock_clip_{stock_cursor+1}.mp4")
+                    raise FileNotFoundError("F5 requires online-stock footage for full coverage")
 
                 stock_cursor += 1
                 segments.append(VisualSegment(
@@ -257,7 +257,9 @@ class TimelineBuilder:
         else:
             # AI Opening (~60s)
             opening_dur = min(self.total_duration, F2_CHAPTER1_DURATION)
-            open_src = chap1_source or (veo_queue.popleft() if veo_queue else Path("placeholder_opening_ai.mp4"))
+            open_src = chap1_source or (veo_queue.popleft() if veo_queue else None)
+            if open_src is None:
+                raise FileNotFoundError(f"{fmt_id.value} requires a generated-video opening asset")
             segments.append(VisualSegment(
                 index=seg_idx,
                 start_time=0.0,
@@ -283,11 +285,15 @@ class TimelineBuilder:
                     target_cls = sh.visual_requirement.preferred_source_class if sh.visual_requirement else SourceClass.STOCK_ONLINE
 
                     if target_cls == SourceClass.STOCK_ONLINE:
-                        src = stock_queue.popleft() if stock_queue else Path(f"stock_{seg_idx}.mp4")
+                        if not stock_queue:
+                            raise FileNotFoundError("F2 requires post-opening online-stock footage")
+                        src = stock_queue.popleft()
                         seg_type = "stock"
                         newly_used.append(src)
                     else:
-                        src = veo_queue.popleft() if veo_queue else Path(f"veo_ai_{seg_idx}.mp4")
+                        if not veo_queue:
+                            raise FileNotFoundError("F2 requires post-opening generated-video footage")
+                        src = veo_queue.popleft()
                         seg_type = "veo_ai"
 
                     segments.append(VisualSegment(
@@ -313,12 +319,16 @@ class TimelineBuilder:
 
                     # Ensure at least 1 stock and at least 1 veo post-opening
                     if slot % 2 == 0:
-                        src = stock_queue.popleft() if stock_queue else Path(f"stock_{seg_idx}.mp4")
+                        if not stock_queue:
+                            raise FileNotFoundError("F2 requires post-opening online-stock footage")
+                        src = stock_queue.popleft()
                         seg_type = "stock"
                         cls = SourceClass.STOCK_ONLINE
                         newly_used.append(src)
                     else:
-                        src = veo_queue.popleft() if veo_queue else Path(f"veo_ai_{seg_idx}.mp4")
+                        if not veo_queue:
+                            raise FileNotFoundError("F2 requires post-opening generated-video footage")
+                        src = veo_queue.popleft()
                         seg_type = "veo_ai"
                         cls = SourceClass.GENERATED_VIDEO
 
@@ -350,9 +360,24 @@ class TimelineBuilder:
             total_duration=self.total_duration,
             segments=segments
         )
+        schedule.format_id = fmt_id.value
+        schedule.format_plan_fingerprint = format_plan.fingerprint
+        if verify_media:
+            import hashlib
+            if not self.audio_path.is_file() or self.audio_path.stat().st_size == 0:
+                raise FileNotFoundError(f"Required narration audio missing or empty: {self.audio_path}")
+            schedule.source_sha256s = {
+                str(s.source_path.resolve()): hashlib.sha256(s.source_path.read_bytes()).hexdigest()
+                for s in segments
+            }
+            schedule.audio_sha256 = hashlib.sha256(self.audio_path.read_bytes()).hexdigest()
 
         # Validate grammar
         if validate:
+            if verify_media:
+                missing = [str(s.source_path) for s in segments if not s.source_path.is_file() or s.source_path.stat().st_size == 0]
+                if missing:
+                    raise FileNotFoundError("Required timeline media missing or empty: " + ", ".join(missing))
             FormatValidator.validate_timeline(segments, format_plan)
 
         return schedule
diff --git a/videopipeline/stages/stage4_render/nvenc_engine.py b/videopipeline/stages/stage4_render/nvenc_engine.py
index 7ba70df..439fb67 100644
--- a/videopipeline/stages/stage4_render/nvenc_engine.py
+++ b/videopipeline/stages/stage4_render/nvenc_engine.py
@@ -173,7 +173,11 @@ class NvencRenderEngine:
         """
         normalized_paths: List[Path] = []
         for seg in schedule.segments:
-            out_file = self.segments_dir / f"seg_{seg.index:03d}_{seg.segment_type}.mp4"
+            source_key = hashlib.sha256()
+            with open(seg.source_path, "rb") as source_file:
+                for block in iter(lambda: source_file.read(1024 * 1024), b""):
+                    source_key.update(block)
+            out_file = self.segments_dir / f"seg_{seg.index:03d}_{seg.segment_type}_{source_key.hexdigest()[:12]}.mp4"
             is_opening = (seg.index < 6)
             needs_render = force or (is_opening and force_opening) or (not out_file.exists()) or (out_file.stat().st_size < 10000)
             if not needs_render and out_file.exists():
@@ -217,6 +221,37 @@ class NvencRenderEngine:
         Supports rich atmospheric HUD for story formats (F4, F3, F2, F2-L) and clean stream composition for F1.
         """
         start_time = time.time()
+        from ...models import FormatId, create_default_format_plan, candidate_source_fingerprint
+        from ...format_validator import FormatValidator
+        canonical_format = str(format).upper()
+        if canonical_format == "F2-L":
+            canonical_format = "F2"
+        plan = format_plan or create_default_format_plan(FormatId(canonical_format))
+        if getattr(schedule, "format_id", canonical_format) != canonical_format:
+            raise ValueError("Selected format does not match the composed timeline")
+        FormatValidator.validate_timeline(schedule.segments, plan)
+        for segment in schedule.segments:
+            if not segment.source_path.is_file() or segment.source_path.stat().st_size == 0:
+                raise FileNotFoundError(f"Required media missing or empty at segment {segment.index}: {segment.source_path}")
+            expected = getattr(schedule, "source_sha256s", {}).get(str(segment.source_path.resolve()))
+            if not expected:
+                raise ValueError(f"Unverifiable timeline lineage: source digest missing for segment {segment.index}")
+            if hashlib.sha256(segment.source_path.read_bytes()).hexdigest() != expected:
+                raise ValueError(f"Stale timeline lineage: source media changed for segment {segment.index}")
+        expected_audio = getattr(schedule, "audio_sha256", "")
+        if not expected_audio:
+            raise ValueError("Unverifiable timeline lineage: narration audio digest missing")
+        if hashlib.sha256(Path(schedule.audio_path).read_bytes()).hexdigest() != expected_audio:
+            raise ValueError("Stale timeline lineage: narration audio changed since compose")
+        if not ass_path or not Path(ass_path).is_file() or not Path(ass_path).stat().st_size:
+            raise FileNotFoundError("Required composed subtitle/settings file is missing or empty")
+        product_state = getattr(schedule, "product_state", {})
+        ass_digest = product_state.get("ass_sha256")
+        if not ass_digest or hashlib.sha256(Path(ass_path).read_bytes()).hexdigest() != ass_digest:
+            raise ValueError("Unverifiable or stale timeline lineage: composed subtitle/settings digest mismatch")
+        plan_fingerprint = product_state.get("format_plan_fingerprint")
+        if not plan_fingerprint or plan_fingerprint != plan.fingerprint:
+            raise ValueError("Unverifiable or stale timeline lineage: resolved format settings mismatch")
         output_path.parent.mkdir(parents=True, exist_ok=True)
         master_audio = audio_path or schedule.audio_path
         if not master_audio or not Path(master_audio).exists():
@@ -229,7 +264,40 @@ class NvencRenderEngine:
                     break
 
         # 1. Normalize all segments
-        seg_paths = self.normalize_all_segments(schedule)
+        fmt_key = format.upper() if isinstance(format, str) else str(format)
+        if fmt_key == "F4":
+            if len(schedule.segments) != 2:
+                raise ValueError("F4 render requires exactly one original-video inset and one stock background track")
+            original = next((s for s in schedule.segments if str(getattr(s.source_class, "value", s.source_class)) == "ORIGINAL_REUP_VIDEO"), None)
+            background = next((s for s in schedule.segments if str(getattr(s.source_class, "value", s.source_class)) == "STOCK_ONLINE"), None)
+            if not original or not background:
+                raise ValueError("F4 render requires verified original-video and online-stock sources")
+            program_end = max(s.end_time for s in schedule.segments)
+            for label, track in (("original inset", original), ("stock background", background)):
+                if track.start_time > 0.01 or track.end_time < program_end - 0.01:
+                    raise ValueError(f"F4 {label} must cover the full rendered program")
+            if not original.source_path.is_file() or not background.source_path.is_file():
+                raise FileNotFoundError("F4 source media is missing")
+            layout = layout_profile or (format_plan.layout_profile if format_plan else None) or LayoutProfile()
+            scale = max(0.1, min(0.95, float(layout.foreground_scale)))
+            width = int(DEFAULT_WIDTH * scale) // 2 * 2
+            height = int(DEFAULT_HEIGHT * scale) // 2 * 2
+            f4_visual = self.work_dir / "f4_composed_visual.mp4"
+            f4_cmd = [
+                "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(background.source_path),
+                "-stream_loop", "-1", "-i", str(original.source_path), "-t", str(schedule.total_duration),
+                "-filter_complex",
+                f"[0:v]scale={DEFAULT_WIDTH}:{DEFAULT_HEIGHT}:force_original_aspect_ratio=increase,crop={DEFAULT_WIDTH}:{DEFAULT_HEIGHT},gblur=sigma={max(0, layout.background_blur)}[bg];"
+                f"[1:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2[fg];"
+                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]",
+                "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(f4_visual)
+            ]
+            proc = subprocess.run(f4_cmd, capture_output=True, text=True)
+            if proc.returncode or not f4_visual.is_file() or f4_visual.stat().st_size < 1000:
+                raise RuntimeError(f"F4 inset composition failed: {proc.stderr[-500:]}")
+            seg_paths = [f4_visual]
+        else:
+            seg_paths = self.normalize_all_segments(schedule)
 
         # 2. Write concat file
         concat_file = self.work_dir / "concat_segments.txt"
@@ -275,7 +343,7 @@ class NvencRenderEngine:
                 fc_ass = f"[v_wave]ass='{escaped_ass}'[v_final]" if has_ass else "[v_wave]null[v_final]"
                 filter_complex = (
                     "[0:v]format=gbrp[base];"
-                    "[2:v]scale=1920:1080,format=gbrp[snow];"
+                    f"[2:v]scale={DEFAULT_WIDTH}:{DEFAULT_HEIGHT},format=gbrp[snow];"
                     "[base][snow]blend=all_mode='screen':all_opacity=0.75,format=yuv420p[v_snow];"
                     "[1:a]asplit=2[a_main][a_wave];"
                     "[a_wave]showwaves=s=460x65:mode=line:colors=0x00E6FF@0.95:scale=cbrt,format=yuva420p[wave];"
@@ -338,7 +406,7 @@ class NvencRenderEngine:
             process_manager.unregister_render_process()
 
         if not output_path.exists() or output_path.stat().st_size < 10000:
-            raise RuntimeError(f"Master render failed (code {proc.returncode}): {stderr[-500:]}")
+            raise RuntimeError(f"Master render failed (code {proc.returncode}): {stderr[-2500:]}")
 
         elapsed = time.time() - start_time
         file_size = output_path.stat().st_size
@@ -364,15 +432,16 @@ class NvencRenderEngine:
                 "index": s.index,
                 "type": s.segment_type,
                 "source_path": str(s.source_path),
+                "source_sha256": hashlib.sha256(Path(s.source_path).read_bytes()).hexdigest(),
                 "source_class": s_class_str,
                 "asset_id": getattr(s, "asset_id", "") or Path(s.source_path).stem,
                 "duration": s.duration
             })
 
         from ...models import RunManifest
-        fmt_val = format.upper() if isinstance(format, str) else (format.value if hasattr(format, "value") else str(format))
+        fmt_val = canonical_format
         story_name = schedule.story_dir.name if hasattr(schedule, "story_dir") and schedule.story_dir else "story"
-        fp_fp = getattr(format_plan, "format_plan_fingerprint", "") if format_plan else ""
+        fp_fp = getattr(format_plan, "fingerprint", "") if format_plan else ""
         manifest = RunManifest(
             run_id=f"run_{output_path.stem}",
             timestamp=datetime.utcnow().isoformat(),
@@ -386,7 +455,21 @@ class NvencRenderEngine:
             owner_disposition=getattr(schedule, "owner_disposition", "AUTO"),
             output_file=str(output_path),
             output_sha256=out_sha256,
-            assets_used=assets_used
+            assets_used=assets_used,
+            product_state={
+                "format_plan_fingerprint": fp_fp,
+                "selected_format": fmt_val,
+                "resolved_schedule_format": getattr(schedule, "format_id", fmt_val),
+                "selected_settings": getattr(schedule, "product_state", {}),
+                "timeline": [dict(item) for item in assets_used],
+                "total_duration": schedule.total_duration,
+                "audio_path": str(schedule.audio_path),
+                "audio_sha256": hashlib.sha256(Path(schedule.audio_path).read_bytes()).hexdigest(),
+                "candidate_source_sha256": candidate_source_fingerprint(Path(__file__).resolve().parents[3]),
+                "ass_path": str(Path(ass_path).resolve()),
+                "ass_sha256": hashlib.sha256(Path(ass_path).read_bytes()).hexdigest(),
+                "output_sha256": out_sha256,
+            }
         )
 
         manifest_path = output_path.parent / "run_manifest.json"
diff --git a/videopipeline/web/server.py b/videopipeline/web/server.py
index fee38ef..8f5f898 100644
--- a/videopipeline/web/server.py
+++ b/videopipeline/web/server.py
@@ -327,6 +327,12 @@ async def handle_action_compose(request):
     story_dir = Path(data.get("story_dir", ""))
     fmt_choice = data.get("format", "f2") # f2, f2-l, f3, f1
 
+    from ..format_contract import resolve_format_id
+    try:
+        fmt_choice = resolve_format_id(fmt_choice).value.lower()
+    except ValueError as exc:
+        return web.json_response({"status": "error", "message": str(exc)}, status=400)
+
     if not story_dir.exists():
         return web.json_response({"status": "error", "message": "Story not found"}, status=404)
 
@@ -371,13 +377,26 @@ async def handle_action_compose(request):
     tb = TimelineBuilder(story_dir, audios[0], total_dur)
     chap1_src = story_dir / "Final_Video_Export" / "Phase1_Prototype_3M.mp4"
     sched = tb.build_schedule(
-        chap1_source=chap1_src if chap1_src.exists() else None,
+        chap1_source=chap1_src if fmt_choice == "f2" and chap1_src.exists() else None,
         stock_clips=stock_mgr.get_stock_pool(),
         veo_clips=veo_clips,
         format=fmt_choice,
         images=body_images,
-        body_scenes=body_scenes
+        body_scenes=body_scenes,
+        verify_media=True
     )
+    from ..models import FormatId, create_default_format_plan
+    resolved_plan = create_default_format_plan(FormatId(fmt_choice.upper()))
+    sched.product_state = {
+        "format_plan_fingerprint": resolved_plan.fingerprint,
+        "effect_profile": vars(resolved_plan.effect_profile),
+        "layout_profile": vars(resolved_plan.layout_profile) if resolved_plan.layout_profile else None,
+        "output_profile": {"width": 1920, "height": 1080, "fps": 30},
+        "srt_path": str(srts[0].resolve()),
+        "srt_sha256": __import__("hashlib").sha256(srts[0].read_bytes()).hexdigest(),
+        "ass_sha256": __import__("hashlib").sha256(ass_path.read_bytes()).hexdigest(),
+    }
+    sched.format_plan_fingerprint = resolved_plan.fingerprint
 
     sched_path = work_dir / "video_schedule.json"
     tb.save_schedule_json(sched, sched_path)
@@ -406,6 +425,8 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
     """Asynchronously orchestrates all 4 pipeline stages from start to finish."""
     global PIPELINE_STATE
     try:
+        from ..format_contract import resolve_format_id
+        fmt_choice = resolve_format_id(fmt_choice).value.lower()
         log_event(f"============================================================")
         log_event(f"🚀 KÍCH HOẠT PIPELINE TOÀN DIỆN CHO: {story_dir.name}")
         log_event(f"   Format: {fmt_choice.upper()} | NVENC: {options.get('use_nvenc', True)} | QA: {options.get('auto_qa', True)}")
@@ -586,12 +607,13 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
         tb = TimelineBuilder(story_dir, chosen_audio, total_dur)
         chap1_src = story_dir / "Final_Video_Export" / "Phase1_Prototype_3M.mp4"
         sched = tb.build_schedule(
-            chap1_source=chap1_src if chap1_src.exists() else None,
+            chap1_source=chap1_src if fmt_choice == "f2" and chap1_src.exists() else None,
             stock_clips=stock_mgr.get_stock_pool(),
             veo_clips=veo_clips,
             format=fmt_choice,
             images=body_images,
-            body_scenes=body_scenes
+            body_scenes=body_scenes,
+            verify_media=True
         )
         sched_path = work_dir / "video_schedule.json"
         tb.save_schedule_json(sched, sched_path)
@@ -603,6 +625,16 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
 
         format_id_enum = FormatId(fmt_choice.upper()) if hasattr(FormatId, fmt_choice.upper()) else FormatId.F2
         format_plan = create_default_format_plan(format_id_enum)
+        sched.product_state = {
+            "format_plan_fingerprint": format_plan.fingerprint,
+            "effect_profile": vars(format_plan.effect_profile),
+            "layout_profile": vars(format_plan.layout_profile) if format_plan.layout_profile else None,
+            "output_profile": {"width": 1920, "height": 1080, "fps": 30},
+            "srt_path": str(chosen_srt.resolve()),
+            "srt_sha256": __import__("hashlib").sha256(chosen_srt.read_bytes()).hexdigest(),
+            "ass_sha256": __import__("hashlib").sha256(ass_path.read_bytes()).hexdigest(),
+        }
+        tb.save_schedule_json(sched, sched_path)
         run_req = RunRequest(story_dir=story_dir, format_id=format_id_enum, format_plan=format_plan, options=options)
 
         # Format Grammar Validation
@@ -658,10 +690,12 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
             except Exception:
                 pass
 
-        if (not master_file.exists() or force_rerender) and not dry_run:
+        if not dry_run:
             log_event(f"[Stage 4 Render] Bắt đầu render video master qua NVIDIA NVENC...")
             engine = NvencRenderEngine(work_dir)
-            engine.render(sched, ass_path, master_file, format=fmt_choice)
+            format_id_enum = FormatId(fmt_choice.upper())
+            bound_plan = create_default_format_plan(format_id_enum)
+            engine.render_master_video(sched, ass_path, master_file, format=fmt_choice, format_plan=bound_plan, layout_profile=bound_plan.layout_profile)
             log_event(f"[Stage 4 Render] Render hoàn tất: {master_file.name} ({master_file.stat().st_size / (1024**3):.2f} GB).")
         else:
             log_event(f"[Stage 4 Render] Master video sẵn sàng: {master_file.name} ({master_file.stat().st_size / (1024**3):.2f} GB).")
@@ -1039,12 +1073,13 @@ async def handle_get_schedule_segments(request):
             tb = TimelineBuilder(story_dir, audios[0], total_dur)
             chap1_src = story_dir / "Final_Video_Export" / "Phase1_Prototype_3M.mp4"
             sched = tb.build_schedule(
-                chap1_source=chap1_src if chap1_src.exists() else None,
+                chap1_source=chap1_src if fmt_choice == "f2" and chap1_src.exists() else None,
                 stock_clips=stock_mgr.get_stock_pool(),
                 veo_clips=veo_clips,
                 format=fmt_choice,
                 images=body_images,
-                body_scenes=body_scenes
+                body_scenes=body_scenes,
+                verify_media=True
             )
             sched_file.parent.mkdir(parents=True, exist_ok=True)
             tb.save_schedule_json(sched, sched_file)
diff --git a/xp004_local_acceptance_evidence.json b/xp004_local_acceptance_evidence.json
new file mode 100644
index 0000000..599cede
--- /dev/null
+++ b/xp004_local_acceptance_evidence.json
@@ -0,0 +1,262 @@
+{
+  "profile": "local 320x180 @ 6fps, libx264; no network/provider",
+  "formats": {
+    "F1": {
+      "duration_sec": 4.0,
+      "timeline_segments": 2,
+      "format": "F1",
+      "format_plan_fingerprint": "4064f69ecd253e81",
+      "selected_settings": {
+        "format_plan_fingerprint": "4064f69ecd253e81",
+        "ass_sha256": "a97ca0f208ce1625b80680ec1cc41cb1130ec0ce0af3609410fe253d90d8f04b",
+        "output_profile": {
+          "width": 320,
+          "height": 180,
+          "fps": 6
+        }
+      },
+      "timeline": [
+        {
+          "index": 0,
+          "start": 0.0,
+          "duration": 1.0,
+          "type": "veo_opening",
+          "class": "GENERATED_VIDEO",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\veo_clips\\open_blue.mp4",
+          "sha256": "acaf1c95a0758098349e93007ca9f51abc11eb4e45db88c5864720c31b6bccf5"
+        },
+        {
+          "index": 1,
+          "start": 1.0,
+          "duration": 3.0,
+          "type": "slideshow",
+          "class": "GENERATED_IMAGE",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\images\\scene_green.png",
+          "sha256": "8ff4b7d755aea5a54e97a2e391ae7dcb57661ed26aec828880096d851be8a4cb"
+        }
+      ],
+      "assets": [
+        {
+          "class": "GENERATED_VIDEO",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\veo_clips\\open_blue.mp4",
+          "sha256": "acaf1c95a0758098349e93007ca9f51abc11eb4e45db88c5864720c31b6bccf5"
+        },
+        {
+          "class": "GENERATED_IMAGE",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\images\\scene_green.png",
+          "sha256": "8ff4b7d755aea5a54e97a2e391ae7dcb57661ed26aec828880096d851be8a4cb"
+        }
+      ],
+      "output_sha256": "2501681a903a8b47f94c49c4a05f9b31e90841aa1d295c5e125d64caabb2a466",
+      "candidate_source_sha256": "48857171329ee6189a4076c49232a02ab29d675b1954b4779689b21b2ae18104",
+      "frame_checks": {
+        "opening_blue": true,
+        "body_green": true
+      }
+    },
+    "F2": {
+      "duration_sec": 27.0,
+      "timeline_segments": 3,
+      "format": "F2",
+      "format_plan_fingerprint": "91666eedab216989",
+      "selected_settings": {
+        "format_plan_fingerprint": "91666eedab216989",
+        "ass_sha256": "a97ca0f208ce1625b80680ec1cc41cb1130ec0ce0af3609410fe253d90d8f04b",
+        "output_profile": {
+          "width": 320,
+          "height": 180,
+          "fps": 6
+        }
+      },
+      "timeline": [
+        {
+          "index": 0,
+          "start": 0.0,
+          "duration": 1.0,
+          "type": "chap1_opening",
+          "class": "GENERATED_VIDEO",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\veo_clips\\open_blue.mp4",
+          "sha256": "acaf1c95a0758098349e93007ca9f51abc11eb4e45db88c5864720c31b6bccf5"
+        },
+        {
+          "index": 1,
+          "start": 1.0,
+          "duration": 25.0,
+          "type": "stock",
+          "class": "STOCK_ONLINE",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\stock\\stock_red.mp4",
+          "sha256": "2151bda142d4ff46c27984981aa5845cb7701c9d9c294e5b487bbf9bf79e49cf"
+        },
+        {
+          "index": 2,
+          "start": 26.0,
+          "duration": 1.0,
+          "type": "veo_ai",
+          "class": "GENERATED_VIDEO",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\veo_clips\\body_green.mp4",
+          "sha256": "09f02c2d6d669d2a456008e06fc6e61ee507c14355c8af9120555c2af10158d8"
+        }
+      ],
+      "assets": [
+        {
+          "class": "GENERATED_VIDEO",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\veo_clips\\open_blue.mp4",
+          "sha256": "acaf1c95a0758098349e93007ca9f51abc11eb4e45db88c5864720c31b6bccf5"
+        },
+        {
+          "class": "STOCK_ONLINE",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\stock\\stock_red.mp4",
+          "sha256": "2151bda142d4ff46c27984981aa5845cb7701c9d9c294e5b487bbf9bf79e49cf"
+        },
+        {
+          "class": "GENERATED_VIDEO",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\veo_clips\\body_green.mp4",
+          "sha256": "09f02c2d6d669d2a456008e06fc6e61ee507c14355c8af9120555c2af10158d8"
+        }
+      ],
+      "output_sha256": "dd0a908b05f27e4acc13ac28d7fc803e76005396f68aa7e741a068f0a3cdc8e3",
+      "candidate_source_sha256": "48857171329ee6189a4076c49232a02ab29d675b1954b4779689b21b2ae18104",
+      "frame_checks": {
+        "opening_blue": true,
+        "stock_red": true,
+        "body_green": true
+      }
+    },
+    "F3": {
+      "duration_sec": 3.0,
+      "timeline_segments": 1,
+      "format": "F3",
+      "format_plan_fingerprint": "4eecd4dcf65ef7b8",
+      "selected_settings": {
+        "format_plan_fingerprint": "4eecd4dcf65ef7b8",
+        "ass_sha256": "a97ca0f208ce1625b80680ec1cc41cb1130ec0ce0af3609410fe253d90d8f04b",
+        "output_profile": {
+          "width": 320,
+          "height": 180,
+          "fps": 6
+        }
+      },
+      "timeline": [
+        {
+          "index": 0,
+          "start": 0.0,
+          "duration": 3.0,
+          "type": "slideshow",
+          "class": "GENERATED_IMAGE",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\images\\scene_green.png",
+          "sha256": "8ff4b7d755aea5a54e97a2e391ae7dcb57661ed26aec828880096d851be8a4cb"
+        }
+      ],
+      "assets": [
+        {
+          "class": "GENERATED_IMAGE",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\images\\scene_green.png",
+          "sha256": "8ff4b7d755aea5a54e97a2e391ae7dcb57661ed26aec828880096d851be8a4cb"
+        }
+      ],
+      "output_sha256": "4706d5970d2ecf18d4df9d9a565bf3a5d8466de874ec6f32745f1d6c6cbed452",
+      "candidate_source_sha256": "48857171329ee6189a4076c49232a02ab29d675b1954b4779689b21b2ae18104",
+      "frame_checks": {
+        "generated_image_green": true
+      }
+    },
+    "F4": {
+      "duration_sec": 2.0,
+      "timeline_segments": 2,
+      "format": "F4",
+      "format_plan_fingerprint": "e4de3699c6b531b9",
+      "selected_settings": {
+        "format_plan_fingerprint": "e4de3699c6b531b9",
+        "ass_sha256": "a97ca0f208ce1625b80680ec1cc41cb1130ec0ce0af3609410fe253d90d8f04b",
+        "output_profile": {
+          "width": 320,
+          "height": 180,
+          "fps": 6
+        }
+      },
+      "timeline": [
+        {
+          "index": 0,
+          "start": 0.0,
+          "duration": 2.0,
+          "type": "f1_framed",
+          "class": "ORIGINAL_REUP_VIDEO",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\original_blue.mp4",
+          "sha256": "acaf1c95a0758098349e93007ca9f51abc11eb4e45db88c5864720c31b6bccf5"
+        },
+        {
+          "index": 1,
+          "start": 0.0,
+          "duration": 2.0,
+          "type": "stock",
+          "class": "STOCK_ONLINE",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\stock\\stock_red.mp4",
+          "sha256": "2151bda142d4ff46c27984981aa5845cb7701c9d9c294e5b487bbf9bf79e49cf"
+        }
+      ],
+      "assets": [
+        {
+          "class": "ORIGINAL_REUP_VIDEO",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\original_blue.mp4",
+          "sha256": "acaf1c95a0758098349e93007ca9f51abc11eb4e45db88c5864720c31b6bccf5"
+        },
+        {
+          "class": "STOCK_ONLINE",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\stock\\stock_red.mp4",
+          "sha256": "2151bda142d4ff46c27984981aa5845cb7701c9d9c294e5b487bbf9bf79e49cf"
+        }
+      ],
+      "output_sha256": "6006889e388b57f77c68b3a52c21d2d6fe7afbe191119ecab239d651eff19183",
+      "candidate_source_sha256": "48857171329ee6189a4076c49232a02ab29d675b1954b4779689b21b2ae18104",
+      "frame_checks": {
+        "foreground_blue": true,
+        "visible_stock_red_edge": true
+      }
+    },
+    "F5": {
+      "duration_sec": 2.0,
+      "timeline_segments": 1,
+      "format": "F5",
+      "format_plan_fingerprint": "273c474f19839507",
+      "selected_settings": {
+        "format_plan_fingerprint": "273c474f19839507",
+        "ass_sha256": "a97ca0f208ce1625b80680ec1cc41cb1130ec0ce0af3609410fe253d90d8f04b",
+        "output_profile": {
+          "width": 320,
+          "height": 180,
+          "fps": 6
+        }
+      },
+      "timeline": [
+        {
+          "index": 0,
+          "start": 0.0,
+          "duration": 2.0,
+          "type": "stock",
+          "class": "STOCK_ONLINE",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\stock\\stock_red.mp4",
+          "sha256": "2151bda142d4ff46c27984981aa5845cb7701c9d9c294e5b487bbf9bf79e49cf"
+        }
+      ],
+      "assets": [
+        {
+          "class": "STOCK_ONLINE",
+          "path": "C:\\Users\\ADMIN\\AppData\\Local\\Temp\\xp004-accept-f040afop\\stock\\stock_red.mp4",
+          "sha256": "2151bda142d4ff46c27984981aa5845cb7701c9d9c294e5b487bbf9bf79e49cf"
+        }
+      ],
+      "output_sha256": "8375ab0bbdeb45c17348c6d9f584c0f3cfa2e6b24273cc2152f8c63d7811ba26",
+      "candidate_source_sha256": "48857171329ee6189a4076c49232a02ab29d675b1954b4779689b21b2ae18104",
+      "frame_checks": {
+        "stock_red": true
+      }
+    }
+  },
+  "failures": {
+    "missing_media": "F1 requires a generated-video opening asset",
+    "illegal_source_class": "F3 requires 100% GENERATED_IMAGE. Found forbidden STOCK_ONLINE at segment 0",
+    "changed_input_stale_lineage": "Stale timeline lineage: source media changed for segment 0",
+    "canonical_format_rejection": "Unsupported format 'INVALID'; expected F1-F5 (or legacy F2-L)"
+  },
+  "candidate_source_sha256": "48857171329ee6189a4076c49232a02ab29d675b1954b4779689b21b2ae18104"
+}
\ No newline at end of file

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
