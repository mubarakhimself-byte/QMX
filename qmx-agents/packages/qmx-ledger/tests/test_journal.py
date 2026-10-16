from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from qmx_ledger.journal import RunJournal, encoded, fingerprint


def records(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_serializes_reopens_and_refuses_other_writer(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    with RunJournal(path, "r") as journal:
        with pytest.raises(FileExistsError):
            RunJournal(path, "r")

        def append(n: int) -> dict[str, Any]:
            return journal.append("test", {"n": n})

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(append, range(20)))
        assert [r["seq"] for r in records(path)] == list(range(1, 21))
        raw = b"invalid evidence\x00\xff"
        assert Path(journal.quarantine(raw, "invalid")).read_bytes() == raw
    with RunJournal(path, "r") as journal:
        assert journal.append("end", {})["seq"] == 22


def test_record_fingerprint_covers_every_field(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    with RunJournal(path, "r", clock=lambda: "2026-10-14T00:00:00+00:00") as journal:
        record = journal.append("start", {"n": 1})
    stored = records(path)[0]
    assert stored == record
    digest = stored.pop("fingerprint")
    assert digest == fingerprint(stored)
    assert encoded(stored) == (
        b'{"event":"start","payload":{"n":1},"run_id":"r","seq":1,'
        b'"time":"2026-10-14T00:00:00+00:00"}'
    )


@pytest.mark.parametrize(
    ("before", "after"),
    [('"seq":1,', '"seq":9,'), ('"n":0', '"n":7'), ('"run_id":"r"', '"run_id":"x"')],
)
def test_reopen_refuses_broken_chain(tmp_path: Path, before: str, after: str) -> None:
    path = tmp_path / "run.jsonl"
    with RunJournal(path, "r") as journal:
        journal.append("a", {"n": 0})
        journal.append("b", {"n": 1})
    path.write_text(path.read_text().replace(before, after, 1))
    with pytest.raises(ValueError, match="corrupt"):
        RunJournal(path, "r")
    assert not path.with_suffix(".jsonl.lock").exists()


def test_reopen_refuses_other_run_id(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    with RunJournal(path, "r") as journal:
        journal.append("a", {})
    with pytest.raises(ValueError, match="corrupt"):
        RunJournal(path, "other")


def test_reopen_refuses_incomplete_record(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    with RunJournal(path, "r") as journal:
        journal.append("a", {})
    path.write_bytes(path.read_bytes() + b'{"seq":2')
    with pytest.raises(ValueError, match="incomplete"):
        RunJournal(path, "r")


def test_stale_lock_blocks_open_until_removed(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    lock = path.with_suffix(".jsonl.lock")
    lock.write_text("", encoding="utf-8")
    with pytest.raises(FileExistsError):
        RunJournal(path, "r")
    assert lock.exists()
    lock.unlink()
    with RunJournal(path, "r") as journal:
        assert journal.append("a", {})["seq"] == 1
    assert not lock.exists()


def test_closed_writer_refuses_appends(tmp_path: Path) -> None:
    journal = RunJournal(tmp_path / "run.jsonl", "r")
    journal.close()
    with pytest.raises(OSError, match="closed"):
        journal.append("a", {})


def test_blank_run_id_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="run id"):
        RunJournal(tmp_path / "run.jsonl", " ")
