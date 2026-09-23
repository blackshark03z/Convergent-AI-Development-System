# XP-003 Frozen Owner Goal

Case: XP-003
Source failure class: AE-002 — end-to-end journey composition
Product: Story Trans And Audio
Base revision: `e07820fcc43f1dbfb1de84feb32fee6cfd4329f2`
Historical reference: `25a09b4`

## Owner Goal

Make the Story Audio assignment/review journey usable as one coherent user flow,
not merely a set of individually working controls.

After speaker review/approval, the Owner must see a clear result/status, know the
next action, and be able to continue into voice assignment/configuration without
a hidden blocker or dead end.

The affected journey should preserve the broader product job:

`Select story -> prepare/review speakers -> assign voices -> save -> continue`

## Fixed constraints

- Do not ask the Owner to prescribe implementation details.
- Do not report success merely because an isolated button/API/unit test works.
- Visible state must truthfully reflect remaining blockers.
- When a blocker remains, the UI/flow must direct the Owner to the actual action
  needed rather than showing a misleading zero/complete state.
- Preserve unrelated Story Audio behavior.
- The historical reference implementation is hidden from the candidate.

This Goal text is identical across N0, N1, C-min and C-current.
