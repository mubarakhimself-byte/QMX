"""The MIS on one machine: read its market store, run each market's pack, publish reading records.

The MIS reads and publishes; no unit needs it (Level 0 AD-40, Part C AD-313, `MIS.md`). Its
readings are code it does not own: the bar, session and day readings are QML's statistic blocks,
loaded by entry id through QML's one block loader from the stdlib folder they ship in, and the
quote readings are qmf-readings' labelers, run through C-08's `Readings`. A pack is only a list
of those ids (`packs.json`), so no reading has a second copy here.

A round reads every configured market from the read-only market root the supervisor hands this
app (`QMX_MARKET_ROOT`), skips every month the host facts' `holdout` seals, and appends one
`reading` record per reading whose newest input opens a period its card has not published yet.
Each market has one writer, `mis.<market id>` in the readings journal under this volume's
`data/journal`, which the host's records job harvests home (Part B B15). What was published is
read back from that journal at start, so a restarted MIS publishes nothing twice.

Nothing here reaches an order, a unit, a deployment or money.
"""

# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import json
import os
import re
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Final, Protocol, cast

import pyarrow.parquet as pq
from qmf.core import (
    ExactRational,
    Fingerprint,
    Instant,
    Instrument,
    Price,
    PriceDelta,
    TypedRefusal,
    UnitKind,
    VenueId,
    is_refusal,
)
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qmf.data.journal_writer import JournalWriter, WriterScope
from qmf.data.series import BAR_KIND, OPEN_NAME, TICKS_KIND, SeriesKey, SeriesStore
from qmf.readings import configure_mis_producer
from qmf.readings.record import (
    READING_KIND,
    Health,
    ReadingRecord,
    ReadingRef,
    ReadingSource,
    Tier,
    TimeBase,
)
from qmf.readings.runner import Quote, ReadingBinding, Readings, outputs_of
from qml.blocks.api import Block, Signal
from qml.catalogue.loader import LockEntry, load

type Json = dict[str, object]

VERSION: Final = "1.0.0"
APP_FOLDER: Final = Path(__file__).resolve().parent
PACKS: Final = APP_FOLDER / "packs.json"
STDLIB: Final[Traversable] = files("qml.blocks") / "stdlib"
ENTRY_ID: Final = re.compile(r"[a-z0-9][a-z0-9-]*")
HOST_FACTS: Final = "road/host/facts.json"
"""Where the host writes its facts in this volume (AD-307); the app cannot write under `road/`."""
NS: Final = 1_000_000_000
MS: Final = 1_000_000
MINUTE_MS: Final = 60_000
BAR_VARIANTS: Final = ("mid", "bid", "")
"""The `bar-m1` side a bar reading reads, the first one the store holds: mid, else bid."""
OPERATIONS: Final = ("configure", "status", "round", "board")
READS: Final = frozenset({"status", "board"})
SETTINGS: Final[Mapping[str, int]] = {
    "round_s": 60,
    "bar_period_s": 3_600,
    "history_months": 4,
}
"""`[mis]` settings with their starting defaults, set through `configure`: seconds between
rounds; the bar the statistic blocks read, one H1 bar as A13b's cards' bar tier says
(`stale_after_s` 3,600); and how many unsealed months back a round reads, enough for Hurst's
1,000 H1 bars on a 24x5 market."""
UNIT_KINDS: Final[Mapping[str, UnitKind]] = {"ratio": UnitKind.DIMENSIONLESS_RATIO}
"""The record's exact value per output measure. A block whose value is a price has no
instrument-free exact kind, so no pack may name it until the record carries one."""


class Refused(Exception):
    """A bad argument or a configuration no market can run, answered as `bad_argument`."""


@dataclass(frozen=True, slots=True)
class Card:
    """What every record of one reading says about it: the reading card's labels."""

    id: str
    version: str
    fingerprint: Fingerprint
    tier: Tier
    time_base: TimeBase
    data_level: int
    stale_after_s: int
    valid_classes: frozenset[str]

    @property
    def pin(self) -> str:
        return f"{self.id}@{self.version}"


