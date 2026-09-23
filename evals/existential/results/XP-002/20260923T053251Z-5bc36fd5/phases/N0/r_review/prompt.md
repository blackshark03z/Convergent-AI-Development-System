You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-002 Reasoning Lead Prompt — N0 / No CADS

You are R, the Reasoning Lead. You do not edit product code.

## Frozen Raw Owner Goal

For F5, analyze the story/script and propose relevant stock video for each shot in
a reviewable table. The Owner must be able to inspect the proposals before they
become final production choices.

The proposal step is not itself approval. Keep the proposal bounded and
reviewable rather than silently committing arbitrary stock choices.

## Fixed intent

- F5 is the full custom-video format using online stock/custom cinematic footage.
- The system should reason from the script/shot intent rather than choose stock
  only from generic/global keywords.
- Proposals must stay reviewable before final production use.
- This case tests the bounded proposal compilation step only. The later
  approve/replace/confirm/cancel lifecycle is outside XP-002 unless already
  required by the pinned base behavior.
- Do not prescribe the implementation method.

## Fixed constraints

- Do not call paid/external providers or the canonical production runtime.
- Keep the historical/reference implementation and held-out evaluator hidden.
- Do not inspect sibling benchmark workspaces or results.
- You may inspect the assigned neutral repository, but must not edit product code.

## Common R→I rule

Produce the smallest Implementation Brief that makes the outcome testable.
SPEC UNTIL TESTABLE, NOT SPEC UNTIL COMPLETE.
Stop specifying once multiple implementations could satisfy the brief, PASS/FAIL
can be judged from observable outcome, and I need not invent a material product
preference or consequence boundary.

Your brief may use Outcome, Acceptance, Constraints / Non-goals, Effects /
Authority, and material assumptions/open questions only if needed. Do not add
design/architecture/task artifacts unless they solve a concrete ambiguity or risk.

## Arm treatment

Use your normal reasoning from the Raw Owner Goal and neutral repository. Do not
use CADS concepts/templates or a prescribed spec workflow.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.


IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** For F5, compile a bounded, owner-reviewable table of online stock proposals for every planned shot, grounded in that shot’s script and visual intent.

**Acceptance:**

- Every planned F5 shot has a row identifying the shot, its timing or narration context, its visual intent, and a small bounded set of stock candidates.
- Each candidate has enough identity and preview information for the Owner to inspect it, plus a concise reason it fits the shot. Distinct shot intents produce appropriately distinct searches or proposals; generic story-wide keywords alone do not satisfy this.
- Ineligible or clearly mismatched footage is excluded. A shot with no suitable candidate is marked unresolved, without arbitrary filler.
- Compiling or viewing the table leaves every candidate provisional. It does not approve a clip, assign a final production choice, or silently substitute one into the production timeline.
- Offline tests with a fake stock provider demonstrate shot coverage, intent-based proposals, bounded results, unresolved shots, and the provisional boundary.

**Constraints / non-goals:** Keep F5 footage within its online stock source policy. The later approve, replace, confirm, and cancel lifecycle is outside this brief. Verification must not call external providers or the canonical production runtime.

OWNER_INPUT_REQUIRED: no

I completion report:
Implemented a provisional F5 stock proposal table. The compiler searches each scheduled F5 segment using its overlapping SRT narration and visual description, filters ineligible or poor-fit footage, and marks segments unresolved when no candidate fits. Results include preview links, candidate identity, and a concise fit reason. Compiling the table does not write to the timeline.

The studio requires an existing F5 schedule. The proposal endpoint reads that schedule and rejects schedules for other formats.

**Files changed:** [stock_proposals.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/N0/videopipeline/stages/stage2_assets/stock_proposals.py:20), [server.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/N0/videopipeline/web/server.py:1356), [index.html](/D:/CADS-Benchmark/XP-002-AUTO/arms/N0/videopipeline/web/static/index.html:324), [app.js](/D:/CADS-Benchmark/XP-002-AUTO/arms/N0/videopipeline/web/static/js/app.js:844), and [test_stock_proposals.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/N0/tests/test_stock_proposals.py:23).

**Checks:** The fake-provider proposal test passed; stock constraint and shot-coverage tests also passed (10 total). Python compilation and `git diff --check` passed. No external provider or production runtime was called.

The tests cover per-shot searches, bounded results, mismatch and eligibility filtering, unresolved shots, and the provisional boundary. I did not exercise the live UI or endpoint against an actual schedule, and I do not claim Product Acceptance.

