"""QML's stdlib blocks for the dummy unit: goldens, cuts, settle, bounds and mirrors (A4)."""

from __future__ import annotations

import json
import statistics
import time
from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import Any, cast

import pytest
from qmf.core.refusal import Ok
from qml.blocks.api import Block, EntryFace, Instance, Side, Signal, Size, parse_entry
from qml.catalogue import Loaded, LockEntry, load
from qml.numbers import InstrumentRecord, parse_record

_QML = Path(__file__).resolve().parents[1]
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_GOLDEN = json.loads((_QML / "tests" / "golden" / "talib-0.7.1.json").read_text("utf-8"))
_CLOSES = [Decimal(c) for c in _GOLDEN["close"]]
_RELATIVE, _ABSOLUTE = 1e-9, 1e-12  # golden_tolerance's starting default (CONTRACTS.md section 9)
_GROWTH = 1.5  # update_time_growth_tolerance's starting default (QML-04)
_WEEK_OF_M1 = 7 * 24 * 60
_TIMING_RUNS = 3  # test bound: growth with history fails every run, load noise fails one


def _face(entry_id: str) -> EntryFace:
    face = parse_entry((_STDLIB / entry_id / "1" / "entry.json").read_bytes())
    assert isinstance(face, EntryFace), face
    return face


@cache
def _blocks() -> Mapping[str, Block]:
    ids = [p.name for p in _STDLIB.iterdir() if (p / "1" / "block.py").is_file()]
    lock = [LockEntry(i, 1, _face(i).fingerprint) for i in ids]
    sources = {f"{i}@1": (_STDLIB / i / "1" / "block.py").read_bytes() for i in ids}
    loaded = load(lock, sources)
    assert isinstance(loaded, Loaded), loaded
    return loaded.blocks


def _make(pin: str, side: Side = Side.LONG, /, **params: str) -> Instance:
    return _blocks()[pin].make({k: Decimal(v) for k, v in params.items()}, {}, side)


def _value(output: object) -> Decimal | None:
    if isinstance(output, Signal):
        return output.value
    return cast("Decimal | None", output)


def _run(instance: Instance, series: Sequence[Decimal]) -> list[Decimal | None]:
    return [_value(instance.update({"series": x})) for x in series]


def _close(ours: Decimal | None, theirs: str | None) -> bool:
    if ours is None or theirs is None:
        return ours is None and theirs is None
    a, b = float(ours), float(theirs)
    return abs(a - b) <= max(_ABSOLUTE, _RELATIVE * abs(b))


_GOLDEN_CASES: dict[str, Callable[[], Instance]] = {
    "ema@1 period=14": lambda: _make("ema@1", period="14"),
    "ema@1 period=100": lambda: _make("ema@1", period="100"),
    "roc-of-series@1 lookback=20": lambda: _make("roc-of-series@1", lookback="20", floor="0"),
    "rsi-cross-back@1 period=14": lambda: _make("rsi-cross-back@1", period="14", level="30"),
    "percentile-of-own-history@1 percentile=20 window_bars=500 of close": lambda: _make(
        "percentile-of-own-history@1", percentile="20", window_bars="500"
    ),
    "percentile-of-own-history@1 percentile=80 window_bars=500 of close": lambda: _make(
        "percentile-of-own-history@1", percentile="80", window_bars="500"
    ),
}


@pytest.mark.parametrize("case", sorted(_GOLDEN_CASES))
def test_values_match_the_committed_golden_and_warm_up_is_missing_not_zero(case: str) -> None:
    instance = _GOLDEN_CASES[case]()
    expected: list[str | None] = _GOLDEN["cases"][case]

    ours = _run(instance, _CLOSES)

    misses = [i for i, (a, b) in enumerate(zip(ours, expected, strict=True)) if not _close(a, b)]
    assert misses == []
    first = next(i for i, v in enumerate(ours) if v is not None)
    assert ours[:first] == [None] * first
    assert first == instance.warm_up_bars - 1


_CUT_CASES: dict[str, Callable[[], Instance]] = {
    **_GOLDEN_CASES,
    "swing-stop-buffer@1 short": lambda: _make("swing-stop-buffer@1", Side.SHORT, buffer="0.0002"),
    "time-exit-bars@1": lambda: _make("time-exit-bars@1", bars="48"),
}


def _evidence(case: str, close: Decimal) -> Mapping[str, object]:
    if case.startswith("swing"):
        return {"series": {"high": close + Decimal("0.0003"), "low": close - Decimal("0.0003")}}
    return {"series": close}


