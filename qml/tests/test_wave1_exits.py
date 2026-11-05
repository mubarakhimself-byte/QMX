"""The first content wave's exits and halts (A13d): each block against its golden cases on a long
and a short run, silent with no position, the published worked examples, stops that never widen,
cuts restored from state, the halts' reasons, the grid family's failure modes,
and trader sentences mapped to entries."""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import cast

import pytest
from qml.blocks.api import (
    Block,
    EntryFace,
    Halt,
    HaltAction,
    Instance,
    OutputType,
    Scope,
    Side,
    Signal,
    parse_entry,
)
from qml.catalogue import Loaded, LockEntry, load
from qml.catalogue.index import match, row

_QML = Path(__file__).resolve().parents[1]
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_SEED = _QML / "catalogue-seed" / "wave-1" / "exits-and-halts"
_GOLDEN = json.loads(
    (_QML / "tests" / "golden" / "exits-and-halts" / "reference.json").read_text("utf-8")
)
_RELATIVE, _ABSOLUTE = Decimal("1e-9"), Decimal("1e-12")  # golden_tolerance's starting default
_EXITS = (
    "offset-gated-trailing-stop",
    "peak-holdings-giveback-exit",
    "profit-fraction-trailing-stop",
    "roi-table-exit",
    "stepped-profit-stop",
    "unrealised-profit-cap",
)
_HALTS = (
    "account-daily-loss-halt",
    "equity-drawdown-halt",
    "losing-days-halt",
    "session-fill-limit-halt",
    "session-loss-limit-halt",
)
_FAMILY = _EXITS + _HALTS
_BARS: list[dict[str, Decimal]] = [
    {k: Decimal(v) for k, v in b.items()} for b in cast("list[dict[str, str]]", _GOLDEN["bars"])
]
_STATS: list[dict[str, Decimal]] = [
    {k: Decimal(v) for k, v in s.items()}
    for s in cast("list[dict[str, str]]", _GOLDEN["statistics"])
]
_WINDOWS = [cast("tuple[int, int]", tuple(w)) for w in _GOLDEN["windows"]]
_CASES = cast("dict[str, object]", _GOLDEN["cases"])


def _entry(entry_id: str) -> dict[str, object]:
    return json.loads((_STDLIB / entry_id / "1" / "entry.json").read_text("utf-8"))


def _face(entry_id: str) -> EntryFace:
    face = parse_entry((_STDLIB / entry_id / "1" / "entry.json").read_bytes())
    assert isinstance(face, EntryFace), face
    return face


@cache
def _blocks() -> Mapping[str, Block]:
    loaded = load(
        [LockEntry(i, 1, _face(i).fingerprint) for i in _FAMILY],
        {f"{i}@1": (_STDLIB / i / "1" / "block.py").read_bytes() for i in _FAMILY},
    )
    assert isinstance(loaded, Loaded), loaded
    return loaded.blocks


def _make(case: str, side: Side = Side.LONG, **given: str) -> Instance:
    pin, *words = case.split()
    parameters = cast(
        "dict[str, dict[str, str]]", _entry(pin.split("@", maxsplit=1)[0])["parameters"]
    )
    params = {name: Decimal(spec["default"]) for name, spec in parameters.items()}
    params |= {k: Decimal(v) for k, v in (w.split("=", 1) for w in words)}
    params |= {k: Decimal(v) for k, v in given.items()}
    return _blocks()[pin].make(params, {}, side)


def _entry_at(t: int) -> Decimal | None:
    first = next((a for a, b in _WINDOWS if a <= t <= b), None)
    return None if first is None else _BARS[first - 1]["close"]


def _evidence(t: int) -> dict[str, object]:
    entry = _entry_at(t)
    evidence: dict[str, object] = {"series": _BARS[t]}
    return evidence if entry is None else evidence | {"entry_price": entry}


def _plain(answer: object) -> object:
    if isinstance(answer, Signal):
        return [answer.state, answer.value]
    if isinstance(answer, Halt):
        return f"{answer.action.value} {answer.scope.value}"
    return answer


