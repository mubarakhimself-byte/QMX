"""The checker names every problem of layers A to F at once, counts first (A6)."""
# pyright: reportPrivateUsage=false

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest
from qmf.core.refusal import is_refusal
from qml.catalogue.loader import block_fingerprint
from qml.check import CheckResult, check, check_block
from qml.compile import CompileContext, CompiledUnit
from qml.door import compile as door_compile
from qml.door import explain, find, new
from qml.numbers import parse_record
from qml.unit.parse import ProblemKind
from test_compile_dummy import _context, _document

_QML = Path(__file__).resolve().parents[1]
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_TEMPLATES = _QML / "src" / "qml" / "unit" / "templates"
_CORPUS = _QML / "tests" / "corpus"

Document = dict[str, object]


def _slots(document: Document, side: str) -> dict[str, dict[str, object]]:
    logic = cast("dict[str, dict[str, dict[str, dict[str, object]]]]", document["logic"])
    return logic[side]["slots"]


def _trigger(document: Document, side: str) -> dict[str, object]:
    return cast("list[dict[str, object]]", _slots(document, side)["trigger"]["bindings"])[0]


def _numbers(document: Document) -> dict[str, dict[str, object]]:
    return cast("dict[str, dict[str, object]]", document["numbers"])


def _errors(result: CheckResult) -> set[tuple[str, str, tuple[str, ...]]]:
    return {(p.kind.value, p.layer, p.where) for p in result.errors}


# --- the dummy and three broken documents ------------------------------------------------


def test_the_dummy_checks_with_zero_errors_and_only_its_known_warnings() -> None:
    result = check(_document(), _context())

    assert result.verdict.value == "pass"
    assert result.errors == ()
    assert {(p.kind.value, p.layer, p.where) for p in result.warnings} == {
        (
            "unsettled_origin",
            "C",
            (
                "/numbers/roc_lookback/origin",
                "/numbers/min_trend_strength/origin",
                "/numbers/rsi_low/origin",
                "/numbers/rsi_high/origin",
            ),
        ),
        ("placeholder", "E", ("/exit_set/0", "/exit_set/1", "/exit_set/2", "/sizer")),
        (
            "placeholder",
            "E",
            (
                "/numbers/stop_buffer/origin",
                "/numbers/target_r/origin",
                "/numbers/time_out_bars/origin",
                "/numbers/risk_fraction/origin",
            ),
        ),
        ("no_halts", "E", ("/halts",)),
    }
    assert result.layers_run == ("A", "B", "C", "D", "E", "F")
    assert result.compiled_fingerprint is not None


def _misspelled_block() -> Document:
    document = _document()
    _trigger(document, "long")["block"] = "rsi-cross-bak@1"
    return document


def _wrong_measure() -> Document:
    document = _document()
    _numbers(document)["rsi_period"]["measure"] = "ratio"
    return document


def _no_sizer() -> Document:
    document = _document()
    del document["sizer"]
    return document


@pytest.mark.parametrize(
    ("broken", "expected"),
    [
        (
            _misspelled_block,
            ("block_not_pinned", "B", ("/logic/long/slots/trigger/bindings/0/block",)),
        ),
        (
            _wrong_measure,
            (
                "measure_mismatch",
                "C",
                (
                    "/logic/long/slots/trigger/bindings/0/params/period",
                    "/logic/short/slots/trigger/bindings/0/params/period",
                ),
            ),
        ),
        (_no_sizer, ("sizer_missing", "E", ("/sizer",))),
    ],
    ids=["layer-b", "layer-c", "layer-e"],
)
def test_each_broken_document_gives_exactly_its_one_error(
    broken: Callable[[], Document], expected: tuple[str, str, tuple[str, ...]]
) -> None:
    result = check(broken(), _context())

    assert result.verdict.value == "fail"
    assert _errors(result) == {expected}
    assert result.compiled_fingerprint is None


