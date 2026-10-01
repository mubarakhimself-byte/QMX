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
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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


def build(destination: Path, ui_build: Path) -> None:
    """Build both workspaces, locked runtime dependencies and mandatory packs."""
    uv = shutil.which("uv")
    git = shutil.which("git")
    if uv is None or git is None:
        raise RuntimeError("uv and git are required for artifact construction")
    if not ui_build.is_dir() or not (ui_build / "index.html").is_file():
        raise RuntimeError("A built static UI with index.html is required")
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
            "release/launcher.py",
        ]
    )
    if dirty.strip():
        raise RuntimeError(
            "Commit reviewed product changes before binding artifacts to a candidate"
        )
    candidate = run([git, "rev-parse", "HEAD"]).strip()
    epoch = run([git, "show", "-s", "--format=%ct", "HEAD"]).strip()
    os.environ["SOURCE_DATE_EPOCH"] = epoch
    run([uv, "build", "--all-packages", "--out-dir", str(destination)])
    run([uv, "build", "--project", "qmx-agents", "--all-packages", "--out-dir", str(destination)])
    export = ["export", "--locked", "--no-default-groups", "--no-emit-local", "--no-header"]
    root_lock = run(
        [uv, *export, "--package", "qmb", "--package", "qmn", "--package", "qmf-calendar-forex"]
    )
    nested_lock = run([uv, *export, "--project", "qmx-agents", "--all-packages"])
    (destination / "requirements.lock").write_text(root_lock + "\n" + nested_lock)
    shutil.copyfile(ROOT / "release/launcher.py", destination / "launcher.py")
    archive(ui_build, destination / "ui.tar.gz")
    packs = ROOT / "qmx-agents/packages/qma-daemon/src/qma/daemon/bundled_packs"
    if not packs.is_dir():
        raise RuntimeError("Installed mandatory pack resources have not been repaired")
    pack_inventory = {
        path.relative_to(packs).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(packs.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }
    (destination / "pack-resources.json").write_text(json.dumps(pack_inventory, indent=2) + "\n")
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
    parser.add_argument("--ui-build", type=Path, required=True)
    args = parser.parse_args()
    build(args.destination.resolve(), args.ui_build.resolve())
