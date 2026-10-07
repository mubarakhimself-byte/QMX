"""Build a portable, checksum-bound product bundle from the isolated candidate.

This builds artifacts. Acceptance remains a separate fail-closed gate.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from release.runtime_wheels import (  # noqa: E402
    RUNTIME_CLASS,
    RUNTIME_FILENAME,
    RUNTIME_INVENTORY_FILENAME,
    marker_environment,
    parse_locked_requirements,
    sha256,
    tag_glibc_floor,
    wheel_metadata,
)


def run(args: list[str], *, cwd: Path = ROOT) -> str:
    """Use actual tool return codes; never suppress a failed build."""
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout


def archive(source: Path, destination: Path) -> None:
    """Sorted entries and stable timestamps make static assets reproducible."""
    with (
        destination.open("wb") as output,
        gzip.GzipFile(
            fileobj=output,
            mode="wb",
            filename="",
            mtime=0,
        ) as compressed,
        tarfile.open(fileobj=compressed, mode="w") as packed,
    ):
        for path in sorted(source.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            info = packed.gettarinfo(str(path), arcname=path.relative_to(source).as_posix())
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            with path.open("rb") as content:
                packed.addfile(info, content)


def build_ui(destination: Path, candidate: str, source: Path) -> None:
    """Build the UI from this candidate in a disposable registered worktree."""
    npm = shutil.which("npm")
    if npm is None:
        raise RuntimeError("npm is required to bootstrap the pinned UI build tools")
    ui = source / "apps/qmx-ui"
    command = [
        npm,
        "exec",
        "--yes",
        "--package=node@22.12.0",
        "--package=pnpm@10.18.3",
        "--",
        "pnpm",
    ]
    run([*command, "install", "--frozen-lockfile"], cwd=ui)
    run([*command, "build"], cwd=ui)
    assets = ui / "build"
    if not (assets / "index.html").is_file():
        raise RuntimeError("Candidate UI build has no index.html")
    archive(assets, destination / "ui.tar.gz")
    (destination / "ui-build.json").write_text(
        json.dumps({"candidate": candidate, "node": "22.12.0", "pnpm": "10.18.3"}) + "\n"
    )


def _runtime_closure(destination: Path, wheelhouse: Path, root_lock: str, nested_lock: str) -> None:
    """Package the exact locked Linux CPython 3.14 wheel closure."""
    if not wheelhouse.is_dir() or wheelhouse.is_symlink():
        raise RuntimeError("Runtime wheelhouse must be an existing real directory")
    requirements = parse_locked_requirements(
        (root_lock, nested_lock), environment=marker_environment(target=True)
    )
    by_distribution: dict[str, list[Path]] = {}
    for path in sorted(wheelhouse.iterdir()):
        if path.is_symlink():
            raise RuntimeError(f"Runtime wheelhouse contains a symbolic link: {path.name}")
        if path.is_file() and path.suffix == ".whl":
            try:
                metadata = wheel_metadata(path)
            except ValueError as error:
                raise RuntimeError(f"Runtime wheel is invalid: {path.name}") from error
            by_distribution.setdefault(str(metadata["distribution"]), []).append(path)

    selected: list[tuple[Path, dict[str, object]]] = []
    glibc_requirements: list[tuple[int, int]] = []
    for name, requirement in sorted(requirements.items()):
        candidates = by_distribution.get(name, [])
        matches: list[tuple[Path, dict[str, object]]] = []
        for candidate in candidates:
            metadata = wheel_metadata(candidate)
            if metadata["version"] != requirement["version"]:
                continue
            if f"sha256:{sha256(candidate)}" not in cast(list[str], requirement["hashes"]):
                continue
            tags = cast(list[str], metadata["tags"])
            floors = [floor for tag in tags if (floor := tag_glibc_floor(tag)) is not None]
            if not floors:
                continue
            glibc_requirements.append(min(floors))
            entry = {
                "filename": candidate.name,
                "distribution": name,
                "version": metadata["version"],
                "sha256": sha256(candidate),
                "tags": tags,
            }
            matches.append((candidate, entry))
        if len(matches) != 1:
            raise RuntimeError(
                "Expected one hash-locked Linux CPython 3.14 wheel for "
                f"{name}; found {len(matches)}"
            )
        selected.extend(matches)
    if len(selected) != len(requirements):
        raise RuntimeError("Runtime wheelhouse is not the exact active lock closure")
    glibc_floor = max(glibc_requirements, default=(2, 17))
    runtime_target = {
        "implementation": "CPython",
        "platform": "linux",
        "machine": "x86_64",
        "python_version": "3.14",
        "glibc_min": f"{glibc_floor[0]}.{glibc_floor[1]}",
    }
    with (
        (destination / RUNTIME_FILENAME).open("wb") as output,
        gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=0) as compressed,
        tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as packed,
    ):
        for source_path, _ in sorted(selected, key=lambda row: row[0].name):
            info = packed.gettarinfo(str(source_path), arcname=source_path.name)
            info.mtime = 0
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.pax_headers = {}
            with source_path.open("rb") as content:
                packed.addfile(info, content)
    inventory: dict[str, object] = {
        "class": RUNTIME_CLASS,
        "target": runtime_target,
        "requirements": [{"name": name, **requirements[name]} for name in sorted(requirements)],
        "wheels": [
            entry
            for _, entry in sorted(selected, key=lambda row: cast(str, row[1]["distribution"]))
        ],
    }
    (destination / RUNTIME_INVENTORY_FILENAME).write_text(
        json.dumps(inventory, sort_keys=True, indent=2) + "\n"
    )


def build(destination: Path, *, runtime_wheelhouse: Path | None = None) -> None:
    """Build both workspaces, locked runtime dependencies and mandatory packs."""
    uv = shutil.which("uv")
    git = shutil.which("git")
    if uv is None or git is None:
        raise RuntimeError("uv and git are required for artifact construction")
    if destination.exists() and any(destination.iterdir()):
        raise RuntimeError("Use an empty artifact destination to prevent stale wheel reuse")
    destination.mkdir(parents=True, exist_ok=True)
    dirty = run(
        [
            git,
            "status",
            "--porcelain",
            "--",
            "packages",
            "extensions",
            "qml",
            "qmb",
            "qmn",
            "qmx-agents",
            "apps",
            "tools",
            "pyproject.toml",
            "uv.lock",
            "release/launcher.py",
            "release/install.py",
            "release/runtime_wheels.py",
            "release/README.md",
        ]
    )
    if dirty.strip():
        raise RuntimeError(
            "Commit reviewed product changes before binding artifacts to a candidate"
        )
    candidate = run([git, "rev-parse", "HEAD"]).strip()
    epoch = run([git, "show", "-s", "--format=%ct", "HEAD"]).strip()
    os.environ["SOURCE_DATE_EPOCH"] = epoch
    with tempfile.TemporaryDirectory(prefix="qmx-release-source-") as temporary:
        source = Path(temporary) / "source"
        run([git, "worktree", "add", "--detach", str(source), candidate])
        try:
            run([uv, "build", "--all-packages", "--out-dir", str(destination)], cwd=source)
            run(
                [
                    uv,
                    "build",
                    "--project",
                    "qmx-agents",
                    "--all-packages",
                    "--out-dir",
                    str(destination),
                ],
                cwd=source,
            )
            export = ["export", "--locked", "--no-default-groups", "--no-emit-local", "--no-header"]
            root_lock = run(
                [
                    uv,
                    *export,
                    "--package",
                    "qmb",
                    "--package",
                    "qmn",
                    "--package",
                    "qmf-calendar-forex",
                ],
                cwd=source,
            )
            nested_lock = run(
                [uv, *export, "--project", "qmx-agents", "--all-packages"], cwd=source
            )
            (destination / "requirements.lock").write_text(root_lock + "\n" + nested_lock)
            shutil.copyfile(source / "release/launcher.py", destination / "launcher.py")
            shutil.copyfile(source / "release/install.py", destination / "install.py")
            shutil.copyfile(source / "release/runtime_wheels.py", destination / "runtime_wheels.py")
            shutil.copyfile(source / "release/README.md", destination / "README.md")
            if runtime_wheelhouse is not None:
                _runtime_closure(destination, runtime_wheelhouse, root_lock, nested_lock)
            shutil.copyfile(
                source / "release/SOURCE_MANIFEST.json", destination / "source-manifest.json"
            )
            archive(source / "qmn/deploy", destination / "qmn-deploy.tar.gz")
            build_ui(destination, candidate, source)
            packs = source / "qmx-agents/packages/qma-daemon/src/qma/daemon/bundled_packs"
            if not packs.is_dir():
                raise RuntimeError("Installed mandatory pack resources have not been repaired")
            pack_inventory = {
                path.relative_to(packs).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(packs.rglob("*"))
                if path.is_file() and "__pycache__" not in path.parts
            }
            (destination / "pack-resources.json").write_text(
                json.dumps(pack_inventory, indent=2) + "\n"
            )
        finally:
            run([git, "worktree", "remove", "--force", str(source)])
    artifacts = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(destination.iterdir())
        if path.is_file()
    }
    manifest = {
        "candidate": candidate,
        "source_date_epoch": epoch,
        "artifacts": artifacts,
        "checks": {},
    }
    (destination / "acceptance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Built {len(artifacts)} artifacts for {candidate}; acceptance is NOT RUN")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument(
        "--runtime-wheelhouse",
        type=Path,
        help="package the exact hash-locked Linux CPython 3.14 runtime closure",
    )
    args = parser.parse_args()
    build(
        args.destination.resolve(),
        runtime_wheelhouse=args.runtime_wheelhouse.resolve()
        if args.runtime_wheelhouse is not None
        else None,
    )