@dataclass(frozen=True, slots=True)
class Outcome:
    """A reading at its newest input: when that input was known, and what it read."""

    at_ns: int
    value: ExactRational | None
    word: str | None
    health: Health


@dataclass(frozen=True, slots=True)
class Market:
    """One configured market as its instrument snapshot describes it.

    `source` names the store folder its bars live under, which is the source that downloaded
    them and never the venue that lists them. None means the store holds no bars for this market:
    it stays configured, publishes nothing, and `status` says which market it is."""

    market_id: str
    venue: str
    symbol: str
    source: str | None
    instrument_class: str
    digits: int
    pip: Decimal | None
    levels: frozenset[int]


@dataclass(frozen=True, slots=True)
class Seal:
    """The host facts' `holdout`: every month from `boundary` on is sealed. On with no boundary,
    or facts that cannot be read, seals every month, so a doubt never leaks a held-out month."""

    on: bool
    boundary: tuple[int, int] | None

    def seals(self, year: int, month: int) -> bool:
        return self.on and (self.boundary is None or (year, month) >= self.boundary)

    def fact(self) -> Json:
        if not self.on:
            return {"on": False}
        if self.boundary is None:
            return {"on": True, "seals": "every month"}
        return {"on": True, "boundary": f"{self.boundary[0]:04d}-{self.boundary[1]:02d}"}


@dataclass(frozen=True, slots=True)
class Facts:
    machine: str
    seal: Seal


def read_facts(volume: Path) -> Facts:
    """The host facts in this volume. Absent or unreadable, every month is sealed."""
    path = volume / HOST_FACTS
    try:
        raw = cast(object, json.loads(path.read_text("utf-8")))
    except OSError, ValueError:
        return Facts("unplaced", Seal(on=True, boundary=None))
    facts = cast(Json, raw) if isinstance(raw, dict) else {}
    placement = facts.get("placement")
    machine = placement if isinstance(placement, str) and placement else "unplaced"
    holdout = facts.get("holdout")
    if not isinstance(holdout, dict):
        return Facts(machine, Seal(on=True, boundary=None))
    seal = cast(Json, holdout)
    if seal.get("on") is False:
        return Facts(machine, Seal(on=False, boundary=None))
    return Facts(machine, Seal(on=True, boundary=_month(seal.get("boundary"))))


def _month(value: object) -> tuple[int, int] | None:
    if not isinstance(value, str):
        return None
    try:
        moment = datetime.strptime(value, "%Y-%m")
    except ValueError:
        return None
    return moment.year, moment.month


class Reading(Protocol):
    @property
    def card(self) -> Card: ...

    def latest(self, data: MarketData) -> Outcome | None:
        """The reading at the market's newest input, or None when the market has no input."""
        ...


@dataclass(frozen=True, slots=True)
class Words:
    """The card's state output: ordered cuts on the value, or an event's two words."""

    cuts: tuple[tuple[str, Decimal | None], ...] = ()
    holds: str | None = None
    clear: str | None = None

    def of(self, output: object) -> tuple[Decimal | None, str | None]:
        if isinstance(output, Signal):
            return output.value, self.holds if output.state else self.clear
        if not isinstance(output, Decimal):
            return None, None
        for word, below in self.cuts:
            if below is None or output < below:
                return output, word
        return output, None


@dataclass(frozen=True, slots=True)
class BlockReading:
    """A QML reading block over the market's closed bars, from the card's default parameters."""

    card: Card
    block: Block
    parameters: Mapping[str, Decimal]
    words: Words
    unit_kind: UnitKind

    def latest(self, data: MarketData) -> Outcome | None:
        closes = data.closes()
        if not closes:
            return None
        instance = self.block.make(self.parameters, {})
        output: object = None
        for _, price in closes:
            output = instance.update({"series": price})
        value, word = self.words.of(output)
        at = closes[-1][0]
        if value is None:
            return Outcome(at, None, None, Health.THIN)
        exact = _exact(value, self.unit_kind)
        return Outcome(at, exact, word, Health.FRESH)


