"""C-22: the host's feed relay passes the MIS's landed board to the trading node, and a unit with
a placement read uses it within its `stale_after` and trades every admitted market otherwise.

The node is C-12a's conformance node on a throwaway folder, trading the dummy unit on the
synthetic March 2025 slices (not evidence about any market). No broker, key or token is read.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import tempfile
import time
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from functools import cache
from itertools import groupby
from pathlib import Path
from typing import cast

import pytest
from qmb.host.unit_runner import load_unit_folder
from qmf.core import Account, AccountRole, TypedRefusal, VenueId
from qmf.data.journal_writer import JournalWriter
from qml.blocks.api import EntryFace, parse_entry
from qml.compile import CompiledUnit
from qml.protocol.unit import QuoteBar
from qmn.app.feed_keeper import Bar, FeedKeeper, Quote, RecordedSource, Recording
from qmn.app.runtime import ConformanceAccount, Deployment, Phase, Runtime, Venue, compile_staged
from qmn.app.server import Node, open_node

from qmx_host import feed_relay
from qmx_host.feed_relay import Pass, relay

REPO = Path(__file__).resolve().parents[4]
STDLIB = REPO / "qml" / "src" / "qml" / "blocks" / "stdlib"
RECORDS = REPO / "qml" / "tests" / "fixtures" / "records"
SLICES = REPO / "qml" / "tests" / "fixtures" / "slices"
DUMMY = REPO / "qml" / "src" / "qml" / "unit" / "templates" / "dummy-trend-pullback.json"
MARKETS = {"fx.eurusd": "eurusd", "metal.xauusd": "xauusd"}
ACCOUNT = "demo-1"
LIVE_FROM = 1_742_500_000_000_000_000
"""2025-03-20 19:46:40 UTC: the bars before it are the node's recording; after it, live."""
DAY = 86_400_000_000_000
S = 1_000_000_000
TAG = "a4dqobyh"
OPEN_FACTS = {"placement": "this-pc", "holdout": {"on": False}}
PLACEMENT = {"tier": "bar", "reading": "efficiency-ratio", "favours": ["trending"]}
THE_DUMMYS_ENTRIES = [
    ("fx.eurusd", Decimal("1.61")),
    ("fx.eurusd", Decimal("1.03")),
    ("fx.eurusd", Decimal("0.72")),
]
"""What the dummy sends in two live days with no board: C-12a's literal tickets."""


# --- the MIS's board and the relay ---------------------------------------------------------


def landed(
    at: int, markets: Mapping[str, tuple[str, str]], facts: object = OPEN_FACTS
) -> dict[str, object]:
    """A board in the MIS's own shape (C-09): each market's efficiency-ratio word and its
    freshness word, one bar-tier board at `at`."""
    return {
        "boards": [
            {
                "tier": "bar",
                "at": at,
                "markets": [
                    {
                        "market_id": market,
                        "states": {"efficiency-ratio": word},
                        "freshness": {"efficiency-ratio": fresh},
                    }
                    for market, (word, fresh) in markets.items()
                ],
            }
        ]
    }


def land(home: Path, board: object, facts: object = OPEN_FACTS) -> None:
    mis = home / "apps" / "mis"
    (mis / "data").mkdir(parents=True, exist_ok=True)
    (mis / "road" / "host").mkdir(parents=True, exist_ok=True)
    (mis / "road" / "host" / "facts.json").write_text(json.dumps(facts), "utf-8")
    (mis / "data" / "board.json").write_text(json.dumps(board), "utf-8")


def node_feed(home: Path) -> Path:
    return home / "apps" / "trading-node" / "data" / "feeds" / "board.json"


def relayed_at(home: Path, host_ns: int, node_ns: int) -> Pass:
    """One relay pass on the host's clock; the node's filesystem stamps the write on its own."""
    passed = relay(home, host_ns)
    os.utime(node_feed(home), ns=(node_ns, node_ns))
    return passed


