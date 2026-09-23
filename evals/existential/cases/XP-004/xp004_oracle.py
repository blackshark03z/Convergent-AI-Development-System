"""Held-out, offline product-path probe for XP-004."""
from __future__ import annotations

import contextlib
import asyncio
import hashlib
import io
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class OracleFailure(AssertionError):
    pass


def require(ok: bool, why: str) -> None:
    if not ok:
        raise OracleFailure(why)


def classes(schedule) -> list[str]:
    return [getattr(s.source_class, "value", str(s.source_class)) for s in schedule.segments]


def check_format(fmt, schedule, supplied: set[Path], plan, creative) -> None:
    from videopipeline.format_validator import FormatValidator

    name = fmt.value
    actual = classes(schedule)
    require(schedule.format_id == name, f"{name}: selected format changed in timeline")
    require(bool(actual) and all(s.source_path in supplied for s in schedule.segments),
            f"{name}: timeline silently substituted an unselected asset")
    require(all(s.asset_id == s.source_path.stem for s in schedule.segments),
            f"{name}: asset identity differs from timeline source")
    require(FormatValidator.validate_timeline(schedule.segments, plan)["valid"] is True,
            f"{name}: format grammar rejected real timeline")
    if name == "F1":
        require(actual[0] == "GENERATED_VIDEO" and set(actual[1:]) == {"GENERATED_IMAGE"},
                "F1: opening/body source semantics changed")
    elif name == "F2":
        require(actual[0] == "GENERATED_VIDEO" and {"STOCK_ONLINE", "GENERATED_VIDEO"} <= set(actual[1:]),
                "F2: post-opening mix lost a required source class")
    elif name == "F3":
        require(set(actual) == {"GENERATED_IMAGE"}, "F3: non-image source accepted")
    elif name == "F4":
        require(set(actual) == {"ORIGINAL_REUP_VIDEO", "STOCK_ONLINE"},
                "F4: inset/background source pair changed")
    elif name == "F5":
        require(set(actual) == {"STOCK_ONLINE"}, "F5: generated or original source accepted")
    expected = {
        "creative_plan_fingerprint": creative.fingerprint,
        "format_plan_fingerprint": plan.fingerprint,
        "effect_profile_fingerprint": plan.effect_profile.fingerprint,
    }
    for field, value in expected.items():
        require(bool(value) and getattr(schedule, field, None) == value,
                f"{name}: {field} lost between plan and timeline")
    for field in ("editorial_timeline_fingerprint", "compose_plan_fingerprint"):
        require(bool(getattr(schedule, field, None)), f"{name}: {field} absent from compose state")


