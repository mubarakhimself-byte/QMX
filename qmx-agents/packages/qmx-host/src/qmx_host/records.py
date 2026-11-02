"""The records host job: the one harvester of this machine, and on This PC the pull that brings
every node's records home (Part B AD-209, AD-210; Level 0 AD-28).

Every app on this machine only appends: journal records and series rows go through the writer
library into one-writer streams under its volume (`apps/<id>/data/journal`), and the host's own
`lifecycle` stream sits under `journals/`. The host is the only thing that files them into this
machine's store. Each round reads every stream with the committed reader, which never writes, and
commits partitions through this machine's market-data door with `born_on = node`:

| What | When |
| --- | --- |
| a closed month of any stream | each round until the store has frozen it, then never again |
| the open month of bars and reading history | every `[records] open_harvest_s` (60) |
| the open month of journals | the same, on This PC only, because `journal_query` reads it there |
| the open month of ticks | every `[records] tick_harvest_s` (3,600) |

A month is closed at its end, plus `[journals] settle_days` (1) for a journal stream. A stream
whose own fingerprint (its files and their sizes) is the last round's is skipped whole, and a
month whose rows have the fingerprint of its last commit is not committed again, because the store
counts the same rows committed again as a second fetch (`idempotent = False`), which would freeze
a bar month that is still open. The open month is one `open.parquet` the store replaces on each
commit (`qmf/data/series.py`), so a growing month never leaves a file per round.

The same round projects each closed paper, demo and live round trip into one Library `trade` item,
named by account, position id and world, so a re-projection lands nothing new, and scores each
paper lane's trades with the judge's paper scoring into its `paper-run` item. Nothing here writes
a `bot` or a `strategy`, and nothing here sends, changes or cancels an order.

The remote half (`Pull`) runs on This PC every `[records] interval_s` (300): per node, by the host
route, `data.list` after the node's watermark with the frozen fingerprints already home as
`confirmed`, then `data.fetch` of what is not home yet. The node's door keeps each `node`-born
partition pinned until This PC confirms it, and a confirmed one stays on the node, unpinned.
"""

# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

import httpx
from pydantic import JsonValue
from qmf.core import TypedRefusal, canonical_bytes, fingerprint, fingerprint_bytes, is_refusal
from qmf.data.journal_reader import CommittedLine, JournalLine, read_committed
from qmf.data.journal_writer import key_token
from qmf.data.series import JOURNAL_SOURCE_PREFIX, TICKS_KIND, CommitReceipt, SeriesKey
from qmf.data.store.engines import StoreEngineError
from qmf.data.store.engines.typed import FLOAT_COLUMNS, TypedWriter
from qmx_engine.service.forward import PASS_HEADER, mint_host_pass
from qmx_judge.paper import (
    PAPER_RUN_KIND,
    PaperLane,
    PaperRule,
    PaperTrade,
    ended_run,
    paper_run,
)
from qmx_library.port import Draft, JsonObject, LibraryRefused
from qmx_library.principal import MAIN, Principal

from qmx_host.maintenance import RESULT, landed
from qmx_host.market_data import MarketDoor, Placement, rows_of
from qmx_host.node_link import (
    CALL_TIMEOUT_S,
    NODE_APP,
    ROUTE_PATH,
    SCHEMA,
    Place,
    Post,
    Unreachable,
    post_json,
)

if TYPE_CHECKING:
    from qmx_library.store import Store

__all__ = [
    "JOB",
    "Cadence",
    "Fetch",
    "Harvest",
    "HarvestRound",
    "Harvester",
    "Listed",
    "NodeRound",
    "Outcome",
    "Projection",
    "Pull",
    "Records",
    "append_roots",
    "harvest_class",
    "trade_fields",
    "trade_item",
]

JOB: Final = "records"
STATE_NAME: Final = "harvest.json"
LANES_NAME: Final = "lanes.json"
TRADE_KIND: Final = "trade"
PROJECTED_WORLDS: Final = frozenset({"paper", "demo", "live"})
OPERATOR: Final = Principal("operator")
_S_PER_DAY: Final = 86_400


class Harvest(StrEnum):
    """A series' harvest class: what decides when its open month is committed."""

    JOURNAL = "journal"
    """Journals: their open month on This PC only, every `open_harvest_s`."""
    OPEN = "open"
    """Bars and reading history: their open month every `open_harvest_s`, on every machine."""
    TICKS = "ticks"
    """Ticks: their open month every `tick_harvest_s`, the largest file a harvest rewrites."""


def harvest_class(source: str, kind: str) -> Harvest:
    """The one rule from a series to its harvest class. A new store kind an app records is one
    more branch here."""
    if source == "journal-readings":
        return Harvest.OPEN
    if source.startswith(JOURNAL_SOURCE_PREFIX):
        return Harvest.JOURNAL
    if kind == TICKS_KIND:
        return Harvest.TICKS
    return Harvest.OPEN


def _positive(values: Mapping[str, object], name: str, default: int) -> int:
    value = values.get(name, default)
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return default


@dataclass(frozen=True, slots=True)
class Cadence:
    """`[records]` and `[journals]` as the harvester reads them. The defaults are the settings'
    own (`qmx_control.service.RECORDS_DEFAULTS`), kept here for a key that is not usable."""

    on: bool = True
    open_s: int = 60
    tick_s: int = 3_600
    interval_s: int = 300
    settle_days: int = 1
    open_pull_s: int = 3_600
    tick_pull_s: int = 86_400

    @classmethod
    def of(cls, records: Mapping[str, object], journals: Mapping[str, object]) -> Cadence:
        settle = journals.get("settle_days", 1)
        return cls(
            on=records.get("on", True) is not False,
            open_s=_positive(records, "open_harvest_s", 60),
            tick_s=_positive(records, "tick_harvest_s", 3_600),
            interval_s=_positive(records, "interval_s", 300),
            settle_days=settle if isinstance(settle, int) and settle >= 0 else 1,
            open_pull_s=_positive(records, "open_pull_s", 3_600),
            tick_pull_s=_positive(records, "tick_pull_s", 86_400),
        )

    def every(self, harvest: Harvest) -> int:
        return self.tick_s if harvest is Harvest.TICKS else self.open_s

    def pull_every(self, harvest: Harvest) -> int:
        """How often a node's open month of this class is fetched whole."""
        return self.tick_pull_s if harvest is Harvest.TICKS else self.open_pull_s


