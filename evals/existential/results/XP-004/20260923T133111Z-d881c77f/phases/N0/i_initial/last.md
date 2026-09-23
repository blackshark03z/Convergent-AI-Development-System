I implemented a partial candidate, but it does **not** meet the full acceptance brief.

Changed:

- [format_validator.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N0/videopipeline/format_validator.py): added strict canonical format resolution and optional checks that required media exists, is nonempty, and has an image or video extension consistent with its claimed class.
- [timeline_builder.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N0/videopipeline/stages/stage3_compose/timeline_builder.py): rejects unknown formats and removes fabricated missing-asset paths for F1–F5.
- [cli.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N0/videopipeline/cli.py) and [server.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N0/videopipeline/web/server.py): persist the selected format in composed schedules; CLI render rejects a compose/render format mismatch and validates media.
- [nvenc_engine.py](/C:/Users/ADMIN/AppData/Local/Temp/cads-existential/XP-004/20260923T133111Z-d881c77f/arms/N0/videopipeline/stages/stage4_render/nvenc_engine.py): rejects missing render media instead of substituting a generated background frame.

Checks run:

- `python -m compileall -q videopipeline` passed.
- `python -m pytest tests/test_format_grammar.py tests/test_negative_mutations.py -q` passed: 26 tests.
- `python -m pytest -q` ran 100 tests: 99 passed, 1 failed. The existing F4 timeline test supplies nonexistent media paths; the builder now rejects the missing original source, as required by the brief.

I did not render local fixture videos or exercise the Web path end to end. The existing renderer manifest records output and claimed asset classes, but the implementation here does not bind a verified plan/timeline/compose/render run or hash source assets. It also does not verify source class beyond file extension, so it cannot distinguish generated video from stock footage by inspecting media alone. F4’s actual background-stock plus original-video inset rendering path remains unverified. These gaps mean this candidate cannot claim product acceptance.