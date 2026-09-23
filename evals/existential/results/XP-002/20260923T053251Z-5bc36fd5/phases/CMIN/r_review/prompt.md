You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-002 Reasoning Lead Prompt — C-min / Minimum CADS residue

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

Preserve only: material Outcome/Intent ambiguity must be bounded and testable;
I DONE and R READY are not Product Acceptance; evidence must apply to the exact
candidate; implementation authority does not grant external effects; assurance
is proportional and unnecessary scaffolding should be omitted.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.


IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** For an F5 story, produce a bounded, reviewable stock-video proposal table for every planned shot, using that shot’s script and visual intent.

**Acceptance:**
- Each planned shot has a row identifying the shot, its relevant story/visual intent, and either a proposed online stock candidate or an explicit no-match disposition.
- Proposed candidates have a stable provider identity, a reviewable preview reference, and a brief reason they fit the shot. Alternatives, if shown, are bounded.
- Evidence with distinct shot intents shows proposals respond to those differences rather than applying one generic story-wide keyword choice. Material visual conflicts and ineligible footage are not presented as viable choices.
- Producing the table does not approve clips, commit them to the final timeline, acquire production media, or mark them used.

**Constraints / evidence:** Preserve F5’s online-stock-only source policy. Verify the exact candidate with offline fixtures or mocked providers; do not call external providers or the canonical production runtime. The later approve/replace/confirm/cancel lifecycle is outside this brief. I DONE and R READY do not constitute Product Acceptance.

OWNER_INPUT_REQUIRED: no

I completion report:
Implemented a read-only, shot-by-shot stock proposal operation. Each row includes the shot ID, script and visual intent, search query, and either up to two candidates or a `NO_MATCH` disposition. Candidates include provider identity, preview reference, and a fit reason. The filter excludes footage that fails hard eligibility checks or has very low semantic fit.

**Files changed:** [online_stock.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/CMIN/videopipeline/stages/stage2_assets/online_stock.py), [server.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/CMIN/videopipeline/web/server.py), and [test_stock_shot_proposals.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/CMIN/tests/test_stock_shot_proposals.py). The API is `POST /api/stock/shot_proposals` and accepts planned shots in its request body.

**Checks run:** 10 targeted tests passed; Python compilation passed; `git diff --check` passed. The tests use a fixture provider and show that distinct shot intents produce distinct queries and candidates, while contradictory and too-short footage is excluded. No external provider was called.

The operation returns `PROPOSAL_ONLY`; it does not download media, mark clips used, or change the timeline. The current API requires the caller to supply planned-shot data; automatic loading from an F5 story plan and a Studio table view are not wired in. No Product Acceptance is claimed.