def append_roots(home: Path) -> tuple[Path, ...]:
    """Every append root on this machine: the host's own journals and each app volume's."""
    roots = [home / "journals"]
    apps = home / "apps"
    if apps.is_dir():
        roots.extend(sorted(path / "data" / "journal" for path in apps.iterdir() if path.is_dir()))
    return tuple(root for root in roots if root.is_dir())


@dataclass(slots=True)
class _Partition:
    """What the harvester knows of one partition month."""

    harvest: Harvest
    closes_at: int
    """Epoch seconds: the month's end, plus the settlement days of a journal stream."""
    committed: str | None = None
    """The fingerprint of the rows last committed."""
    frozen: bool = False
    at: int | None = None
    """Epoch seconds of the last commit."""
    waiting: bool = False
    """Rows past the last commit wait on the class's cadence."""

    def document(self) -> dict[str, object]:
        found: dict[str, object] = {
            "harvest": self.harvest.value,
            "closes_at": self.closes_at,
            "frozen": self.frozen,
            "waiting": self.waiting,
        }
        if self.committed is not None:
            found["committed"] = self.committed
        if self.at is not None:
            found["at"] = self.at
        return found

    @classmethod
    def parse(cls, value: Mapping[str, object]) -> _Partition:
        committed, at, closes = value.get("committed"), value.get("at"), value.get("closes_at")
        return cls(
            harvest=Harvest(str(value.get("harvest", Harvest.OPEN.value))),
            closes_at=closes if isinstance(closes, int) else 0,
            committed=committed if isinstance(committed, str) else None,
            frozen=value.get("frozen") is True,
            at=at if isinstance(at, int) else None,
            waiting=value.get("waiting") is True,
        )

    def due(self, now: int, cadence: Cadence) -> bool:
        return self.at is None or now - self.at >= cadence.every(self.harvest)


@dataclass(slots=True)
class _Stream:
    fingerprint: str = ""
    partitions: dict[str, _Partition] = field(default_factory=dict[str, _Partition])

    def settled(self, now: int, cadence: Cadence) -> bool:
        """Nothing here is due until the stream's bytes change: no month closed since it was
        committed, and no open month waits on a cadence that has come round."""
        return all(
            part.frozen or (now < part.closes_at and not (part.waiting and part.due(now, cadence)))
            for part in self.partitions.values()
        )


@dataclass(frozen=True, slots=True)
class HarvestRound:
    """One round's counts, as the `maintenance-result` carries them."""

    streams: int
    partitions: int
    skipped_unchanged: int
    waiting: int
    refusals: tuple[Mapping[str, object], ...]
    committed: tuple[str, ...]
    trades: int = 0
    paper_runs: int = 0

    def document(self) -> dict[str, object]:
        return {
            "streams": self.streams,
            "partitions": self.partitions,
            "skipped_unchanged": self.skipped_unchanged,
            "waiting": self.waiting,
            "refusals": [dict(item) for item in self.refusals],
            "trades": self.trades,
            "paper_runs": self.paper_runs,
        }


def _month_end_s(year: int, month: int) -> int:
    after = (year + 1, 1) if month == 12 else (year, month + 1)
    return int(datetime(*after, 1, tzinfo=UTC).timestamp())


