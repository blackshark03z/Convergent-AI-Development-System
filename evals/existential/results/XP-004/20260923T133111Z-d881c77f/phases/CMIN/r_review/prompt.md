You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-004 Reasoning Lead Prompt - C-min / Minimum CADS residue

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

Preserve only: material Outcome/Intent ambiguity must be bounded and testable; I DONE and R READY are not Product Acceptance; evidence must apply to the exact candidate; implementation authority does not grant external effects; assurance is proportional and unnecessary scaffolding should be omitted.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.


IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** Acceptance of each canonical F1–F5 format must prove that the selected format’s legal sources pass through the real plan, timeline, compose, and render path into the resulting video. Acceptance must identify the exact source assets, product state, and output that were verified.

**Acceptance:**

- Exercise all five formats with local, controlled media through the product path. Verify the rendered result against the selected sources, not only against schedule labels or a self-reported manifest: F1 has a generated-video opening and generated-image body; F2 has a generated-video opening plus both stock and generated video after it; F3 uses generated images throughout; F4 shows the original video as a readable inset over stock background; F5 uses stock footage throughout.
- Equivalent CLI and Web selections enforce the same format rules. Missing required media, unsupported selections, failed verification, and stale outputs cannot produce an accepted result or silently change format or source class.
- Acceptance evidence binds the selected format, identities of the actual media bytes, relevant plan/timeline/compose state, exact candidate code and configuration state, and final output bytes. Changing any bound input, product state, or output invalidates that acceptance.
- The evidence is reproducible for the exact candidate submitted to R. I DONE and R READY are handoff states, not Product Acceptance.

**Constraints:** Use isolated local media and verification. Do not call paid or external providers or the canonical production runtime. Implementation shape is open.

OWNER_INPUT_REQUIRED: no

I completion report:
**I DONE — candidate implementation ready for R review.** I am not claiming Product Acceptance.

The product path now records the selected format on the composed schedule, rejects unsupported or mismatched selections, and blocks rendering when required media or compose inputs are missing. Rendered segments are regenerated on each run to avoid stale normalized clips. F4 now composites the original video as an inset over the stock background. Run manifests bind the format policy, timeline, subtitles, audio, source asset bytes, candidate Python files, and final output; [acceptance.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/CMIN/videopipeline/acceptance.py) checks whether those bindings still match.

**Product-path evidence:** I rendered F1–F5 locally using generated color media and silence, then decoded representative frames. The checks matched F1’s generated-video opening and generated-image body; F2’s generated-video opening, stock interval, and generated-video body; both generated-image colors in F3; F4’s original-video inset and stock-colored exposed background; and F5’s stock footage.

**Checks run:** `py_compile` passed; the format grammar, timeline builder, and Web server suites passed (24 tests); `git diff --check` passed. No paid providers or production runtime were used.

**Known limitation:** The persistent manifest verifier checks byte and state bindings, but does not independently compare rendered frames with source media. The frame comparisons above were a local smoke exercise, not a durable acceptance record. CLI/Web end-to-end parity beyond these targeted checks, and real project media, remain unverified.

