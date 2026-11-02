"""The node trades the dummy unit against the conformance venue (Part C slice C-12a, CA-03).

The rig is a node on a throwaway folder with one account binding on the conformance venue, a
fake that never reaches a broker. The dummy is staged as the node link stages it, deployed,
warmed up from the node's own recording of QML's synthetic EURUSD and XAUUSD month, and then
fed a recorded day bar by bar, the clock set to each bar as it closes.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from functools import cache
from itertools import groupby
from pathlib import Path
from typing import cast

from qmb.host.unit_runner import load_unit_folder
from qmb.runloop import SliceObservation, run_slice
from qmf.core import Account, AccountRole, Instant, TypedRefusal, VenueId
from qmf.data.journal_writer import JournalWriter
from qmf.venue.commands import CommandKind
from qml.blocks.api import EntryFace, parse_entry
from qml.compile import CompiledUnit
from qml.numbers import lots, parse_record
from qml.protocol.unit import QuoteBar

from qmn.app.feed_keeper import Bar, FeedKeeper, Quote, RecordedSource, Recording
from qmn.app.runtime import (
    ConformanceAccount,
    Deployment,
    Phase,
    Runtime,
    Venue,
    compile_staged,
)
from qmn.app.server import Node, open_node
from qmn.app.store import Json

REPO = Path(__file__).resolve().parents[2]
STDLIB = REPO / "qml" / "src" / "qml" / "blocks" / "stdlib"
RECORDS = REPO / "qml" / "tests" / "fixtures" / "records"
SLICES = REPO / "qml" / "tests" / "fixtures" / "slices"
DUMMY = REPO / "qml" / "src" / "qml" / "unit" / "templates" / "dummy-trend-pullback.json"
MARKETS = {"fx.eurusd": "eurusd", "metal.xauusd": "xauusd"}
ACCOUNT = "demo-1"
EQUITY = Decimal("10000.00")
LIVE_FROM = 1_742_500_000_000_000_000
"""2025-03-20 19:46:40 UTC: the bars before it are the node's recording, the day after it is
played live."""
DAY = 86_400_000_000_000
TAG = "a4dqobyh"
"""The node tag the rig's fixed random source mints."""


@dataclass(frozen=True)
class Month:
    fingerprint: str
    bars: tuple[tuple[int, str, QuoteBar], ...]
    files: tuple[tuple[str, str, int, str, bytes], ...]
    """Every pinned block file: entry id, kind, version, path, bytes."""


