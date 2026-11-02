"""The first content wave's statistics, written as readings (A13b): goldens from arch, statsmodels
and LEAN's formulas, the minimum sample, cuts restored from state, a year of H1 inside the state
bound, the sanity series, and the reading card the entry checker reads."""

from __future__ import annotations

import json
import statistics
import time
from collections.abc import Mapping
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import cast

import pytest
from qml.blocks.api import Block, EntryFace, Instance, Signal, parse_entry
from qml.catalogue import Loaded, LockEntry, load
from qml.catalogue.entry import Health, Status, check_entry, compute_status
from qml.catalogue.index import match, row
from qml.protocol.unit import OHLC

_QML = Path(__file__).resolve().parents[1]
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_SEED = _QML / "catalogue-seed" / "wave-1" / "statistics"
_CASES_FILE = "qml/tests/golden/statistics/reference.json"
_GOLDEN = json.loads((_QML.parent / _CASES_FILE).read_text("utf-8"))
_SANITY = json.loads((_QML / "tests" / "golden" / "statistics" / "sanity.json").read_text("utf-8"))
_RELATIVE, _ABSOLUTE = 1e-9, 1e-12  # golden_tolerance's starting default (CONTRACTS.md section 9)
_GROWTH = 1.5  # update_time_growth_tolerance's starting default (QML-04)
_YEAR_OF_H1 = 52 * 5 * 24
_TIMING_RUNS = 3  # test bound: growth with history fails every run, load noise fails one


def _entry(entry_id: str) -> dict[str, object]:
    return json.loads((_STDLIB / entry_id / "1" / "entry.json").read_text("utf-8"))


def _face(entry_id: str) -> EntryFace:
    face = parse_entry((_STDLIB / entry_id / "1" / "entry.json").read_bytes())
    assert isinstance(face, EntryFace), face
    return face


def _ids() -> list[str]:
    return [
        folder.name
        for folder in sorted(_STDLIB.iterdir())
        if (folder / "1" / "entry.json").is_file()
        and cast("dict[str, object]", _entry(folder.name).get("golden") or {}).get("cases")
        == _CASES_FILE
    ]


@cache
def _blocks() -> Mapping[str, Block]:
    ids = _ids()
    lock = [LockEntry(i, 1, _face(i).fingerprint) for i in ids]
    sources = {f"{i}@1": (_STDLIB / i / "1" / "block.py").read_bytes() for i in ids}
    loaded = load(lock, sources)
    assert isinstance(loaded, Loaded), loaded
    return loaded.blocks


def _defaults(entry_id: str) -> dict[str, Decimal]:
    parameters = cast("dict[str, dict[str, str]]", _entry(entry_id)["parameters"])
    return {name: Decimal(spec["default"]) for name, spec in parameters.items()}


def _make(case: str) -> Instance:
    pin, *words = case.split()
    params = _defaults(pin.split("@", maxsplit=1)[0])
    params |= {k: Decimal(v) for k, v in (w.split("=", 1) for w in words)}
    return _blocks()[pin].make(params, {})


def _bars_block(entry_id: str) -> bool:
    return _face(entry_id).inputs[0].stream_kind == "bars"


_BARS = [{k: Decimal(v) for k, v in b.items()} for b in _GOLDEN["bars"]]
_CLOSES = [Decimal(c) for c in _GOLDEN["close"]]
_CASES = sorted(_GOLDEN["cases"])


def _feed(case: str) -> list[object]:
    return list(_BARS) if _bars_block(case.split("@", maxsplit=1)[0]) else list(_CLOSES)


def _value(output: object) -> Decimal | None:
    return output.value if isinstance(output, Signal) else cast("Decimal | None", output)


def _close(ours: Decimal | None, theirs: str | None) -> bool:
    if ours is None or theirs is None:
        return ours is None and theirs is None
    a, b = float(ours), float(theirs)
    return abs(a - b) <= max(_ABSOLUTE, _RELATIVE * abs(b))


def _card(entry: Mapping[str, object]) -> dict[str, object]:
    return cast("dict[str, object]", entry["reading"])


def test_every_statistics_block_has_a_golden_case_and_every_case_a_block() -> None:
    pins = {case.split()[0] for case in _CASES}

    assert pins == {f"{i}@1" for i in _ids()}
    assert len(pins) == 17


