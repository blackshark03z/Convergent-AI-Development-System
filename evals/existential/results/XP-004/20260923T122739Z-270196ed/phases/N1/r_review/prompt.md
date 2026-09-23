You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-004 Reasoning Lead Prompt - N1 / Existing-minimal stack

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

Use ordinary product/developer documentation, existing tests and normal engineering conventions available in the neutral repository. Do not create a custom process/framework.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.


IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** Acceptance for each selected canonical format F1–F5 proves that its legal sources pass through the product’s plan, timeline, compose, and render path into the final master. CLI and Web use the same format meaning.

**Acceptance:**

- Use local, distinguishable media fixtures through the real product path for all five formats. Independently inspect the resulting master to verify: F1 generated video opening and generated image body; F2 generated video opening plus both online stock and generated video after the opening; F3 generated images throughout; F4 original video visibly inset over an online video background; F5 online stock throughout. A source-class label or valid stream metadata alone is insufficient evidence.
- Acceptance identifies the selected format, actual source assets and their content identities, the verified plan/timeline/compose state, the executable product revision or equivalent product-state identity, and the final output digest. Rechecking after a source, selection, plan, render setting, product revision, or output changes must detect stale evidence.
- Verify CLI and Web select and report the same canonical format semantics. A missing, misclassified, or unverified required source; an illegal substitution; or a rendered output that disagrees with the verified state cannot receive final acceptance. Report a truthful failure or owner-needed state. An explicit format change must produce new verification and lineage.

**Constraints:** Use the RC4 canonical F1–F5 definitions where older format documentation conflicts. Verification must run without paid or external providers or the canonical production runtime.

OWNER_INPUT_REQUIRED: no

I completion report:
Implemented the candidate changes in:

- [format_semantics.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T122739Z-270196ed/arms/N1/videopipeline/format_semantics.py) and [format_evidence.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T122739Z-270196ed/arms/N1/videopipeline/format_evidence.py): shared F1–F5 meanings and format normalization; required-source checks; render evidence containing source hashes, plan/timeline state, code identity, render settings, and output digest. Rechecking detects changed state or output. Evidence stays `NEEDS_VISUAL_REVIEW` until independent frame review is recorded.
- [timeline_builder.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T122739Z-270196ed/arms/N1/videopipeline/stages/stage3_compose/timeline_builder.py), [nvenc_engine.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T122739Z-270196ed/arms/N1/videopipeline/stages/stage4_render/nvenc_engine.py), [models.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T122739Z-270196ed/arms/N1/videopipeline/models.py), and [format_validator.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T122739Z-270196ed/arms/N1/videopipeline/format_validator.py): F4 now pairs its online stock background with the original video inset during rendering, and render rejects missing sources or unverified source classes.
- [cli.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T122739Z-270196ed/arms/N1/videopipeline/cli.py) and [server.py](C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T122739Z-270196ed/arms/N1/videopipeline/web/server.py): CLI and Web use shared format semantics; compose reports the selected format and fails truthfully when required sources are missing.

Checks run: `compileall` passed; 24 format grammar, timeline builder, and Web server tests passed; `git diff --check` reported no whitespace errors. A local evidence check confirmed changed source content is detected as stale.

**This does not establish Product Acceptance.** I did not run all five formats through rendering with distinguishable fixtures or independently inspect their master frames. The evidence mechanism records lineage and digest, but it cannot prove from source labels or hashes alone that the footage visibly has the required content. No paid or external providers or canonical production runtime were used.

Candidate tree: f9d72e9879e08de9b629178800825c89b24d84f2
Candidate status:
M  videopipeline/cli.py
A  videopipeline/format_evidence.py
A  videopipeline/format_semantics.py
M  videopipeline/format_validator.py
M  videopipeline/models.py
M  videopipeline/stages/stage3_compose/timeline_builder.py
M  videopipeline/stages/stage4_render/nvenc_engine.py
M  videopipeline/web/server.py
Candidate diff:
diff --git a/videopipeline/cli.py b/videopipeline/cli.py
index b51124e..9bc415a 100644
--- a/videopipeline/cli.py
+++ b/videopipeline/cli.py
@@ -98,18 +98,24 @@ def cmd_compose(args):
     from .stages.stage3_compose.editorial_qc import EditorialQC
     import json
 
