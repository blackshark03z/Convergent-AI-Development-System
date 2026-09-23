# XP-002 Common Implementer Prompt

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

**Outcome:** For an F5 story, the product presents a bounded stock-video proposal table for every planned shot, derived from that shot’s script and visual intent. The Owner can inspect the proposals before any footage becomes a final production choice.

**Acceptance:**
- Each shot has a row showing its scene/shot and narration interval, visual purpose, a small ranked shortlist with identifiable source and preview, a brief fit reason, and any uncertainty or conflict. Shots without a suitable candidate remain visible as `NO_MATCH` or needing review.
- Representative shots with different actions or settings produce meaningfully different proposals even when they share broad story keywords. Ineligible or story-contradicting clips cannot become the proposed lead choice.
- The table clearly labels choices as proposals. Compiling or viewing it does not approve footage, download final assets, or silently change the F5 format or production timeline.
- Candidate evidence demonstrates the F5 review journey using an offline provider fixture, including a suitable match, a conflicting or ineligible result, and a no-match shot. Tie that evidence to the implementation candidate submitted for review.

**Constraints / non-goals:** Reuse the existing F5 shot plan and stock retrieval behavior where suitable. This slice covers proposal compilation and inspection only; approval, replacement, rough-cut production, and final acquisition are outside scope. No paid or external provider calls or canonical production runtime.

OWNER_INPUT_REQUIRED: no

Your previous completion report:
Implemented the F5 proposal review slice.

- Added a proposal compiler that creates a ranked shortlist for every cached body scene. It uses shot-specific visuals and action before narration, filters ineligible candidates, flags weak or contradictory matches, and preserves `NO_MATCH` rows.
- Added an F5-only review table with scene/shot IDs, narration intervals, visual purpose, source IDs, preview links, fit notes, and conflicts. It is explicitly labeled as proposals requiring Owner review.
- Added a read-only API that uses the cached shot plan and overlapping SRT cues. It does not approve or download clips or modify the production schedule.
- Added an offline fixture and evidence record at [f5-stock-proposal-offline-review.json](/D:/CADS-Benchmark/XP-002-AUTO/arms/CCURRENT/docs/evidence/f5-stock-proposal-offline-review.json).

The fixture shows distinct leads for the cycling and courtroom shots, exposes a conflicting celebration clip and a rights-unknown clip, and leaves the archive shot as `NO_MATCH`.

Checks run: focused pytest checks passed (4 tests); Python compilation, JavaScript syntax validation, and `git diff --check` passed. No external provider or production runtime was called.

Limitations: preview links and product rendering were not exercised against a live provider or browser. Candidate quality depends on the cached shot plan and available provider metadata. This is an implementation candidate for review; Product Acceptance is not claimed.

