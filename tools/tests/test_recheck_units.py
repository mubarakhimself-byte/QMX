"""The re-check script marks exactly the verdicts a changed rule touches (A10, UT-03)."""

from __future__ import annotations

import dataclasses
import importlib.util
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, cast

import pytest
from qmf.core.refusal import TypedRefusal
from qml.blocks.api import EntryFace, parse_entry
from qml.check import check
from qml.check.result import problem_set
from qml.compile import CompileContext
from qml.numbers import InstrumentRecord, parse_record
from qml.unit.parse import Problem, ProblemKind

_ROOT = Path(__file__).resolve().parents[2]
_QML = _ROOT / "qml"
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_RECORDS = _QML / "tests" / "fixtures" / "records"
_OLD = "qml-check/1 fp1:sha256:the-checker-before-the-rule-change"
_UNITS = (
    "dummy-trend-pullback",
    "twin-exits-unfired",
    "twin-one-side-only",
    "twin-signal-constant",
)


class _Script(Protocol):
    def main(self, argv: Sequence[str] | None = None) -> int: ...


def _script() -> _Script:
    spec = importlib.util.spec_from_file_location(
        "recheck_units", _ROOT / "tools" / "qml" / "recheck_units.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast("_Script", module)


def _documents() -> dict[str, dict[str, object]]:
    pins: list[dict[str, object]] = []
    for entry in sorted(_STDLIB.glob("*/*/entry.json")):
        face = parse_entry(entry.read_bytes())
        assert isinstance(face, EntryFace), face
        pins.append(
            {"entry_id": face.entry_id, "version": face.version, "fingerprint": face.fingerprint}
        )
    paths = [_QML / "src" / "qml" / "unit" / "templates" / "dummy-trend-pullback.json"]
    paths += sorted((_QML / "tests" / "corpus").glob("*.json"))
    documents = {p.stem: cast("dict[str, object]", json.loads(p.read_text("utf-8"))) for p in paths}
    return {name: d | {"pins": pins} for name, d in documents.items()}


def _context() -> CompileContext:
    records: dict[str, InstrumentRecord] = {}
    for market, file in (("fx.eurusd", "eurusd"), ("metal.xauusd", "xauusd")):
        parsed = parse_record(json.loads((_RECORDS / f"{file}.json").read_text("utf-8")))
        assert not isinstance(parsed, TypedRefusal), parsed
        records[market] = parsed.value
    pins = [p.parent for p in _STDLIB.glob("*/*/block.py")]
    return CompileContext(
        sources={f"{p.parent.name}@{p.name}": (p / "block.py").read_bytes() for p in pins},
        entries={f"{p.parent.name}@{p.name}": (p / "entry.json").read_bytes() for p in pins},
        records=records,
    )


def _old_verdict(document: dict[str, object], touched: bool) -> dict[str, object]:
    """What the checker before the change stored: its version, and its old rule's warning."""
    result = check(document, _context())
    warnings = result.warnings
    if touched:
        warnings += (
            Problem(
                ProblemKind.EXITS_UNFIRED,
                ("/exit_set/1",),
                "a target beyond 5 R is rarely reached",
                "bring the target within 5 R",
                "E",
            ),
        )
    old = dataclasses.replace(
        result,
        warnings=warnings,
        checker_version=_OLD,
        problem_set=problem_set(result.errors, warnings),
    )
    return old.to_json()


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    for name, document in _documents().items():
        (tmp_path / f"{name}.json").write_text(json.dumps(document), "utf-8")
        stored = [_old_verdict(document, touched=name == "twin-exits-unfired")]
        (tmp_path / f"{name}.verdicts.json").write_text(json.dumps(stored), "utf-8")
    return tmp_path


def _run(corpus: Path, capsys: pytest.CaptureFixture[str]) -> list[str]:
    assert _script().main([str(corpus), "--records", str(_RECORDS)]) == 0
    return capsys.readouterr().out.splitlines()


def _stored(corpus: Path, name: str) -> list[dict[str, object]]:
    return cast(
        "list[dict[str, object]]", json.loads((corpus / f"{name}.verdicts.json").read_text("utf-8"))
    )


def test_one_changed_rule_supersedes_exactly_the_verdict_it_touches(
    corpus: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lines = _run(corpus, capsys)

    assert lines == [
        "confirmed dummy-trend-pullback: pass -> pass",
        "superseded twin-exits-unfired: pass -> pass",
        "confirmed twin-one-side-only: pass -> pass",
        "confirmed twin-signal-constant: pass -> pass",
        "current 0, confirmed 3, superseded 1, first 0",
    ]
    twin = _stored(corpus, "twin-exits-unfired")
    now = check(_documents()["twin-exits-unfired"], _context()).to_json()
    assert [(v.get("status"), v.get("superseded_by"), v["checker_version"]) for v in twin] == [
        ("superseded", now["checker_version"], _OLD),
        (None, None, now["checker_version"]),
    ]
    assert twin[1] == now
    for name in ("dummy-trend-pullback", "twin-one-side-only", "twin-signal-constant"):
        kept = _stored(corpus, name)
        assert [(v.get("status"), v["checker_version"], v["rechecked_with"]) for v in kept] == [
            (None, _OLD, now["checker_version"])
        ]


def test_a_second_run_with_the_same_checker_changes_nothing(
    corpus: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(corpus, capsys)
    before = {name: _stored(corpus, name) for name in _UNITS}

    lines = _run(corpus, capsys)

    assert lines[-1] == "current 4, confirmed 0, superseded 0, first 0"
    assert {name: _stored(corpus, name) for name in _UNITS} == before


def test_a_unit_with_no_stored_verdict_gets_its_first(
    corpus: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (corpus / "twin-signal-constant.verdicts.json").unlink()

    lines = _run(corpus, capsys)

    assert "first twin-signal-constant: none -> pass" in lines
    assert [v["verdict"] for v in _stored(corpus, "twin-signal-constant")] == ["pass"]
