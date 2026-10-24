"""P-QMBREAD: one month replays the same from typed partitions and from CT-10 receipts.

Acceptance probe for DR4 (W12, fix-check N2). QMB's replay reader has two entry points now, and
they must agree: the typed monthly partitions the market-data door serves, and the CT-10 archive
receipts the old reader admitted. This probe builds one month of quotes three ways on scratch
roots under `--scratch` (default `D:/Temp`):

- a `ticks` partition, both sides in each row;
- a `bar-m1` pair, the bid series and the ask series of the same month;
- the same frontiers admitted as CT-10 source observations into a scratch `EvidenceStore`.

Each is read through its entry point, each source is executed by one fixed trade rule over the
frontiers it produced, and every trade must be equal across the three. A bid series offered
without its ask must be refused rather than replayed as a half pair, and a partition whose rows do
not hash to the fingerprint claimed for it must be refused before a quote is built.

`--step-minutes` sets the spacing of the month's frontiers, and defaults to 60: the whole month,
one quote an hour, 744 frontiers. Both readers hold the whole series so far in every frontier's
read surface, so a read costs memory quadratic in the frontier count: the default run of 744
frontiers replayed in 12 to 16 s from the tick series, 14 to 17 s from the bid/ask pair and 27 to
38 s from 1,488 CT-10 receipts over three runs, with a peak working set around 1 GB, and the
month's whole 44,640 frontiers would hold about 1.0e9 sample entries, roughly 16 GB. The probe
therefore refuses more than 1,000 frontiers and prints the bound it applied. The bound belongs to
this probe and to the reader's inherited read surface, not to the number of minutes a month holds.

Nothing here touches his real home, his stores, his raw tree or his settings; every root is under
`--scratch` and is removed before the verdict unless `--keep`.
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
import time
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path

from qmb.host.replay import (
    PinnedInstrumentPriceMetadata,
    RecordedReplaySource,
    TypedPartitionRef,
    read_recorded_replay_source,
    read_typed_replay_source,
)
from qmf.core import (
    Instant,
    Instrument,
    Result,
    VenueId,
    World,
    WriterId,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.data.observation import ForeignMoney, MarketDataContext, SourceObservation
from qmf.data.series import SeriesKey, SeriesStore
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.store import EvidenceStore

YEAR = 2025
MONTH = 10
PRICE_SCALE = 5
FIRST_BID = 1_084_500
SPREAD = 20
MS = 1_000_000
MINUTE_NS = 60 * 1_000_000_000


def _ok(result: Result[object]) -> object:
    if not is_ok(result):
        raise SystemExit(f"P-QMBREAD FAIL: {result}")
    return result.value


def _month(day: int) -> int:
    return int(datetime(YEAR, MONTH, day, tzinfo=UTC).timestamp()) * 1_000_000_000


FIRST_NS = _month(1)
LAST_NS = FIRST_NS + 31 * 86_400 * 1_000_000_000
MINUTES_IN_MONTH = (LAST_NS - FIRST_NS) // MINUTE_NS
"""Every one-minute frontier the month holds: 44,640 in October."""


def _quotes(frontiers: int, step_minutes: int) -> tuple[tuple[int, int, int], ...]:
    """The month's quotes: (frontier_ns, bid, ask) every `step_minutes`, spread constant."""
    return tuple(
        (
            FIRST_NS + index * step_minutes * MINUTE_NS,
            FIRST_BID + (index * 7) % 200,
            FIRST_BID + (index * 7) % 200 + SPREAD,
        )
        for index in range(frontiers)
    )


def _metadata() -> PinnedInstrumentPriceMetadata:
    venue = _ok(VenueId.try_create("dukascopy"))
    instrument = _ok(Instrument.try_create(venue, "EURUSD"))
    identity: dict[str, object] = {
        "instrument": instrument.fp1_identity(),
        "metadata_version": "p-qmbread-fixture-v1",
        "price_scale": PRICE_SCALE,
        "source_policy": {"kind": "probe-fixture"},
    }
    return _ok(
        PinnedInstrumentPriceMetadata.try_create(
            instrument=instrument,
            price_scale=PRICE_SCALE,
            metadata_identity=identity,
            metadata_fp1=_ok(fingerprint(identity)),
        )
    )


def _partition(
    root: Path, kind: str, variant: str, rows: list[tuple[object, ...]]
) -> TypedPartitionRef:
    key = _ok(SeriesKey.try_create("dukascopy", "EURUSD", kind, YEAR, MONTH, variant))
    store = SeriesStore(root / "series-root")
    done = _ok(store.commit(key, rows))
    return _ok(
        TypedPartitionRef.try_create(
            path=done.path,
            series=key.series,
            month=f"{YEAR:04d}-{MONTH:02d}",
            fingerprint=done.fingerprint,
        )
    )