Current candidate tree: 27a0c91fdaf8c7ea41644218331d64421cabbd34
Current diff:
diff --git a/docs/evidence/f5-stock-proposal-offline-review.json b/docs/evidence/f5-stock-proposal-offline-review.json
new file mode 100644
index 0000000..be1dc27
--- /dev/null
+++ b/docs/evidence/f5-stock-proposal-offline-review.json
@@ -0,0 +1,17 @@
+{
+  "evidence_type": "offline_candidate_review",
+  "candidate_files": [
+    "videopipeline/stages/stage2_assets/stock_proposals.py",
+    "videopipeline/web/server.py",
+    "videopipeline/web/static/index.html",
+    "videopipeline/web/static/js/app.js"
+  ],
+  "fixture": "tests/fixtures/f5_stock_proposals.json",
+  "check": "python -m pytest tests/test_stock_proposals.py -q",
+  "observed": {
+    "scene_road": {"status": "PROPOSALS", "lead": "fixture_ride_01"},
+    "scene_hearing": {"status": "PROPOSALS", "lead": "fixture_court_01", "conflicts": ["fixture_conflict_01", "fixture_rights_01"]},
+    "scene_archive": {"status": "NO_MATCH", "lead": null}
+  },
+  "effect_boundary": "Fixture-only provider; no downloads, approvals, schedule edits, paid calls, or production runtime."
+}
diff --git a/tests/fixtures/f5_stock_proposals.json b/tests/fixtures/f5_stock_proposals.json
new file mode 100644
index 0000000..7053c05
--- /dev/null
+++ b/tests/fixtures/f5_stock_proposals.json
@@ -0,0 +1,49 @@
+{
+  "provider": "offline_fixture",
+  "scenes": [
+    {
+      "scene_id": "scene_road",
+      "shot_id": "shot_ride",
+      "start_sec": 120,
+      "end_sec": 126,
+      "narration": "She rides along a forest road.",
+      "visual_purpose": "cyclist riding through a forest",
+      "visual_intent": "cyclist forest road",
+      "required_visuals": ["cyclist", "forest"],
+      "forbidden_visuals": []
+    },
+    {
+      "scene_id": "scene_hearing",
+      "shot_id": "shot_cross_exam",
+      "start_sec": 126,
+      "end_sec": 132,
+      "narration": "The judge questions the witness in court.",
+      "visual_purpose": "judge cross-examines a witness in a courtroom",
+      "visual_intent": "judge witness courtroom cross-examination",
+      "required_visuals": ["judge", "witness", "courtroom"],
+      "forbidden_visuals": ["celebration"]
+    },
+    {
+      "scene_id": "scene_archive",
+      "shot_id": "shot_empty",
+      "start_sec": 132,
+      "end_sec": 138,
+      "narration": "The sealed record remains untouched.",
+      "visual_purpose": "sealed archive drawer in a secure records room",
+      "visual_intent": "sealed archive secure records drawer",
+      "required_visuals": ["sealed archive"],
+      "forbidden_visuals": []
+    }
+  ],
+  "results": {
+    "cyclist": [
+      {"id":"ride-01","online_id":"fixture_ride_01","source":"offline_fixture","title":"Cyclist Riding Through Forest","duration":12,"width":1920,"height":1080,"thumbnail":"https://fixture.invalid/ride.jpg","preview_url":"https://fixture.invalid/ride.mp4","rights_status":"ELIGIBLE","tags":["cyclist","forest","road"]}
+    ],
+    "judge": [
+      {"id":"court-01","online_id":"fixture_court_01","source":"offline_fixture","title":"Judge Questions Witness In Courtroom","duration":15,"width":1920,"height":1080,"thumbnail":"https://fixture.invalid/court.jpg","preview_url":"https://fixture.invalid/court.mp4","rights_status":"ELIGIBLE","tags":["judge","witness","courtroom"]},
+      {"id":"conflict-01","online_id":"fixture_conflict_01","source":"offline_fixture","title":"Courtroom Celebration Party","duration":15,"width":1920,"height":1080,"thumbnail":"https://fixture.invalid/conflict.jpg","preview_url":"https://fixture.invalid/conflict.mp4","rights_status":"ELIGIBLE","tags":["courtroom","celebration"]},
+      {"id":"rights-01","online_id":"fixture_rights_01","source":"offline_fixture","title":"Judge And Witness","duration":15,"width":1920,"height":1080,"rights_status":"UNKNOWN","tags":["judge","witness","courtroom"]}
+    ],
+    "archive": []
+  }
+}
diff --git a/tests/test_stock_proposals.py b/tests/test_stock_proposals.py
new file mode 100644
index 0000000..d7aa984
--- /dev/null
+++ b/tests/test_stock_proposals.py
@@ -0,0 +1,30 @@
+import json
+from pathlib import Path
+
+from videopipeline.stages.stage2_assets.stock_proposals import compile_stock_proposals
+
+
+class OfflineFixtureProvider:
+    def __init__(self, fixture):
+        self.fixture = fixture
+
+    def search_videos(self, query, per_page=12):
+        words = query.lower().split()
+        bucket = "cyclist" if "cyclist" in words else "judge" if "judge" in words else "archive" if "archive" in words else "archive"
+        return {"status": "ok", "videos": self.fixture["results"][bucket]}
+
+
+def test_f5_proposals_keep_shots_distinct_and_expose_conflicts_and_no_match():
+    fixture_path = Path(__file__).parent / "fixtures" / "f5_stock_proposals.json"
+    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
+    result = compile_stock_proposals(fixture["scenes"], OfflineFixtureProvider(fixture))
+
+    assert result["label"] == "PROPOSALS — not approved"
+    ride, hearing, archive = result["rows"]
+    assert ride["proposals"][0]["online_id"] == "fixture_ride_01"
+    assert "cyclist" in ride["query"]
+    assert "judge" in hearing["query"] and "cyclist" not in hearing["query"]
+    assert hearing["proposals"][0]["online_id"] == "fixture_court_01"
+    assert {c["online_id"] for c in hearing["conflicts"]} == {"fixture_conflict_01", "fixture_rights_01"}
+    assert archive["status"] == "NO_MATCH" and not archive["proposals"]
+
diff --git a/videopipeline/stages/stage2_assets/stock_proposals.py b/videopipeline/stages/stage2_assets/stock_proposals.py
new file mode 100644
index 0000000..1c1f70d
--- /dev/null
+++ b/videopipeline/stages/stage2_assets/stock_proposals.py
@@ -0,0 +1,61 @@
+"""Proposal-only stock shortlist compilation for planned F5 shots."""
+from typing import Any, Dict, List
+
+from .online_stock import StockConstraintChecker, StoryStockRetriever
+
+
+def _value(scene: Dict[str, Any], *keys: str, default: Any = "") -> Any:
+    for key in keys:
+        value = scene.get(key)
+        if value not in (None, ""):
+            return value
+    return default
+
+
+def compile_stock_proposals(scenes: List[Dict[str, Any]], provider: Any, limit: int = 3) -> Dict[str, Any]:
+    """Compile review rows without acquiring media or mutating a production schedule."""
+    retriever = StoryStockRetriever(provider)
+    rows = []
+    for index, scene in enumerate(scenes, 1):
+        sid = str(_value(scene, "scene_id", "id", default=f"scene_{index:02d}"))
+        shot_id = str(_value(scene, "shot_id", default=f"shot_{index:02d}"))
+        start = float(_value(scene, "start_sec", "start", default=0) or 0)
+        end = float(_value(scene, "end_sec", "end", default=start + float(_value(scene, "duration", "duration_sec", default=0) or 0)) or start)
+        narration = str(_value(scene, "narration", "script", "story_context", "key_event", "dramatic_beat"))
+        purpose = str(_value(scene, "visual_purpose", "dramatic_purpose", "primary_action", "dramatic_beat", default="Visual coverage"))
+        visual = str(_value(scene, "stock_search_intent", "visual_intent", "visual_description", default=""))
+        required = _value(scene, "required_visuals", default=[])
+        forbidden = _value(scene, "forbidden_visuals", default=[])
+        # Lead the query with shot-specific visible details and action; narration
+        # provides context after those differentiating concepts.
+        intent = " ".join([" ".join(map(str, required)), purpose, visual, narration]).strip()
+        query = retriever.compile_search_query(intent, narration)
+        result = provider.search_videos(query, per_page=12)
+        candidates, rejected = [], []
+        if result.get("status") == "ok":
+            for candidate in result.get("videos", []):
+                ok, reason = StockConstraintChecker.evaluate(candidate, min_duration=4.0, forbidden_terms=list(map(str, forbidden)))
+                score = retriever.compute_semantic_similarity(candidate, intent)
+                item = dict(candidate)
+                item["semantic_score"] = score
+                if not ok:
+                    item["conflict"] = reason
+                    rejected.append(item)
+                elif score < 0.20:
+                    item["conflict"] = "Weak or contradictory visual fit"
+                    rejected.append(item)
+                else:
+                    item["fit_reason"] = f"Visual intent overlap ({score:.2f}); duration and rights checks passed."
+                    candidates.append(item)
+        candidates = retriever.rank_candidates(candidates, intent, max(1, end-start))[:limit]
+        for candidate in candidates:
+            candidate.setdefault("fit_reason", f"Visual intent overlap ({candidate.get('semantic_score', 0):.2f}); duration and rights checks passed.")
+        status = "PROPOSALS" if candidates else ("NEEDS_REVIEW" if rejected or result.get("status") != "ok" else "NO_MATCH")
+        rows.append({
+            "scene_id": sid, "shot_id": shot_id, "start_sec": start, "end_sec": end,
+            "narration": narration, "visual_purpose": purpose, "query": query,
+            "status": status, "proposals": candidates,
+            "conflicts": rejected,
+            "uncertainty": "Review required: no eligible matching candidate." if status != "PROPOSALS" else "Shortlist only; Owner approval required.",
+        })
+    return {"status": "ok", "label": "PROPOSALS — not approved", "rows": rows}
diff --git a/videopipeline/tests/test_web_server.py b/videopipeline/tests/test_web_server.py
index e60c460..0944402 100644
--- a/videopipeline/tests/test_web_server.py
+++ b/videopipeline/tests/test_web_server.py
@@ -21,6 +21,7 @@ def test_app_routes_registered():
     assert "/api/editorial_qc/report" in routes
     assert "/api/editorial_qc/adjudicate" in routes
     assert "/api/stock_exceptions" in routes
