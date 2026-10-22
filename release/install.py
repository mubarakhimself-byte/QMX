"""Install the checksum-bound QMX bundle into a non-editable private environment.

Run with CPython 3.14. Offline bundles install their hash-pinned runtime
wheel closure; legacy online resolution requires the explicit --allow-online
option. Developer/factory tools are not product prerequisites.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from stat import S_ISLNK
from typing import Any, cast

PRODUCT_DISTRIBUTIONS = frozenset(
    {
        "qmf_core",
        "qmf_data",
        "qmf_registry",
        "qmf_indicators",
        "qmf_structure",
        "qmf_risk",
        "qmf_venue",
        "qmf_calendar_forex",
        "qml",
        "qmb",
        "qmn",
    }
)
REQUIRED_ARTIFACTS = frozenset(
    {
        "requirements.lock",
        "launcher.py",
        "install.py",
        "ui.tar.gz",
        "qmn-deploy.tar.gz",
        "README.md",
        "source-manifest.json",
        "runtime_wheels.py",
    }
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_RUNTIME_FILES = {"runtime-wheels.tar.gz", "runtime-wheelhouse.json"}
_HELPER_PATH = Path(__file__).with_name("runtime_wheels.py")
_HELPER_SPEC = importlib.util.spec_from_file_location("qmx_runtime_wheels", _HELPER_PATH)
if _HELPER_SPEC is None or _HELPER_SPEC.loader is None:
    raise RuntimeError("The runtime wheel validation helper is unavailable")
_RUNTIME_HELPER = importlib.util.module_from_spec(_HELPER_SPEC)
_HELPER_SPEC.loader.exec_module(_RUNTIME_HELPER)


def _runtime_helper() -> Any:
    return _RUNTIME_HELPER


def _manifest(bundle: Path) -> tuple[dict[str, object], dict[str, str]]:
    """Read a structurally valid checksum inventory without creating a destination."""
    manifest_path = bundle / "acceptance.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise RuntimeError("The bundle acceptance manifest is missing or unsafe")
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError("The bundle acceptance manifest is malformed") from error
    if not isinstance(raw, dict):
        raise RuntimeError("The bundle acceptance manifest must be an object")
    record = cast("dict[str, object]", raw)
    candidate = record.get("candidate")
    if not isinstance(candidate, str) or _COMMIT.fullmatch(candidate) is None:
        raise RuntimeError("The bundle candidate must be a full commit SHA")
    raw_artifacts = record.get("artifacts")
    if not isinstance(raw_artifacts, dict) or not raw_artifacts:
        raise RuntimeError("The bundle has no artifact checksum inventory")
    artifacts: dict[str, str] = {}
    for name, digest in cast("dict[object, object]", raw_artifacts).items():
        if (
            not isinstance(name, str)
            or not name
            or Path(name).name != name
            or "/" in name
            or "\\" in name
        ):
            raise RuntimeError("Artifact paths must be local bundle filenames")
        if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            raise RuntimeError(f"Artifact checksum is malformed: {name}")
        path = bundle / name
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"Artifact is missing or unsafe: {name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Artifact checksum mismatch: {name}")
        artifacts[name] = digest
    _require_product_inventory(bundle, artifacts)
    _validate_wheels(bundle, artifacts)
    _validate_lock(bundle / "requirements.lock")
    _validate_ui_archive(bundle / "ui.tar.gz")
    _validate_qmn_archive(bundle / "qmn-deploy.tar.gz")
    _validate_runtime_closure(bundle, artifacts)
    return record, artifacts


def _validate_runtime_closure(bundle: Path, artifacts: Mapping[str, str]) -> None:
    present = set(artifacts) & _RUNTIME_FILES
    if present and present != _RUNTIME_FILES:
        raise RuntimeError("Offline runtime closure requires both archive and inventory")
    if not present:
        return
    helper = _runtime_helper()
    try:
        raw = json.loads((bundle / "runtime-wheelhouse.json").read_text(encoding="utf-8"))
        lock_text = (bundle / "requirements.lock").read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError("Runtime wheel inventory or requirements lock is malformed") from error
    if not isinstance(raw, dict):
        raise RuntimeError("Runtime wheel inventory must be an object")
    inventory = cast(Mapping[str, object], raw)
    if inventory.get("class") != helper.RUNTIME_CLASS:
        raise RuntimeError("Runtime wheel inventory class is unsupported")
    target = inventory.get("target")
    if not isinstance(target, Mapping):
        raise RuntimeError("Runtime wheel inventory target is malformed")
    try:
        glibc = helper.validate_runtime_target(
            target=cast(Mapping[str, object], target), running=True
        )
        wheels = helper.validate_inventory_requirements(
            inventory=inventory, lock_text=lock_text, glibc=glibc
        )
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"Runtime wheel closure preflight failed: {error}") from error

    total_size = 0
    try:
        with tarfile.open(bundle / "runtime-wheels.tar.gz", mode="r:gz") as archive:
            members = archive.getmembers()
            names: list[str] = []
            for member in members:
                name = member.name
                if (
                    not member.isfile()
                    or not name
                    or Path(name).name != name
                    or "/" in name
                    or "\\" in name
                    or name in names
                    or not name.endswith(".whl")
                ):
                    raise RuntimeError(f"Runtime wheel archive has an unsafe member: {name!r}")
                if member.size < 0 or member.size > 512 * 1024 * 1024:
                    raise RuntimeError(f"Runtime wheel archive member has an unsafe size: {name}")
                total_size += member.size
                names.append(name)
            expected_names = sorted(str(entry["filename"]) for entry in wheels.values())
            if sorted(names) != expected_names or total_size > 2 * 1024 * 1024 * 1024:
                raise RuntimeError("Runtime wheel archive does not match its exact inventory")
            with tempfile.TemporaryDirectory(prefix="qmx-runtime-preflight-") as temporary:
                extracted = Path(temporary)
                for member in members:
                    destination = extracted / member.name
                    source = archive.extractfile(member)
                    if source is None:
                        raise RuntimeError("Runtime wheel archive member cannot be read")
                    data = source.read(512 * 1024 * 1024 + 1)
                    if len(data) != member.size:
                        raise RuntimeError(f"Runtime wheel archive size mismatch: {member.name}")
                    destination.write_bytes(data)
                    actual = helper.wheel_metadata(destination)
                    entry = wheels[actual["distribution"]]
                    if (
                        member.name != entry["filename"]
                        or hashlib.sha256(data).hexdigest() != entry["sha256"]
                        or actual["distribution"] != entry["distribution"]
                        or actual["version"] != entry["version"]
                        or actual["tags"] != entry["tags"]
                    ):
                        raise RuntimeError(
                            f"Runtime wheel differs from locked inventory: {member.name}"
                        )
    except (OSError, tarfile.TarError, KeyError, ValueError) as error:
        raise RuntimeError("Runtime wheel archive is malformed") from error


def _require_product_inventory(bundle: Path, artifacts: Mapping[str, str]) -> None:
    names = set(artifacts)
    missing = sorted(REQUIRED_ARTIFACTS - names)
    if missing:
        raise RuntimeError(f"Required product artifact is missing: {missing[0]}")
    wheels = sorted(name for name in names if name.endswith(".whl"))
    represented = {name.split("-", 1)[0].replace("-", "_").lower() for name in wheels}
    missing_distributions = sorted(PRODUCT_DISTRIBUTIONS - represented)
    if missing_distributions:
        raise RuntimeError(f"Required product wheel is missing: {missing_distributions[0]}")
    on_disk_wheels = {path.name for path in bundle.glob("*.whl")}
    unlisted_wheels = sorted(on_disk_wheels - set(wheels))
    if unlisted_wheels:
        raise RuntimeError(f"Unlisted product wheel is present: {unlisted_wheels[0]}")
    if not wheels:
        raise RuntimeError("Product wheels are missing")


def _validate_lock(path: Path) -> None:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise RuntimeError("The product requirements lock is unreadable") from error
    if not content.strip():
        raise RuntimeError("The product requirements lock is empty")
    requirements = 0
    current: str | None = None
    hashes: list[str] = []

    def finish() -> None:
        nonlocal requirements, current, hashes
        if current is None:
            return
        if not hashes:
            raise RuntimeError("Every locked requirement must carry at least one SHA256")
        requirements += 1
        current = None
        hashes = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("    #"):
            continue
        line = line.split("  #", 1)[0].rstrip()
        if not line:
            continue
        if line.endswith("\\"):
            line = line[:-1].rstrip()
        if line.startswith("--hash="):
            if current is None or re.fullmatch(r"--hash=sha256:[0-9a-f]{64}", line) is None:
                raise RuntimeError("The product requirements lock has a malformed hash line")
            hashes.append(line)
            continue
        if line.startswith(("--index-url ", "--extra-index-url ", "--trusted-host ")):
            finish()
            continue
        requirement_line = re.match(r"^[A-Za-z0-9_.-]+==[A-Za-z0-9_.+!-]+(?:\s*;.*)?$", line)
        if line.startswith("-") or requirement_line is None:
            raise RuntimeError("The product requirements lock contains an unsupported line")
        finish()
        current = line
    finish()
    if requirements == 0:
        raise RuntimeError("The product requirements lock contains no pinned requirements")


def _validate_wheels(bundle: Path, artifacts: Mapping[str, str]) -> None:
    for name in sorted(item for item in artifacts if item.endswith(".whl")):
        path = bundle / name
        parts = name[:-4].split("-")
        if len(parts) < 5:
            raise RuntimeError(f"Product wheel filename is malformed: {name}")
        expected_name = _normalize_distribution(parts[0])
        expected_version = parts[1]
        try:
            with zipfile.ZipFile(path) as wheel:
                bad_member = wheel.testzip()
                if bad_member is not None:
                    raise RuntimeError(f"Product wheel has a corrupt member: {name}")
                members = wheel.infolist()
                member_names = {member.filename for member in members}
                for member in members:
                    info = member.external_attr >> 16
                    if (
                        member.filename.startswith("/")
                        or "\\" in member.filename
                        or PurePosixPath(member.filename).as_posix() != member.filename.rstrip("/")
                        or any(
                            part in {"", ".", ".."}
                            for part in member.filename.rstrip("/").split("/")
                        )
                        or S_ISLNK(info)
                    ):
                        raise RuntimeError(f"Product wheel contains an unsafe path: {name}")
                dist_info = {
                    member.filename.split("/", 1)[0]
                    for member in members
                    if ".dist-info/" in member.filename
                }
                if len(dist_info) != 1:
                    raise RuntimeError(f"Product wheel metadata is missing or ambiguous: {name}")
                root = next(iter(dist_info))
                metadata_path = f"{root}/METADATA"
                if not {metadata_path, f"{root}/WHEEL", f"{root}/RECORD"}.issubset(member_names):
                    raise RuntimeError(f"Product wheel metadata is incomplete: {name}")
                metadata = wheel.read(metadata_path).decode("utf-8")
        except (OSError, UnicodeError, zipfile.BadZipFile, RuntimeError) as error:
            if isinstance(error, RuntimeError) and str(error).startswith("Product wheel"):
                raise
            raise RuntimeError(f"Product wheel is malformed: {name}") from error
        fields = _email_fields(metadata)
        if (
            _normalize_distribution(fields.get("Name", "")) != expected_name
            or fields.get("Version") != expected_version
        ):
            raise RuntimeError(f"Product wheel filename and METADATA disagree: {name}")


def _email_fields(content: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in content.splitlines():
        if not line:
            break
        key, separator, value = line.partition(":")
        if separator:
            fields[key] = value.strip()
    return fields


def _normalize_distribution(value: str) -> str:
    return re.sub(r"[-_.]+", "_", value).lower()


def _validate_ui_archive(path: Path) -> None:
    _validate_archive(path, label="UI", required_files={"index.html"})


def _validate_qmn_archive(path: Path) -> None:
    _validate_archive(
        path,
        label="QMN deployment",
        required_files={
            "install.py",
            "safe_io.py",
            "systemd/templates/qmn.service.in",
            "justfile-recipes/node.just",
        },
    )


def _validate_archive(path: Path, *, label: str, required_files: set[str]) -> None:
    try:
        with tarfile.open(path, mode="r:gz") as assets:
            members = assets.getmembers()
    except (OSError, tarfile.TarError) as error:
        raise RuntimeError(f"The {label} archive is malformed") from error
    seen: dict[str, bool] = {}
    present: set[str] = set()
    for member in members:
        name = member.name
        parts = Path(name).parts
        if (
            not name
            or "\\" in name
            or name.startswith("/")
            or PurePosixPath(name).as_posix() != name.rstrip("/")
            or any(part in {"..", "."} for part in parts)
            or (parts and ":" in parts[0])
        ):
            raise RuntimeError(f"{label} archive contains an unsafe path: {name!r}")
        if name in seen:
            raise RuntimeError(f"{label} archive contains a duplicate path: {name!r}")
        if not (member.isdir() or member.isfile()):
            raise RuntimeError(f"{label} archive contains a link or special file: {name!r}")
        if member.isfile() and any(item.startswith(name.rstrip("/") + "/") for item in seen):
            raise RuntimeError(f"{label} archive file is also used as a directory: {name!r}")
        seen[name] = member.isdir()
        parent = Path(name).parent
        while parent != Path("."):
            parent_name = parent.as_posix()
            if seen.get(parent_name) is False:
                raise RuntimeError(
                    f"{label} archive file is also used as a directory: {parent_name!r}"
                )
            parent = parent.parent
        if member.isfile():
            present.add(name)
    missing = sorted(required_files - present)
    if missing:
        raise RuntimeError(f"The {label} archive has no required file {missing[0]}")


def install(bundle: Path, destination: Path, *, allow_online: bool = False) -> None:
    """Preflight the complete bundle before creating a clean environment."""
    if sys.version_info[:2] != (3, 14):
        raise RuntimeError("QMX requires CPython 3.14; use that interpreter to install")
    if destination.exists():
        raise RuntimeError(
            "Use a new destination to preserve an existing installation and its data"
        )
    record, artifacts = _manifest(bundle)
    offline = bool(set(artifacts) & _RUNTIME_FILES)
    if not offline and not allow_online:
        raise RuntimeError(
            "This bundle has no offline runtime closure; pass --allow-online explicitly"
        )
    if offline and allow_online:
        raise RuntimeError("--allow-online cannot override a bundle's pinned offline closure")
    # Installation may launch pip or other environment setup. Bind every input
    # to a private verified snapshot before those effects, not late bundle reads.
    with tempfile.TemporaryDirectory(prefix="qmx-verified-") as temporary:
        verified = Path(temporary)
        for name, expected in artifacts.items():
            data = (bundle / name).read_bytes()
            if hashlib.sha256(data).hexdigest() != expected:
                raise RuntimeError(f"Product artifact changed after preflight: {name}")
            (verified / name).write_bytes(data)
        (verified / "acceptance.json").write_text(json.dumps(record, indent=2) + "\n")
        verified_record, verified_artifacts = _manifest(verified)
        _install_verified(verified, destination, verified_record, verified_artifacts)


def _install_verified(
    bundle: Path, destination: Path, record: dict[str, object], artifacts: dict[str, str]
) -> None:
    wheels = sorted(str(bundle / name) for name in artifacts if name.endswith(".whl"))
    ui_bytes = (bundle / "ui.tar.gz").read_bytes()

    offline = _RUNTIME_FILES.issubset(artifacts)
    runtime_wheel_dir: Path | None = None
    if offline:
        runtime_wheel_dir = bundle / "runtime-wheelhouse"
        runtime_wheel_dir.mkdir()
        with tarfile.open(bundle / "runtime-wheels.tar.gz", mode="r:gz") as runtime_archive:
            for member in runtime_archive.getmembers():
                source = runtime_archive.extractfile(member)
                if source is None:
                    raise RuntimeError("Verified runtime wheel cannot be read")
                (runtime_wheel_dir / member.name).write_bytes(source.read())

    venv.EnvBuilder(with_pip=True).create(destination / "venv")
    scripts = destination / "venv" / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    pip_prefix = [str(python), "-m", "pip"]
    if offline:
        pip_prefix.append("--isolated")
    runtime_command = [*pip_prefix, "install", "--require-hashes"]
    if runtime_wheel_dir is not None:
        runtime_command.extend(["--no-index", "--find-links", str(runtime_wheel_dir)])
    runtime_command.extend(["-r", str(bundle / "requirements.lock")])
    subprocess.run(runtime_command, check=True)
    subprocess.run([*pip_prefix, "install", "--no-deps", *wheels], check=True)
    subprocess.run([*pip_prefix, "check"], check=True)
    with tarfile.open(fileobj=io.BytesIO(ui_bytes), mode="r:gz") as assets:
        assets.extractall(destination / "ui", filter="data")
    with tarfile.open(bundle / "qmn-deploy.tar.gz", mode="r:gz") as assets:
        assets.extractall(destination / "qmn/deploy", filter="data")
    if os.name != "nt":
        # Ubuntu node templates retain their declared .venv entrypoint. This
        # local alias does not install services, change system paths or trade.
        (destination / ".venv").symlink_to("venv", target_is_directory=True)
    shutil.copyfile(bundle / "README.md", destination / "README.md")
    shutil.copyfile(bundle / "source-manifest.json", destination / "source-manifest.json")
    shutil.copyfile(bundle / "launcher.py", destination / "launcher.py")
    shutil.copyfile(bundle / "acceptance.json", destination / "installed-artifacts.json")
    print(f"Installed candidate {record.get('candidate')} in {destination}")
    print("Release acceptance is separate; inspect installed-artifacts.json for pending checks.")
    print(f"Start the configured local host: {python} {destination / 'launcher.py'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument(
        "--allow-online",
        action="store_true",
        help="allow hash-pinned package-index downloads when the bundle has no offline closure",
    )
    args = parser.parse_args()
    install(
        Path(__file__).resolve().parent,
        args.destination.resolve(),
        allow_online=args.allow_online,
    )