def _materialised(ref: TypedPartitionRef, into: Path) -> TypedPartitionRef:
    """Put the partition where a run reads it: a copy named by its fingerprint, hash checked."""
    into.mkdir(parents=True, exist_ok=True)
    copied = into / f"{ref.fingerprint}.parquet"
    shutil.copyfile(ref.path, copied)
    return TypedPartitionRef(
        path=copied, series=ref.series, month=ref.month, fingerprint=ref.fingerprint
    )


def _observation(side: str, frontier_ns: int, index: int, price: int) -> SourceObservation:
    at = _ok(Instant.try_create(frontier_ns))
    writer = _ok(WriterId.try_create("probe-node", "data", "market", "p-qmbread"))
    return _ok(
        SourceObservation.try_create(
            event_time=at,
            known_at=at,
            source="p-qmbread-fixture",
            source_native_id=f"p-qmbread-{index}-{side}",
            revision="1",
            receive_wall_time=at,
            writer=writer,
            sequence=index * 2 + (0 if side == "bid" else 1),
            world=World.REPLAY,
            foreign_money=_ok(ForeignMoney.try_create(price, PRICE_SCALE)),
            market_data=_ok(
                MarketDataContext.try_create(
                    venue="dukascopy",
                    symbol="EURUSD",
                    resolution="tick",
                    side=side,
                    license_tag="local-fixture",
                    provenance={"source_kind": "p-qmbread"},
                )
            ),
        )
    )


def _ct10_source(root: Path, quotes: tuple[tuple[int, int, int], ...]) -> RecordedReplaySource:
    boundary = SourceObservationBoundary(EvidenceStore(root / "ct10-room"))
    refs = tuple(
        _ok(boundary.admit(_observation(side, at, index, price))).archive.fingerprint.value
        for index, (at, bid, ask) in enumerate(quotes)
        for side, price in (("bid", bid), ("ask", ask))
    )
    return _ok(
        read_recorded_replay_source(
            store_root=root / "ct10-room",
            archive_fingerprints=refs,
            stream_id="eurusd",
            instrument_metadata=_metadata(),
        )
    )


def _trades(source: RecordedReplaySource) -> tuple[tuple[int, int, int, int], ...]:
    """One trade a frontier: enter at this frontier's ask, exit at the next one's bid."""
    priced: list[tuple[int, int, int]] = []
    for path in source.execution_paths:
        if path.bar_start is None or path.bid is None or path.ask is None:
            raise SystemExit("P-QMBREAD FAIL: an execution path carries no quote")
        priced.append((path.bar_start.value_ns, path.bid.value, path.ask.value))
    return tuple((entry[0], entry[2], follow[0], follow[1]) for entry, follow in pairwise(priced))


def _main_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", default="D:/Temp", help="where the scratch roots go")
    parser.add_argument(
        "--step-minutes",
        type=int,
        default=60,
        help="minutes between the month's frontiers (default 60: the whole month every hour)",
    )
    parser.add_argument("--keep", action="store_true", help="keep the scratch roots")
    return parser.parse_args()