def test_a_landed_board_reaches_the_node_with_its_age_on_this_machines_clock(
    tmp_path: Path,
) -> None:
    (tmp_path / "apps" / "trading-node" / "data").mkdir(parents=True)
    at = LIVE_FROM
    land(tmp_path, landed(at, {"fx.eurusd": ("ranging", "fresh")}))

    passed = relay(tmp_path, at + 30 * S)

    assert passed == Pass("relayed")
    assert json.loads(node_feed(tmp_path).read_text("utf-8")) == {
        "schema_version": "qmx.node.feed.board/1",
        "boards": [
            {
                "tier": "bar",
                "at": LIVE_FROM,
                "age_ns": 30_000_000_000,
                "markets": [
                    {
                        "market_id": "fx.eurusd",
                        "states": {"efficiency-ratio": "ranging"},
                        "freshness": {"efficiency-ratio": "fresh"},
                    }
                ],
            }
        ],
    }
    assert sorted(p.name for p in node_feed(tmp_path).parent.iterdir()) == ["board.json"]


@pytest.mark.parametrize(
    ("board", "facts", "relayed_at_ns", "why"),
    [
        (None, OPEN_FACTS, LIVE_FROM, "the MIS has landed no board"),
        ("{not json", OPEN_FACTS, LIVE_FROM, "the MIS's board could not be read"),
        ({"boards": "bar"}, OPEN_FACTS, LIVE_FROM, "the MIS's board has no boards list"),
        (
            landed(LIVE_FROM + S, {}),
            OPEN_FACTS,
            LIVE_FROM,
            "the MIS's board is stamped after this machine's clock",
        ),
        (
            landed(LIVE_FROM, {}),
            {"holdout": {"on": True, "boundary": "2025-03", "months": 3}},
            LIVE_FROM,
            "the holdout seals 2025-03, the month of the MIS's board",
        ),
        (
            landed(LIVE_FROM, {}),
            None,
            LIVE_FROM,
            "the holdout seals 2025-03, the month of the MIS's board",
        ),
    ],
    ids=["no-board", "garbled", "no-boards-list", "future", "sealed", "no-facts"],
)
def test_the_relay_withholds_a_board_it_cannot_vouch_for(
    tmp_path: Path, board: object, facts: object, relayed_at_ns: int, why: str
) -> None:
    (tmp_path / "apps" / "trading-node" / "data").mkdir(parents=True)
    mis = tmp_path / "apps" / "mis"
    (mis / "data").mkdir(parents=True)
    if facts is not None:
        (mis / "road" / "host").mkdir(parents=True)
        (mis / "road" / "host" / "facts.json").write_text(json.dumps(facts), "utf-8")
    if isinstance(board, str):
        (mis / "data" / "board.json").write_text(board, "utf-8")
    elif board is not None:
        (mis / "data" / "board.json").write_text(json.dumps(board), "utf-8")

    passed = relay(tmp_path, relayed_at_ns)

    assert passed == Pass("withheld", why)
    assert json.loads(node_feed(tmp_path).read_text("utf-8")) == {
        "schema_version": "qmx.node.feed.board/1",
        "withheld": why,
    }


def test_with_no_trading_node_installed_the_relay_writes_nothing(tmp_path: Path) -> None:
    land(tmp_path, landed(LIVE_FROM, {}))

    passed = relay(tmp_path, LIVE_FROM)

    assert passed == Pass("no node")
    assert not (tmp_path / "apps" / "trading-node").exists()


