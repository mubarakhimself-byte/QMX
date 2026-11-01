"""The dictionary entry `qmx.entry/1`: its checker, its computed status and its index (A11)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import cast

from qml.catalogue.entry import EntryProblem, Status, check_entry, compute_status, corpus_problems
from qml.catalogue.index import find, match, row

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


def test_a_name_another_entry_holds_is_a_corpus_problem() -> None:
    clash = _entry("roc-of-series") | {"aliases": ["ROC", "EMA"]}

    assert [(p.where, p.message) for p in corpus_problems([_entry("ema"), clash])] == [
        ("roc-of-series@1/aliases/1", "'EMA' already names ema"),
    ]


def test_find_and_match_read_the_one_line_index() -> None:
    rows = [row(_entry(i), "implemented") for i in _ids()]

    found = [r.pin for r in find(rows, "trend filter", role="filter")]
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
