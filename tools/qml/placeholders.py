"""The rip-out list: every published unit and what in it uses a placeholder (A15, AD-116).

A published unit is a ``unit`` item whose head on ``main`` is not archived. Each of its bindings
(the logic slots, the exit set, the sizer, the halts and a plain-Python block) is listed when its
block's entry says ``origin: placeholder``, and each of its numbers when the number's origin says
so. A binding whose block is in neither QML's stdlib nor the Library's ``component`` items is
listed as ``unfound``, because nothing can say whether it is a placeholder.

The script reads the Library's evidence files under ``<QMX folder>/library`` (``refs/log.jsonl``
and ``objects/``, the layout ``qmx_library.store`` documents) and writes nothing, so it runs
beside a running host.

    uv run python tools/qml/placeholders.py QMX_FOLDER

One tab-separated line per use: unit id, Library item, what, name, where in the document, the
block pin and its owner. A summary line follows.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from importlib.resources import files
from pathlib import Path
from typing import Final, cast

from qml.blocks.api import EntryFace, parse_entry
from qml.unit import parse
from qml.unit.model import Binding, EntryRef, Origin, Scope, SlotsSide, Unit

PLACEHOLDER: Final = Origin.PLACEHOLDER.value
MAIN: Final = "main"
HEADER: Final = "unit\titem\twhat\tname\twhere\tblock\towner"


class What(StrEnum):
    BINDING = "binding"
    NUMBER = "number"
    UNFOUND = "unfound"
    UNREADABLE = "unreadable"


@dataclass(frozen=True, slots=True)
class Use:
    unit_id: str
    item: str
    what: What
    name: str
    where: str
    block: str = ""
    owner: str = ""

    def line(self) -> str:
        fields = (self.unit_id, self.item, self.what, self.name, self.where, self.block, self.owner)
        return "\t".join(fields)


def _bindings(unit: Unit) -> Iterator[tuple[str, str, EntryRef]]:
    """Each binding as (where, name, block), in document order."""
    for side_name in ("long", "short"):
        side = getattr(unit.logic, side_name)
        if isinstance(side, SlotsSide):
            for slot_name, slot in side.slots.items():
                for i, binding in enumerate(slot.bindings):
                    where = f"/logic/{side_name}/slots/{slot_name}/bindings/{i}"
                    yield where, binding.name, binding.block
    scoped: list[tuple[str, Binding]] = [(f"/exit_set/{i}", b) for i, b in enumerate(unit.exit_set)]
    if unit.sizer is not None:
        scoped.append(("/sizer", unit.sizer))
    for scope in Scope:
        halts = cast("tuple[Binding, ...]", getattr(unit.halts, scope.value))
        scoped += [(f"/halts/{scope.value}/{i}", b) for i, b in enumerate(halts)]
    for where, binding in scoped:
        yield where, binding.name, binding.block
    if unit.plain_python is not None:
        yield "/plain_python", "plain_python", unit.plain_python.block


def uses(item: str, document: object, faces: Mapping[str, EntryFace]) -> tuple[Use, ...]:
    """What in one unit document uses a placeholder, reading block entries from ``faces``."""
    parsed = parse(document)
    unit = parsed.unit
    if unit is None:
        raw = cast("Mapping[str, object]", document if isinstance(document, Mapping) else {})
        first = parsed.problems[0]
        where = "/".join(first.where)
        return (Use(str(raw.get("unit_id", "")), item, What.UNREADABLE, first.message, where),)
    found: list[Use] = []
    for where, name, block in _bindings(unit):
        face = faces.get(str(block))
        if face is None:
            found.append(Use(unit.unit_id, item, What.UNFOUND, name, where, str(block)))
        elif face.origin == PLACEHOLDER:
            owner = face.owner or ""
            found.append(Use(unit.unit_id, item, What.BINDING, name, where, str(block), owner))
    for name, spec in unit.numbers.items():
        if spec.origin is Origin.PLACEHOLDER:
            found.append(Use(unit.unit_id, item, What.NUMBER, name, f"/numbers/{name}"))
    return tuple(found)


def _manifest(library: Path, object_id: str) -> Mapping[str, object]:
    digest = object_id.rsplit(":", 1)[-1]
    path = library / "objects" / digest[:2] / digest[2:4] / f"{digest}.json"
    return cast("Mapping[str, object]", json.loads(path.read_bytes()))


def published(library: Path) -> Iterator[tuple[str, Mapping[str, object]]]:
    """Each item whose head on ``main`` is live, with that head's manifest, by item."""
    heads: dict[tuple[str, str], object] = {}
    with (library / "refs" / "log.jsonl").open("rb") as log:
        for line in log:
            try:
                move = cast("Mapping[str, object]", json.loads(line))
            except ValueError:
                continue
            heads[str(move["item"]), str(move["ref"])] = move["new_head"]
    for (item, ref), head in sorted(heads.items()):
        if ref != MAIN or not isinstance(head, str):
            continue
        if heads.get((item, f"refs/items/{item}/state")) == "archived":
            continue
        yield item, _manifest(library, head)


def _stdlib_faces() -> dict[str, EntryFace]:
    faces: dict[str, EntryFace] = {}
    for folder in (files("qml.blocks") / "stdlib").iterdir():
        for version in folder.iterdir() if folder.is_dir() else ():
            entry = version / "entry.json"
            face = parse_entry(entry.read_bytes()) if entry.is_file() else None
            if isinstance(face, EntryFace):
                faces[face.pin] = face
    return faces


def rip_out(folder: Path) -> tuple[int, tuple[Use, ...]]:
    """How many units are published in the QMX folder, and every placeholder use among them."""
    library = folder / "library"
    faces = _stdlib_faces()
    units: list[tuple[str, Mapping[str, object]]] = []
    for item, manifest in published(library):
        fields = cast("Mapping[str, object]", manifest.get("fields") or {})
        if manifest.get("kind") == "unit":
            units.append((item, fields))
        elif manifest.get("kind") == "component" and isinstance(fields.get("entry"), Mapping):
            entry = cast("Mapping[str, object]", fields["entry"])
            face_json = {"component_type": fields.get("component_type"), **entry}
            face = parse_entry(json.dumps(face_json).encode())
            if isinstance(face, EntryFace):
                faces.setdefault(face.pin, face)
    found = [use for item, fields in units for use in uses(item, fields, faces)]
    return len(units), tuple(found)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List every published unit's placeholders.")
    parser.add_argument("folder", type=Path, help="the QMX folder whose Library is read")
    args = parser.parse_args(argv)
    folder = cast("Path", args.folder)
    if not (folder / "library" / "refs" / "log.jsonl").is_file():
        print(f"no Library with a ref log under {folder}", file=sys.stderr)
        return 2
    count, found = rip_out(folder)
    print(HEADER)
    for use in found:
        print(use.line())
    by_what = {what: sum(1 for u in found if u.what is what) for what in What}
    users = len({u.item for u in found})
    print(
        f"{count} published units, {users} use a placeholder: "
        f"{by_what[What.BINDING]} bindings, {by_what[What.NUMBER]} numbers, "
        f"{by_what[What.UNFOUND]} blocks not found, {by_what[What.UNREADABLE]} unreadable"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
