"""The core read rows `instrument_get` and `readings_query` (Part C CONTRACTS.md section 12,
slice C-24): an instrument record as it stood at an instant, and reading history over a
required window through the market-data door's holdout, the open month included."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from fastmcp import Client
from pydantic import JsonValue
from qmf.core import canonical_bytes, fingerprint_bytes, is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts, envelope_json
from qmf.data.series import OPEN_NAME, SeriesKey, SeriesStore
from qmf.readings.record import (  # pyright: ignore[reportMissingTypeStubs]
    Health,
    ReadingRecord,
    ReadingRef,
    ReadingSource,
    Tier,
    TimeBase,
)
from qmx_control.library import OPERATOR
from qmx_library.port import Draft
from qmx_library.principal import MAIN

from qmx_tools.functions import domain_functions
from qmx_tools.servers import create_server
from qmx_tools.service import DomainContext, MarketPort, unwrap

NOON = timedelta(hours=12)
WEEK = {"start": "2024-12-30T00:00:00Z", "end": "2025-01-06T00:00:00Z"}
WORDS = ("quiet", "normal", "elevated", "stressed", "normal", "quiet", "elevated")
DAYS = [datetime(2024, 12, 28, tzinfo=UTC) + timedelta(days=n) for n in range(7)]
"""28 December 2024 to 3 January 2025: four days in a closed month, three in the open one."""


def door(root: Path, data: dict[str, object]) -> MarketPort:
    from qmx_host.market_data import MarketDoor  # pyright: ignore[reportMissingTypeStubs]

    return cast("MarketPort", unwrap(MarketDoor.open(root / "market", data)))


@pytest.fixture
def context(tmp_path: Path) -> Iterator[DomainContext]:
    ctx = DomainContext(root=tmp_path, market=door(tmp_path, {}))
    yield ctx
    ctx.control.close()


def record(reading: str, market: str, at: datetime, word: str) -> dict[str, object]:
    ns = int(at.timestamp()) * 1_000_000_000
    body = ReadingRecord(
        reading=ReadingRef(reading, "1", fingerprint_bytes(reading.encode())),
        source=ReadingSource.MIS,
        machine="this-pc",
        market_id=market,
        instrument=market.upper(),
        tier=Tier.BAR,
        time_base=TimeBase.CLOCK,
        health=Health.FRESH,
        data_level=1,
        fallback_step=0,
        inputs_received_at=ns,
        computed_at=ns,
        stale_after_s=7_200,
        word=word,
    ).body()
    return envelope_json(
        RowFacts(ts_recv=ns, clock_ok=True, market_id=market),
        record_id=f"mis@this-pc/{reading}-{ns}",
        stream=JournalStream.READINGS,
        kind="reading",
        schema_version=1,
        writer_id="mis@this-pc",
        seq=0,
        ts_write=ns,
        world=JournalWorld.LIVE,
        machine="this-pc",
        build="test",
        body=body,
    )


def harvested(root: Path, market: str, records: list[dict[str, object]]) -> None:
    """The MIS app's reading history of one market as the records job files it: December
    closed, January held open."""
    store = SeriesStore(root / "market" / "series")
    for year, month in ((2024, 12), (2025, 1)):
        key = SeriesKey.try_create(
            "journal-readings", f"mis.{market}", "reading", year, month, "live.this-pc"
        )
        assert not is_refusal(key)
        rows: list[tuple[object, ...]] = []
        for seq, made in enumerate(sorted(records, key=lambda made: cast("int", made["ts_recv"]))):
            t = int(cast("int", made["ts_recv"])) // 1_000_000
            moment = datetime.fromtimestamp(t // 1_000, tz=UTC)
            if (moment.year, moment.month) == (year, month):
                rows.append((t, seq, cast("bytes", unwrap(canonical_bytes(made))).decode()))
        hold = "the open month" if (year, month) == (2025, 1) else None
        assert not is_refusal(store.commit(key.value, rows, hold=hold))


@pytest.fixture
def week(context: DomainContext) -> DomainContext:
    eurusd = [
        record("volatility-state", "eurusd", day + NOON, w)
        for day, w in zip(DAYS, WORDS, strict=True)
    ]
    others = [record("spread-state", "eurusd", day + NOON, "wide") for day in DAYS]
    harvested(context.root, "eurusd", [*eurusd, *others])
    harvested(
        context.root, "gbpusd", [record("volatility-state", "gbpusd", DAYS[3] + NOON, "quiet")]
    )
    return context


def query(context: DomainContext, **asked: Any) -> dict[str, Any]:
    return domain_functions(context)["readings"]["readings_query"](**asked)


def test_a_week_of_readings_pages_by_cursor_into_exactly_its_rows(week: DomainContext) -> None:
    pages: list[list[dict[str, Any]]] = []
    cursor = None
    while True:
        answer = query(
            week,
            reading="volatility-state",
            window=WEEK,
            markets=["eurusd"],
            limit=2,
            cursor=cursor,
        )
        pages.append(answer["result"])
        cursor = answer["next_cursor"]
        if cursor is None:
            break
    folder = week.root / "market/series/journal-readings/mis.eurusd/reading/live.this-pc/2025-01"

    assert [[(row["at"], row["word"]) for row in page] for page in pages] == [
        [("2024-12-30T12:00:00.000Z", "elevated"), ("2024-12-31T12:00:00.000Z", "stressed")],
        [("2025-01-01T12:00:00.000Z", "normal"), ("2025-01-02T12:00:00.000Z", "quiet")],
        [("2025-01-03T12:00:00.000Z", "elevated")],
    ]
    assert (folder / OPEN_NAME).is_file()
    assert pages[0][0] == {
        "at": "2024-12-30T12:00:00.000Z",
        "word": "elevated",
        "reading": "volatility-state@1",
        "source": "mis",
        "market_id": "eurusd",
        "tier": "bar",
        "health": "fresh",
        "fallback_step": 0,
        "computed_at": "2024-12-30T12:00:00.000Z",
        "stale_after_s": 7_200,
    }
    detailed = query(week, reading="volatility-state", window=WEEK, response_format="detailed")
    assert detailed["result"][0]["record"]["body"]["instrument"] == "EURUSD"


def test_a_window_past_the_data_answers_where_the_data_ends(week: DomainContext) -> None:
    answer = query(
        week,
        reading="volatility-state",
        window={"start": "2025-02-01T00:00:00Z", "end": "2025-02-08T00:00:00Z"},
    )

    assert (answer["result"], answer["next_cursor"]) == ([], None)
    assert answer["data_ends_at"] == "2025-01-03T12:00:00.000Z"
    assert answer["note"] == (
        "the data stops at 2025-01-03T12:00:00.000Z; nothing after it is recorded yet"
    )


def test_a_query_without_a_window_is_refused(week: DomainContext) -> None:
    with pytest.raises(ValueError, match="readings_query needs a time window"):
        query(week, reading="volatility-state", window={"start": "2025-01-01T00:00:00Z"})

    async def unwindowed() -> str:
        async with Client(create_server("readings", week)) as client:
            try:
                await client.call_tool("readings_query", {"reading": "volatility-state"})
            except Exception as refused:
                return str(refused)
        return "answered"

    assert "window" in asyncio.run(unwindowed())


def test_a_study_holdout_seals_reading_history_and_the_journal_door_reads_none(
    tmp_path: Path,
) -> None:
    sealed = DomainContext(
        root=tmp_path, market=door(tmp_path, {"holdout": True, "holdout_boundary": "2025-01"})
    )
    harvested(
        tmp_path,
        "eurusd",
        [
            record("volatility-state", "eurusd", d + NOON, w)
            for d, w in zip(DAYS, WORDS, strict=True)
        ],
    )
    try:
        before = query(
            sealed,
            reading="volatility-state",
            window={"start": "2024-12-30T00:00:00Z", "end": "2025-01-01T00:00:00Z"},
        )
        with pytest.raises(
            ValueError, match="the study's holdout seals reading history"
        ) as refused:
            query(sealed, reading="volatility-state", window=WEEK)

        async def through_the_journal_door() -> str:
            async with Client(create_server("research", sealed)) as client:
                try:
                    await client.call_tool("journal_query", {"stream": "readings", "window": WEEK})
                except Exception as error:
                    return str(error)
            return "answered"

        journal = asyncio.run(through_the_journal_door())
    finally:
        sealed.control.close()

    assert [row["word"] for row in before["result"]] == ["elevated", "stressed"]
    assert (before["data_ends_at"], before["holdout_from"]) == (
        "2024-12-31T12:00:00.000Z",
        "2025-01-01T00:00:00.000Z",
    )
    assert str(refused.value) == (
        "the study's holdout seals reading history from 2025-01-01T00:00:00.000Z; this window "
        "reaches journal-readings/mis.eurusd/reading/live.this-pc/2025-01, so it is refused, "
        "never answered empty; ask for a window that ends before the holdout"
    )
    assert journal != "answered"
    assert "'unit', 'market' or 'node'" in journal


def landed(context: DomainContext, fields: dict[str, object], at: datetime) -> None:
    store = context.library.store
    store.wall = lambda: at
    item = f"instrument:{fields['venue']}:{fields['symbol']}"
    head = store.head(item, MAIN)
    draft = Draft("instrument", item, item, fields=cast("dict[str, JsonValue]", fields))
    store.put(OPERATOR, draft, on=MAIN, expected_head=None if head is None else head[0])


def instrument(venue: str, symbol: str, market_id: str, **facts: object) -> dict[str, object]:
    return {
        "venue": venue,
        "symbol": symbol,
        "market_id": market_id,
        "class": "fx",
        "currency": "USD",
        "status": "live",
        **facts,
    }


def test_instrument_get_answers_the_version_in_force_at_each_instant(
    context: DomainContext,
) -> None:
    eurusd = instrument(
        "icmarkets-ctrader", "EURUSD", "eurusd", contract_size="100000", min_lot="0.01"
    )
    landed(context, eurusd, datetime(2025, 1, 1, tzinfo=UTC))
    landed(context, eurusd | {"min_lot": "0.1"}, datetime(2025, 2, 1, tzinfo=UTC))
    get = domain_functions(context)["instrument"]["instrument_get"]

    january = get(venue="icmarkets-ctrader", symbol="EURUSD", at="2025-01-15T00:00:00Z")
    february = get(venue="icmarkets-ctrader", symbol="EURUSD", at="2025-02-15T00:00:00Z")
    first = get(market_id="eurusd", version=1)
    before = get(venue="icmarkets-ctrader", symbol="EURUSD", at="2024-12-01T00:00:00Z")

    assert (january["version"], january["record"]["min_lot"], january["in_force_since"]) == (
        1,
        "0.01",
        "2025-01-01T00:00:00Z",
    )
    assert (february["version"], february["record"]["min_lot"], february["status"]) == (
        2,
        "0.1",
        "live",
    )
    assert (first["id"], first["version"], first["fingerprint"]) == (
        "instrument:icmarkets-ctrader:EURUSD",
        1,
        january["fingerprint"],
    )
    assert february["fingerprint"] != january["fingerprint"]
    assert before == {
        "ok": False,
        "code": "not_found",
        "nearest": ["icmarkets-ctrader:EURUSD"],
        "message": "no version of it was in force at 2024-12-01T00:00:00.000Z; its first "
        "version reached main at 2025-01-01T00:00:00Z",
    }


def test_instrument_get_names_the_choices_and_the_nearest_records(context: DomainContext) -> None:
    at = datetime(2025, 1, 1, tzinfo=UTC)
    landed(context, instrument("icmarkets-ctrader", "XAUUSD", "gold", **{"class": "metal"}), at)
    landed(context, instrument("pepperstone", "XAUUSD", "gold", **{"class": "metal"}), at)
    get = domain_functions(context)["instrument"]["instrument_get"]

    gold = get(market_id="gold")

    assert gold["message"] == (
        "2 instrument records hold gold; name one by venue and symbol, or archive the one withdrawn"
    )
    assert gold["choices"] == [
        {
            "id": "instrument:icmarkets-ctrader:XAUUSD",
            "venue": "icmarkets-ctrader",
            "symbol": "XAUUSD",
        },
        {"id": "instrument:pepperstone:XAUUSD", "venue": "pepperstone", "symbol": "XAUUSD"},
    ]
    assert get(venue="pepperstone", symbol="XAUUSD")["record"]["market_id"] == "gold"
    assert get(venue="pepperstone", symbol="XAGUSD") == {
        "ok": False,
        "code": "not_found",
        "nearest": ["pepperstone:XAUUSD", "icmarkets-ctrader:XAUUSD"],
    }