Candidate tree: 50950abfc38125e8febfe33d6f47bff686dad7ea
Candidate status:
A  tests/test_stock_proposals.py
A  videopipeline/stages/stage2_assets/stock_proposals.py
M  videopipeline/web/server.py
M  videopipeline/web/static/index.html
M  videopipeline/web/static/js/app.js
Candidate diff:
diff --git a/tests/test_stock_proposals.py b/tests/test_stock_proposals.py
new file mode 100644
index 0000000..4188f76
--- /dev/null
+++ b/tests/test_stock_proposals.py
@@ -0,0 +1,41 @@
+from videopipeline.stages.stage2_assets.stock_proposals import compile_stock_proposal_table
+
+
+class FakeStockProvider:
+    def __init__(self):
+        self.queries = []
+
+    def search_videos(self, query, per_page=12):
+        self.queries.append(query)
+        if "rain" in query.lower():
+            videos = [
+                {"id": "rain-1", "online_id": "pexels_rain-1", "title": "Woman walking through rain at night", "duration": 9, "width": 1920, "height": 1080, "preview_url": "https://preview/rain", "thumbnail": "https://thumb/rain", "rights_status": "ELIGIBLE"},
+                {"id": "short", "title": "Rain", "duration": 2, "width": 1920, "height": 1080, "rights_status": "ELIGIBLE"},
+                {"id": "portrait", "title": "Rain street", "duration": 9, "width": 1080, "height": 1920, "rights_status": "ELIGIBLE"},
+            ]
+        elif "archive" in query.lower():
+            videos = [{"id": "wrong", "title": "Puppies playing", "duration": 8, "width": 1920, "height": 1080, "rights_status": "ELIGIBLE"}]
+        else:
+            videos = []
+        return {"status": "ok", "videos": videos}
+
+
+def test_stock_proposals_cover_shots_use_intent_bound_results_and_remain_provisional():
+    provider = FakeStockProvider()
+    shots = [
+        {"shot_index": 1, "time_range": "0:00 - 0:10", "dramatic_beat": "Woman crosses rainy street", "shot_type": "Tracking shot", "visual_description": "woman walking through rain at night"},
+        {"shot_index": 2, "time_range": "0:10 - 0:20", "dramatic_beat": "Archive reveals hidden record", "shot_type": "Extreme close up", "visual_description": "old archive document"},
+        {"shot_index": 3, "time_range": "0:20 - 0:30", "dramatic_beat": "Empty hallway", "shot_type": "Wide shot", "visual_description": "empty courthouse hallway"},
+    ]
+    result = compile_stock_proposal_table(shots, provider, max_candidates=1)
+    assert len(result["rows"]) == 3
+    assert len(provider.queries) == 3
+    assert provider.queries[0] != provider.queries[1]
+    assert [row["status"] for row in result["rows"]] == ["PROVISIONAL", "UNRESOLVED", "UNRESOLVED"]
+    candidate = result["rows"][0]["candidates"][0]
+    assert candidate["id"] == "rain-1"
+    assert candidate["preview_url"] and candidate["thumbnail"] and candidate["reason"]
+    assert candidate["provisional"] is True
+    assert result["rows"][0]["timeline_assignment"] is None
+    assert result["provisional"] is True
+    assert result["rows"][1]["candidates"] == []
diff --git a/videopipeline/stages/stage2_assets/stock_proposals.py b/videopipeline/stages/stage2_assets/stock_proposals.py
new file mode 100644
index 0000000..0ae4d48
--- /dev/null
+++ b/videopipeline/stages/stage2_assets/stock_proposals.py
@@ -0,0 +1,59 @@
+"""Compile provisional, shot-specific online stock proposals."""
+from typing import Any, Dict, List, Optional
+
+from .online_stock import StockConstraintChecker, StoryStockRetriever
+
+
+def _shot_intent(shot: Dict[str, Any]) -> str:
+    # Keep the query anchored in this shot's concrete beat and visual direction.
+    fields = ("visual_description", "dramatic_beat", "shot_type", "location", "characters_present")
+    parts = []
+    for field in fields:
+        value = shot.get(field, "")
+        if isinstance(value, list):
+            value = " ".join(map(str, value))
+        if value and str(value).strip():
+            parts.append(str(value).strip())
+    return " ".join(parts)
+
+
+def compile_stock_proposal_table(
+    shots: List[Dict[str, Any]], provider: Any, narration_by_range: Optional[Dict[str, str]] = None,
+    max_candidates: int = 3, min_duration: float = 4.0,
+) -> Dict[str, Any]:
+    """Search once per planned shot; results remain proposals and never select timeline media."""
+    retriever = StoryStockRetriever(provider_client=provider)
+    rows = []
+    for shot in shots:
+        shot_id = shot.get("shot_index", shot.get("shot_id", "unknown"))
+        time_range = str(shot.get("time_range", ""))
+        beat = str(shot.get("dramatic_beat", ""))
+        visual = _shot_intent(shot)
+        query = retriever.compile_search_query(visual)
+        result = provider.search_videos(query, per_page=12)
+        candidates = []
+        if result.get("status") == "ok":
+            for candidate in result.get("videos", []):
+                if not candidate.get("id") or not candidate.get("preview_url"):
+                    continue
+                eligible, _ = StockConstraintChecker.evaluate(candidate, min_duration=min_duration)
+                if not eligible:
+                    continue
+                score = retriever.compute_semantic_similarity(candidate, visual)
+                # A proposal needs actual evidence of fit; reject generic or mismatched footage.
+                if score < 0.2:
+                    continue
+                candidate = dict(candidate)
+                candidate["reason"] = f"Matches this shot's {beat or visual[:90]} intent (fit {score:.2f})."
+                candidate["provisional"] = True
+                candidates.append((score, candidate))
+            candidates.sort(key=lambda item: item[0], reverse=True)
+        narration = (narration_by_range or {}).get(time_range, "")
+        rows.append({
+            "shot_id": shot_id, "time_range": time_range, "narration": narration,
+            "visual_intent": visual, "query": query,
+            "status": "PROVISIONAL" if candidates else "UNRESOLVED",
+            "candidates": [candidate for _, candidate in candidates[:max(0, min(5, max_candidates))]],
+            "timeline_assignment": None,
+        })
+    return {"status": "ok", "provisional": True, "rows": rows}
diff --git a/videopipeline/web/server.py b/videopipeline/web/server.py
index 56ccf83..222505d 100644
--- a/videopipeline/web/server.py
+++ b/videopipeline/web/server.py
@@ -1353,6 +1353,58 @@ async def handle_director_get_storyboard(request):
     except Exception as e:
         return web.json_response({"status": "error", "message": str(e)}, status=500)
 
