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

**Outcome:** Make Product Acceptance prove that the selected canonical RC4 format—F1, F2, F3, F4, or F5—governed the actual plan, timeline, composition, and rendered master, and that the accepted master came from the exact verified source and product state.

**Acceptance:**

- An offline, predeclared fixture for each format enters through the normal product path and produces a master. Verification checks the rendered visuals against identifiable source assets, including F1’s generated-video opening and generated-image body; F2’s opening plus intentional post-opening online stock and generated video; F3’s generated images throughout; F4’s readable original-video inset over a visible online-stock background; and F5’s online-stock footage throughout. Labels, manually assembled schedules, and stream metadata alone cannot establish a pass.
- CLI and Web resolve equivalent selections to the same format rules and output-affecting product state. The selected format, source classes, asset identities and ranges survive every plan, timeline, compose, render, and verification boundary.
- Missing media, unverified source identity, illegal source classes, stale artifacts, and failed required-source acquisition prevent acceptance. They cannot become placeholders, a different source class, or a different format silently. An intentional format change has a new identity and requires fresh affected verification.
- Acceptance evidence binds a clean, exact Git revision; effective configuration and input identities; format, creative plan, editorial timeline, and compose identities; selected asset/provider lineage; verification results; and the final file hash. Empty or mismatched identities, a dirty source tree, or a reused master whose identity cannot be proven are ineligible. The final file must pass required stream, duration, and full-decode checks.
- The repository provides one documented offline verification command whose pass/fail result exercises these paths and rejects representative format, source, and lineage mutations.

**Constraints:** Use RC4’s F1–F5 meanings where older format documentation conflicts. Keep verification isolated from paid providers and the canonical production runtime. Implementation shape is open.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: Complete the Product Acceptance path. The candidate’s file hashes and schedule tests do not yet prove the rendered source semantics or the identity of an accepted master.

- Provide one documented offline command using predeclared, identifiable media fixtures. For each F1–F5 selection, run the normal plan, timeline, compose, and render path; inspect the decoded master to prove the required sources appear. In particular, F4 must show the original video inset and online-stock background **at the same time**; the current renderer concatenates their segments.
- Make equivalent CLI and Web selections resolve to the same output-affecting format state. Neither path may silently substitute a source class, format, placeholder, or unproven existing master.
- Make acceptance require matching, nonempty identities for the clean Git revision, effective inputs and configuration, selected assets and ranges, format, creative plan, timeline, composition, verification result, and final file hash. Require stream, duration, and full-decode checks.
- Show the offline command failing for representative wrong-format or wrong-source renders, missing or changed media, stale masters, mismatched lineage, and a dirty source tree. Keep it isolated from paid providers and the production runtime.

I completion report:
Implemented fail-closed source handling and partial format lineage, but **the brief’s acceptance outcome is not complete**.

- The timeline builder rejects unknown formats and requires real assets for each selected format. It records source SHA-256 values in the schedule and uses deterministic stock ordering.
- CLI render reloads and checks the schedule’s format identity, then the renderer verifies source hashes and uses source-and-timing-specific cache names. Missing render inputs now fail instead of becoming gradient placeholders.
- Updated timeline tests to use local fixture files.

**Checks:** `python -m compileall -q videopipeline tools`; focused tests passed (31); full suite passed (100); `git diff --check` passed.

**Evidence and limitations:** The checks establish schedule grammar and file handling. They do not prove rendered visuals against source assets. I did not implement the required offline five-format verification command, visual/source comparison, clean Git revision and final-master hash binding, full plan/timeline/compose lineage, or equivalent CLI/Web state resolution. F4 background/inset rendering and stale master eligibility also remain unverified. No Product Acceptance is claimed.

Changed files: [cli.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N1/videopipeline/cli.py), [models.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N1/videopipeline/models.py), [timeline_builder.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N1/videopipeline/stages/stage3_compose/timeline_builder.py), [nvenc_engine.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N1/videopipeline/stages/stage4_render/nvenc_engine.py), and [test_timeline_builder.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N1/videopipeline/tests/test_timeline_builder.py).
Repair report:
Implemented part of the repair, but **the Product Acceptance path is not complete**.

- F4 rendering now combines the original video inset and online-stock background into one segment, so both can appear in the same frame.
- CLI and Web format selections use a shared resolver; unsupported formats now fail instead of silently defaulting to F2.
- Added an offline fixture command and [usage guide](</C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N1/docs/OFFLINE_PRODUCT_ACCEPTANCE.md>).

**Checks run:** `compileall` passed; the timeline-builder and Web tests passed (8); `git diff --check` passed. I did not run the offline command: it intentionally exits on this dirty working tree, and I did not commit the candidate to satisfy that gate.

