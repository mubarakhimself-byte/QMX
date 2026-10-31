"""Every store of a QMX folder and the version this release writes (design 62 B1, Library AD-35).

`version` is the store version this release writes. `min_reader` is the oldest store version
whose code can still read and write it safely: a step that only adds leaves it, a step that
changes what existing data means raises it. A SQLite store's own file is the truth for both; a
store of plain files keeps them in the label; an index never refuses and is rebuilt instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

type Kind = Literal["sqlite", "files", "index"]

APPLICATION_ID: Final = 0x514D5831
"""`PRAGMA application_id` of every QMX SQLite file, the bytes `QMX1`, so tools recognise it."""


@dataclass(frozen=True, slots=True, order=True)
class Version:
    version: int
    min_reader: int


@dataclass(frozen=True, slots=True)
class Store:
    name: str
    """Its key in the label's `[stores]` table."""
    words: str
    """What a refusal calls it, in plain words."""
    kind: Kind
    release: Version
    path: str = ""
    """A SQLite store's or index's file, relative to the folder's `data/`."""
    tables: tuple[str, ...] = ()
    """Tables only this store's file holds: an unmarked file holding none of them is not QMX's."""
    meta: str = "qmx_meta"
    """The key-value table that holds the file's `min_reader` row."""
    version_key: str = ""
    """The `meta` row that held the version before files carried `user_version` (the engine's
    `schema_version`, which the release before this one still reads and writes)."""
    read_only: bool = False
    """Too new, it opens read-only instead of staying closed: its files are open formats an older
    reader understands as far as it goes (the Library and the price data)."""


STORES: Final = {
    store.name: store
    for store in (
        Store("library", "Library", "files", Version(1, 1), read_only=True),
        Store("market", "price data", "files", Version(1, 1), read_only=True),
        Store(
            "engine",
            "run ledger",
            "sqlite",
            Version(5, 3),
            "engine/engine.sqlite",
            ("events", "memos", "spans"),
            meta="meta",
            version_key="schema_version",
        ),
        Store("inbox", "inbox", "sqlite", Version(1, 1), "engine/inbox.sqlite", ("items",)),
        Store(
            "control",
            "control store",
            "sqlite",
            Version(1, 1),
            "control.db",
            ("sessions", "blocks", "events"),
        ),
        Store("runs_index", "run index", "sqlite", Version(1, 1), "runs.db", ("runs", "journals")),
        Store(
            "apps",
            "mini-app catalogue",
            "sqlite",
            Version(1, 1),
            "apps.db",
            ("definitions", "selected"),
        ),
        Store(
            "portfolio",
            "portfolio store",
            "sqlite",
            Version(1, 1),
            "portfolio.db",
            ("order_proposals",),
        ),
        Store("chats", "chats", "files", Version(1, 1)),
        Store("settings", "settings", "files", Version(1, 1)),
        Store(
            "catalog",
            "Library catalogue",
            "index",
            Version(1, 1),
            "library/catalog.db",
            ("objects", "moves", "heads"),
            meta="meta",
        ),
    )
}
"""The stores this release opens through `qmx_home.versions`, in the order `check_open` reads
them."""