+async def handle_stock_proposals(request):
+    """Builds an owner-reviewable, provisional proposal table for storyboard shots."""
+    try:
+        data = await request.json()
+        story_dir = Path(data.get("story_dir", ""))
+        schedule_file = story_dir / "fast_pipeline" / "video_schedule.json"
+        if not story_dir.is_dir() or not schedule_file.is_file():
+            return web.json_response({"status": "error", "message": "Compose an F5 schedule first to define the planned shots."}, status=404)
+        schedule = json.loads(schedule_file.read_text(encoding="utf-8"))
+        if schedule.get("format_id") != "F5":
+            return web.json_response({"status": "error", "message": "Stock proposals are available for an F5 schedule."}, status=409)
+        segments = schedule.get("segments", [])
+        shots = []
+        from ..stages.stage2_assets.stock_proposals import compile_stock_proposal_table
+        narration_by_range = {}
+        srt_files = list(story_dir.glob("*.srt"))
+        if srt_files:
+            cues = parse_srt_file(srt_files[0])
+            def stamp(seconds):
+                total = max(0, int(seconds))
+                return f"{total // 60}:{total % 60:02d}"
+            for segment in segments:
+                start_sec = float(segment.get("start", 0))
+                end_sec = start_sec + float(segment.get("duration", 0))
+                time_range = f"{stamp(start_sec)} - {stamp(end_sec)}"
+                narration_by_range[time_range] = " ".join(
+                    cue.text for cue in cues if cue.start_sec < end_sec and cue.end_sec > start_sec
+                )
+                narration = narration_by_range[time_range]
+                shots.append({
+                    "shot_index": segment.get("index"), "time_range": time_range,
+                    "dramatic_beat": narration or segment.get("description", ""),
+                    "visual_description": narration,
+                    "shot_type": segment.get("description", "F5 stock shot"),
+                })
+        else:
+            for segment in segments:
+                start_sec = float(segment.get("start", 0))
+                end_sec = start_sec + float(segment.get("duration", 0))
+                shots.append({
+                    "shot_index": segment.get("index"),
+                    "time_range": f"{int(start_sec // 60)}:{int(start_sec % 60):02d} - {int(end_sec // 60)}:{int(end_sec % 60):02d}",
+                    "dramatic_beat": segment.get("description", ""),
+                    "shot_type": "F5 stock shot",
+                })
+        client = PexelsClient()
+        loop = asyncio.get_event_loop()
+        table = await loop.run_in_executor(None, lambda: compile_stock_proposal_table(shots, client, narration_by_range))
+        return web.json_response(table)
+    except Exception as e:
+        return web.json_response({"status": "error", "message": str(e)}, status=500)
+
 async def handle_get_system_health(request):
     """Executes the System Doctor diagnostics and returns JSON health report."""
     try:
@@ -1528,6 +1580,7 @@ def create_app() -> web.Application:
     # Gemini Showrunner Director Routes
     app.router.add_get("/api/director/storyboard", handle_director_get_storyboard)
     app.router.add_post("/api/director/analyze_story", handle_director_analyze_story)
+    app.router.add_post("/api/stock/proposals", handle_stock_proposals)
 
     # Actions & Pipeline Execution
     app.router.add_get("/api/system/health", handle_get_system_health)