def test_a_pass_that_dies_midway_leaves_the_last_board_and_the_next_pass_mends_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "apps" / "trading-node" / "data").mkdir(parents=True)
    land(tmp_path, landed(LIVE_FROM, {"fx.eurusd": ("ranging", "fresh")}))
    relay(tmp_path, LIVE_FROM + S)
    before = node_feed(tmp_path).read_bytes()
    land(tmp_path, landed(LIVE_FROM + 60 * S, {"fx.eurusd": ("trending", "fresh")}))

    def dies(source: object, target: object) -> None:
        raise OSError("the pass died before its replace")

    with monkeypatch.context() as patched:
        patched.setattr(feed_relay.os, "replace", dies)
        with pytest.raises(OSError, match="died before its replace"):
            relay(tmp_path, LIVE_FROM + 61 * S)
    kept = node_feed(tmp_path).read_bytes()
    mended = relay(tmp_path, LIVE_FROM + 62 * S)

    calls: list[int] = []

    def flaky(home: Path, now_ns: int) -> Pass:
        calls.append(now_ns)
        if len(calls) == 1:
            raise OSError("disk full")
        return Pass("relayed")

    async def two_passes() -> None:
        monkeypatch.setattr(feed_relay, "relay", flaky)
        task = asyncio.create_task(feed_relay.keep(tmp_path, every_s=0.01, clock_ns=lambda: 7))
        while len(calls) < 2:
            await asyncio.sleep(0.01)
        task.cancel()

    asyncio.run(two_passes())

    assert kept == before
    assert mended == Pass("relayed")
    words = json.loads(node_feed(tmp_path).read_text("utf-8"))["boards"][0]["markets"][0]
    assert words["states"] == {"efficiency-ratio": "trending"}
    assert sorted(p.name for p in node_feed(tmp_path).parent.iterdir()) == ["board.json"]
    assert calls[:2] == [7, 7]
    assert "feed relay: the board was not passed this time: OSError('disk full')" in (
        capsys.readouterr().err
    )


# --- the node: C-12a's conformance node trading the dummy ------------------------------------


@dataclass(frozen=True)
class Month:
    fingerprint: str
    bars: tuple[tuple[int, str, QuoteBar], ...]
    files: tuple[tuple[str, str, int, str, bytes], ...]


def dummy_document() -> dict[str, object]:
    document = cast("dict[str, object]", json.loads(DUMMY.read_text("utf-8")))
    pins: list[dict[str, object]] = []
    for entry in sorted(STDLIB.glob("*/*/entry.json")):
        face = parse_entry(entry.read_bytes())
        assert isinstance(face, EntryFace), face
        pins.append(
            {"entry_id": face.entry_id, "version": face.version, "fingerprint": face.fingerprint}
        )
    document["pins"] = pins
    return document


@cache
def month() -> Month:
    root = Path(tempfile.mkdtemp(prefix="c22-month-"))
    try:
        folder = root / "run"
        (folder / "records").mkdir(parents=True)
        (folder / "unit.json").write_text(json.dumps(dummy_document()), "utf-8")
        files: list[tuple[str, str, int, str, bytes]] = []
        for block in sorted(STDLIB.glob("*/*/block.py")):
            face = parse_entry(block.with_name("entry.json").read_bytes())
            assert isinstance(face, EntryFace), face
            pin = folder / "blocks" / face.pin
            pin.mkdir(parents=True)
            for name, kind in (("block.py", "block"), ("entry.json", "entry")):
                shutil.copyfile(block.with_name(name), pin / name)
                path = f"blocks/{face.pin}/{name}"
                files.append(
                    (face.entry_id, kind, face.version, path, block.with_name(name).read_bytes())
                )
        for market, symbol in MARKETS.items():
            shutil.copyfile(RECORDS / f"{symbol}.json", folder / "records" / f"{market}.json")
            (folder / "bars" / market).mkdir(parents=True)
            for side in ("bid", "ask"):
                shutil.copyfile(
                    SLICES / f"synthetic-{symbol}-m15-{side}-2025-03-01-2025-04-01.csv",
                    folder / "bars" / market / f"{side}.csv",
                )
        loaded = load_unit_folder(folder)
        assert not isinstance(loaded, TypedRefusal), loaded
        held = loaded.value.bars()
        assert not isinstance(held, TypedRefusal), held
        merged = sorted(
            (bar.knowable_at.value_ns, market, bar)
            for market, bars in held.value.items()
            for bar in bars
        )
        return Month(loaded.value.compiled.compiled_fingerprint.value, tuple(merged), tuple(files))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def deployment(data: Path, placement: Mapping[str, object] | None) -> dict[str, object]:
    files: list[object] = []
    for entry_id, kind, version, path, raw in month().files:
        target = data / "deployments" / "dep-1" / "in" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        files.append(
            {
                "entry_id": entry_id,
                "version": version,
                "fingerprint": f"sha256:{hashlib.sha256(raw).hexdigest()}",
                "path": path,
                "kind": kind,
                "bytes": len(raw),
            }
        )
    document: dict[str, object] = {
        "schema_version": "qmx.node.deployment/1",
        "deployment_id": "dep-1",
        "node": {"tag": TAG, "install_id": None},
        "unit": {"id": "dummy-trend-pullback", "version": 1},
        "unit_document": dummy_document(),
        "compiled_fingerprint": month().fingerprint,
        "g_record": {
            "id": "g-test-report",
            "version": 1,
            "compiled_fingerprint": month().fingerprint,
        },
        "files": files,
        "starting": {"source": "defaults", "values": {}},
        "markets": [{"market_id": market} for market in MARKETS],
        "account": {"id": ACCOUNT, "version": 1, "fingerprint": None},
        "snapshots": [
            json.loads((RECORDS / f"{symbol}.json").read_text("utf-8"))
            for symbol in MARKETS.values()
        ],
        "lane": "live",
        "placeholders_acknowledged": False,
        "created_by": "operator",
        "created_at": "2026-11-03T09:00:00+00:00",
    }
    if placement is not None:
        document["placement"] = dict(placement)
    return document