def _month_of(t_ms: int) -> tuple[int, int]:
    moment = datetime.fromtimestamp(t_ms // 1_000, tz=UTC)
    return moment.year, moment.month


def _key(series: str, t_ms: int) -> SeriesKey | None:
    parts = series.split("/")
    if len(parts) != 4:
        return None
    made = SeriesKey.try_create(
        parts[0], parts[1], parts[2], *_month_of(t_ms), "" if parts[3] == "-" else parts[3]
    )
    return None if is_refusal(made) else made.value


def _canonical(line: JournalLine) -> str | None:
    text = canonical_bytes(dict(line.record))
    return None if is_refusal(text) else text.value.decode("utf-8")


def _row(line: CommittedLine, columns: Sequence[str]) -> tuple[object, ...]:
    if isinstance(line, JournalLine):
        return (line.t, line.seq, _canonical(line) or "")
    return tuple(
        (None if cell == "" else float.fromhex(cell)) if name in FLOAT_COLUMNS else int(cell)
        for name, cell in zip(columns, line.cells, strict=True)
    )


def _content(lines: Sequence[CommittedLine]) -> str | None:
    """The fingerprint of one month's rows, as the stream holds them."""
    texts: list[str] = []
    for line in lines:
        if isinstance(line, JournalLine):
            text = _canonical(line)
            if text is None:
                return None
            texts.append(f"{line.t}\t{line.seq}\t{text}")
        else:
            texts.append("\t".join((str(line.t), *line.cells)))
    return fingerprint_bytes("\n".join(texts).encode("utf-8")).value


def _reason(refusal: TypedRefusal) -> str:
    context = dict(refusal.context)
    return f"{refusal.category.value}: {context.get('reason') or context}"


def _stream_print(folder: Path) -> str:
    """One stream's own fingerprint: its rotation files and their sizes. A stream only grows at
    its end, so the same sizes are the same rows, and an unchanged stream is never read."""
    sizes = {
        path.name: path.stat().st_size
        for path in sorted(folder.glob("[0-9][0-9][0-9][0-9][0-9][0-9].jsonl"))
    }
    printed = fingerprint(sizes)
    return "" if is_refusal(printed) else printed.value.value


class Harvester:
    """The local half of the records job over one machine's append roots and its own door.

    ``folder`` is the harvester's own: its state file and its staging folder. ``journals_open``
    is true on This PC, where `journal_query` reads the open month of journals.
    """

    def __init__(
        self,
        roots: Callable[[], Sequence[Path]],
        door: MarketDoor,
        folder: Path,
        *,
        journals_open: bool,
    ) -> None:
        self._roots = roots
        self._door = door
        self._folder = folder
        self._journals_open = journals_open

    @property
    def staging(self) -> Path:
        return self._folder / "staging"

    def round(
        self, now: datetime, cadence: Cadence
    ) -> tuple[HarvestRound, tuple[JournalLine, ...]]:
        """One harvest round at ``now``, and the journal lines of every stream it read again.
        The app's stream files are only read."""
        at = int(now.timestamp())
        state = self._read_state()
        streams, skipped, waiting, partitions = 0, 0, 0, 0
        refusals: list[Mapping[str, object]] = []
        committed: list[str] = []
        read_again: list[JournalLine] = []
        for root in self._roots():
            for folder in sorted(entry for entry in root.iterdir() if entry.is_dir()):
                name = f"{root.as_posix()}|{folder.name}"
                try:
                    printed = _stream_print(folder)
                except OSError as error:
                    refusals.append({"stream": folder.name, "reason": str(error)})
                    continue
                known = state.get(name)
                if (
                    known is not None
                    and known.fingerprint == printed
                    and known.settled(at, cadence)
                ):
                    skipped += 1
                    continue
                read = read_committed(folder)
                if is_refusal(read):
                    refusals.append({"stream": folder.name, "reason": _reason(read)})
                    continue
                streams += 1
                stream = known or _Stream()
                done, waits = self._stream(read.value, stream, at, cadence, refusals, committed)
                partitions += done
                waiting += waits
                stream.fingerprint = printed
                state[name] = stream
                read_again.extend(line for line in read.value if isinstance(line, JournalLine))
        self._write_state(state)
        counts = HarvestRound(
            streams, partitions, skipped, waiting, tuple(refusals), tuple(committed)
        )
        return counts, tuple(read_again)

    def _stream(
        self,
        lines: Sequence[CommittedLine],
        stream: _Stream,
        at: int,
        cadence: Cadence,
        refusals: list[Mapping[str, object]],
        committed: list[str],
    ) -> tuple[int, int]:
        months: dict[str, tuple[SeriesKey, list[CommittedLine]]] = {}
        for line in lines:
            key = _key(line.series, line.t)
            if key is None:
                refusals.append({"series": line.series, "reason": "not a store key"})
                continue
            months.setdefault(key.text, (key, []))[1].append(line)
        landed_count, waiting = 0, 0
        for text, (key, rows) in months.items():
            journal = key.source.startswith(JOURNAL_SOURCE_PREFIX)
            closes = _month_end_s(key.year, key.month) + (
                cadence.settle_days * _S_PER_DAY if journal else 0
            )
            part = stream.partitions.setdefault(
                text, _Partition(harvest_class(key.source, key.kind), closes)
            )
            part.closes_at = closes
            if part.frozen:
                continue
            printed = _content(rows)
            if printed is None:
                refusals.append({"key": text, "reason": "a record has no canonical form"})
                continue
            if at < closes:
                if part.harvest is Harvest.JOURNAL and not self._journals_open:
                    continue
                if part.committed == printed:
                    part.waiting = False
                    continue
                if not part.due(at, cadence):
                    part.waiting = True
                    waiting += 1
                    continue
            frozen = self._commit(key, rows, refusals)
            if frozen is None:
                continue
            part.committed, part.frozen, part.at, part.waiting = printed, frozen, at, False
            landed_count += 1
            committed.append(text)
        return landed_count, waiting

    def _commit(
        self, key: SeriesKey, rows: Sequence[CommittedLine], refusals: list[Mapping[str, object]]
    ) -> bool | None:
        """Stage one partition in the door's own layout and commit it with `born_on = node`. It
        answers the store's frozen flag, or None when the door refused it (named in
        ``refusals``)."""
        target = self.staging.joinpath(
            *key.series.split("/"), f"{key.year:04d}-{key.month:02d}.parquet"
        )
        temp = target.with_name(f".{target.name}.incoming")
        columns = key.rule.columns
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            TypedWriter(temp, key.text, columns).add(_row(line, columns) for line in rows).finish()
            os.replace(temp, target)
        except (OSError, ValueError) as error:
            temp.unlink(missing_ok=True)
            refusals.append({"key": key.text, "reason": f"could not stage: {error}"})
            return None
        try:
            receipts = self._door.commit([target], staging=self.staging, born_on=Placement.NODE)
        finally:
            target.unlink(missing_ok=True)
        if is_refusal(receipts):
            refusals.append({"key": key.text, "reason": _reason(receipts)})
            return None
        return receipts.value[0].frozen

    def _read_state(self) -> dict[str, _Stream]:
        try:
            raw = json.loads((self._folder / STATE_NAME).read_text(encoding="utf-8"))
        except OSError, ValueError:
            return {}
        streams: dict[str, _Stream] = {}
        for name, value in cast("dict[str, dict[str, object]]", raw.get("streams", {})).items():
            parts = cast("dict[str, Mapping[str, object]]", value.get("partitions", {}))
            streams[name] = _Stream(
                str(value.get("fingerprint", "")),
                {key: _Partition.parse(part) for key, part in parts.items()},
            )
        return streams

    def _write_state(self, state: Mapping[str, _Stream]) -> None:
        document = {
            "streams": {
                name: {
                    "fingerprint": stream.fingerprint,
                    "partitions": {
                        key: part.document() for key, part in sorted(stream.partitions.items())
                    },
                }
                for name, stream in sorted(state.items())
            }
        }
        _write_json(self._folder / STATE_NAME, document)


def _write_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
    os.replace(temp, path)


# --- the Library `trade` projection and the paper lanes ---------------------------------------


def trade_item(record: Mapping[str, object]) -> str | None:
    """The `trade` item of one journal round trip, named by account, position id and world."""
    body = cast("Mapping[str, object]", record.get("body", {}))
    position = body.get("position_id", body.get("trade_id"))
    account, world = record.get("account"), record.get("world")
    if not isinstance(position, str) or not isinstance(account, str) or not isinstance(world, str):
        return None
    named = fingerprint({"account": account, "position_id": position, "world": world})
    return None if is_refusal(named) else f"trade-{named.value.digest[:24]}"


def _decimal(value: object) -> Decimal | None:
    if not isinstance(value, str | int) or isinstance(value, bool):
        return None
    try:
        found = Decimal(str(value))
    except InvalidOperation:
        return None
    return found if found.is_finite() else None


def _text(value: object) -> str | None:
    """An exact number or a word as the kind keeps it: decimal text, never a binary float."""
    if isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return None


def _digits(*values: Decimal | None) -> int:
    exponents = [-cast("int", v.as_tuple().exponent) for v in values if v is not None]
    return max([0, *exponents])


def _scaled(value: Decimal | None, digits: int) -> int | None:
    return None if value is None else int(value.scaleb(digits))


def trade_fields(record: Mapping[str, object]) -> JsonObject | None:
    """A journal `trade` row as `trade` version 2 fields, or None when it names no account or
    market. Money and prices are scaled integers with their digits. A trade whose initial risk is
    unknown carries `r_missing` and no R."""
    body = cast("Mapping[str, object]", record.get("body", {}))
    account, market, world = record.get("account"), record.get("market_id"), record.get("world")
    side = body.get("side")
    if not all(isinstance(value, str) for value in (account, market, world, side)):
        return None
    position = body.get("position_id", body.get("trade_id"))
    money = _decimal(body.get("money"))
    money_digits = _digits(money)
    entry, exit_price = _decimal(body.get("entry_price")), _decimal(body.get("exit_price"))
    price_digits = _digits(entry, exit_price)
    r = _decimal(body.get("r"))
    fields: dict[str, object] = {
        "account": account,
        "instrument": market,
        "market_id": market,
        "side": side,
        "world": world,
        "money_digits": money_digits,
        "price_digits": price_digits,
        "r_missing": r is None,
        "gap_through_stop": body.get("gap_through_stop") is True,
    }
    optional: dict[str, object | None] = {
        "position_id": position if isinstance(position, str) else None,
        "broker": record.get("venue"),
        "run_id": record.get("run_id"),
        "machine": record.get("machine"),
        "trace_id": record.get("trace_id"),
        "volume": body.get("quantity"),
        "entry_ns": body.get("opened_at"),
        "exit_ns": body.get("closed_at"),
        "entry_price": _scaled(entry, price_digits),
        "exit_price": _scaled(exit_price, price_digits),
        "net_result": _scaled(money, money_digits),
        "r": None if r is None else float(r),
        "mae_r": _text(body.get("mae_r")),
        "mfe_r": _text(body.get("mfe_r")),
        "costs": body.get("costs") if isinstance(body.get("costs"), dict) else None,
        "equity_before": _text(body.get("equity_before")),
        "session": _text(body.get("session")),
        "streak": body.get("streak") if isinstance(body.get("streak"), int) else None,
        "placeholders": body.get("placeholders")
        if isinstance(body.get("placeholders"), list)
        else None,
    }
    unit, version = record.get("unit_id"), record.get("unit_version")
    if isinstance(unit, str):
        optional["unit"] = f"{unit}@{version}" if isinstance(version, str) else unit
    entry_ns, exit_ns = body.get("opened_at"), body.get("closed_at")
    if isinstance(entry_ns, int) and isinstance(exit_ns, int):
        optional["holding_ns"] = exit_ns - entry_ns
    fields.update({name: value for name, value in optional.items() if value is not None})
    return cast("JsonObject", fields)


def _lane_key(record: Mapping[str, object]) -> tuple[str, str, str, str] | None:
    parts = (
        record.get("unit_id"),
        record.get("market_id"),
        record.get("account"),
        record.get("machine"),
    )
    if not all(isinstance(part, str) for part in parts):
        return None
    return cast("tuple[str, str, str, str]", parts)


def _at_ns(text: object) -> int | None:
    if not isinstance(text, str):
        return None
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return int(moment.timestamp()) * 1_000_000_000


def _fold_moves(lines: Sequence[JournalLine], starts: dict[str, dict[str, object]]) -> None:
    """Fold the `lifecycle` moves in ``lines`` into each market's lane entry: its latest move
    (``to``, ``moved_at``) and, kept apart, its latest move into paper (``paper_at``), the lane's
    start."""
    for line in lines:
        record = line.record
        if record.get("kind") != "lifecycle":
            continue
        body = cast("Mapping[str, object]", record.get("body", {}))
        unit, market, to = body.get("unit_id"), body.get("market_id"), str(body.get("to"))
        moved = _at_ns(body.get("at"))
        if not isinstance(unit, str) or not isinstance(market, str) or moved is None:
            continue
        entry = starts.setdefault(f"{unit}|{market}", {})
        if to == "paper" and moved >= cast("int", entry.get("paper_at", moved)):
            entry["paper_at"] = moved
        if moved >= cast("int", entry.get("moved_at", moved)):
            entry["to"], entry["moved_at"] = to, moved


def _lane_state(entry: Mapping[str, object]) -> tuple[str, int | None, int | None]:
    """A market's paper lane as its moves left it: status, start and end in epoch ns. The start
    is unknown while no move into paper was seen."""
    paper_at = entry.get("paper_at")
    started = paper_at if isinstance(paper_at, int) else None
    to = entry.get("to")
    if to is None or to == "paper":
        return "running", started, None
    return ("ended" if to == "live" else "stopped"), started, cast("int", entry["moved_at"])


class Projection:
    """The records job's Library writes: `trade` items and the paper lanes' `paper-run` items.

    ``folder`` holds each market's lane entry, read from its `lifecycle` moves, and the accounts
    and nodes its paper runs were scored on. A lane keeps its start once that stream has been
    filed, and a later move out of paper ends its runs even when their trades are not re-read.
    """

    def __init__(
        self,
        store: Store,
        folder: Path,
        *,
        rule: Callable[[], PaperRule] = PaperRule,
    ) -> None:
        self._store = store
        self._folder = folder
        self._rule = rule

    def land(self, lines: Sequence[JournalLine], now: datetime) -> tuple[int, int]:
        """Project the round trips and score the paper lanes in ``lines``; the counts of `trade`
        and `paper-run` versions that landed."""
        starts = self._read_lanes()
        _fold_moves(lines, starts)
        self._write_lanes(starts)
        trades = 0
        lanes: dict[tuple[str, str, str, str], list[Mapping[str, object]]] = {}
        series: dict[tuple[str, str, str, str], set[str]] = {}
        for line in lines:
            record = line.record
            if record.get("kind") != TRADE_KIND or record.get("world") not in PROJECTED_WORLDS:
                continue
            if self._project(record):
                trades += 1
            lane = _lane_key(record)
            if record.get("world") == "paper" and lane is not None:
                lanes.setdefault(lane, []).append(record)
                series.setdefault(lane, set()).add(line.series)
        papers = sum(
            self._paper(lane, rows, starts, series[lane], now) for lane, rows in lanes.items()
        )
        papers += sum(self._end(key, entry, lanes.keys()) for key, entry in sorted(starts.items()))
        self._write_lanes(starts)
        return trades, papers

    def _project(self, record: Mapping[str, object]) -> bool:
        item, fields = trade_item(record), trade_fields(record)
        if item is None or fields is None or self._store.head(item, MAIN) is not None:
            return False
        title = f"{fields['side']} {fields['instrument']} ({fields['world']})"
        return self._put(TRADE_KIND, item, fields, title)

    def _paper(
        self,
        lane: tuple[str, str, str, str],
        rows: Sequence[Mapping[str, object]],
        starts: dict[str, dict[str, object]],
        series: set[str],
        now: datetime,
    ) -> int:
        unit, market, account, node = lane
        trades: list[PaperTrade] = []
        for record in rows:
            body = cast("Mapping[str, object]", record.get("body", {}))
            closed = body.get("closed_at")
            if isinstance(closed, int):
                trades.append(PaperTrade(closed, _decimal(body.get("r"))))
        if not trades:
            return 0
        entry = starts.setdefault(f"{unit}|{market}", {})
        scored = cast("list[list[str]]", entry.setdefault("lanes", []))
        if [account, node] not in scored:
            scored.append([account, node])
        status, started, ended = _lane_state(entry)
        if started is None:
            opened = [
                cast("int", cast("Mapping[str, object]", r.get("body", {})).get("opened_at", 0))
                for r in rows
            ]
            started = min(opened)
        item, fields = paper_run(
            PaperLane(unit, market, account, node, started),
            trades,
            now_ns=int(now.timestamp()) * 1_000_000_000,
            status=status,
            ended_at_ns=ended,
            journal=sorted(series),
            rule=self._rule(),
        )
        found = self._store.head(item, MAIN)
        head = None if found is None else found[0]
        if head is not None and self._store.get(OPERATOR, head).fields == fields:
            return 0
        title = f"Paper run of {unit} on {market}"
        landed = self._put(PAPER_RUN_KIND, item, cast("JsonObject", fields), title, head=head)
        return 1 if landed else 0

    def _end(
        self,
        key: str,
        entry: Mapping[str, object],
        scored: Iterable[tuple[str, str, str, str]],
    ) -> int:
        """End the runs a move out of paper closed whose trades this round did not re-read. A run
        already ended lands nothing again."""
        status, started, ended = _lane_state(entry)
        if started is None or ended is None:
            return 0
        unit, _, market = key.partition("|")
        rescored = set(scored)
        landed = 0
        for account, node in cast("list[list[str]]", entry.get("lanes", [])):
            if (unit, market, account, node) in rescored:
                continue
            item = PaperLane(unit, market, account, node, started).item
            found = self._store.head(item, MAIN)
            if found is None:
                continue
            last = self._store.get(OPERATOR, found[0]).fields
            fields = ended_run(last, status=status, ended_at_ns=ended)
            if fields == last:
                continue
            title = f"Paper run of {unit} on {market}"
            if self._put(PAPER_RUN_KIND, item, cast("JsonObject", fields), title, head=found[0]):
                landed += 1
        return landed

    def _put(
        self, kind: str, item: str, fields: JsonObject, title: str, *, head: str | None = None
    ) -> bool:
        """Land a version of ``item`` over ``head``, the main head it was read at."""
        draft = Draft(kind, item, title=title, summary=title, fields=fields)
        try:
            self._store.put(OPERATOR, draft, on=MAIN, expected_head=head)
        except LibraryRefused as refused:
            print(f"records: the {kind} {item} did not land: {refused}", file=sys.stderr)
            return False
        return True

    def _read_lanes(self) -> dict[str, dict[str, object]]:
        try:
            raw = json.loads((self._folder / LANES_NAME).read_text(encoding="utf-8"))
        except OSError, ValueError:
            return {}
        return cast("dict[str, dict[str, object]]", raw) if isinstance(raw, dict) else {}

    def _write_lanes(self, starts: Mapping[str, Mapping[str, object]]) -> None:
        _write_json(self._folder / LANES_NAME, dict(starts))


# --- the remote half: records come home from the nodes -------------------------------------------


HOME_JOB: Final = "records-home"
HOME_NAME: Final = "Bring node records home"
PULL_NAME: Final = "pull.json"
TAIL_FOLDER: Final = "tail"
FETCH_READ_S: Final = 60.0
"""Seconds a partition fetch waits for its next bytes, so a month of any size streams in whole
and only a stalled line ends it."""

type Fetch = Callable[[str, Mapping[str, JsonValue], Mapping[str, str], Path], int]
"""One `data.fetch` POST: the answer's body streams into the path, and its HTTP status comes
back. A host that does not answer at all raises `Unreachable`."""


def fetch_file(
    url: str, body: Mapping[str, JsonValue], headers: Mapping[str, str], into: Path
) -> int:
    try:
        with httpx.stream(
            "POST",
            url,
            json=dict(body),
            headers=dict(headers),
            timeout=httpx.Timeout(FETCH_READ_S, connect=CALL_TIMEOUT_S),
        ) as answer:
            with into.open("wb") as handle:
                for chunk in answer.iter_bytes():
                    handle.write(chunk)
            return answer.status_code
    except httpx.TransportError as error:
        raise Unreachable(f"{type(error).__name__}: {error}") from error


class Outcome(StrEnum):
    """What one listed partition came to in a round; the watermark stops at the first failure."""

    HOME = "home"
    """Committed here now, or already here with the listed fingerprint."""
    WAITING = "waiting"
    """An open month whose class is not due yet; it is listed again after its next harvest."""
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Listed:
    """One partition a node's `data.list` named."""

    key: SeriesKey
    fingerprint: str
    bytes: int
    frozen: bool
    committed_at: str

    @classmethod
    def parse(cls, row: Mapping[str, object]) -> Listed | None:
        text, printed, size = row.get("key"), row.get("fingerprint"), row.get("bytes")
        frozen, at = row.get("frozen"), row.get("committed_at")
        if not (
            isinstance(text, str)
            and isinstance(printed, str)
            and isinstance(size, int)
            and isinstance(frozen, bool)
            and isinstance(at, str)
        ):
            return None
        parts = text.split("/")
        month = re.fullmatch(r"(\d{4})-(\d{2})", parts[-1])
        if len(parts) != 5 or month is None:
            return None
        source, subject, kind, variant = parts[:4]
        made = SeriesKey.try_create(
            source,
            subject,
            kind,
            int(month.group(1)),
            int(month.group(2)),
            "" if variant == "-" else variant,
        )
        return None if is_refusal(made) else cls(made.value, printed, size, frozen, at)

    @property
    def month(self) -> str:
        return f"{self.key.year:04d}-{self.key.month:02d}"


@dataclass(frozen=True, slots=True)
class NodeRound:
    """One node's part of a pull round, as the `maintenance-result` carries it."""

    node: str
    reached: bool
    partitions: int = 0
    """Partitions committed here this round, closed and open."""
    open_fetched: int = 0
    already_home: int = 0
    waiting: int = 0
    bytes: int = 0
    confirmed: int = 0
    """Fingerprints this round's `data.list` confirmed, so the node's door unpinned them."""
    still_pinned: tuple[str, ...] = ()
    oldest_unshipped: str | None = None
    tail_rows: int = 0
    refusals: tuple[Mapping[str, object], ...] = ()

    def document(self) -> dict[str, object]:
        return {
            "node": self.node,
            "reached": self.reached,
            "partitions": self.partitions,
            "open_fetched": self.open_fetched,
            "already_home": self.already_home,
            "waiting": self.waiting,
            "bytes": self.bytes,
            "confirmed": self.confirmed,
            "still_pinned": list(self.still_pinned),
            "oldest_unshipped": self.oldest_unshipped,
            "tail_rows": self.tail_rows,
            "refusals": [dict(item) for item in self.refusals],
        }


@dataclass(slots=True)
class _Node:
    """What This PC keeps of one node between rounds, in `records/pull.json`."""

    watermark: str = ""
    """The `committed_at` past which every partition the node listed is home or waiting."""
    confirm: list[str] = field(default_factory=list[str])
    """Fingerprints of frozen partitions home here, for the next `data.list` to confirm."""
    opened: dict[str, int] = field(default_factory=dict[str, int])
    """Each open month's key and when it was last fetched, in epoch seconds."""
    last: dict[str, object] | None = None

    def document(self) -> dict[str, object]:
        return {
            "watermark": self.watermark,
            "confirm": self.confirm,
            "opened": dict(sorted(self.opened.items())),
            "last": self.last,
        }

    @classmethod
    def parse(cls, value: Mapping[str, object]) -> _Node:
        watermark, confirm = value.get("watermark"), value.get("confirm")
        opened, last = value.get("opened"), value.get("last")
        return cls(
            watermark if isinstance(watermark, str) else "",
            [str(item) for item in cast("list[object]", confirm)]
            if isinstance(confirm, list)
            else [],
            {str(k): int(v) for k, v in cast("dict[str, int]", opened).items()}
            if isinstance(opened, dict)
            else {},
            cast("dict[str, object]", last) if isinstance(last, dict) else None,
        )


@dataclass(slots=True)
class _Tally:
    partitions: int = 0
    open_fetched: int = 0
    already_home: int = 0
    waiting: int = 0
    bytes: int = 0
    oldest: str | None = None

    def unshipped(self, listed: Listed) -> None:
        self.oldest = listed.month if self.oldest is None else min(self.oldest, listed.month)


class _Missed(Exception):
    """A node that did not answer an ask, or refused it; the message names why."""


def _advanced(mark: str, outcomes: Sequence[tuple[str, Outcome]]) -> str:
    """The watermark past every partition that came home or waits on its cadence, and never past
    one that failed: it is listed again next round, with whatever followed it."""
    failed = [at for at, outcome in outcomes if outcome is Outcome.FAILED]
    first = min(failed, default=None)
    passed = [
        at
        for at, outcome in outcomes
        if outcome is not Outcome.FAILED and (first is None or at < first)
    ]
    return max([mark, *passed])


class Pull:
    """The records job's remote half, on This PC only (Part B AD-210, Level 0 AD-28).

    Each round asks every owned node its `data.list` after its watermark, confirming the frozen
    partitions the last round brought home, so the node's door unpins them and keeps them. It
    fetches each listed partition this door does not hold with that fingerprint: a frozen one at
    once, an open one only when its class is due. The fetched rows are fingerprinted before the
    commit, so a partition whose rows differ from what the node listed never lands. A partition
    is named by its key, and one this door holds with its fingerprint is home already, so a
    resend lands nothing. Nothing here pushes into This PC or prunes a node.
    """

    def __init__(
        self,
        door: MarketDoor,
        folder: Path,
        *,
        here: str,
        places: Callable[[], Mapping[str, Place]],
        key: Callable[[], str | None],
        post: Post = post_json,
        fetch: Fetch = fetch_file,
    ) -> None:
        self._door = door
        self._folder = folder
        self._here = here
        self._places = places
        self._key = key
        self._post = post
        self._fetch = fetch

    @property
    def staging(self) -> Path:
        return self._folder / "pull-staging"

    def round(self, now: datetime, cadence: Cadence) -> tuple[NodeRound, ...]:
        """One pull round at ``now`` over every owned node."""
        at = int(now.timestamp())
        state = self._read()
        rounds: list[NodeRound] = []
        for name, place in sorted(self._places().items()):
            node = state.setdefault(name, _Node())
            found = self._node(place, node, at, cadence)
            node.last = {**found.document(), "at": now.isoformat()}
            rounds.append(found)
        self._write(state)
        return tuple(rounds)

    def entry(self, on: bool) -> dict[str, object]:
        """Its row on the maintenance list: each node's last round and what it still pins."""
        nodes = [node.last for _, node in sorted(self._read().items()) if node.last is not None]
        return {
            "id": HOME_JOB,
            "kind": "host",
            "name": HOME_NAME,
            "on": on,
            "switch": {"section": "records", "key": "on"},
            "running": [],
            "output": RESULT,
            "nodes": nodes,
        }

    def _node(self, place: Place, node: _Node, at: int, cadence: Cadence) -> NodeRound:
        sent = list(node.confirm)
        after: dict[str, JsonValue] = {"committed_at": node.watermark} if node.watermark else {}
        try:
            value = self._ask(
                place,
                "data.list",
                {"after": after, "confirmed": cast("list[JsonValue]", sent)},
            )
        except _Missed as missed:
            known = node.last or {}
            pinned = known.get("still_pinned")
            return NodeRound(
                place.name,
                reached=False,
                still_pinned=tuple(cast("list[str]", pinned)) if isinstance(pinned, list) else (),
                refusals=({"node": place.name, "reason": str(missed)},),
            )
        listing = cast("Mapping[str, object]", value) if isinstance(value, dict) else {}
        confirmed = 0
        if "unpinned" in listing:
            node.confirm, confirmed = [], len(sent)
        pinned = listing.get("pinned")
        rows = listing.get("partitions")
        tally, refusals = _Tally(), list[Mapping[str, object]]()
        outcomes: list[tuple[str, Outcome]] = []
        for row in cast("list[object]", rows) if isinstance(rows, list) else []:
            table = cast("Mapping[str, object]", row) if isinstance(row, dict) else {}
            listed = Listed.parse(table)
            if listed is None:
                refusals.append({"node": place.name, "reason": f"not a partition: {row!r}"})
                outcomes.append((str(table.get("committed_at", "")), Outcome.FAILED))
                continue
            outcome = self._one(place, listed, node, at, cadence, tally, refusals)
            outcomes.append((listed.committed_at, outcome))
        node.watermark = _advanced(node.watermark, outcomes)
        tail = self._tail(place, refusals) if NODE_APP in place.apps else 0
        return NodeRound(
            place.name,
            reached=True,
            partitions=tally.partitions,
            open_fetched=tally.open_fetched,
            already_home=tally.already_home,
            waiting=tally.waiting,
            bytes=tally.bytes,
            confirmed=confirmed,
            still_pinned=tuple(str(item) for item in cast("list[object]", pinned))
            if isinstance(pinned, list)
            else (),
            oldest_unshipped=tally.oldest,
            tail_rows=tail,
            refusals=tuple(refusals),
        )

    def _one(
        self,
        place: Place,
        listed: Listed,
        node: _Node,
        at: int,
        cadence: Cadence,
        tally: _Tally,
        refusals: list[Mapping[str, object]],
    ) -> Outcome:
        key = listed.key
        held = self._door.series_store().state(key)
        if (
            held is not None
            and held.fingerprint == listed.fingerprint
            and (held.frozen or not listed.frozen)
        ):
            tally.already_home += 1
            if listed.frozen:
                self._confirm(node, listed.fingerprint)
            return Outcome.HOME
        if not listed.frozen:
            last = node.opened.get(key.text)
            every = cadence.pull_every(harvest_class(key.source, key.kind))
            if last is not None and at - last < every:
                tally.waiting += 1
                tally.unshipped(listed)
                return Outcome.WAITING
        brought = self._bring(place, listed)
        if isinstance(brought, str):
            refusals.append({"node": place.name, "key": key.text, "reason": brought})
            tally.unshipped(listed)
            return Outcome.FAILED
        tally.partitions += 1
        tally.bytes += listed.bytes
        if not listed.frozen:
            node.opened[key.text] = at
            tally.open_fetched += 1
            return Outcome.HOME
        node.opened.pop(key.text, None)
        if not brought.frozen:
            reason = "home, but not frozen on This PC yet; it is fetched again next round"
            refusals.append({"node": place.name, "key": key.text, "reason": reason})
            tally.unshipped(listed)
            return Outcome.FAILED
        self._confirm(node, listed.fingerprint)
        return Outcome.HOME

    def _bring(self, place: Place, listed: Listed) -> CommitReceipt | str:
        """Fetch one partition, check its rows have the listed fingerprint, and commit it here
        with `born_on = node`; the receipt, or why it did not land. A month the node froze is
        committed a second time when the first left it open here: the same rows again are the
        one re-fetch the store's freeze rule asks for."""
        key = listed.key
        target = self.staging.joinpath(*key.series.split("/"), f"{listed.month}.parquet")
        fetched = target.with_name(f".{target.name}.fetched")
        written = target.with_name(f".{target.name}.incoming")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            asked: dict[str, JsonValue] = {
                "schema_version": SCHEMA,
                "verb": "data.fetch",
                "args": {"fingerprint": listed.fingerprint},
            }
            try:
                status = self._fetch(f"{place.url}{ROUTE_PATH}", asked, self._pass(place), fetched)
            except Unreachable as error:
                return f"{place.name} did not answer the fetch: {error}"
            if status != 200:
                said = fetched.read_text(encoding="utf-8", errors="replace")[:300]
                return f"{place.name} refused the fetch (HTTP {status}): {said}"
            rule = key.rule
            made = (
                TypedWriter(written, key.text, rule.columns, hole_bounds=rule.hole_bounds)
                .add(rows_of(fetched, rule.columns))
                .finish()
            )
            if made.fingerprint != listed.fingerprint:
                return (
                    f"the fetched rows have fingerprint {made.fingerprint}, not the listed "
                    f"{listed.fingerprint}"
                )
            os.replace(written, target)
            receipt = self._commit(target)
            if not isinstance(receipt, str) and listed.frozen and not receipt.frozen:
                receipt = self._commit(target)
            if not isinstance(receipt, str) and receipt.fingerprint != listed.fingerprint:
                return f"This PC holds {receipt.fingerprint} for it, not {listed.fingerprint}"
            return receipt
        except _Missed as missed:
            return str(missed)
        except (OSError, ValueError, StoreEngineError) as error:
            return f"could not stage the fetched partition: {error}"
        finally:
            for path in (fetched, written, target):
                path.unlink(missing_ok=True)

    def _commit(self, target: Path) -> CommitReceipt | str:
        receipts = self._door.commit([target], staging=self.staging, born_on=Placement.NODE)
        return _reason(receipts) if is_refusal(receipts) else receipts.value[0]

    def _tail(self, place: Place, refusals: list[Mapping[str, object]]) -> int:
        """The node's newest committed journal rows, kept whole in This PC's tail file for that
        node until the next round replaces it; the harvester never reads it."""
        asked: dict[str, JsonValue] = {
            "app": NODE_APP,
            "operation": "journal_tail",
            "arguments": {},
        }
        try:
            value = self._ask(place, "apps.ask", asked)
        except _Missed as missed:
            refusals.append({"node": place.name, "tail": str(missed)})
            return 0
        found = cast("Mapping[str, object]", value) if isinstance(value, dict) else {}
        inner = found.get("value") if found.get("ok") is True else found
        rows = cast("Mapping[str, object]", inner).get("rows") if isinstance(inner, dict) else None
        if not isinstance(rows, list):
            refusals.append({"node": place.name, "tail": "journal_tail answered no rows"})
            return 0
        tail = self._folder / TAIL_FOLDER / f"{key_token(place.name)}.json"
        _write_json(tail, {"node": place.name, "rows": rows})
        return len(cast("list[object]", rows))

    def _confirm(self, node: _Node, printed: str) -> None:
        if printed not in node.confirm:
            node.confirm.append(printed)

    def _pass(self, place: Place) -> dict[str, str]:
        key = self._key()
        if not key:
            raise _Missed("this home holds no pairing key, so it asks no node")
        held = mint_host_pass(
            key, source=self._here, target=place.name, principal=f"host:{self._here}"
        )
        return {PASS_HEADER: held}

    def _ask(self, place: Place, verb: str, args: Mapping[str, JsonValue]) -> JsonValue:
        body: dict[str, JsonValue] = {"schema_version": SCHEMA, "verb": verb, "args": dict(args)}
        try:
            answer = self._post(f"{place.url}{ROUTE_PATH}", body, self._pass(place), CALL_TIMEOUT_S)
        except Unreachable as error:
            raise _Missed(f"{place.name} did not answer: {error}") from error
        found = cast("Mapping[str, JsonValue]", answer) if isinstance(answer, dict) else {}
        if found.get("ok") is not True:
            code, said = found.get("code", "no answer"), found.get("message", "")
            raise _Missed(f"{place.name} refused {verb}: {code}: {said}")
        return found.get("value")

    def _read(self) -> dict[str, _Node]:
        try:
            raw = json.loads((self._folder / PULL_NAME).read_text(encoding="utf-8"))
        except OSError, ValueError:
            return {}
        nodes = raw.get("nodes", {}) if isinstance(raw, dict) else {}
        return {
            str(name): _Node.parse(cast("Mapping[str, object]", value))
            for name, value in cast("dict[str, object]", nodes).items()
            if isinstance(value, dict)
        }

    def _write(self, state: Mapping[str, _Node]) -> None:
        nodes = {name: node.document() for name, node in sorted(state.items())}
        _write_json(self._folder / PULL_NAME, {"nodes": nodes})


# --- the host job -------------------------------------------------------------------------------


class Records:
    """The records host job beside the backup rounds: a harvest round every `open_harvest_s`
    on its own thread, and every `interval_s` the pull round from the nodes, when This PC has
    the remote half, and one `maintenance-result` with the counts since the last one. It lands
    when a round committed, projected or refused something, or asked any node."""

    def __init__(
        self,
        harvester: Harvester,
        settings: Callable[[], Cadence],
        *,
        clock: Callable[[], datetime],
        projection: Projection | None = None,
        store: Store | None = None,
        pull: Pull | None = None,
    ) -> None:
        self.harvester = harvester
        self.settings = settings
        self.clock = clock
        self.projection = projection
        self.store = store
        self.pull = pull
        self._since: list[HarvestRound] = []
        self._reported: datetime | None = None

    def on(self) -> bool:
        return self.settings().on

    def round(self) -> HarvestRound:
        """One harvest round now, its projection, and the result when its interval came."""
        cadence, now = self.settings(), self.clock()
        counts, lines = self.harvester.round(now, cadence)
        if self.projection is not None and lines:
            trades, papers = self.projection.land(lines, now)
            counts = HarvestRound(
                counts.streams,
                counts.partitions,
                counts.skipped_unchanged,
                counts.waiting,
                counts.refusals,
                counts.committed,
                trades,
                papers,
            )
        self._since.append(counts)
        if self._reported is None or (now - self._reported).total_seconds() >= cadence.interval_s:
            nodes = () if self.pull is None else self.pull.round(now, cadence)
            self._report(now, nodes)
        return counts

    def _report(self, now: datetime, nodes: Sequence[NodeRound] = ()) -> None:
        rounds, self._since, self._reported = self._since, [], now
        total = {
            "rounds": len(rounds),
            "streams": sum(r.streams for r in rounds),
            "partitions": sum(r.partitions for r in rounds),
            "skipped_unchanged": sum(r.skipped_unchanged for r in rounds),
            "waiting": rounds[-1].waiting if rounds else 0,
            "refusals": [dict(item) for r in rounds for item in r.refusals],
            "trades": sum(r.trades for r in rounds),
            "paper_runs": sum(r.paper_runs for r in rounds),
        }
        worth = (
            total["partitions"]
            or total["refusals"]
            or total["trades"]
            or total["paper_runs"]
            or nodes
        )
        if self.store is None or not worth:
            return
        refused = total["refusals"] or any(node.refusals for node in nodes)
        line = (
            f"{total['partitions']} partitions filed from {total['streams']} streams, "
            f"{total['trades']} trades projected, {len(cast('list[object]', total['refusals']))} "
            "refusals"
        )
        if nodes:
            skipped = [node.node for node in nodes if not node.reached]
            line += (
                f"; {len(nodes) - len(skipped)} of {len(nodes)} nodes reached, "
                f"{sum(node.partitions for node in nodes)} partitions brought home"
            )
            if skipped:
                line += f", {', '.join(skipped)} skipped"
        landed(
            self.store,
            JOB,
            "refused" if refused else "ok",
            line,
            extra={
                "harvest": total,
                "nodes": [node.document() for node in nodes],
                "at": now.isoformat(),
            },
        )

    async def run(self) -> None:
        """A round every `open_harvest_s` until the host stops; one bad round never ends it."""
        while True:
            cadence = self.settings()
            await asyncio.sleep(cadence.open_s)
            if not cadence.on:
                continue
            try:
                await asyncio.to_thread(self.round)
            except Exception as error:  # one bad round never ends the loop
                print(f"records: a round failed: {type(error).__name__}: {error}", file=sys.stderr)
