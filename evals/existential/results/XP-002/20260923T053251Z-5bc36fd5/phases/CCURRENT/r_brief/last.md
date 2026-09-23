IMPLEMENTATION_BRIEF

**Outcome:** For an F5 story, the product presents a bounded stock-video proposal table for every planned shot, derived from that shot’s script and visual intent. The Owner can inspect the proposals before any footage becomes a final production choice.

**Acceptance:**
- Each shot has a row showing its scene/shot and narration interval, visual purpose, a small ranked shortlist with identifiable source and preview, a brief fit reason, and any uncertainty or conflict. Shots without a suitable candidate remain visible as `NO_MATCH` or needing review.
- Representative shots with different actions or settings produce meaningfully different proposals even when they share broad story keywords. Ineligible or story-contradicting clips cannot become the proposed lead choice.
- The table clearly labels choices as proposals. Compiling or viewing it does not approve footage, download final assets, or silently change the F5 format or production timeline.
- Candidate evidence demonstrates the F5 review journey using an offline provider fixture, including a suitable match, a conflicting or ineligible result, and a no-match shot. Tie that evidence to the implementation candidate submitted for review.

**Constraints / non-goals:** Reuse the existing F5 shot plan and stock retrieval behavior where suitable. This slice covers proposal compilation and inspection only; approval, replacement, rough-cut production, and final acquisition are outside scope. No paid or external provider calls or canonical production runtime.

OWNER_INPUT_REQUIRED: no