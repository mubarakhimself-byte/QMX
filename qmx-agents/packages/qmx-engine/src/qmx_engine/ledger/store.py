"""The run ledger: `<qmx_home>/engine/engine.sqlite`, one writer thread, readers free (AD-23).

`Ledger` owns the only write connection. It lives on one thread, and every write from any caller
reaches it as an operation on a queue, so `seq` assignment and span derivation never race. The
thread commits whatever the queue holds in one transaction, each operation under its own
savepoint, so one failed operation fails only its own caller. A write returns after its commit.

A second writer in another process is refused by an OS lock on `engine.sqlite.lock`, which also
holds the owner's pid for the refusal message. The OS drops the lock when its process dies, so a
killed writer leaves nothing to clean up. `Reader` opens its own `mode=ro` connection and never
takes the lock.

No error raised here quotes event data: messages name the SQLite error code, never a value. Every
string in an event's data is redacted before it is queued (AD-37), so the stored text is the only
text: the event `append` returns, its span's `redactions` count and every reader see the same.
"""

from __future__ import annotations

import json
import os
import queue
import sqlite3
import sys
import threading
from collections.abc import Callable
from concurrent.futures import Future
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import IO, Final, Self, cast

from qmx_ledger.journal import encoded

from qmx_engine.ledger import spans
from qmx_engine.ledger.events import KINDS, Event, EventKind, JsonObject
from qmx_engine.ledger.migrations import migrate, schema_version
from qmx_engine.ledger.redact import redact_json

BATCH_LIMIT: Final = 256
BUSY_TIMEOUT_S: Final = 5.0
LOCK_OFFSET: Final = 4096


def ledger_path(home: Path) -> Path:
    return home / "engine" / "engine.sqlite"


class LedgerWriteError(Exception):
    pass


class WriterRefused(Exception):
    def __init__(self, path: Path, pid: int | None) -> None:
        holder = "an unknown pid" if pid is None else f"pid {pid}"
        super().__init__(f"the ledger {path} already has a writer: {holder}")
        self.pid = pid


def _write_error(error: sqlite3.Error) -> LedgerWriteError:
    return LedgerWriteError(f"ledger write failed: {getattr(error, 'sqlite_errorname', 'SQLITE')}")