-    fmt_id = FormatId(fmt_str) if hasattr(FormatId, fmt_str) else FormatId.F2
+    from .format_semantics import normalize_format
+    fmt_id = normalize_format(fmt_str)
+    from .format_semantics import FORMAT_SEMANTICS
+    print(f"[Compose] Selected {fmt_id.value}: {FORMAT_SEMANTICS[fmt_id]}")
     format_plan = create_default_format_plan(fmt_id)
     run_req = RunRequest(story_dir=story_dir, format_id=fmt_id, format_plan=format_plan)
 
     tb = TimelineBuilder(story_dir, audio_path, total_dur)
     sched = tb.build_schedule(
-        chap1_source=chap1_candidate if chap1_candidate.exists() else None,
+        chap1_source=chap1_candidate if chap1_candidate.exists() and fmt_id != FormatId.F4 else None,
         stock_clips=stock_mgr.get_stock_pool(),
         veo_clips=veo_clips,
         format=fmt_str.lower()
     )
 
+    from .format_evidence import validate_bound_sources
+    validate_bound_sources(sched)
+
     # Format Grammar Validation
     FormatValidator.validate_timeline(sched.segments, format_plan)
 
@@ -154,7 +160,7 @@ def cmd_render(args):
 
     # Load schedule
     import json
-    from .models import TimelineSchedule, VisualSegment
+    from .models import TimelineSchedule, VisualSegment, SourceClass
     with open(sched_path, "r", encoding="utf-8") as f:
         data = json.load(f)
     segments = [
@@ -164,7 +170,10 @@ def cmd_render(args):
             duration=s["duration"],
             segment_type=s["type"],
             source_path=Path(s["source"]),
-            description=s.get("description", "")
+            description=s.get("description", ""),
+            source_class=SourceClass(s["source_class"]) if s.get("source_class") else None,
+            asset_id=s.get("asset_id", ""),
+            background_source_path=Path(s["background_source"]) if s.get("background_source") else None
         )
         for s in data["segments"]
     ]
@@ -193,7 +202,8 @@ def cmd_render(args):
     print(f"[Render] Starting NVENC Render Engine...")
     print(f"[Render] Target Output: {out_file}")
     engine = NvencRenderEngine(work_dir)
-    metrics = engine.render_master_video(schedule, ass_path, out_file, format=getattr(args, "format", "f2"))
+    from .format_semantics import normalize_format
+    metrics = engine.render_master_video(schedule, ass_path, out_file, format=normalize_format(getattr(args, "format", "f2")).value)
     print(f"[Render] COMPLETE!")
     print(f"  Duration: {metrics.duration_sec:.2f}s")
     print(f"  File Size: {metrics.file_size_bytes:,} bytes")
@@ -201,6 +211,7 @@ def cmd_render(args):
     print(f"  Average FPS: {metrics.average_encoding_fps:.1f} FPS")
 
 def cmd_qa(args):
+    import json
     story_dir = Path(args.story_dir)
     out_dir = story_dir / "Final_Video_Export"
     video_file = out_dir / (args.output_name or "Full_Master_Video_26M.mp4")
@@ -217,6 +228,29 @@ def cmd_qa(args):
     print(f"  Video Codec: {meta.get('video_codec')}")
     print(f"  Audio Codec: {meta.get('audio_codec')}")
 
