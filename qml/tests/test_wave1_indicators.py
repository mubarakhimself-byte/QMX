"""The first content wave's indicator blocks (A13a): TA-Lib goldens, missing warm-up, cuts
restored from state, bounded state over a week of updates, and the session reset."""

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
from qml.catalogue.index import match, row

_QML = Path(__file__).resolve().parents[1]
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_GOLDEN = json.loads(
    (_QML / "tests" / "golden" / "indicators" / "talib-0.7.1.json").read_text("utf-8")
)
_RELATIVE, _ABSOLUTE = 1e-9, 1e-12  # golden_tolerance's starting default (CONTRACTS.md section 9)
_GROWTH = 1.5  # update_time_growth_tolerance's starting default (QML-04)
_WEEK_OF_M1 = 7 * 24 * 60
_TIMING_RUNS = 3  # test bound: growth with history fails every run, load noise fails one
_BAR_NS = 15 * 60 * 10**9


def _bar(row: Mapping[str, object], shift_ns: int = 0) -> dict[str, object]:
    return {
        k: cast("int", v) + shift_ns if k == "time" else Decimal(str(v)) for k, v in row.items()
    }


_BARS = [_bar(row) for row in _GOLDEN["bars"]]
_CLOSES = [Decimal(c) for c in _GOLDEN["close"]]


def _face(entry_id: str) -> EntryFace:
    face = parse_entry((_STDLIB / entry_id / "1" / "entry.json").read_bytes())
    assert isinstance(face, EntryFace), face
    return face


def _wave_ids() -> list[str]:
    found: list[str] = []
    for folder in sorted(_STDLIB.iterdir()):
        face = folder / "1" / "entry.json"
        if face.is_file():
            entry = cast("dict[str, object]", json.loads(face.read_text("utf-8")))
            golden = cast("dict[str, object]", entry.get("golden") or {})
            if golden.get("cases") == "qml/tests/golden/indicators/talib-0.7.1.json":
                found.append(folder.name)
    return found


@cache
def _blocks() -> Mapping[str, Block]:
    ids = _wave_ids()
    lock = [LockEntry(i, 1, _face(i).fingerprint) for i in ids]
    sources = {f"{i}@1": (_STDLIB / i / "1" / "block.py").read_bytes() for i in ids}
    loaded = load(lock, sources)
    assert isinstance(loaded, Loaded), loaded
    return loaded.blocks


def _make(case: str) -> Instance:
    pin, *words = case.split()
    params = dict(w.split("=", 1) for w in words)
    return _blocks()[pin].make({k: Decimal(v) for k, v in params.items()}, {})


def _feed(case: str) -> list[object]:
    entry_id = case.split("@", maxsplit=1)[0]
    return list(_BARS) if _face(entry_id).inputs[0].stream_kind == "bars" else list(_CLOSES)


def _warm_up_rule(case: str) -> str:
    entry = (_STDLIB / case.split("@", maxsplit=1)[0] / "1" / "entry.json").read_text("utf-8")
    return str(cast("dict[str, dict[str, object]]", json.loads(entry))["warm_up"]["rule"])


def _value(output: object) -> Decimal | None:
    return output.value if isinstance(output, Signal) else cast("Decimal | None", output)


def _close(ours: Decimal | None, theirs: str | None) -> bool:
    if ours is None or theirs is None:
        return ours is None and theirs is None
    a, b = float(ours), float(theirs)
    return abs(a - b) <= max(_ABSOLUTE, _RELATIVE * abs(b))


_CASES = sorted(_GOLDEN["cases"])


def test_every_wave_block_has_a_golden_case_and_every_case_a_block() -> None:
    pins = {case.split()[0] for case in _CASES}

    assert pins == {f"{i}@1" for i in _wave_ids()}


@pytest.mark.parametrize("case", _CASES)
def test_values_match_the_golden_and_warm_up_is_missing_not_zero(case: str) -> None:
    instance = _make(case)
    expected: list[str | None] = _GOLDEN["cases"][case]

    ours = [_value(instance.update({"series": x})) for x in _feed(case)]

    misses = [i for i, (a, b) in enumerate(zip(ours, expected, strict=True)) if not _close(a, b)]
    assert misses == []
    first = next(i for i, v in enumerate(ours) if v is not None)
    assert ours[:first] == [None] * first
    if "confirmed" in _warm_up_rule(case):
        assert first >= instance.warm_up_bars - 1
    else:
        assert first == instance.warm_up_bars - 1


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
    assert len(samples) == 20
    assert unequal == []


def _week(case: str) -> list[object]:
    if _face(case.split("@", maxsplit=1)[0]).inputs[0].stream_kind != "bars":
        return [_CLOSES[i % len(_CLOSES)] for i in range(_WEEK_OF_M1)]
    loop = len(_BARS) * _BAR_NS
    rows = _GOLDEN["bars"]
    return [_bar(rows[i % len(rows)], (i // len(rows)) * loop) for i in range(_WEEK_OF_M1)]


def _replay_week(case: str) -> tuple[int, int, float, float]:
    instance = _make(case)
    peak = 0
    took: list[int] = []
    for x in _week(case):
        start = time.perf_counter_ns()
        instance.update({"series": x})
        took.append(time.perf_counter_ns() - start)
        peak = max(peak, instance.retained())
    settled = took[instance.warm_up_bars :]
    tenth = len(settled) // 10
    first = statistics.median(settled[:tenth]) / 1000
    last = statistics.median(settled[-tenth:]) / 1000
    return peak, instance.state_bound, first, last


@pytest.mark.parametrize("case", sorted({c.split()[0]: c for c in _CASES}.values()))
def test_a_week_of_updates_stays_inside_the_state_bound_without_slowing(
    case: str, capsys: pytest.CaptureFixture[str]
) -> None:
    runs: list[tuple[int, int, float, float]] = []
    for _ in range(_TIMING_RUNS):
        runs.append(_replay_week(case))
        peak, bound, first, last = runs[-1]
        assert peak <= bound
        if last <= _GROWTH * max(first, 1.0):
            break

    with capsys.disabled():
        for peak, bound, first, last in runs:
            print(f"\n{case} peak {peak}/{bound} first {first:.2f}us last {last:.2f}us")
    _, _, first, last = runs[-1]
    assert last <= _GROWTH * max(first, 1.0)


def test_metatrader_sentences_map_to_wave_entries_and_an_unknown_one_is_an_append_request() -> None:
    rows = [
        row(json.loads((_STDLIB / i / "1" / "entry.json").read_text("utf-8")), None)
        for i in _wave_ids()
    ]

    report = match(
        "Parabolic SAR flips below price. Williams %R rises above -20. "
        "The Awesome Oscillator crosses zero. Price sweeps the Asian high.",
        rows,
    )

    assert report.as_json() == {
        "sentences": [
            {"sentence": "Parabolic SAR flips below price", "entry": "parabolic-sar@1"},
            {"sentence": "Williams %R rises above -20", "entry": "williams-percent-r@1"},
            {"sentence": "The Awesome Oscillator crosses zero", "entry": "awesome-oscillator@1"},
            {"sentence": "Price sweeps the Asian high", "entry": "unmatched"},
        ],
        "append_requests": [
            {
                "sentence": "Price sweeps the Asian high",
                "words": ["price", "sweep", "asian", "high"],
            }
        ],
    }

