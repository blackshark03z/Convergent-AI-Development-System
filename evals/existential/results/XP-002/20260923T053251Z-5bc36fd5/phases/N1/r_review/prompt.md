You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-002 Reasoning Lead Prompt — N1 / Existing-minimal stack

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

Use ordinary product/developer documentation, existing tests and normal
engineering conventions available in the neutral repository. Do not create a
custom process/framework.

## Output for phase 1

Return only `IMPLEMENTATION_BRIEF`, `OWNER_INPUT_REQUIRED: yes|no`, and, if yes,
the minimum material question blocking a safe/testable handoff. After I returns
a candidate, you will receive its diff/evidence and may respond READY or one
REPAIR brief.


IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** For an F5 story, produce an Owner reviewable table with a proposal row for every planned shot. Derive each shot’s stock search intent from its script and shot meaning, then present a bounded set of relevant online stock candidates. A proposal is never a final production choice.

**Acceptance:**
- Every planned F5 shot has a row, including shots with no suitable match. Each row identifies the shot and its story or visual intent, and shows candidate identity, a preview reference when available, and enough fit or exception information for the Owner to judge it.
- Distinct shot intents yield distinct searches and relevant rankings. Generic storywide keywords alone cannot drive every row. Ineligible, clearly conflicting, or unsuitable candidates are not presented as usable matches.
- Candidate lists have a small, enforced upper bound. Search failure or no match remains explicit; it does not trigger an arbitrary substitute.
- Producing the table does not approve, download, assign, or commit footage to the final timeline. Offline tests with a fake stock provider demonstrate these outcomes without calling external services or the production runtime.

**Scope:** This covers proposal compilation and reviewability only. The later approve, replace, confirm, and cancel lifecycle is outside this brief.

OWNER_INPUT_REQUIRED: no

I completion report:
Implemented F5 stock proposal compilation in [online_stock.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/N1/videopipeline/stages/stage2_assets/online_stock.py) and added offline fake-provider coverage in [test_stock_proposals.py](/D:/CADS-Benchmark/XP-002-AUTO/arms/N1/tests/test_stock_proposals.py).

The compiler returns one review-only row per supplied shot, builds its search intent from shot meaning and visual requirements, and includes candidate identity, preview reference, fit score, and explicit no-match or search-failure status. Shortlists are capped at five; candidates with negligible semantic fit are filtered out. It does not download or assign footage.

Checks run: `python -m pytest tests/test_stock_proposals.py tests/test_stock_constraints.py -q` — **7 passed**. Fake-provider tests observed distinct shot searches, filtering of unsuitable candidates, bounded results, preview references, and explicit provider failure without external services.

Limitation: the compiler returns a structured table, but this change does not add a Studio UI or endpoint to display it. Candidate ranking uses the retriever’s existing metadata-based semantic scoring. No material Owner preference or authority decision was needed.