Candidate tree: 555e3445d0a26e37285408289bffcbd830d6b38d
Candidate status:
A  videopipeline/acceptance.py
M  videopipeline/cli.py
M  videopipeline/format_validator.py
M  videopipeline/models.py
M  videopipeline/stages/stage3_compose/timeline_builder.py
M  videopipeline/stages/stage4_render/nvenc_engine.py
M  videopipeline/web/server.py
Candidate diff:
diff --git a/videopipeline/acceptance.py b/videopipeline/acceptance.py
new file mode 100644
index 0000000..bcf9cb2
--- /dev/null
+++ b/videopipeline/acceptance.py
@@ -0,0 +1,48 @@
+"""Recheck byte-bound evidence emitted by a completed local render."""
+import hashlib
+import json
+from pathlib import Path
+from typing import Any, Dict, List
+
+
+def _file_hash(path: Path) -> str:
+    digest = hashlib.sha256()
+    with path.open("rb") as stream:
+        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
+            digest.update(chunk)
+    return digest.hexdigest()
+
+
+def verify_run_manifest(manifest_path: Path) -> Dict[str, Any]:
+    """Return valid only while all bound assets, state files, code, and output match."""
+    manifest_path = Path(manifest_path)
+    data = json.loads(manifest_path.read_text(encoding="utf-8"))
+    failures: List[str] = []
+
+    def check(path_text: str, expected: str, label: str) -> None:
+        path = Path(path_text) if path_text else None
+        if not path or not path.is_file():
+            failures.append(f"{label} missing: {path_text}")
+        elif not expected or _file_hash(path) != expected:
+            failures.append(f"{label} hash mismatch: {path_text}")
+
+    check(data.get("output_file", ""), data.get("output_sha256", ""), "output")
+    for asset in data.get("assets_used", []):
+        check(asset.get("source_path", ""), asset.get("sha256", ""), f"asset {asset.get('index')}")
+    state = data.get("product_state", {})
+    canonical_timeline = json.dumps(state.get("timeline_state"), sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
+    if hashlib.sha256(canonical_timeline).hexdigest() != state.get("timeline_sha256"):
+        failures.append("timeline state hash mismatch")
+    check(state.get("compose_path", ""), state.get("compose_sha256", ""), "compose state")
+    check(state.get("audio_path", ""), state.get("audio_sha256", ""), "audio")
+    if state.get("timeline_file_sha256"):
+        check(state.get("timeline_path", ""), state["timeline_file_sha256"], "timeline state")
+    package = Path(__file__).resolve().parent
+    digest = hashlib.sha256()
+    for source in sorted(package.rglob("*.py")):
+        digest.update(source.relative_to(package).as_posix().encode("utf-8"))
+        digest.update(_file_hash(source).encode("ascii"))
+    if digest.hexdigest() != state.get("candidate_sha256"):
+        failures.append("candidate code hash mismatch")
+    return {"valid": not failures, "failures": failures, "format_id": data.get("format_id"),
+            "output_file": data.get("output_file"), "output_sha256": data.get("output_sha256")}
diff --git a/videopipeline/cli.py b/videopipeline/cli.py
index b51124e..2580b51 100644
--- a/videopipeline/cli.py
+++ b/videopipeline/cli.py
@@ -154,7 +154,8 @@ def cmd_render(args):
 
     # Load schedule
     import json
-    from .models import TimelineSchedule, VisualSegment
+    from .models import TimelineSchedule, VisualSegment, FormatId, SourceClass, create_default_format_plan
+    from .format_validator import FormatValidator
     with open(sched_path, "r", encoding="utf-8") as f:
         data = json.load(f)
     segments = [
@@ -164,7 +165,9 @@ def cmd_render(args):
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
@@ -172,7 +175,16 @@ def cmd_render(args):
         story_dir=Path(data["story_dir"]),
         audio_path=Path(data["audio_path"]),
         total_duration=data["total_duration"],
-        segments=segments
+        segments=segments,
+        format_id=data.get("format_id", "")
+    )
+
+    fmt_text = getattr(args, "format", "f2").upper().replace("-L", "")
+    fmt_id = FormatId(fmt_text)
+    if data.get("format_id") != fmt_id.value:
+        raise ValueError(f"Selected format {fmt_id.value} does not match composed schedule {data.get('format_id')!r}; compose again")
+    FormatValidator.validate_timeline(
+        schedule.segments, create_default_format_plan(fmt_id), require_files=True
     )
 
     qc_verdict = data.get("editorial_qc_verdict", "PASS")
@@ -193,7 +205,7 @@ def cmd_render(args):
     print(f"[Render] Starting NVENC Render Engine...")
     print(f"[Render] Target Output: {out_file}")
     engine = NvencRenderEngine(work_dir)
-    metrics = engine.render_master_video(schedule, ass_path, out_file, format=getattr(args, "format", "f2"))
+    metrics = engine.render_master_video(schedule, ass_path, out_file, format=fmt_id.value.lower())
     print(f"[Render] COMPLETE!")
     print(f"  Duration: {metrics.duration_sec:.2f}s")
     print(f"  File Size: {metrics.file_size_bytes:,} bytes")
diff --git a/videopipeline/format_validator.py b/videopipeline/format_validator.py
index 9d5241b..f154fdc 100644
--- a/videopipeline/format_validator.py
+++ b/videopipeline/format_validator.py
@@ -3,6 +3,7 @@ Format Grammar Validator for AutoVideoPipeline.
 Strictly enforces the canonical Five Formats (F1-F5) source grammar and failure matrix.
 Raises FORMAT_GRAMMAR_VIOLATION on any source class or structure breach.
 """
+from pathlib import Path
 from typing import List, Dict, Any, Optional
 from .models import FormatId, SourceClass, FormatPlan, VisualSegment, LayoutProfile
 
@@ -19,7 +20,7 @@ class FormatValidator:
     """
 
     @staticmethod
-    def validate_timeline(segments: List[VisualSegment], format_plan: FormatPlan) -> Dict[str, Any]:
+    def validate_timeline(segments: List[VisualSegment], format_plan: FormatPlan, *, require_files: bool = False) -> Dict[str, Any]:
         """
         Validates the visual segments against the FormatPlan grammar.
         Raises FORMAT_GRAMMAR_VIOLATION on any breach.
@@ -27,6 +28,14 @@ class FormatValidator:
         if not segments:
             raise FORMAT_GRAMMAR_VIOLATION("Timeline is empty. Full visual coverage is required.")
 
+        if require_files:
+            for seg in segments:
+                path = Path(seg.source_path)
+                if not path.is_file() or path.stat().st_size == 0:
+                    raise FORMAT_GRAMMAR_VIOLATION(
+                        f"Required media is missing or empty at segment {seg.index}: {path}"
+                    )
+
         fmt = format_plan.format_id
 
         # Normalize segment source class mapping
@@ -175,6 +184,10 @@ class FormatValidator:
         has_original = any(seg.source_class == SourceClass.ORIGINAL_REUP_VIDEO for seg in segments)
         if not has_original:
             raise FORMAT_GRAMMAR_VIOLATION("F4 Reup requires an ORIGINAL_REUP_VIDEO source file.")
+        if not any(seg.source_class == SourceClass.STOCK_ONLINE for seg in segments):
+            raise FORMAT_GRAMMAR_VIOLATION("F4 Reup requires a STOCK_ONLINE background source.")
+        if any(seg.source_class not in (SourceClass.ORIGINAL_REUP_VIDEO, SourceClass.STOCK_ONLINE) for seg in segments):
+            raise FORMAT_GRAMMAR_VIOLATION("F4 allows only ORIGINAL_REUP_VIDEO and STOCK_ONLINE sources.")
 
         return {"valid": True, "format": "F4", "layout_id": layout.layout_id}
 
diff --git a/videopipeline/models.py b/videopipeline/models.py
index 989a603..b308d92 100644
--- a/videopipeline/models.py
+++ b/videopipeline/models.py
@@ -371,12 +371,14 @@ class TimelineSchedule:
     audio_path: Path
     total_duration: float
     segments: List[VisualSegment] = field(default_factory=list)
+    format_id: str = ""
 
     def to_dict(self) -> Dict[str, Any]:
         return {
             "story_dir": str(self.story_dir),
             "audio_path": str(self.audio_path),
             "total_duration": round(self.total_duration, 2),
+            "format_id": self.format_id,
             "segment_count": len(self.segments),
             "segments": [s.to_dict() for s in self.segments]
         }
@@ -485,6 +487,7 @@ class RunManifest:
     output_file: str = ""
     output_sha256: str = ""
     assets_used: List[Dict[str, Any]] = field(default_factory=list)
+    product_state: Dict[str, Any] = field(default_factory=dict)
     redacted: bool = True
 
     def to_dict(self) -> Dict[str, Any]:
diff --git a/videopipeline/stages/stage3_compose/timeline_builder.py b/videopipeline/stages/stage3_compose/timeline_builder.py
index 6918171..9d411c3 100644
--- a/videopipeline/stages/stage3_compose/timeline_builder.py
+++ b/videopipeline/stages/stage3_compose/timeline_builder.py
@@ -63,7 +63,7 @@ class TimelineBuilder:
             elif fmt_str == "F2-L":
                 fmt_id = FormatId.F2
             else:
-                fmt_id = FormatId.F2
+                raise ValueError(f"Unsupported format: {format}")
             format_plan = create_default_format_plan(fmt_id)
 
         # ── Filter out globally-used clips ──
@@ -348,7 +348,8 @@ class TimelineBuilder:
             story_dir=self.story_dir,
             audio_path=self.audio_path,
             total_duration=self.total_duration,
-            segments=segments
+            segments=segments,
+            format_id=fmt_id.value
         )
 
         # Validate grammar
diff --git a/videopipeline/stages/stage4_render/nvenc_engine.py b/videopipeline/stages/stage4_render/nvenc_engine.py
index 7ba70df..9a38991 100644
--- a/videopipeline/stages/stage4_render/nvenc_engine.py
+++ b/videopipeline/stages/stage4_render/nvenc_engine.py
@@ -37,7 +37,8 @@ class NvencRenderEngine:
         is_loop: bool = False,
         segment_type: str = "",
         start_time: float = 0.0,
-        layout_profile: Optional[LayoutProfile] = None
+        layout_profile: Optional[LayoutProfile] = None,
+        background_path: Optional[Path] = None
     ) -> bool:
         """
         Normalizes a single visual segment to 1920x1080 @ 30.0 fps closed GOP via NVENC.
@@ -63,15 +64,17 @@ class NvencRenderEngine:
                 fg_w = layout_profile.foreground_width if layout_profile else 1536
                 fg_h = layout_profile.foreground_height if layout_profile else 864
                 bg_blur = layout_profile.background_blur if layout_profile else 25
+                bg_input = 1 if background_path else 0
                 filter_complex = (
-                    f"[0:v]split=2[bg_in][fg_in];"
-                    f"[bg_in]scale={DEFAULT_WIDTH}:{DEFAULT_HEIGHT}:force_original_aspect_ratio=increase,"
+                    f"[{bg_input}:v]scale={DEFAULT_WIDTH}:{DEFAULT_HEIGHT}:force_original_aspect_ratio=increase,"
                     f"crop={DEFAULT_WIDTH}:{DEFAULT_HEIGHT},boxblur={bg_blur}:5[bg];"
-                    f"[fg_in]scale={fg_w}:{fg_h}:force_original_aspect_ratio=decrease[fg];"
+                    f"[0:v]scale={fg_w}:{fg_h}:force_original_aspect_ratio=decrease[fg];"
                     f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps={DEFAULT_FPS}[outv]"
                 )
                 filter_map = "[outv]"
                 input_args = ["-ss", f"{start_time:.3f}", "-i", str(p)] if start_time > 0 else ["-i", str(p)]
+                if background_path:
+                    input_args.extend(["-stream_loop", "-1", "-i", str(background_path)])
             elif segment_type == "f1_fullscreen":
                 input_args = ["-ss", f"{start_time:.3f}", "-i", str(p)] if start_time > 0 else ["-i", str(p)]
             elif is_image or segment_type == "slideshow":
@@ -172,7 +175,10 @@ class NvencRenderEngine:
         Pre-renders all visual segments in the schedule into the work directory.
         """
         normalized_paths: List[Path] = []
+        f4_bg = next((s.source_path for s in schedule.segments if s.segment_type == "stock"), None)
         for seg in schedule.segments:
+            if seg.segment_type == "stock" and f4_bg and any(s.segment_type == "f1_framed" for s in schedule.segments):
+                continue
             out_file = self.segments_dir / f"seg_{seg.index:03d}_{seg.segment_type}.mp4"
             is_opening = (seg.index < 6)
             needs_render = force or (is_opening and force_opening) or (not out_file.exists()) or (out_file.stat().st_size < 10000)
@@ -194,7 +200,8 @@ class NvencRenderEngine:
                     is_loop=is_loop,
                     segment_type=seg.segment_type,
                     start_time=seg.start_time,
-                    layout_profile=layout_profile
+                    layout_profile=layout_profile,
+                    background_path=f4_bg if seg.segment_type == "f1_framed" else None
                 )
                 if not success:
                     raise RuntimeError(f"Failed to normalize segment {seg.index}: {seg.source_path}")
@@ -218,6 +225,20 @@ class NvencRenderEngine:
         """
         start_time = time.time()
         output_path.parent.mkdir(parents=True, exist_ok=True)
+        from ...models import FormatId, create_default_format_plan
+        from ...format_validator import FormatValidator
+        try:
+            selected_format = FormatId(str(format).upper().replace("-L", ""))
+        except ValueError as exc:
+            raise ValueError(f"Unsupported format: {format}") from exc
+        if schedule.format_id != selected_format.value:
+            raise ValueError(
+                f"Selected format {selected_format.value} does not match composed schedule {schedule.format_id!r}"
+            )
+        strict_plan = format_plan or create_default_format_plan(selected_format)
+        FormatValidator.validate_timeline(schedule.segments, strict_plan, require_files=True)
+        if not ass_path or not Path(ass_path).is_file() or Path(ass_path).stat().st_size == 0:
+            raise FileNotFoundError(f"Required compose subtitles missing: {ass_path}")
         master_audio = audio_path or schedule.audio_path
         if not master_audio or not Path(master_audio).exists():
             # Auto-detect audio from story directory
@@ -227,9 +248,13 @@ class NvencRenderEngine:
                 if audios:
                     master_audio = audios[0]
                     break
+        if not master_audio or not Path(master_audio).is_file():
+            raise FileNotFoundError(f"Required render audio missing: {master_audio}")
 
         # 1. Normalize all segments
-        seg_paths = self.normalize_all_segments(schedule)
+        seg_paths = self.normalize_all_segments(
+            schedule, force=True, force_opening=True, layout_profile=strict_plan.layout_profile
+        )
 
         # 2. Write concat file
         concat_file = self.work_dir / "concat_segments.txt"
@@ -360,13 +385,15 @@ class NvencRenderEngine:
         for s in schedule.segments:
             s_class = getattr(s, "source_class", None)
             s_class_str = s_class.value if hasattr(s_class, "value") else (str(s_class) if s_class else "UNKNOWN")
+            asset_path = Path(s.source_path)
             assets_used.append({
                 "index": s.index,
                 "type": s.segment_type,
                 "source_path": str(s.source_path),
                 "source_class": s_class_str,
                 "asset_id": getattr(s, "asset_id", "") or Path(s.source_path).stem,
-                "duration": s.duration
+                "duration": s.duration,
+                "sha256": self._sha256_file(asset_path)
             })
 
         from ...models import RunManifest
@@ -386,7 +413,24 @@ class NvencRenderEngine:
             owner_disposition=getattr(schedule, "owner_disposition", "AUTO"),
             output_file=str(output_path),
             output_sha256=out_sha256,
-            assets_used=assets_used
+            assets_used=assets_used,
+            product_state={
+                "format_plan": {
+                    "format_id": selected_format.value,
+                    "fingerprint": strict_plan.fingerprint,
+                    "source_policy": strict_plan.source_policy,
+                    "layout": vars(strict_plan.layout_profile) if strict_plan.layout_profile else None,
+                },
+                "timeline_state": schedule.to_dict(),
+                "timeline_sha256": self._sha256_json(schedule.to_dict()),
+                "timeline_path": str(self.work_dir / "video_schedule.json"),
+                "timeline_file_sha256": self._sha256_file(self.work_dir / "video_schedule.json") if (self.work_dir / "video_schedule.json").is_file() else "",
+                "compose_sha256": self._sha256_file(Path(ass_path)),
+                "compose_path": str(Path(ass_path).resolve()),
+                "audio_sha256": self._sha256_file(Path(master_audio)),
+                "audio_path": str(Path(master_audio).resolve()),
+                "candidate_sha256": self._candidate_sha256(),
+            }
         )
 
         manifest_path = output_path.parent / "run_manifest.json"