def _close(ours: object, theirs: object) -> bool:
    if isinstance(theirs, list):
        pair = cast("list[object]", theirs)
        if not isinstance(ours, list):
            return False
        mine = cast("list[object]", ours)
        return mine[0] == pair[0] and _close(mine[1], pair[1])
    if ours is None or theirs is None:
        return ours is None and theirs is None
    if not isinstance(ours, Decimal) or not isinstance(theirs, str):
        return ours == theirs
    expected = Decimal(theirs)
    return abs(ours - expected) <= max(_ABSOLUTE, _RELATIVE * abs(expected))


def _exit_cases() -> list[tuple[str, str]]:
    return [
        (case, side)
        for case in sorted(_CASES)
        if case.split("@")[0] in _EXITS
        for side in ("long", "short")
    ]


def _halt_cases() -> list[str]:
    return sorted(case for case in _CASES if case.split("@")[0] in _HALTS)


def test_every_exit_and_halt_block_has_golden_cases_and_every_case_a_block() -> None:
    families = {
        i: _entry(i)["component_type"]
        for i in sorted(f.name for f in _STDLIB.iterdir())
        if "exits-and-halts" in cast("str", _entry(i).get("tests", ""))
    }

    assert families == dict.fromkeys(_EXITS, "exit") | dict.fromkeys(_HALTS, "halt")
    assert {case.split()[0] for case in _CASES} == {f"{i}@1" for i in _FAMILY}


@pytest.mark.parametrize(("case", "side"), _exit_cases())
def test_an_exit_matches_its_reference_on_a_long_and_a_short_run(case: str, side: str) -> None:
    instance = _make(case, Side(side))
    expected = cast("dict[str, list[object]]", _CASES[case])[side]

    ours = [_plain(instance.update(_evidence(t))) for t in range(len(_BARS))]

    assert [
        t for t, (a, b) in enumerate(zip(ours, expected, strict=True)) if not _close(a, b)
    ] == []
    assert [t for t, a in enumerate(ours) if a is not None and _entry_at(t) is None] == []


@pytest.mark.parametrize("case", _halt_cases())
def test_a_halt_matches_its_reference(case: str) -> None:
    instance = _make(case)
    expected = cast("list[str | None]", _CASES[case])

    ours = [_plain(instance.update(s)) for s in _STATS]

    assert ours == expected
    assert any(v is not None for v in ours)


@pytest.mark.parametrize("entry_id", _EXITS)
def test_an_exit_answers_only_for_a_position_it_is_given_and_forgets_it_after(
    entry_id: str,
) -> None:
    long, short = _make(f"{entry_id}@1", Side.LONG), _make(f"{entry_id}@1", Side.SHORT)
    up = {"open": Decimal(100), "high": Decimal(160), "low": Decimal(100), "close": Decimal(150)}
    down = {"open": Decimal(100), "high": Decimal(100), "low": Decimal(40), "close": Decimal(50)}

    none = [long.update({"series": up}), short.update({"series": down})]
    given = [
        long.update({"series": up, "entry_price": Decimal(100)}),
        short.update({"series": down, "entry_price": Decimal(100)}),
    ]
    after = [long.update({"series": up}), short.update({"series": down})]

    assert none == after == [None, None]
    assert all(g is not None for g in given), given
    assert (long.retained(), short.retained()) == (0, 0)


_POSITION_HELD = (
    "profit-fraction-trailing-stop",
    "offset-gated-trailing-stop",
    "stepped-profit-stop",
    "peak-holdings-giveback-exit",
    "roi-table-exit",
)


@pytest.mark.parametrize("entry_id", _POSITION_HELD)
def test_a_new_entry_price_starts_a_new_position_with_no_flat_bar_between(entry_id: str) -> None:
    def walk(entry: str, prices: tuple[str, ...], long: bool) -> list[dict[str, object]]:
        def at(p: str) -> Decimal:
            return Decimal(p) if long else 200 - Decimal(p)

        bars = [dict.fromkeys(("open", "high", "low", "close"), at(p)) for p in prices]
        return [{"series": b, "entry_price": at(entry)} for b in bars]

    for side in (Side.LONG, Side.SHORT):
        long = side is Side.LONG
        first = walk("100", ("110", "130", "150", *["148"] * 20), long)
        second = walk("100.5", ("101", "104", "110", "125", "122"), long)
        carried, fresh = _make(f"{entry_id}@1", side), _make(f"{entry_id}@1", side)
        for evidence in first:
            carried.update(evidence)

        answers = [carried.update(e) for e in second]
        expected = [fresh.update(e) for e in second]

        assert answers == expected, side
        assert any(a is not None for a in expected), side


