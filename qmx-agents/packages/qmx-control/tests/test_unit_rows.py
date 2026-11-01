"""The copilot's unit doors in the catalog (Part A AD-117, A8), and a kind's refusal that keeps
every problem it named at the control door."""

from __future__ import annotations

from pathlib import Path

import pytest
from qmx_library.kinds import Problem
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import Principal, drafts_ref

from qmx_control.catalog import CORE_TOOLSETS, rows
from qmx_control.models import ControlError
from qmx_control.service import ControlService

SEVEN = {
    "unit_new": "domain_write",
    "unit_check": "domain_write",
    "unit_explain": "read",
    "blocks_find": "read",
    "blocks_get": "read",
    "blocks_check": "read",
    "blocks_match": "read",
}


def test_the_unit_and_blocks_toolsets_hold_the_seven_rows_for_every_agent() -> None:
    found = {
        row.name: (row.approval, row.binds, row.agent, row.toolset in CORE_TOOLSETS)
        for row in rows()
        if row.toolset in ("unit", "blocks")
    }

    assert found == {name: (approval, "domain_fn", True, True) for name, approval in SEVEN.items()}


def unit_fields() -> JsonObject:
    return {
        "schema": "qmx.unit/1",
        "unit_id": "u",
        "family_id": "f",
        "claim_card": {"idea": "an idea", "sources": [], "written_at": "2026-11-01"},
        "markets": [],
        "streams": [],
        "direction": "long",
        "logic": {},
        "exit_set": [],
        "halts": {},
        "reads": [],
        "numbers": {},
        "pins": [],
    }


def two_problems(fields: JsonObject) -> list[Problem]:
    return [
        Problem("ema@1 is not in the unit's pins", ("/logic/long",), "check_failed", "B/pin"),
        Problem("no market is named", ("/markets",), "check_failed", "A/shape"),
    ]


def test_a_publish_refusal_keeps_the_first_message_and_every_problem(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    store = service.library.store
    store.register_checker("qml.unit/1", two_problems)
    draft = Draft("unit", "u", "u", fields=unit_fields())
    saved = store.put(Principal("operator"), draft, on=drafts_ref("u"), expected_head=None)

    with pytest.raises(ControlError) as refused:
        service.library_merge(saved.object_id, from_ref=drafts_ref("u"))

    error = refused.value.document()["error"]
    assert str(refused.value) == "unit: ema@1 is not in the unit's pins"
    assert error == {
        "code": "check_failed",
        "message": "unit: ema@1 is not in the unit's pins",
        "problems": [
            {
                "code": "check_failed",
                "rule": "B/pin",
                "message": "ema@1 is not in the unit's pins",
                "where": ["/logic/long"],
            },
            {
                "code": "check_failed",
                "rule": "A/shape",
                "message": "no market is named",
                "where": ["/markets"],
            },
        ],
    }
    assert store.head("u", "main") is None
