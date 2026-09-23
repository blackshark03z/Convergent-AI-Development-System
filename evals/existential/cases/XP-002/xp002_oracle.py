from __future__ import annotations

import importlib
import inspect
import json
import os
import pkgutil
import socket
import subprocess
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

SEMANTIC = ("proposal", "propose", "plan", "planner", "stock")
METHOD = ("proposal", "propose", "plan", "compile", "build")
RESULT_KEYS = ("proposals", "items", "results", "recommendations", "suggestions")


class OracleFailure(RuntimeError):
    pass


class StaticProvider:
    def __init__(self, videos: list[dict[str, Any]]):
        self.videos = videos
        self.queries: list[str] = []

    def search_videos(self, query: str, page: int = 1, per_page: int = 12):
        self.queries.append(str(query))
        return {"status": "ok", "videos": list(self.videos), "total_results": len(self.videos)}


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if hasattr(value, "__dict__") and not isinstance(value, type):
        return {k: _plain(v) for k, v in vars(value).items() if not k.startswith("_")}
    return value


def _normalize(result: Any) -> list[dict[str, Any]] | None:
    result = _plain(result)
    if isinstance(result, list):
        values = result
    elif isinstance(result, dict):
        values = None
        for key in RESULT_KEYS:
            if isinstance(result.get(key), list):
                values = result[key]
                break
        if values is None and any(k in result for k in ("shot_id", "source_shot_id", "shot")):
            values = [result]
        if values is None:
            return None
    else:
        return None
    normalized = []
    for item in values:
        item = _plain(item)
        if isinstance(item, dict):
            normalized.append(item)
    return normalized