@dataclass(frozen=True, slots=True)
class LabelerReading:
    """A qmf-readings labeler on the market's newest quote, through C-08's `Readings`."""

    card: Card
    binding: ReadingBinding

    def latest(self, data: MarketData) -> Outcome | None:
        found = data.last_quote()
        if found is None:
            return None
        quote, pip = found
        readings = Readings(
            (self.binding,), instrument=quote.bid.instrument, environment="live", pip=pip
        )
        emitted = readings.step(quote)
        if is_refusal(emitted):
            return Outcome(quote.at.value_ns, None, None, Health.DEGRADED)
        said = outputs_of(self.binding, emitted.value[0])
        return Outcome(quote.at.value_ns, said.value, said.word, said.health)


def _exact(value: Decimal, kind: UnitKind) -> ExactRational | None:
    ratio = Fraction(value)
    made = ExactRational.try_create(ratio.numerator, ratio.denominator, kind)
    return None if is_refusal(made) else made.value


def _decimal(value: object, where: str) -> Decimal:
    try:
        return Decimal(str(value))
    except InvalidOperation:
        raise Refused(f"{where} is a decimal") from None


def _block_reading(pin: str) -> BlockReading:
    entry_id, _, version = pin.partition("@")
    if not (ENTRY_ID.fullmatch(entry_id) and version.isdigit()):
        raise Refused(f"no reading {pin}")
    folder = STDLIB / entry_id / version
    face_file, source_file = folder / "entry.json", folder / "block.py"
    if not (face_file.is_file() and source_file.is_file()):
        raise Refused(f"no reading {pin}")
    face = cast(Json, json.loads(face_file.read_bytes()))
    card = cast(Json | None, face.get("reading"))
    if card is None:
        raise Refused(f"{pin} has no reading card")
    lock = LockEntry(entry_id, int(version), str(face["fingerprint"]))
    loaded = load((lock,), {pin: source_file.read_bytes()})
    if isinstance(loaded, tuple):
        raise Refused(f"{pin} does not load: {loaded[0].message}")
    outputs = cast(Json, card["outputs"])
    measure = str(cast(Json, outputs["value"])["measure"])
    if measure not in UNIT_KINDS:
        raise Refused(f"{pin} reads a {measure}, which a reading record cannot carry yet")
    state = cast(Json, outputs.get("state") or {})
    state = cast(Json, state.get("signal", state))
    words = Words(
        cuts=tuple(
            (str(cut["word"]), None if "below" not in cut else _decimal(cut["below"], pin))
            for cut in cast(list[Json], state.get("cuts", []))
        ),
        holds=cast(str | None, state.get("holds")),
        clear=cast(str | None, state.get("clear")),
    )
    parameters = {
        name: _decimal(cast(Json, spec)["default"], f"{pin} {name}")
        for name, spec in cast(Json, face.get("parameters") or {}).items()
    }
    return BlockReading(
        Card(
            entry_id,
            version,
            _fingerprint(str(face["fingerprint"])),
            Tier(str(card["tier"])),
            TimeBase(str(card["time_base"])),
            int(cast(int, card["data_level"])),
            int(cast(int, card["stale_after_s"])),
            frozenset(cast(list[str], card["valid_classes"])),
        ),
        loaded.blocks[pin],
        parameters,
        words,
        UNIT_KINDS[measure],
    )


def _fingerprint(value: str) -> Fingerprint:
    made = Fingerprint.try_create(value)
    if is_refusal(made):
        raise Refused(f"fingerprint {value} does not parse")
    return made.value


def _labeler_reading(pin: str, spec: Json, parameters: Json) -> LabelerReading:
    producer_id, _ = pin.split("@")
    made = configure_mis_producer(
        producer_id,
        parameters={name: _count(value, f"{pin} {name}") for name, value in parameters.items()},
        warm_up=int(cast(int, spec.get("warm_up", 0))),
    )
    if is_refusal(made):
        raise Refused(f"{pin} does not configure: {said(made)}")
    producer = made.value
    printed = producer.fingerprint()
    if is_refusal(printed):
        raise Refused(f"{pin} has no fingerprint: {said(printed)}")
    if f"{producer.producer_id}@{producer.version}" != pin:
        raise Refused(f"{pin} names {producer.producer_id}@{producer.version}")
    tier, time_base = Tier(str(spec["tier"])), TimeBase(str(spec["time_base"]))
    level, stale = int(cast(int, spec["data_level"])), int(cast(int, spec["stale_after_s"]))
    return LabelerReading(
        Card(
            producer.producer_id,
            producer.version,
            printed.value,
            tier,
            time_base,
            level,
            stale,
            frozenset(cast(list[str], spec["valid_classes"])),
        ),
        ReadingBinding(producer, tier, time_base, data_level=level, stale_after_s=stale),
    )


