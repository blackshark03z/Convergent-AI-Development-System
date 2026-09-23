You are R. Inspect only the assigned disposable repository. Do not edit, stage, delete, or create any file. Do not cause external or production effects. Do not inspect the hidden oracle, historical reference, sibling arms, or their results.

You are a fresh non-editing R reviewer. Reconstruct continuity from this record. Do not edit files, inspect hidden evaluation, other arms, or historical references.

# XP-003 Reasoning Lead Prompt — N1 / Existing-minimal stack

You are R, the Reasoning Lead. You do not edit product code.

## Frozen Raw Owner Goal

Make the Story Audio assignment/review journey usable as one coherent user flow,
not merely a set of individually working controls. After speaker review/approval,
the Owner must see a clear result/status, know the next action, and be able to
continue into voice assignment/configuration without a hidden blocker or dead end.

## Fixed intent

- The affected journey is: select story -> prepare/review speakers -> assign voices -> save -> continue.
- Visible state must truthfully reflect remaining blockers.
- If a blocker remains, direct the Owner to the actual action required to clear it.
- Completing speaker review must expose a clear continuation into voice assignment/configuration.
- Saving/approving voice work must expose the next production action without silently starting render.
- Preserve unrelated Story Audio behavior.
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

**Outcome:** The Owner can follow the selected story scope from speaker review through voice configuration and into the next production gate, with a truthful status and a clear next action at each transition.

**Acceptance:**
- After speaker review or approval, show the result and the number of decisions still requiring review. An approved current review with zero remaining decisions must allow continuation into voice configuration, even if historical unresolved items exist.
- If speaker or voice work is blocked, identify the current blocker and provide a path to the action that clears it. Do not show a completed or ready state while a required blocker remains.
- Voice configuration is reachable from completed speaker review and shows the effective speaking roles for the selected scope. After voice changes are saved or approved, show the saved result and a clear action to the next required gate: final voice-map review where required, then production preflight when ready.
- Preserve the selected scope across these steps. Saving or approving must not implicitly PREPARE a Job, start render, call a provider, or change existing audio.

**Verification:** Demonstrate the connected journey in an isolated browser fixture, including an approved review with a nonzero historical unresolved count, a remaining blocker, and a successful voice save. Confirm that the visible next action matches authoritative readiness and that no render command is issued.

OWNER_INPUT_REQUIRED: no
R repair brief:
REPAIR: The added test verifies a resolver result, but the Owner’s production screen uses the backend task projection rather than that resolver. Demonstrate the live selected-scope journey in an isolated browser fixture with an approved current speaker review, zero remaining decisions, and a nonzero historical invalid count. Verify the visible review result and continuation to effective speaking roles; a remaining blocker links to the action that clears it; and a successful voice save leads to final voice-map review or production preflight as readiness requires. Confirm the scope is preserved and no PREPARE or render command is issued. Fix any live-flow failure the fixture exposes.

I completion report:
Implemented the speaker-review transition fix in [production_state.js](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-003/20260923T094959Z-0e1a1c3f/arms/N1/ui/production_state.js) and added a regression case in [test_production_state_resolver.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-003/20260923T094959Z-0e1a1c3f/arms/N1/tests/test_production_state_resolver.py). A non-stale, approved current draft with zero remaining decisions now proceeds to voice configuration even when its historical invalid count is nonzero. Stale drafts and drafts with remaining decisions still block progression.

**Checks run:** `python -m unittest tests.test_production_state_resolver tests.test_speaker_review_ui tests.test_assignment_workflow_browser` passed (35 tests). `git diff --check` passed.

**Evidence and limits:** The resolver test confirms the next action is voice-map creation for the approved-review case. I did not demonstrate the requested connected browser journey or verify a voice save, final voice-map review, preflight action, and absence of render commands in a browser. The available assignment browser test creates temporary data under `C:\StoryAudio_AssignmentFlow_Test`, outside this clone, so I did not run it. No browser preview was inspected; product discoverability and the complete journey remain unverified.
Repair report:
The existing isolated browser smoke passed, but it does not cover the repair brief’s required connected journey: its fixture stops at a speaker blocker or a completed range and does not save a voice assignment. I did not change the candidate, and the requested browser evidence remains incomplete.

**Check run:** `python -m unittest tests.test_production_workflow_browser` passed (2 tests).

**Limit:** I did not verify the approved review with historical invalid count, blocker recovery, successful voice save, next gate, preserved scope, or absence of PREPARE/render commands in one browser journey.

Candidate tree: 87b678d48cda363acf4ff0b766679f056d94ec25
Candidate status:
M  tests/test_production_state_resolver.py
M  ui/production_state.js
Candidate diff:
diff --git a/tests/test_production_state_resolver.py b/tests/test_production_state_resolver.py
index 5bcb021..2b45af2 100644
--- a/tests/test_production_state_resolver.py
+++ b/tests/test_production_state_resolver.py
@@ -159,6 +159,13 @@ class ProductionStateResolverTests(unittest.TestCase):
         payload["speakerDraft"] = {"id": 15, "status": "draft", "stale": False}
         self.assert_state(payload, "SPEAKER_EXCEPTIONS", "speakers")
 
+    def test_approved_current_speaker_review_ignores_historical_unresolved_count(self) -> None:
+        payload = base_state()
+        payload["casting"] = {"voice_profile": {"validation": {"valid": True}}}
+        payload["speakerDraft"].update({"status": "approved", "remaining_unreviewed_count": 0, "invalid_count": 3})
+        vm = self.assert_state(payload, "VOICE_BLOCKED", "voices")
+        self.assertEqual(vm["primaryActionKey"], "CREATE_VOICE_MAP_DRAFT")
+
     def test_missing_effective_voice_blocks_voice_configuration(self) -> None:
         payload = base_state()
         payload["voice"] = {"missingEffectiveVoiceCount": 1}
diff --git a/ui/production_state.js b/ui/production_state.js
index 4ccc49c..d2b2335 100644
--- a/ui/production_state.js
+++ b/ui/production_state.js
@@ -206,6 +206,8 @@
     if(draft.stale)return 'Speaker Draft đã cũ so với text/casting hiện tại.';
     if(lower(draft.status)!=='approved')return 'Speaker Draft chưa được duyệt.';
     if(n(draft.remaining_unreviewed_count)>0)return 'Speaker Draft vẫn còn dòng chưa review.';
+    // An approved current draft with no remaining decisions is complete even when historical unresolved totals remain.
+    if(lower(draft.status)==='approved'&&n(draft.remaining_unreviewed_count)===0)return '';
     if(n(draft.invalid_count)>0)return 'Speaker Draft còn dòng invalid.';
     return '';
   }

Return exactly READY or NOT_READY with a brief reason. No more repair is allowed.
