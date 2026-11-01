"""The control door over the Library's kind checks (Part A AD-112): a unit never reaches `main`
through `library_merge` unchecked, and a mini app's provides component still lands unchecked."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from pydantic import JsonValue
from qmx_apps.artifacts import ArtifactRef, Landing
from qmx_library.port import Draft
from qmx_library.principal import Principal, drafts_ref

from qmx_control.models import ControlError
from qmx_control.service import ControlService, WorkflowEngine

UNIT: dict[str, JsonValue] = {
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


def test_a_unit_merge_onto_main_refuses_on_a_store_with_no_checker(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    his_door = SimpleNamespace(principal=lambda: SimpleNamespace(principal="operator"))
    service.attach_workflow_engine(cast("WorkflowEngine", his_door))
    store = service.library.store
    draft = Draft("unit", "u", "u", fields=UNIT)
    saved = store.put(Principal("operator"), draft, on=drafts_ref("u"), expected_head=None)

    with pytest.raises(ControlError) as refused:
        service.library_merge(saved.object_id, from_ref=drafts_ref("u"))

    assert (refused.value.code, str(refused.value)) == (
        "checker_unavailable",
        "unit: no checker 'qml.unit/1' is registered on this host",
    )
    assert store.head("u", "main") is None


def test_an_app_output_lands_its_provides_component_unchecked(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    sink = service.app_runtime().artifacts.library
    assert sink is not None
    landing = Landing(
        app_id="exchange-status",
        version="1.0.0",
        output="status",
        ref=ArtifactRef(
            producer_app="exchange-status",
            definition_hash="abc123",
            output="status",
            sha256="0" * 64,
        ),
        data={"status": "ok"},
        schema={"type": "object"},
        stale_after=60.0,
        at="2026-10-23T00:00:00+00:00",
        fields={"type": "status"},
    )

    sink(landing)

    components = service.library.store.catalog.db.execute(
        "SELECT count(*) FROM objects WHERE kind = 'component'"
    ).fetchone()
    assert components == (1,)