@@ -405,6 +449,28 @@ class NvencRenderEngine:
             average_encoding_fps=avg_fps
         )
 
+    @staticmethod
+    def _sha256_file(path: Path) -> str:
+        digest = hashlib.sha256()
+        with open(path, "rb") as handle:
+            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
+                digest.update(chunk)
+        return digest.hexdigest()
+
+    @staticmethod
+    def _sha256_json(value: Any) -> str:
+        payload = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
+        return hashlib.sha256(payload).hexdigest()
+
+    @staticmethod
+    def _candidate_sha256() -> str:
+        package = Path(__file__).resolve().parents[2]
+        digest = hashlib.sha256()
+        for source in sorted(package.rglob("*.py")):
+            digest.update(source.relative_to(package).as_posix().encode("utf-8"))
+            digest.update(NvencRenderEngine._sha256_file(source).encode("ascii"))
+        return digest.hexdigest()
+
     def render(
         self,
         schedule_or_path: Any,
@@ -443,7 +509,8 @@ class NvencRenderEngine:
                 story_dir=story_dir,
                 audio_path=aud_path,
                 total_duration=tot_dur,
-                segments=segments
+                segments=segments,
+                format_id=data.get("format_id", "") if isinstance(data, dict) else ""
             )
         else:
             schedule = schedule_or_path