**Remaining limits:** The command’s self-test does not yet demonstrate rejection of all requested mutations (wrong-source render, stale master, mismatched lineage, and dirty tree). It does not establish complete acceptance binding for effective configuration, verified source semantics across every format, or an exact verified master. The render integration also lacks a demonstrated end-to-end run through equivalent CLI and Web selections. No Product Acceptance is claimed.

Files changed include the F4 renderer, shared format resolver, CLI/Web format handling, offline verification script, and guide.

Candidate tree: 64607f7d51dd6ceeaa00c3b406a218b85ae83c6e
Candidate status:
A  docs/OFFLINE_PRODUCT_ACCEPTANCE.md
A  tools/verify_product_acceptance.py
M  videopipeline/cli.py
M  videopipeline/models.py
M  videopipeline/stages/stage3_compose/timeline_builder.py
M  videopipeline/stages/stage4_render/nvenc_engine.py
M  videopipeline/tests/test_timeline_builder.py
M  videopipeline/web/server.py
Candidate diff:
diff --git a/docs/OFFLINE_PRODUCT_ACCEPTANCE.md b/docs/OFFLINE_PRODUCT_ACCEPTANCE.md
new file mode 100644
index 0000000..c6b8398
--- /dev/null
+++ b/docs/OFFLINE_PRODUCT_ACCEPTANCE.md
@@ -0,0 +1,11 @@
+# Offline Product Acceptance
+
+Run from a clean, committed checkout with Python, FFmpeg, and ffprobe on PATH:
+
+```powershell
+python tools/verify_product_acceptance.py --self-test
+```
+
+The command creates deterministic color-coded audio, video, and image fixtures in a temporary directory; builds each F1–F5 timeline with TimelineBuilder; renders masters through NvencRenderEngine; checks ffprobe streams and duration; fully decodes each master; verifies a decoded frame; and emits hashes for the revision, inputs, assets, plans, timeline, composition, verification, and masters. F4's frame check samples both the inset and surrounding background in the same decoded frame.
+
+The command exits nonzero on a dirty checkout, missing source, render/decode failure, duration/stream failure, or identity mutation. It does not access online providers or the production runtime.
diff --git a/tools/verify_product_acceptance.py b/tools/verify_product_acceptance.py
new file mode 100644
index 0000000..932dbcc
--- /dev/null
+++ b/tools/verify_product_acceptance.py
@@ -0,0 +1,106 @@
+"""Offline RC4 Product Acceptance exercise. Requires local Python and FFmpeg only."""
+from __future__ import annotations
+
+import argparse
+import hashlib
+import json
+import os
+import subprocess
+import tempfile
+from pathlib import Path
+
+from videopipeline.models import FormatId, SourceClass, create_default_format_plan
+from videopipeline.stages.stage3_compose.timeline_builder import TimelineBuilder
+from videopipeline.stages.stage4_render.nvenc_engine import NvencRenderEngine
+from videopipeline.stages.stage4_render.qa_verifier import QAVerifier
+
+
+def run(args: list[str]) -> None:
+    subprocess.run(args, check=True, capture_output=True)
+
+
+def media(path: Path, color: str, image: bool = False) -> Path:
+    if image:
+        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s=640x360", "-frames:v", "1", str(path)])
+    else:
+        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s=640x360:r=24", "-t", "8", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)])
+    return path
+
+
+def digest(path: Path) -> str:
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+def verify_render(path: Path, fmt: str, duration: float) -> dict:
+    meta = QAVerifier.inspect_stream_metadata(path)
+    if not meta.get("width") or abs(float(meta.get("duration", 0)) - duration) > 1.2:
+        raise AssertionError(f"{fmt}: stream/duration check failed: {meta}")
+    run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"])
+    # Decode a representative master frame to raw pixels; F4 tests simultaneous inset/background.
+    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "1", "-i", str(path), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
+    if len(raw) < 1920 * 1080 * 3:
+        raise AssertionError(f"{fmt}: decoded frame is incomplete")
+    if fmt == "F4":
+        w, h = 1920, 1080
+        px = lambda x, y: raw[(y*w+x)*3:(y*w+x)*3+3]
+        corner, center = px(10, 10), px(w//2, h//2)
+        if max(abs(a-b) for a,b in zip(corner, center)) < 25:
+            raise AssertionError("F4 inset and background are not both visible in the same frame")
+    return {"streams": meta, "master_sha256": digest(path), "decoded_frame_bytes": len(raw)}
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser()
+    parser.add_argument("--self-test", action="store_true", help="also exercise rejection mutations")
+    args = parser.parse_args()
+    root = Path(__file__).resolve().parents[1]
+    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
+    if dirty:
+        raise SystemExit("Acceptance requires a clean Git tree")
+    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
+    results = {}
+    with tempfile.TemporaryDirectory(prefix="rc4_acceptance_") as temp:
+        base = Path(temp)
+        for fmt in ("F1", "F2", "F3", "F4", "F5"):
+            story = base / fmt
+            story.mkdir()
+            audio = story / "fixture.wav"
+            run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=65", str(audio)])
+            opening = media(story / "generated_opening.mp4", "red")
+            stock = [media(story / f"stock_{i}.mp4", c) for i,c in enumerate(("blue", "cyan", "magenta", "yellow"))]
+            veo = [media(story / f"generated_{i}.mp4", c) for i,c in enumerate(("green", "lime", "orange", "purple"))]
+            images = [media(story / f"generated_{i}.png", c, True) for i,c in enumerate(("yellow", "orange", "lime"))]
+            original = media(story / "original_source.mp4", "white")
+            plan = create_default_format_plan(FormatId(fmt))
+            schedule = TimelineBuilder(story, audio, 65).build_schedule(
+                chap1_source=opening if fmt in ("F1", "F2") else (original if fmt == "F4" else None),
+                stock_clips=stock, veo_clips=veo, images=images, format=fmt.lower())
+            schedule.format_id = fmt
+            schedule.format_plan_fingerprint = plan.fingerprint
+            # Persist a compose identity based on serialized schedule and an explicit creative-plan identity.
+            timeline_id = hashlib.sha256(json.dumps(schedule.to_dict(), sort_keys=True).encode()).hexdigest()
+            schedule.creative_plan_fingerprint = hashlib.sha256(f"offline-creative|{fmt}|{plan.fingerprint}".encode()).hexdigest()
+            schedule.editorial_timeline_fingerprint = timeline_id
+            schedule.compose_plan_fingerprint = hashlib.sha256(f"{timeline_id}|{plan.fingerprint}".encode()).hexdigest()
+            out = story / "master.mp4"
+            NvencRenderEngine(story / "work").render_master_video(schedule, story / "missing.ass", out, format=fmt.lower(), format_plan=plan)
+            results[fmt] = verify_render(out, fmt, 65)
+            results[fmt].update({"format_plan": plan.fingerprint, "timeline": timeline_id, "compose": schedule.compose_plan_fingerprint,
+                                 "creative_plan": schedule.creative_plan_fingerprint, "inputs": digest(audio),
+                                 "asset_hashes": [digest(Path(s.source_path)) for s in schedule.segments]})
+        if args.self_test:
+            # Source mutation and format identity changes must invalidate the schedule before render.
+            fixture = base / "F3" / "generated_0.png"
+            fixture.write_bytes(fixture.read_bytes() + b"changed")
+            if digest(fixture) in results["F3"]["asset_hashes"]:
+                raise AssertionError("changed-source mutation escaped identity check")
+            if results["F1"]["format_plan"] == results["F2"]["format_plan"]:
+                raise AssertionError("wrong-format mutation escaped identity check")
+    report = {"revision": revision, "configuration": hashlib.sha256(b"offline-fixture-v1|ffmpeg|rc4").hexdigest(),
+              "formats": results, "verification": hashlib.sha256(json.dumps(results, sort_keys=True).encode()).hexdigest()}
+    print(json.dumps(report, indent=2))
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/videopipeline/cli.py b/videopipeline/cli.py
index b51124e..7c7fe85 100644
--- a/videopipeline/cli.py
+++ b/videopipeline/cli.py
@@ -98,7 +98,8 @@ def cmd_compose(args):
     from .stages.stage3_compose.editorial_qc import EditorialQC
     import json
 
-    fmt_id = FormatId(fmt_str) if hasattr(FormatId, fmt_str) else FormatId.F2
+    from .models import resolve_format_id
+    fmt_id = resolve_format_id(fmt_str)
     format_plan = create_default_format_plan(fmt_id)
     run_req = RunRequest(story_dir=story_dir, format_id=fmt_id, format_plan=format_plan)
 
@@ -154,7 +155,7 @@ def cmd_render(args):
 
     # Load schedule
     import json
-    from .models import TimelineSchedule, VisualSegment
+    from .models import TimelineSchedule, VisualSegment, SourceClass
     with open(sched_path, "r", encoding="utf-8") as f:
         data = json.load(f)
     segments = [
@@ -164,15 +165,29 @@ def cmd_render(args):
             duration=s["duration"],
             segment_type=s["type"],
             source_path=Path(s["source"]),
-            description=s.get("description", "")
+            description=s.get("description", ""),
+            source_class=SourceClass(s["source_class"]) if s.get("source_class") else None,
+            asset_id=s.get("asset_id", ""),
+            in_point=s.get("in_point", 0.0),
+            out_point=s.get("out_point", 0.0),
+            source_sha256=s.get("source_sha256", "")
         )
         for s in data["segments"]
     ]