def _count(value: object, where: str) -> ExactRational:
    ratio = Fraction(_decimal(value, where))
    made = ExactRational.try_create(ratio.numerator, ratio.denominator, UnitKind.COUNT)
    if is_refusal(made):
        raise Refused(f"{where} is an exact count")
    return made.value


@dataclass(frozen=True, slots=True)
class PackRow:
    reading: Reading
    shadow: bool = False


@dataclass(frozen=True, slots=True)
class Catalogue:
    """The shipped packs and every reading they or a shadow request name, loaded once."""

    packs: Mapping[str, tuple[str, tuple[Reading, ...]]]
    labelers: Mapping[str, Json]
    _built: dict[str, Reading] = field(default_factory=dict[str, Reading])

    @classmethod
    def shipped(cls, path: Path = PACKS) -> Catalogue:
        document = cast(Json, json.loads(path.read_text("utf-8")))
        labelers = cast(Mapping[str, Json], document["labelers"])
        catalogue = cls({}, labelers)
        packs: dict[str, tuple[str, tuple[Reading, ...]]] = {}
        for name, pack in cast(Mapping[str, Json], document["packs"]).items():
            rows = cast(list[Json], pack["readings"])
            packs[name] = (
                str(pack["class"]),
                tuple(
                    catalogue.reading(str(row["pin"]), cast(Json, row.get("parameters") or {}))
                    for row in rows
                ),
            )
        return cls(packs, labelers, catalogue._built)

    def reading(self, pin: str, parameters: Json | None = None) -> Reading:
        """The reading one pin names: a labeler this catalogue declares, else a QML block."""
        key = pin if not parameters else f"{pin}{json.dumps(parameters, sort_keys=True)}"
        if key not in self._built:
            if pin in self.labelers:
                self._built[key] = _labeler_reading(pin, self.labelers[pin], parameters or {})
            else:
                self._built[key] = _block_reading(pin)
        return self._built[key]