+    from .format_evidence import recheck_render_evidence
+    from .models import TimelineSchedule, VisualSegment, SourceClass
+    schedule_file = story_dir / "fast_pipeline" / "video_schedule.json"
+    evidence_file = out_dir / "format_evidence.json"
+    if schedule_file.is_file():
+        data = json.loads(schedule_file.read_text(encoding="utf-8"))
+        schedule = TimelineSchedule(
+            story_dir=Path(data["story_dir"]), audio_path=Path(data["audio_path"]),
+            total_duration=data["total_duration"],
+            segments=[VisualSegment(
+                index=s["index"], start_time=s["start"], duration=s["duration"],
+                segment_type=s["type"], source_path=Path(s["source"]),
+                description=s.get("description", ""),
+                source_class=SourceClass(s["source_class"]) if s.get("source_class") else None,
+                asset_id=s.get("asset_id", ""),
+                background_source_path=Path(s["background_source"]) if s.get("background_source") else None,
+            ) for s in data["segments"]]
+        )
+        result = recheck_render_evidence(schedule, args.format, evidence_file)
+        print(f"  Format evidence: {result['status']} — {result['reason']}")
+    else:
+        print("  Format evidence: NEEDS_OWNER — composed schedule is missing.")
+
     previews_dir = out_dir / "previews_v2"
     timestamps = [
         ("00:01:30", "qa_01_chap1.jpg"),
diff --git a/videopipeline/format_evidence.py b/videopipeline/format_evidence.py
new file mode 100644
index 0000000..75592d5
--- /dev/null
+++ b/videopipeline/format_evidence.py
@@ -0,0 +1,110 @@
+"""Reproducible local lineage evidence for canonical format renders."""
+import hashlib
+import json
+from pathlib import Path
+from typing import Any
+
+from .format_semantics import normalize_format, FORMAT_SEMANTICS
+from .models import TimelineSchedule, create_default_format_plan
+
+
+def _sha256(path: Path) -> str:
+    h = hashlib.sha256()
+    with path.open("rb") as stream:
+        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
+            h.update(chunk)
+    return h.hexdigest()
+
+
+def product_revision() -> str:
+    """Content identity of executable pipeline Python sources, including local edits."""
+    root = Path(__file__).resolve().parent
+    h = hashlib.sha256()
+    source_files = (p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".py", ".js", ".html", ".css"})
+    for path in sorted(source_files):
+        h.update(path.relative_to(root).as_posix().encode())
+        h.update(bytes.fromhex(_sha256(path)))
+    return h.hexdigest()
+
+
+def _state(schedule: TimelineSchedule, format_id: str) -> dict[str, Any]:
+    fmt = normalize_format(format_id)
+    plan = create_default_format_plan(fmt)
+    assets = []
+    paths = []
+    for seg in schedule.segments:
+        entries = [(seg.source_path, seg.source_class.value if seg.source_class else "UNVERIFIED")]
+        if seg.background_source_path:
+            entries.append((seg.background_source_path, "STOCK_ONLINE_BACKGROUND"))
+        for path, source_class in entries:
+            if path not in paths:
+                paths.append(path)
+            assets.append({"segment": seg.index, "path": str(path.resolve()), "source_class": source_class,
+                           "sha256": _sha256(path) if path.is_file() else None})
+    return {
+        "format": fmt.value,
+        "format_semantics": FORMAT_SEMANTICS[fmt],
+        "format_plan": {"fingerprint": plan.fingerprint, "source_policy": plan.source_policy,
+                        "layout": vars(plan.layout_profile) if plan.layout_profile else None,
+                        "effects": vars(plan.effect_profile)},
+        "timeline": schedule.to_dict(),
+        "assets": assets,
+        "render_settings": {"width": 1920, "height": 1080, "fps": 30,
+                            "video_codec": "h264_nvenc_with_cpu_fallback", "format": fmt.value},
+        "product_revision": product_revision(),
+    }
+
+
+def validate_bound_sources(schedule: TimelineSchedule) -> None:
+    """Reject missing media before a compose state can be called usable."""
+    missing = []
+    for seg in schedule.segments:
+        if not seg.source_class:
+            missing.append(f"segment {seg.index}: source class is unverified")
+        if not seg.source_path.is_file():
+            missing.append(f"segment {seg.index} ({seg.source_class.value if seg.source_class else 'UNKNOWN'}): {seg.source_path}")
+        if seg.background_source_path and not seg.background_source_path.is_file():
+            missing.append(f"segment {seg.index} background: {seg.background_source_path}")
+    # F4 keeps background and inset as distinct timeline entries.
+    from .models import SourceClass
+    if any(s.source_class == SourceClass.ORIGINAL_REUP_VIDEO for s in schedule.segments) and not any(
+        s.source_class == SourceClass.STOCK_ONLINE for s in schedule.segments
+    ):
+        missing.append("F4 requires an online stock background video")
+    if missing:
+        raise FileNotFoundError("Required format source unavailable or unverified: " + "; ".join(missing))
+
+
+def write_render_evidence(schedule: TimelineSchedule, format_id: str, output: Path) -> Path:
+    state = _state(schedule, format_id)
+    state_digest = hashlib.sha256(json.dumps(state, sort_keys=True, default=str).encode()).hexdigest()
+    evidence = {
+        "status": "NEEDS_VISUAL_REVIEW",
+        "format": state["format"],
+        "format_semantics": state["format_semantics"],
+        "state_sha256": state_digest,
+        "state": state,
+        "output": str(output.resolve()),
+        "output_sha256": _sha256(output),
+        "visual_review": {"status": "NOT_PERFORMED", "reason": "Independent inspection of sampled master frames is required."},
+    }
+    target = output.parent / "format_evidence.json"
+    target.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
+    return target
+
+
+def recheck_render_evidence(schedule: TimelineSchedule, selected_format: str, evidence_path: Path) -> dict[str, Any]:
+    if not evidence_path.is_file():
+        return {"valid": False, "status": "NEEDS_OWNER", "reason": "Render evidence is missing."}
+    old = json.loads(evidence_path.read_text(encoding="utf-8"))
+    fmt = normalize_format(selected_format).value
+    output = Path(old.get("output", ""))
+    expected_state = _state(schedule, fmt)
+    expected_digest = hashlib.sha256(json.dumps(expected_state, sort_keys=True, default=str).encode()).hexdigest()
+    if old.get("state_sha256") != expected_digest:
+        return {"valid": False, "status": "STALE", "reason": "Format, source, timeline, plan, render settings, or product revision changed."}
+    if not output.is_file() or _sha256(output) != old.get("output_sha256"):
+        return {"valid": False, "status": "STALE", "reason": "Final output is missing or its digest changed."}
+    return {"valid": old.get("visual_review", {}).get("status") == "PASSED",
+            "status": old.get("status", "NEEDS_VISUAL_REVIEW"),
+            "reason": "Independent visual review has not been recorded."}
diff --git a/videopipeline/format_semantics.py b/videopipeline/format_semantics.py
new file mode 100644
index 0000000..a619b29
--- /dev/null
+++ b/videopipeline/format_semantics.py
@@ -0,0 +1,21 @@
+"""Shared canonical format selection used by CLI, Web, planning and rendering."""
+from .models import FormatId
+
+
+FORMAT_SEMANTICS = {
+    FormatId.F1: "Generated video opening followed by generated images",
+    FormatId.F2: "Generated video opening followed by online stock and generated video",
+    FormatId.F3: "Generated images throughout",
+    FormatId.F4: "Online video background with original video visibly inset",
+    FormatId.F5: "Online stock video throughout",
+}
+
+
+def normalize_format(value: str | FormatId) -> FormatId:
+    raw = value.value if isinstance(value, FormatId) else str(value).strip().upper()
+    if raw == "F2-L":
+        raw = "F2"
+    try:
+        return FormatId(raw)
+    except ValueError as exc:
+        raise ValueError(f"Unknown canonical format {value!r}; choose F1, F2, F3, F4, or F5") from exc
diff --git a/videopipeline/format_validator.py b/videopipeline/format_validator.py
index 9d5241b..6dee4c3 100644
--- a/videopipeline/format_validator.py
+++ b/videopipeline/format_validator.py
@@ -29,10 +29,11 @@ class FormatValidator:
 
         fmt = format_plan.format_id
 
