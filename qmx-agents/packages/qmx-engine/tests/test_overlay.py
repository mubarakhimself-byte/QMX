"""A variant resolves over its parent into a full snapshot that validates on its own."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import JsonValue

from qmx_engine.definition.folder import content_hash, load
from qmx_engine.definition.overlay import OverlayError, resolve
from qmx_engine.definition.validate import validate

PARENT = Path(__file__).parent / "fixtures" / "workflows" / "paper-scout-min"


def parent() -> dict[str, JsonValue]:
    return json.loads((PARENT / "definition.json").read_text(encoding="utf-8"))


def variant(*patches: JsonValue) -> dict[str, JsonValue]:
    return {
        "schema": "qmx.workflow/1",
        "id": "paper-scout-fx",
        "name": "Paper scout for FX papers",
        "extends": {
            "workflow_item": "paper-scout",
            "object_id": "obj-7f3a",
            "patches": list(patches),
        },
    }


def test_a_variant_resolves_to_a_patched_snapshot_that_records_its_parent(tmp_path: Path) -> None:
    resolved = resolve(
        variant(
            {"op": "replace", "path": "/nodes/2/parameters/max_items", "value": 3},
            {"op": "add", "path": "/inputs/properties/region", "value": {"type": "string"}},
            {"op": "remove", "path": "/pinData"},
            {"op": "add", "path": "/nodes/3/parameters/tools/-", "value": "Grep"},
        ),
        parent(),
    )
    folder = Path(shutil.copytree(PARENT, tmp_path / "fx"))
    (folder / "definition.json").write_text(json.dumps(resolved.snapshot), encoding="utf-8")
    snapshot = resolved.snapshot

    assert resolved.variant_of == ("paper-scout", "obj-7f3a")
    assert (snapshot["id"], snapshot["name"], snapshot["extends"]) == (
        "paper-scout-fx",
        "Paper scout for FX papers",
        None,
    )
    assert snapshot["nodes"][2]["parameters"]["max_items"] == 3  # type: ignore[index]
    assert snapshot["nodes"][3]["parameters"]["tools"] == ["Read", "WebFetch", "Grep"]  # type: ignore[index]
    assert snapshot["inputs"]["properties"]["region"] == {"type": "string"}  # type: ignore[index]
    assert "pinData" not in snapshot
    assert parent()["pinData"] is not None
    assert validate(load(folder)) == []


def test_a_patch_that_misses_the_parent_names_itself() -> None:
    with pytest.raises(OverlayError, match=r"patches\[1\] replace /settings/nope"):
        resolve(
            variant(
                {"op": "replace", "path": "/name", "value": "x"},
                {"op": "replace", "path": "/settings/nope", "value": 1},
            ),
            parent(),
        )


def test_an_unresolved_variant_neither_validates_nor_hashes(tmp_path: Path) -> None:
    folder = Path(shutil.copytree(PARENT, tmp_path / "fx"))
    document = parent() | variant(
        {"op": "add", "path": "/nodes/2/parameters/action", "value": "triage"}
    )
    (folder / "definition.json").write_text(json.dumps(document), encoding="utf-8")

    assert [(p.code, p.path) for p in validate(load(folder))] == [("extends_unresolved", "extends")]
    with pytest.raises(ValueError, match="unresolved variant"):
        content_hash(load(folder))
    resolved = resolve(document, parent())
    (folder / "definition.json").write_text(json.dumps(resolved.snapshot), encoding="utf-8")
    assert [(p.code, p.path) for p in validate(load(folder))] == []