class _WriterLock:
    """An exclusive OS lock on one byte past the pid text, held for the writer's lifetime."""

    def __init__(self, path: Path) -> None:
        # Unbuffered: a buffered read of the pid would reach the locked byte and fail.
        self._file: IO[bytes] = path.open("a+b", buffering=0)
        try:
            self._lock()
        except OSError:
            self._file.seek(0)
            text = self._file.read(32).decode("ascii", "replace").strip()
            self._file.close()
            raise WriterRefused(
                path.with_suffix(""), int(text) if text.isdigit() else None
            ) from None
        self._file.seek(0)
        self._file.truncate()
        self._file.write(str(os.getpid()).encode())
        self._file.flush()

    def _lock(self) -> None:
        if sys.platform == "win32":
            import msvcrt  # noqa: PLC0415

            self._file.seek(LOCK_OFFSET)
            msvcrt.locking(self._file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl  # noqa: PLC0415

            fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def release(self) -> None:
        self._file.seek(0)
        self._file.truncate()
        self._file.flush()
        if sys.platform == "win32":
            import msvcrt  # noqa: PLC0415

            self._file.seek(LOCK_OFFSET)
            msvcrt.locking(self._file.fileno(), msvcrt.LK_UNLCK, 1)
        self._file.close()


class Transaction:
    """What a write operation sees on the writer thread: the connection, inside an open
    transaction, and the next `seq` of a run counting writes not yet committed. An operation
    never runs BEGIN, COMMIT, ROLLBACK or RELEASE: the writer owns the transaction."""

    def __init__(self, connection: sqlite3.Connection, committed: dict[str, int]) -> None:
        self.connection = connection
        self._committed = committed
        self._batch: dict[str, int] = {}
        self._operation: dict[str, int] = {}

    def next_seq(self, run_id: str) -> int:
        last = self._operation.get(run_id) or self._batch.get(run_id) or self._committed.get(run_id)
        if last is None:
            row = self.connection.execute(
                "SELECT max(seq) FROM events WHERE run_id = ?", (run_id,)
            ).fetchone()
            last = row[0] or 0
        self._operation[run_id] = last + 1
        return last + 1

    def keep_operation(self) -> None:
        self._batch |= self._operation
        self._operation = {}

    def drop_operation(self) -> None:
        self._operation = {}

    def keep_batch(self) -> None:
        self._committed |= self._batch


type Operation[T] = Callable[[Transaction], T]


@dataclass(frozen=True, slots=True)
class _Item:
    operation: Operation[object]
    future: Future[object]


_STOP: Final = object()


class Ledger:
    """The one writer. Open it with `Ledger.open(home)`, then close it or use it as a context
    manager."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._lock = _WriterLock(path.with_name(path.name + ".lock"))
        self._queue: queue.SimpleQueue[_Item | object] = queue.SimpleQueue()
        self._ready = threading.Event()
        self._startup: BaseException | None = None
        self._closed = False
        self._close_mutex = threading.Lock()
        self.applied: list[int] = []
        self._seqs: dict[str, int] = {}
        self._thread = threading.Thread(target=self._run, name="qmx-engine-ledger", daemon=True)
        self._thread.start()
        self._ready.wait()
        if self._startup is not None:
            self._lock.release()
            raise self._startup

    @classmethod
    def open(cls, home: Path) -> Ledger:
        return cls(ledger_path(home))

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def write[T](self, operation: Operation[T]) -> T:
        """Run `operation` on the writer thread and return its result once committed. An
        operation does all its work through its `Transaction` and never calls `write` or `append`
        itself: the writer thread would wait on its own queue forever, so that is refused."""
        if threading.current_thread() is self._thread:
            raise LedgerWriteError("a ledger operation cannot write through the ledger again")
        future: Future[object] = Future()
        with self._close_mutex:
            if self._closed:
                raise LedgerWriteError("the ledger is closed")
            self._queue.put(_Item(cast(Operation[object], operation), future))
        return cast(T, future.result())

    def append(self, run_id: str, kind: EventKind, data: JsonObject, *, at: str) -> Event:
        """Append one event; `at` comes from the run's recorded clock (AD-6)."""
        if not run_id:
            raise ValueError("an event needs a run id")
        if kind not in KINDS:
            raise ValueError("unknown event kind")
        try:
            datetime.fromisoformat(at)
        except TypeError, ValueError:
            raise ValueError("`at` is not an ISO-8601 instant") from None
        try:
            # Through JSON first, so a string inside a tuple or a model is redacted too.
            clean, redactions = redact_json(json.loads(encoded(data)))
            text = encoded(clean).decode()
        except TypeError, ValueError:
            raise ValueError("event data is not a JSON object") from None
        data = cast(JsonObject, clean)
        if kind == "node_started" and spans.attempt_of(data) is None:
            raise ValueError("node_started needs a string node_id and an integer attempt")

        def operation(txn: Transaction) -> Event:
            seq = txn.next_seq(run_id)
            txn.connection.execute(
                "INSERT INTO events (run_id, seq, at, kind, data) VALUES (?, ?, ?, ?, ?)",
                (run_id, seq, at, kind, text),
            )
            event = Event(seq, run_id, at, kind, data)
            spans.apply(txn.connection, event, redactions)
            return event

        return self.write(operation)

    def close(self) -> None:
        with self._close_mutex:
            if self._closed:
                return
            self._closed = True
            self._queue.put(_STOP)
        self._thread.join()
        self._lock.release()

    def _run(self) -> None:
        try:
            connection = sqlite3.connect(
                self.path, isolation_level=None, timeout=BUSY_TIMEOUT_S, check_same_thread=True
            )
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
            self.applied = migrate(connection)
        except BaseException as error:
            self._startup = error
            self._ready.set()
            return
        self._ready.set()
        stopping = False
        while not stopping:
            batch: list[_Item] = []
            item = self._queue.get()
            while True:
                if item is _STOP:
                    stopping = True
                    break
                batch.append(cast(_Item, item))
                if len(batch) >= BATCH_LIMIT:
                    break
                try:
                    item = self._queue.get_nowait()
                except queue.Empty:
                    break
            if not batch:
                continue
            try:
                self._commit(connection, batch)
            except Exception as error:
                failure = _write_error(error) if isinstance(error, sqlite3.Error) else error
                self._seqs.clear()
                for unresolved in batch:
                    if not unresolved.future.done():
                        unresolved.future.set_exception(failure)
        try:
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            connection.close()

    def _commit(self, connection: sqlite3.Connection, batch: list[_Item]) -> None:
        txn = Transaction(connection, self._seqs)
        try:
            connection.execute("BEGIN IMMEDIATE")
        except sqlite3.Error as error:
            for item in batch:
                item.future.set_exception(_write_error(error))
            return
        done: list[tuple[_Item, object]] = []
        for index, item in enumerate(batch):
            try:
                connection.execute("SAVEPOINT operation")
                result = item.operation(txn)
                connection.execute("RELEASE operation")
            except Exception as error:
                txn.drop_operation()
                failure = _write_error(error) if isinstance(error, sqlite3.Error) else error
                # SQLITE_FULL, IOERR and NOMEM roll back the whole transaction, not only the
                # savepoint; running on would autocommit later operations outside it.
                try:
                    if not connection.in_transaction:
                        raise failure
                    connection.execute("ROLLBACK TO operation")
                    connection.execute("RELEASE operation")
                except Exception:
                    self._abandon(connection, [i for i, _ in done] + batch[index:], failure)
                    return
                item.future.set_exception(failure)
                continue
            txn.keep_operation()
            done.append((item, result))
        try:
            connection.execute("COMMIT")
        except sqlite3.Error as error:
            self._abandon(connection, [i for i, _ in done], _write_error(error))
            return
        txn.keep_batch()
        for item, result in done:
            item.future.set_result(result)

    def _abandon(
        self, connection: sqlite3.Connection, items: list[_Item], failure: BaseException
    ) -> None:
        """Roll the batch back, fail every caller still waiting, and forget the cached seqs so
        the next append reads `max(seq)` from the file."""
        try:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
        finally:
            self._seqs.clear()
            for item in items:
                item.future.set_exception(failure)


@dataclass(frozen=True, slots=True)
class Stats:
    schema_version: int
    sqlite_version: str | None
    events: int


class Reader:
    """A `mode=ro` connection to the ledger, for one thread. It never blocks the writer."""

    def __init__(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"no ledger at {path}")
        self.path = path
        self.connection = sqlite3.connect(
            f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=BUSY_TIMEOUT_S
        )

    @classmethod
    def open(cls, home: Path) -> Reader:
        return cls(ledger_path(home))

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    def events(self, run_id: str, *, after: int = 0) -> list[Event]:
        rows = self.connection.execute(
            "SELECT seq, at, kind, data FROM events WHERE run_id = ? AND seq > ? ORDER BY seq",
            (run_id, after),
        ).fetchall()
        return [Event(seq, run_id, at, kind, json.loads(data)) for seq, at, kind, data in rows]

    def spans(self, run_id: str) -> list[spans.Span]:
        rows = self.connection.execute(
            "SELECT record FROM spans WHERE trace_id = ? ORDER BY started_at, span_id", (run_id,)
        ).fetchall()
        return [spans.from_record(record) for (record,) in rows]

    def stats(self) -> Stats:
        version = schema_version(self.connection)
        row = self.connection.execute(
            "SELECT value FROM meta WHERE key = 'sqlite_version'"
        ).fetchone()
        (count,) = self.connection.execute("SELECT count(*) FROM events").fetchone()
        return Stats(version, None if row is None else row[0], count)