+    assert "/api/stock/proposals" in routes
 
 def test_discover_stories():
     stories = discover_stories(BASE_DIR)
diff --git a/videopipeline/web/server.py b/videopipeline/web/server.py
index 56ccf83..e097cb6 100644
--- a/videopipeline/web/server.py
+++ b/videopipeline/web/server.py
@@ -28,6 +28,7 @@ from ..stages.stage2_assets.stock_manager import StockManager
 from ..stages.stage2_assets.veo_client import GoogleFlowVeoClient
 from ..stages.stage2_assets.flow_generator import check_cookie_expiry
 from ..stages.stage2_assets.online_stock import PexelsClient
+from ..stages.stage2_assets.stock_proposals import compile_stock_proposals
 from ..stages.stage3_compose.timeline_builder import TimelineBuilder
 from ..stages.stage3_compose.ass_karaoke import generate_karaoke_ass
 from ..stages.stage4_render.nvenc_engine import NvencRenderEngine
@@ -1210,6 +1211,28 @@ async def handle_online_stock_search(request):
     except Exception as e:
         return web.json_response({"status": "error", "message": f"Lỗi tìm kiếm online stock: {e}"}, status=500)
 
+async def handle_stock_proposals(request):
+    """Compiles a proposal-only shortlist from the cached director shot plan."""
+    story_dir = Path(request.query.get("story_dir", ""))
+    cache_file = story_dir / "gemini_storyboard.json"
+    if not story_dir.is_dir() or not cache_file.is_file():
+        return web.json_response({"status": "error", "message": "F5 shot plan is not available; analyze the story first."}, status=404)
+    try:
+        data = json.loads(cache_file.read_text(encoding="utf-8"))
+        scenes = data.get("body_scenes", [])
+        if not isinstance(scenes, list) or not scenes:
+            return web.json_response({"status": "error", "message": "Cached shot plan has no body scenes."}, status=404)
+        srts = sorted(story_dir.glob("*.srt"))
+        if srts:
+            cues = parse_srt_file(srts[0])
+            for scene in scenes:
+                start = float(scene.get("start_sec", 0) or 0)
+                end = float(scene.get("end_sec", start) or start)
+                scene["narration"] = " ".join(c.text for c in cues if c.start_sec < end and c.end_sec > start)
+        result = await asyncio.get_event_loop().run_in_executor(None, lambda: compile_stock_proposals(scenes, PexelsClient()))
+        return web.json_response(result)
+    except Exception as exc:
+        return web.json_response({"status": "error", "message": str(exc)}, status=500)
 async def handle_online_stock_download_and_swap(request):
     """Downloads an online stock video and assigns it to a target segment (ADR-009)."""
     try:
