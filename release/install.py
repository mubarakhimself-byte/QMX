"""Install the checksum-bound QMX bundle into a non-editable private environment.

Run with CPython 3.14. Runtime downloads use the hash-pinned requirements;
developer/factory tools are not installed as product prerequisites.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import venv
from pathlib import Path


def install(bundle: Path, destination: Path) -> None:
    """Verify files before creating a clean environment; refuse accidental reuse."""
    if sys.version_info[:2] != (3, 14):
        raise RuntimeError("QMX requires CPython 3.14; use that interpreter to install")
    if destination.exists():
        raise RuntimeError(
            "Use a new destination to preserve an existing installation and its data"
        )
    record = json.loads((bundle / "acceptance.json").read_text(encoding="utf-8"))
    artifacts = record.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise RuntimeError("The bundle has no artifact checksum inventory")
    for name, digest in artifacts.items():
        if not isinstance(name, str) or Path(name).name != name:
            raise RuntimeError("Artifact paths must be local bundle filenames")
        path = bundle / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Artifact checksum mismatch: {name}")
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
    wheels = sorted(str(path) for path in bundle.glob("*.whl"))
    if not wheels:
        raise RuntimeError("Product wheels are missing")
    subprocess.run([str(python), "-m", "pip", "install", "--no-deps", *wheels], check=True)
    subprocess.run([str(python), "-m", "pip", "check"], check=True)
    with tarfile.open(bundle / "ui.tar.gz") as assets:
        assets.extractall(destination / "ui", filter="data")
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
