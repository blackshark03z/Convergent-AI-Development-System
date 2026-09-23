# XP-002 Frozen Owner Goal

Case: XP-002
Source failure class: AE-022 — material intent ambiguity
Product: AutoVideoPipeline
Base revision: `eb0a6480962612865a4974c960e6c6547b7b2009`
Historical reference: `9051238`

## Owner Goal

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
- The historical reference implementation is hidden from the candidate.

This Goal text is identical across N0, N1, C-min and C-current.
