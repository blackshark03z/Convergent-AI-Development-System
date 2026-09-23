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

I completion report:
Implemented a fail closed candidate for the format and media boundaries. **This does not establish acceptance of all five rendered paths.**

- CLI and Web now resolve F1–F5 consistently, reject unsupported Web formats, and no longer silently fall back to F2. Missing required assets stop composition instead of becoming placeholder paths.
- Composed schedules record the selected format and hashes for media, narration, subtitles, and format settings. CLI render rejects missing digests, changed inputs, and format mismatches. Web rerenders the current schedule instead of reusing a master by filename.
- F4 rendering now composites the original video as an inset over a stock background. The renderer checks that both tracks cover the program.
- Updated [cli.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/videopipeline/cli.py), [server.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/videopipeline/web/server.py), [timeline_builder.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/videopipeline/stages/stage3_compose/timeline_builder.py), [nvenc_engine.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/videopipeline/stages/stage4_render/nvenc_engine.py), [format_validator.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/videopipeline/format_validator.py), and [models.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CCURRENT/videopipeline/models.py).

**Checks run:** `compileall` passed; the format grammar, timeline builder, and Web server tests passed (24 total); `git diff --check` passed. A local smoke check confirmed F1 schedule binding and rejection of changed media, missing images, and an illegal source class.

**Remaining acceptance gap:** I did not run plan → timeline → compose → render for all five formats with local representative media, or independently inspect those rendered outputs. Source class still comes from pipeline classification metadata; this work hashes the bytes but does not independently prove that the content’s origin matches its declared class. Treat this as a candidate for R review, not Product Acceptance.

Candidate tree: 408e2115ddf5c3b1a4f125ce101b61832bf1aa52
Candidate status:
M  videopipeline/cli.py
M  videopipeline/format_validator.py
M  videopipeline/models.py
M  videopipeline/stages/stage3_compose/timeline_builder.py
M  videopipeline/stages/stage4_render/nvenc_engine.py
M  videopipeline/web/server.py
Candidate diff:
diff --git a/videopipeline/cli.py b/videopipeline/cli.py
index b51124e..948b9bb 100644
--- a/videopipeline/cli.py
+++ b/videopipeline/cli.py
@@ -21,6 +21,7 @@ from .stages.stage3_compose.timeline_builder import TimelineBuilder
 from .stages.stage3_compose.ass_karaoke import generate_karaoke_ass
 from .stages.stage4_render.nvenc_engine import NvencRenderEngine
 from .stages.stage4_render.qa_verifier import QAVerifier
+from .models import SourceClass
 
 def resolve_story_assets(story_dir: Path):
     """Finds audio and srt files inside the story folder."""
@@ -88,6 +89,8 @@ def cmd_compose(args):
     stock_mgr = StockManager(get_story_stock_dirs(story_dir))
     veo_client = GoogleFlowVeoClient()
     veo_clips = veo_client.get_existing_veo_clips(story_dir / "veo_clips")