Candidate tree: 62a0571b2601a3b28a500659a1282be4bb8c9ae4
Candidate status:
A  tests/test_stock_shot_proposals.py
M  videopipeline/stages/stage2_assets/online_stock.py
M  videopipeline/web/server.py
Candidate diff:
diff --git a/tests/test_stock_shot_proposals.py b/tests/test_stock_shot_proposals.py
new file mode 100644
index 0000000..919c8d6
--- /dev/null
+++ b/tests/test_stock_shot_proposals.py
@@ -0,0 +1,40 @@
+from videopipeline.stages.stage2_assets.online_stock import StoryStockRetriever
+
+
+class FixtureProvider:
+    def __init__(self):
+        self.queries = []
+
+    def search_videos(self, query, per_page=12):
+        self.queries.append(query)
+        fixtures = {
+            "woman walking rainy street": [self.clip("rain-walk", "Woman walking on a rainy street", tags=["woman", "rain", "street"]),
+                                           self.clip("sun-beach", "Sunny beach", tags=["sunny", "beach"])],
+            "man typing office desk": [self.clip("man-desk", "Man typing at an office desk", tags=["man", "typing", "office", "desk"]),
+                                       self.clip("short", "Man at desk", duration=2)],
+        }
+        return {"status": "ok", "videos": fixtures.get(query, [])}
+
+    @staticmethod
+    def clip(identity, title, tags=None, duration=8):
+        return {"id": identity, "online_id": "pexels_" + identity, "source": "pexels", "title": title,
+                "tags": tags or [], "duration": duration, "width": 1920, "height": 1080,
+                "thumbnail": "https://preview.example/" + identity}
+
+
+def test_proposal_table_is_per_shot_bounded_and_filters_conflicts_and_ineligible():
+    provider = FixtureProvider()
+    retriever = StoryStockRetriever(provider)
+    rows = retriever.build_shot_proposal_table([
+        {"shot_id": "s1", "script": "woman walking rainy street", "duration_sec": 5,
+         "visual_requirement": {"stock_search_intent": "woman walking rainy street"}},
+        {"shot_id": "s2", "script": "man typing office desk", "duration_sec": 5,
+         "visual_requirement": {"stock_search_intent": "man typing office desk"}},
+    ])
+
+    assert len(rows) == 2
+    assert rows[0]["shot_id"] == "s1" and rows[1]["shot_id"] == "s2"
+    assert provider.queries == ["woman walking rainy street", "man typing office desk"]
+    assert [row["candidates"][0]["provider_id"] for row in rows] == ["pexels_rain-walk", "pexels_man-desk"]
+    assert all(row["disposition"] == "PROPOSED" and len(row["candidates"]) <= 2 for row in rows)
+    assert all(c["preview_reference"] and c["reason"] for row in rows for c in row["candidates"])
diff --git a/videopipeline/stages/stage2_assets/online_stock.py b/videopipeline/stages/stage2_assets/online_stock.py
index efab3e8..2504ab0 100644
--- a/videopipeline/stages/stage2_assets/online_stock.py
+++ b/videopipeline/stages/stage2_assets/online_stock.py
@@ -466,3 +466,50 @@ class StoryStockRetriever:
             "candidates": bounded_proposals,
             "selected_candidate": top_candidate if disposition == "AUTO_SELECT" else None
         }
+
+    def build_shot_proposal_table(self, shots: List[Dict[str, Any]], alternatives: int = 2) -> List[Dict[str, Any]]:
+        """Build a read-only, bounded stock proposal row for each planned shot."""
+        rows = []
+        for shot in shots:
+            vr = shot.get("visual_requirement") or {}
+            if not isinstance(vr, dict):
+                vr = {
+                    "stock_search_intent": getattr(vr, "stock_search_intent", ""),
+                    "required_visuals": getattr(vr, "required_visuals", []),
+                    "forbidden_visuals": getattr(vr, "forbidden_visuals", []),
+                }
+            intent_parts = [shot.get("script", ""), shot.get("primary_subject", ""),
+                            shot.get("primary_action", ""), shot.get("action_or_event", ""),
+                            vr.get("stock_search_intent", ""), " ".join(vr.get("required_visuals", []))]
+            intent = " ".join(str(p).strip() for p in intent_parts if p and str(p).strip())
+            # Compile per-shot script/action together with the structured visual requirement.
+            query = self.compile_search_query(intent)
+            result = self.provider.search_videos(query, per_page=12) if query else {"status": "ok", "videos": []}
+            accepted = []
+            if result.get("status") == "ok":
+                for candidate in result.get("videos", []):
+                    ok, _ = StockConstraintChecker.evaluate(
+                        candidate, min_duration=min(4.0, float(shot.get("duration_sec") or 4.0)),
+                        forbidden_terms=vr.get("forbidden_visuals", []))
+                    score = self.compute_semantic_similarity(candidate, intent)
+                    # Do not present semantically unrelated or contradicted footage as viable.
+                    if ok and score >= 0.20:
+                        accepted.append(candidate)
+            ranked = self.rank_candidates(accepted, intent, float(shot.get("duration_sec") or 5.0))[:max(1, min(int(alternatives), 3))]
+            candidates = [{
+                "provider": str(c.get("source") or "pexels"),
+                "provider_id": str(c.get("online_id") or c.get("id") or ""),
+                "preview_reference": c.get("thumbnail") or c.get("preview_url") or "",
+                "title": c.get("title", ""),
+                "reason": f"Matches the shot’s visual intent (fit {c.get('semantic_score', 0):.2f}).",
+                "semantic_score": c.get("semantic_score", 0),
+            } for c in ranked if (c.get("online_id") or c.get("id")) and (c.get("thumbnail") or c.get("preview_url"))]
+            rows.append({
+                "shot_id": shot.get("shot_id", ""),
+                "script": shot.get("script", ""),
+                "visual_intent": intent,
+                "search_query": query,
+                "disposition": "PROPOSED" if candidates else "NO_MATCH",
+                "candidates": candidates,
+            })
+        return rows
diff --git a/videopipeline/web/server.py b/videopipeline/web/server.py
index 56ccf83..12bcd04 100644
--- a/videopipeline/web/server.py
+++ b/videopipeline/web/server.py
@@ -27,7 +27,7 @@ from ..stages.stage1_ingest.scene_planner import plan_story_scenes
 from ..stages.stage2_assets.stock_manager import StockManager
 from ..stages.stage2_assets.veo_client import GoogleFlowVeoClient
 from ..stages.stage2_assets.flow_generator import check_cookie_expiry