_COMPILED: dict[str, CompiledUnit | str] = {}


@dataclass
class Rig:
    home: Path
    node: Node
    runtime: Runtime
    account: ConformanceAccount
    source: RecordedSource
    now: list[int]


def rig(home: Path, placement: Mapping[str, object] | None) -> Rig:
    """C-12a's node in `home`'s trading-node volume, bound to one conformance account, its
    recording holding the month before `LIVE_FROM`, the dummy deployed and trading."""
    now = [LIVE_FROM - DAY]
    source = RecordedSource([])
    account = Account(ACCOUNT, VenueId("icmarkets-ctrader"), AccountRole.DEMO)
    made: dict[str, object] = {}

    def venues(journal: JournalWriter, epoch: str) -> Mapping[str, Venue]:
        del journal, epoch
        client = ConformanceAccount.open(account, Decimal("10000.00"), holds_stops=True)
        assert not isinstance(client, TypedRefusal), client
        feed = FeedKeeper(
            "ctrader", "demo", source, tuple(MARKETS), lambda: now[0], Recording(None)
        )
        feed.listen(client.value.on_bar)
        made.update(client=client.value, feed=feed)
        return {ACCOUNT: Venue(client.value, feed)}

    def sleep(seconds: float) -> None:
        now[0] += int(seconds * S)

    data = home / "apps" / "trading-node" / "data"
    node = open_node(
        data,
        here="fp-pc-1",
        machine="pc",
        clock_ns=lambda: now[0],
        sleep=sleep,
        random_bytes=lambda size: b"\x07" * size,
        venues=venues,
    )
    runtime = cast("Runtime", node.runtime)
    runtime.compile = compile_cached
    feed = cast("FeedKeeper", made["feed"])
    for at, market, bar in month().bars:
        if at < LIVE_FROM:
            feed.recording.keep(market, bar)
    built = Rig(home, node, runtime, cast("ConformanceAccount", made["client"]), source, now)
    # R22 holds a compiled unit until its account's session is ready, so the rig takes the feed's
    # first turn here: a node whose feed has never pumped waits instead of hosting the unit.
    feed.pump()
    assert feed.ready, feed.reason
    answer = node.call(
        "deploy", {"op_id": "op-deploy-1", "deployment": deployment(data, placement)}
    )
    assert answer["ok"] is True, answer
    deadline = time.monotonic() + 60
    while (hosted := runtime.hosted.get("dep-1")) is None or hosted.phase is Phase.COMPILING:
        runtime.tick()
        assert time.monotonic() < deadline, "the compile did not finish in 60 s"
        time.sleep(0.02)
    assert hosted.phase is Phase.TRADING, hosted.detail
    return built