def test_the_published_worked_examples_hold() -> None:
    def bar(high: str, low: str, close: str) -> dict[str, object]:
        return {
            "series": {
                "open": Decimal(close),
                "high": Decimal(high),
                "low": Decimal(low),
                "close": Decimal(close),
            },
            "entry_price": Decimal(100),
        }

    gated = _make("offset-gated-trailing-stop@1")
    fraction = _make("profit-fraction-trailing-stop@1")
    stepped = _make("stepped-profit-stop@1")
    roi = _make("roi-table-exit@1")
    cap = _make("unrealised-profit-cap@1")
    giveback = _make("peak-holdings-giveback-exit@1")

    assert [gated.update(bar(h, "100", h)) for h in ("102", "103", "101")] == [
        None,
        Decimal("100.94"),
        Decimal("100.94"),
    ]
    assert [fraction.update(bar(h, "100", h)) for h in ("103.99", "104", "112", "105")] == [
        None,
        Decimal("101.400"),
        Decimal("106.400"),
        Decimal("106.400"),
    ]
    assert [stepped.update(bar(h, "100", h)) for h in ("120", "121", "126", "141", "122")] == [
        None,
        Decimal("107.00"),
        Decimal("115.00"),
        Decimal("125.00"),
        Decimal("125.00"),
    ]
    held = [cast("Signal", roi.update(bar("103", "100", "103"))).state for _ in range(21)]
    assert held[:20] == [False] * 20
    assert held[20] is True
    assert [cap.update(bar(c, "100", c)) for c in ("105", "105.01")] == [
        Signal(state=False, value=Decimal("0.05")),
        Signal(state=True, value=Decimal("0.0501")),
    ]
    assert [giveback.update(bar(c, "90", c)) for c in ("110", "104.5", "104.49")] == [
        Signal(state=False, value=Decimal("0")),
        Signal(state=False, value=Decimal("0.05")),
        Signal(state=True, value=Decimal("0.0500909090909")),
    ]


@pytest.mark.parametrize(
    "case",
    [
        "offset-gated-trailing-stop@1",
        "profit-fraction-trailing-stop@1",
        "stepped-profit-stop@1 lock_1=0 lock_2=0.05 trigger_1=0.05 trigger_2=0.1",
    ],
)
def test_a_trailing_stop_never_widens_inside_a_position(case: str) -> None:
    widened: list[tuple[str, int]] = []
    tightened = {Side.LONG: 0, Side.SHORT: 0}
    for side in (Side.LONG, Side.SHORT):
        instance = _make(case, side)
        before: Decimal | None = None
        for t in range(len(_BARS)):
            level = cast("Decimal | None", instance.update(_evidence(t)))
            if _entry_at(t) is None:
                before = None
                continue
            if before is not None and (
                level is None or (level < before if side is Side.LONG else level > before)
            ):
                widened.append((side.value, t))
            if before is not None and level is not None and level != before:
                tightened[side] += 1
            before = level if level is not None else before

    assert widened == []
    assert min(tightened.values()) > 0, tightened
    assert _face(case.split("@")[0]).output.type is OutputType.LEVEL