def _pick(d: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in d:
            return d[key]
    return None


def _semantic_name(name: str, words: tuple[str, ...]) -> bool:
    low = name.lower()
    return any(w in low for w in words)


def _arg_for(name: str, plan: Any, provider: Any, retriever: Any, fmt: Any):
    low = name.lower()
    if "creative" in low or low in {"plan", "story_plan", "creative_plan"}:
        return plan, True
    if "retriever" in low:
        return retriever, True
    if "provider" in low or low in {"client", "provider_client"}:
        return provider, True
    if low in {"format", "format_id", "fmt"}:
        return fmt, True
    return None, False


def _kwargs(sig: inspect.Signature, plan: Any, provider: Any, retriever: Any, fmt: Any):
    out = {}
    for p in sig.parameters.values():
        if p.name in {"self", "cls"} or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        value, known = _arg_for(p.name, plan, provider, retriever, fmt)
        if known:
            out[p.name] = value
        elif p.default is p.empty:
            return None
    return out


def _modules(package) -> list[Any]:
    found = []
    prefix = package.__name__ + "."
    for info in pkgutil.iter_modules(package.__path__, prefix):
        leaf = info.name.rsplit(".", 1)[-1].lower()
        if leaf.startswith("_"):
            continue
        if not _semantic_name(leaf, ("stock", "proposal", "asset", "plan")):
            continue
        try:
            found.append(importlib.import_module(info.name))
        except Exception:
            continue
    try:
        online = importlib.import_module(prefix + "online_stock")
        if online not in found:
            found.insert(0, online)
    except Exception:
        pass
    return found


def _descriptors(modules: list[Any]):
    desc = []
    for mod in modules:
        for name, obj in vars(mod).items():
            if name.startswith("_") or getattr(obj, "__module__", None) != mod.__name__:
                continue
            if inspect.isfunction(obj) and _semantic_name(name, METHOD):
                desc.append(("function", mod.__name__, name, None))
            elif inspect.isclass(obj) and _semantic_name(name, SEMANTIC):
                for method_name, method in vars(obj).items():
                    if method_name.startswith("_") or not callable(method):
                        continue
                    if _semantic_name(method_name, METHOD):
                        desc.append(("method", mod.__name__, name, method_name))
    return desc


def _invoke(desc, plan, provider, retriever, fmt):
    kind, mod_name, obj_name, method_name = desc
    mod = importlib.import_module(mod_name)
    if kind == "function":
        func = getattr(mod, obj_name)
        kwargs = _kwargs(inspect.signature(func), plan, provider, retriever, fmt)
        if kwargs is None:
            raise TypeError("unsupported required function parameters")
        return func(**kwargs)
    cls = getattr(mod, obj_name)
    init_kwargs = _kwargs(inspect.signature(cls), plan, provider, retriever, fmt)
    if init_kwargs is None:
        raise TypeError("unsupported required constructor parameters")
    instance = cls(**init_kwargs)
    func = getattr(instance, method_name)
    kwargs = _kwargs(inspect.signature(func), plan, provider, retriever, fmt)
    if kwargs is None:
        raise TypeError("unsupported required method parameters")
    return func(**kwargs)


def _discover(plan, provider, retriever, fmt):
    package = importlib.import_module("videopipeline.stages.stage2_assets")
    attempts = []
    for desc in _descriptors(_modules(package)):
        try:
            result = _invoke(desc, plan, provider, retriever, fmt)
            proposals = _normalize(result)
            if proposals is not None:
                return desc, proposals, attempts
        except Exception as exc:
            attempts.append({"descriptor": desc, "error": f"{type(exc).__name__}: {exc}"})
    raise OracleFailure("no proposal-oriented public capability produced a proposal collection")


def _call(desc, plan, provider, retriever, fmt):
    result = _invoke(desc, plan, provider, retriever, fmt)
    proposals = _normalize(result)
    if proposals is None:
        raise OracleFailure(f"selected capability stopped returning a proposal collection: {desc}")
    return proposals


def _candidate_ids(proposal: dict[str, Any]) -> set[str]:
    vals = _pick(proposal, "candidates", "alternatives", "options", "suggestions") or []
    ids = set()
    if isinstance(vals, list):
        for item in vals:
            item = _plain(item)
            if isinstance(item, dict):
                value = _pick(item, "id", "online_id", "candidate_id", "asset_id")
                if value is not None:
                    ids.add(str(value))
    selected = _plain(_pick(proposal, "selected_candidate", "selected", "choice"))
    if isinstance(selected, dict):
        value = _pick(selected, "id", "online_id", "candidate_id", "asset_id")
        if value is not None:
            ids.add(str(value))
    return ids


def _assert_high(proposals, provider):
    if len(proposals) != 1:
        raise OracleFailure(f"expected exactly one STOCK_ONLINE proposal, got {len(proposals)}")
    p = proposals[0]
    shot = str(_pick(p, "shot_id", "source_shot_id", "shot") or "")
    scene = str(_pick(p, "scene_id", "source_scene_id", "scene") or "")
    if shot != "shot_stock":
        raise OracleFailure(f"proposal is not bound to stock shot: {shot!r}")
    if scene and scene != "scene_01":
        raise OracleFailure(f"proposal scene identity mismatch: {scene!r}")

    start = _pick(p, "start_sec", "start_time", "start")
    end = _pick(p, "end_sec", "end_time", "end")
    duration = _pick(p, "target_duration", "duration_sec", "duration")
    timing_ok = False
    try:
        timing_ok = (start is not None and end is not None and abs(float(end) - float(start) - 6.0) < 0.05)
    except Exception:
        pass
    try:
        timing_ok = timing_ok or (duration is not None and abs(float(duration) - 6.0) < 0.05)
    except Exception:
        pass
    if not timing_ok:
        raise OracleFailure("proposal lacks shot-bound timing/duration")

    alternatives = _pick(p, "candidates", "alternatives", "options", "suggestions")
    if not isinstance(alternatives, list) or not (1 <= len(alternatives) <= 3):
        raise OracleFailure("proposal alternatives are not reviewably bounded to 1..3")

    ids = _candidate_ids(p)
    if not ({"good", "pexels_good"} & ids):
        raise OracleFailure(f"eligible semantic candidate not present in proposal: {sorted(ids)}")

    status_text = " ".join(str(_pick(p, k) or "") for k in ("disposition", "status", "state", "next_action", "action")).upper()
    if any(word in status_text for word in ("FINAL_APPROVED", "COMMITTED", "PUBLISHED")):
        raise OracleFailure(f"proposal was silently finalized: {status_text}")

    query_text = " ".join(provider.queries).lower()
    if not provider.queries or sum(term in query_text for term in ("woman", "courthouse", "exterior")) < 2:
        raise OracleFailure(f"provider query is not grounded in shot-specific semantic intent: {provider.queries}")


def _assert_no_match(proposals):
    if len(proposals) != 1:
        raise OracleFailure("F5 no-match must preserve one reviewable stock proposal")
    p = proposals[0]
    if _candidate_ids(p):
        raise OracleFailure("F5 no-match unexpectedly selected/proposed a candidate")
    text = " ".join(str(_pick(p, k) or "") for k in ("disposition", "status", "state", "next_action", "action")).upper()
    if not any(token in text for token in ("NO_MATCH", "NEEDS_OWNER", "OWNER_REVIEW", "REVIEW")):
        raise OracleFailure(f"F5 no-match is not routed to review/owner handling: {text}")
    if any(token in text for token in ("ROUTE_AI_VIDEO_FLOW", "GENERATED_VIDEO", "GENERATED_IMAGE", "DISPATCH")):
        raise OracleFailure(f"F5 no-match silently falls back/dispatches: {text}")


def _assert_forbidden(proposals):
    if len(proposals) != 1:
        raise OracleFailure("forbidden-candidate scenario lost the stock proposal")
    ids = _candidate_ids(proposals[0])
    if {"bad", "pexels_bad"} & ids:
        raise OracleFailure("forbidden candidate survived hard filtering")


def _git_state(candidate: Path) -> str:
    cp = subprocess.run(
        ["git", "-C", str(candidate), "status", "--porcelain=v1", "-uall"],
        text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
    )
    return cp.stdout


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: xp002_oracle.py <candidate_dir>", file=sys.stderr)
        return 2
    candidate = Path(sys.argv[1]).resolve()
    if not candidate.exists():
        print("candidate directory missing", file=sys.stderr)
        return 2

    sys.path.insert(0, str(candidate))
    os.chdir(candidate)
    before = _git_state(candidate)

    # Prevent accidental external network. Local fake provider is the only source.
    real_create_connection = socket.create_connection
    def blocked(*args, **kwargs):
        raise RuntimeError("XP-002 oracle blocks external network")
    socket.create_connection = blocked

    evidence: dict[str, Any] = {}
    try:
        from videopipeline.models import (
            CreativePlan, FormatId, Scene, ShotSpec, SourceClass,
            VisualRequirement, create_default_format_plan,
        )
        online = importlib.import_module("videopipeline.stages.stage2_assets.online_stock")
        retriever_cls = getattr(online, "StoryStockRetriever", None)
        if retriever_cls is None:
            raise OracleFailure("existing StoryStockRetriever product surface is missing")

        def make_plan():
            scene = Scene(
                scene_id="scene_01", scene_index=1, start_sec=10.0, end_sec=22.0,
                location_id="loc_court", time_context="day",
            )
            stock_req = VisualRequirement(
                required_visuals=["woman", "courthouse"],
                forbidden_visuals=["beach"],
                preferred_source_class=SourceClass.STOCK_ONLINE,
                stock_search_intent="woman courthouse exterior",
            )
            generated_req = VisualRequirement(
                preferred_source_class=SourceClass.GENERATED_VIDEO,
                stock_search_intent="dramatic reveal",
            )
            shots = [
                ShotSpec("shot_stock", "scene_01", 6.0, primary_action="woman approaches courthouse", visual_requirement=stock_req),
                ShotSpec("shot_generated", "scene_01", 6.0, primary_action="dramatic reveal", visual_requirement=generated_req),
            ]
            plan = CreativePlan(
                creative_plan_id="cp_xp002", story_title="XP002",
                format_plan=create_default_format_plan(FormatId.F5),
                scenes=[scene], shot_specs=shots,
            )
            plan.fingerprint = plan.compute_fingerprint()
            return plan

        good = [{
            "id": "good", "online_id": "pexels_good",
            "title": "woman courthouse exterior entrance",
            "duration": 10.0, "width": 1920, "height": 1080,
            "rights_status": "ELIGIBLE", "preview_url": "local://preview/good",
        }]
        provider = StaticProvider(good)
        retriever = retriever_cls(provider_client=provider)
        desc, high, attempts = _discover(make_plan(), provider, retriever, FormatId.F5)
        _assert_high(high, provider)

        empty_provider = StaticProvider([])
        empty_retriever = retriever_cls(provider_client=empty_provider)
        no_match = _call(desc, make_plan(), empty_provider, empty_retriever, FormatId.F5)
        _assert_no_match(no_match)

        bad = [{
            "id": "bad", "online_id": "pexels_bad",
            "title": "woman courthouse exterior beach",
            "duration": 10.0, "width": 1920, "height": 1080,
            "rights_status": "ELIGIBLE", "preview_url": "local://preview/bad",
        }]
        bad_provider = StaticProvider(bad)
        bad_retriever = retriever_cls(provider_client=bad_provider)
        forbidden = _call(desc, make_plan(), bad_provider, bad_retriever, FormatId.F5)
        _assert_forbidden(forbidden)

        after = _git_state(candidate)
        if before != after:
            raise OracleFailure("proposal compilation mutated candidate worktree")

        evidence = {
            "status": "PASS",
            "descriptor": list(desc),
            "high_queries": provider.queries,
            "high_proposals": high,
            "no_match_proposals": no_match,
            "forbidden_proposals": forbidden,
            "discovery_failures_before_match": attempts,
        }
        print(json.dumps(evidence, ensure_ascii=False, default=str))
        return 0
    except Exception as exc:
        evidence = {"status": "FAIL", "reason": f"{type(exc).__name__}: {exc}"}
        print(json.dumps(evidence, ensure_ascii=False, default=str))
        return 1
    finally:
        socket.create_connection = real_create_connection


if __name__ == "__main__":
    raise SystemExit(main())