def test_a_near_miss_lists_the_nearest_pin() -> None:
    result = check(_misspelled_block(), _context())

    assert result.errors[0].nearest == ("rsi-cross-back@1",)
    assert result.to_json()["errors"] == [
        {
            "kind": "block_not_pinned",
            "layer": "B",
            "where": ["/logic/long/slots/trigger/bindings/0/block"],
            "message": "rsi-cross-bak@1 is not in the unit's pins",
            "hint": "pin the block's entry, or bind a pinned one",
            "nearest": ["rsi-cross-back@1"],
        }
    ]


def test_every_problem_of_every_layer_comes_back_at_once() -> None:
    document = _no_sizer()
    _trigger(document, "long")["block"] = "rsi-cross-bak@1"
    _numbers(document)["rsi_period"]["measure"] = "ratio"

    result = check(document, _context())

    assert [p.layer for p in result.errors] == ["B", "C", "E"]
    assert result.to_json()["counts"] == {"errors": 3, "warnings": 4}


def test_the_same_problem_set_twice_reports_no_progress() -> None:
    first = check(_wrong_measure(), _context())
    second = check(_wrong_measure(), _context(), previous_problem_set=first.problem_set)
    moved = check(_no_sizer(), _context(), previous_problem_set=first.problem_set)

    assert (first.no_progress, second.no_progress, moved.no_progress) == (False, True, False)


def test_a_200_problem_answer_leads_with_its_counts_and_first_errors() -> None:
    document = _document()
    numbers = _numbers(document)
    for i in range(200):
        numbers[f"spare_{i:03d}"] = {
            "kind": "fixed",
            "measure": "bars",
            "range": {"min": str(1000 + i), "max": str(i), "step": "1"},
            "default": "5",
            "motion": {"mode": "fixed"},
            "authority": "motion_inside_range",
            "origin": "published_convention",
        }

    head = check(document, _context()).text()[:2000]

    assert head.startswith('{"schema":"qmx.check/1","verdict":"fail","counts":{"errors":200,')
    assert '"where":["/numbers/spare_000/range"]' in head
    assert "the range's min 1000 is above its max 0" in head


def test_a_percent_written_in_whole_percents_warns_and_a_fraction_does_not() -> None:
    document = _document()
    _numbers(document)["stop_buffer"]["range"] = {"min": "0.1", "max": "1", "step": "0.1"}
    _numbers(document)["stop_buffer"]["default"] = "0.5"

    warned = [
        p for p in check(document, _context()).warnings if p.kind.value == "percent_looks_whole"
    ]

    assert [(p.where, p.message) for p in warned] == [
        (
            ("/numbers/stop_buffer",),
            "stop_buffer is stored as a fraction, so its default 0.5 means 50.0% and its range "
            "reaches 100%",
        )
    ]


def test_a_market_without_the_data_level_a_block_reads_is_an_error() -> None:
    context = _context()
    raw = json.loads((_QML / "tests" / "fixtures" / "records" / "eurusd.json").read_text("utf-8"))
    raw["data_levels"] = {"levels": [0], "volume": "tick_count"}
    record = parse_record(raw)
    assert not is_refusal(record)
    records = dict(context.records) | {"fx.eurusd": record.value}

    result = check(_document(), CompileContext(context.sources, context.entries, records))

    assert {p.kind.value for p in result.errors} == {"data_level_missing"}
    assert "ema@1 reads data level 1 on series, which fx.eurusd does not offer" in {
        p.message for p in result.errors
    }


def _session(calendar_ref: str) -> dict[str, object]:
    return {
        "name": calendar_ref.split("@")[0],
        "calendar_ref": calendar_ref,
        "zone": "Europe/London",
        "windows": [{"from": "08:00", "to": "16:00"}],
    }


def test_a_session_on_either_market_calendar_is_not_an_error() -> None:
    document = _document()
    document["sessions"] = [_session("fx-24x5@1"), _session("metals-24x5@1")]

    result = check(document, _context())

    assert result.errors == ()


def test_a_session_on_a_calendar_no_market_holds_is_one_error() -> None:
    document = _document()
    document["sessions"] = [_session("fx-24x5@1"), _session("crypto-24x7@1")]

    result = check(document, _context())

    assert [(p.kind.value, p.where, p.message) for p in result.errors] == [
        (
            "calendar_not_held",
            ("/sessions/1/calendar_ref",),
            "crypto-24x7@1 is not a calendar any market's record holds "
            "(fx-24x5@1, metals-24x5@1)",
        )
    ]