def compile_cached(deployment: Deployment, folder: Path) -> CompiledUnit | str:
    """The dummy compiles to the same unit in every test, so it compiles once per process."""
    if "dummy" not in _COMPILED:
        _COMPILED["dummy"] = compile_staged(deployment, folder)
    return _COMPILED["dummy"]


def play(node: Rig, until: int, *, relay_every: bool = False, host_skew: int = 0) -> None:
    """Play the recorded bars in `[now, until)` as the venue's feed, one tick per bar; with
    `relay_every`, the relay passes the MIS's board before each tick."""
    live = [
        item for item in month().bars if node.now[0] <= item[0] < until and item[0] >= LIVE_FROM
    ]
    for at, group in groupby(live, key=lambda item: item[0]):
        closed = list(group)
        node.now[0] = at
        if relay_every:
            relayed_at(node.home, at + host_skew, at)
        node.source.play(
            [
                *(Bar(market, bar) for _, market, bar in closed),
                *(
                    Quote(market, at, bar.bid.close, bar.ask.close, "both")
                    for _, market, bar in closed
                ),
            ]
        )
        node.runtime.tick()


def entries(node: Rig) -> list[tuple[str, Decimal | None]]:
    return [(t.market_id, t.quantity) for t in node.account.received if t.tags is not None]


def unit_row(node: Rig) -> dict[str, object]:
    answer = node.node.call("units", {})
    assert answer["ok"] is True, answer
    return cast("list[dict[str, object]]", answer["value"])[0]


def status_board(node: Rig) -> object:
    answer = node.node.call("status", {})
    assert answer["ok"] is True, answer
    return cast("dict[str, object]", answer["value"])["board"]


def guard_rows(node: Rig) -> list[tuple[str, str]]:
    answer = node.node.call("journal_tail", {"streams": ["unit"]})
    assert answer["ok"] is True, answer
    rows = cast("list[dict[str, object]]", cast("dict[str, object]", answer["value"])["rows"])
    bodies = [cast("dict[str, str]", row["body"]) for row in rows if row["kind"] == "guard"]
    return [(body["reason"], body["detail"]) for body in bodies]


def test_a_fresh_board_keeps_the_unit_off_the_market_it_does_not_favour(tmp_path: Path) -> None:
    node = rig(tmp_path, {**PLACEMENT, "stale_after_s": 3 * 86_400})
    land(
        tmp_path,
        landed(
            LIVE_FROM - 60 * S,
            {
                "fx.eurusd": ("ranging", "fresh"),
                "metal.xauusd": ("trending", "fresh"),
                "fx.gbpusd": ("trending", "fresh"),
            },
        ),
    )
    play(node, LIVE_FROM + 2 * DAY, relay_every=True)

    board = {
        "state": "fresh",
        "detail": "",
        "as_of_ms": (LIVE_FROM - 60 * S) // 1_000_000,
        "favoured": ["metal.xauusd"],
        "held_back": {"fx.eurusd": "ranging"},
        "fallback": [],
    }
    assert entries(node) == []
    assert unit_row(node)["board"] == board
    assert status_board(node) == {"dep-1": board}
    held = "the board does not favour fx.eurusd now (efficiency-ratio is ranging)"
    assert set(guard_rows(node)) == {("not_favoured", held)}
    node.runtime.stop()


