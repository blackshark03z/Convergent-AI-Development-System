from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path


BASE = "b6a9efb1de053edccbf9541deaaf21a830d71727"
EXCLUDE_FILES = {
    ".buildos-authority.json",
    ".buildos-policy.json",
    "AGENTS.md",
    "TASK.md",
    "NEXT_TASK.md",
}
EXCLUDE_DIRS = {
    ".buildos-legacy",
    "skills",
    "templates",
}
ARMS = {
    "N0": "N0.txt",
    "N1": "N1.txt",
    "CMIN": "CMIN.txt",
    "CCURRENT": "CCURRENT.txt",
}


def run(args: list[str], cwd: Path | None = None) -> str:
    cp = subprocess.run(args, cwd=cwd, text=True, encoding="utf-8",
                        capture_output=True, check=True)
    return cp.stdout.strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def zip_tree(source: Path, dest: Path, prompt: Path, arm: str) -> None:
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "README_FIRST.md",
            f"""# XP-001 Reasoning Lead bundle — {arm}

Open this bundle in a brand-new reasoning chat.

Instructions:
1. Read R_PROMPT.txt first.
2. Inspect NEUTRAL_REPO/ as needed.
3. Do not search for historical/reference versions of this repository.
4. Do not ask for other arm prompts or benchmark results.
5. Return the requested IMPLEMENTATION_BRIEF only.

This bundle intentionally does not contain the held-out oracle or reference patch.
""",
        )
        zf.write(prompt, "R_PROMPT.txt")
        for path in source.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(source)
            if ".git" in rel.parts:
                continue
            zf.write(path, Path("NEUTRAL_REPO") / rel)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=r"D:\Youtube\Story Trans And Audio")
    ap.add_argument("--out", default=r"D:\CADS-Benchmark\XP-001-RI")
    ap.add_argument("--force", action="store_true")
    ns = ap.parse_args()

    source = Path(ns.source).resolve()
    out = Path(ns.out).resolve()
    repo = Path(__file__).resolve().parents[1]
    prompt_dir = repo / "evals" / "existential" / "cases" / "XP-001" / "prompts"

    if out.exists():
        if not ns.force:
            raise SystemExit(f"output exists: {out}; rerun with --force")
        shutil.rmtree(out)

    out.mkdir(parents=True)
    neutral = out / "neutral"
    workspaces = out / "I_WORKSPACES"
    bundles = out / "R_BUNDLES"
    results = out / "RESULTS"
    workspaces.mkdir()
    bundles.mkdir()
    results.mkdir()

    run(["git", "-C", str(source), "cat-file", "-e", f"{BASE}^{{commit}}"])

    archive = out / "base.zip"
    run(["git", "-C", str(source), "archive", "--format=zip", "-o", str(archive), BASE])
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(neutral)

    for name in EXCLUDE_FILES:
        (neutral / name).unlink(missing_ok=True)
    for name in EXCLUDE_DIRS:
        shutil.rmtree(neutral / name, ignore_errors=True)

    # Fresh one-commit neutral repository: old Git history cannot leak treatment/reference data.
    run(["git", "init"], cwd=neutral)
    run(["git", "add", "-A"], cwd=neutral)
    run([
        "git", "-c", "user.name=CADS Benchmark",
        "-c", "user.email=benchmark@local.invalid",
        "commit", "-m", "XP001 neutral baseline"
    ], cwd=neutral)

    neutral_head = run(["git", "rev-parse", "HEAD"], cwd=neutral)
    neutral_tree = run(["git", "rev-parse", "HEAD^{tree}"], cwd=neutral)

    workspace_heads = {}
    for arm in ARMS:
        target = workspaces / arm
        run(["git", "clone", "--quiet", str(neutral), str(target)])
        workspace_heads[arm] = run(["git", "rev-parse", "HEAD"], cwd=target)
        tree = run(["git", "rev-parse", "HEAD^{tree}"], cwd=target)
        if tree != neutral_tree:
            raise RuntimeError(f"tree mismatch for {arm}: {tree} != {neutral_tree}")

    bundle_meta = {}
    for arm, prompt_name in ARMS.items():
        prompt = prompt_dir / prompt_name
        dest = bundles / f"XP001_R_{arm}.zip"
        zip_tree(neutral, dest, prompt, arm)
        bundle_meta[arm] = {
            "path": str(dest),
            "sha256": sha256(dest),
            "bytes": dest.stat().st_size,
            "prompt_sha256": sha256(prompt),
        }

    all_bundle = out / "XP001_ALL_R_BUNDLES.zip"
    with zipfile.ZipFile(all_bundle, "w", compression=zipfile.ZIP_STORED) as zf:
        for arm in ARMS:
            p = bundles / f"XP001_R_{arm}.zip"
            zf.write(p, p.name)

    manifest = {
        "schema": "cads-xp001-ri-setup-v1",
        "base_revision": BASE,
        "source_repo": str(source),
        "neutral_head": neutral_head,
        "neutral_tree": neutral_tree,
        "workspaces": {arm: str(workspaces / arm) for arm in ARMS},
        "workspace_heads": workspace_heads,
        "r_bundles": bundle_meta,
        "all_r_bundles": {
            "path": str(all_bundle),
            "sha256": sha256(all_bundle),
            "bytes": all_bundle.stat().st_size,
        },
        "hidden_oracle_in_bundles": False,
        "reference_patch_in_bundles": False,
    }
    (out / "SETUP_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