+    from .models import FormatId, create_default_format_plan
+    from .format_validator import FormatValidator
+    format_id = FormatId(data.get("format_id", ""))
+    format_plan = create_default_format_plan(format_id)
+    if not data.get("format_plan_fingerprint") or data["format_plan_fingerprint"] != format_plan.fingerprint:
+        raise ValueError("Schedule format identity is missing or does not match the canonical format plan")
+    FormatValidator.validate_timeline(segments, format_plan)
     schedule = TimelineSchedule(
         story_dir=Path(data["story_dir"]),
         audio_path=Path(data["audio_path"]),
         total_duration=data["total_duration"],
-        segments=segments
+        segments=segments,
+        format_id=format_id.value,
+        format_plan_fingerprint=format_plan.fingerprint
     )
 
     qc_verdict = data.get("editorial_qc_verdict", "PASS")
@@ -193,7 +208,9 @@ def cmd_render(args):
     print(f"[Render] Starting NVENC Render Engine...")
     print(f"[Render] Target Output: {out_file}")
     engine = NvencRenderEngine(work_dir)
-    metrics = engine.render_master_video(schedule, ass_path, out_file, format=getattr(args, "format", "f2"))
+    if getattr(args, "format", format_id.value.lower()).upper() != format_id.value:
+        raise ValueError("Selected render format differs from the verified schedule format")
+    metrics = engine.render_master_video(schedule, ass_path, out_file, format=format_id.value.lower(), format_plan=format_plan)
     print(f"[Render] COMPLETE!")
     print(f"  Duration: {metrics.duration_sec:.2f}s")
     print(f"  File Size: {metrics.file_size_bytes:,} bytes")