def main() -> int:
    options = _main_arguments()
    if not 1 <= options.step_minutes <= MINUTES_IN_MONTH:
        raise SystemExit(f"P-QMBREAD FAIL: --step-minutes must be 1 to {MINUTES_IN_MONTH}")
    frontiers = MINUTES_IN_MONTH // options.step_minutes
    if frontiers > 1_000:
        raise SystemExit(
            "P-QMBREAD FAIL: "
            f"{frontiers} frontiers is past this probe's bound; the reader's read surface holds "
            "every sample so far, and 4,320 frontiers died with MemoryError. Raise "
            "--step-minutes instead"
        )
    scratch_root = Path(options.scratch).resolve()
    if not scratch_root.is_dir():
        raise SystemExit(f"P-QMBREAD FAIL: no scratch root at {scratch_root}")
    quotes = _quotes(frontiers, options.step_minutes)
    root = Path(tempfile.mkdtemp(prefix="p_qmbread-", dir=scratch_root))
    print(f"P-QMBREAD: DR4 acceptance probe; scratch {root}")
    print(
        f"month {YEAR}-{MONTH:02d}: {frontiers} frontiers, one every {options.step_minutes} "
        f"minutes, covering all {MINUTES_IN_MONTH} minutes of it"
    )
    print(
        "bound: the read surface carries every sample so far, so a replay costs memory "
        f"quadratic in the frontier count; the month's whole {MINUTES_IN_MONTH} holds about "
        "1.0e9 sample entries and would need roughly 16 GB"
    )
    try:
        rows = [(at // MS, bid, ask, 1.0, 1.0) for at, bid, ask in quotes]
        ticks = _materialised(_partition(root, "ticks", "", rows), root / "run-ticks")
        bar_bid = _materialised(
            _partition(
                root,
                "bar-m1",
                "bid",
                [(at // MS, bid, bid, bid, bid, 1.0) for at, bid, _ask in quotes],
            ),
            root / "run-bars",
        )
        bar_ask = _materialised(
            _partition(
                root,
                "bar-m1",
                "ask",
                [(at // MS, ask, ask, ask, ask, 1.0) for at, _bid, ask in quotes],
            ),
            root / "run-bars",
        )

        started = time.perf_counter()
        tick_source = _ok(
            read_typed_replay_source(
                partitions=(ticks,), stream_id="eurusd", instrument_metadata=_metadata()
            )
        )
        typed_ticks_seconds = time.perf_counter() - started
        started = time.perf_counter()
        pair_source = _ok(
            read_typed_replay_source(
                partitions=(bar_bid, bar_ask),
                stream_id="eurusd",
                instrument_metadata=_metadata(),
            )
        )
        typed_pair_seconds = time.perf_counter() - started
        started = time.perf_counter()
        ct10_source = _ct10_source(root, quotes)
        ct10_seconds = time.perf_counter() - started

        tick_trades = _trades(tick_source)
        pair_trades = _trades(pair_source)
        ct10_trades = _trades(ct10_source)

        print(
            f"typed ticks : {len(tick_source.execution_paths)} frontiers, "
            f"{typed_ticks_seconds:.2f} s"
        )
        print(
            f"typed pair  : {len(pair_source.execution_paths)} frontiers, "
            f"{typed_pair_seconds:.2f} s ({len(pair_source.partitions)} partitions)"
        )
        print(
            f"ct10        : {len(ct10_source.execution_paths)} frontiers, "
            f"{ct10_seconds:.2f} s ({len(ct10_source.observations)} receipts)"
        )
        print(
            f"trades      : {len(tick_trades)} from the same frontiers; ticks==pair "
            f"{tick_trades == pair_trades}; ticks==ct10 {tick_trades == ct10_trades}"
        )
        first, last = tick_trades[0], tick_trades[-1]
        net = sum(exit_price - entry_price for _, entry_price, _, exit_price in tick_trades)
        print(f"first trade : entry {first[1]} at {first[0]}, exit {first[3]} at {first[2]}")
        print(f"last trade  : entry {last[1]} at {last[0]}, exit {last[3]} at {last[2]}")
        print(f"net         : {net} ticks of source price over {len(tick_trades)} trades")

        half = read_typed_replay_source(
            partitions=(bar_bid,), stream_id="eurusd", instrument_metadata=_metadata()
        )
        substituted = TypedPartitionRef(
            path=ticks.path, series=ticks.series, month=ticks.month, fingerprint="0" * 64
        )
        forged = read_typed_replay_source(
            partitions=(substituted,), stream_id="eurusd", instrument_metadata=_metadata()
        )
        print(
            "missing ask : REFUSED "
            f"field={half.context.get('field')} missing={half.context.get('missing')}"
            if is_refusal(half)
            else "missing ask : ACCEPTED (wrong)"
        )
        print(
            f"bad hash    : REFUSED field={forged.context.get('field')}"
            if is_refusal(forged)
            else "bad hash    : ACCEPTED (wrong)"
        )

        problems: list[str] = []
        if is_refusal(half):
            if half.context.get("missing") != ("ask",):
                problems.append("the half-pair refusal does not name the missing ask")
        else:
            problems.append("a bid series without its ask was accepted")
        if not is_refusal(forged):
            problems.append("a partition that does not hash to its fingerprint was accepted")
        if tick_trades != pair_trades:
            problems.append("the bar pair gives different trades from the ticks")
        if tick_trades != ct10_trades:
            problems.append("the typed ticks give different trades from the CT-10 receipts")
        if len(tick_trades) != frontiers - 1:
            problems.append(f"expected {frontiers - 1} trades, got {len(tick_trades)}")
        if problems:
            for problem in problems:
                print(f"P-QMBREAD FAIL: {problem}")
            return 1
        print(
            f"P-QMBREAD PASS: {len(tick_trades)} trades equal from typed ticks, the bid/ask m1 "
            "pair and the CT-10 receipts; the half pair and the bad hash were refused"
        )
        return 0
    finally:
        if options.keep:
            print(f"kept {root}")
        else:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
