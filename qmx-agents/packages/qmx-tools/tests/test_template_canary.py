"""The canary template and the records QML ships (RC-17, slice 5).

`unit_new("canary")` writes a complete unit from one JSON, and `unit_check` on a store that holds
nothing reads the instrument records that ship with QML rather than falling back to the test
fixtures, which exist only in a checkout. One more JSON in the templates folder is one more
template, with no other edit.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, cast

import pytest
from qmx_library.port import Draft
from qmx_library.principal import MAIN, Principal, drafts_ref

from qmx_tools import functions, gather
from qmx_tools.functions import domain_functions
from qmx_tools.service import DomainContext

TEMPLATES = Path(str(gather.TEMPLATES))
OPERATOR = Principal("operator")
EURUSD: dict[str, Any] = {
    "venue": "icmarkets-ctrader",
    "symbol": "EURUSD",
    "market_id": "eurusd",
    "class": "fx",
    "currency": "USD",
    "status": "specified",
}
"""A record on the canary's fx market, with the kind's six required keys and nothing else."""


@pytest.fixture
def context(tmp_path: Path) -> DomainContext:
    return DomainContext(root=tmp_path)


def _numbers(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return cast("dict[str, dict[str, Any]]", document["numbers"])


def test_canary_compiles_from_nothing(context: DomainContext) -> None:
    unit = domain_functions(context)["unit"]

    made = unit["unit_new"]("canary", {})
    result = unit["unit_check"](document=made["document"], item=made["item"])

    numbers = _numbers(cast("dict[str, Any]", made["document"]))
    warnings = cast("list[dict[str, Any]]", result["warnings"])
    assert (result["verdict"], result["counts"]["errors"]) == ("pass", 0)
    assert result["notes"] == []
    assert {spec["origin"] for spec in numbers.values()} == {"placeholder"}
    spans = [cast("dict[str, Any]", spec["range"]) for spec in numbers.values()]
    assert all({"min", "max", "step"} <= set(span) for span in spans)
    labelled = {
        where
        for problem in warnings
        for where in problem["where"]
        if problem["kind"] == "placeholder"
    }
    assert labelled >= {f"/numbers/{name}/origin" for name in numbers}
    brakes = [problem for problem in warnings if problem["kind"] == "no_halts"]
    assert len(brakes) == 1
    assert "no brakes" in brakes[0]["message"]
    assert "no brakes" in unit["unit_explain"](document=made["document"])["lines"][0]


def test_a_new_template_is_one_json(
    context: DomainContext, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = tmp_path / "templates"
    shutil.copytree(TEMPLATES, folder)
    shutil.copyfile(folder / "dummy-trend-pullback.json", folder / "third-shape.json")
    monkeypatch.setattr(functions, "TEMPLATES", folder)
    monkeypatch.setattr(gather, "TEMPLATES", folder)
    unit = domain_functions(context)["unit"]

    with pytest.raises(ValueError) as refused:
        unit["unit_new"]("no-such-template", {})
    made = unit["unit_new"]("third-shape", {})
    checked = unit["unit_check"](document=made["document"])

    assert str(refused.value) == (
        "no template 'no-such-template'; the templates are "
        "['canary', 'dummy-trend-pullback', 'third-shape']"
    )
    assert (checked["verdict"], checked["counts"]["errors"]) == ("pass", 0)


def test_an_archived_eurusd_lets_the_shipped_record_answer(context: DomainContext) -> None:
    store = context.library.store
    store.put(
        OPERATOR,
        Draft("instrument", "instrument-eurusd", "EURUSD", fields=dict(EURUSD)),
        on=MAIN,
        expected_head=None,
    )
    store.archive(OPERATOR, "instrument-eurusd", "withdrawn")
    unit = domain_functions(context)["unit"]
    made = unit["unit_new"]("canary", {})

    result = unit["unit_check"](document=made["document"])

    assert (result["verdict"], result["counts"]["errors"]) == ("pass", 0)
    assert result["notes"] == []


def test_a_draft_only_eurusd_does_not_hide_the_shipped_record(context: DomainContext) -> None:
    store = context.library.store
    store.put(
        OPERATOR,
        Draft("instrument", "instrument-eurusd", "EURUSD", fields=dict(EURUSD)),
        on=drafts_ref("instrument-eurusd"),
        expected_head=None,
    )
    unit = domain_functions(context)["unit"]
    made = unit["unit_new"]("canary", {})

    result = unit["unit_check"](document=made["document"])

    assert (result["verdict"], result["counts"]["errors"]) == ("pass", 0)
    assert result["notes"] == []
