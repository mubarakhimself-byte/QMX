"""The PC's write outbox: a save made while the Library server is away is kept, then replayed
once (Library AD-14, AD-26; 55 D-2).

One entry is one intent, appended to one local file: the item id, the ref it belongs on, the head
the PC read, the object id it intends, the kind and schema version that wrote it, and the
`qmx_version` of the writer. The replay is idempotent by the ref log alone: when the server ever
placed that object on that ref, the save is done, whether it is still the head or the ref has moved
past it. A reply lost after the commit therefore costs nothing, and a server workflow that moved the
same ref afterwards is not a conflict (F11).

Two refusals keep an entry instead of dropping it, because only a person or an update resolves
them: a kind or schema version the reader lacks (`needs_update`, naming the side that is behind,
F16 and N17), and a failure that says the primary could not be reached. A head that moved under an
entry whose object was never placed is neither dropped nor applied: it becomes a `merge-conflict`
item on the primary, so he picks the side (AD-26).

Reads never wait: `pending` is what a screen says about an entry, "waiting for the server".
"""

from __future__ import annotations

import importlib.metadata
import json
import os
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, Protocol, cast

from pydantic import JsonValue

from qmx_library.port import Commit, Draft, LibraryRefused

OUTBOX: Final = "outbox.jsonl"
NEEDS_UPDATE: Final = "needs_update"
WAITING: Final = "waiting for the server"


def qmx_version() -> str:
    """The version of the writer that minted an entry, so a reader can name the side behind."""
    try:
        return importlib.metadata.version("qmx-library")
    except importlib.metadata.PackageNotFoundError:
        return "0"


@dataclass(frozen=True, slots=True)
class Entry:
    """One pending write, exactly as the writer minted it."""

    item: str
    ref: str
    expected_head: str | None
    object_id: str
    kind: str
    schema_version: int
    draft: Mapping[str, JsonValue]
    """The port payload, so a replay re-sends the same save rather than a rewrite of it."""
    qmx_version: str = ""
    at: str = ""

    def row(self) -> dict[str, Any]:
        return {
            "item": self.item,
            "ref": self.ref,
            "expected_head": self.expected_head,
            "object_id": self.object_id,
            "kind": self.kind,
            "schema_version": self.schema_version,
            "draft": dict(self.draft),
            "qmx_version": self.qmx_version,
            "at": self.at,
        }

    @classmethod
    def parse(cls, row: Mapping[str, Any]) -> Entry:
        return cls(
            str(row["item"]),
            str(row["ref"]),
            None if row.get("expected_head") is None else str(row["expected_head"]),
            str(row["object_id"]),
            str(row["kind"]),
            int(row["schema_version"]),
            cast(Mapping[str, JsonValue], row.get("draft") or {}),
            str(row.get("qmx_version") or ""),
            str(row.get("at") or ""),
        )


def enter(
    draft: Draft,
    *,
    item: str,
    ref: str,
    expected_head: str | None,
    object_id: str,
    kind: str,
    schema_version: int,
    writer: str = "",
) -> Entry:
    """The entry a failed forward leaves behind. `item` and `object_id` were minted here, so the
    replay asks the primary for exactly the object this PC meant to save."""
    from qmx_library.client import draft_payload  # noqa: PLC0415 (one shared payload shape)

    payload = cast(Mapping[str, JsonValue], draft_payload(replace(draft, item=item)))
    return Entry(
        item,
        ref,
        expected_head,
        object_id,
        kind,
        schema_version,
        payload,
        writer or qmx_version(),
        datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )


class Target(Protocol):
    """What a replay needs from the store that answers: its ref log, its head, put and its kinds."""

    def ever_placed(self, object_id: str, item: str, ref: str) -> bool: ...

    def head(self, item: str, ref: str) -> str | None: ...

    def put(self, draft: Draft, *, on: str, expected_head: str | None) -> Commit: ...

    def can_read(self, kind: str, version: int) -> bool: ...

    def park(self, entry: Entry) -> str:
        """Mint the `merge-conflict` item for an entry whose ref moved under it."""
        ...


@dataclass(slots=True)
class Replayed:
    applied: list[str] = field(default_factory=list[str])
    """Object ids the primary now holds, this replay included."""
    kept: list[str] = field(default_factory=list[str])
    """Entries still waiting, by item."""
    parked: list[str] = field(default_factory=list[str])
    """Refs of the `merge-conflict` items a moved head produced."""
    refused: list[str] = field(default_factory=list[str])
    """Why each kept entry stayed, in the reader's words."""

    @property
    def ok(self) -> bool:
        return not self.kept


class Outbox:
    """The append-only file of pending intents, replayed in the order they were saved."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def entries(self) -> list[Entry]:
        if not self.path.exists():
            return []
        found: list[Entry] = []
        with self.path.open("rb") as handle:
            for line in handle:
                if not line.strip() or b"\x00" in line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict):
                    found.append(Entry.parse(cast(Mapping[str, Any], row)))
        return found

    def append(self, entry: Entry) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab") as handle:
            handle.write(json.dumps(entry.row(), sort_keys=True).encode("utf-8") + b"\n")
            handle.flush()
            os.fsync(handle.fileno())

    def replace(self, entries: Sequence[Entry]) -> None:
        """Rewrite the file with what is left. A crash mid-rewrite leaves the old file whole, so
        an entry is replayed twice rather than lost."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(f".{self.path.name}.{uuid.uuid4().hex}")
        with temp.open("wb") as handle:
            for entry in entries:
                handle.write(json.dumps(entry.row(), sort_keys=True).encode("utf-8") + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(self.path)

    def for_item(self, item: str) -> list[Entry]:
        return [entry for entry in self.entries() if entry.item == item]

    def __len__(self) -> int:
        return len(self.entries())


def replay(outbox: Outbox, target: Target) -> Replayed:
    """Send the entries in order and keep the ones that cannot land yet (AD-14, AD-26)."""
    from qmx_library.client import draft_from_payload  # noqa: PLC0415 (one payload shape)

    done = Replayed()
    kept: list[Entry] = []
    for entry in outbox.entries():
        if not target.can_read(entry.kind, entry.schema_version):
            kept.append(entry)
            done.kept.append(entry.item)
            done.refused.append(
                f"{NEEDS_UPDATE}: the server needs updating: it has no {entry.kind} schema "
                f"version {entry.schema_version} ({entry.item} on {entry.ref})"
            )
            continue
        if target.ever_placed(entry.object_id, entry.item, entry.ref):
            done.applied.append(entry.object_id)
            continue
        if target.head(entry.item, entry.ref) != entry.expected_head:
            done.parked.append(target.park(entry))
            continue
        try:
            target.put(
                draft_from_payload(entry.draft), on=entry.ref, expected_head=entry.expected_head
            )
        except LibraryRefused as refused:
            if refused.code == "stale_head":
                done.parked.append(target.park(entry))
                continue
            kept.append(entry)
            done.kept.append(entry.item)
            done.refused.append(f"{refused.code}: {refused}")
            continue
        done.applied.append(entry.object_id)
    outbox.replace(kept)
    return done
