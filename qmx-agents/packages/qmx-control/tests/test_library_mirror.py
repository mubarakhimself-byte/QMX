"""The dual write (MIGRATION step 5): with a mirror attached, every save and link also reaches
it, and a mirror's refusal is recorded on the event without failing the save."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from qmx_control.models import Document
from qmx_control.service import ControlService, LibraryInput


def mirrored(service: ControlService) -> list[object]:
    return [cast(Document, e["data"]).get("mirror") for e in service.events("library")]


class Mirror:
    def __init__(self, refuse: str | None = None) -> None:
        self.refuse = refuse
        self.saved_ids: list[str] = []
        self.links: list[tuple[str, str]] = []

    def saved(self, document: Document) -> str | None:
        self.saved_ids.append(str(document["id"]))
        return self.refuse

    def linked(self, source_id: str, target_id: str) -> str | None:
        self.links.append((source_id, target_id))
        return self.refuse


def test_saves_and_links_reach_the_mirror_once_it_is_attached(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    before = service.library_save(LibraryInput(title="Before", kind="note", content={}))
    mirror = Mirror()
    service.attach_library_mirror(mirror)
    after = service.library_save(LibraryInput(title="After", kind="note", content={"a": 1}))
    service.library_link(str(before["id"]), str(after["id"]))

    assert mirror.saved_ids == [after["id"]]
    assert mirror.links == [(before["id"], after["id"])]
    assert mirrored(service) == [None, "ok", "ok"]


def test_a_mirror_refusal_is_on_the_event_and_the_save_still_lands(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    service.attach_library_mirror(Mirror(refuse="stale_head"))

    saved = service.library_save(LibraryInput(title="Kept", kind="note", content={"b": 2}))

    assert service.library_get(str(saved["id"]))["content"] == {"b": 2}
    assert mirrored(service) == ["stale_head"]
