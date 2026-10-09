"""Publish blobs before manifests; readers fetch immutable blobs by their hash."""

from __future__ import annotations

import hashlib
import re
import shutil
import sqlite3
import subprocess
import tempfile
from contextlib import closing
from pathlib import Path

from qmx_remote.models import Artifact, Manifest, RemoteError, safe_path


def checksum(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def files(root: Path) -> list[Path]:
    result: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise RemoteError("Run files cannot be symlinks or junctions.")
        if path.is_file():
            safe_path(path.relative_to(root).as_posix())
            result.append(path)
    return result


class ResultsStore:
    def __init__(self, bucket: str):
        self.bucket = bucket.rstrip("/\\")
        if not self.bucket or self.bucket.startswith("-"):
            raise RemoteError("Set a local directory or named rclone remote as the bucket.")

    def location(self, run_id: str) -> str:
        # Run IDs also enter remote commands and filesystem paths.
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}", run_id):
            raise RemoteError("Invalid run id.")
        return self.bucket + "/runs/" + run_id

    @staticmethod
    def copy(source: str | Path, target: str | Path, *, include: str = "") -> None:
        def local(value: str | Path) -> bool:
            return (
                isinstance(value, Path)
                or ":" not in value
                or bool(re.match(r"^[A-Za-z]:[/\\]", value))
            )

        if local(source) and local(target):
            src, dst = Path(source), Path(target)
            for path in files(src):
                relative = path.relative_to(src)
                if include and "/" + relative.as_posix() != include:
                    continue
                output = dst / relative
                if not output.resolve().is_relative_to(dst.resolve()):
                    raise RemoteError("Result path escapes the bucket.")
                output.parent.mkdir(parents=True, exist_ok=True)
                pending = output.with_name(output.name + ".pending")
                shutil.copyfile(path, pending)
                pending.replace(output)
            return
        binary = shutil.which("rclone")
        if binary is None:
            raise RemoteError("Install rclone and configure the named SFTP or S3 remote.")
        args = [binary, "copy", str(source), str(target), "--checksum"]
        if include:
            args.extend(["--include", include])
        result = subprocess.run(args, capture_output=True, check=False, timeout=3600)
        if result.returncode:
            raise RemoteError("Result transfer failed; check rclone access on the target.")

    def publish(self, root: Path, manifest: Manifest) -> None:
        manifest.revision += 1
        with tempfile.TemporaryDirectory(prefix="qmx-publish-") as temporary:
            stage = Path(temporary)
            blobs = stage / "artifacts"
            blobs.mkdir()
            artifacts: list[Artifact] = []
            for source in files(root):
                name = source.relative_to(root).as_posix()
                if (
                    name.split("/")[0] not in {"outputs", "logs", "traces", "checkpoints"}
                    and name != "journal.jsonl"
                ):
                    continue
                if source.name.endswith(("-wal", "-shm", ".lock")):
                    continue
                data = source.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                (blobs / digest).write_bytes(data)
                artifacts.append(Artifact(path=name, sha256=digest, size=len(data)))
            manifest.artifacts = artifacts
            checkpoint = next(
                (a.sha256 for a in artifacts if a.path == "checkpoints/latest.db"), None
            )
            manifest.checkpoint = checkpoint
            manifest.seal()
            self.copy(stage, self.location(manifest.run_id))
            # A killed upload leaves the previous manifest valid and its blobs intact.
            self.commit(manifest)

    def commit(self, manifest: Manifest) -> None:
        manifest.seal()
        with tempfile.TemporaryDirectory(prefix="qmx-commit-") as temporary:
            stage = Path(temporary)
            (stage / "manifest.json").write_text(manifest.model_dump_json(), encoding="utf-8")
            self.copy(stage, self.location(manifest.run_id), include="/manifest.json")

    def read(self, run_id: str) -> Manifest:
        with tempfile.TemporaryDirectory(prefix="qmx-manifest-") as temporary:
            self.copy(self.location(run_id), temporary, include="/manifest.json")
            try:
                manifest = Manifest.model_validate_json(
                    (Path(temporary) / "manifest.json").read_bytes()
                )
                manifest.verify(run_id)
                return manifest
            except (OSError, ValueError) as error:
                raise RemoteError("Run manifest is missing or invalid.") from error

    def fetch(self, run_id: str, destination: Path) -> Manifest:
        manifest = self.read(run_id)
        destination.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="qmx-fetch-", dir=destination.parent) as temporary:
            stage = Path(temporary)
            # The manifest is read once; concurrent flushes cannot change this snapshot.
            for artifact in manifest.artifacts:
                blob = stage / "blobs"
                self.copy(self.location(run_id) + "/artifacts", blob, include="/" + artifact.sha256)
                source = blob / artifact.sha256
                if (
                    not source.is_file()
                    or source.stat().st_size != artifact.size
                    or checksum(source) != artifact.sha256
                ):
                    raise RemoteError("Run artifact hash or size mismatch.")
                target = stage / artifact.path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            for artifact in manifest.artifacts:
                target = destination / artifact.path
                if not target.resolve().is_relative_to(destination.resolve()):
                    raise RemoteError("Fetch destination escapes its run directory.")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(stage / artifact.path, target)
            (destination / "manifest.json").write_text(manifest.model_dump_json(), encoding="utf-8")
        return manifest


def snapshot_checkpoint(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    with closing(sqlite3.connect(source)) as db, closing(sqlite3.connect(temporary)) as copy:
        db.backup(copy)
        if copy.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise RemoteError("Workflow checkpoint snapshot is corrupt.")
        copy.execute("PRAGMA journal_mode=DELETE")
    temporary.replace(target)
