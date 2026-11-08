"""The copilot's unit doors in the catalog (Part A AD-117, A8), a kind's refusal that keeps every
problem it named at the control door, and a unit that reaches `main` only by his click."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from qmx_library.kinds import Checker, Problem
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import MAIN, Principal, drafts_ref

from qmx_control.models import ControlError, LibraryInput
from qmx_control.service import ControlService, WorkflowEngine


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


def no_runs(workflow_id: str | None) -> list[object]:
    return []


def called_by(service: ControlService, principal: str) -> None:
    """An engine door with no runs whose caller reader names `principal`, as the host's would."""
    caller = SimpleNamespace(principal=principal)
    door = SimpleNamespace(principal=lambda: caller, workflow_runs_list=no_runs)
    service.attach_workflow_engine(cast("WorkflowEngine", door))


def a_unit_draft(service: ControlService, checker: Checker) -> str:
    store = service.library.store
    store.register_checker("qml.unit/1", checker)
    draft = Draft("unit", "u", "u", fields=unit_fields())
    return store.put(Principal("operator"), draft, on=drafts_ref("u"), expected_head=None).object_id


def test_a_publish_refusal_keeps_the_first_message_and_every_problem(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    called_by(service, "operator")
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


@pytest.mark.parametrize("caller", [None, "agent:chat-1", "run:r-1"])
def test_only_his_door_publishes_a_unit_draft_onto_main(tmp_path: Path, caller: str | None) -> None:
    service = ControlService(tmp_path)
    if caller is not None:
        called_by(service, caller)
    saved = a_unit_draft(service, lambda fields: [])

    with pytest.raises(ControlError) as refused:
        service.library_merge(saved, from_ref=drafts_ref("u"))

    named = caller or "agent:unnamed"
    assert (refused.value.code, refused.value.status, str(refused.value)) == (
        "his_click",
        403,
        f"publishing a unit onto main is his click; {named} writes unit drafts only, and he "
        "publishes them from his own door",
    )
    assert service.library.store.head("u", "main") is None


def test_an_agent_cannot_branch_a_unit_draft_into_main(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    called_by(service, "agent:chat-1")
    saved = a_unit_draft(service, lambda fields: [])

    with pytest.raises(ControlError) as refused:
        service.library_branch(saved, "main", from_ref=drafts_ref("u"))

    assert refused.value.code == "his_click"
    assert service.library.store.head("u", "main") is None


def test_his_door_publishes_a_checked_unit_draft(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    called_by(service, "operator")
    saved = a_unit_draft(service, lambda fields: [])

    merged = service.library_merge(saved, from_ref=drafts_ref("u"))

    assert merged == {"outcome": "fast-forward", "object_id": saved}
    assert service.library.store.head("u", "main") == (saved, 1)


def test_library_save_refuses_a_unit_and_names_the_unit_doors(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    called_by(service, "operator")

    with pytest.raises(ControlError) as refused:
        service.library_save(LibraryInput(title="u", kind="unit", content=unit_fields()))

    assert (refused.value.code, str(refused.value)) == (
        "unit_doors_only",
        "library_save stores no unit; start one with unit_new, then save and check it with "
        "unit_check",
    )
    assert service.library.count() == 0


def test_an_agent_cannot_resolve_a_unit_conflict_onto_main(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    called_by(service, "operator")
    store, his, variant = service.library.store, Principal("operator"), "refs/variants/u"
    first = a_unit_draft(service, lambda fields: [])
    service.library_merge(first, from_ref=drafts_ref("u"))
    service.library_branch(first, variant)
    for ref, family in ((drafts_ref("u"), "on-main"), (variant, "on-variant")):
        fields = {**unit_fields(), "family_id": family}
        store.put(
            his,
            Draft("unit", "u", "u", fields=fields, parents=[first]),
            on=ref,
            expected_head=first,
        )
    service.library_merge(first, from_ref=drafts_ref("u"))
    held = store.head("u", MAIN)
    clash = service.library_merge(first, from_ref=variant)
    called_by(service, "agent:chat-1")

    with pytest.raises(ControlError) as refused:
        service.library_resolve(str(clash["object_id"]), values={"fields.family_id": "on-variant"})

    assert (clash["outcome"], refused.value.code) == ("conflict", "his_click")
    assert store.head("u", MAIN) == held
