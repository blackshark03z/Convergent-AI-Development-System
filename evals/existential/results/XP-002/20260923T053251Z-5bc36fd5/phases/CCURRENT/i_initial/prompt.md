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


IMPLEMENTATION_BRIEF
IMPLEMENTATION_BRIEF

**Outcome:** For an F5 story, the product presents a bounded stock-video proposal table for every planned shot, derived from that shot’s script and visual intent. The Owner can inspect the proposals before any footage becomes a final production choice.

**Acceptance:**
- Each shot has a row showing its scene/shot and narration interval, visual purpose, a small ranked shortlist with identifiable source and preview, a brief fit reason, and any uncertainty or conflict. Shots without a suitable candidate remain visible as `NO_MATCH` or needing review.
- Representative shots with different actions or settings produce meaningfully different proposals even when they share broad story keywords. Ineligible or story-contradicting clips cannot become the proposed lead choice.
- The table clearly labels choices as proposals. Compiling or viewing it does not approve footage, download final assets, or silently change the F5 format or production timeline.
- Candidate evidence demonstrates the F5 review journey using an offline provider fixture, including a suitable match, a conflicting or ineligible result, and a no-match shot. Tie that evidence to the implementation candidate submitted for review.

**Constraints / non-goals:** Reuse the existing F5 shot plan and stock retrieval behavior where suitable. This slice covers proposal compilation and inspection only; approval, replacement, rough-cut production, and final acquisition are outside scope. No paid or external provider calls or canonical production runtime.

OWNER_INPUT_REQUIRED: no

Work only inside this disposable clone. Do not call external or production services, paid providers, or mutate any path outside this clone. Do not inspect benchmark harness, oracle, reference, or sibling arms. Report NEEDS_OWNER if material Owner intent or authority is missing.