def test_a_pin_whose_block_source_is_missing_is_named_not_raised() -> None:
    context = _context()
    sources = {k: v for k, v in context.sources.items() if k != "ema@1"}

    result = check(_document(), CompileContext(sources, context.entries, context.records))

    assert _errors(result) == {("block_source_missing", "B", ("/pins/0",))}


# --- layer F --------------------------------------------------------------------------------

_SNEAKY = b"""import importlib

def _make(text):
    return eval(text)

def _run(text):
    exec(text)
    return __import__("math")


class _Block:
    def make(self, params, inputs, side=None):
        return None


BLOCK = _Block()
"""


def _with_block(origin: str, source: bytes = _SNEAKY) -> tuple[Document, CompileContext]:
    fp = block_fingerprint(source).value
    face = json.loads((_STDLIB / "market-next-open" / "1" / "entry.json").read_text("utf-8"))
    face |= {"entry_id": "agent-written", "origin": origin, "fingerprint": fp}
    document = _document()
    cast("list[object]", document["pins"]).append(
        {"entry_id": "agent-written", "version": 1, "fingerprint": fp}
    )
    context = _context()
    return document, CompileContext(
        dict(context.sources) | {"agent-written@1": source},
        dict(context.entries) | {"agent-written@1": json.dumps(face).encode()},
        context.records,
    )


def test_an_agent_block_that_loads_or_evaluates_code_fails_layer_f() -> None:
    document, context = _with_block("agent")

    result = check(document, context)

    assert sorted(p.message for p in result.errors) == [
        "agent-written@1 line 1: import importlib",
        "agent-written@1 line 4: uses eval",
        "agent-written@1 line 7: uses exec",
        "agent-written@1 line 8: uses __import__",
    ]
    assert {p.where for p in result.errors} == {("/pins/10",)}


def test_the_same_code_written_by_a_human_only_warns() -> None:
    document, context = _with_block("human")

    result = check(document, context)

    assert result.errors == ()
    assert sum(1 for p in result.warnings if p.kind is ProblemKind.UNSAFE_CODE) == 4


@pytest.mark.parametrize(
    ("source", "first"),
    [
        (b"getattr(__builtins__, 'exec')('y=1')\n", "uses getattr"),
        (b"getattr(__builtins__, '__im' + 'port__')('os')\n", "uses getattr"),
        (b"from builtins import exec as run\nrun('1')\n", "from builtins import"),
        (b"import builtins\nbuiltins.__dict__['exec']('1')\n", "import builtins"),
        (b"globals()['__builtins__']['eval']('1')\n", "uses globals"),
        (b"vars(__builtins__)['ev'+'al']('1')\n", "uses vars"),
        (b"import sys\nsys.modules['os'].system('x')\n", "import sys"),
        (b"().__class__.__base__.__subclasses__()\n", "uses __class__.__base__.__subclasses__"),
        (b"(x for x in ()).gi_frame.f_globals['__builtins__']\n", "uses gi_frame.f_globals"),
    ],
    ids=[
        "getattr-exec",
        "getattr-import",
        "from-builtins",
        "builtins-dict",
        "globals",
        "vars",
        "sys-modules",
        "subclasses",
        "frame-globals",
    ],
)
def test_an_agent_block_reaching_builtins_another_way_fails_layer_f(
    source: bytes, first: str
) -> None:
    agent = check_block("p@1", "agent", source)
    human = check_block("p@1", "human", source)

    assert agent.errors[0].message == f"p@1 line 1: {first}"
    assert {p.kind.value for p in agent.errors} == {"unsafe_code"}
    assert (human.errors, len(human.warnings)) == ([], len(agent.errors))


@pytest.mark.parametrize("folder", sorted(p.name for p in _STDLIB.iterdir() if p.is_dir()))
def test_every_stdlib_block_passes_layer_f_as_if_an_agent_wrote_it(folder: str) -> None:
    found = check_block(f"{folder}@1", "agent", (_STDLIB / folder / "1" / "block.py").read_bytes())

    assert found.errors == []
    assert [p for p in found.warnings if p.kind.value == "unsafe_code"] == []


