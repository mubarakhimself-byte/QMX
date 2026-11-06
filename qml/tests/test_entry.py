"""The dictionary entry `qmx.entry/1`: its checker, its computed status and its index (A11)."""

from __future__ import annotations

import copy
import json
from decimal import Decimal
from pathlib import Path
from typing import cast

from qml.blocks.api import EntryFace, parse_entry
from qml.catalogue.entry import EntryProblem, Status, check_entry, compute_status, corpus_problems
from qml.catalogue.index import find, match, row
from qml.catalogue.loader import block_fingerprint

_QML = Path(__file__).resolve().parents[1]
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_GOLDEN = json.loads((_QML / "tests" / "golden" / "talib-0.7.1.json").read_text("utf-8"))

Entry = dict[str, object]


def _entry(entry_id: str) -> Entry:
    return cast("Entry", json.loads((_STDLIB / entry_id / "1" / "entry.json").read_text("utf-8")))


def _source(entry_id: str) -> bytes:
    return (_STDLIB / entry_id / "1" / "block.py").read_bytes()


def _ids() -> list[str]:
    return sorted(p.name for p in _STDLIB.iterdir() if (p / "1" / "entry.json").is_file())


def test_an_entry_claiming_native_with_no_source_is_refused_with_the_reason() -> None:
    entry = _entry("ema") | {"transfer": {"fx": "native"}}
    del entry["sources"]

    assert check_entry(entry) == (
        EntryProblem(
            "/transfer/fx",
            "fx is claimed native with no source",
            "cite a source with its exact quote and date, or claim not_assessed",
        ),
    )
    assert compute_status(entry, _source("ema"), _GOLDEN).status is None


def test_an_unknown_role_names_the_nearest_roles() -> None:
    entry = _entry("rsi-cross-back") | {"eligible_roles": ["triger"]}

    assert check_entry(entry) == (
        EntryProblem(
            "/eligible_roles/0",
            "'triger' is not a role; the nearest are trigger, sizer, filter",
            "use a role from the roles table",
        ),
    )


def test_a_market_input_needs_its_data_level_and_a_fallback_its_expected_loss() -> None:
    entry = _entry("ema")
    entry["inputs"] = [
        {"port": "series", "stream_kind": "series", "measure": "price"},
        {"port": "flow", "stream_kind": "tape", "data_level": 4, "fallback": [{"data_level": 2}]},
    ]

    assert [(p.where, p.message) for p in check_entry(entry)] == [
        ("/inputs/0/data_level", "an input from market data has no data level"),
        ("/inputs/1/fallback/0/expected_loss", "a fallback has no expected-loss label"),
    ]


def test_a_warm_up_value_of_zero_instead_of_missing_keeps_the_block_specified() -> None:
    golden = copy.deepcopy(_GOLDEN)
    golden["cases"]["ema@1 period=14"][0] = "0"

    computed = compute_status(_entry("ema"), _source("ema"), golden)

    assert (computed.status, [p.message for p in computed.problems]) == (
        Status.SPECIFIED,
        ["ema@1 period=14 differs from its golden values at 1 bars, first 0"],
    )


def test_an_entry_the_compiler_cannot_read_stays_specified_with_the_compiler_problem() -> None:
    entry = _entry("ema") | {"settle_bars": {"bars": 3}}

    computed = compute_status(entry, _source("ema"), _GOLDEN)

    assert (computed.status, computed.problems) == (
        Status.SPECIFIED,
        (
            EntryProblem(
                "/settle_bars/params", "expected an object", "the compiler reads this face"
            ),
        ),
    )


