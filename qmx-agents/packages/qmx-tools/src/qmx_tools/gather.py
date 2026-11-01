"""What the unit checker reads, gathered for QML's pure door (Part A AD-111, AD-117, A7).

QML's verbs read no file and no Library, so the host hands them a `CompileContext`: each pinned
block's entry face and source, and each market's instrument record. Blocks come from QML's own
package files first and from the Library's `component` entries otherwise. Instrument records are
the Library's `instrument` items on `main` (C-02), each read at its head with the Library's own
version as `record_version`. A market no item holds falls back to QML's test fixtures, which exist
only in a checkout, and every check that reads one says so in a warning. A record is handed to the
checker under a unit's market only when its venue and symbol are the ones the market's
`instrument_ref` names, so a record is never bound by item or file name.
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
from qml.catalogue.entry import EntryProblem, check_entry
from qml.check import CheckResult
from qml.compile import CompileContext
from qml.compile.compiler import DERIVED_BLOCKS
from qml.door import check
from qml.numbers import InstrumentRecord, parse_record
from qml.unit import parse
from qml.unit.model import SymbolRef
from qml.unit.schema import ENTRY_REF_PATTERN
from qmx_library.principal import MAIN, state_ref

if TYPE_CHECKING:
    from qmx_library.port import JsonObject
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


def entry_face(fields: Mapping[str, object]) -> dict[str, object]:
    """A `component` item's entry with its `component_type` beside it, as QML reads an entry."""
    entry = cast(dict[str, object], fields.get("entry") or {})
    return {"component_type": fields.get("component_type"), **entry}


def entry_bytes(fields: Mapping[str, object]) -> bytes:
    """A `component` item's entry face as QML reads an `entry.json`."""
    return json.dumps(entry_face(fields), sort_keys=True).encode()


def entry_problems(fields: Mapping[str, object]) -> tuple[EntryProblem, ...]:
    """The put check of a `component` marked `qmx.entry/1`: QML's entry checker over its face,
    every problem at once. Only items carrying that marker reach it (the kind file's
    `applies_when`), so every other `component` item saves as before."""
    return check_entry(entry_face(fields))


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


def _held(store: Store, ref: SymbolRef) -> list[tuple[str, JsonObject, int]]:
    """Each live `instrument` item whose head on `main` holds `ref`'s venue and symbol: the item,
    its fields and how many times `main` has moved for it, which is the record's version. An
    archived item is withdrawn (Library AD-6), so it binds nothing and its replacement binds
    alone."""
    items = {
        store.get(store.engine, object_id).item
        for object_id in store.with_field("instrument", "symbol", ref.symbol)
    }
    held: list[tuple[str, JsonObject, int]] = []
    for item in sorted(items):
        head = store.head(item, MAIN)
        state = store.head(item, state_ref(item))
        if head is None or (state is not None and state[0] == "archived"):
            continue
        fields = store.get(store.engine, head[0]).fields
        if fields.get("venue") == ref.venue and fields.get("symbol") == ref.symbol:
            held.append((item, fields, head[1]))
    return held


def _record(
    store: Store | None,
    ref: SymbolRef,
    market_id: str,
    fixtures: dict[tuple[str, str], tuple[str, InstrumentRecord]],
) -> tuple[InstrumentRecord | None, str | None]:
    """The record a market reads and the warning that comes with it, if any."""
    held = [] if store is None else _held(store, ref)
    if len(held) > 1:
        items = ", ".join(item for item, _, _ in held)
        return None, (
            f"{market_id}: {len(held)} instrument items hold {ref.venue}:{ref.symbol} "
            f"({items}), so the check reads none of them"
        )
    if held:
        item, fields, version = held[0]
        parsed = parse_record({**fields, "record_version": version})
        if is_refusal(parsed):
            reason = parsed.context.get("reason")
            return None, f"{market_id}: the instrument item {item} is not a full record: {reason}"
        return parsed.value, None
    matched = fixtures.get((ref.venue, ref.symbol))
    if matched is None:
        return None, None
    return matched[1], f"{FIXTURE_WARNING}: {market_id} reads {matched[0]}"


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
            if not isinstance(ref, SymbolRef):
                continue
            record, warning = _record(store, ref, market.market_id, fixtures)
            if record is not None:
                records[market.market_id] = record
            if warning is not None:
                warnings.append(warning)
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
