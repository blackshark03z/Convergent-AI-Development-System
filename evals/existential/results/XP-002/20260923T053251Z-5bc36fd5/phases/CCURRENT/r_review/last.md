REPAIR:

**Outcome:** Make the F5 proposal table cover every planned stock shot across the full story, with proposals tied to each shot’s script and visual intent.

**Acceptance:**
- An offline F5 story produces one row per planned shot, including the opening, with correct shot identity and narration interval. The current endpoint reads only cached `body_scenes`, while the F5 timeline covers the full story.
- Shots with different actions or settings yield meaningfully different proposals even when they share broad visual terms. Ineligible or contradictory clips cannot lead; unmatched shots remain visible.
- The review table displays each proposal’s fit reason as well as conflicts or uncertainty. The current UI receives `fit_reason` but does not show it.
- Candidate-bound offline evidence exercises the F5 request and rendered review journey, beyond the compiler-only fixture, without external provider or production calls.