def test_an_entry_with_only_its_trader_face_saves_as_named() -> None:
    entry: Entry = {
        "schema": "qmx.entry/1",
        "entry_id": "asian-range-sweep",
        "version": 1,
        "component_type": "trigger",
        "origin": "port-239",
        "definition": "Price trades beyond the Asian session's range and closes back inside it.",
        "eligible_roles": ["trigger", "setup"],
        "sources": [
            {"source_ref": "stats/triggers.md", "quote": "sweep of Asia", "dated": "2026-08-26"}
        ],
    }

    computed = compute_status(entry)

    assert check_entry(entry) == ()
    assert (computed.status, computed.missing) == (
        Status.NAMED,
        (
            "machine face: inputs",
            "machine face: output",
            "machine face: parameters",
            "machine face: warm_up",
            "machine face: transfer",
            "machine face: mirroring",
        ),
    )


_AGENT_EMA = b'''"""An agent's recursive average, which forgets its start only slowly."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _Average:
    __slots__ = ("_alpha", "_value")

    def __init__(self, period: int) -> None:
        self._alpha = 2.0 / (period + 1)
        self._value: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return 1

    @property
    def state_bound(self) -> int:
        return 1

    def retained(self) -> int:
        return 1

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        now = float(price)
        before = now if self._value is None else self._value
        self._value = before + self._alpha * (now - before)
        return quantise(self._value)

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Average:
        return _Average(int(params["period"]))


BLOCK = _Block()
'''


def _agent_entry(**more: object) -> Entry:
    return {
        "schema": "qmx.entry/1",
        "entry_id": "agents-average",
        "version": 1,
        "component_type": "indicator",
        "origin": "agent",
        "definition": "An agent's own recursive average of the close.",
        "sources": [{"source_ref": "a note", "quote": "its words", "dated": "2026-11-06"}],
        "inputs": [
            {"port": "series", "stream_kind": "series", "measure": "price", "data_level": 1}
        ],
        "output": {"type": "series", "measure": "price"},
        "parameters": {
            "period": {"measure": "bars", "default": "20", "origin": "builder_chosen"},
        },
        "warm_up": {"rule": "1", "bars": 1},
        "transfer": {"fx": "not_assessed"},
        "mirroring": "not_applicable",
        "fingerprint": block_fingerprint(_AGENT_EMA).value,
    } | more


def test_an_agent_block_with_no_golden_is_not_implemented() -> None:
    settled = {"params": {"period": "20"}, "bars": 400, "tolerance": "1e-9", "scales_by": "period"}

    computed = compute_status(_agent_entry(settle_bars=settled), _AGENT_EMA)
    ours = compute_status(_agent_entry(settle_bars=settled, origin="qml"), _AGENT_EMA)

    assert (computed.status, computed.problems, computed.missing) == (
        Status.SPECIFIED,
        (),
        ("implementation: golden cases for its cut-against-full run",),
    )
    assert (ours.status, ours.missing) == (Status.IMPLEMENTED, ())


def test_an_unsettled_block_fails_check_entry() -> None:
    too_short = {"params": {"period": "20"}, "bars": 5, "tolerance": "1e-9", "scales_by": "period"}
    long_enough = too_short | {"bars": 400}

    assert [(p.where, p.message) for p in check_entry(_agent_entry(), _AGENT_EMA)] == [
        (
            "/settle_bars",
            "agents-average@1 has not settled by bar 1: a run started there differs from a long "
            "run by more than 1E-9",
        ),
    ]
    assert [
        (p.where, p.message) for p in check_entry(_agent_entry(settle_bars=too_short), _AGENT_EMA)
    ] == [
        (
            "/settle_bars/bars",
            "agents-average@1 has not settled by bar 5: a run started there differs from a long "
            "run by more than 1E-9",
        ),
    ]
    assert check_entry(_agent_entry(settle_bars=long_enough), _AGENT_EMA) == ()
    assert compute_status(_agent_entry(settle_bars=too_short), _AGENT_EMA).status is None
    assert check_entry(_agent_entry(settle_bars=too_short)) == ()


