"""A storage is a place that can keep, not a place to run (design 06 section 4): the place list and
the forwarder's rows hold only rows that can run, and a row that names no `can` still runs."""

from __future__ import annotations

from qmx_engine.roles import Candidate
from qmx_engine.service.forward import placement_rows
from qmx_engine.settings import places
from qmx_engine.triggers.preflight import placement_kind, plan_on_provider

SETTINGS: dict[str, object] = {
    "placement.pc.cpu_slots": 3,
    "placement.myserver.id": "01J-SRV",
    "placement.myserver.kind": "owned",
    "placement.myserver.engine_url": "http://myserver:8000",
    "placement.usb.id": "01J-USB",
    "placement.usb.via": "folder",
    "placement.usb.can": ("keep",),
    "placement.usb.path": "E:\\",
    "placement.both.can": ("run", "keep"),
    "placement.both.kind": "owned",
    "placement.modal.kind": "serverless",
    "placement.modal.provider": "modal",
}


def test_the_place_list_and_the_forwarders_rows_skip_a_keep_only_row() -> None:
    assert places(SETTINGS) == {
        "pc": "pc",
        "myserver": "01J-SRV",
        "both": "both",
        "modal": "modal",
    }
    rows = placement_rows(SETTINGS)
    assert [row["name"] for row in rows] == ["both", "modal", "myserver", "pc"]
    assert rows[2] == {
        "name": "myserver",
        "kind": "owned",
        "engine_url": "http://myserver:8000",
    }


def test_a_plan_login_on_a_serverless_row_is_still_refused_with_the_provider_line() -> None:
    plan = Candidate("claude", "haiku", None, 200_000, False)
    kinds = {name: placement_kind(SETTINGS, name) for name in places(SETTINGS)}

    refused = plan_on_provider("n1", "triage", "modal", [plan], kinds)

    assert refused is not None
    assert (refused.code, refused.message) == (
        "plan_on_provider",
        "n1: role triage resolves to the plan row claude/haiku on modal (serverless); plan "
        "logins stay on his machines",
    )