-from ..stages.stage2_assets.online_stock import PexelsClient
+from ..stages.stage2_assets.online_stock import PexelsClient, StoryStockRetriever
 from ..stages.stage3_compose.timeline_builder import TimelineBuilder
 from ..stages.stage3_compose.ass_karaoke import generate_karaoke_ass
 from ..stages.stage4_render.nvenc_engine import NvencRenderEngine
@@ -1210,6 +1210,21 @@ async def handle_online_stock_search(request):
     except Exception as e:
         return web.json_response({"status": "error", "message": f"Lỗi tìm kiếm online stock: {e}"}, status=500)
 
+async def handle_stock_shot_proposals(request):
+    """Returns a bounded, read-only proposal table for supplied planned shots."""
+    try:
+        data = await request.json()
+        shots = data.get("shots", [])
+        if not isinstance(shots, list) or not shots:
+            return web.json_response({"status": "error", "message": "shots must be a non-empty list"}, status=400)
+        loop = asyncio.get_event_loop()
+        retriever = StoryStockRetriever(PexelsClient())
+        rows = await loop.run_in_executor(None, lambda: retriever.build_shot_proposal_table(shots, alternatives=2))
+        return web.json_response({"status": "ok", "disposition": "PROPOSAL_ONLY", "rows": rows})
+    except Exception as e:
+        return web.json_response({"status": "error", "message": str(e)}, status=400)
+
+
 async def handle_online_stock_download_and_swap(request):
     """Downloads an online stock video and assigns it to a target segment (ADR-009)."""
     try:
@@ -1513,6 +1528,7 @@ def create_app() -> web.Application:
     app.router.add_get("/api/assets/available_clips", handle_get_available_clips)
     app.router.add_post("/api/schedule/swap_segment", handle_action_swap_segment)
     app.router.add_get("/api/stock/online/search", handle_online_stock_search)
+    app.router.add_post("/api/stock/shot_proposals", handle_stock_shot_proposals)
     app.router.add_post("/api/stock/online/download_and_swap", handle_online_stock_download_and_swap)
     app.router.add_get("/api/stock_exceptions", handle_get_stock_exceptions)
     app.router.add_get("/api/editorial_qc/report", handle_get_editorial_qc_report)

Return exactly READY or REPAIR: followed by one bounded repair brief. If no safe repair is possible, return NOT_READY with a reason.