+    image_dir = story_dir / "images"
+    body_images = sorted(p for p in image_dir.glob("scene_*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}) if image_dir.exists() else []
     chap1_candidate = story_dir / "Final_Video_Export" / "Phase1_Prototype_3M.mp4"
 
     fmt_str = getattr(args, "format", "f2").upper()
@@ -98,20 +101,31 @@ def cmd_compose(args):
     from .stages.stage3_compose.editorial_qc import EditorialQC
     import json
 
-    fmt_id = FormatId(fmt_str) if hasattr(FormatId, fmt_str) else FormatId.F2
+    fmt_id = FormatId(fmt_str)
     format_plan = create_default_format_plan(fmt_id)
     run_req = RunRequest(story_dir=story_dir, format_id=fmt_id, format_plan=format_plan)
 
     tb = TimelineBuilder(story_dir, audio_path, total_dur)
     sched = tb.build_schedule(
-        chap1_source=chap1_candidate if chap1_candidate.exists() else None,
+        chap1_source=chap1_candidate if fmt_id != FormatId.F4 and chap1_candidate.exists() else None,
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
@@ -164,16 +178,54 @@ def cmd_render(args):
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
+    requested = getattr(args, "format", "f2").upper()
+    requested = "F2" if requested == "F2-L" else requested
+    bound = data.get("format_id")
+    if not bound or bound != requested:
+        raise ValueError(f"Selected format {requested} does not match composed timeline format {bound}")
+    format_plan = create_default_format_plan(FormatId(requested))
+    schedule.format_id = bound
+    schedule.format_plan_fingerprint = data.get("format_plan_fingerprint", "")
+    schedule.source_sha256s = {str(seg.source_path.resolve()): item["source_sha256"] for item, seg in zip(data["segments"], segments)}
+    schedule.audio_sha256 = expected_audio_hash
+    if product_state.get("format_plan_fingerprint") and product_state["format_plan_fingerprint"] != format_plan.fingerprint:
+        raise ValueError("Stale timeline lineage: resolved format settings changed since compose")
+    from .format_validator import FormatValidator
+    FormatValidator.validate_timeline(segments, format_plan)
 
     qc_verdict = data.get("editorial_qc_verdict", "PASS")
     owner_disp = data.get("owner_disposition", "AUTO")
@@ -193,7 +245,7 @@ def cmd_render(args):
     print(f"[Render] Starting NVENC Render Engine...")
     print(f"[Render] Target Output: {out_file}")
     engine = NvencRenderEngine(work_dir)
-    metrics = engine.render_master_video(schedule, ass_path, out_file, format=getattr(args, "format", "f2"))
+    metrics = engine.render_master_video(schedule, ass_path, out_file, format=requested, format_plan=format_plan)
     print(f"[Render] COMPLETE!")
     print(f"  Duration: {metrics.duration_sec:.2f}s")
     print(f"  File Size: {metrics.file_size_bytes:,} bytes")
diff --git a/videopipeline/format_validator.py b/videopipeline/format_validator.py
index 9d5241b..8bfb8cd 100644
--- a/videopipeline/format_validator.py
+++ b/videopipeline/format_validator.py
@@ -58,7 +58,9 @@ class FormatValidator:
             return SourceClass.STOCK_ONLINE
         elif t in ("f1_framed", "reup", "original_source"):
             return SourceClass.ORIGINAL_REUP_VIDEO
-        return SourceClass.STOCK_ONLINE
+        raise FORMAT_GRAMMAR_VIOLATION(
+            f"Cannot verify source class for segment {seg.index} ({seg.segment_type})"
+        )
 
     @staticmethod
     def _validate_f1(segments: List[VisualSegment], plan: FormatPlan) -> Dict[str, Any]:
@@ -172,10 +174,12 @@ class FormatValidator:
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
index 989a603..4051b7c 100644
--- a/videopipeline/models.py
+++ b/videopipeline/models.py
@@ -348,12 +348,22 @@ class VisualSegment:
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
@@ -373,11 +383,20 @@ class TimelineSchedule:
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
 
@@ -485,6 +504,7 @@ class RunManifest:
     output_file: str = ""
     output_sha256: str = ""
     assets_used: List[Dict[str, Any]] = field(default_factory=list)
+    product_state: Dict[str, Any] = field(default_factory=dict)
     redacted: bool = True
 
     def to_dict(self) -> Dict[str, Any]:
diff --git a/videopipeline/stages/stage3_compose/timeline_builder.py b/videopipeline/stages/stage3_compose/timeline_builder.py
index 6918171..9843297 100644
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
@@ -63,7 +64,7 @@ class TimelineBuilder:
             elif fmt_str == "F2-L":
                 fmt_id = FormatId.F2
             else:
-                fmt_id = FormatId.F2
+                raise ValueError(f"Unsupported format {format!r}; expected F1-F5 (or legacy F2-L)")
             format_plan = create_default_format_plan(fmt_id)
 
         # ── Filter out globally-used clips ──
@@ -118,7 +119,9 @@ class TimelineBuilder:
                     current_time += clip_dur
                     seg_idx += 1
             else:
-                open_src = chap1_source or (veo_queue.popleft() if veo_queue else Path("placeholder_opening_ai.mp4"))
+                open_src = chap1_source or (veo_queue.popleft() if veo_queue else None)
+                if open_src is None:
+                    raise FileNotFoundError("F1 requires a generated-video opening asset")
                 segments.append(VisualSegment(
                     index=seg_idx,
                     start_time=0.0,
@@ -139,7 +142,9 @@ class TimelineBuilder:
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
@@ -157,7 +162,9 @@ class TimelineBuilder:
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
@@ -178,7 +185,9 @@ class TimelineBuilder:
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
@@ -196,12 +205,14 @@ class TimelineBuilder:
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
@@ -215,7 +226,9 @@ class TimelineBuilder:
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
@@ -237,7 +250,7 @@ class TimelineBuilder:
                     st_src = stock_queue.popleft()
                     newly_used.append(st_src)
                 else:
-                    st_src = Path(f"stock_clip_{stock_cursor+1}.mp4")
+                    raise FileNotFoundError("F5 requires online-stock footage for full coverage")
 
                 stock_cursor += 1
                 segments.append(VisualSegment(
@@ -257,7 +270,9 @@ class TimelineBuilder:
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
@@ -283,11 +298,15 @@ class TimelineBuilder:
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
@@ -313,12 +332,16 @@ class TimelineBuilder:
 
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
 
@@ -350,9 +373,24 @@ class TimelineBuilder:
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
index 7ba70df..6ff5f9e 100644
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
@@ -217,6 +221,24 @@ class NvencRenderEngine:
         Supports rich atmospheric HUD for story formats (F4, F3, F2, F2-L) and clean stream composition for F1.
         """
         start_time = time.time()
+        from ...models import FormatId, create_default_format_plan
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
+            if expected and hashlib.sha256(segment.source_path.read_bytes()).hexdigest() != expected:
+                raise ValueError(f"Stale timeline lineage: source media changed for segment {segment.index}")
+        expected_audio = getattr(schedule, "audio_sha256", "")
+        if expected_audio and hashlib.sha256(Path(schedule.audio_path).read_bytes()).hexdigest() != expected_audio:
+            raise ValueError("Stale timeline lineage: narration audio changed since compose")
         output_path.parent.mkdir(parents=True, exist_ok=True)
         master_audio = audio_path or schedule.audio_path
         if not master_audio or not Path(master_audio).exists():
@@ -229,7 +251,40 @@ class NvencRenderEngine:
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
@@ -364,6 +419,7 @@ class NvencRenderEngine:
                 "index": s.index,
                 "type": s.segment_type,
                 "source_path": str(s.source_path),
+                "source_sha256": hashlib.sha256(Path(s.source_path).read_bytes()).hexdigest(),
                 "source_class": s_class_str,
                 "asset_id": getattr(s, "asset_id", "") or Path(s.source_path).stem,
                 "duration": s.duration
@@ -372,7 +428,7 @@ class NvencRenderEngine:
         from ...models import RunManifest
         fmt_val = format.upper() if isinstance(format, str) else (format.value if hasattr(format, "value") else str(format))
         story_name = schedule.story_dir.name if hasattr(schedule, "story_dir") and schedule.story_dir else "story"
-        fp_fp = getattr(format_plan, "format_plan_fingerprint", "") if format_plan else ""
+        fp_fp = getattr(format_plan, "fingerprint", "") if format_plan else ""
         manifest = RunManifest(
             run_id=f"run_{output_path.stem}",
             timestamp=datetime.utcnow().isoformat(),
@@ -386,7 +442,17 @@ class NvencRenderEngine:
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
+            }
         )
 
         manifest_path = output_path.parent / "run_manifest.json"
diff --git a/videopipeline/web/server.py b/videopipeline/web/server.py
index fee38ef..da4a98b 100644
--- a/videopipeline/web/server.py
+++ b/videopipeline/web/server.py
@@ -327,6 +327,12 @@ async def handle_action_compose(request):
     story_dir = Path(data.get("story_dir", ""))
     fmt_choice = data.get("format", "f2") # f2, f2-l, f3, f1
 
+    fmt_choice = str(fmt_choice).strip().lower()
+    if fmt_choice == "f2-l":
+        fmt_choice = "f2"
+    if fmt_choice not in {"f1", "f2", "f3", "f4", "f5"}:
+        return web.json_response({"status": "error", "message": f"Unsupported format {fmt_choice!r}; expected F1-F5"}, status=400)
+
     if not story_dir.exists():
         return web.json_response({"status": "error", "message": "Story not found"}, status=404)
 
@@ -371,13 +377,26 @@ async def handle_action_compose(request):
     tb = TimelineBuilder(story_dir, audios[0], total_dur)
     chap1_src = story_dir / "Final_Video_Export" / "Phase1_Prototype_3M.mp4"
     sched = tb.build_schedule(
-        chap1_source=chap1_src if chap1_src.exists() else None,
+        chap1_source=chap1_src if fmt_choice != "f4" and chap1_src.exists() else None,
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
@@ -406,6 +425,11 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
     """Asynchronously orchestrates all 4 pipeline stages from start to finish."""
     global PIPELINE_STATE
     try:
+        fmt_choice = str(fmt_choice).strip().lower()
+        if fmt_choice == "f2-l":
+            fmt_choice = "f2"
+        if fmt_choice not in {"f1", "f2", "f3", "f4", "f5"}:
+            raise ValueError(f"Unsupported format {fmt_choice!r}; expected F1-F5")
         log_event(f"============================================================")
         log_event(f"🚀 KÍCH HOẠT PIPELINE TOÀN DIỆN CHO: {story_dir.name}")
         log_event(f"   Format: {fmt_choice.upper()} | NVENC: {options.get('use_nvenc', True)} | QA: {options.get('auto_qa', True)}")
@@ -586,12 +610,13 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
         tb = TimelineBuilder(story_dir, chosen_audio, total_dur)
         chap1_src = story_dir / "Final_Video_Export" / "Phase1_Prototype_3M.mp4"
         sched = tb.build_schedule(
-            chap1_source=chap1_src if chap1_src.exists() else None,
+            chap1_source=chap1_src if fmt_choice != "f4" and chap1_src.exists() else None,
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
@@ -603,6 +628,16 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
 
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
@@ -658,10 +693,12 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
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
@@ -1039,12 +1076,13 @@ async def handle_get_schedule_segments(request):
             tb = TimelineBuilder(story_dir, audios[0], total_dur)
             chap1_src = story_dir / "Final_Video_Export" / "Phase1_Prototype_3M.mp4"
             sched = tb.build_schedule(
-                chap1_source=chap1_src if chap1_src.exists() else None,
+                chap1_source=chap1_src if fmt_choice != "f4" and chap1_src.exists() else None,
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

Return exactly READY or REPAIR: followed by one bounded repair brief. If no safe repair is possible, return NOT_READY with a reason.