def test_a_block_that_reads_the_clock_fails_whoever_wrote_it() -> None:
    clock = b"import time\n\nBLOCK = time.time()\n"
    document, context = _with_block("human", clock)

    result = check(document, context)

    assert [(p.kind.value, p.message) for p in result.errors] == [
        ("unsafe_code", "agent-written@1 line 1: import time (clock)"),
        ("unsafe_code", "agent-written@1 line 3: call time.time() (clock)"),
    ]


def test_an_agent_block_comparing_against_a_literal_warns() -> None:
    found = check_block("x@1", "agent", b"def f(x):\n    return x > 0.7 or x < 1\n")

    assert (found.errors, [p.message for p in found.warnings]) == (
        [],
        ["x@1 line 2 compares against the literal 0.7"],
    )


# --- the door -------------------------------------------------------------------------------


def test_compile_returns_the_failing_check_or_the_unit_it_checked() -> None:
    refused = door_compile(_no_sizer(), _context())
    compiled = door_compile(_document(), _context())

    assert isinstance(refused, CheckResult)
    assert _errors(refused) == {("sizer_missing", "E", ("/sizer",))}
    assert isinstance(compiled, CompiledUnit)
    assert (
        compiled.compiled_fingerprint.value == check(_document(), _context()).compiled_fingerprint
    )


def test_new_copies_the_template_with_its_overrides_and_names_bad_pointers() -> None:
    template = json.loads((_TEMPLATES / "dummy-trend-pullback.json").read_text("utf-8"))
    made = new(template, {"/unit_id": "mine", "/numbers/ema_period/default": "120"})
    refused = new(template, {"/nowhere/at/all": 1, "/unit_id": "mine"})

    assert isinstance(made, dict)
    assert (made["unit_id"], _numbers(made)["ema_period"]["default"]) == ("mine", "120")
    assert template["unit_id"] == "dummy-trend-pullback"
    assert isinstance(refused, tuple)
    assert [(p.kind.value, p.where) for p in refused] == [("unknown_field", ("/nowhere/at/all",))]


def test_find_ranks_entries_by_the_words_they_share() -> None:
    found = find("rsi trigger", _context().entries)

    assert [m.pin for m in found][:1] == ["rsi-cross-back@1"]
    assert found[0].component_type == "trigger"


def test_explain_names_what_the_unit_trades_and_its_check_counts() -> None:
    lines = explain(_document(), _context())

    assert lines[:2] == (
        "Trend pullback (dummy): buy pullbacks in an uptrend, sell rallies in a downtrend",
        "trades both on fx.eurusd, metal.xauusd",
    )
    assert lines[-1] == "check: 0 errors, 4 warnings"


# --- the corpus gate ----------------------------------------------------------------------


def _pinned(document: Document) -> Document:
    pinned = copy.deepcopy(document)
    if not pinned["pins"]:
        pinned["pins"] = _document()["pins"]
    return pinned


def _corpus() -> list[tuple[str, Document]]:
    found = [(f"template/{p.stem}", p) for p in sorted(_TEMPLATES.glob("*.json"))]
    found += [(f"corpus/{p.stem}", p) for p in sorted(_CORPUS.glob("*.json"))]
    return [(name, _pinned(json.loads(path.read_text("utf-8")))) for name, path in found]


@pytest.mark.parametrize(("name", "document"), _corpus(), ids=[n for n, _ in _corpus()])
def test_corpus_document_has_no_error(name: str, document: Document) -> None:
    result = check(document, _context())

    assert result.errors == (), f"{name}: {result.text()[:2000]}"


@pytest.mark.parametrize("folder", sorted(p.name for p in _STDLIB.iterdir() if p.is_dir()))
def test_corpus_block_has_no_error(folder: str) -> None:
    entry = json.loads((_STDLIB / folder / "1" / "entry.json").read_text("utf-8"))
    source = (_STDLIB / folder / "1" / "block.py").read_bytes()

    found = check_block(f"{folder}@1", str(entry["origin"]), source)

    assert (found.errors, entry["fingerprint"]) == ([], block_fingerprint(source).value)