def test_a_stale_board_lets_the_unit_trade_every_admitted_market(tmp_path: Path) -> None:
    node = rig(tmp_path, {**PLACEMENT, "stale_after_s": 3_600})
    land(tmp_path, landed(LIVE_FROM - 60 * S, {"fx.eurusd": ("ranging", "fresh")}))
    relayed_at(tmp_path, LIVE_FROM - 30 * S, LIVE_FROM - 30 * S)
    play(node, LIVE_FROM + 2 * DAY)

    assert entries(node) == THE_DUMMYS_ENTRIES
    assert unit_row(node)["board"] == {
        "state": "stale",
        "detail": "older than its stale_after of 3600 s",
        "as_of_ms": (LIVE_FROM - 60 * S) // 1_000_000,
        "favoured": [],
        "held_back": {},
        "fallback": ["fx.eurusd", "metal.xauusd"],
    }
    node.runtime.stop()


def test_the_unit_trades_on_while_the_mis_is_stopped(tmp_path: Path) -> None:
    """Level 0 AD-2: the MIS's last board says no to EURUSD, then the MIS stops and lands
    nothing more. The relay keeps passing that board until it is stale, then its file goes."""
    node = rig(tmp_path, {**PLACEMENT, "stale_after_s": 3_600})
    land(tmp_path, landed(LIVE_FROM - 60 * S, {"fx.eurusd": ("ranging", "fresh")}))
    play(node, LIVE_FROM + DAY // 2, relay_every=True)
    stale = cast("dict[str, object]", unit_row(node)["board"])["state"]
    (tmp_path / "apps" / "mis" / "data" / "board.json").unlink()
    play(node, LIVE_FROM + 2 * DAY, relay_every=True)

    assert stale == "stale"
    assert entries(node) == THE_DUMMYS_ENTRIES
    assert unit_row(node)["board"] == {
        "state": "withheld",
        "detail": "the MIS has landed no board",
        "as_of_ms": None,
        "favoured": [],
        "held_back": {},
        "fallback": ["fx.eurusd", "metal.xauusd"],
    }
    node.runtime.stop()


def test_a_board_for_markets_the_unit_is_not_admitted_on_is_ignored(tmp_path: Path) -> None:
    node = rig(tmp_path, {**PLACEMENT, "stale_after_s": 3 * 86_400})
    land(tmp_path, landed(LIVE_FROM - 60 * S, {"fx.gbpusd": ("ranging", "fresh")}))
    play(node, LIVE_FROM + 2 * DAY, relay_every=True)

    assert entries(node) == THE_DUMMYS_ENTRIES
    assert unit_row(node)["board"] == {
        "state": "fresh",
        "detail": "",
        "as_of_ms": (LIVE_FROM - 60 * S) // 1_000_000,
        "favoured": [],
        "held_back": {},
        "fallback": ["fx.eurusd", "metal.xauusd"],
    }
    node.runtime.stop()


def test_a_market_whose_own_reading_is_not_fresh_trades_on_its_own_conditions(
    tmp_path: Path,
) -> None:
    """The board is fresh, but the MIS marked EURUSD's word stale and gold's thin at its time."""
    node = rig(tmp_path, {**PLACEMENT, "stale_after_s": 60})
    words = {"fx.eurusd": ("ranging", "stale"), "metal.xauusd": ("trending", "thin")}
    land(tmp_path, landed(LIVE_FROM - 10 * S, words))
    relayed_at(tmp_path, LIVE_FROM, LIVE_FROM)
    node.now[0] = LIVE_FROM
    node.runtime.tick()

    assert unit_row(node)["board"] == {
        "state": "fresh",
        "detail": "",
        "as_of_ms": (LIVE_FROM - 10 * S) // 1_000_000,
        "favoured": [],
        "held_back": {},
        "fallback": ["fx.eurusd", "metal.xauusd"],
    }
    node.runtime.stop()


def test_a_board_exactly_at_its_stale_after_is_used_and_one_nanosecond_later_is_not(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path, {**PLACEMENT, "stale_after_s": 60})
    land(tmp_path, landed(LIVE_FROM - 10 * S, {"fx.eurusd": ("ranging", "fresh")}))
    relayed_at(tmp_path, LIVE_FROM, LIVE_FROM)
    node.now[0] = LIVE_FROM + 50 * S
    node.runtime.tick()
    at_the_edge = cast("dict[str, object]", unit_row(node)["board"])
    node.now[0] = LIVE_FROM + 50 * S + 1
    node.runtime.tick()
    past_it = cast("dict[str, object]", unit_row(node)["board"])

    assert (at_the_edge["state"], at_the_edge["held_back"]) == ("fresh", {"fx.eurusd": "ranging"})
    assert (past_it["state"], past_it["held_back"]) == ("stale", {})
    node.runtime.stop()


def test_the_node_judges_a_boards_age_on_its_own_clock_not_the_hosts(tmp_path: Path) -> None:
    """The host's clock reads a year ahead of the node's. The relay stamps the board 10 s old on
    the host's clock; the node adds the time since the write on its own clock."""
    year = 365 * DAY
    node = rig(tmp_path, {**PLACEMENT, "stale_after_s": 60})
    land(tmp_path, landed(LIVE_FROM + year - 10 * S, {"fx.eurusd": ("ranging", "fresh")}))
    relayed_at(tmp_path, LIVE_FROM + year, LIVE_FROM)
    node.now[0] = LIVE_FROM + 20 * S
    node.runtime.tick()

    board = cast("dict[str, object]", unit_row(node)["board"])
    assert (board["state"], board["held_back"]) == ("fresh", {"fx.eurusd": "ranging"})
    assert board["as_of_ms"] == (LIVE_FROM - 10 * S) // 1_000_000
    node.runtime.stop()


FEEDS: list[tuple[object, str, str]] = [
    (None, "missing", "no board has been relayed to this node"),
    (
        {"schema_version": "qmx.node.feed.board/1", "boards": []},
        "empty",
        "the board holds nothing for the bar tier",
    ),
    (
        {"schema_version": "qmx.node.feed.board/2", "boards": []},
        "unreadable",
        "the board feed is not qmx.node.feed.board/1",
    ),
    ("{half a board", "unreadable", "the board feed is not qmx.node.feed.board/1"),
    (
        {"schema_version": "qmx.node.feed.board/1", "boards": [{"tier": "bar", "markets": []}]},
        "unreadable",
        "a relayed board lacks its tier or its age",
    ),
]


@pytest.mark.parametrize(
    ("feed", "state", "detail"),
    FEEDS,
    ids=["missing", "empty", "other-schema", "garbled", "no-age"],
)
def test_a_missing_empty_or_garbled_board_trades_every_admitted_market(
    tmp_path: Path, feed: object, state: str, detail: str
) -> None:
    node = rig(tmp_path, {**PLACEMENT, "stale_after_s": 60})
    if feed is not None:
        node_feed(tmp_path).parent.mkdir(parents=True, exist_ok=True)
        text = feed if isinstance(feed, str) else json.dumps(feed)
        node_feed(tmp_path).write_text(text, "utf-8")
    node.runtime.tick()

    assert unit_row(node)["board"] == {
        "state": state,
        "detail": detail,
        "as_of_ms": None,
        "favoured": [],
        "held_back": {},
        "fallback": ["fx.eurusd", "metal.xauusd"],
    }
    node.runtime.stop()


def test_a_deployment_without_a_placement_read_shows_no_board(tmp_path: Path) -> None:
    node = rig(tmp_path, None)
    land(tmp_path, landed(LIVE_FROM - 60 * S, {"fx.eurusd": ("ranging", "fresh")}))
    relayed_at(tmp_path, LIVE_FROM, LIVE_FROM)
    play(node, LIVE_FROM + 2 * DAY)

    assert entries(node) == THE_DUMMYS_ENTRIES
    assert "board" not in unit_row(node)
    assert status_board(node) == {}
    node.runtime.stop()


def test_a_placement_read_without_a_stale_after_refuses_the_deployment(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="stale_after_s is a whole number of seconds"):
        rig(tmp_path, PLACEMENT)