class MarketData:
    """One market's unsealed history in the store, read once per round."""

    def __init__(
        self, store: SeriesStore | None, market: Market, seal: Seal, settings: Mapping[str, int]
    ) -> None:
        self._store = store
        self._market = market
        self._seal = seal
        self._period_ms = settings["bar_period_s"] * 1_000
        self._months = settings["history_months"]
        self._closes: list[tuple[int, Decimal]] | None = None
        self.sealed: set[str] = set()

    def _keys(self, kind: str, variant: str) -> list[SeriesKey]:
        store = self._store
        source = self._market.source
        if store is None or source is None:
            return []
        market = self._market
        folder = store.root / source / market.symbol / kind / (variant or "-")
        keys: list[SeriesKey] = []
        for state in sorted(folder.glob("*/state.json")) if folder.is_dir() else ():
            month = _month(state.parent.name)
            if month is None:
                continue
            if self._seal.seals(*month):
                self.sealed.add(state.parent.name)
                continue
            made = SeriesKey.try_create(market.source, market.symbol, kind, *month, variant)
            if not is_refusal(made):
                keys.append(made.value)
        return keys

    def _path(self, key: SeriesKey) -> Path | None:
        store = self._store
        state = None if store is None else store.state(key)
        if store is None or state is None:
            return None
        folder = store.folder(key)
        return folder / (f"{state.fingerprint}.parquet" if state.frozen else OPEN_NAME)

    def closes(self) -> list[tuple[int, Decimal]]:
        """Each closed bar's close, with the time of its newest minute, oldest first."""
        if self._closes is not None:
            return self._closes
        keys: list[SeriesKey] = []
        for variant in BAR_VARIANTS:
            keys = self._keys(BAR_KIND, variant)
            if keys:
                break
        times: list[int] = []
        prices: list[int] = []
        for key in keys[-self._months :]:
            path = self._path(key)
            if path is None:
                continue
            table = pq.read_table(path, columns=["t", "close"])
            times.extend(cast(list[int], table.column("t").to_pylist()))
            prices.extend(cast(list[int], table.column("close").to_pylist()))
        self._closes = self._bars(times, prices)
        return self._closes

    def _bars(self, times: Sequence[int], prices: Sequence[int]) -> list[tuple[int, Decimal]]:
        period = self._period_ms
        bars: list[tuple[int, int, int]] = []
        for t, price in zip(times, prices, strict=True):
            bucket = t // period
            if bars and bars[-1][0] == bucket:
                bars[-1] = (bucket, t, price)
            else:
                bars.append((bucket, t, price))
        if bars and bars[-1][1] < (bars[-1][0] + 1) * period - MINUTE_MS:
            bars.pop()
        digits = self._market.digits
        return [(t * MS, Decimal(price).scaleb(-digits)) for _, t, price in bars]

    def last_quote(self) -> tuple[Quote, PriceDelta] | None:
        """The newest quote in the newest unsealed month of ticks, and the market's pip."""
        market = self._market
        keys = self._keys(TICKS_KIND, "")
        path = None if not keys else self._path(keys[-1])
        if path is None or market.pip is None:
            return None
        table = pq.read_table(path, columns=["t", "bid", "ask"])
        if table.num_rows == 0:
            return None
        last = table.num_rows - 1
        t, bid, ask = (
            int(cast(int, table.column(name)[last].as_py())) for name in ("t", "bid", "ask")
        )
        venue = VenueId.try_create(market.venue)
        if is_refusal(venue):
            return None
        instrument = Instrument.try_create(venue.value, market.symbol)
        if is_refusal(instrument):
            return None
        scale = market.digits
        made = (
            Instant.try_create(t * MS),
            Price.try_create(bid, instrument.value, scale),
            Price.try_create(ask, instrument.value, scale),
            PriceDelta.try_create(int(market.pip.scaleb(scale)), instrument.value, scale),
        )
        at, bid_price, ask_price, pip = made
        if is_refusal(at) or is_refusal(bid_price) or is_refusal(ask_price) or is_refusal(pip):
            return None
        return Quote(at.value, bid_price.value, ask_price.value), pip.value


def said(refusal: TypedRefusal) -> str:
    return f"{refusal.category.value} {dict(refusal.context)}"


def _only(arguments: Json, allowed: set[str], where: str) -> None:
    unknown = sorted(set(arguments) - allowed)
    if unknown:
        raise Refused(f"{where}: unknown argument {unknown[0]}")


def _market(entry: object, index: int) -> Market:
    where = f"configure: markets[{index}]"
    if not isinstance(entry, dict):
        raise Refused(f"{where} is an object")
    market = cast(Json, entry)
    _only(market, {"market_id", "instrument", "source"}, where)
    snapshot = market.get("instrument")
    if not isinstance(snapshot, dict):
        raise Refused(f"{where}.instrument is the instrument record's snapshot")
    record = cast(Json, snapshot)
    market_id = market.get("market_id", record.get("market_id"))
    texts = {name: record.get(name) for name in ("venue", "symbol", "class")}
    if not isinstance(market_id, str) or not market_id:
        raise Refused(f"{where}.market_id is a text")
    for name, value in texts.items():
        if not isinstance(value, str) or not value:
            raise Refused(f"{where}.instrument.{name} is a text")
    digits = record.get("digits")
    if not isinstance(digits, int) or isinstance(digits, bool) or digits < 0:
        raise Refused(f"{where}.instrument.digits is a whole number")
    levels = cast(Json, record.get("data_levels") or {}).get("levels")
    if not isinstance(levels, list) or not all(
        isinstance(level, int) for level in cast(list[object], levels)
    ):
        raise Refused(f"{where}.instrument.data_levels.levels is a list of levels")
    pip = cast(Json, record.get("pip") or {}).get("size")
    source = market.get("source")
    if source is not None and (not isinstance(source, str) or not source):
        raise Refused(f"{where}.source is the source that holds its bars, or left out")
    return Market(
        market_id=market_id,
        venue=str(texts["venue"]),
        symbol=str(texts["symbol"]),
        source=source,
        instrument_class=str(texts["class"]),
        digits=digits,
        pip=None if pip is None else _decimal(pip, f"{where}.instrument.pip.size"),
        levels=frozenset(cast(list[int], levels)),
    )