def test_a_block_whose_code_raises_still_gets_an_answer() -> None:
    raising = _AGENT_EMA.replace(b"return quantise(self._value)", b"return quantise([][7])")
    stated = block_fingerprint(raising).value
    cases = {"close": ["1", "2"], "cases": {"agents-average@1 period=20": [None, None]}}

    no_golden = compute_status(_agent_entry(fingerprint=stated), raising)
    declared = {"reference": "a note", "cases": "its-cases.json"}
    golden = compute_status(_agent_entry(fingerprint=stated, golden=declared), raising, cases)

    assert (no_golden.status, no_golden.problems, no_golden.missing) == (
        Status.SPECIFIED,
        (),
        ("implementation: golden cases for its cut-against-full run",),
    )
    assert (golden.status, [(p.where, p.message) for p in golden.problems]) == (
        Status.SPECIFIED,
        [("/golden", "agents-average@1 period=20 does not run: list index out of range")],
    )


def test_a_settle_row_scales_with_the_parameter_it_names() -> None:
    row = {"params": {"period": "14"}, "bars": 285, "tolerance": "1e-9", "scales_by": "period"}

    face = parse_entry(json.dumps(_entry("rsi-series") | {"settle_bars": row}).encode())

    assert isinstance(face, EntryFace)
    assert face.settle is not None
    assert [face.settle.bars_at({"period": Decimal(p)}) for p in ("14", "28", "7", "15")] == [
        285,
        570,
        143,
        306,
    ]
    assert face.settle.bars_at({}) == 285
    assert [
        (p.where, p.message)
        for p in check_entry(_entry("ema") | {"settle_bars": row | {"scales_by": "fast"}})
    ] == [("/settle_bars/scales_by", "scales_by is one of its params, not 'fast'")]


def test_every_link_names_an_entry_the_corpus_holds() -> None:
    port = json.loads(
        (_QML / "catalogue-seed" / "stats-2026-08-26" / "port.json").read_text("utf-8")
    )
    corpus = [
        *(r["fields"]["entry"] for r in port["drafts"]),
        *(json.loads(p.read_text("utf-8")) for p in _STDLIB.glob("*/*/entry.json")),
        *(
            json.loads(p.read_text("utf-8"))
            for p in (_QML / "catalogue-seed" / "wave-1").glob("*/*.json")
        ),
    ]
    held = {f"{e['entry_id']}@{e['version']}" for e in corpus}

    links = {pin for e in corpus for pin in cast("list[str]", e.get("same_word_as") or [])}

    assert sorted(links - held) == []
    assert "session-high@1" in links


def test_a_name_another_entry_holds_is_a_corpus_problem() -> None:
    clash = _entry("roc-of-series") | {"aliases": ["ROC", "EMA"]}

    assert [(p.where, p.message) for p in corpus_problems([_entry("ema"), clash])] == [
        ("roc-of-series@1/aliases/1", "'EMA' already names ema"),
    ]


_DUMMY_BLOCKS = (
    "ema",
    "fixed-fraction-at-stop",
    "market-next-open",
    "percentile-of-own-history",
    "roc-of-series",
    "rsi-cross-back",
    "swing-stop-buffer",
    "target-r-multiple",
    "time-exit-bars",
    "trend-floor-from-record",
)


def test_find_and_match_read_the_one_line_index() -> None:
    rows = [row(_entry(i), "implemented") for i in _ids()]

    dummy = [row(_entry(i), "implemented") for i in _DUMMY_BLOCKS]
    found = [r.pin for r in find(dummy, "trend filter", role="filter")]
    report = match(
        "RSI crosses back above 30. Price sweeps the Asian high and closes back in.", rows
    )

    assert found == ["roc-of-series@1", "ema@1"]
    assert report.as_json() == {
        "sentences": [
            {"sentence": "RSI crosses back above 30", "entry": "rsi-cross-back@1"},
            {"sentence": "Price sweeps the Asian high and closes back in", "entry": "unmatched"},
        ],
        "append_requests": [
            {
                "sentence": "Price sweeps the Asian high and closes back in",
                "words": ["price", "sweep", "asian", "high", "close", "back"],
            }
        ],
    }