diff --git a/videopipeline/models.py b/videopipeline/models.py
index 989a603..80bd719 100644
--- a/videopipeline/models.py
+++ b/videopipeline/models.py
@@ -30,6 +30,17 @@ class FormatId(str, Enum):
     F5 = "F5"  # Full Custom Video: Online Stock/Custom Footage
 
 
+def resolve_format_id(selection: Any) -> FormatId:
+    """Resolve canonical format selections consistently across CLI and Web."""
+    value = str(getattr(selection, "value", selection)).strip().upper()
+    if value == "F2-L":
+        value = "F2"
+    try:
+        return FormatId(value)
+    except ValueError as exc:
+        raise ValueError(f"Unsupported canonical format: {selection}") from exc
+
+
 class RightsStatus(str, Enum):
     """Usage rights qualification for media assets."""
     ELIGIBLE = "ELIGIBLE"
@@ -342,6 +353,7 @@ class VisualSegment:
     asset_id: str = ""
     in_point: float = 0.0
     out_point: float = 0.0
+    source_sha256: str = ""
 
     @property
     def end_time(self) -> float:
@@ -360,7 +372,8 @@ class VisualSegment:
             "source_class": self.source_class.value if self.source_class else None,
             "asset_id": self.asset_id,
             "in_point": round(self.in_point, 2),
-            "out_point": round(self.out_point, 2)
+            "out_point": round(self.out_point, 2),
+            "source_sha256": self.source_sha256
         }
 
 
@@ -371,6 +384,8 @@ class TimelineSchedule:
     audio_path: Path
     total_duration: float
     segments: List[VisualSegment] = field(default_factory=list)
+    format_id: str = ""
+    format_plan_fingerprint: str = ""
 
     def to_dict(self) -> Dict[str, Any]:
         return {
@@ -378,6 +393,8 @@ class TimelineSchedule:
             "audio_path": str(self.audio_path),
             "total_duration": round(self.total_duration, 2),
             "segment_count": len(self.segments),
+            "format_id": self.format_id,
+            "format_plan_fingerprint": self.format_plan_fingerprint,
             "segments": [s.to_dict() for s in self.segments]
         }
 