diff --git a/videopipeline/web/static/index.html b/videopipeline/web/static/index.html
index f31657f..87eb10c 100644
--- a/videopipeline/web/static/index.html
+++ b/videopipeline/web/static/index.html
@@ -319,6 +319,20 @@
 
         </div>
 
+        <section style="margin: 18px 0; padding: 16px; border: 1px solid rgba(255,255,255,.1); border-radius: 10px;">
+          <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;">
+            <h3 style="margin:0">F5 online stock proposals</h3>
+            <button id="btnCompileStockProposals" class="btn btn-secondary btn-sm">Find provisional stock</button>
+          </div>
+              <div id="stockProposalStatus" style="margin: 10px 0; color: var(--text-muted);"></div>
+              <div class="storyboard-table-wrapper" style="max-height: 420px; overflow-y: auto; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; margin-top: 12px;">
+                <table class="styled-table" style="width: 100%; border-collapse: collapse;">
+                  <thead><tr><th>Shot / time</th><th>Script beat and visual intent</th><th>Online candidates (provisional)</th></tr></thead>
+                  <tbody id="stockProposalRows"></tbody>
+                </table>
+              </div>
+        </section>
+
         <!-- Navigation Footer -->
         <div class="wizard-footer-actions">
           <div></div>
diff --git a/videopipeline/web/static/js/app.js b/videopipeline/web/static/js/app.js
index d6ea459..49cbab1 100644
--- a/videopipeline/web/static/js/app.js
+++ b/videopipeline/web/static/js/app.js
@@ -62,6 +62,9 @@ const el = {
   locationAnchorsGrid: document.getElementById("locationAnchorsGrid"),
   storyboardShotsBody: document.getElementById("storyboardShotsBody"),
   btnCopyAllPrompts: document.getElementById("btnCopyAllPrompts"),
+  btnCompileStockProposals: document.getElementById("btnCompileStockProposals"),
+  stockProposalRows: document.getElementById("stockProposalRows"),
+  stockProposalStatus: document.getElementById("stockProposalStatus"),
 
   // Step 2 & Segment Inspector (ADR-005)
   formatCards: document.querySelectorAll(".format-card"),
@@ -838,6 +841,34 @@ if (el.btnForceRefreshDirector) {
   el.btnForceRefreshDirector.addEventListener("click", () => triggerAnalyzeDirector(true));
 }
 
+if (el.btnCompileStockProposals) {
+  el.btnCompileStockProposals.addEventListener("click", async () => {
+    if (!state.selectedStoryDir) return;
+    el.btnCompileStockProposals.disabled = true;
+    el.stockProposalStatus.textContent = "Searching each planned F5 shot using its narration context and visual intent…";
+    try {
+      const response = await fetch("/api/stock/proposals", {
+        method: "POST", headers: { "Content-Type": "application/json" },
+        body: JSON.stringify({ story_dir: state.selectedStoryDir })
+      });
+      const table = await response.json();
+      if (!response.ok) throw new Error(table.message || "Stock search failed");
+      el.stockProposalRows.innerHTML = "";
+      table.rows.forEach(row => {
+        const tr = document.createElement("tr");
+        const proposals = row.candidates.map(c => `<article style="margin-bottom:10px"><a href="${escapeHtml(c.preview_url || "#")}" target="_blank" rel="noopener">${escapeHtml(c.title || `Clip ${c.id}`)}</a> · ${escapeHtml(c.duration)}s · ${escapeHtml(c.width)}×${escapeHtml(c.height)}<br><a href="${escapeHtml(c.thumbnail || "#")}" target="_blank" rel="noopener">Preview image</a><br><small>${escapeHtml(c.reason)}</small><br><small>PROVISIONAL · ${escapeHtml(c.online_id || c.id)}</small></article>`).join("");
+        tr.innerHTML = `<td>${escapeHtml(row.shot_id)}<br>${escapeHtml(row.time_range)}<br>${escapeHtml(row.status)}</td><td>${escapeHtml(row.narration || row.visual_intent)}<br><small>Visual intent: ${escapeHtml(row.visual_intent)}</small></td><td>${proposals || "Unresolved: no eligible, fitting candidate."}</td>`;
+        el.stockProposalRows.appendChild(tr);
+      });
+      el.stockProposalStatus.textContent = `${table.rows.length} planned shots · all candidates are provisional; none assigned to the timeline.`;
+    } catch (error) {
+      el.stockProposalStatus.textContent = error.message;
+    } finally {
+      el.btnCompileStockProposals.disabled = false;
+    }
+  });
+}
+
 // ============================================================
 // STEP 2: FORMAT SELECTION & TIMELINE BREAKDOWN
 // ============================================================

Return exactly READY or REPAIR: followed by one bounded repair brief. If no safe repair is possible, return NOT_READY with a reason.