-        # Normalize segment source class mapping
+        # Source classes are part of the compose contract; do not infer them
+        # from names or segment labels during acceptance.
         for seg in segments:
-            if not seg.source_class:
-                seg.source_class = FormatValidator._infer_source_class(seg)
+            if seg.source_class is None:
+                raise FORMAT_GRAMMAR_VIOLATION(f"Source class is unverified at segment {seg.index}")
 
         if fmt == FormatId.F1:
             return FormatValidator._validate_f1(segments, format_plan)
@@ -175,6 +176,8 @@ class FormatValidator:
         has_original = any(seg.source_class == SourceClass.ORIGINAL_REUP_VIDEO for seg in segments)
         if not has_original:
             raise FORMAT_GRAMMAR_VIOLATION("F4 Reup requires an ORIGINAL_REUP_VIDEO source file.")
+        if not any(seg.source_class == SourceClass.STOCK_ONLINE for seg in segments):
+            raise FORMAT_GRAMMAR_VIOLATION("F4 Reup requires an ONLINE STOCK background video.")
 
         return {"valid": True, "format": "F4", "layout_id": layout.layout_id}
 
diff --git a/videopipeline/models.py b/videopipeline/models.py
index 989a603..4f2ccbd 100644
--- a/videopipeline/models.py
+++ b/videopipeline/models.py
@@ -342,6 +342,7 @@ class VisualSegment:
     asset_id: str = ""
     in_point: float = 0.0
     out_point: float = 0.0