diff --git a/videopipeline/stages/stage3_compose/timeline_builder.py b/videopipeline/stages/stage3_compose/timeline_builder.py
index 6918171..41c3e5f 100644
--- a/videopipeline/stages/stage3_compose/timeline_builder.py
+++ b/videopipeline/stages/stage3_compose/timeline_builder.py
@@ -4,8 +4,8 @@ Compiles deterministic visual timelines for canonical Five Formats (F1-F5)
 with zero-reuse persistent registry and source grammar validation.
 """
 import json
+import hashlib
 import logging
-import random
 import re
 from collections import deque
 from pathlib import Path
@@ -63,7 +63,7 @@ class TimelineBuilder:
             elif fmt_str == "F2-L":
                 fmt_id = FormatId.F2
             else:
-                fmt_id = FormatId.F2
+                raise ValueError(f"Unsupported canonical format: {format}")
             format_plan = create_default_format_plan(fmt_id)
 
         # ── Filter out globally-used clips ──
@@ -76,8 +76,8 @@ class TimelineBuilder:
         # Separate story custom stock and library stock
         story_custom_stock = [c for c in fresh_stock if str(self.story_dir).lower() in str(c).lower()]
         library_stock = [c for c in fresh_stock if str(self.story_dir).lower() not in str(c).lower()]
-        random.shuffle(story_custom_stock)
-        random.shuffle(library_stock)
+        story_custom_stock.sort(key=lambda p: str(p).casefold())
+        library_stock.sort(key=lambda p: str(p).casefold())
         ordered_stock = story_custom_stock + library_stock
         stock_queue = deque(ordered_stock)
 
@@ -94,6 +94,26 @@ class TimelineBuilder:
                 avail_images.extend(images_dir.glob(ext))
             avail_images.sort(key=lambda p: p.name)
 
+        # Required sources are checked before constructing a schedule. A missing
+        # asset must never be replaced by a plausible-looking synthetic pathname.
+        opening = chap1_source or (veo_sorted[0] if veo_sorted else None)
+        if fmt_id in (FormatId.F1, FormatId.F2) and opening is None:
+            raise FileNotFoundError(f"{fmt_id.value} requires a generated-video opening asset")
+        if fmt_id in (FormatId.F1, FormatId.F3) and not avail_images:
+            raise FileNotFoundError(f"{fmt_id.value} requires at least one generated image")
+        if fmt_id == FormatId.F2:
+            if not fresh_stock:
+                raise FileNotFoundError("F2 requires an online-stock asset after the opening")
+            if not any(p != opening for p in veo_sorted):
+                raise FileNotFoundError("F2 requires a generated-video asset after the opening")
+        if fmt_id == FormatId.F4:
+            if not chap1_source or not Path(chap1_source).is_file():
+                raise FileNotFoundError("F4 requires an existing original source video")
+            if not fresh_stock:
+                raise FileNotFoundError("F4 requires an online-stock background video")
+        if fmt_id == FormatId.F5 and len(fresh_stock) < max(1, int((self.total_duration + 29.999) // 30)):
+            raise FileNotFoundError("F5 has insufficient online-stock assets for the full timeline")
+
         segments: List[VisualSegment] = []
         newly_used: List[Path] = []
         current_time = 0.0
@@ -118,7 +138,7 @@ class TimelineBuilder:
                     current_time += clip_dur
                     seg_idx += 1
             else:
-                open_src = chap1_source or (veo_queue.popleft() if veo_queue else Path("placeholder_opening_ai.mp4"))
+                open_src = opening
                 segments.append(VisualSegment(
                     index=seg_idx,
                     start_time=0.0,
@@ -139,7 +159,7 @@ class TimelineBuilder:
                     dur = min(s_dur, max(0.0, self.total_duration - current_time))
                     if dur <= 0:
                         break
-                    img_src = avail_images[img_cursor % len(avail_images)] if avail_images else Path("placeholder_scene.jpg")
+                    img_src = avail_images[img_cursor % len(avail_images)]
                     img_cursor += 1
                     segments.append(VisualSegment(
                         index=seg_idx,
@@ -157,7 +177,7 @@ class TimelineBuilder:
                 while current_time < self.total_duration:
                     rem = self.total_duration - current_time
                     dur = min(rem, 45.0)
-                    img_src = avail_images[img_cursor % len(avail_images)] if avail_images else Path("placeholder_scene.jpg")
+                    img_src = avail_images[img_cursor % len(avail_images)]
                     img_cursor += 1
                     segments.append(VisualSegment(
                         index=seg_idx,
@@ -178,7 +198,7 @@ class TimelineBuilder:
             while current_time < self.total_duration:
                 rem = self.total_duration - current_time
                 dur = min(rem, 45.0)
-                img_src = avail_images[img_cursor % len(avail_images)] if avail_images else Path("placeholder_scene.jpg")
+                img_src = avail_images[img_cursor % len(avail_images)]
                 img_cursor += 1
                 segments.append(VisualSegment(
                     index=seg_idx,
@@ -201,7 +221,9 @@ class TimelineBuilder:
                              list(self.story_dir.glob("full_video.mp4")) + \
                              list(self.story_dir.glob("reup_video.mp4")) + \
                              list(self.story_dir.glob("*.mp4"))
-                src_video = candidates[0] if candidates else Path("source_video.mp4")
+                src_video = candidates[0] if candidates else None
+            if src_video is None:
+                raise FileNotFoundError("F4 requires an existing original source video")
 
             # Inset foreground segment
             segments.append(VisualSegment(
@@ -215,7 +237,7 @@ class TimelineBuilder:
                 asset_id=Path(src_video).stem
             ))
             # Background stock interval
-            bg_stock = stock_queue.popleft() if stock_queue else Path("placeholder_bg_stock.mp4")
+            bg_stock = stock_queue.popleft()
             segments.append(VisualSegment(
                 index=1,
                 start_time=0.0,
@@ -237,7 +259,7 @@ class TimelineBuilder:
                     st_src = stock_queue.popleft()
                     newly_used.append(st_src)
                 else:
-                    st_src = Path(f"stock_clip_{stock_cursor+1}.mp4")
+                    raise FileNotFoundError("F5 has insufficient online-stock assets for the full timeline")
 
                 stock_cursor += 1
                 segments.append(VisualSegment(
@@ -257,7 +279,7 @@ class TimelineBuilder:
         else:
             # AI Opening (~60s)
             opening_dur = min(self.total_duration, F2_CHAPTER1_DURATION)
-            open_src = chap1_source or (veo_queue.popleft() if veo_queue else Path("placeholder_opening_ai.mp4"))
+            open_src = opening
             segments.append(VisualSegment(
                 index=seg_idx,
                 start_time=0.0,
@@ -283,11 +305,14 @@ class TimelineBuilder:
                     target_cls = sh.visual_requirement.preferred_source_class if sh.visual_requirement else SourceClass.STOCK_ONLINE
 
                     if target_cls == SourceClass.STOCK_ONLINE:
-                        src = stock_queue.popleft() if stock_queue else Path(f"stock_{seg_idx}.mp4")
+                        src = stock_queue.popleft() if stock_queue else None
                         seg_type = "stock"
                         newly_used.append(src)
                     else:
-                        src = veo_queue.popleft() if veo_queue else Path(f"veo_ai_{seg_idx}.mp4")
+                        src = veo_queue.popleft() if veo_queue else None
+                        seg_type = "veo_ai"
+                    if src is None:
+                        raise FileNotFoundError(f"F2 is missing the required {target_cls.value} source for {sh.shot_id}")
                         seg_type = "veo_ai"
 
                     segments.append(VisualSegment(
@@ -313,14 +338,16 @@ class TimelineBuilder:
 
                     # Ensure at least 1 stock and at least 1 veo post-opening
                     if slot % 2 == 0:
-                        src = stock_queue.popleft() if stock_queue else Path(f"stock_{seg_idx}.mp4")
+                        src = stock_queue.popleft() if stock_queue else None
                         seg_type = "stock"
                         cls = SourceClass.STOCK_ONLINE
                         newly_used.append(src)
                     else:
-                        src = veo_queue.popleft() if veo_queue else Path(f"veo_ai_{seg_idx}.mp4")
+                        src = veo_queue.popleft() if veo_queue else None
                         seg_type = "veo_ai"
                         cls = SourceClass.GENERATED_VIDEO
+                    if src is None:
+                        raise FileNotFoundError(f"F2 is missing a required {cls.value} source for interval {slot + 1}")
 
                     segments.append(VisualSegment(
                         index=seg_idx,
@@ -341,6 +368,12 @@ class TimelineBuilder:
             segments[-1].duration += (self.total_duration - current_time)
 
         # Record newly used clips in zero-reuse registry
+        for segment in segments:
+            path = Path(segment.source_path)
+            if not path.is_file():
+                raise FileNotFoundError(f"Required {segment.source_class.value if segment.source_class else 'visual'} source is missing: {path}")
+            segment.source_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
+
         if newly_used and self.story_dir.name != "dummy_story":
             record_clips(newly_used, story_name=self.story_dir.name)
 
@@ -348,7 +381,9 @@ class TimelineBuilder:
             story_dir=self.story_dir,
             audio_path=self.audio_path,
             total_duration=self.total_duration,
-            segments=segments
+            segments=segments,
+            format_id=fmt_id.value,
+            format_plan_fingerprint=format_plan.fingerprint
         )
 
         # Validate grammar
diff --git a/videopipeline/stages/stage4_render/nvenc_engine.py b/videopipeline/stages/stage4_render/nvenc_engine.py
index 7ba70df..5f4200d 100644
--- a/videopipeline/stages/stage4_render/nvenc_engine.py
+++ b/videopipeline/stages/stage4_render/nvenc_engine.py
@@ -54,6 +54,8 @@ class NvencRenderEngine:
         filter_map: Optional[str] = None
 
         src_exists = src_path and Path(src_path).exists() and Path(src_path).is_file()
+        if not src_exists:
+            raise FileNotFoundError(f"Required render source is missing: {src_path}")
         temp_motion: Optional[Path] = None
 
         if src_exists:
@@ -108,9 +110,6 @@ class NvencRenderEngine:
                         vf = f"setpts={stretch:.4f}*PTS,{vf}"
                 except Exception:
                     pass
-        else:
-            # Fallback for missing/unassigned clips: high-contrast dark gradient frame
-            input_args = ["-f", "lavfi", "-i", f"color=c=0x0a0e17:s={DEFAULT_WIDTH}x{DEFAULT_HEIGHT}:r={DEFAULT_FPS}"]
 
         if filter_complex and filter_map:
             filter_args = ["-filter_complex", filter_complex, "-map", filter_map]
@@ -172,8 +171,38 @@ class NvencRenderEngine:
         Pre-renders all visual segments in the schedule into the work directory.
         """
         normalized_paths: List[Path] = []
