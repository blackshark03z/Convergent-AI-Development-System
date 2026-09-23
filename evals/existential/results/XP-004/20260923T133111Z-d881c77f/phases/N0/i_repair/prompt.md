# XP-004 Common Implementer Prompt

You are the implementation role (I) for a controlled benchmark. You receive a
disposable neutral AutoVideoPipeline snapshot and an Implementation Brief from R.
Implement the brief using the cheapest coherent technical path you judge
appropriate.

Rules:
- inspect the assigned repository as needed and own implementation details;
- keep changes scoped to the brief and run relevant deterministic checks;
- do not call paid/external providers or the canonical production runtime;
- do not search for historical/reference implementations, sibling workspaces,
  results or hidden benchmark tests;
- do not weaken tests/acceptance surfaces to make the candidate pass;
- do not cross external or irreversible effect boundaries absent from the brief;
- decide ordinary implementation choices yourself; report a genuinely missing
  material product preference or authority decision rather than inventing it.

When finished, report exact files/behavior changed, checks actually run and
their results, product-level evidence observed, known limitations/untested
surfaces, and material assumptions. Do not claim Product Acceptance. Your output
is a candidate for R review and later hidden evaluation.


Original IMPLEMENTATION_BRIEF:
IMPLEMENTATION_BRIEF

**Outcome:** Acceptance for each canonical F1–F5 format proves that the selected format and actual source assets pass through the product’s plan, timeline, compose, and render path, and binds the accepted output to the product state that produced it.

**Acceptance:**

- Exercise each format through the real CLI and Web product paths with local media and no external providers. Verify the rendered result against the selected format’s source semantics: F1 generated video opening and generated image body; F2 generated opening plus stock and generated video after the opening; F3 generated images only; F4 original video inset with stock background; F5 stock footage only. Check media used by the render, not just segment labels or validator return values.
- CLI and Web must resolve the same canonical format truth. An unknown format, missing required asset, unverifiable source class, or format mismatch between compose and render must produce an explicit non-accepted result. Neither path may silently select F2, invent a placeholder, or substitute another source class.
- A successful acceptance record identifies the selected format, the source assets actually used, the verified product state, and the output’s content identity. Its lineage must connect the plan, timeline, compose decision, render, and verification for that same run. Changed inputs, product state, or a reused stale output cannot retain the prior acceptance.
- Demonstrate rejection with negative cases that change a required source class, remove required media, or break lineage after verification. A record whose claims are internally consistent but disagree with the rendered media must fail.

**Constraints:** Use disposable local fixtures and local rendering or equivalent product-path evidence. Do not call paid or external providers or the canonical production runtime. Judge observable behavior; the storage format and implementation structure are open.

OWNER_INPUT_REQUIRED: no

Your previous completion report:
I implemented a partial candidate, but it does **not** meet the full acceptance brief.

Changed:

- [format_validator.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N0/videopipeline/format_validator.py): added strict canonical format resolution and optional checks that required media exists, is nonempty, and has an image or video extension consistent with its claimed class.
- [timeline_builder.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N0/videopipeline/stages/stage3_compose/timeline_builder.py): rejects unknown formats and removes fabricated missing-asset paths for F1–F5.
- [cli.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N0/videopipeline/cli.py) and [server.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N0/videopipeline/web/server.py): persist the selected format in composed schedules; CLI render rejects a compose/render format mismatch and validates media.
- [nvenc_engine.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N0/videopipeline/stages/stage4_render/nvenc_engine.py): rejects missing render media instead of substituting a generated background frame.

Checks run:

- `python -m compileall -q videopipeline` passed.
- `python -m pytest tests/test_format_grammar.py tests/test_negative_mutations.py -q` passed: 26 tests.
- `python -m pytest -q` ran 100 tests: 99 passed, 1 failed. The existing F4 timeline test supplies nonexistent media paths; the builder now rejects the missing original source, as required by the brief.

I did not render local fixture videos or exercise the Web path end to end. The existing renderer manifest records output and claimed asset classes, but the implementation here does not bind a verified plan/timeline/compose/render run or hash source assets. It also does not verify source class beyond file extension, so it cannot distinguish generated video from stock footage by inspecting media alone. F4’s actual background-stock plus original-video inset rendering path remains unverified. These gaps mean this candidate cannot claim product acceptance.