@pytest.mark.parametrize("case", sorted(_CUT_CASES))
def test_a_cut_restored_from_exported_state_equals_the_full_run_at_50_sampled_bars(
    case: str,
) -> None:
    full = _CUT_CASES[case]()
    outputs = [full.update(_evidence(case, x)) for x in _CLOSES]
    samples = range(1, len(_CLOSES), len(_CLOSES) // 50)
    unequal: list[int] = []
    for cut in samples:
        before = _CUT_CASES[case]()
        for x in _CLOSES[:cut]:
            before.update(_evidence(case, x))
        after = _CUT_CASES[case]()
        after.import_state(json.loads(json.dumps(before.export_state())))
        if after.update(_evidence(case, _CLOSES[cut])) != outputs[cut]:
            unequal.append(cut)
    assert len(samples) == 50
    assert unequal == []


def _settle(make: Callable[[], Instance], tolerance: float) -> int:
    full = _run(make(), _CLOSES)
    targets = range(len(_CLOSES) - 50, len(_CLOSES), 10)
    base = make().warm_up_bars
    for multiple in range(1, len(_CLOSES) // base):
        length = base * multiple
        agree = True
        for target in targets:
            late = _run(make(), _CLOSES[target - length + 1 : target + 1])[-1]
            reference = full[target]
            assert late is not None and reference is not None
            if abs(float(late) - float(reference)) > tolerance * abs(float(reference)):
                agree = False
                break
        if agree:
            return length
    raise AssertionError("never settled inside the golden series")


@pytest.mark.parametrize(
    ("entry_id", "make"),
    [
        ("ema", lambda: _make("ema@1", period="100")),
        ("rsi-cross-back", lambda: _make("rsi-cross-back@1", period="14", level="30")),
    ],
)
def test_the_recursive_settle_length_is_the_one_recorded_in_the_entry(
    entry_id: str, make: Callable[[], Instance], capsys: pytest.CaptureFixture[str]
) -> None:
    recorded = _face(entry_id).settle
    assert recorded is not None

    found = _settle(make, float(recorded.tolerance))

    with capsys.disabled():
        print(f"\n{entry_id}@1 settle {found} bars at {dict(recorded.params)}")
    assert found == recorded.bars


def _m1_week() -> list[Decimal]:
    return [_CLOSES[i % len(_CLOSES)] for i in range(_WEEK_OF_M1)]


def _week_evidence(pin: str) -> Callable[[Decimal], Mapping[str, object]]:
    record = _record("eurusd")
    trades = [{"strength": Decimal("0.0007"), "r": Decimal("-1")}] * 10 + [
        {"strength": Decimal("0.0015"), "r": Decimal("1")}
    ] * 10
    by_pin: dict[str, Callable[[Decimal], Mapping[str, object]]] = {
        "swing-stop-buffer@1": lambda x: {"series": {"high": x, "low": x}},
        "target-r-multiple@1": lambda x: {"entry_price": x, "stop_price": x - Decimal("0.002")},
        "fixed-fraction-at-stop@1": lambda x: {
            "equity": Decimal("10000"),
            "entry_price": x,
            "stop_price": x - Decimal("0.002"),
            "record": record,
        },
        "trend-floor-from-record@1": lambda x: {"trades": trades, "current": Decimal("0")},
    }
    return by_pin.get(pin, lambda x: {"series": x})


_WEEK_MAKERS: dict[str, Callable[[], Instance]] = {
    "ema@1": lambda: _make("ema@1", period="100"),
    "roc-of-series@1": lambda: _make("roc-of-series@1", lookback="20", floor="0"),
    "rsi-cross-back@1": lambda: _make("rsi-cross-back@1", period="14", level="30"),
    "market-next-open@1": lambda: _make("market-next-open@1"),
    "swing-stop-buffer@1": lambda: _make("swing-stop-buffer@1", buffer="0.0002"),
    "target-r-multiple@1": lambda: _make("target-r-multiple@1", multiple="2"),
    "time-exit-bars@1": lambda: _make("time-exit-bars@1", bars="48"),
    "fixed-fraction-at-stop@1": lambda: _make("fixed-fraction-at-stop@1", fraction="0.005"),
    "percentile-of-own-history@1": lambda: _make(
        "percentile-of-own-history@1", percentile="20", window_bars="500"
    ),
    "trend-floor-from-record@1": lambda: _make("trend-floor-from-record@1", **_FLOOR_PARAMS),
}


def _replay_week(pin: str) -> tuple[int, int, float, float]:
    instance = _WEEK_MAKERS[pin]()
    evidence = _week_evidence(pin)
    peak = 0
    took: list[int] = []
    for x in _m1_week():
        facts = evidence(x)
        start = time.perf_counter_ns()
        instance.update(facts)
        took.append(time.perf_counter_ns() - start)
        peak = max(peak, instance.retained())
    settled = took[instance.warm_up_bars :]
    tenth = len(settled) // 10
    first = statistics.median(settled[:tenth]) / 1000
    last = statistics.median(settled[-tenth:]) / 1000
    return peak, instance.state_bound, first, last


@pytest.mark.parametrize("pin", sorted(_WEEK_MAKERS))
def test_a_week_of_m1_updates_stays_inside_the_state_bound_without_slowing(
    pin: str, capsys: pytest.CaptureFixture[str]
) -> None:
    runs: list[tuple[int, int, float, float]] = []
    for _ in range(_TIMING_RUNS):
        runs.append(_replay_week(pin))
        peak, bound, first, last = runs[-1]
        assert peak <= bound
        if last <= _GROWTH * max(first, 1.0):
            break

    with capsys.disabled():
        for peak, bound, first, last in runs:
            print(f"\n{pin} peak {peak}/{bound} first {first:.2f}us last {last:.2f}us")
    _, _, first, last = runs[-1]
    assert last <= _GROWTH * max(first, 1.0)


def test_the_short_side_mirrors_rsi_roc_and_the_swing_stop() -> None:
    path = [Decimal(v) for v in ("1", "2", "3", "4", "3", "4", "3", "2", "4")]
    long_rsi = _make("rsi-cross-back@1", Side.LONG, period="2", level="50")
    short_rsi = _make("rsi-cross-back@1", Side.SHORT, period="2", level="50")
    long_roc = _make("roc-of-series@1", Side.LONG, lookback="2", floor="0.1")
    short_roc = _make("roc-of-series@1", Side.SHORT, lookback="2", floor="0.1")
    bars = [
        ("1.10", "1.08"),
        ("1.11", "1.07"),
        ("1.12", "1.05"),
        ("1.13", "1.06"),
        ("1.14", "1.09"),
    ]
    long_stop = _make("swing-stop-buffer@1", Side.LONG, buffer="0.01")
    short_stop = _make("swing-stop-buffer@1", Side.SHORT, buffer="0.01")

    long_events = [_signal(long_rsi.update({"series": x})) for x in path]
    short_events = [_signal(short_rsi.update({"series": x})) for x in path]
    long_trend = [_signal(long_roc.update({"series": x})) for x in path]
    short_trend = [_signal(short_roc.update({"series": x})) for x in path]
    stops = [
        (long_stop.update({"series": bar}), short_stop.update({"series": bar}))
        for bar in ({"high": Decimal(h), "low": Decimal(lo)} for h, lo in bars)
    ]

    assert long_events == [None, None, False, False, False, False, False, False, True]
    assert short_events == [None, None, False, False, True, False, True, False, False]
    assert long_trend == [None, None, True, True, False, False, False, False, True]
    assert short_trend == [None, None, False, False, False, False, False, True, False]
    assert stops[-1] == (Decimal("1.0395"), None)


def _signal(output: object) -> bool | None:
    return output.state if isinstance(output, Signal) else None


def test_the_target_sits_two_r_away_on_either_side() -> None:
    target = _make("target-r-multiple@1", multiple="2")

    long_target = target.update({"entry_price": Decimal("1.1000"), "stop_price": Decimal("1.0980")})
    short_target = target.update(
        {"entry_price": Decimal("1.1000"), "stop_price": Decimal("1.1020")}
    )

    assert (long_target, short_target) == (Decimal("1.1040"), Decimal("1.0960"))


def test_the_time_exit_fires_on_the_48th_bar_held() -> None:
    exit_ = _make("time-exit-bars@1", bars="48")

    fired = [_signal(exit_.update({})) for _ in range(49)]

    assert fired.index(True) == 47


def _record(name: str) -> InstrumentRecord:
    document = json.loads(
        (_QML / "tests" / "fixtures" / "records" / f"{name}.json").read_text("utf-8")
    )
    parsed = parse_record(document)
    assert isinstance(parsed, Ok)
    return cast("Any", parsed).value


def test_the_sizer_risks_half_a_percent_at_the_stop_and_skips_below_the_minimum_lot() -> None:
    sizer = _make("fixed-fraction-at-stop@1", fraction="0.005")
    eurusd = _record("eurusd")
    trade = {"entry_price": Decimal("1.10000"), "stop_price": Decimal("1.09800"), "record": eurusd}

    sized = sizer.update({**trade, "equity": Decimal("10000")})
    odd = sizer.update({**trade, "equity": Decimal("10333")})
    small = sizer.update({**trade, "equity": Decimal("100")})

    assert sized == Size(lots=Decimal("0.25"))
    assert odd == Size(lots=Decimal("0.25"))
    assert small == Size(
        lots=None,
        skip_reason="0.0025 lots rounds down to 0.00, "
        "below icmarkets-ctrader:EURUSD@1's minimum lot of 0.01",
    )


_FLOOR_PARAMS = {
    "buckets": "5",
    "min_count": "20",
    "shrink_k": "100",
    "step_limit": "1",
    "min": "0",
    "max": "0.0030",
    "step": "0.0001",
    "default": "0",
}


def test_the_trend_floor_moves_one_step_toward_its_shrunk_edge_after_20_trades() -> None:
    rule = _make("trend-floor-from-record@1", **_FLOOR_PARAMS)
    losers = [{"strength": Decimal("0.0007"), "r": Decimal("-1")}] * 10
    winners = [{"strength": Decimal("0.0015"), "r": Decimal("1")}] * 10

    nineteen = rule.update({"trades": losers + winners[:9], "current": Decimal("0")})
    twenty = rule.update({"trades": losers + winners, "current": Decimal("0")})
    settled = rule.update({"trades": losers + winners, "current": Decimal("0.0002")})
    all_good = rule.update({"trades": winners * 2, "current": Decimal("0.0001")})

    assert nineteen is None
    assert twenty == Decimal("0.0001")
    assert settled == Decimal("0.0002")
    assert all_good == Decimal("0")