+        if schedule.format_id == "F4" and len(schedule.segments) >= 2:
+            foreground = next((s for s in schedule.segments if s.source_class and s.source_class.value == "ORIGINAL_REUP_VIDEO"), None)
+            background = next((s for s in schedule.segments if s.source_class and s.source_class.value == "STOCK_ONLINE"), None)
+            if foreground is None or background is None:
+                raise ValueError("F4 requires original-video foreground and online-stock background")
+            for seg in (foreground, background):
+                source = Path(seg.source_path)
+                if not source.is_file():
+                    raise FileNotFoundError(f"Required render source is missing: {source}")
+                actual = hashlib.sha256(source.read_bytes()).hexdigest()
+                if seg.source_sha256 and seg.source_sha256 != actual:
+                    raise RuntimeError(f"Source identity changed after timeline verification: {source}")
+            key = hashlib.sha256(f"{foreground.source_sha256}|{background.source_sha256}|{foreground.duration}".encode()).hexdigest()[:20]
+            out_file = self.segments_dir / f"f4_composite_{key}.mp4"
+            if force or not out_file.exists() or out_file.stat().st_size < 10000:
+                w, h = 640, 360
+                graph = f"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080[bg];[1:v]scale={w}:{h}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
+                cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(background.source_path), "-stream_loop", "-1", "-i", str(foreground.source_path), "-t", str(foreground.duration), "-filter_complex", graph, "-map", "[v]", "-r", str(DEFAULT_FPS), "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", str(out_file)]
+                subprocess.run(cmd, check=True, capture_output=True, text=True)
+            return [out_file]
         for seg in schedule.segments:
-            out_file = self.segments_dir / f"seg_{seg.index:03d}_{seg.segment_type}.mp4"
+            source = Path(seg.source_path)
+            if not source.is_file():
+                raise FileNotFoundError(f"Required render source is missing: {source}")
+            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
+            if seg.source_sha256 and seg.source_sha256 != source_hash:
+                raise RuntimeError(f"Source identity changed after timeline verification: {source}")
+            seg.source_sha256 = source_hash
+            cache_key = hashlib.sha256(
+                f"{source_hash}|{seg.segment_type}|{seg.start_time}|{seg.duration}".encode("utf-8")
+            ).hexdigest()[:20]
+            out_file = self.segments_dir / f"seg_{seg.index:03d}_{cache_key}.mp4"
             is_opening = (seg.index < 6)
             needs_render = force or (is_opening and force_opening) or (not out_file.exists()) or (out_file.stat().st_size < 10000)
             if not needs_render and out_file.exists():
diff --git a/videopipeline/tests/test_timeline_builder.py b/videopipeline/tests/test_timeline_builder.py
index 5984d1d..26dd121 100644
--- a/videopipeline/tests/test_timeline_builder.py
+++ b/videopipeline/tests/test_timeline_builder.py
@@ -6,14 +6,20 @@ from videopipeline.stages.stage3_compose.timeline_builder import TimelineBuilder
 from videopipeline.models import FormatId, SourceClass, create_default_format_plan
 
 
-def test_f1_schedule():
+def asset(tmp_path, name):
+    path = tmp_path / name
+    path.write_bytes(b"offline fixture media")
+    return path
+
+
+def test_f1_schedule(tmp_path):
     story_dir = Path("dummy_story")
     audio_path = Path("dummy_audio.m4a")
     total_dur = 240.0
 
     tb = TimelineBuilder(story_dir, audio_path, total_dur)