+    background_source_path: Optional[Path] = None
 
     @property
     def end_time(self) -> float:
@@ -361,6 +362,7 @@ class VisualSegment:
             "asset_id": self.asset_id,
             "in_point": round(self.in_point, 2),
             "out_point": round(self.out_point, 2)
+            ,"background_source": str(self.background_source_path) if self.background_source_path else None
         }
 
 
diff --git a/videopipeline/stages/stage3_compose/timeline_builder.py b/videopipeline/stages/stage3_compose/timeline_builder.py
index 6918171..974d845 100644
--- a/videopipeline/stages/stage3_compose/timeline_builder.py
+++ b/videopipeline/stages/stage3_compose/timeline_builder.py
@@ -18,6 +18,7 @@ from ...models import (
 from ...config import F2_CHAPTER1_DURATION, F2_SEGMENT_DURATION
 from ...clip_registry import filter_unused, record_clips, get_registry_stats
 from ...format_validator import FormatValidator
+from ...format_semantics import normalize_format
 
 logger = logging.getLogger(__name__)
 
@@ -57,13 +58,7 @@ class TimelineBuilder:
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
+            fmt_id = normalize_format(format)
             format_plan = create_default_format_plan(fmt_id)
 
         # ── Filter out globally-used clips ──
@@ -214,7 +209,7 @@ class TimelineBuilder:
                 source_class=SourceClass.ORIGINAL_REUP_VIDEO,
                 asset_id=Path(src_video).stem
             ))