def run() -> dict:
    from videopipeline.models import CreativePlan, FormatId, SourceClass, create_default_format_plan
    from videopipeline.stages.stage3_compose.timeline_builder import TimelineBuilder
    from videopipeline.stages.stage4_render.nvenc_engine import NvencRenderEngine
    from videopipeline.stages.stage3_compose.motion_slideshow import CinematicMotionEngine
    from videopipeline.cli import cmd_render
    from videopipeline.format_validator import FORMAT_GRAMMAR_VIOLATION
    from videopipeline.web.server import handle_get_schedule_segments

    evidence = {}
    with tempfile.TemporaryDirectory(prefix="xp004-path-") as temp:
        root = Path(temp)
        story = root / "dummy_story"
        story.mkdir()
        audio = story / "narration.m4a"
        audio.write_bytes(b"offline fixture")
        opening = story / "veo_open.mp4"
        second_veo = story / "veo_body.mp4"
        original = story / "source_video.mp4"
        stocks = [story / f"stock_{i}.mp4" for i in range(1, 5)]
        images = [story / f"flow_{i}.jpg" for i in range(1, 4)]
        for path in (opening, second_veo, original, *stocks, *images):
            path.write_bytes(b"local asset identity: " + path.name.encode("ascii"))
        supplied = {opening, second_veo, original, *stocks, *images}

        class FakeProcess:
            pid = 4004
            returncode = 0

            def __init__(self, command, **_kwargs):
                require(command[0] == "ffmpeg" and command[-1].endswith(".mp4"),
                        "render command did not target a master output")
                render_inputs = [command[index + 1] for index, token in enumerate(command[:-1]) if token == "-i"]
                require(str(story / "fast_pipeline" / "concat_segments.txt") in render_inputs and
                        str(audio) in render_inputs,
                        "render command did not consume the verified timeline and narration")
                Path(command[-1]).write_bytes(("offline render command " + " ".join(command)).encode("utf-8") * 200)

            def communicate(self):
                return "", ""

        def fake_normalize(self, schedule):
            # Preserve the real schedule, CLI reload, render command and manifest path.
            # Only the expensive media normalization is replaced.
            return [segment.source_path for segment in schedule.segments]

        with patch.object(NvencRenderEngine, "normalize_all_segments", fake_normalize), \
             patch("videopipeline.stages.stage4_render.nvenc_engine.subprocess.Popen", FakeProcess), \
             patch.object(CinematicMotionEngine, "create_radio_hud_overlay", return_value=None):
            for fmt in FormatId:
                name = fmt.value
                plan = create_default_format_plan(fmt)
                creative = CreativePlan("offline-plan", "Same story", plan)
                require(bool(creative.fingerprint), f"{name}: creative plan has no identity")
                builder = TimelineBuilder(story, audio, 145.0 if name == "F2" else 90.0)
                with contextlib.redirect_stdout(io.StringIO()):
                    schedule = builder.build_schedule(
                        chap1_source=original if name == "F4" else opening,
                        stock_clips=stocks, veo_clips=[second_veo], images=images,
                        format=plan, creative_plan=creative,
                    )
                check_format(fmt, schedule, supplied, plan, creative)
                work = story / "fast_pipeline"
                schedule_file = work / "video_schedule.json"
                builder.save_schedule_json(schedule, schedule_file)
                (work / "master_karaoke.ass").write_text("[Script Info]\n", encoding="utf-8")
                restored = TimelineBuilder.load_schedule_json(schedule_file)
                require(restored.to_dict() == schedule.to_dict(), f"{name}: saved schedule lost source or lineage")
                web_response = asyncio.run(handle_get_schedule_segments(
                    SimpleNamespace(query={"dir": str(story), "format": name.lower()})
                ))
                web_state = json.loads(web_response.text)
                require(web_response.status == 200 and web_state.get("status") == "ok",
                        f"{name}: Web cannot read the saved product timeline")
                require([row.get("source_path") for row in web_state.get("segments", [])] ==
                        [str(segment.source_path.resolve()) for segment in restored.segments],
                        f"{name}: Web timeline differs from CLI compose state")
                require(all(row.get("exists") and row.get("size_bytes") ==
                            restored.segments[index].source_path.stat().st_size
                            for index, row in enumerate(web_state["segments"])),
                        f"{name}: Web shows an unavailable or changed source asset")

                class Args:
                    story_dir = str(story)
                    format = name.lower()
                    output_name = f"master_{name}.mp4"
                    accept_override = False

                with contextlib.redirect_stdout(io.StringIO()):
                    cmd_render(Args())
                output = story / "Final_Video_Export" / Args.output_name
                manifest_file = output.parent / "run_manifest.json"
                require(output.exists() and manifest_file.exists(), f"{name}: render output or manifest absent")
                concat_file = work / "concat_segments.txt"
                require(concat_file.exists() and concat_file.read_text(encoding="utf-8").splitlines() ==
                        [f"file '{segment.source_path.resolve().as_posix()}'" for segment in restored.segments],
                        f"{name}: render input list differs from selected timeline assets")
                manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                require(manifest.get("format_id") == name, f"{name}: final manifest selected format changed")
                require(manifest.get("output_file") == str(output),
                        f"{name}: manifest points to a different product output")
                for field in ("creative_plan_fingerprint", "format_plan_fingerprint",
                              "editorial_timeline_fingerprint", "compose_plan_fingerprint",
                              "effect_profile_fingerprint"):
                    require(bool(getattr(restored, field, None)) and manifest.get(field) == getattr(restored, field),
                            f"{name}: final manifest {field} differs from verified compose state")
                require(manifest.get("output_sha256") == hashlib.sha256(output.read_bytes()).hexdigest(),
                        f"{name}: final artifact hash differs from manifest")
                require([a.get("source_class") for a in manifest.get("assets_used", [])] == classes(restored),
                        f"{name}: rendered source classes differ from verified timeline")
                require([a.get("asset_id") for a in manifest["assets_used"]] ==
                        [s.asset_id for s in restored.segments],
                        f"{name}: rendered asset identities differ from verified timeline")
                require([a.get("source_path") for a in manifest["assets_used"]] ==
                        [str(s.source_path) for s in restored.segments],
                        f"{name}: rendered source paths differ from verified timeline")
                evidence[name] = {"segments": len(restored.segments), "source_classes": sorted(set(classes(restored))),
                                  "lineage_bound": True, "web_readback_bound": True,
                                  "render_inputs_bound": True, "output_hash_bound": True}

                if name == "F3":
                    changed_story = CreativePlan("offline-plan", "Changed story", plan)
                    changed_plan = builder.build_schedule(
                        chap1_source=opening, stock_clips=stocks, veo_clips=[second_veo],
                        images=images, format=plan, creative_plan=changed_story,
                    )
                    require(changed_plan.creative_plan_fingerprint != schedule.creative_plan_fingerprint and
                            changed_plan.editorial_timeline_fingerprint != schedule.editorial_timeline_fingerprint and
                            changed_plan.compose_plan_fingerprint != schedule.compose_plan_fingerprint,
                            "F3: changed creative plan did not change downstream lineage")
                    alternate = story / "different_flow.jpg"
                    alternate.write_bytes(b"different local image")
                    changed_asset = builder.build_schedule(
                        chap1_source=opening, stock_clips=stocks, veo_clips=[second_veo],
                        images=[alternate, *images[1:]], format=plan, creative_plan=creative,
                    )
                    require(changed_asset.editorial_timeline_fingerprint != schedule.editorial_timeline_fingerprint and
                            changed_asset.compose_plan_fingerprint != schedule.compose_plan_fingerprint,
                            "F3: changed selected asset did not change downstream lineage")
                    evidence[name]["lineage_sensitive"] = True

                if name == "F5":
                    tampered = json.loads(schedule_file.read_text(encoding="utf-8"))
                    tampered["segments"][0]["source_class"] = SourceClass.GENERATED_VIDEO.value
                    schedule_file.write_text(json.dumps(tampered), encoding="utf-8")
                    output.unlink()
                    try:
                        with contextlib.redirect_stdout(io.StringIO()):
                            cmd_render(Args())
                    except FORMAT_GRAMMAR_VIOLATION:
                        pass
                    else:
                        raise OracleFailure("F5: render boundary accepted tampered generated media")
                    require(not output.exists(), "F5: tampered timeline produced output")
                    evidence[name]["tamper_blocked"] = True
    return evidence


if __name__ == "__main__":
    try:
        print(json.dumps({"status": "PASS", "evidence": run()}, ensure_ascii=True))
        raise SystemExit(0)
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "reason": f"{type(exc).__name__}: {exc}"}, ensure_ascii=True))
        raise SystemExit(1)