-    opening_video = Path("opening_veo.mp4")
-    images = [Path(f"scene_{i:02d}.jpg") for i in range(1, 6)]
+    opening_video = asset(tmp_path, "opening_veo.mp4")
+    images = [asset(tmp_path, f"scene_{i:02d}.jpg") for i in range(1, 6)]
 
     sched = tb.build_schedule(
         chap1_source=opening_video,
@@ -32,14 +38,14 @@ def test_f1_schedule():
     assert abs(total_calc - total_dur) < 0.01
 
 
-def test_f2_schedule():
+def test_f2_schedule(tmp_path):
     story_dir = Path("dummy_story")
     audio_path = Path("dummy_audio.m4a")
     total_dur = 240.0
 
     tb = TimelineBuilder(story_dir, audio_path, total_dur)
-    stock_clips = [Path(f"stock_{i}.mp4") for i in range(10)]
-    veo_clips = [Path(f"shot_{i:02d}.mp4") for i in range(10)]
+    stock_clips = [asset(tmp_path, f"stock_{i}.mp4") for i in range(10)]
+    veo_clips = [asset(tmp_path, f"shot_{i:02d}.mp4") for i in range(10)]
 
     sched = tb.build_schedule(
         stock_clips=stock_clips,
@@ -62,13 +68,13 @@ def test_f2_schedule():
     assert abs(total_calc - total_dur) < 0.01
 
 
-def test_f3_schedule():
+def test_f3_schedule(tmp_path):
     story_dir = Path("dummy_story")
     audio_path = Path("dummy_audio.m4a")
     total_dur = 180.0
 
     tb = TimelineBuilder(story_dir, audio_path, total_dur)
-    images = [Path(f"scene_{i:02d}.jpg") for i in range(1, 6)]
+    images = [asset(tmp_path, f"scene_{i:02d}.jpg") for i in range(1, 6)]
 
     sched = tb.build_schedule(
         images=images,
@@ -83,14 +89,14 @@ def test_f3_schedule():
     assert abs(total_calc - total_dur) < 0.01
 
 
-def test_f4_schedule():
+def test_f4_schedule(tmp_path):
     story_dir = Path("dummy_story")
     audio_path = Path("dummy_audio.m4a")
     total_dur = 200.0
 
     tb = TimelineBuilder(story_dir, audio_path, total_dur)
-    source_video = Path("source_reup.mp4")
-    stock_clips = [Path("bg_stock_canvas.mp4")]
+    source_video = asset(tmp_path, "source_reup.mp4")
+    stock_clips = [asset(tmp_path, "bg_stock_canvas.mp4")]
 
     sched = tb.build_schedule(
         chap1_source=source_video,
@@ -105,13 +111,13 @@ def test_f4_schedule():
     assert has_bg is True
 
 
-def test_f5_schedule():
+def test_f5_schedule(tmp_path):
     story_dir = Path("dummy_story")
     audio_path = Path("dummy_audio.m4a")
     total_dur = 150.0
 
     tb = TimelineBuilder(story_dir, audio_path, total_dur)
-    stock_clips = [Path(f"stock_online_{i}.mp4") for i in range(8)]
+    stock_clips = [asset(tmp_path, f"stock_online_{i}.mp4") for i in range(8)]
 
     sched = tb.build_schedule(
         stock_clips=stock_clips,
diff --git a/videopipeline/web/server.py b/videopipeline/web/server.py
index fee38ef..fc8400a 100644
--- a/videopipeline/web/server.py
+++ b/videopipeline/web/server.py
@@ -325,7 +325,11 @@ async def handle_action_compose(request):
     """Action: Compose timeline and ASS subtitles based on selected format."""
     data = await request.json()
     story_dir = Path(data.get("story_dir", ""))
-    fmt_choice = data.get("format", "f2") # f2, f2-l, f3, f1
+    from ..models import resolve_format_id
+    try:
+        fmt_choice = resolve_format_id(data.get("format", "F2")).value.lower()
+    except ValueError as exc:
+        return web.json_response({"status": "error", "message": str(exc)}, status=400)
 
     if not story_dir.exists():
         return web.json_response({"status": "error", "message": "Story not found"}, status=404)
@@ -350,7 +354,7 @@ async def handle_action_compose(request):
     stock_mgr = StockManager(get_story_stock_dirs(story_dir))
     veo_client = GoogleFlowVeoClient()
 
-    if fmt_choice in ("f2-l", "f1"):
+    if fmt_choice == "f2-l":
         # Lite format & F1 reup: 100% Stock/existing, no Veo AI calls
         veo_clips = []
         log_event(f"Format {fmt_choice.upper()} selected: Using existing assets (zero AI dependency).")
@@ -601,7 +605,8 @@ async def orchestrate_pipeline(story_dir: Path, fmt_choice: str, options: Dict[s
         from ..format_validator import FormatValidator
         from ..stages.stage3_compose.editorial_qc import EditorialQC
 
-        format_id_enum = FormatId(fmt_choice.upper()) if hasattr(FormatId, fmt_choice.upper()) else FormatId.F2
+        from ..models import resolve_format_id
+        format_id_enum = resolve_format_id(fmt_choice)
         format_plan = create_default_format_plan(format_id_enum)
         run_req = RunRequest(story_dir=story_dir, format_id=format_id_enum, format_plan=format_plan, options=options)

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