-            # Background stock interval
+            # The stock source remains a distinct, auditable timeline asset.
             bg_stock = stock_queue.popleft() if stock_queue else Path("placeholder_bg_stock.mp4")
             segments.append(VisualSegment(
                 index=1,
diff --git a/videopipeline/stages/stage4_render/nvenc_engine.py b/videopipeline/stages/stage4_render/nvenc_engine.py
index 7ba70df..2aa9731 100644
--- a/videopipeline/stages/stage4_render/nvenc_engine.py
+++ b/videopipeline/stages/stage4_render/nvenc_engine.py
@@ -63,15 +63,17 @@ class NvencRenderEngine:
                 fg_w = layout_profile.foreground_width if layout_profile else 1536
                 fg_h = layout_profile.foreground_height if layout_profile else 864
                 bg_blur = layout_profile.background_blur if layout_profile else 25
+                background = getattr(self, "_active_background", None)
+                if not background or not Path(background).is_file():
+                    raise FileNotFoundError("F4 requires its selected online stock background source")
                 filter_complex = (
-                    f"[0:v]split=2[bg_in][fg_in];"
-                    f"[bg_in]scale={DEFAULT_WIDTH}:{DEFAULT_HEIGHT}:force_original_aspect_ratio=increase,"
+                    f"[0:v]scale={DEFAULT_WIDTH}:{DEFAULT_HEIGHT}:force_original_aspect_ratio=increase,"
                     f"crop={DEFAULT_WIDTH}:{DEFAULT_HEIGHT},boxblur={bg_blur}:5[bg];"
-                    f"[fg_in]scale={fg_w}:{fg_h}:force_original_aspect_ratio=decrease[fg];"
+                    f"[1:v]scale={fg_w}:{fg_h}:force_original_aspect_ratio=decrease[fg];"
                     f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps={DEFAULT_FPS}[outv]"
                 )
                 filter_map = "[outv]"
-                input_args = ["-ss", f"{start_time:.3f}", "-i", str(p)] if start_time > 0 else ["-i", str(p)]
+                input_args = (["-ss", f"{start_time:.3f}"] if start_time > 0 else []) + ["-stream_loop", "-1", "-i", str(background)] + (["-ss", f"{start_time:.3f}"] if start_time > 0 else []) + ["-i", str(p)]
             elif segment_type == "f1_fullscreen":
                 input_args = ["-ss", f"{start_time:.3f}", "-i", str(p)] if start_time > 0 else ["-i", str(p)]
             elif is_image or segment_type == "slideshow":
@@ -173,6 +175,8 @@ class NvencRenderEngine:
         """
         normalized_paths: List[Path] = []
         for seg in schedule.segments:
+            selected_bg = seg.background_source_path or getattr(self, "_f4_background_path", None)
+            self._active_background = str(selected_bg) if selected_bg else None
             out_file = self.segments_dir / f"seg_{seg.index:03d}_{seg.segment_type}.mp4"
             is_opening = (seg.index < 6)
             needs_render = force or (is_opening and force_opening) or (not out_file.exists()) or (out_file.stat().st_size < 10000)
@@ -218,6 +222,25 @@ class NvencRenderEngine:
         """
         start_time = time.time()
         output_path.parent.mkdir(parents=True, exist_ok=True)
+        from ...models import FormatId, SourceClass, TimelineSchedule, create_default_format_plan
+        from ...format_validator import FormatValidator
+        from ...format_semantics import normalize_format
+        format_id = normalize_format(format)
+        format = format_id.value
+        format_plan = format_plan or create_default_format_plan(format_id)
+        FormatValidator.validate_timeline(schedule.segments, format_plan)
+        f4_background = next((s.source_path for s in schedule.segments if s.source_class == SourceClass.STOCK_ONLINE), None) if format_id == FormatId.F4 else None
+        render_segments = [s for s in schedule.segments if not (format_id == FormatId.F4 and s.source_class == SourceClass.STOCK_ONLINE)]
+        if format_id == FormatId.F4 and not f4_background:
+            raise FileNotFoundError("F4 requires a selected online stock background source")
+        if f4_background and not f4_background.is_file():
+            raise FileNotFoundError(f"Required F4 online background source is missing: {f4_background}")
+        original_schedule = schedule
+        for seg in render_segments:
+            if not seg.source_path.is_file():
+                raise FileNotFoundError(f"Required {seg.source_class.value} source is missing: {seg.source_path}")
+            if seg.background_source_path and not seg.background_source_path.is_file():
+                raise FileNotFoundError(f"Required F4 online background source is missing: {seg.background_source_path}")
         master_audio = audio_path or schedule.audio_path
         if not master_audio or not Path(master_audio).exists():
             # Auto-detect audio from story directory
@@ -229,7 +252,12 @@ class NvencRenderEngine:
                     break
 
         # 1. Normalize all segments
+        if format_id == FormatId.F4:
+            self._f4_background_path = f4_background
+            schedule = TimelineSchedule(schedule.story_dir, schedule.audio_path, schedule.total_duration, render_segments)
         seg_paths = self.normalize_all_segments(schedule)
+        schedule = original_schedule
+        self._f4_background_path = None
 
         # 2. Write concat file
         concat_file = self.work_dir / "concat_segments.txt"
@@ -356,6 +384,9 @@ class NvencRenderEngine:
         except Exception:
             pass
 
+        from ...format_evidence import write_render_evidence
+        write_render_evidence(schedule, format_id.value, output_path)
+
         assets_used = []
         for s in schedule.segments:
             s_class = getattr(s, "source_class", None)
@@ -433,7 +464,10 @@ class NvencRenderEngine:
                     duration=s.get("duration", 30.0),
                     segment_type=s.get("segment_type", s.get("type", "stock")),
                     source_path=Path(src) if src else Path(""),
-                    description=s.get("description", "")
+                    description=s.get("description", ""),
+                    source_class=__import__("videopipeline.models", fromlist=["SourceClass"]).SourceClass(s["source_class"]) if s.get("source_class") else None,
+                    asset_id=s.get("asset_id", ""),
+                    background_source_path=Path(s["background_source"]) if s.get("background_source") else None
                 ))
             story_dir = Path(data.get("story_dir")) if isinstance(data, dict) and data.get("story_dir") else self.work_dir.parent
             aud_path = Path(data.get("audio_path")) if isinstance(data, dict) and data.get("audio_path") else (audio_path or Path(""))