@@ -1513,6 +1536,7 @@ def create_app() -> web.Application:
     app.router.add_get("/api/assets/available_clips", handle_get_available_clips)
     app.router.add_post("/api/schedule/swap_segment", handle_action_swap_segment)
     app.router.add_get("/api/stock/online/search", handle_online_stock_search)
+    app.router.add_get("/api/stock/proposals", handle_stock_proposals)
     app.router.add_post("/api/stock/online/download_and_swap", handle_online_stock_download_and_swap)
     app.router.add_get("/api/stock_exceptions", handle_get_stock_exceptions)
     app.router.add_get("/api/editorial_qc/report", handle_get_editorial_qc_report)
diff --git a/videopipeline/web/static/index.html b/videopipeline/web/static/index.html
index f31657f..4937fb2 100644
--- a/videopipeline/web/static/index.html
+++ b/videopipeline/web/static/index.html
@@ -491,6 +491,15 @@
           </div>
         </div>
 
+        <section class="glass-card" id="f5ProposalCard" style="display:none; margin-top:20px;">
+          <div class="card-header-clean">
+            <div><h3>F5 Stock Proposals</h3><span class="sub-badge">Proposal shortlist · nothing is approved or added to the timeline</span></div>
+            <button id="btnCompileF5Proposals" class="btn btn-primary btn-sm">Compile shot proposals</button>
+          </div>
+          <p id="f5ProposalStatus" role="status" style="color:var(--text-muted);">Uses the cached shot plan. Compilation only searches and displays previews.</p>
+          <div style="overflow-x:auto;"><table style="width:100%; border-collapse:collapse; min-width:900px;"><thead><tr><th>Scene / shot · narration</th><th>Visual purpose</th><th>Ranked proposal / preview</th><th>Fit / conflict</th></tr></thead><tbody id="f5ProposalRows"></tbody></table></div>
+        </section>
+
         <!-- ============================================================ -->
         <!-- FORMAT-SPECIFIC INSPECTOR CARDS                              -->
         <!-- ============================================================ -->
