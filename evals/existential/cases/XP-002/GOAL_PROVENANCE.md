# XP-002 Goal Provenance

Status: reconstructed from pre-implementation Owner conversation evidence, not
from the reference diff.

## Source evidence

On 2026-09-22 the Owner stated that F5 must analyze the script and propose video
per shot in a table so the Owner can inspect the proposed material. The same
conversation distinguished proposal from the later review/approval/replacement
lifecycle.

A later implementation summary identified:
- `eb0a648...` as the shot-based stock coverage baseline; and
- `9051238...` as the bounded stock-proposal step.

## Anti-leak rule

The frozen Goal intentionally does not expose:
- exact data structures;
- shortlist length;
- ranking formula;
- filenames/classes;
- historical patch shape;
- later approval-state implementation.

Those belong to the hidden reference/evaluator side, not the candidate prompt.