diff --git a/videopipeline/web/server.py b/videopipeline/web/server.py
index fee38ef..931254a 100644
--- a/videopipeline/web/server.py
+++ b/videopipeline/web/server.py
@@ -325,7 +325,12 @@ async def handle_action_compose(request):
     """Action: Compose timeline and ASS subtitles based on selected format."""
     data = await request.json()
     story_dir = Path(data.get("story_dir", ""))
-    fmt_choice = data.get("format", "f2") # f2, f2-l, f3, f1
+    from ..format_semantics import normalize_format, FORMAT_SEMANTICS
+    try:
+        selected_format = normalize_format(data.get("format", "f2"))
+    except ValueError as exc:
+        return web.json_response({"status": "error", "message": str(exc)}, status=400)
+    fmt_choice = selected_format.value.lower()
 
     if not story_dir.exists():
         return web.json_response({"status": "error", "message": "Story not found"}, status=404)
@@ -350,15 +355,15 @@ async def handle_action_compose(request):
     stock_mgr = StockManager(get_story_stock_dirs(story_dir))
     veo_client = GoogleFlowVeoClient()
 
-    if fmt_choice in ("f2-l", "f1"):
-        # Lite format & F1 reup: 100% Stock/existing, no Veo AI calls
+    if fmt_choice in ("f3", "f4"):
+        # These formats do not use generated video assets.
         veo_clips = []
         log_event(f"Format {fmt_choice.upper()} selected: Using existing assets (zero AI dependency).")
     else:
         veo_clips = veo_client.get_existing_veo_clips(story_dir / "veo_clips")
         log_event(f"Format {fmt_choice.upper()} selected: Using {len(veo_clips)} Veo 3.1 AI clips alternating with stock.")
 
-    body_images = veo_client.get_existing_body_images(story_dir / "images") if fmt_choice in ("f4", "f3") else []
+    body_images = veo_client.get_existing_body_images(story_dir / "images") if fmt_choice in ("f1", "f3") else []
     body_scenes = None
     cache_file = story_dir / "gemini_storyboard.json"
     if cache_file.exists():
@@ -369,7 +374,7 @@ async def handle_action_compose(request):
             pass
 
     tb = TimelineBuilder(story_dir, audios[0], total_dur)
-    chap1_src = story_dir / "Final_Video_Export" / "Phase1_Prototype_3M.mp4"
+    chap1_src = None if selected_format.value == "F4" else story_dir / "Final_Video_Export" / "Phase1_Prototype_3M.mp4"
     sched = tb.build_schedule(
         chap1_source=chap1_src if chap1_src.exists() else None,
         stock_clips=stock_mgr.get_stock_pool(),
@@ -378,6 +383,11 @@ async def handle_action_compose(request):
         images=body_images,
         body_scenes=body_scenes
     )
