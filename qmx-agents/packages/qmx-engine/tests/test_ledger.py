from __future__ import annotations

import os
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path

import pytest

from qmx_engine.ledger.events import JsonObject
from qmx_engine.ledger.store import Ledger, LedgerWriteError, Reader, Transaction

AT = "2026-10-17T09:00:00+00:00"


def test_eight_threads_get_contiguous_seq_per_run(tmp_path: Path) -> None:
    with Ledger.open(tmp_path) as ledger:

        def burst(thread: int) -> None:
            for i in range(50):
                ledger.append(f"run-{thread % 2}", "log", {"thread": thread, "i": i}, at=AT)

        threads = [threading.Thread(target=burst, args=(t,)) for t in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    with Reader.open(tmp_path) as reader:
        assert [e.seq for e in reader.events("run-0")] == list(range(1, 201))
        assert [e.seq for e in reader.events("run-1")] == list(range(1, 201))
        assert reader.stats().events == 400


def test_a_second_writer_process_is_refused_with_the_holders_pid(tmp_path: Path) -> None:
    script = (
        "import sys\nfrom pathlib import Path\n"
        "from qmx_engine.ledger.store import Ledger, Reader, WriterRefused\n"
        "try:\n    Ledger.open(Path(sys.argv[1]))\n"
        "except WriterRefused as refused:\n    print(refused)\n"
        "with Reader.open(Path(sys.argv[1])) as reader:\n    print(reader.stats().events)\n"
    )
    with Ledger.open(tmp_path) as ledger:
        ledger.append("run", "run_created", {"mode": "test"}, at=AT)
        child = subprocess.run(
            [sys.executable, "-c", script, str(tmp_path)],
            capture_output=True,
            text=True,
            check=True,
        )

    sqlite = tmp_path / "engine" / "engine.sqlite"
    assert child.stdout.splitlines() == [
        f"the ledger {sqlite} already has a writer: pid {os.getpid()}",
        "1",
    ]


def test_reopening_after_close_continues_seq_and_applies_no_migration(tmp_path: Path) -> None:
    with Ledger.open(tmp_path) as first:
        assert first.applied == [1]
        first.append("run", "run_created", {"mode": "live"}, at=AT)
        first.append("run", "clock_tick", {"now": AT}, at=AT)

    with Ledger.open(tmp_path) as second:
        assert second.applied == []
        third = second.append("run", "run_input", {"topic": "papers"}, at=AT)

    assert third.seq == 3
    with Reader.open(tmp_path) as reader:
        assert [(e.seq, e.kind, e.data) for e in reader.events("run")] == [
            (1, "run_created", {"mode": "live"}),
            (2, "clock_tick", {"now": AT}),
            (3, "run_input", {"topic": "papers"}),
        ]
        assert reader.stats().schema_version == 1


def test_a_failed_write_fails_only_its_caller_and_echoes_no_value(tmp_path: Path) -> None:
    def broken(txn: Transaction) -> None:
        txn.next_seq("run")
        txn.connection.execute("INSERT INTO nowhere VALUES (?)", ("sk-secret-value",))

    with Ledger.open(tmp_path) as ledger:
        ledger.append("run", "run_created", {"mode": "test"}, at=AT)
        with pytest.raises(LedgerWriteError) as caught:
            ledger.write(broken)
        after = ledger.append("run", "log", {"line": "still writing"}, at=AT)

    assert str(caught.value) == "ledger write failed: SQLITE_ERROR"
    assert after.seq == 2


def test_a_disk_full_batch_leaves_no_gap_and_no_stored_failure(tmp_path: Path) -> None:
    def cap_pages(extra: int) -> Callable[[Transaction], None]:
        def operation(txn: Transaction) -> None:
            (pages,) = txn.connection.execute("PRAGMA page_count").fetchone()
            txn.connection.execute(f"PRAGMA max_page_count = {pages + extra}")

        return operation

    confirmed: dict[str, int] = {}
    failed: list[str] = []
    mutex = threading.Lock()
    with Ledger.open(tmp_path) as ledger:
        ledger.append("run", "log", {"id": "first"}, at=AT)
        ledger.write(cap_pages(40))
        barrier = threading.Barrier(16)

        def burst(thread: int) -> None:
            barrier.wait()
            for i in range(40):
                name, size = f"{thread}-{i}", 30_000 if (thread, i) == (0, 3) else 200
                try:
                    event = ledger.append("run", "log", {"id": name, "p": "x" * size}, at=AT)
                except LedgerWriteError:
                    with mutex:
                        failed.append(name)
                    continue
                with mutex:
                    confirmed[name] = event.seq

        threads = [threading.Thread(target=burst, args=(t,)) for t in range(16)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        ledger.write(cap_pages(100_000))
        after = ledger.append("run", "log", {"id": "after"}, at=AT)

    with Reader.open(tmp_path) as reader:
        stored = reader.events("run")
    assert failed
    assert [e.seq for e in stored] == list(range(1, len(stored) + 1))
    by_id = {e.data["id"]: e.seq for e in stored}
    assert {name: by_id[name] for name in confirmed} == confirmed
    assert set(by_id) == {"first", "after", *confirmed}
    assert after.seq == len(stored)


def test_an_operation_that_writes_through_the_ledger_is_refused(tmp_path: Path) -> None:
    with Ledger.open(tmp_path) as ledger:

        def nested(txn: Transaction) -> None:
            ledger.append("run", "log", {"nested": True}, at=AT)

        with pytest.raises(LedgerWriteError, match=r"^a ledger operation cannot write"):
            ledger.write(nested)
        later = ledger.append("run", "log", {"i": 1}, at=AT)

    assert later.seq == 1


def test_refused_events_name_the_rule_and_not_the_value(tmp_path: Path) -> None:
    with Ledger.open(tmp_path) as ledger:
        with pytest.raises(ValueError, match=r"^`at` is not an ISO-8601 instant$"):
            ledger.append("run", "log", {}, at="sk-secret-value")
        with pytest.raises(ValueError, match=r"^event data is not a JSON object$"):
            ledger.append("run", "log", {"bad": float("nan")}, at=AT)
        with pytest.raises(ValueError, match=r"^node_started needs"):
            ledger.append("run", "node_started", {"node_id": "n1"}, at=AT)


def test_a_span_row_per_attempt_from_its_start_and_end(tmp_path: Path) -> None:
    with Ledger.open(tmp_path) as ledger:
        ledger.append("run", "run_created", {"mode": "test"}, at=AT)
        attempt: JsonObject = {"node_id": "n1", "attempt": 1}
        ledger.append("run", "node_started", attempt | {"model": "haiku"}, at=AT)
        failed: JsonObject = {**attempt, "signature": "abc", "tokens": {"in": 10, "out": 2}}
        ledger.append("run", "node_failed", failed, at="2026-10-17T09:00:04+00:00")
        ledger.append("run", "node_started", {"node_id": "n1", "attempt": 2}, at=AT)
        ledger.append("run", "node_waiting", {"node_id": "n9", "attempt": 1}, at=AT)

    with Reader.open(tmp_path) as reader:
        rows = [
            (s.node_id, s.attempt, s.status, s.duration_seconds, s.mode, s.model, s.tokens)
            for s in reader.spans("run")
        ]
    assert sorted(rows, key=lambda row: row[1]) == [
        ("n1", 1, "failed", 4.0, "test", "haiku", {"in": 10, "out": 2}),
        ("n1", 2, None, None, "test", None, {}),
    ]
