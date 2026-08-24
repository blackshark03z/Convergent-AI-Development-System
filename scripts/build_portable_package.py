"""Create and verify a provenance-bound portable export without overwrites."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import unicodedata
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "PACKAGE_MANIFEST.json"
PACKAGE_STORE = Path(os.environ.get("BUILDOS_PACKAGE_STORE", r"D:\Youtube\_packages"))
FROZEN_KERNEL = ROOT / "FROZEN_KERNEL.sha256"
IDENTITY = ROOT / "scripts" / "package_identity.py"
GENERATED_MEMBERS = {"PACKAGE_VALIDATION.json", "PACKAGE_CONTENTS.sha256"}
POST_FREEZE_METADATA_ALLOWLIST = {
    "FROZEN_KERNEL.sha256", "PACKAGE_MANIFEST.json", "docs/V1.25_RC4_REPORT.md",
}
RELEASE_SUITE_TIMEOUT_SECONDS = 2_400
PRIVATE_KEY_BEGIN = b"-----" + b"BEGIN "
PRIVATE_KEY_END = b"PRIVATE " + b"KEY-----"
TOKEN_PATTERNS = (
    re.compile(rb"\b" + b"s" + rb"k-(?:(?:proj|svcacct)-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(rb"\b" + b"A" + rb"KIA[0-9A-Z]{16}\b"),
    re.compile(rb"\b" + b"gh" + rb"[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(rb"\b" + b"AI" + rb"za[0-9A-Za-z_-]{30,}\b"),
)
WINDOWS_DEVICES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def strict_json_loads(payload: str | bytes) -> object:
    def pairs(rows: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in rows:
            if key in result:
                raise ValueError(f"duplicate JSON object key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise ValueError(f"non-finite JSON constant is forbidden: {value}")

    return json.loads(payload, object_pairs_hook=pairs, parse_constant=reject_constant)


def contains_secret_like(payload: bytes) -> bool:
    return (
        PRIVATE_KEY_BEGIN in payload and PRIVATE_KEY_END in payload
    ) or any(pattern.search(payload) for pattern in TOKEN_PATTERNS)


def _run(command: list[str], *, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return _run_at(ROOT, command, timeout=timeout)


def _run_at(
    root: Path, command: list[str], *, timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=root, text=True, encoding="utf-8", errors="replace",
        capture_output=True, timeout=timeout,
    )


def _git_bytes(commit: str, relative: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
    )
    if completed.returncode:
        raise RuntimeError(f"cannot read frozen Git member: {relative}")
    return completed.stdout


def _git_lines(*args: str) -> list[str]:
    completed = _run(["git", *args])
    if completed.returncode:
        raise RuntimeError((completed.stderr or completed.stdout or "Git command failed").strip())
    return [line for line in completed.stdout.splitlines() if line]


def canonical_member_key(name: str) -> str:
    """Reject archive aliases that could overwrite another member on Windows."""
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise RuntimeError("ZIP contains a noncanonical member name")
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name) or name.endswith("/"):
        raise RuntimeError("ZIP contains a noncanonical member name")
    parts = name.split("/")
    if any(not part or part in {".", ".."} or part.endswith((" ", ".")) or ":" in part for part in parts):
        raise RuntimeError("ZIP contains a noncanonical member name")
    if PurePosixPath(name).as_posix() != name:
        raise RuntimeError("ZIP contains a noncanonical member name")
    for part in parts:
        stem = part.split(".", 1)[0].upper()
        if stem in WINDOWS_DEVICES:
            raise RuntimeError("ZIP contains a Windows-reserved member name")
    return unicodedata.normalize("NFC", name).casefold()


def validate_archive_names(names: list[str]) -> None:
    if len(names) != len(set(names)):
        raise RuntimeError("ZIP contains duplicate member names")
    normalized: dict[str, str] = {}
    for name in names:
        key = canonical_member_key(name)
        if key in normalized:
            raise RuntimeError(
                f"ZIP contains colliding member aliases: {normalized[key]} and {name}"
            )
        normalized[key] = name


def parse_frozen_kernel(payload: bytes) -> dict[str, str]:
    try:
        lines = payload.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise RuntimeError("frozen kernel index is not ASCII") from exc
    rows: dict[str, str] = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  (buildos/[A-Za-z0-9._/-]+)", line)
        if match is None:
            raise RuntimeError("frozen kernel index contains a malformed row")
        digest, name = match.groups()
        canonical_member_key(name)
        if name in rows:
            raise RuntimeError("frozen kernel index contains a duplicate path")
        rows[name] = digest
    if not rows:
        raise RuntimeError("frozen kernel index is empty")
    return rows


def frozen_kernel_matches(frozen_commit: str, source_root: Path = ROOT) -> bool:
    try:
        expected = parse_frozen_kernel((source_root / "FROZEN_KERNEL.sha256").read_bytes())
        committed_names = set(_git_lines("ls-tree", "-r", "--name-only", frozen_commit, "--", "buildos"))
        if set(expected) != committed_names:
            return False
        committed = {
            name: hashlib.sha256(_git_bytes(frozen_commit, name)).hexdigest()
            for name in expected
        }
        observed = {
            path.relative_to(source_root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (source_root / "buildos").rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
    except (OSError, RuntimeError, subprocess.SubprocessError):
        return False
    return observed == expected and committed == expected


def source_snapshot() -> tuple[str, str, list[str], dict]:
    status = _run(["git", "status", "--porcelain=v1", "--untracked-files=all"])
    if status.returncode or status.stdout.strip():
        raise RuntimeError("portable package requires a clean Git worktree")
    commit = _git_lines("rev-parse", "HEAD")[0]
    tree = _git_lines("rev-parse", f"{commit}^{{tree}}")[0]
    try:
        manifest = strict_json_loads(_git_bytes(commit, "PACKAGE_MANIFEST.json"))
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as exc:
        raise RuntimeError("frozen package manifest JSON is invalid") from exc
    if not isinstance(manifest, dict):
        raise RuntimeError("frozen package manifest must be an object")
    frozen_commit = manifest.get("frozen_kernel_commit")
    if not isinstance(frozen_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", frozen_commit):
        raise RuntimeError("package manifest frozen kernel commit is invalid")
    ancestry = _run(["git", "merge-base", "--is-ancestor", frozen_commit, commit])
    if ancestry.returncode:
        raise RuntimeError("package source commit does not descend from the frozen kernel commit")
    changed = set(_git_lines("diff", "--name-only", frozen_commit, commit, "--"))
    additions = set(_git_lines("diff", "--name-only", "--diff-filter=A", frozen_commit, commit, "--"))
    if additions or not changed.issubset(POST_FREEZE_METADATA_ALLOWLIST):
        unexpected = sorted(additions | (changed - POST_FREEZE_METADATA_ALLOWLIST))
        raise RuntimeError(
            "package source contains unreviewed post-freeze additions or executable/content changes: "
            + ", ".join(unexpected)
        )
    tracked = _git_lines("ls-tree", "-r", "--name-only", commit)
    included = manifest.get("included")
    if not isinstance(included, list) or not included or any(not isinstance(item, str) for item in included):
        raise RuntimeError("package manifest included allowlist is invalid")
    if len(included) != len(set(included)):
        raise RuntimeError("package manifest included allowlist contains duplicates")
    if not GENERATED_MEMBERS.issubset(set(included)):
        raise RuntimeError("package allowlist must include generated validation and checksum evidence")
    selected: set[str] = set()
    for entry in included:
        canonical_member_key(entry)
        if entry in GENERATED_MEMBERS:
            selected.add(entry)
            continue
        matches = [name for name in tracked if name == entry or name.startswith(entry + "/")]
        if not matches:
            raise RuntimeError(f"package allowlist entry has no frozen Git members: {entry}")
        selected.update(matches)
    return commit, tree, sorted(selected), manifest


def materialize_validation_checkout(source_commit: str, destination: Path) -> None:
    clone = subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout", str(ROOT), str(destination)],
        cwd=ROOT, text=True, encoding="utf-8", errors="replace",
        capture_output=True, timeout=300,
    )
    if clone.returncode:
        raise RuntimeError(f"cannot materialize immutable validation checkout: {clone.stderr}")
    checkout = _run_at(destination, ["git", "checkout", "--quiet", "--detach", source_commit])
    if checkout.returncode:
        raise RuntimeError(f"cannot checkout package source commit: {checkout.stderr}")
    observed_head = _run_at(destination, ["git", "rev-parse", "HEAD"])
    observed_status = _run_at(
        destination, ["git", "status", "--porcelain=v1", "--untracked-files=all"],
    )
    if (
        observed_head.returncode or observed_head.stdout.strip() != source_commit
        or observed_status.returncode or observed_status.stdout.strip()
    ):
        raise RuntimeError("immutable validation checkout identity is not clean and exact")


def _identity_pass(completed: subprocess.CompletedProcess[str]) -> bool:
    if completed.returncode:
        return False
    try:
        payload = strict_json_loads(completed.stdout)
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return False
    return (
        isinstance(payload, dict)
        and payload.get("status") == "PASS"
        and payload.get("invariant") == "PACKAGE_IDENTITY_CONSISTENT"
        and payload.get("errors") == []
    )


def validate(
    manifest: dict, *, source_commit: str, source_tree: str, source_root: Path,
) -> dict:
    command = [sys.executable, str(source_root / "scripts" / "release_suite.py")]
    try:
        completed = _run_at(
            source_root, command, timeout=RELEASE_SUITE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"portable release suite exceeded {RELEASE_SUITE_TIMEOUT_SECONDS} seconds; "
            "no package was published"
        ) from exc
    identity = _run_at(
        source_root,
        [sys.executable, str(source_root / "scripts" / "package_identity.py"), "--root", str(source_root)],
    )
    try:
        suite_result = strict_json_loads(completed.stdout)
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        suite_result = {}
    test_count = suite_result.get("tests_run") if isinstance(suite_result, dict) else None
    inventory = sorted(path.name for path in (source_root / "tests").glob("test_*.py") if path.is_file())
    assurance = manifest.get("release_assurance") or {}
    frozen_commit = str(manifest.get("frozen_kernel_commit") or "")
    expected_count = assurance.get("expected_test_count")
    expected_inventory = assurance.get("expected_test_modules")
    allowed_skips = set(assurance.get("allowed_skip_tests") or [])
    observed_skip_ids = suite_result.get("skipped_test_ids") if isinstance(suite_result, dict) else []
    observed_skips = [str(item) for item in observed_skip_ids or []]
    manifest_hash = hashlib.sha256((source_root / "PACKAGE_MANIFEST.json").read_bytes()).hexdigest()
    result = {
        "schema": "buildos.portable-validation-evidence.v2",
        "status": "PASS",
        "package_id": manifest.get("package_id"),
        "archive_name": manifest.get("archive_name"),
        "manifest_sha256": manifest_hash,
        "frozen_kernel_commit": frozen_commit,
        "package_source_commit": source_commit,
        "package_source_tree": source_tree,
        "frozen_kernel_ancestor_of_package_source": True,
        "command": command,
        "exit_code": completed.returncode,
        "test_count": test_count,
        "test_module_inventory": inventory,
        "skipped_tests": observed_skips,
        "suite_result": suite_result,
        "output_tail": completed.stderr[-4000:],
        "frozen_kernel_byte_identical": frozen_kernel_matches(frozen_commit, source_root),
        "manifest_valid": bool(re.fullmatch(r"[0-9a-f]{40}", frozen_commit)),
        "package_identity_consistent": _identity_pass(identity),
        "identity_output": identity.stdout[-1000:] + identity.stderr[-1000:],
        "final_zip_sha256": "BOUND_BY_EXTERNAL_FINAL_RECEIPT",
    }
    if (
        completed.returncode or suite_result.get("schema") != "buildos.release-suite-result.v1"
        or suite_result.get("successful") is not True
        or suite_result.get("discovered_test_count") != expected_count
        or test_count != expected_count or inventory != expected_inventory
        or suite_result.get("failure_count") != 0 or suite_result.get("error_count") != 0
        or suite_result.get("expected_failure_count") != 0
        or suite_result.get("unexpected_success_count") != 0
        or len(observed_skips) != len(set(observed_skips))
        or not set(observed_skips).issubset(allowed_skips)
        or not result["frozen_kernel_byte_identical"]
        or not result["manifest_valid"]
        or not result["package_identity_consistent"]
    ):
        result["status"] = "FAIL"
        raise RuntimeError("portable validation failed; no package was published")
    return result


def build_payloads(paths: list[str], source_commit: str, validation: dict) -> dict[str, bytes]:
    payloads = {
        name: _git_bytes(source_commit, name)
        for name in paths if name not in GENERATED_MEMBERS
    }
    payloads["PACKAGE_VALIDATION.json"] = (
        json.dumps(validation, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    rows = [
        f"{hashlib.sha256(payload).hexdigest()}  {name}"
        for name, payload in sorted(payloads.items())
    ]
    payloads["PACKAGE_CONTENTS.sha256"] = ("\n".join(rows) + "\n").encode("utf-8")
    if set(payloads) != set(paths):
        raise RuntimeError("frozen package payload set differs from the manifest allowlist")
    return payloads


def verify_checksum_index(archive: zipfile.ZipFile) -> None:
    """Require the checksum index to cover every other archive member exactly."""
    names = archive.namelist()
    validate_archive_names(names)
    checksum_rows: dict[str, str] = {}
    for line in archive.read("PACKAGE_CONTENTS.sha256").decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise RuntimeError("ZIP checksum index is malformed")
        digest, name = match.groups()
        canonical_member_key(name)
        if name in checksum_rows:
            raise RuntimeError("ZIP checksum index contains an invalid or duplicate row")
        checksum_rows[name] = digest
    expected_names = set(names) - {"PACKAGE_CONTENTS.sha256"}
    if set(checksum_rows) != expected_names:
        raise RuntimeError("ZIP checksum index does not exactly cover packaged content")
    for name, expected_hash in checksum_rows.items():
        if hashlib.sha256(archive.read(name)).hexdigest() != expected_hash:
            raise RuntimeError(f"ZIP content checksum mismatch: {name}")


def verify_zip(
    archive_path: Path, manifest: dict, *, expected_members: set[str], validation: dict,
) -> dict:
    with zipfile.ZipFile(archive_path, "r") as archive:
        names = archive.namelist()
        validate_archive_names(names)
        if set(names) != expected_members:
            raise RuntimeError("ZIP member set differs from frozen manifest allowlist")
        verify_checksum_index(archive)
        zipped_manifest = strict_json_loads(archive.read("PACKAGE_MANIFEST.json"))
        if zipped_manifest != manifest:
            raise RuntimeError("ZIP manifest does not match package manifest")
        if hashlib.sha256(archive.read("PACKAGE_MANIFEST.json")).hexdigest() != validation.get("manifest_sha256"):
            raise RuntimeError("ZIP manifest hash does not match validation evidence")
        zipped_validation = strict_json_loads(archive.read("PACKAGE_VALIDATION.json"))
        if zipped_validation != validation:
            raise RuntimeError("ZIP validation evidence does not match verified build evidence")
        kernel_hashes = parse_frozen_kernel(archive.read("FROZEN_KERNEL.sha256"))
        for name, expected_hash in kernel_hashes.items():
            if name not in names or hashlib.sha256(archive.read(name)).hexdigest() != expected_hash:
                raise RuntimeError(f"ZIP frozen kernel mismatch: {name}")
        for name in names:
            payload = archive.read(name)
            if contains_secret_like(payload):
                raise RuntimeError(f"ZIP contains secret-like material: {name}")
    with tempfile.TemporaryDirectory(prefix="buildos-package-identity-") as raw:
        extraction_root = Path(raw)
        with zipfile.ZipFile(archive_path, "r") as archive:
            for name in archive.namelist():
                target = extraction_root.joinpath(*name.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(name))
        identity = subprocess.run(
            [sys.executable, str(extraction_root / "scripts" / "package_identity.py"), "--root", raw],
            text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=60,
        )
        if not _identity_pass(identity):
            raise RuntimeError(
                f"ZIP package identity validation failed: {identity.stdout[-1000:]}{identity.stderr[-1000:]}"
            )
    return {
        "zip_opens": True,
        "manifest_valid": True,
        "package_identity_consistent": True,
        "frozen_kernel_byte_identical": True,
        "content_index_exhaustive": True,
        "canonical_member_names": True,
        "source_bytes_git_frozen": True,
        "bounded_secret_pattern_scan": True,
    }


def publish(manifest: dict, validation: dict, payloads: dict[str, bytes]) -> tuple[Path, Path, str, dict]:
    if not PACKAGE_STORE.is_dir():
        raise RuntimeError(f"durable package store does not exist: {PACKAGE_STORE}")
    archive_name = manifest.get("archive_name")
    if not isinstance(archive_name, str):
        raise RuntimeError("package archive_name is invalid")
    canonical_member_key(archive_name)
    if not archive_name.lower().endswith(".zip"):
        raise RuntimeError("package archive_name must end in .zip")
    output = PACKAGE_STORE / archive_name
    receipt = PACKAGE_STORE / f"{archive_name}.validation.json"
    if output.exists() or receipt.exists():
        raise RuntimeError(f"refusing to overwrite previous package or receipt: {output}")
    with tempfile.TemporaryDirectory(prefix=".buildos-package-stage-", dir=PACKAGE_STORE) as raw:
        stage = Path(raw) / archive_name
        with zipfile.ZipFile(stage, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, payload in sorted(payloads.items()):
                archive.writestr(name, payload)
        checks = verify_zip(
            stage, manifest, expected_members=set(payloads), validation=validation,
        )
        zip_hash = hashlib.sha256(stage.read_bytes()).hexdigest()
        receipt_payload = {
            "schema": "buildos.portable-final-receipt.v1",
            "status": "PASS",
            "package_id": manifest["package_id"],
            "archive_name": archive_name,
            "zip_sha256": zip_hash,
            "manifest_sha256": validation["manifest_sha256"],
            "frozen_kernel_commit": validation["frozen_kernel_commit"],
            "package_source_commit": validation["package_source_commit"],
            "package_source_tree": validation["package_source_tree"],
            "validation_schema": validation["schema"],
            **checks,
        }
        staged_receipt = Path(raw) / f"{archive_name}.validation.json"
        staged_receipt.write_text(
            json.dumps(receipt_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8",
        )
        os.link(staged_receipt, receipt)
        try:
            os.link(stage, output)
        except BaseException:
            receipt.unlink(missing_ok=True)
            raise
    if hashlib.sha256(output.read_bytes()).hexdigest() != zip_hash:
        output.unlink(missing_ok=True)
        receipt.unlink(missing_ok=True)
        raise RuntimeError("published package bytes changed after verified staging")
    return output, receipt, zip_hash, checks


def main() -> int:
    source_commit, source_tree, paths, manifest = source_snapshot()
    with tempfile.TemporaryDirectory(prefix="buildos-package-source-") as raw:
        source_root = Path(raw) / "source"
        materialize_validation_checkout(source_commit, source_root)
        validation = validate(
            manifest, source_commit=source_commit, source_tree=source_tree,
            source_root=source_root,
        )
        after_head = _run_at(source_root, ["git", "rev-parse", "HEAD"])
        after_status = _run_at(
            source_root, ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        )
        if (
            after_head.returncode or after_head.stdout.strip() != source_commit
            or after_status.returncode or after_status.stdout.strip()
        ):
            raise RuntimeError("release validation mutated its immutable package-source checkout")
        payloads = build_payloads(paths, source_commit, validation)
    output, receipt, zip_hash, checks = publish(manifest, validation, payloads)
    print(json.dumps({
        "status": "PASS",
        "zip": str(output),
        "receipt": str(receipt),
        "sha256": zip_hash,
        "package_id": manifest["package_id"],
        "frozen_kernel_commit": manifest["frozen_kernel_commit"],
        "package_source_commit": source_commit,
        "package_source_tree": source_tree,
        "validation_exit_code": validation["exit_code"],
        "content_checksums": "embedded:PACKAGE_CONTENTS.sha256",
        **checks,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
