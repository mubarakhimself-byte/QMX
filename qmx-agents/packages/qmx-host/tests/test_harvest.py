"""The host is the one harvester of every app's append streams on its machine (Part B B15).

A fixture app volume holds a unit journal, a market journal with its bars and ticks, and reading
history, written by the real writer library. Rounds of the real harvester file them through the
real market-data door; the store, the Library and the stream files are read back.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from qmf.core import fingerprint_bytes, is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_writer import JournalWriter, WriterScope
from qmf.data.series import SeriesKey, SeriesStore
from qmx_engine.ledger import redact
from qmx_library.principal import MAIN, Principal
from qmx_library.store import Store

from qmx_host.market_data import MarketDoor
from qmx_host.records import Cadence, Harvester, Projection, Records, append_roots

_REAL = datetime.now(UTC)  # ambient-scan: allow (the store freezes by the real month)
OPEN_MONTH = datetime(_REAL.year, _REAL.month, 1, tzinfo=UTC)
CLOSED_MONTH = (OPEN_MONTH - timedelta(days=40)).replace(day=1)
NOW = OPEN_MONTH + timedelta(days=10)
MACHINE = "this-pc"
OPERATOR = Principal("operator")


@dataclass
class Clock:
    ns: int

    def __call__(self) -> int:
        return self.ns

    def at(self, moment: datetime) -> None:
        self.ns = int(moment.timestamp()) * 1_000_000_000


def ms(moment: datetime) -> int:
    return int(moment.timestamp()) * 1_000


@dataclass
class Volume:
    home: Path
    unit: JournalWriter
    market: JournalWriter
    readings: JournalWriter
    clock: Clock
    bars: int = 0
    ticks: int = 0

    @property
    def store(self) -> SeriesStore:
        return SeriesStore(self.home / "market" / "series")

    def signal(self, at: datetime, row_id: str, *, backfilled: bool = False) -> None:
        self.clock.at(at)
        body: dict[str, object] = {
            "row_id": row_id,
            "instant": int(at.timestamp()) * 1_000_000_000,
            "market_id": "fx.eurusd",
            "outcome": "skipped",
            "reason": "spread_wide",
        }
        facts = RowFacts(
            ts_recv=self.clock.ns,
            clock_ok=True,
            unit_id="dummy",
            market_id="fx.eurusd",
            backfilled=backfilled,
        )
        assert not is_refusal(self.unit.append("signal", body, facts))

    def trade(self, trade_id: str, opened: datetime, closed: datetime, **extra: str) -> None:
        self.clock.at(closed)
        body = {
            "closing_deal_id": f"{trade_id}.close",
            "trade_id": trade_id,
            "side": "long",
            "opened_at": int(opened.timestamp()) * 1_000_000_000,
            "closed_at": self.clock.ns,
            "entry_price": "1.08000",
            "exit_price": "1.08300",
            "quantity": "0.10",
            **extra,
        }
        facts = RowFacts(
            ts_recv=self.clock.ns,
            clock_ok=True,
            unit_id="dummy",
            unit_version="v1",
            market_id="fx.eurusd",
            venue="conformance",
            account="demo-1",
        )
        assert not is_refusal(self.unit.append("trade", body, facts))

    def add_bars(self, count: int) -> None:
        for _ in range(count):
            t = ms(OPEN_MONTH) + self.bars * 60_000
            row = [t, 108_000, 108_010, 107_990, 108_005, 12.5]
            assert not is_refusal(self.market.append_series("dukascopy", "EURUSD", "bar-m1", row))
            self.bars += 1

    def add_ticks(self, count: int) -> None:
        for _ in range(count):
            t = ms(OPEN_MONTH) + self.ticks * 1_000
            row = [t, 108_000, 108_002, 1.0, 1.0]
            assert not is_refusal(self.market.append_series("dukascopy", "EURUSD", "ticks", row))
            self.ticks += 1

    def stream_bytes(self) -> dict[str, str]:
        return {
            path.relative_to(self.home).as_posix(): fingerprint_bytes(path.read_bytes()).value
            for path in sorted((self.home / "apps").rglob("*"))
            if path.is_file()
        }


def writer(root: Path, stream: JournalStream, subject: str, clock: Clock) -> JournalWriter:
    scope = WriterScope(stream, subject, JournalWorld.PAPER, MACHINE, "node", "test-build")
    opened = JournalWriter.open(root, scope, clock=clock, boot_epoch_id="boot1")
    assert not is_refusal(opened)
    return opened.value


@pytest.fixture
def volume(tmp_path: Path) -> Iterator[Volume]:
    home = tmp_path / "QMX"
    root = home / "apps" / "practice-node" / "data" / "journal"
    clock = Clock(0)
    clock.at(CLOSED_MONTH)
    made = Volume(
        home,
        writer(root, JournalStream.UNIT, "dummy", clock),
        writer(root, JournalStream.MARKET, "fx.eurusd", clock),
        writer(root, JournalStream.READINGS, "node.fx.eurusd", clock),
        clock,
    )
    yield made
    for journal in (made.unit, made.market, made.readings):
        journal.close()


def harvester(home: Path) -> Harvester:
    door = MarketDoor(root=home / "market")
    return Harvester(lambda: append_roots(home), door, home / "records", journals_open=True)


def key(series: str, moment: datetime) -> SeriesKey:
    source, subject, kind, variant = series.split("/")
    made = SeriesKey.try_create(source, subject, kind, moment.year, moment.month, variant)
    assert not is_refusal(made)
    return made.value


BARS = "dukascopy/EURUSD/bar-m1/-"
TICKS = "dukascopy/EURUSD/ticks/-"
SIGNALS = f"journal-unit/dummy/signal/paper.{MACHINE}"


def test_a_closed_month_files_once_and_the_open_month_of_bars_grows_in_one_file(
    volume: Volume,
) -> None:
    for n in range(3):
        volume.signal(CLOSED_MONTH + timedelta(days=2, minutes=n), f"closed-{n}")
    volume.clock.at(OPEN_MONTH)
    volume.add_bars(60)
    volume.signal(OPEN_MONTH + timedelta(hours=8), "open-0")
    harvest = harvester(volume.home)

    first, _ = harvest.round(NOW, Cadence())
    after_first = volume.store.state(key(BARS, OPEN_MONTH))
    volume.add_bars(60)
    second, _ = harvest.round(NOW + timedelta(seconds=60), Cadence())
    bars = volume.store.state(key(BARS, OPEN_MONTH))
    closed = volume.store.state(key(SIGNALS, CLOSED_MONTH))
    opened = volume.store.state(key(SIGNALS, OPEN_MONTH))
    folder = volume.store.folder(key(BARS, OPEN_MONTH))

    assert after_first is not None and bars is not None and closed is not None
    assert opened is not None
    assert (after_first.rows, bars.rows, bars.frozen) == (60, 120, False)
    assert sorted(path.name for path in folder.iterdir()) == ["open.parquet", "state.json"]
    assert (closed.rows, closed.frozen, opened.rows, opened.frozen) == (3, True, 1, False)
    assert key(SIGNALS, CLOSED_MONTH).text in first.committed
    assert key(SIGNALS, CLOSED_MONTH).text not in second.committed
    assert second.committed == (key(BARS, OPEN_MONTH).text,)


def test_ticks_wait_for_their_cadence_while_bars_keep_theirs(volume: Volume) -> None:
    volume.clock.at(OPEN_MONTH)
    volume.add_ticks(10)
    volume.add_bars(10)
    harvest = harvester(volume.home)

    harvest.round(NOW, Cadence())
    volume.add_ticks(10)
    volume.add_bars(10)
    minute_on, _ = harvest.round(NOW + timedelta(seconds=60), Cadence())
    ticks_then = volume.store.state(key(TICKS, OPEN_MONTH))
    hour_on, _ = harvest.round(NOW + timedelta(seconds=3_600), Cadence())
    ticks = volume.store.state(key(TICKS, OPEN_MONTH))
    bars = volume.store.state(key(BARS, OPEN_MONTH))

    assert ticks_then is not None and ticks is not None and bars is not None
    assert (ticks_then.rows, minute_on.waiting) == (10, 1)
    assert (ticks.rows, bars.rows) == (20, 20)
    assert hour_on.committed == (key(TICKS, OPEN_MONTH).text,)


def test_an_unchanged_stream_is_skipped_by_its_fingerprint(volume: Volume) -> None:
    volume.clock.at(OPEN_MONTH)
    volume.add_bars(30)
    volume.signal(OPEN_MONTH + timedelta(hours=8), "open-0")
    harvest = harvester(volume.home)

    first, _ = harvest.round(NOW, Cadence())
    second, _ = harvest.round(NOW + timedelta(seconds=60), Cadence())
    bars = volume.store.state(key(BARS, OPEN_MONTH))

    assert bars is not None
    assert (first.streams, first.partitions) == (2, 2)
    assert (second.streams, second.partitions, second.skipped_unchanged) == (0, 0, 2)
    assert (bars.rows, bars.attempts) == (30, 1)


def test_a_round_leaves_every_stream_file_byte_for_byte_with_a_line_in_flight(
    volume: Volume,
) -> None:
    volume.clock.at(OPEN_MONTH)
    volume.add_bars(5)
    volume.signal(OPEN_MONTH + timedelta(hours=8), "open-0")
    stream = next((volume.home / "apps").rglob("000000.jsonl"))
    with stream.open("ab") as file:
        file.write(b'{"series": "in flight')
    before = volume.stream_bytes()

    counts, _ = harvester(volume.home).round(NOW, Cadence())

    assert counts.refusals == ()
    assert volume.stream_bytes() == before


def test_a_reprojected_trade_lands_nothing_new_and_one_without_initial_risk_says_so(
    volume: Volume, tmp_path: Path
) -> None:
    closed = OPEN_MONTH + timedelta(hours=9)
    volume.trade("t1", OPEN_MONTH, closed, r="1.5", money="53.30")
    volume.trade("t2", OPEN_MONTH, closed, money="-12.00")
    with Store.open(tmp_path / "library", redactor=redact) as store:
        job = Records(
            harvester(volume.home),
            Cadence,
            clock=lambda: NOW,
            projection=Projection(store, volume.home / "records"),
            store=store,
        )
        first = job.round()
        volume.signal(OPEN_MONTH + timedelta(hours=10), "later")
        again = job.round()
        views = [store.get(OPERATOR, object_id) for _item, object_id in store.heads_on(MAIN)]

    landed = {(view.kind, str(view.fields.get("position_id", ""))): view for view in views}
    risked, unrisked = landed["trade", "t1"], landed["trade", "t2"]
    paper = next(view for view in views if view.kind == "paper-run")
    assert (first.trades, again.trades, first.paper_runs, again.paper_runs) == (2, 0, 1, 0)
    assert sorted(kind for kind, _ in landed) == ["artifact", "paper-run", "trade", "trade"]
    assert (risked.fields["r"], risked.fields["net_result"], risked.fields["r_missing"]) == (
        1.5,
        5330,
        False,
    )
    assert (unrisked.fields["r_missing"], "r" in unrisked.fields) == (True, False)
    assert (paper.fields["trades"], paper.fields["r_missing"], paper.fields["record_r"]) == (
        2,
        1,
        "1.5",
    )
    assert (paper.fields["sequential_score"], paper.fields["fresh_enough"]) == ("1.140625", False)


def iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_a_lane_that_leaves_paper_ends_its_one_run_from_the_move_into_paper(
    volume: Volume, tmp_path: Path
) -> None:
    host = writer(volume.home / "journals", JournalStream.UNIT, "dummy", volume.clock)

    def move(at: datetime, was: str, to: str) -> None:
        volume.clock.at(at)
        body = {
            "schema": "qmx.lifecycle/1",
            "event_id": f"move-{to}",
            "unit_id": "dummy",
            "version_ref": "v1",
            "compiled_fingerprint": "fp1-dummy",
            "market_id": "fx.eurusd",
            "from": was,
            "to": to,
            "by": {"kind": "his_click", "principal": "operator"},
            "reason": "his click",
            "at": at.isoformat(),
        }
        facts = RowFacts(
            ts_recv=volume.clock.ns, clock_ok=True, unit_id="dummy", market_id="fx.eurusd"
        )
        assert not is_refusal(host.append("lifecycle", body, facts))

    into_paper, to_live = OPEN_MONTH + timedelta(hours=2), OPEN_MONTH + timedelta(hours=5)
    volume.trade("before", OPEN_MONTH, OPEN_MONTH + timedelta(hours=1), r="-0.5")
    move(into_paper, "tested", "paper")
    volume.trade("p1", into_paper, OPEN_MONTH + timedelta(hours=3), r="1.5")
    volume.trade("p2", into_paper, OPEN_MONTH + timedelta(hours=4), r="1.0")
    try:
        with Store.open(tmp_path / "library", redactor=redact) as store:
            now = [NOW]
            job = Records(
                harvester(volume.home),
                Cadence,
                clock=lambda: now[0],
                projection=Projection(store, volume.home / "records"),
                store=store,
            )
            running = job.round()
            move(to_live, "paper", "live")
            now[0] = NOW + timedelta(seconds=60)
            ended = job.round()
            views = [store.get(OPERATOR, object_id) for _item, object_id in store.heads_on(MAIN)]
    finally:
        host.close()

    runs = [view.fields for view in views if view.kind == "paper-run"]
    assert (running.paper_runs, ended.paper_runs, len(runs)) == (1, 1, 1)
    assert (runs[0]["status"], runs[0]["started_at"], runs[0]["ended_at"]) == (
        "ended",
        iso(into_paper),
        iso(to_live),
    )
    assert (runs[0]["trades"], runs[0]["record_r"]) == (2, "2.5")
