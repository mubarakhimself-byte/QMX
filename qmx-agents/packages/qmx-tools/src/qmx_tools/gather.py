"""What the unit checker reads, gathered for QML's pure door (Part A AD-111, AD-117, A7).

QML's verbs read no file and no Library, so the host hands them a `CompileContext`: each pinned
block's entry face and source, and each market's instrument record. Blocks come from QML's own
package files first and from the Library's `component` entries otherwise. Instrument records are
QML's test fixtures until Part C's `instrument` kind lands (C-02); every check that reads them says
so in a warning. A record is handed to the checker under a unit's market only when its venue and
symbol are the ones the market's `instrument_ref` names, so a record is never bound by file name.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

import qml
from qmf.core import is_refusal
from qml.blocks.api import FaceProblem, parse_entry
from qml.check import CheckResult
from qml.compile import CompileContext
from qml.compile.compiler import DERIVED_BLOCKS
from qml.door import check
from qml.numbers import InstrumentRecord, parse_record
from qml.unit import parse
from qml.unit.model import SymbolRef
from qml.unit.schema import ENTRY_REF_PATTERN

if TYPE_CHECKING:
    from qmx_library.store import Store

ENTRY_SCHEMA: Final = "qmx.entry/1"
DUMMY: Final = "dummy-trend-pullback"
STDLIB: Final[Traversable] = files("qml.blocks") / "stdlib"
TEMPLATES: Final[Traversable] = files("qml.unit") / "templates"
FIXTURE_RECORDS: Final = Path(qml.__file__).resolve().parents[2] / "tests" / "fixtures" / "records"
FIXTURE_WARNING: Final = (
    "instrument records are QML's test fixtures until the instrument kind lands (C-02)"
)
_PIN: Final = re.compile(ENTRY_REF_PATTERN)


@dataclass(frozen=True, slots=True)
class Gathered:
    context: CompileContext
    warnings: tuple[str, ...]


def entry_bytes(fields: Mapping[str, object]) -> bytes:
    """A `component` item's entry face as QML reads an `entry.json`."""
    entry = cast(dict[str, object], fields.get("entry") or {})
    face = {"component_type": fields.get("component_type"), **entry}
    return json.dumps(face, sort_keys=True).encode()


def entry_problems(fields: Mapping[str, object]) -> tuple[FaceProblem, ...]:
    """The put check of a `component` marked `qmx.entry/1`: its face reads as QML's entry."""
    found = parse_entry(entry_bytes(fields))
    return (found,) if isinstance(found, FaceProblem) else ()


def _own(pin: str) -> tuple[bytes, bytes] | None:
    entry_id, version = pin.split("@")
    folder = STDLIB / entry_id / version
    face, source = folder / "entry.json", folder / "block.py"
    if not (face.is_file() and source.is_file()):
        return None
    return face.read_bytes(), source.read_bytes()


def _library(store: Store, pin: str) -> tuple[bytes, bytes] | None:
    entry_id, version = pin.split("@")
    for object_id in store.with_field("component", "entry.entry_id", entry_id):
        view = store.get(store.engine, object_id)
        entry = cast(dict[str, object], view.fields.get("entry") or {})
        code = view.blobs.get("code")
        if entry.get("schema") == ENTRY_SCHEMA and str(entry.get("version")) == version and code:
            return entry_bytes(view.fields), store.read_blob(code.blob_id)
    return None


def _named(value: object) -> set[str]:
    """Every `<entry>@<version>` string anywhere in a document."""
    if isinstance(value, str):
        return {value} if _PIN.match(value) else set()
    found: set[str] = set()
    if isinstance(value, dict):
        found = found.union(*map(_named, cast(dict[str, object], value).values()))
    elif isinstance(value, list):
        found = found.union(*map(_named, cast(list[object], value)))
    return found


def _fixtures() -> dict[tuple[str, str], tuple[str, InstrumentRecord]]:
    found: dict[tuple[str, str], tuple[str, InstrumentRecord]] = {}
    for path in sorted(FIXTURE_RECORDS.glob("*.json")):
        parsed = parse_record(json.loads(path.read_text("utf-8")))
        if not is_refusal(parsed):
            record = parsed.value
            found[record.venue, record.symbol] = (path.name, record)
    return found


def gather(store: Store | None, document: object) -> Gathered:
    """The check context of `document`: the blocks its pins name and its markets' records. A
    document whose shape does not hold gets an empty context, since only layer A runs on it."""
    entries: dict[str, bytes] = {}
    sources: dict[str, bytes] = {}
    records: dict[str, InstrumentRecord] = {}
    warnings: list[str] = []
    unit = parse(document).unit
    if unit is not None:
        for given in unit.pins:
            pin = f"{given.entry_id}@{given.version}"
            if not _PIN.match(pin):
                continue
            found = _own(pin) or (_library(store, pin) if store is not None else None)
            if found is not None:
                entries[pin], sources[pin] = found
        fixtures = _fixtures()
        for market in unit.markets:
            ref = market.instrument_ref
            matched = fixtures.get((ref.venue, ref.symbol)) if isinstance(ref, SymbolRef) else None
            if matched is not None:
                records[market.market_id] = matched[1]
                warnings.append(f"{FIXTURE_WARNING}: {market.market_id} reads {matched[0]}")
    return Gathered(CompileContext(sources, entries, records), tuple(warnings))


def check_unit(store: Store | None, document: object) -> tuple[CheckResult, tuple[str, ...]]:
    """Layers A to F over `document` with what `gather` found, and gather's warnings."""
    gathered = gather(store, document)
    return check(document, gathered.context), gathered.warnings


def _runs(document: dict[str, object]) -> set[str]:
    """The blocks the compiler runs for the document's derived numbers."""
    unit = parse(document).unit
    if unit is None:
        return set()
    modes = (spec.motion.mode for spec in unit.numbers.values())
    return {DERIVED_BLOCKS[mode] for mode in modes if mode in DERIVED_BLOCKS}


def template(name: str = DUMMY) -> dict[str, object]:
    """A QML template unit with every QML block it uses pinned at that block's fingerprint. Only
    the blocks it uses, so a new block in QML leaves the template's fingerprint as it was."""
    document = cast(dict[str, object], json.loads((TEMPLATES / f"{name}.json").read_text("utf-8")))
    pins: list[object] = []
    for pin in sorted(_named(document) | _runs(document)):
        own = _own(pin)
        if own is None:
            continue
        face = parse_entry(own[0])
        if isinstance(face, FaceProblem):
            continue
        pins.append(
            {"entry_id": face.entry_id, "version": face.version, "fingerprint": face.fingerprint}
        )
    document["pins"] = pins
    return document