@pytest.mark.parametrize("case", _CASES)
def test_values_match_the_reference_and_warm_up_is_missing_not_zero(case: str) -> None:
    instance = _make(case)
    expected: list[str | None] = _GOLDEN["cases"][case]

    ours = [_value(instance.update({"series": x})) for x in _feed(case)]

    assert [
        i for i, (a, b) in enumerate(zip(ours, expected, strict=True)) if not _close(a, b)
    ] == []
    first = next(i for i, v in enumerate(ours) if v is not None)
    assert (first, ours[:first]) == (instance.warm_up_bars - 1, [None] * first)


@pytest.mark.parametrize("entry_id", _ids())
def test_below_its_minimum_sample_a_reading_is_missing_and_its_card_says_thin(
    entry_id: str,
) -> None:
    entry = _entry(entry_id)
    card = _card(entry)
    sample = cast("int", card["minimum_sample"])
    instance = _blocks()[f"{entry_id}@1"].make(_defaults(entry_id), {})
    series = list(_BARS if _bars_block(entry_id) else _CLOSES)

    below = [_value(instance.update({"series": x})) for x in series[: sample - 1]]
    at = _value(instance.update({"series": series[sample - 1]}))

    assert below == [None] * (sample - 1)
    assert at is not None
    assert (entry["min_sample"], instance.warm_up_bars) == (sample, sample)
    outputs = cast("dict[str, dict[str, str]]", card["outputs"])
    assert outputs["health"] == {"below_minimum_sample": "thin"}


def test_the_card_health_words_are_the_stamped_reading_records() -> None:
    # Part C's record, qmf/readings/record.py Health, which QML does not import.
    assert [h.value for h in Health] == ["fresh", "stale", "degraded", "thin", "shadow", "retired"]


