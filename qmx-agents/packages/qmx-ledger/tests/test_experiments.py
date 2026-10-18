"""Durable experiment evidence without the old actor and lease machinery."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from qmx_ledger.experiments import EvidenceRejected, ExperimentLedger


def test_reopen_retains_identity_refs_and_exact_bytes(tmp_path: Path) -> None:
    path = tmp_path / "experiment.db"
    data = b'{ "result_ref": "artifact:backtest", "predecessor_ref": "experiment:parent" }\n'
    ledger = ExperimentLedger(path, "experiment-a")
    entry = ledger.append(data, run_id="run-a", app_id="app-a")
    assert entry.seq == 1
    assert ExperimentLedger(path, "experiment-a").records() == (entry,)
    assert entry.data == data
    assert entry.run_id == "run-a" and entry.app_id == "app-a"
    with pytest.raises(ValueError, match="different experiment"):
        ExperimentLedger(path, "experiment-b")


@pytest.mark.parametrize(
    "data",
    [
        b"\xff\x00",
        b'{"jsonl": [1]}',
        b'{"run_ref": ""}',
        b'{"note": NaN}',
        b"[" * 2000 + b"]" * 2000,
    ],
)
def test_invalid_evidence_is_committed_verbatim(tmp_path: Path, data: bytes) -> None:
    ledger = ExperimentLedger(tmp_path / "experiment.db", "experiment-a")
    with pytest.raises(EvidenceRejected):
        ledger.append(data, run_id="run-a", app_id="app-a")
    record = ledger.records()[0]
    assert record.data == data
    assert record.disposition == "quarantine"
    assert record.reason
    next_entry = ledger.append(b'{"note": "correction"}', run_id="run-b", app_id="app-a")
    assert next_entry.seq == 2


def test_sqlite_refuses_updates_and_deletes(tmp_path: Path) -> None:
    path = tmp_path / "experiment.db"
    ledger = ExperimentLedger(path, "experiment-a")
    ledger.append(b'{"note": "original"}', run_id="run-a", app_id="app-a")
    with sqlite3.connect(path) as db:
        for sql in (
            "DELETE FROM entries",
            "UPDATE entries SET app_id='other'",
            "DELETE FROM identity",
        ):
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(sql)
    assert ledger.records()[0].app_id == "app-a"


def test_concurrent_writers_serialize_sequence(tmp_path: Path) -> None:
    path = tmp_path / "experiment.db"
    ledger = ExperimentLedger(path, "experiment-a")

    def append(index: int) -> int:
        return ledger.append(b'{"note": "observation"}', run_id=f"run-{index}", app_id="app-a").seq

    with ThreadPoolExecutor(max_workers=4) as pool:
        sequence = sorted(pool.map(append, range(12)))
    assert sequence == list(range(1, 13))
    assert len(ExperimentLedger(path, "experiment-a").records()) == 12


def test_storage_failure_raises_without_claiming_success(tmp_path: Path) -> None:
    path = tmp_path / "experiment.db"
    ledger = ExperimentLedger(path, "experiment-a")
    with sqlite3.connect(path) as db:
        db.execute("DROP TABLE entries")
    with pytest.raises(sqlite3.OperationalError):
        ledger.append(b'{"note": "observation"}', run_id="run-a", app_id="app-a")


def test_missing_identity_is_refused(tmp_path: Path) -> None:
    ledger = ExperimentLedger(tmp_path / "experiment.db", "experiment-a")
    with pytest.raises(ValueError, match="Run id and app id"):
        ledger.append(b'{"note": "observation"}', run_id="", app_id="app-a")
    assert ledger.records() == ()


def test_reopen_rejects_tampered_record_fingerprint(tmp_path: Path) -> None:
    path = tmp_path / "experiment.db"
    ledger = ExperimentLedger(path, "experiment-a")
    ledger.append(b'{"note": "original"}', run_id="run-a", app_id="app-a")
    with sqlite3.connect(path) as db:
        db.execute("DROP TRIGGER entries_no_update")
        db.execute("UPDATE entries SET data=?", (b'{"note": "forged"}',))
    with pytest.raises(ValueError, match="corrupt"):
        ExperimentLedger(path, "experiment-a")
