"""What a check with no Library can say (foundation check 17): it defers what only the Library can
settle, and it still names every real error on a market only the Library knows."""

from __future__ import annotations

import copy
import json
from typing import Any, cast

from qmx_tools import unit_check
from qmx_tools.gather import template
from qmx_tools.unit_check import checked

NO_RECORD_NOTE = (
    "no_record at /markets/0: no instrument record was given for fx.gbpusd. A check with no "
    "Library cannot settle this, and QMB's lander checks it with the Library before any run."
)


def on_gbpusd() -> dict[str, Any]:
    """The dummy on one market no fixture holds."""
    document = cast("dict[str, Any]", copy.deepcopy(template()))
    document["markets"] = [
        {
            "market_id": "fx.gbpusd",
            "instrument_ref": {"venue": "icmarkets-ctrader", "symbol": "GBPUSD"},
        }
    ]
    return document


def kinds(result: dict[str, Any]) -> list[str]:
    return [problem["kind"] for problem in result["errors"]]


def test_the_dummy_on_gbpusd_passes_with_notes() -> None:
    result = unit_check.offline_checked(on_gbpusd())

    assert (result["verdict"], result["errors"]) == ("pass", [])
    assert cast("dict[str, Any]", result["counts"])["errors"] == 0
    assert result["notes"] == [NO_RECORD_NOTE]
    assert unit_check.offline_checked(template()) == checked(None, template())


def test_a_broken_number_on_gbpusd_keeps_its_error() -> None:
    document = on_gbpusd()
    document["numbers"]["ema_period"]["default"] = "1"

    result = cast("dict[str, Any]", unit_check.offline_checked(document))

    assert result["verdict"] == "fail"
    assert kinds(result) == ["outside_range"]
    assert result["errors"][0]["where"] == ["/numbers/ema_period/default"]
    assert result["counts"]["errors"] == 1
    assert result["notes"] == [NO_RECORD_NOTE]


def test_a_second_stop_on_gbpusd_keeps_its_error() -> None:
    document = on_gbpusd()
    stop = copy.deepcopy(document["exit_set"][0])
    document["exit_set"].append({**stop, "name": "second_stop"})

    first = cast("dict[str, Any]", unit_check.offline_checked(document))
    again = cast("dict[str, Any]", unit_check.offline_checked(document, str(first["problem_set"])))

    assert first["verdict"] == "fail"
    assert kinds(first) == ["exit_not_built"]
    assert first["errors"][0]["where"] == ["/exit_set/3"]
    assert first["errors"][0]["layer"] == "compile"
    assert first["notes"] == [NO_RECORD_NOTE]
    assert (first["no_progress"], again["no_progress"]) == (False, True)


def test_a_block_only_the_library_holds_passes_with_notes() -> None:
    text = json.dumps(on_gbpusd())
    ported = text.replace('"ema@1"', '"ported-ema@1"').replace(
        '"entry_id": "ema"', '"entry_id": "ported-ema"'
    )

    result = unit_check.offline_checked(json.loads(ported))

    assert (result["verdict"], result["errors"]) == ("pass", [])
    assert result["notes"] == [
        "pin_unresolved at /pins/0: no entry ported-ema@1 was found. A check with no Library "
        "cannot settle this, and QMB's lander checks it with the Library before any run.",
        NO_RECORD_NOTE,
    ]
