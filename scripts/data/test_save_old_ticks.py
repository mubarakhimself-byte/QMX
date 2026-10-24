"""The old-ticks saver, run twice over two scratch folders through a local rclone remote.

uv run --no-sync python -m pytest scripts/data -q -n 2
"""

# ruff: noqa: S101

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import save_old_ticks

NESTED = bytes(range(16))
FLAT = b"first file"
CSV = b"a,b\n1,2\n"
FILES = {"nested/two.bin": NESTED, "one.txt": FLAT, "three.csv": CSV}
TOTAL_BYTES = 34
EXPECTED_MANIFEST = [
    f"{hashlib.sha256(NESTED).hexdigest()}  16  nested/two.bin",
    f"{hashlib.sha256(FLAT).hexdigest()}  10  one.txt",
    f"{hashlib.sha256(CSV).hexdigest()}  8  three.csv",
]
RCLONE = save_old_ticks.find_rclone()

pytestmark = pytest.mark.skipif(RCLONE is None, reason="rclone is not installed")


def scratch(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """A config with one local remote, a source tree, a copy target and a record path."""
    config = tmp_path / "rclone.conf"
    config.write_text("[scratch]\ntype = local\n", encoding="utf-8")
    source = tmp_path / "old-ticks"
    for name, payload in FILES.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    return config, source, tmp_path / "server" / "old-ticks", tmp_path / "copy-record.json"


def test_first_run_records_the_source_count_and_bytes(tmp_path: Path) -> None:
    config, source, server, record = scratch(tmp_path)

    report = save_old_ticks.save_old_ticks(
        source, [f"scratch:{server.as_posix()}"], record, config=config, rclone=RCLONE
    )

    written = json.loads(record.read_text(encoding="utf-8"))
    assert (written["files"], written["bytes"], written["manifest_lines"]) == (3, TOTAL_BYTES, 3)
    manifest = (server / "MANIFEST.sha256").read_bytes()
    assert written["manifest_sha256"] == hashlib.sha256(manifest).hexdigest()
    assert manifest.decode("utf-8").splitlines() == EXPECTED_MANIFEST
    assert b"\r\n" not in manifest
    assert (server / "nested" / "two.bin").read_bytes() == NESTED
    assert (report.files, report.total_bytes, report.transfers) == (3, TOTAL_BYTES, 3)
    assert (report.destinations[0].compared, report.destinations[0].manifest) == (
        "size",
        "identical",
    )


def test_second_run_copies_zero_files_and_writes_the_same_record(tmp_path: Path) -> None:
    config, source, server, record = scratch(tmp_path)
    target = [f"scratch:{server.as_posix()}"]

    first = save_old_ticks.save_old_ticks(source, target, record, config=config, rclone=RCLONE)
    recorded = record.read_bytes()
    second = save_old_ticks.save_old_ticks(source, target, record, config=config, rclone=RCLONE)

    assert (first.transfers, second.transfers) == (3, 0)
    assert (second.destinations[0].bytes_moved, second.destinations[0].manifest) == (0, "identical")
    assert record.read_bytes() == recorded
    assert sorted(p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()) == [
        "nested/two.bin",
        "one.txt",
        "three.csv",
    ]
