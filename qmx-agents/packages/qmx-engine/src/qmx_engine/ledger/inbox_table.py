"""The inbox table: `<qmx_home>/engine/inbox.sqlite`, the `InboxPort` the engine raises items on.

It is its own file, not a table in `engine.sqlite`, because the one fault that most needs an item,
a ledger that cannot be written, must still be able to raise it (SOLUTION-DESIGN 10.3). The
engine is the only process that writes it. The category column is checked against the closed set,
so no other kind of item can be stored. An item's title, cause and what was tried pass the one
redaction (AD-37) before they are stored, so a provider message that echoes a key never lands here.
An engine that raises on the table also takes its answers: `resolve` records the answer, then hands
it to `answers`, which writes `gate_resolved` through the ledger writer and wakes the run (B-32).
"""

from __future__ import annotations

import json
import sqlite3
from hashlib import sha256
from pathlib import Path
from types import TracebackType
from typing import Final, Self, cast

from qmx_engine.ledger.redact import redact
from qmx_engine.ports.inbox import (
    ACTIONS,
    SEVERITY,
    Action,
    Answers,
    Category,
    Item,
    Raise,
    Severity,
)

BUSY_TIMEOUT_S: Final = 5.0
CATEGORIES: Final = ", ".join(f"'{c.value}'" for c in Category)
SCHEMA: Final = (
    "CREATE TABLE IF NOT EXISTS items ("
    " id TEXT PRIMARY KEY, run_id TEXT NOT NULL, signature TEXT NOT NULL,"
    f" category TEXT NOT NULL CHECK (category IN ({CATEGORIES})),"
    " severity TEXT NOT NULL, title TEXT NOT NULL, cause TEXT NOT NULL, node_id TEXT,"
    " tried TEXT NOT NULL, idempotency_key TEXT, blocks_run INTEGER NOT NULL,"
    " actions TEXT NOT NULL, first_raised_at TEXT NOT NULL, last_raised_at TEXT NOT NULL,"
    " count INTEGER NOT NULL, resolved_by TEXT, resolution TEXT, resolved_at TEXT,"
    " UNIQUE (run_id, signature))"
)
COLUMNS: Final = (
    "id, run_id, signature, category, severity, title, cause, node_id, tried, idempotency_key,"
    " blocks_run, actions, first_raised_at, last_raised_at, count, resolved_by, resolution,"
    " resolved_at"
)


def inbox_path(home: Path) -> Path:
    return home / "engine" / "inbox.sqlite"


def item_id(run_id: str, signature: str) -> str:
    return "inbox-" + sha256(f"{run_id}\n{signature}".encode()).hexdigest()[:16]


class InboxRefused(Exception):
    pass


class InboxTable:
    def __init__(self, path: Path) -> None:
        self.answers: Answers | None = None
        """The engine the answers go to; without one an answer is only recorded."""
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, isolation_level=None, timeout=BUSY_TIMEOUT_S)
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute(SCHEMA)

    @classmethod
    def open(cls, home: Path) -> InboxTable:
        return cls(inbox_path(home))

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

    def raise_item(self, item: Raise, *, at: str) -> str:
        """A repeat counts one more, takes the latest cause and what was tried, and reopens an
        item that was resolved."""
        found = item_id(item.run_id, item.signature)
        self.connection.execute(
            f"INSERT INTO items ({COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1,"  # noqa: S608
            " NULL, NULL, NULL)"
            " ON CONFLICT (run_id, signature) DO UPDATE SET count = count + 1,"
            " last_raised_at = excluded.last_raised_at, cause = excluded.cause,"
            " tried = excluded.tried, resolved_by = NULL, resolution = NULL, resolved_at = NULL",
            (
                found,
                item.run_id,
                item.signature,
                item.category.value,
                item.severity or SEVERITY[item.category],
                redact(item.title),
                redact(item.cause),
                item.node_id,
                json.dumps([redact(step) for step in item.tried]),
                item.idempotency_key,
                int(item.blocks_run),
                json.dumps(list(ACTIONS[item.category])),
                at,
                at,
            ),
        )
        return found

    def resolve(self, item_id: str, action: Action, principal: str, *, at: str) -> Item:
        item = self.get(item_id)
        if item is None:
            raise InboxRefused(f"no inbox item {item_id}")
        if action not in item.actions:
            raise InboxRefused(f"inbox item {item_id} does not offer {action}")
        self.connection.execute(
            "UPDATE items SET resolved_by = ?, resolution = ?, resolved_at = ? WHERE id = ?",
            (principal, action, at, item_id),
        )
        resolved = cast(Item, self.get(item_id))
        if self.answers is not None and action != "open_trace":
            self.answers.answer(resolved, action, principal, at=at)
        return resolved

    def get(self, item_id: str) -> Item | None:
        row = self.connection.execute(
            f"SELECT {COLUMNS} FROM items WHERE id = ?",  # noqa: S608
            (item_id,),
        ).fetchone()
        return None if row is None else _item(row)

    def list_items(self, *, open_only: bool = True) -> list[Item]:
        where = " WHERE resolved_at IS NULL" if open_only else ""
        rows = self.connection.execute(
            f"SELECT {COLUMNS} FROM items{where} ORDER BY first_raised_at, id"  # noqa: S608
        ).fetchall()
        return [_item(row) for row in rows]


def _item(row: tuple[object, ...]) -> Item:
    (
        found,
        run_id,
        signature,
        category,
        severity,
        title,
        cause,
        node_id,
        tried,
        key,
        blocks,
        actions,
        first,
        last,
        count,
        by,
        resolution,
        resolved_at,
    ) = row
    return Item(
        id=str(found),
        run_id=str(run_id),
        signature=str(signature),
        category=Category(category),
        severity=cast(Severity, severity),
        title=str(title),
        cause=str(cause),
        node_id=None if node_id is None else str(node_id),
        tried=tuple(json.loads(str(tried))),
        idempotency_key=None if key is None else str(key),
        blocks_run=bool(blocks),
        actions=tuple(json.loads(str(actions))),
        first_raised_at=str(first),
        last_raised_at=str(last),
        count=cast(int, count),
        resolved_by=None if by is None else str(by),
        resolution=cast(Action | None, resolution),
        resolved_at=None if resolved_at is None else str(resolved_at),
    )