def _pins(value: object, where: str) -> list[str]:
    if not isinstance(value, list):
        raise Refused(f"configure: {where} is a list of {{id, version}}")
    pins: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, dict) or set(cast(Json, item)) != {"id", "version"}:
            raise Refused(f"configure: {where} is a list of {{id, version}}")
        row = cast(Json, item)
        pins.append(f"{row['id']}@{row['version']}")
    return pins


@dataclass(frozen=True, slots=True)
class Plan:
    """One configuration: each market with the readings its pack and data levels allow."""

    op_id: str | None
    markets: tuple[tuple[Market, tuple[PackRow, ...]], ...]
    refused: tuple[Json, ...]
    settings: Mapping[str, int]
    asked: Json

    def answer(self) -> Json:
        return {"configured": len(self.markets), "refused": list(self.refused)}


def plan(catalogue: Catalogue, arguments: Json) -> Plan:
    """Parse `configure`'s arguments into a plan, or refuse them whole."""
    _only(arguments, {"op_id", "markets", "packs", "shadow", "settings"}, "configure")
    op_id = arguments.get("op_id")
    if op_id is not None and not isinstance(op_id, str):
        raise Refused("configure: op_id is a text")
    entries = arguments.get("markets")
    if not isinstance(entries, list):
        raise Refused("configure: markets is a list of objects")
    markets = [_market(entry, index) for index, entry in enumerate(cast(list[object], entries))]
    asked = _pins(arguments.get("packs", []), "packs") or list(catalogue.packs)
    for name in asked:
        if name.replace("@", "-") not in catalogue.packs:
            raise Refused(f"configure: no pack {name}")
    packs = [catalogue.packs[name.replace("@", "-")] for name in asked]
    shadow = [catalogue.reading(pin) for pin in _pins(arguments.get("shadow", []), "shadow")]
    settings = dict(SETTINGS)
    given = arguments.get("settings", {})
    if not isinstance(given, dict):
        raise Refused("configure: settings is an object")
    for name, value in cast(Json, given).items():
        if name not in SETTINGS:
            raise Refused(f"configure: no setting {name}")
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise Refused(f"configure: settings.{name} is a whole number above 0")
        settings[name] = value
    planned: list[tuple[Market, tuple[PackRow, ...]]] = []
    refused: list[Json] = []
    for market in markets:
        readings = [rows for kind, rows in packs if kind == market.instrument_class]
        if not readings:
            refused.append(
                {"market_id": market.market_id, "reason": f"no pack for {market.instrument_class}"}
            )
            continue
        rows = [PackRow(reading) for reading in readings[0]]
        rows.extend(PackRow(reading, shadow=True) for reading in shadow)
        planned.append((market, tuple(row for row in rows if _allows(market, row.reading.card))))
    return Plan(op_id, tuple(planned), tuple(refused), settings, arguments)


def _allows(market: Market, card: Card) -> bool:
    """A market gets a reading only when it offers the reading's data level, for its class."""
    return card.data_level in market.levels and market.instrument_class in card.valid_classes