@pytest.mark.parametrize("case", _CASES)
def test_a_cut_restored_from_exported_state_equals_the_full_run_at_20_sampled_bars(
    case: str,
) -> None:
    series = _feed(case)
    full = _make(case)
    outputs = [full.update({"series": x}) for x in series]
    samples = range(1, len(series), len(series) // 20)
    unequal: list[int] = []
    for cut in samples:
        before = _make(case)
        for x in series[:cut]:
            before.update({"series": x})
        after = _make(case)
        after.import_state(json.loads(json.dumps(before.export_state())))
        if after.update({"series": series[cut]}) != outputs[cut]:
            unequal.append(cut)

    assert (len(samples), unequal) == (20, [])
    assert sum(_value(outputs[cut]) is not None for cut in samples) >= 10


def _year(case: str) -> list[object]:
    series = _feed(case)
    return [series[i % len(series)] for i in range(_YEAR_OF_H1)]


def _replay_year(case: str) -> tuple[int, int, float, float, float]:
    instance = _make(case)
    peak = 0
    took: list[int] = []
    for x in _year(case):
        start = time.perf_counter_ns()
        instance.update({"series": x})
        took.append(time.perf_counter_ns() - start)
        peak = max(peak, instance.retained())
    settled = took[instance.warm_up_bars :]
    tenth = len(settled) // 10
    first = statistics.median(settled[:tenth]) / 1e6
    last = statistics.median(settled[-tenth:]) / 1e6
    return peak, instance.state_bound, first, last, statistics.median(settled) / 1e6


@pytest.mark.parametrize("case", sorted({c.split()[0]: c for c in _CASES}.values()))
def test_a_year_of_h1_stays_inside_the_state_bound_without_slowing(
    case: str, capsys: pytest.CaptureFixture[str]
) -> None:
    runs: list[tuple[int, int, float, float, float]] = []
    for _ in range(_TIMING_RUNS):
        runs.append(_replay_year(case))
        peak, bound, first, last, _median = runs[-1]
        assert peak <= bound
        if last <= _GROWTH * max(first, 0.001):
            break

    with capsys.disabled():
        for peak, bound, first, last, median in runs:
            print(
                f"\nperf {case} peak {peak}/{bound} median {median:.4f}ms "
                f"first {first:.4f}ms last {last:.4f}ms"
            )
    _, _, first, last, _ = runs[-1]
    assert last <= _GROWTH * max(first, 0.001)


def _reading_at_end(case: str, values: list[str]) -> float:
    instance = _make(case)
    out = [_value(instance.update({"series": Decimal(v)})) for v in values]
    assert out[-1] is not None
    return float(out[-1])


@pytest.mark.parametrize("case", sorted(_SANITY["bounds"]))
@pytest.mark.parametrize("kind", ["random_walk", "persistent", "reverting"])
def test_a_random_walk_reads_near_its_null_and_a_persistent_walk_above_it(
    case: str, kind: str
) -> None:
    low, high = (float(b) for b in _SANITY["bounds"][case][kind])

    ours = _reading_at_end(case, _SANITY["series"][kind])

    assert low <= ours <= high, (case, kind, ours)
    reference = float(_SANITY["reference_reading_at_last_bar"][case][kind])
    assert abs(ours - reference) <= max(_ABSOLUTE, _RELATIVE * abs(reference))


@pytest.mark.parametrize("moment", ["1", "2"])
def test_cusum_holds_exactly_when_a_side_passes_its_threshold(moment: str) -> None:
    case = f"cusum-change-point@1 window=100 drift=0.5 threshold=5 moment={moment}"
    instance = _make(case)

    outputs = [instance.update({"series": x}) for x in _CLOSES]

    signals = [o for o in outputs if isinstance(o, Signal)]
    assert all(s.state == (abs(cast("Decimal", s.value)) > 5) for s in signals)
    assert sum(s.state for s in signals) >= 1


def test_every_statistics_bars_block_gives_values_on_the_bars_the_unit_runtime_passes() -> None:
    fed = [
        OHLC(open=b["open"], high=b["high"], low=b["low"], close=b["close"]).fields() for b in _BARS
    ]
    silent: list[str] = []
    for entry_id in (i for i in _ids() if _bars_block(i)):
        instance = _blocks()[f"{entry_id}@1"].make(_defaults(entry_id), {})
        if all(_value(instance.update({"series": x})) is None for x in fed):
            silent.append(entry_id)

    assert silent == []


def _seed(name: str) -> dict[str, object]:
    return json.loads((_SEED / f"{name}.json").read_text("utf-8"))


def test_the_seed_statistics_compute_named_or_specified_with_hmm_and_garch_specified() -> None:
    computed = {p.stem: compute_status(_seed(p.stem)) for p in sorted(_SEED.glob("*.json"))}

    assert {name: (c.status, c.problems) for name, c in computed.items()} == {
        "arima-forecast": (Status.SPECIFIED, ()),
        "bayesian-online-change-point": (Status.SPECIFIED, ()),
        "bounce-ratio": (Status.SPECIFIED, ()),
        "cointegration-of-two-instruments": (Status.SPECIFIED, ()),
        "dispersion-across-markets": (Status.NAMED, ()),
        "garch-volatility-forecast": (Status.SPECIFIED, ()),
        "gaussian-mixture-regime": (Status.NAMED, ()),
        "hidden-markov-regime": (Status.SPECIFIED, ()),
        "markov-switching-garch": (Status.SPECIFIED, ()),
        "range-volatility-against-usual": (Status.SPECIFIED, ()),
        "shiryaev-roberts-change-point": (Status.NAMED, ()),
        "trend-against-range": (Status.NAMED, ()),
        "two-scale-realized-variance": (Status.SPECIFIED, ()),
        "volatility-state": (Status.SPECIFIED, ()),
    }


def test_the_entry_checker_names_every_problem_of_a_reading_card() -> None:
    entry = _entry("hurst-exponent")
    card = _card(entry)
    outputs = cast("dict[str, object]", card["outputs"])
    broken = entry | {
        "reading": card
        | {
            "tier": "minute",
            "minimum_sample": 999,
            "valid_classes": ["fx", "bonds"],
            "outputs": outputs
            | {
                "state": {
                    "cuts": [{"word": "low", "below": "0.6"}, {"word": "high", "below": "0.4"}]
                },
                "health": {"below_minimum_sample": "empty"},
            },
        }
    }

    problems = {p.where for p in check_entry(broken)}

    assert problems == {
        "/reading/tier",
        "/reading/valid_classes/1",
        "/reading/outputs/state/cuts/1",
        "/reading/outputs/health/below_minimum_sample",
        "/reading/minimum_sample",
    }


def test_trader_sentences_map_to_statistics_and_an_unknown_one_is_an_append_request() -> None:
    rows = [row(_entry(i), None) for i in _ids()]

    report = match(
        "The Hurst exponent rises above its middle. The variance ratio falls. "
        "The choppiness index turns high. The order book flips.",
        rows,
    )

    assert report.as_json() == {
        "sentences": [
            {"sentence": "The Hurst exponent rises above its middle", "entry": "hurst-exponent@1"},
            {"sentence": "The variance ratio falls", "entry": "variance-ratio@1"},
            {"sentence": "The choppiness index turns high", "entry": "choppiness-index@1"},
            {"sentence": "The order book flips", "entry": "unmatched"},
        ],
        "append_requests": [
            {"sentence": "The order book flips", "words": ["order", "book", "flip"]}
        ],
    }