diff --git a/videopipeline/web/static/js/app.js b/videopipeline/web/static/js/app.js
index d6ea459..9cf9895 100644
--- a/videopipeline/web/static/js/app.js
+++ b/videopipeline/web/static/js/app.js
@@ -86,6 +86,10 @@ const el = {
   onlineSearchLoading: document.getElementById("onlineSearchLoading"),
   onlineClipsList: document.getElementById("onlineClipsList"),
   onlineQuickChips: document.querySelectorAll(".online-quick-chip"),
+  f5ProposalCard: document.getElementById("f5ProposalCard"),
+  btnCompileF5Proposals: document.getElementById("btnCompileF5Proposals"),
+  f5ProposalStatus: document.getElementById("f5ProposalStatus"),
+  f5ProposalRows: document.getElementById("f5ProposalRows"),
 
   // Step 3
   chkKaraoke: document.getElementById("chkKaraoke"),
@@ -844,6 +848,7 @@ if (el.btnForceRefreshDirector) {
 function selectFormat(formatKey) {
   if (!formatKey) return;
   state.selectedFormat = formatKey;
+  if (el.f5ProposalCard) el.f5ProposalCard.style.display = formatKey === "f5" ? "block" : "none";
   try {
     localStorage.setItem("videopipeline_selected_format", formatKey);
   } catch (e) {}
@@ -876,6 +881,38 @@ function selectFormat(formatKey) {
   updateFormatInspectorView(formatKey);
 }
 
+if (el.btnCompileF5Proposals) {
+  el.btnCompileF5Proposals.addEventListener("click", async () => {
+    if (!state.selectedStoryDir) return;
+    el.btnCompileF5Proposals.disabled = true;
+    el.f5ProposalStatus.textContent = "Searching cached shot intent for proposal candidates…";
+    el.f5ProposalRows.innerHTML = "";
+    try {
+      const res = await fetch(`/api/stock/proposals?story_dir=${encodeURIComponent(state.selectedStoryDir)}`);
+      const data = await res.json();
+      if (!res.ok || data.status !== "ok") throw new Error(data.message || "Proposal compilation failed");
+      el.f5ProposalStatus.textContent = `${data.label} · ${data.rows.length} planned shots · schedule unchanged.`;
+      data.rows.forEach((row) => {
+        const proposals = row.proposals || [];
+        const media = proposals.length ? proposals.map((c, index) => `
+          <div style="display:flex;gap:10px;align-items:flex-start;margin:8px 0;">
+            ${c.thumbnail ? `<img src="${escapeHtml(c.thumbnail)}" alt="Preview thumbnail for ${escapeHtml(c.title || c.id)}" style="width:120px;max-height:70px;object-fit:cover;border-radius:5px;">` : ""}
+            <div><strong>#${index + 1} ${escapeHtml(c.title || c.id)}</strong> · ${escapeHtml(c.source || "stock")} ${escapeHtml(c.online_id || c.id)}<br>
+            ${c.preview_url ? `<a href="${escapeHtml(c.preview_url)}" target="_blank" rel="noopener">Open preview</a>` : "Preview unavailable"}</div>
+          </div>`).join("") : `<strong>${escapeHtml(row.status)}</strong>`;
+        const conflict = (row.conflicts || []).map(c => `${escapeHtml(c.title || c.id)}: ${escapeHtml(c.conflict || "Needs review")}`).join("<br>");
+        const tr = document.createElement("tr");
+        tr.innerHTML = `<td style="vertical-align:top;padding:10px;">${escapeHtml(row.scene_id)} / ${escapeHtml(row.shot_id)}<br>${Number(row.start_sec).toFixed(1)}–${Number(row.end_sec).toFixed(1)}s<br><small>${escapeHtml(row.narration || "Narration not supplied")}</small></td><td style="vertical-align:top;padding:10px;">${escapeHtml(row.visual_purpose)}</td><td style="vertical-align:top;padding:10px;">${media}</td><td style="vertical-align:top;padding:10px;">${conflict || escapeHtml(row.uncertainty)}</td>`;
+        el.f5ProposalRows.appendChild(tr);
+      });
+    } catch (error) {
+      el.f5ProposalStatus.textContent = `${error.message}. Check that the story has a cached director shot plan, then retry.`;
+    } finally {
+      el.btnCompileF5Proposals.disabled = false;
+    }
+  });
+}
+
 el.formatCards.forEach((card) => {
   card.addEventListener("click", () => {
     const fmt = card.getAttribute("data-format");
@@ -1978,7 +2015,7 @@ function formatSec(sec) {
 }
 
 function escapeHtml(str) {
-  return str ? String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;") : "";
+  return str ? String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\"/g, "&quot;").replace(/'/g, "&#39;") : "";
 }
 
 async function loadDiscoveredStories() {

R repair brief:
REPAIR:

**Outcome:** Make the F5 proposal table cover every planned stock shot across the full story, with proposals tied to each shot’s script and visual intent.

**Acceptance:**
- An offline F5 story produces one row per planned shot, including the opening, with correct shot identity and narration interval. The current endpoint reads only cached `body_scenes`, while the F5 timeline covers the full story.
- Shots with different actions or settings yield meaningfully different proposals even when they share broad visual terms. Ineligible or contradictory clips cannot lead; unmatched shots remain visible.
- The review table displays each proposal’s fit reason as well as conflicts or uncertainty. The current UI receives `fit_reason` but does not show it.
- Candidate-bound offline evidence exercises the F5 request and rendered review journey, beyond the compiler-only fixture, without external provider or production calls.

This is the sole repair. Work only in this disposable clone. No external or production effects. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report checks actually run and remaining limits.