@cache
def month() -> Month:
    """The dummy's compiled fingerprint and both markets' bars, read once."""
    root = Path(tempfile.mkdtemp(prefix="c12a-month-"))
    try:
        folder = root / "run"
        (folder / "records").mkdir(parents=True)
        (folder / "unit.json").write_text(json.dumps(dummy_document()), "utf-8")
        for block in (p for p in STDLIB.iterdir() if (p / "1" / "block.py").is_file()):
            pin = folder / "blocks" / f"{block.name}@1"
            pin.mkdir(parents=True)
            for name in ("block.py", "entry.json"):
                shutil.copyfile(block / "1" / name, pin / name)
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
        return Month(
            loaded.value.compiled.compiled_fingerprint.value,
            tuple(merged),
            tuple(block_files()),
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def dummy_document() -> dict[str, object]:
    document = cast("dict[str, object]", json.loads(DUMMY.read_text("utf-8")))
    pins: list[dict[str, object]] = []
    for folder in sorted(p for p in STDLIB.iterdir() if (p / "1" / "entry.json").is_file()):
        face = parse_entry((folder / "1" / "entry.json").read_bytes())
        assert isinstance(face, EntryFace), face
        pins.append({"entry_id": face.entry_id, "version": 1, "fingerprint": face.fingerprint})
    document["pins"] = pins
    return document


def block_files() -> list[tuple[str, str, int, str, bytes]]:
    found: list[tuple[str, str, int, str, bytes]] = []
    for block in sorted(p for p in STDLIB.iterdir() if (p / "1" / "block.py").is_file()):
        face = parse_entry((block / "1" / "entry.json").read_bytes())
        assert isinstance(face, EntryFace), face
        for name, kind in (("block.py", "block"), ("entry.json", "entry")):
            path = f"blocks/{face.entry_id}@1/{name}"
            found.append((face.entry_id, kind, 1, path, (block / "1" / name).read_bytes()))
    return found


def fingerprint(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def stage(data: Path, deployment_id: str, path: str, raw: bytes) -> None:
    target = data / "deployments" / deployment_id / "in" / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)


def deployment(
    data: Path,
    deployment_id: str = "dep-1",
    *,
    compiled: str | None = None,
    extra: tuple[tuple[str, str, bytes], ...] = (),
    staged: bool = True,
) -> dict[str, Json]:
    """The dummy's deployment document, its files staged as the node link stages them."""
    files: list[Json] = []
    for entry_id, kind, version, path, raw in (
        *month().files,
        *((entry, "weights", 1, path, raw) for entry, path, raw in extra),
    ):
        if staged:
            stage(data, deployment_id, path, raw)
        files.append(
            {
                "entry_id": entry_id,
                "version": version,
                "fingerprint": fingerprint(raw),
                "path": path,
                "kind": kind,
                "bytes": len(raw),
            }
        )
    tested = compiled or month().fingerprint
    return {
        "schema_version": "qmx.node.deployment/1",
        "deployment_id": deployment_id,
        "node": {"tag": TAG, "install_id": None},
        "unit": {"id": "dummy-trend-pullback", "version": 1},
        "unit_document": cast("Json", dummy_document()),
        "compiled_fingerprint": tested,
        "g_record": {"id": "g-test-report", "version": 1, "compiled_fingerprint": tested},
        "files": files,
        "starting": {"source": "defaults", "values": {}},
        "markets": [],
        "account": {"id": ACCOUNT, "version": 1, "fingerprint": None},
        "snapshots": [
            cast("Json", json.loads((RECORDS / f"{symbol}.json").read_text("utf-8")))
            for symbol in MARKETS.values()
        ],
        "lane": "paper",
        "placeholders_acknowledged": False,
        "created_by": "operator",
        "created_at": "2026-11-02T09:00:00+00:00",
    }


@dataclass
class Rig:
    node: Node
    runtime: Runtime
    account: ConformanceAccount
    feed: FeedKeeper
    source: RecordedSource
    now: list[int]
    data: Path


def rig(
    root: Path,
    *,
    holds_stops: bool = True,
    compile: Callable[[Deployment, Path], CompiledUnit | str] = compile_staged,
    recorded: bool = True,
    here: str = "fp-pc-1",
) -> Rig:
    """A node on ``root`` bound to one conformance account, its recording holding the month
    before ``LIVE_FROM``."""
    now = [LIVE_FROM - DAY]
    source = RecordedSource([])
    venue = VenueId("icmarkets-ctrader")
    account = Account(ACCOUNT, venue, AccountRole.DEMO)
    made: dict[str, object] = {}

    def venues(journal: JournalWriter, epoch: str) -> Mapping[str, Venue]:
        del journal, epoch
        client = ConformanceAccount.open(account, EQUITY, holds_stops=holds_stops)
        assert not isinstance(client, TypedRefusal), client
        feed = FeedKeeper(
            "ctrader", "demo", source, tuple(MARKETS), lambda: now[0], Recording(None)
        )
        feed.listen(client.value.on_bar)
        made.update(client=client.value, feed=feed)
        return {ACCOUNT: Venue(client.value, feed)}

    def sleep(seconds: float) -> None:
        now[0] += int(seconds * 1e9)

    data = root / "data"
    node = open_node(
        data,
        here=here,
        machine="pc",
        clock_ns=lambda: now[0],
        sleep=sleep,
        random_bytes=lambda size: b"\x07" * size,
        venues=venues,
    )
    runtime = cast("Runtime", node.runtime)
    runtime.compile = compile
    feed = cast("FeedKeeper", made["feed"])
    if recorded:
        for at, market, bar in month().bars:
            if at < LIVE_FROM:
                feed.recording.keep(market, bar)
    return Rig(node, runtime, cast("ConformanceAccount", made["client"]), feed, source, now, data)


def settle(rig: Rig, deployment_id: str = "dep-1") -> str:
    """Tick until the deployment has compiled; answers its phase."""
    deadline = time.monotonic() + 60
    while True:
        rig.runtime.tick()
        hosted = rig.runtime.hosted.get(deployment_id)
        if hosted is not None and hosted.phase is not Phase.COMPILING:
            return hosted.phase.value
        assert time.monotonic() < deadline, "the compile did not finish in 60 s"
        time.sleep(0.02)


def play(rig: Rig, until: int, *, start: int = LIVE_FROM) -> None:
    """Play the recorded bars in ``[start, until)`` as the venue's feed, one tick per bar."""
    live = [item for item in month().bars if start <= item[0] < until]
    for at, group in groupby(live, key=lambda item: item[0]):
        closed = list(group)
        rig.now[0] = at
        rig.source.play(
            [
                *(Bar(market, bar) for _, market, bar in closed),
                *(Quote(market, at, bar.bid.close, bar.ask.close, "both") for _, market, bar in closed),
            ]
        )
        rig.runtime.tick()


def value(answer: dict[str, Json]) -> dict[str, Json]:
    assert answer["ok"] is True, answer
    return cast("dict[str, Json]", answer["value"])


def deploy(rig: Rig, document: dict[str, Json], op_id: str = "op-deploy-1") -> dict[str, Json]:
    return rig.node.call("deploy", {"op_id": op_id, "deployment": document})


def unit_rows(rig: Rig, kind: str) -> list[dict[str, object]]:
    rows = rig.node.call("journal_tail", {"streams": ["unit"]})
    found = cast("list[dict[str, object]]", value(rows)["rows"])
    return [cast("dict[str, object]", row["body"]) for row in found if row["kind"] == kind]


def receipt_after_rounding(quantity: Decimal) -> Decimal:
    record = parse_record(json.loads((RECORDS / "eurusd.json").read_text("utf-8")))
    assert not isinstance(record, TypedRefusal)
    sized = lots(quantity, record.value)
    assert not isinstance(sized, TypedRefusal)
    return Decimal(sized.value.value).scaleb(-sized.value.scale)


def test_the_dummy_opens_and_closes_at_the_venue_with_its_stop_there(tmp_path: Path) -> None:
    node = rig(tmp_path)
    accepted = deploy(node, deployment(node.data))
    phase = settle(node)
    play(node, LIVE_FROM + 2 * DAY)

    tickets = node.account.received
    assert accepted == {
        "ok": True,
        "value": {"deployment_id": "dep-1", "state": "accepted"},
        "op_id": "op-deploy-1",
    }
    assert phase == "trading"
    assert value(node.node.call("status", {}))["headline"] == "Trading, 1 unit"
    assert [(t.command.kind, t.market_id, t.side.value, t.quantity) for t in tickets] == [
        (CommandKind.PLACE_ORDER, "fx.eurusd", "short", Decimal("1.72")),
        (CommandKind.PLACE_ORDER, "fx.eurusd", "short", Decimal("1.08")),
        (CommandKind.PLACE_ORDER, "fx.eurusd", "short", Decimal("0.75")),
        (CommandKind.CLOSE_POSITION, "fx.eurusd", "short", None),
    ]
    entries = [t for t in tickets if t.tags is not None]
    assert [t.quantity for t in entries] == [
        receipt_after_rounding(cast("Decimal", t.receipt_quantity)) for t in entries
    ]
    assert all(
        t.command.order_parameters is not None
        and t.command.order_parameters.protective_stop_distance is not None
        for t in entries
    )
    names = [cast("str", t.tags.client_order_id) for t in entries if t.tags is not None]
    assert all(re.fullmatch(r"qa4dqobyh-[0-9A-HJKMNP-TV-Z]{26}", name) for name in names)
    assert {t.tags.label for t in entries if t.tags is not None} == {
        "qmx:a4dqobyh:dummy-trend-pullback"
    }
    assert tickets[3].position == names[2]
    trades = unit_rows(node, "trade")
    assert [(t["trade_id"], t["exit_kind"], t["quantity"]) for t in trades] == [
        (names[0], "stop", "1.72"),
        (names[1], "stop", "1.08"),
        (names[2], "close", "0.75"),
    ]
    fills = unit_rows(node, "fill")
    assert [(f["kind"], f.get("receipt_quantity")) for f in fills if f["kind"] == "entry"] == [
        ("entry", "1.72"),
        ("entry", "1.08"),
        ("entry", "0.75"),
    ]
    node.runtime.stop()


def test_deploy_answers_before_a_40_second_compile(tmp_path: Path) -> None:
    release = threading.Event()

    def slow(deployment: Deployment, folder: Path) -> CompiledUnit | str:
        release.wait(40)
        return compile_staged(deployment, folder)

    node = rig(tmp_path, compile=slow)
    node.runtime.start()
    started = time.monotonic()
    accepted = deploy(node, deployment(node.data))
    answered = time.monotonic() - started
    time.sleep(0.5)
    shown = value(node.node.call("status", {}))
    compiling = node.node.call("deployments", {})
    killed = node.node.call("kill", {"op_id": "op-kill", "level": "YELLOW", "scope": "all"})
    release.set()
    node.runtime.stop()

    assert answered < 2.0
    assert value(accepted)["state"] == "accepted"
    assert [(d["state"], d["detail"]) for d in cast("list[dict[str, Json]]", compiling["value"])] == [
        ("compiling", "compiling after the answer")
    ]
    assert shown["headline"] == "Ready"
    assert killed == {"ok": True, "value": {"level_in_force": "YELLOW"}, "op_id": "op-kill"}


def test_a_missing_or_changed_staged_file_refuses_deploy_by_name_and_32_mb_deploys(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    weights = (b"0123456789abcdef" * 2 * 1024 * 1024)[: 32 * 1024 * 1024]
    missing = deployment(node.data, "dep-missing", staged=False)
    changed = deployment(node.data, "dep-changed")
    stage(node.data, "dep-changed", "blocks/ema@1/block.py", b"# another block\n")
    heavy = deployment(node.data, "dep-heavy", extra=(("weights-1", "weights/model.bin", weights),))

    refused_missing = deploy(node, missing, "op-missing")
    refused_changed = deploy(node, changed, "op-changed")
    started = time.monotonic()
    accepted = deploy(node, heavy, "op-heavy")
    answered = time.monotonic() - started

    assert (refused_missing["code"], refused_missing["message"]) == (
        "files_missing",
        "deploy: staged file blocks/accelerator-oscillator@1/block.py is missing from in/",
    )
    assert refused_changed["code"] == "file_mismatch"
    assert refused_changed["message"] == (
        "deploy: staged file blocks/ema@1/block.py has fingerprint "
        f"{fingerprint(b'# another block\n')}, not "
        f"{fingerprint((STDLIB / 'ema' / '1' / 'block.py').read_bytes())}"
    )
    assert value(accepted) == {"deployment_id": "dep-heavy", "state": "accepted"}
    assert len(weights) == 33_554_432
    assert answered < 2.0
    lock = json.loads((node.data / "deployments" / "dep-heavy" / "lock.json").read_text("utf-8"))
    assert {"fingerprint": fingerprint(weights), "kind": "weights", "path": "weights/model.bin"} in lock
    assert [d["deployment_id"] for d in cast("list[dict[str, Json]]", listed(node))] == [
        "dep-heavy"
    ]


def listed(node: Rig) -> list[Json]:
    answer = node.node.call("deployments", {})
    assert answer["ok"] is True
    return cast("list[Json]", answer["value"])


def test_a_unit_that_compiles_to_another_fingerprint_than_its_g_record_never_trades(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    other = "fp1:sha256:" + "0" * 64
    deploy(node, deployment(node.data, compiled=other))
    phase = settle(node)
    play(node, LIVE_FROM + DAY)

    assert phase == "refused"
    assert listed(node) == [
        {
            "deployment_id": "dep-1",
            "unit": {"id": "dummy-trend-pullback", "version": 1},
            "state": "refused",
            "detail": f"compiled to {month().fingerprint}, not the {other} its G record tested",
            "accepted_at": "2025-03-19T19:46:40+00:00",
        }
    ]
    assert node.account.received == []


def test_a_copied_volume_hosts_no_deployment_until_confirm_same_node(tmp_path: Path) -> None:
    original = rig(tmp_path / "pc")
    deploy(original, deployment(original.data))
    original.runtime.stop()
    shutil.copytree(tmp_path / "pc", tmp_path / "server")
    moved = rig(tmp_path / "server", here="fp-server-1")
    play(moved, LIVE_FROM + DAY // 4)
    word = value(moved.node.call("status", {}))["word"]
    hosted = dict(moved.runtime.hosted)
    moved.node.call("confirm_same_node", {"op_id": "op-confirm"})
    phase = settle(moved)

    assert word == "Stopped by a health check"
    assert hosted == {}
    assert moved.account.received == []
    assert phase == "trading"


def test_a_slice_driven_again_sends_nothing_and_fills_nothing_twice(tmp_path: Path) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    live = [item for item in month().bars if item[0] >= LIVE_FROM]
    at = LIVE_FROM
    for at in sorted({t for t, _, _ in live}):
        play(node, at + 1, start=at)
        if node.account.received:
            break
    hosted = node.runtime.hosted["dep-1"]
    unit, loop = hosted.unit, hosted.loop
    assert unit is not None and unit.handler is not None and loop is not None
    after = min(t for t, _, _ in live if t > at)
    # The driver's own state before the slice it would drive again after a refusal.
    frontier, resting = loop._frontier, loop._resting  # pyright: ignore[reportPrivateUsage]
    for _, market, bar in (item for item in live if item[0] == after):
        unit.windows[market].push(bar)
    observations = tuple(
        SliceObservation(market, Instant(after), True) for t, market, _ in live if t == after
    )
    driven = [
        run_slice(
            observations,
            stream_set=loop.stream_set,
            current_frontier=frontier,
            clock=None,
            handler=unit,
            resting=resting,
        )
        for _ in range(2)
    ]

    assert all(not isinstance(outcome, TypedRefusal) for outcome in driven)
    assert [t.command.kind for t in node.account.received] == [CommandKind.PLACE_ORDER]
    assert [(f.kind.value, f.quantity) for f in unit.handler.fills] == [("entry", Decimal("1.72"))]