Candidate tree: b1d6b2d6c5b691a9d1fa0364910f385cffa39380
Candidate status:
A  tests/test_stock_proposals.py
M  videopipeline/stages/stage2_assets/online_stock.py
Candidate diff:
diff --git a/tests/test_stock_proposals.py b/tests/test_stock_proposals.py
new file mode 100644
index 0000000..39f5b64
--- /dev/null
+++ b/tests/test_stock_proposals.py
@@ -0,0 +1,74 @@
+from videopipeline.models import ShotSpec, VisualRequirement
+from videopipeline.stages.stage2_assets.online_stock import StoryStockRetriever
+
+
+class FakeStockProvider:
+    def __init__(self):
+        self.queries = []
+
+    def search_videos(self, query, per_page=12):
+        self.queries.append(query)
+        query_words = set(query.lower().split())
+        if "rain" in query_words:
+            videos = [
+                {"id": "rain-1", "online_id": "fake_rain_1", "title": "Rainy city street", "duration": 8,
+                 "width": 1920, "height": 1080, "rights_status": "ELIGIBLE", "preview_url": "https://fake/rain"},
+                {"id": "rain-2", "title": "Sunny beach", "duration": 8,
+                 "width": 1920, "height": 1080, "rights_status": "ELIGIBLE"},
+                {"id": "rain-3", "title": "Wet street portrait", "duration": 8,
+                 "width": 720, "height": 1280, "rights_status": "UNKNOWN"},
+            ]
+        else:
+            videos = [
+                {"id": f"office-{i}", "title": "Office worker at desk", "duration": 8,
+                 "width": 1920, "height": 1080, "rights_status": "ELIGIBLE", "preview_url": f"https://fake/{i}"}
+                for i in range(8)
+            ]
+        return {"status": "ok", "videos": videos}
+
+
+def _shot(shot_id, action, required, intent):
+    return ShotSpec(
+        shot_id=shot_id, scene_id="scene-1", duration_sec=5,
+        primary_subject="woman", primary_action=action,
+        visual_requirement=VisualRequirement(required_visuals=required,
+            forbidden_visuals=["beach"], stock_search_intent=intent),
+    )
+
+
+def test_f5_table_searches_each_shot_and_is_review_only():
+    provider = FakeStockProvider()
+    retriever = StoryStockRetriever(provider)
+    result = retriever.compile_f5_proposal_table([
+        _shot("s1", "walks alone in rain", ["rain", "street"], "rainy street at night"),
+        _shot("s2", "works at desk", ["office", "desk"], "office desk interior"),
+    ], max_candidates=8)
+
+    assert len(result["rows"]) == 2
+    assert provider.queries[0] != provider.queries[1]
+    assert all(row["proposal_only"] for row in result["rows"])
+    rain = result["rows"][0]
+    assert rain["shot_id"] == "s1"
+    assert [c["id"] for c in rain["candidates"]] == ["rain-1"]
+    assert rain["candidates"][0]["preview_reference"] == "https://fake/rain"
+    office = result["rows"][1]
+    assert len(office["candidates"]) == 5
+    assert all("AUTO_SELECT" not in row for row in result["rows"])
+
+
+def test_search_failure_and_no_match_are_explicit():
+    class FailingProvider:
+        def search_videos(self, query, per_page=12):
+            return {"status": "error", "message": "offline", "videos": []}
+
+    result = StoryStockRetriever(FailingProvider()).compile_f5_proposal_table([
+        _shot("s1", "walks in rain", ["rain"], "rainy street")
+    ])
+    assert result["rows"][0]["status"] == "SEARCH_FAILED"
+    assert result["rows"][0]["exception"]
+    assert result["rows"][0]["candidates"] == []
+
+
+def test_empty_planned_shots_produce_empty_table():
+    result = StoryStockRetriever(FakeStockProvider()).compile_f5_proposal_table([])
+    assert result["rows"] == []
diff --git a/videopipeline/stages/stage2_assets/online_stock.py b/videopipeline/stages/stage2_assets/online_stock.py
index efab3e8..05a364f 100644
--- a/videopipeline/stages/stage2_assets/online_stock.py
+++ b/videopipeline/stages/stage2_assets/online_stock.py
@@ -420,10 +420,14 @@ class StoryStockRetriever:
         """
         search_query = self.compile_search_query(intent)
 
+        # Keep the provider request bounded too; the shortlist limit is enforced below.
+        max_candidates = max(0, min(int(max_candidates), 5))
         raw_res = self.provider.search_videos(search_query, per_page=12)
         if raw_res.get("status") != "ok":
             return {
                 "disposition": "NO_MATCH",
+                "query_compiled": search_query,
+                "status": "SEARCH_FAILED",
                 "message": f"Provider search failed: {raw_res.get('message')}",
                 "candidates": []
             }
@@ -441,6 +445,8 @@ class StoryStockRetriever:
                 eligible.append(cand)
 
         ranked = self.rank_candidates(eligible, target_intent=intent, target_duration=min_duration)
+        # A candidate with negligible semantic fit is an arbitrary substitute, not a match.
+        ranked = [c for c in ranked if c.get("semantic_score", 0.0) >= 0.20]
         bounded_proposals = ranked[:max_candidates]
 
         if not bounded_proposals:
@@ -461,8 +467,76 @@ class StoryStockRetriever:
 
         return {
             "disposition": disposition,
+            "status": "MATCHES_FOUND",
             "query_compiled": search_query,
             "total_evaluated": len(candidates),
             "candidates": bounded_proposals,
             "selected_candidate": top_candidate if disposition == "AUTO_SELECT" else None
         }
+
+    @staticmethod
+    def _shot_value(shot: Any, key: str, default: Any = "") -> Any:
+        if isinstance(shot, dict):
+            return shot.get(key, default)
+        return getattr(shot, key, default)
+
+    def compile_f5_proposal_table(
+        self,
+        planned_shots: List[Any],
+        narration_by_shot: Optional[Dict[str, str]] = None,
+        max_candidates: int = 3,
+        min_duration: float = 4.0,
+    ) -> Dict[str, Any]:
+        """Build owner-reviewable F5 proposals without selecting or acquiring footage."""
+        narration_by_shot = narration_by_shot or {}
+        rows = []
+        for shot in planned_shots:
+            shot_id = str(self._shot_value(shot, "shot_id", ""))
+            scene_id = str(self._shot_value(shot, "scene_id", ""))
+            duration = float(self._shot_value(shot, "duration_sec", 0.0) or 0.0)
+            requirement = self._shot_value(shot, "visual_requirement", None)
+            action = str(self._shot_value(shot, "primary_action", "") or "")
+            subject = str(self._shot_value(shot, "primary_subject", "") or "")
+            intent_parts = [subject, action]
+            if requirement is not None:
+                intent_parts.extend(self._shot_value(requirement, "required_visuals", []) or [])
+                intent_parts.append(self._shot_value(requirement, "stock_search_intent", "") or "")
+            forbidden = self._shot_value(requirement, "forbidden_visuals", []) or [] if requirement is not None else []
+            intent = " ".join(str(p) for p in intent_parts if str(p).strip())
+            narration = narration_by_shot.get(shot_id, "")
+            query = self.compile_search_query(intent, narration=narration)
+            result = self.retrieve_candidates_for_requirement(
+                intent or narration or query,
+                min_duration=max(min_duration, duration),
+                forbidden_terms=list(forbidden),
+                max_candidates=max_candidates,
+            )
+            candidates = []
+            for candidate in result.get("candidates", []):
+                candidates.append({
+                    "id": candidate.get("id"),
+                    "online_id": candidate.get("online_id"),
+                    "title": candidate.get("title", ""),
+                    "source": candidate.get("source", ""),
+                    "preview_reference": candidate.get("thumbnail") or candidate.get("preview_url") or "",
+                    "preview_url": candidate.get("preview_url", ""),
+                    "duration": candidate.get("duration", 0),
+                    "fit_score": candidate.get("semantic_score", 0.0),
+                    "fit_reason": "Eligible stock candidate ranked against this shot's visual intent",
+                })
+            status = result.get("status", "NO_MATCH")
+            if not candidates and status != "SEARCH_FAILED":
+                status = "NO_MATCH"
+            rows.append({
+                "shot_id": shot_id,
+                "scene_id": scene_id,
+                "duration_sec": duration,
+                "story_intent": action or subject or narration,
+                "visual_intent": intent,
+                "search_query": result.get("query_compiled", query),
+                "status": status,
+                "exception": result.get("message", "") if not candidates else "",
+                "candidates": candidates,
+                "proposal_only": True,
+            })
+        return {"status": "ok", "format": "F5", "proposal_only": True, "rows": rows}

Return exactly READY or REPAIR: followed by one bounded repair brief. If no safe repair is possible, return NOT_READY with a reason.