Current candidate tree: 19a39c0350be8c8982e1cbfcf233fafbf20178fb
Current diff:
diff --git a/videopipeline/cli.py b/videopipeline/cli.py
index b51124e..65a991c 100644
--- a/videopipeline/cli.py
+++ b/videopipeline/cli.py
@@ -90,15 +90,14 @@ def cmd_compose(args):
     veo_clips = veo_client.get_existing_veo_clips(story_dir / "veo_clips")
     chap1_candidate = story_dir / "Final_Video_Export" / "Phase1_Prototype_3M.mp4"
 
-    fmt_str = getattr(args, "format", "f2").upper()
-    if fmt_str == "F2-L":
-        fmt_str = "F2"
+    from .format_validator import resolve_format
+    fmt_id = resolve_format(getattr(args, "format", "f2"))
+    fmt_str = fmt_id.value
     from .models import FormatId, RunRequest, create_default_format_plan, EditorialVerdict
     from .format_validator import FormatValidator
     from .stages.stage3_compose.editorial_qc import EditorialQC
     import json
 
-    fmt_id = FormatId(fmt_str) if hasattr(FormatId, fmt_str) else FormatId.F2
     format_plan = create_default_format_plan(fmt_id)
     run_req = RunRequest(story_dir=story_dir, format_id=fmt_id, format_plan=format_plan)
 
@@ -138,6 +137,10 @@ def cmd_compose(args):
 
     sched_path = work_dir / "video_schedule.json"
     tb.save_schedule_json(sched, sched_path)
+    data = json.loads(sched_path.read_text(encoding="utf-8"))
+    data["format_id"] = fmt_id.value
+    data["format_plan_fingerprint"] = format_plan.fingerprint
+    sched_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
     print(f"[Compose] Generated Schedule: {sched_path} ({len(sched.segments)} segments)")
 
 def cmd_render(args):
@@ -154,9 +157,13 @@ def cmd_render(args):
 
     # Load schedule
     import json
-    from .models import TimelineSchedule, VisualSegment
+    from .models import TimelineSchedule, VisualSegment, create_default_format_plan
     with open(sched_path, "r", encoding="utf-8") as f:
         data = json.load(f)
