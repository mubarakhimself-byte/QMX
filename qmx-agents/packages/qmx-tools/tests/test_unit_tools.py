"""The copilot's unit doors (Part A AD-117, A8): write from a template, check every problem at
once, save drafts only, and the same check from the command line."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import MAIN, Principal, drafts_ref

from qmx_tools.functions import domain_functions
from qmx_tools.gather import template
from qmx_tools.service import DomainContext


def broken() -> dict[str, Any]:
    """The dummy with three layer C errors at three places."""
    document: dict[str, Any] = copy.deepcopy(template())
    document["numbers"]["ema_period"]["motion"] = {"mode": "scaled"}
    document["numbers"]["time_out_bars"]["default"] = "47.5"
    document["markets"][0]["settings"] = {"ema_periodd": "50"}
    return document


BROKEN_ERRORS = {
    ("motion_not_allowed", "/numbers/ema_period/motion/mode"),
    ("not_in_measure", "/numbers/time_out_bars/default"),
    ("undeclared_number", "/markets/0/settings/ema_periodd"),
}


def errors(result: dict[str, Any]) -> set[tuple[str, str]]:
    return {(p["kind"], where) for p in result["errors"] for where in p["where"]}


@pytest.fixture
def context(tmp_path: Path) -> DomainContext:
    return DomainContext(root=tmp_path)


def test_a_unit_from_the_dummy_checks_clean_and_saves_only_as_its_draft(
    context: DomainContext,
) -> None:
    unit = domain_functions(context)["unit"]
    made = unit["unit_new"](overrides={"/title": "Gold pullback"})
    result = unit["unit_check"](document=made["document"], item=made["item"])

    store = context.library.store
    head = store.head(made["item"], drafts_ref(made["item"]))
    assert (result["verdict"], result["counts"]["errors"]) == ("pass", 0)
    assert head is not None
    assert head[0] == result["saved"]["object_id"]
    assert store.get(store.engine, head[0]).title == "Gold pullback"
    assert store.head(made["item"], MAIN) is None


def test_a_draft_of_a_unit_only_on_main_publishes_as_a_fast_forward(
    context: DomainContext,
) -> None:
    store, his, variant = context.library.store, Principal("operator"), "refs/variants/u"
    store.register_checker("qml.unit/1", lambda fields: [])
    dummy = Draft("unit", "u", "Gold", fields=cast("JsonObject", template()))
    first = store.put(his, dummy, on=variant, expected_head=None).object_id
    store.merge(his, "u", from_ref=variant, into=MAIN)
    changed = {**template(), "title": "Gold, tighter"}

    saved = domain_functions(context)["unit"]["unit_check"](document=changed, item="u")
    merged = store.merge(his, "u", from_ref=drafts_ref("u"), into=MAIN)

    assert store.get(his, saved["saved"]["object_id"]).parents == (first,)
    assert (merged.outcome, store.head("u", MAIN)) == (
        "fast-forward",
        (saved["saved"]["object_id"], 2),
    )


def test_a_broken_unit_names_every_problem_and_a_repeat_says_no_progress(
    context: DomainContext,
) -> None:
    check = domain_functions(context)["unit"]["unit_check"]
    first = check(document=broken())
    again = check(document=broken(), previous_problem_set=first["problem_set"])

    assert (first["verdict"], errors(first)) == ("fail", BROKEN_ERRORS)
    assert (first["no_progress"], again["no_progress"]) == (False, True)


def test_a_shape_the_library_refuses_keeps_the_last_draft_and_lists_every_refusal(
    context: DomainContext,
) -> None:
    unit = domain_functions(context)["unit"]
    made = unit["unit_new"]()
    bad = copy.deepcopy(made["document"])
    bad["direction"] = "sideways"
    del bad["markets"]

    result = unit["unit_check"](document=bad, item=made["item"])

    head = context.library.store.head(made["item"], drafts_ref(made["item"]))
    assert result["verdict"] == "fail"
    assert result["saved"]["object_id"] is None
    assert {p["where"][0] for p in result["saved"]["refused"]} == {"", "/direction"}
    assert head is not None
    assert head[0] == made["object_id"]


def test_the_unit_path_writes_no_bot_or_strategy_and_nothing_on_main(
    context: DomainContext,
) -> None:
    unit = domain_functions(context)["unit"]
    made = unit["unit_new"]()
    unit["unit_check"](document=broken(), item=made["item"])
    unit["unit_check"](document=made["document"], item=made["item"])
    unit["unit_explain"](item=made["item"])
    with pytest.raises(ValueError, match="names no place in the template"):
        unit["unit_new"](overrides={"/nowhere/at/all": 1})
    with pytest.raises(ValueError, match="names no unit in the Library"):
        unit["unit_check"](document=made["document"], item="not-an-item")

    db = context.library.store.catalog.db
    kinds = db.execute("SELECT kind, count(*) FROM objects GROUP BY kind").fetchall()
    assert kinds == [("unit", 3)]
    assert context.library.store.heads_on(MAIN) == []


def test_explain_reads_a_saved_unit_in_plain_lines(context: DomainContext) -> None:
    unit = domain_functions(context)["unit"]
    made = unit["unit_new"]()

    lines = unit["unit_explain"](item=made["item"])["lines"]

    assert lines[1] == "trades both on fx.eurusd, metal.xauusd"
    assert lines[-1] == "check: 0 errors, 4 warnings"


def test_the_block_rows_answer_that_they_arrive_with_a11(context: DomainContext) -> None:
    find = domain_functions(context)["blocks"]["blocks_find"]

    with pytest.raises(ValueError, match=r"^blocks_find: Not built yet: .*\(A11\)"):
        find(words="ema")


def run(document: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "qmx_tools.unit_check", str(document)],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def test_the_command_exits_0_on_the_dummy_and_1_with_every_problem(tmp_path: Path) -> None:
    good, bad = tmp_path / "dummy.json", tmp_path / "broken.json"
    good.write_text(json.dumps(template()), encoding="utf-8")
    bad.write_text(json.dumps(broken()), encoding="utf-8")

    passed, failed = run(good), run(bad)

    assert (passed.returncode, json.loads(passed.stdout)["verdict"]) == (0, "pass")
    assert (failed.returncode, errors(json.loads(failed.stdout))) == (1, BROKEN_ERRORS)


def test_the_command_exits_1_on_a_file_that_is_not_json(tmp_path: Path) -> None:
    text = tmp_path / "unit.json"
    text.write_text("{not json", encoding="utf-8")

    found = run(text)

    assert (found.returncode, found.stdout) == (1, "")
    assert "does not read as JSON" in found.stderr
