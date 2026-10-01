"""Install the checksum-bound QMX bundle into a non-editable private environment.

Run with CPython 3.14. Runtime downloads use the hash-pinned requirements;
developer/factory tools are not installed as product prerequisites.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import venv
import zipfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from stat import S_ISLNK
from typing import cast

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
        "qma_core",
        "qma_wire",
        "qma_daemon",
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
        "pack-resources.json",
    }
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")


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
    _validate_pack_inventory(bundle / "pack-resources.json")
    _validate_lock(bundle / "requirements.lock")
    _validate_ui_archive(bundle / "ui.tar.gz")
    _validate_qmn_archive(bundle / "qmn-deploy.tar.gz")
    return record, artifacts


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


def _validate_pack_inventory(path: Path) -> None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError("The mandatory pack inventory is malformed") from error
    if not isinstance(raw, dict) or not raw:
        raise RuntimeError("The mandatory pack inventory is empty or malformed")
    for name, digest in cast("dict[object, object]", raw).items():
        if (
            not isinstance(name, str)
            or not name
            or Path(name).is_absolute()
            or "\\" in name
            or PurePosixPath(name).as_posix() != name
            or ":" in name.split("/", 1)[0]
            or any(part in {"", ".", ".."} for part in name.split("/"))
        ):
            raise RuntimeError("Pack inventory paths must be safe relative paths")
        if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            raise RuntimeError(f"Pack inventory checksum is malformed: {name}")


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


def install(bundle: Path, destination: Path) -> None:
    """Preflight the complete bundle before creating a clean environment."""
    if sys.version_info[:2] != (3, 14):
        raise RuntimeError("QMX requires CPython 3.14; use that interpreter to install")
    if destination.exists():
        raise RuntimeError(
            "Use a new destination to preserve an existing installation and its data"
        )
    record, artifacts = _manifest(bundle)
    wheels = sorted(str(bundle / name) for name in artifacts if name.endswith(".whl"))
    ui_bytes = (bundle / "ui.tar.gz").read_bytes()

    venv.EnvBuilder(with_pip=True).create(destination / "venv")
    scripts = destination / "venv" / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--require-hashes",
            "-r",
            str(bundle / "requirements.lock"),
        ],
        check=True,
    )
    subprocess.run([str(python), "-m", "pip", "install", "--no-deps", *wheels], check=True)
    subprocess.run([str(python), "-m", "pip", "check"], check=True)
    with tarfile.open(fileobj=io.BytesIO(ui_bytes), mode="r:gz") as assets:
        assets.extractall(destination / "ui", filter="data")
    with tarfile.open(bundle / "qmn-deploy.tar.gz", mode="r:gz") as assets:
        assets.extractall(destination / "qmn/deploy", filter="data")
    if os.name != "nt":
        # Ubuntu node templates retain their declared .venv entrypoint. This
        # local alias does not install services, change system paths or trade.
        (destination / ".venv").symlink_to("venv", target_is_directory=True)
    shutil.copyfile(bundle / "README.md", destination / "README.md")
    shutil.copyfile(bundle / "launcher.py", destination / "launcher.py")
    shutil.copyfile(bundle / "acceptance.json", destination / "installed-artifacts.json")
    print(f"Installed candidate {record.get('candidate')} in {destination}")
    print("Release acceptance is separate; inspect installed-artifacts.json for pending checks.")
    print(f"Start the configured local host: {python} {destination / 'launcher.py'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    install(Path(__file__).resolve().parent, args.destination.resolve())