+    from .format_validator import resolve_format, FormatValidator
+    selected_format = resolve_format(getattr(args, "format", "f2"))
+    if data.get("format_id") != selected_format.value:
+        raise ValueError(f"Compose/render format mismatch: composed {data.get('format_id')!r}, requested {selected_format.value}")
     segments = [
         VisualSegment(
             index=s["index"],
@@ -174,6 +181,9 @@ def cmd_render(args):
         total_duration=data["total_duration"],
         segments=segments
     )
+    schedule.format_id = selected_format.value
+    format_plan = create_default_format_plan(selected_format)
+    FormatValidator.validate_timeline(segments, format_plan, require_media=True)
 
     qc_verdict = data.get("editorial_qc_verdict", "PASS")
     owner_disp = data.get("owner_disposition", "AUTO")
@@ -193,7 +203,7 @@ def cmd_render(args):
     print(f"[Render] Starting NVENC Render Engine...")
     print(f"[Render] Target Output: {out_file}")
     engine = NvencRenderEngine(work_dir)
-    metrics = engine.render_master_video(schedule, ass_path, out_file, format=getattr(args, "format", "f2"))
+    metrics = engine.render_master_video(schedule, ass_path, out_file, format=selected_format.value, format_plan=format_plan)
     print(f"[Render] COMPLETE!")
     print(f"  Duration: {metrics.duration_sec:.2f}s")
     print(f"  File Size: {metrics.file_size_bytes:,} bytes")
@@ -275,7 +285,7 @@ def main():
     # Common story arg
     parent_parser = argparse.ArgumentParser(add_help=False)
     parent_parser.add_argument("--story-dir", required=True, help="Path to story directory")
-    parent_parser.add_argument("--format", choices=["f1", "f2", "f3", "f4", "f5", "f2-l"], default="f2", help="Canonical video format (F1-F5)")
+    parent_parser.add_argument("--format", default="f2", help="Canonical video format (F1-F5)")
     parent_parser.add_argument("--accept-override", action="store_true", help="Accept EditorialQC override if verdict is NEEDS_OWNER")
 
     # Ingest
diff --git a/videopipeline/format_validator.py b/videopipeline/format_validator.py
index 9d5241b..346210a 100644
--- a/videopipeline/format_validator.py
+++ b/videopipeline/format_validator.py
@@ -5,6 +5,19 @@ Raises FORMAT_GRAMMAR_VIOLATION on any source class or structure breach.
 """
 from typing import List, Dict, Any, Optional
 from .models import FormatId, SourceClass, FormatPlan, VisualSegment, LayoutProfile
+from pathlib import Path
+import hashlib
+
+
+def resolve_format(value):
+    """Resolve a user supplied format without silently changing its identity."""
+    raw = str(value or "").strip().upper()
+    if raw == "F2-L":
+        raw = "F2"
+    try:
+        return FormatId(raw)
+    except ValueError as exc:
+        raise FORMAT_GRAMMAR_VIOLATION(f"Unknown format: {value!r}") from exc
 
 
 class FORMAT_GRAMMAR_VIOLATION(ValueError):
@@ -19,7 +32,7 @@ class FormatValidator:
     """
 
     @staticmethod
-    def validate_timeline(segments: List[VisualSegment], format_plan: FormatPlan) -> Dict[str, Any]:
+    def validate_timeline(segments: List[VisualSegment], format_plan: FormatPlan, require_media: bool = False) -> Dict[str, Any]:
         """
         Validates the visual segments against the FormatPlan grammar.
         Raises FORMAT_GRAMMAR_VIOLATION on any breach.
@@ -27,6 +40,20 @@ class FormatValidator:
         if not segments:
             raise FORMAT_GRAMMAR_VIOLATION("Timeline is empty. Full visual coverage is required.")
 
+        if require_media:
+            for seg in segments:
+                p = Path(seg.source_path)
+                if not p.is_file() or p.stat().st_size == 0:
+                    raise FORMAT_GRAMMAR_VIOLATION(f"Missing required media for segment {seg.index}: {p}")
+                ext = p.suffix.lower()
+                if ext not in {".mp4", ".mov", ".mkv", ".webm", ".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
+                    raise FORMAT_GRAMMAR_VIOLATION(f"Unverifiable media type for segment {seg.index}: {p}")
+                is_image = ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
+                if seg.source_class == SourceClass.GENERATED_IMAGE and not is_image:
+                    raise FORMAT_GRAMMAR_VIOLATION(f"Segment {seg.index} claims GENERATED_IMAGE but is {ext}")
+                if seg.source_class in (SourceClass.GENERATED_VIDEO, SourceClass.STOCK_ONLINE, SourceClass.ORIGINAL_REUP_VIDEO) and is_image:
+                    raise FORMAT_GRAMMAR_VIOLATION(f"Segment {seg.index} claims video source class but is {ext}")
+
         fmt = format_plan.format_id
 
         # Normalize segment source class mapping
@@ -58,7 +85,7 @@ class FormatValidator:
             return SourceClass.STOCK_ONLINE
         elif t in ("f1_framed", "reup", "original_source"):
             return SourceClass.ORIGINAL_REUP_VIDEO
-        return SourceClass.STOCK_ONLINE
+        raise FORMAT_GRAMMAR_VIOLATION(f"Cannot verify source class for segment {seg.index}: {seg.segment_type}")
 
     @staticmethod
     def _validate_f1(segments: List[VisualSegment], plan: FormatPlan) -> Dict[str, Any]:
diff --git a/videopipeline/stages/stage3_compose/timeline_builder.py b/videopipeline/stages/stage3_compose/timeline_builder.py
index 6918171..0d63487 100644
--- a/videopipeline/stages/stage3_compose/timeline_builder.py
+++ b/videopipeline/stages/stage3_compose/timeline_builder.py
@@ -18,6 +18,7 @@ from ...models import (
 from ...config import F2_CHAPTER1_DURATION, F2_SEGMENT_DURATION
 from ...clip_registry import filter_unused, record_clips, get_registry_stats
 from ...format_validator import FormatValidator
+from ...format_validator import resolve_format
 
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
+            fmt_id = resolve_format(format)
             format_plan = create_default_format_plan(fmt_id)
 
         # ── Filter out globally-used clips ──
@@ -118,7 +113,9 @@ class TimelineBuilder:
                     current_time += clip_dur
                     seg_idx += 1
             else:
-                open_src = chap1_source or (veo_queue.popleft() if veo_queue else Path("placeholder_opening_ai.mp4"))
+                open_src = chap1_source or (veo_queue.popleft() if veo_queue else None)
+                if open_src is None:
+                    raise ValueError("F1 requires an existing generated opening video asset")
                 segments.append(VisualSegment(
                     index=seg_idx,
                     start_time=0.0,
@@ -139,7 +136,9 @@ class TimelineBuilder:
                     dur = min(s_dur, max(0.0, self.total_duration - current_time))
                     if dur <= 0:
                         break
-                    img_src = avail_images[img_cursor % len(avail_images)] if avail_images else Path("placeholder_scene.jpg")
+                    if not avail_images:
+                        raise ValueError("F1 requires existing generated body images")
+                    img_src = avail_images[img_cursor % len(avail_images)]
                     img_cursor += 1
                     segments.append(VisualSegment(
                         index=seg_idx,
@@ -157,7 +156,9 @@ class TimelineBuilder:
                 while current_time < self.total_duration:
                     rem = self.total_duration - current_time
                     dur = min(rem, 45.0)
-                    img_src = avail_images[img_cursor % len(avail_images)] if avail_images else Path("placeholder_scene.jpg")
+                    if not avail_images:
+                        raise ValueError("F1 requires existing generated body images")
+                    img_src = avail_images[img_cursor % len(avail_images)]
                     img_cursor += 1
                     segments.append(VisualSegment(
                         index=seg_idx,
@@ -178,7 +179,9 @@ class TimelineBuilder:
             while current_time < self.total_duration:
                 rem = self.total_duration - current_time
                 dur = min(rem, 45.0)
-                img_src = avail_images[img_cursor % len(avail_images)] if avail_images else Path("placeholder_scene.jpg")
+                if not avail_images:
+                    raise ValueError("F3 requires existing generated images")
+                img_src = avail_images[img_cursor % len(avail_images)]
                 img_cursor += 1
                 segments.append(VisualSegment(
                     index=seg_idx,
@@ -201,7 +204,9 @@ class TimelineBuilder:
                              list(self.story_dir.glob("full_video.mp4")) + \
                              list(self.story_dir.glob("reup_video.mp4")) + \
                              list(self.story_dir.glob("*.mp4"))
-                src_video = candidates[0] if candidates else Path("source_video.mp4")
+                src_video = candidates[0] if candidates else None
+            if src_video is None:
+                raise ValueError("F4 requires an existing original source video")
 
             # Inset foreground segment
             segments.append(VisualSegment(
@@ -215,7 +220,9 @@ class TimelineBuilder:
                 asset_id=Path(src_video).stem
             ))
             # Background stock interval
-            bg_stock = stock_queue.popleft() if stock_queue else Path("placeholder_bg_stock.mp4")
+            if not stock_queue:
+                raise ValueError("F4 requires an existing stock background video")
+            bg_stock = stock_queue.popleft()
             segments.append(VisualSegment(
                 index=1,
                 start_time=0.0,
@@ -237,7 +244,7 @@ class TimelineBuilder:
                     st_src = stock_queue.popleft()
                     newly_used.append(st_src)
                 else:
-                    st_src = Path(f"stock_clip_{stock_cursor+1}.mp4")
+                    raise ValueError("F5 requires existing stock footage for the full timeline")
 
                 stock_cursor += 1
                 segments.append(VisualSegment(
@@ -257,7 +264,9 @@ class TimelineBuilder:
         else:
             # AI Opening (~60s)
             opening_dur = min(self.total_duration, F2_CHAPTER1_DURATION)
-            open_src = chap1_source or (veo_queue.popleft() if veo_queue else Path("placeholder_opening_ai.mp4"))
+            open_src = chap1_source or (veo_queue.popleft() if veo_queue else None)
+            if open_src is None:
+                raise ValueError("F2 requires an existing generated opening video asset")
             segments.append(VisualSegment(
                 index=seg_idx,
                 start_time=0.0,
@@ -283,11 +292,15 @@ class TimelineBuilder:
                     target_cls = sh.visual_requirement.preferred_source_class if sh.visual_requirement else SourceClass.STOCK_ONLINE
 
                     if target_cls == SourceClass.STOCK_ONLINE:
-                        src = stock_queue.popleft() if stock_queue else Path(f"stock_{seg_idx}.mp4")
+                        if not stock_queue:
+                            raise ValueError("F2 requires existing stock footage")
+                        src = stock_queue.popleft()
                         seg_type = "stock"
                         newly_used.append(src)
                     else:
-                        src = veo_queue.popleft() if veo_queue else Path(f"veo_ai_{seg_idx}.mp4")
+                        if not veo_queue:
+                            raise ValueError("F2 requires existing generated video footage")
+                        src = veo_queue.popleft()
                         seg_type = "veo_ai"
 
                     segments.append(VisualSegment(
@@ -313,12 +326,16 @@ class TimelineBuilder:
 
                     # Ensure at least 1 stock and at least 1 veo post-opening
                     if slot % 2 == 0:
-                        src = stock_queue.popleft() if stock_queue else Path(f"stock_{seg_idx}.mp4")
+                        if not stock_queue:
+                            raise ValueError("F2 requires existing stock footage")
+                        src = stock_queue.popleft()
                         seg_type = "stock"
                         cls = SourceClass.STOCK_ONLINE
                         newly_used.append(src)
                     else:
-                        src = veo_queue.popleft() if veo_queue else Path(f"veo_ai_{seg_idx}.mp4")
+                        if not veo_queue:
+                            raise ValueError("F2 requires existing generated video footage")
+                        src = veo_queue.popleft()
                         seg_type = "veo_ai"
                         cls = SourceClass.GENERATED_VIDEO
 
@@ -353,7 +370,7 @@ class TimelineBuilder:
 
         # Validate grammar
         if validate:
-            FormatValidator.validate_timeline(segments, format_plan)
+            FormatValidator.validate_timeline(segments, format_plan, require_media=self.story_dir.exists())
 
         return schedule
 
diff --git a/videopipeline/stages/stage4_render/nvenc_engine.py b/videopipeline/stages/stage4_render/nvenc_engine.py
index 7ba70df..ecd9341 100644
--- a/videopipeline/stages/stage4_render/nvenc_engine.py
+++ b/videopipeline/stages/stage4_render/nvenc_engine.py
@@ -54,6 +54,8 @@ class NvencRenderEngine:
         filter_map: Optional[str] = None
 
         src_exists = src_path and Path(src_path).exists() and Path(src_path).is_file()
+        if not src_exists:
+            raise FileNotFoundError(f"Required render media is missing: {src_path}")
         temp_motion: Optional[Path] = None
 
         if src_exists:
@@ -109,8 +111,7 @@ class NvencRenderEngine:
                 except Exception:
                     pass
         else:
-            # Fallback for missing/unassigned clips: high-contrast dark gradient frame
-            input_args = ["-f", "lavfi", "-i", f"color=c=0x0a0e17:s={DEFAULT_WIDTH}x{DEFAULT_HEIGHT}:r={DEFAULT_FPS}"]
+            raise FileNotFoundError(f"Required render media is missing: {src_path}")
 
         if filter_complex and filter_map:
             filter_args = ["-filter_complex", filter_complex, "-map", filter_map]
@@ -217,6 +218,16 @@ class NvencRenderEngine:
         Supports rich atmospheric HUD for story formats (F4, F3, F2, F2-L) and clean stream composition for F1.
         """
         start_time = time.time()
+        from ...format_validator import resolve_format, FormatValidator
+        selected = resolve_format(format)
+        composed = getattr(schedule, "format_id", None)
+        if composed and composed != selected.value:
+            raise ValueError(f"Compose/render format mismatch: composed {composed}, requested {selected.value}")
+        plan = format_plan
+        if plan is None:
+            from ...models import create_default_format_plan
+            plan = create_default_format_plan(selected)
+        FormatValidator.validate_timeline(schedule.segments, plan, require_media=True)
         output_path.parent.mkdir(parents=True, exist_ok=True)
         master_audio = audio_path or schedule.audio_path
         if not master_audio or not Path(master_audio).exists():
diff --git a/videopipeline/web/server.py b/videopipeline/web/server.py
index fee38ef..5862bef 100644
--- a/videopipeline/web/server.py
+++ b/videopipeline/web/server.py
@@ -326,6 +326,11 @@ async def handle_action_compose(request):
     data = await request.json()
     story_dir = Path(data.get("story_dir", ""))
     fmt_choice = data.get("format", "f2") # f2, f2-l, f3, f1
+    from ..format_validator import resolve_format
+    try:
+        fmt_choice = resolve_format(fmt_choice).value.lower()
+    except ValueError as exc:
+        return web.json_response({"status": "rejected", "accepted": False, "message": str(exc)}, status=400)
 
     if not story_dir.exists():
         return web.json_response({"status": "error", "message": "Story not found"}, status=404)
@@ -381,6 +386,9 @@ async def handle_action_compose(request):
 
     sched_path = work_dir / "video_schedule.json"
     tb.save_schedule_json(sched, sched_path)
+    sched_data = json.loads(sched_path.read_text(encoding="utf-8"))
+    sched_data["format_id"] = fmt_choice.upper()
+    sched_path.write_text(json.dumps(sched_data, indent=2, ensure_ascii=False), encoding="utf-8")
     log_event(f"Timeline schedule created: {len(sched.segments)} segments (Format {fmt_choice.upper()}).")
 
 
@@ -406,6 +414,8 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
     """Asynchronously orchestrates all 4 pipeline stages from start to finish."""
     global PIPELINE_STATE
     try:
+        from ..format_validator import resolve_format
+        fmt_choice = resolve_format(fmt_choice).value.lower()
         log_event(f"============================================================")
         log_event(f"🚀 KÍCH HOẠT PIPELINE TOÀN DIỆN CHO: {story_dir.name}")
         log_event(f"   Format: {fmt_choice.upper()} | NVENC: {options.get('use_nvenc', True)} | QA: {options.get('auto_qa', True)}")
@@ -595,6 +605,9 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
         )
         sched_path = work_dir / "video_schedule.json"
         tb.save_schedule_json(sched, sched_path)
