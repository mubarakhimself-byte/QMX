"""Save the old ticks to the server with checksums, and write the record the importer reads.

rclone does the copy and the comparison. This module decides what was copied, what was
compared, and what the record says. It never deletes a source file, and it never reads an
rclone config: it passes the config path to rclone and takes remote names only.

    uv run --no-sync python scripts/data/save_old_ticks.py `
        --source C:/Users/Mubarak/Documents/QMX/data/raw/external-deep-history `
        --target qmxserver:/srv/qmx/data/raw-backup/external-deep-history `
        --config D:/Tools/rclone/rclone-qmx.conf `
        --record D:/QMX-worktrees/qma-ship/data/evidence/dr0/copy-record.json

The check compares sizes and the written manifest, not a remote hash per file. A full
`rclone check --checksum` costs one remote md5sum per file, measured at 0.2 to 0.9 MB/s on
this tree's 257,628 small files, so `--check-mode checksum` is for small folders only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

MANIFEST_NAME = "MANIFEST.sha256"
NO_BUCKET = "no bucket remote configured"
_CHUNK = 1 << 20


@dataclass(frozen=True)
class Manifest:
    """One line per file: sha256, bytes, then the path relative to the source."""

    text: bytes
    files: int
    total_bytes: int
    sha256: str


@dataclass(frozen=True)
class Destination:
    remote: str
    transfers: int
    bytes_moved: int
    seconds: float
    compared: str
    manifest: str


@dataclass(frozen=True)
class Report:
    record: Path
    files: int
    total_bytes: int
    manifest_sha256: str
    transfers: int
    destinations: tuple[Destination, ...]


def find_rclone() -> str | None:
    """An explicit override, then PATH, then the path the plan installs it at."""
    for candidate in (
        os.environ.get("QMX_RCLONE"),
        shutil.which("rclone"),
        "D:/Tools/rclone/rclone.exe",
    ):
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def build_manifest(source: Path) -> Manifest:
    """Hash every file under `source` in path order, so a rerun writes the same bytes."""
    if not source.is_dir():
        raise ValueError(f"source is not a folder: {source}")
    rows: list[str] = []
    total = 0
    for path in sorted(p for p in source.rglob("*") if p.is_file()):
        size = path.stat().st_size
        total += size
        rows.append(f"{_sha256_file(path)}  {size}  {path.relative_to(source).as_posix()}")
    text = "".join(f"{row}\n" for row in rows).encode("utf-8")
    return Manifest(
        text=text,
        files=len(rows),
        total_bytes=total,
        sha256=hashlib.sha256(text).hexdigest(),
    )


def save_old_ticks(
    source: Path,
    targets: Sequence[str],
    record: Path,
    *,
    bucket: str | None = None,
    config: Path | None = None,
    copy_mode: str = "checksum",
    check_mode: str = "size",
    rclone: str | None = None,
) -> Report:
    """Copy `source` to each remote, compare the copy, then write the manifest and the record."""
    binary = rclone or find_rclone()
    if binary is None:
        raise RuntimeError("rclone is not installed; set QMX_RCLONE to the binary")
    remotes = [*targets, *([bucket] if bucket else [])]
    if not remotes:
        raise ValueError("no target given")
    for spec in remotes:
        _validate_remote(spec)
    manifest = build_manifest(source)
    with tempfile.TemporaryDirectory(prefix="qmx-old-ticks-") as scratch:
        local_manifest = Path(scratch) / MANIFEST_NAME
        local_manifest.write_bytes(manifest.text)
        destinations = tuple(
            _copy_to(binary, config, source, spec, local_manifest, manifest, copy_mode, check_mode)
            for spec in remotes
        )
    _write_record(record, _record_bytes(source, manifest, destinations))
    return Report(
        record=record,
        files=manifest.files,
        total_bytes=manifest.total_bytes,
        manifest_sha256=manifest.sha256,
        transfers=sum(destination.transfers for destination in destinations),
        destinations=destinations,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Copy the old ticks to a remote and write the record."
    )
    parser.add_argument("--source", type=Path, required=True, help="the folder to copy")
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        required=True,
        help="an rclone remote and path, such as qmxserver:/srv/qmx/data/raw-backup/old-ticks",
    )
    parser.add_argument("--record", type=Path, required=True, help="the JSON record to write")
    parser.add_argument("--bucket", default=None, help="the bucket remote, once G-R2 is open")
    parser.add_argument("--config", type=Path, default=None, help="the rclone config path")
    parser.add_argument("--copy-mode", choices=("checksum", "size"), default="checksum")
    parser.add_argument("--check-mode", choices=("size", "checksum"), default="size")
    args = parser.parse_args(argv)
    if not args.bucket:
        print(NO_BUCKET)
    try:
        report = save_old_ticks(
            args.source,
            args.target,
            args.record,
            bucket=args.bucket,
            config=args.config,
            copy_mode=args.copy_mode,
            check_mode=args.check_mode,
        )
    except (RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"source: {args.source} ({report.files} files, {report.total_bytes} bytes)")
    print(f"manifest: {report.manifest_sha256} ({report.files} lines)")
    for destination in report.destinations:
        rate = (
            destination.bytes_moved / destination.seconds / 1_000_000 if destination.seconds else 0
        )
        print(
            f"destination {destination.remote}: "
            f"{destination.transfers} files transferred ({rate:.1f} MB/s), "
            f"{destination.compared} check clean, manifest {destination.manifest}"
        )
    print(f"record: {report.record}")
    return 0


def _copy_to(
    binary: str,
    config: Path | None,
    source: Path,
    remote: str,
    local_manifest: Path,
    manifest: Manifest,
    copy_mode: str,
    check_mode: str,
) -> Destination:
    copy = _run(
        binary,
        config,
        [
            "copy",
            *_copy_flags(copy_mode),
            "--use-json-log",
            "--stats",
            "1m",
            "--stats-log-level",
            "NOTICE",
            str(source),
            remote,
        ],
    )
    if copy.returncode != 0:
        raise RuntimeError(f"rclone copy to {remote} failed ({copy.returncode}): {_tail(copy)}")
    transfers, bytes_moved, seconds = _stats(_output(copy))
    check = _run(
        binary, config, ["check", *_check_flags(check_mode), "--one-way", str(source), remote]
    )
    if check.returncode != 0:
        raise RuntimeError(
            f"rclone check against {remote} is not clean ({check.returncode}): {_tail(check)}"
        )
    target_manifest = f"{remote.rstrip('/')}/{MANIFEST_NAME}"
    upload = _run(binary, config, ["copyto", str(local_manifest), target_manifest])
    if upload.returncode != 0:
        raise RuntimeError(
            f"rclone copyto of the manifest to {remote} failed "
            f"({upload.returncode}): {_tail(upload)}"
        )
    readback = _run(binary, config, ["cat", target_manifest])
    if readback.returncode != 0 or readback.stdout != manifest.text:
        raise RuntimeError(
            f"the manifest on {remote} does not match the one written: {_tail(readback)}"
        )
    return Destination(
        remote=remote,
        transfers=transfers,
        bytes_moved=bytes_moved,
        seconds=seconds,
        compared=check_mode,
        manifest="identical",
    )


def _record_bytes(source: Path, manifest: Manifest, destinations: Sequence[Destination]) -> bytes:
    """Stable bytes: two runs over an unchanged source write the same record."""
    body = {
        "source": source.resolve().as_posix(),
        "files": manifest.files,
        "bytes": manifest.total_bytes,
        "manifest_sha256": manifest.sha256,
        "manifest_lines": manifest.files,
        "destinations": [
            {
                "remote": destination.remote,
                "compared": destination.compared,
                "manifest": destination.manifest,
            }
            for destination in destinations
        ],
    }
    return (json.dumps(body, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_record(record: Path, payload: bytes) -> None:
    record.parent.mkdir(parents=True, exist_ok=True)
    scratch = record.with_name(f"{record.name}.tmp")
    scratch.write_bytes(payload)
    os.replace(scratch, record)


def _copy_flags(mode: str) -> list[str]:
    return ["--checksum"] if mode == "checksum" else ["--size-only"]


def _check_flags(mode: str) -> list[str]:
    return ["--size-only"] if mode == "size" else []


def _run(
    binary: str, config: Path | None, args: Sequence[str]
) -> subprocess.CompletedProcess[bytes]:
    command = [binary, *(["--config", str(config)] if config else []), *args]
    return subprocess.run(command, capture_output=True, check=False)


def _output(process: subprocess.CompletedProcess[bytes]) -> str:
    return process.stdout.decode("utf-8", "replace") + process.stderr.decode("utf-8", "replace")


def _tail(process: subprocess.CompletedProcess[bytes]) -> str:
    return _output(process).strip()[-800:].replace("\n", " | ")


def _stats(output: str) -> tuple[int, int, float]:
    """The last json log line carrying rclone's stats: files, bytes and transfer seconds."""
    summary: tuple[int, int, float] | None = None
    for line in output.splitlines():
        if not line.startswith("{"):
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        stats = entry.get("stats")
        if isinstance(stats, dict) and isinstance(stats.get("transfers"), int):
            summary = (
                stats["transfers"],
                int(stats.get("bytes", 0)),
                float(stats.get("transferTime", 0.0)),
            )
    if summary is None:
        raise RuntimeError("rclone copy printed no stats line")
    return summary


def _validate_remote(spec: str) -> None:
    """A remote name, never a credential: rclone's config owns the secret."""
    if "://" in spec or spec.startswith(":") or "pass=" in spec.lower():
        raise ValueError(f"pass an rclone remote name, not a URL or connection string: {spec}")
    if ":" not in spec:
        raise ValueError(
            f"a target names an rclone remote and path, such as qmxserver:/srv/...: {spec}"
        )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