class Mis:
    """The MIS of one app volume: its plan, its writers and what it has published.

    Every operation answers and none raises on a bad argument, so a mistyped call never
    counts toward the supervisor's breaker."""

    def __init__(
        self,
        volume: Path,
        market_root: Path | None,
        *,
        clock: Callable[[], int],
        boot: str,
        catalogue: Catalogue | None = None,
    ) -> None:
        self.volume = volume
        self.data = volume / "data"
        self._store = None if market_root is None else SeriesStore(market_root / "series")
        self._catalogue = catalogue if catalogue is not None else Catalogue.shipped()
        self._clock = clock
        self._boot = boot
        self._writers: dict[tuple[str, str], JournalWriter] = {}
        self._published = self._read_published()
        self._last_round: Json | None = None
        self._last_error: str | None = None
        self._lock = threading.Lock()
        self.plan = self._saved_plan()

    @property
    def journal(self) -> Path:
        return self.data / "journal"

    @property
    def configuration(self) -> Path:
        return self.data / "mis" / "configuration.json"

    @property
    def board_file(self) -> Path:
        return self.data / "board.json"

    def call(self, operation: str, arguments: object) -> Json:
        if not isinstance(arguments, dict):
            return _bad(f"{operation}: arguments are an object")
        given = cast(Json, arguments)
        with self._lock:
            try:
                match operation:
                    case "configure":
                        return _ok(self._configure(given))
                    case "status":
                        _only(given, set(), "status")
                        return _ok(self._status())
                    case "round":
                        _only(given, set(), "round")
                        return _ok(self._round())
                    case "board":
                        _only(given, set(), "board")
                        return _ok(self._board(self._clock()))
                    case _:
                        return _bad(f"no operation {operation}")
            except Refused as refused:
                return _bad(str(refused))

    def close(self) -> None:
        with self._lock:
            for writer in self._writers.values():
                writer.close()
            self._writers.clear()

    def round_failed(self, error: BaseException) -> None:
        """Record why a round raised, for `status`; the round thread carries on and the next
        round reads again. A later success leaves the last error in place, because the market or
        month it names is still the reason a reading is missing."""
        with self._lock:
            self._last_error = f"{type(error).__name__}: {error}"

    def _configure(self, arguments: Json) -> Json:
        current = self.plan
        op_id = arguments.get("op_id")
        if current is not None and op_id is not None and current.op_id == op_id:
            if current.asked != arguments:
                raise Refused(f"configure: op_id {op_id} already configured something else")
            return current.answer()
        made = plan(self._catalogue, arguments)
        _write(self.configuration, made.asked)
        self.plan = made
        return made.answer()

    def _saved_plan(self) -> Plan | None:
        try:
            saved = cast(Json, json.loads(self.configuration.read_text("utf-8")))
        except OSError, ValueError:
            return None
        try:
            return plan(self._catalogue, saved)
        except Refused:
            return None

    def _read_published(self) -> dict[tuple[str, str], Json]:
        newest: dict[tuple[str, str], Json] = {}
        for folder in stream_folders(self.journal):
            lines = read_committed(folder)
            if is_refusal(lines):
                continue
            for line in lines.value:
                if not isinstance(line, JournalLine) or line.record.get("kind") != READING_KIND:
                    continue
                body = cast(Json, line.record["body"])
                reading = cast(Json, body["reading"])
                key = (str(body["market_id"]), f"{reading['id']}@{reading['version']}")
                before = newest.get(key)
                at = cast(int, body["inputs_received_at"])
                if before is None or cast(int, before["inputs_received_at"]) <= at:
                    newest[key] = body
        return newest

    def _writer(self, market: Market, machine: str) -> JournalWriter:
        key = (market.market_id, machine)
        if key not in self._writers:
            scope = WriterScope(
                stream=JournalStream.READINGS,
                subject=f"{ReadingSource.MIS.value}.{market.market_id}",
                world=JournalWorld.LIVE,
                machine=machine,
                role="mis",
                build=f"mis-app@{VERSION}",
            )
            opened = JournalWriter.open(
                self.journal, scope, clock=self._clock, boot_epoch_id=self._boot
            )
            if is_refusal(opened):
                raise Refused(f"round: the readings journal does not open: {said(opened)}")
            self._writers[key] = opened.value
        return self._writers[key]

    def _round(self) -> Json:
        current = self.plan
        if current is None:
            raise Refused("round: configure the MIS first")
        started = self._clock()
        facts = read_facts(self.volume)
        published: list[Json] = []
        sealed: set[str] = set()
        for market, rows in current.markets:
            data = MarketData(self._store, market, facts.seal, current.settings)
            for row in rows:
                record = self._publish(market, row, data, facts.machine)
                if record is not None:
                    published.append({"market_id": market.market_id, "reading": record})
            sealed |= data.sealed
        board = self._board(self._clock())
        _write(self.board_file, board)
        self._last_round = {
            "published": published,
            "sealed_months": sorted(sealed),
            "took_ms": (self._clock() - started) // MS,
        }
        return self._last_round

    def _publish(self, market: Market, row: PackRow, data: MarketData, machine: str) -> str | None:
        outcome = row.reading.latest(data)
        if outcome is None:
            return None
        card = row.reading.card
        key = (market.market_id, card.pin)
        period = card.stale_after_s * NS
        before = self._published.get(key)
        if before is not None and cast(int, before["inputs_received_at"]) // period >= (
            outcome.at_ns // period
        ):
            return None
        body = ReadingRecord(
            reading=ReadingRef(card.id, card.version, card.fingerprint),
            source=ReadingSource.MIS,
            machine=machine,
            market_id=market.market_id,
            instrument=market.symbol,
            tier=card.tier,
            time_base=card.time_base,
            health=Health.SHADOW if row.shadow else outcome.health,
            data_level=card.data_level,
            fallback_step=0,
            inputs_received_at=outcome.at_ns,
            computed_at=self._clock(),
            stale_after_s=card.stale_after_s,
            value=outcome.value,
            word=outcome.word,
        ).body()
        appended = self._writer(market, machine).append(
            READING_KIND,
            body,
            # No clock fact reaches an app volume yet (C-01), so this machine's offset is unproven.
            RowFacts(ts_recv=outcome.at_ns, clock_ok=False, market_id=market.market_id),
        )
        if is_refusal(appended):
            raise Refused(
                f"round: {card.pin} on {market.market_id} was not written: {said(appended)}"
            )
        self._published[key] = body
        return card.pin

    def _status(self) -> Json:
        facts = read_facts(self.volume)
        current = self.plan
        markets: list[Json] = []
        for market, rows in () if current is None else current.markets:
            bodies = [self._published.get((market.market_id, row.reading.card.pin)) for row in rows]
            found = [body for body in bodies if body is not None]
            markets.append(
                {
                    "market_id": market.market_id,
                    "source": market.source,
                    "readings": {
                        str(row.reading.card.pin): None if body is None else body["health"]
                        for row, body in zip(rows, bodies, strict=True)
                    },
                    "last_computed_at": max(
                        (cast(int, body["computed_at"]) for body in found), default=None
                    ),
                }
            )
        return {
            "state": "not configured" if current is None else "configured",
            "machine": facts.machine,
            "holdout": facts.seal.fact(),
            "markets": markets,
            "last_round": self._last_round,
            "last_error": self._last_error,
        }

    def _board(self, now: int) -> Json:
        """One board per tier: each market's live reading words and their freshness."""
        tiers: dict[str, list[Json]] = {}
        for market, rows in () if self.plan is None else self.plan.markets:
            per_tier: dict[str, tuple[Json, Json]] = {}
            for row in rows:
                body = self._published.get((market.market_id, row.reading.card.pin))
                if body is None or row.shadow:
                    continue
                states, freshness = per_tier.setdefault(str(body["tier"]), ({}, {}))
                reading = str(cast(Json, body["reading"])["id"])
                if "word" in body:
                    states[reading] = body["word"]
                freshness[reading] = _freshness(body, now)
            for tier, (states, freshness) in per_tier.items():
                tiers.setdefault(tier, []).append(
                    {"market_id": market.market_id, "states": states, "freshness": freshness}
                )
        return {
            "boards": [
                {"tier": tier.value, "at": now, "markets": tiers[tier.value]}
                for tier in Tier
                if tier.value in tiers
            ]
        }


def _freshness(body: Json, now: int) -> str:
    health = str(body["health"])
    if health != Health.FRESH.value:
        return health
    age = now - cast(int, body["inputs_received_at"])
    return "fresh" if age <= cast(int, body["stale_after_s"]) * NS else "stale"


def _write(path: Path, document: Json) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(document, sort_keys=True), "utf-8")
    os.replace(temporary, path)


def _ok(value: Json) -> Json:
    return {"ok": True, "value": value}


def _bad(message: str) -> Json:
    return {"ok": False, "code": "bad_argument", "message": message}