+        sched_data = json.loads(sched_path.read_text(encoding="utf-8"))
+        sched_data["format_id"] = fmt_choice.upper()
+        sched_path.write_text(json.dumps(sched_data, indent=2, ensure_ascii=False), encoding="utf-8")
         log_event(f"[Stage 3 Compose] Đã lên lịch trình phân đoạn timeline: {len(sched.segments)} segments (Format {fmt_choice.upper()}).")
 
         from ..models import FormatId, RunRequest, create_default_format_plan, EditorialVerdict

R repair brief:
REPAIR: The candidate rejects some missing assets, but it cannot yet establish acceptance for the rendered product. F4’s original and stock segments are rendered sequentially rather than as an inset over a stock background; Web can report success for an existing master without rendering; and the manifest’s source classes and lineage are largely unverified claims.

Complete the acceptance path so that:

- Local product-path runs for F1–F5 verify the media actually rendered, including F4’s simultaneous original inset and stock background. Source class evidence must establish provenance beyond a file extension or schedule label.
- CLI and Web accept an output only when its selected format, plan, timeline, compose decision, source assets, rendered content, and verification belong to the same current product state. Missing evidence, changed inputs, or a stale cached segment or master must yield a non-accepted result.
- Disposable local tests demonstrate all five successful formats and rejection after a source-class substitution, missing required media, a compose/render format mismatch, and a lineage or output change. Resolve the failing F4 fixture test with valid media. Do not use external providers or the production runtime.

This is the sole repair. Work only in this disposable clone. No external or production effects. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report checks actually run and remaining limits.