@pytest.mark.parametrize("entry_id", _FAMILY)
def test_a_cut_restored_from_exported_state_equals_the_full_run_and_stays_in_bound(
    entry_id: str,
) -> None:
    feed = list(_STATS) if entry_id in _HALTS else [_evidence(t) for t in range(len(_BARS))]
    samples = range(1, len(feed), len(feed) // 20)
    unequal: list[tuple[str, int]] = []
    answered = 0
    for side in (Side.LONG, Side.SHORT):
        full = _make(f"{entry_id}@1", side)
        outputs: list[object] = []
        for evidence in feed:
            outputs.append(full.update(evidence))
            assert full.retained() <= full.state_bound
        for cut in samples:
            before = _make(f"{entry_id}@1", side)
            for evidence in feed[:cut]:
                before.update(evidence)
            after = _make(f"{entry_id}@1", side)
            after.import_state(json.loads(json.dumps(before.export_state())))
            if after.update(feed[cut]) != outputs[cut]:
                unequal.append((side.value, cut))
        answered += sum(outputs[cut] is not None for cut in samples)

    assert unequal == []
    assert answered >= 4


def test_a_halt_names_what_it_does_its_scope_and_why() -> None:
    answers = [
        _make("session-loss-limit-halt@1").update({"session_loss_r": Decimal("-3.5")}),
        _make("losing-days-halt@1").update({"losing_day_streak": 3}),
        _make("session-fill-limit-halt@1").update({"session_fills": 21}),
        _make("account-daily-loss-halt@1").update(
            {"equity": Decimal(9400), "day_start_equity": Decimal(10000)}
        ),
    ]
    drawdown = _make("equity-drawdown-halt@1")
    answers += [drawdown.update({"equity": Decimal(e)}) for e in ("10000", "9600", "9400", "10500")]

    assert answers == [
        Halt(HaltAction.FLATTEN, Scope.UNIT, "lost 3.5R this session, at or past the 3R limit"),
        Halt(HaltAction.FLATTEN, Scope.UNIT, "3 losing days in a row, at or past the limit of 3"),
        Halt(HaltAction.FLATTEN, Scope.UNIT, "21 fills this session, above the limit of 20"),
        Halt(
            HaltAction.FLATTEN,
            Scope.ACCOUNT,
            "the account is down 0.06 today, at or past the 0.05 limit",
        ),
        None,
        None,
        Halt(
            HaltAction.FLATTEN,
            Scope.ACCOUNT,
            "equity 9400 is 0.06 below its base 10000, past the 0.05 drawdown limit",
        ),
        Halt(
            HaltAction.FLATTEN,
            Scope.ACCOUNT,
            "equity 9400 is 0.06 below its base 10000, past the 0.05 drawdown limit",
        ),
    ]
    assert _make("session-loss-limit-halt@1").update({"session_loss_r": Decimal(-2)}) is None


def _seeds() -> dict[str, dict[str, object]]:
    return {p.stem: json.loads(p.read_text("utf-8")) for p in sorted(_SEED.glob("*.json"))}


@pytest.mark.parametrize(
    "entry_id",
    [
        "anti-martingale-sizing",
        "averaging-down",
        "grid-of-orders",
        "grid-take-profit-at-average-price",
        "martingale-sizing",
        "zone-recovery-hedge",
    ],
)
def test_a_grid_martingale_or_averaging_entry_states_its_known_failure_with_a_source(
    entry_id: str,
) -> None:
    entry = _seeds()[entry_id]
    sources = cast("list[dict[str, str]]", entry["sources"])

    assert cast("str", entry["boundaries"]).startswith("Known failure: ")
    assert len(sources) == 2
    assert all(s["quote"] and s["dated"] for s in sources)


def test_trader_sentences_map_to_exit_and_halt_entries_and_an_unknown_one_is_an_append_request() -> (
    None
):
    rows = [row(e, None) for e in [*_seeds().values(), *(_entry(i) for i in _FAMILY)]]

    report = match(
        "The minimal ROI is reached. The equity kill switch trips. "
        "The max intraday loss is hit. The triple barrier is touched. "
        "Martingale doubles the lot. The vanna exposure decays.",
        rows,
    )

    assert report.as_json() == {
        "sentences": [
            {"sentence": "The minimal ROI is reached", "entry": "roi-table-exit@1"},
            {"sentence": "The equity kill switch trips", "entry": "equity-drawdown-halt@1"},
            {"sentence": "The max intraday loss is hit", "entry": "session-loss-limit-halt@1"},
            {"sentence": "The triple barrier is touched", "entry": "triple-barrier-exit@1"},
            {"sentence": "Martingale doubles the lot", "entry": "martingale-sizing@1"},
            {"sentence": "The vanna exposure decays", "entry": "unmatched"},
        ],
        "append_requests": [
            {"sentence": "The vanna exposure decays", "words": ["vanna", "exposure", "decay"]}
        ],
    }