+    from ..format_evidence import validate_bound_sources
+    try:
+        validate_bound_sources(sched)
+    except FileNotFoundError as exc:
+        return web.json_response({"status": "needs_owner", "message": str(exc), "format": fmt_choice}, status=409)
 
     sched_path = work_dir / "video_schedule.json"
     tb.save_schedule_json(sched, sched_path)
@@ -387,6 +397,7 @@ async def handle_action_compose(request):
     return web.json_response({
         "status": "ok",
         "format": fmt_choice,
+        "format_semantics": FORMAT_SEMANTICS[selected_format],
         "segments": len(sched.segments),
         "ass_file": str(ass_path.resolve()),
         "schedule_file": str(sched_path.resolve())
@@ -405,6 +416,8 @@ PIPELINE_STATE: Dict[str, Any] = {
 async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[str, Any], dry_run: bool):
     """Asynchronously orchestrates all 4 pipeline stages from start to finish."""
     global PIPELINE_STATE
+    from ..format_semantics import normalize_format
+    fmt_choice = normalize_format(fmt_choice).value.lower()
     try:
         log_event(f"============================================================")
         log_event(f"🚀 KÍCH HOẠT PIPELINE TOÀN DIỆN CHO: {story_dir.name}")
@@ -474,7 +487,7 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
         veo_client = GoogleFlowVeoClient()
         cookie_stat = veo_client.validate_cookie()
         reg_stats = get_registry_stats()
-        if fmt_choice in ("f2-l", "f1"):
+        if fmt_choice in ("f3", "f4"):
             veo_clips = []
             log_event(f"[Stage 2 Assets] Format {fmt_choice.upper()}: Sẵn sàng {stock_mgr.unused_count} clips mới 100% (Đã lọc bỏ {reg_stats['total_used']} clips đã dùng từ các video trước).")
         else:
@@ -512,7 +525,7 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
         body_images: List[Path] = []
         body_scenes: Optional[List[Dict[str, Any]]] = None
 
-        if fmt_choice in ("f4", "f3"):
+        if fmt_choice in ("f1", "f3"):
             body_images = veo_client.get_existing_body_images(story_dir / "images")
 
         if fmt_choice == "f4":
@@ -586,13 +599,15 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
         tb = TimelineBuilder(story_dir, chosen_audio, total_dur)
         chap1_src = story_dir / "Final_Video_Export" / "Phase1_Prototype_3M.mp4"
         sched = tb.build_schedule(
-            chap1_source=chap1_src if chap1_src.exists() else None,
+            chap1_source=chap1_src if chap1_src.exists() and fmt_choice != "f4" else None,
             stock_clips=stock_mgr.get_stock_pool(),
             veo_clips=veo_clips,
             format=fmt_choice,
             images=body_images,
             body_scenes=body_scenes
         )
+        from ..format_evidence import validate_bound_sources
+        validate_bound_sources(sched)
         sched_path = work_dir / "video_schedule.json"
         tb.save_schedule_json(sched, sched_path)
         log_event(f"[Stage 3 Compose] Đã lên lịch trình phân đoạn timeline: {len(sched.segments)} segments (Format {fmt_choice.upper()}).")
@@ -601,7 +616,7 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
         from ..format_validator import FormatValidator
         from ..stages.stage3_compose.editorial_qc import EditorialQC
 
-        format_id_enum = FormatId(fmt_choice.upper()) if hasattr(FormatId, fmt_choice.upper()) else FormatId.F2
+        format_id_enum = normalize_format(fmt_choice)
         format_plan = create_default_format_plan(format_id_enum)
         run_req = RunRequest(story_dir=story_dir, format_id=format_id_enum, format_plan=format_plan, options=options)

Return exactly READY or REPAIR: followed by one bounded repair brief. If no safe repair is possible, return NOT_READY with a reason.
