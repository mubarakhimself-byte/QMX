"""The one Library store: a save lands there and nowhere else, and an app output lands through
`app_runtime()`'s sink (MIGRATION step 6, AD-64)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from qmx_apps.artifacts import ArtifactRef, Landing

from qmx_control.models import Document
from qmx_control.service import ControlService, LibraryInput


def objects(home: Path) -> list[dict[str, object]]:
    """Every object manifest the store wrote."""
    return [
        cast(dict[str, object], json.loads(path.read_bytes()))
        for path in sorted((home / "library" / "objects").rglob("*.json"))
    ]


def test_a_save_lands_one_object_in_the_store_and_no_library_db(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    saved = service.library_save(LibraryInput(title="Rates", kind="strategy", content={"a": 1}))

    written = objects(tmp_path)
    assert len(written) == 1
    assert written[0]["title"] == "Rates"
    assert not (tmp_path / "library.db").exists()
    assert service.library_get(str(saved["id"])) == saved
    moves = (tmp_path / "library" / "refs" / "log.jsonl").read_text("utf-8").splitlines()
    assert [json.loads(line)["ref"] for line in moves] == ["main"]


def test_an_app_output_lands_as_one_artifact_linked_to_its_instance(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    supervisor = service.app_runtime()
    sink = supervisor.artifacts.library
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
        fields={"type": "status", "metadata": {"producer_app": "exchange-status"}},
    )

    landed = sink(landing)
    again = sink(landing)

    assert landed == again, "a re-landing is the same object, not a second one"
    written = objects(tmp_path)
    assert sorted(str(item["kind"]) for item in written) == [
        "artifact",
        "component",
        "mini-app-instance",
    ]
    artifact = next(item for item in written if item["kind"] == "artifact")
    relations = cast(list[dict[str, str]], artifact["relations"])
    assert sorted(relation["type"] for relation in relations) == ["instance-of", "produced-by"]
    written_ids = {
        f"fp1:sha256:{path.stem}" for path in (tmp_path / "library" / "objects").rglob("*.json")
    }
    assert {relation["to"] for relation in relations} == written_ids - {landed}
    assert artifact["fields"] == {
        "type": "status",
        "metadata": {"producer_app": "exchange-status"},
        "legacy_ref": landing.ref.model_dump_json(),
        "legacy_kind": "app-output",
        "output": "status",
        "definition_hash": "abc123",
        "producer_app": "exchange-status",
    }
    assert service.events("library") == []


def test_a_fetched_item_is_saved_once_per_source_and_day(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    item = LibraryInput(
        title="Article",
        kind="article",
        source="https://example.org/article",
        fetched_date="2026-10-08",
        content={"text": "research"},
    )

    first = service.library_save(item)

    assert service.library_save(item.model_copy(update={"content": "new"})) == first
    assert len(objects(tmp_path)) == 1
    document: Document = service.library_get(str(first["id"]))
    assert document["source"] == "https://example.org/article"
    assert document["kind"] == "article"
