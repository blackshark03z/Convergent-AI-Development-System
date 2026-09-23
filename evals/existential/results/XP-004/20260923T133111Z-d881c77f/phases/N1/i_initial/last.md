Implemented fail-closed source handling and partial format lineage, but **the brief’s acceptance outcome is not complete**.

- The timeline builder rejects unknown formats and requires real assets for each selected format. It records source SHA-256 values in the schedule and uses deterministic stock ordering.
- CLI render reloads and checks the schedule’s format identity, then the renderer verifies source hashes and uses source-and-timing-specific cache names. Missing render inputs now fail instead of becoming gradient placeholders.
- Updated timeline tests to use local fixture files.

**Checks:** `python -m compileall -q videopipeline tools`; focused tests passed (31); full suite passed (100); `git diff --check` passed.

**Evidence and limitations:** The checks establish schedule grammar and file handling. They do not prove rendered visuals against source assets. I did not implement the required offline five-format verification command, visual/source comparison, clean Git revision and final-master hash binding, full plan/timeline/compose lineage, or equivalent CLI/Web state resolution. F4 background/inset rendering and stale master eligibility also remain unverified. No Product Acceptance is claimed.

Changed files: [cli.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N1/videopipeline/cli.py), [models.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N1/videopipeline/models.py), [timeline_builder.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N1/videopipeline/stages/stage3_compose/timeline_builder.py), [nvenc_engine.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N1/videopipeline/stages/stage4_render/nvenc_engine.py), and [test_timeline_builder.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N1/videopipeline/tests/test_timeline_builder.py).