diff --git a/videopipeline/web/server.py b/videopipeline/web/server.py
index fee38ef..9a5ca0c 100644
--- a/videopipeline/web/server.py
+++ b/videopipeline/web/server.py
@@ -601,13 +601,16 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
         from ..format_validator import FormatValidator
         from ..stages.stage3_compose.editorial_qc import EditorialQC
 
-        format_id_enum = FormatId(fmt_choice.upper()) if hasattr(FormatId, fmt_choice.upper()) else FormatId.F2
+        try:
+            format_id_enum = FormatId(fmt_choice.upper().replace("-L", ""))
+        except ValueError as exc:
+            raise ValueError(f"Unsupported format: {fmt_choice}") from exc
         format_plan = create_default_format_plan(format_id_enum)
         run_req = RunRequest(story_dir=story_dir, format_id=format_id_enum, format_plan=format_plan, options=options)
 
         # Format Grammar Validation
         try:
-            FormatValidator.validate_timeline(sched.segments, format_plan)
+            FormatValidator.validate_timeline(sched.segments, format_plan, require_files=True)
         except Exception as fve:
             log_event(f"❌ [Stage 3 FormatValidator] Vi phạm quy tắc định dạng: {fve}")
             raise
@@ -658,7 +661,7 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
             except Exception:
                 pass
 
-        if (not master_file.exists() or force_rerender) and not dry_run:
+        if not dry_run:
             log_event(f"[Stage 4 Render] Bắt đầu render video master qua NVIDIA NVENC...")
             engine = NvencRenderEngine(work_dir)
             engine.render(sched, ass_path, master_file, format=fmt_choice)
@@ -728,6 +731,11 @@ async def handle_action_run_pipeline(request):
     dry_run = data.get("dry_run", False)
 
     story_dir = Path(story_dir_str)
+    try:
+        from ..models import FormatId
+        FormatId(str(fmt_choice).upper().replace("-L", ""))
+    except ValueError:
+        return web.json_response({"status": "error", "message": f"Unsupported format: {fmt_choice}"}, status=400)
     if not story_dir.exists():
         return web.json_response({"status": "error", "message": "Thư mục câu chuyện không tồn tại"}, status=404)

Return exactly READY or REPAIR: followed by one bounded repair brief. If no safe repair is possible, return NOT_READY with a reason.
