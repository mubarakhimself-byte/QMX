"""Port the Stats dictionary's 239 entries into `qmx.entry/1` drafts (Part A AD-114, slice A12).

    uv run python tools/dictionary/port_stats.py --dry-run
    uv run python tools/dictionary/port_stats.py --write
    uv run python tools/dictionary/port_stats.py --freeze C:/Users/Mubarak/Desktop/Stats/dictionary
    uv run --project qmx-agents --no-sync python tools/dictionary/port_stats.py --home HOME

The input is the frozen copy in ``qml/catalogue-seed/stats-2026-08-26/``, its README and its four
family files, whose fingerprints ``SOURCES.json`` holds. ``--freeze`` copies them from the
operator's folder, which it only reads. Every ``##`` record is read with QML's parser
(``resolve_dictionary_entry``) and becomes one draft. The trader words go to the trader face. The
role strings go through ``roles_map.json``. Each class gets a transfer status, ``not_assessed``
unless a transfer-note sentence states it. Every other field's text is kept word for word as a
source quote, so nothing of an entry is lost. The nine slugs two families share, and the two a QML
entry already answers to, become ids scoped by family and linked ``same_word_as``.

``port.json`` beside the seed holds the drafts and their one collection exactly as they land, so
the diff shows every entry. The host lands it once per store at each start
(``qmx_host.first_start.land_port``). ``--dry-run`` writes nothing: it prints the counts and the
report and says whether ``port.json`` and ``SOURCES.json`` are current. ``--write`` writes both.
``--home`` lands the drafts into a QMX folder's Library; it needs the qmx-agents environment and
a Library no running host holds. The exit is 1 when an entry is lost or refused, a draft fails
the entry checker, or a written file is stale.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import shutil
import sys
import uuid
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import is_refusal
from qml.catalogue.entry import (
    ENTRY_SCHEMA,
    EntryOrigin,
    Transfer,
    alias_key,
    check_entry,
    compute_status,
    corpus_problems,
)
from qml.numbers import InstrumentClass
from qml.research.vocab import (
    _HEADING_RE,  # pyright: ignore[reportPrivateUsage] - QML's own reading of a record heading
    DictionaryEntry,
    resolve_dictionary_entry,
)
from qml.unit.model import Role

import qml

ROOT: Final = Path(__file__).resolve().parents[2]
SEED: Final = ROOT / "qml" / "catalogue-seed" / "stats-2026-08-26"
ROLES_MAP: Final = Path(__file__).resolve().parent / "roles_map.json"
STDLIB: Final = Path(qml.__file__).resolve().parent / "blocks" / "stdlib"
SOURCES: Final = "SOURCES.json"
PORT: Final = "port.json"
README: Final = "README.md"
DATED: Final = "2026-08-26"
"""The day the four family files were last written, which the seed folder is named for."""

FAMILIES: Final[Mapping[str, str]] = {
    "context-regime-and-intermarket/context-filters-confirmations.md": "context",
    "invalidation-exits-and-management/exits-execution-management.md": "exits",
    "market-structure-and-location/locations-and-structure.md": "locations",
    "price-action-and-patterns/triggers-patterns-transitions.md": "triggers",
}
"""The four checked family files, as the README's table names them, and the short family name
that scopes a slug two families share."""

FAMILY_TYPE: Final[Mapping[str, str]] = {
    "context": "context",
    "exits": "exit",
    "locations": "structure",
    "triggers": "trigger",
}
"""A ported entry's ``component_type`` by family, unless its roles make it a sizer or an entry
order (``_component_type``)."""

QUOTED: Final[Sequence[tuple[str, str]]] = (
    ("aliases", "Aliases"),
    ("observable_inputs", "Observable inputs"),
    ("parameters_profiles", "Parameters/profiles"),
    ("eligible_roles", "Eligible roles"),
    ("market_data_constraints", "Market/data constraints"),
    ("transfer_notes", "Transfer notes"),
    ("evidence_status", "Evidence/status"),
    ("uncertainty_variants", "Uncertainty/variants"),
)
"""The seed fields with no face of their own yet, each kept word for word as a source quote."""

FACED: Final[Mapping[str, str]] = {
    "family": "family",
    "definition": "definition",
    "boundaries": "boundaries",
    "recognition_semantics": "recognition",
}
"""The seed fields the trader face holds word for word."""

_STATES: Final = (
    r"\b(fully transferable|directly transferable|transfers directly|portable)\b"
    r".*\b(forex|fx)\b.*\bcrypto spot\b"
)
_HEDGED: Final = r"\b(not|only|but|except|unless|without)\b"
_NOT_FX: Final = r"\b(not transferable|do not transfer)\b.*\bspot[ -]fx\b"
TRANSFER_RULES: Final[
    Sequence[tuple[re.Pattern[str], re.Pattern[str] | None, Mapping[str, str]]]
] = (
    (
        re.compile(_STATES, re.I),
        re.compile(_HEDGED, re.I),
        {"fx": "direct", "spot_crypto": "direct"},
    ),
    (re.compile(_NOT_FX, re.I), None, {"fx": "not_transferable"}),
)
"""A transfer-note sentence that states a class's transfer, and what it states. A sentence that
names forex and crypto spot as fully, directly or portably transferable, with no hedge word,
states ``direct`` for both; one that says the entry does not transfer to spot FX states
``not_transferable`` for fx. Every other class, and these two where no sentence states one, stays
``not_assessed``."""

_NAMESPACE: Final = uuid.UUID("6f1d7a52-3c0e-5b8e-9a41-2d6c0b7e5f13")


@dataclass(frozen=True, slots=True)
class Record:
    """One parsed seed record: the family file it came from and QML's reading of it."""

    path: str
    family: str
    entry: DictionaryEntry


@dataclass(frozen=True, slots=True)
class Port:
    """The port of one frozen seed: what it read, the drafts it made and their report."""

    sources: dict[str, object]
    records: tuple[Record, ...]
    refused: tuple[str, ...]
    skipped: tuple[str, ...]
    drafts: tuple[dict[str, object], ...]
    collection: dict[str, object]
    unmapped: dict[str, list[str]]
    held_aliases: dict[str, list[str]]

    def faces(self) -> list[dict[str, object]]:
        """Each draft's entry with its ``component_type`` beside it, as QML reads an entry."""
        return [_face(draft) for draft in self.drafts]

    def lost(self) -> list[str]:
        """Records with no draft, by ``<file>#<slug>``, counted from the sources each draft
        cites, so a draft that drops or renames its record shows here."""
        cited = {
            str(cast(dict[str, object], s)["source_ref"]).split(" ")[0]
            for face in self.faces()
            for s in cast(list[object], face.get("sources") or [])
        }
        return [k for k in (_locator(r) for r in self.records) if k not in cited]

    def statuses(self) -> Counter[str]:
        return Counter(compute_status(face).annotation()["value"] for face in self.faces())

    def problems(self) -> list[str]:
        """Every entry-checker and corpus problem of the drafts beside QML's own ten entries."""
        found = [
            f"{face.get('entry_id')}{p.where}: {p.message}"
            for face in self.faces()
            for p in check_entry(face)
        ]
        found += [f"{p.where}: {p.message}" for p in corpus_problems([*own(), *self.faces()])]
        return found

    def transfer(self) -> dict[str, dict[str, int]]:
        counts: dict[str, Counter[str]] = {c.value: Counter() for c in InstrumentClass}
        for face in self.faces():
            for name, claim in cast(dict[str, str], face["transfer"]).items():
                counts[name][claim] += 1
        return {name: dict(sorted(c.items())) for name, c in counts.items()}

    def document(self) -> dict[str, object]:
        """``port.json``: what the host lands, and the report it was made with."""
        return {
            "schema": "qmx.port/1",
            "source_fingerprint": self.sources["fingerprint"],
            "collection": self.collection,
            "drafts": list(self.drafts),
            "report": {
                "parsed": len(self.records),
                "drafts": len(self.drafts),
                "lost": self.lost(),
                "refused": list(self.refused),
                "not_entries": list(self.skipped),
                "statuses": dict(sorted(self.statuses().items())),
                "transfer": self.transfer(),
                "unmapped_roles": self.unmapped,
                "held_aliases": self.held_aliases,
            },
        }


def _face(draft: Mapping[str, object]) -> dict[str, object]:
    fields = cast(dict[str, object], draft["fields"])
    return {"component_type": fields["component_type"], **cast(dict[str, object], fields["entry"])}


def _locator(record: Record) -> str:
    return f"{SEED.relative_to(ROOT).as_posix()}/{record.path}#{record.entry.id}"


def own() -> list[dict[str, object]]:
    """QML's own entries, which a ported id or alias must not name again."""
    return [
        cast(dict[str, object], json.loads(face.read_text("utf-8")))
        for face in sorted(STDLIB.glob("*/*/entry.json"))
    ]


def file_fingerprint(data: bytes) -> str:
    """The sha256 of a file's text with CRLF read as LF, so a Windows checkout that turned the
    seed's line ends gives the fingerprint its LF original has."""
    digest = hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()
    return f"sha256:{digest}"


def sources(seed: Path = SEED) -> dict[str, object]:
    """``SOURCES.json``: each frozen file's fingerprint and their one fingerprint, the key the
    port's drafts land under."""
    files = {
        name: file_fingerprint((seed / name).read_bytes()) for name in [README, *sorted(FAMILIES)]
    }
    made = fingerprint(files)
    if is_refusal(made):
        raise ValueError(f"the seed's fingerprints do not fingerprint: {made}")
    return {
        "schema": "qmx.seed-sources/1",
        "taken_from": "C:/Users/Mubarak/Desktop/Stats/dictionary",
        "dated": DATED,
        "files": files,
        "fingerprint": made.value.value,
    }


def roles_table(path: Path = ROLES_MAP) -> dict[str, list[str]]:
    return cast(dict[str, list[str]], json.loads(path.read_text("utf-8"))["roles"])


def read(seed: Path = SEED) -> tuple[list[Record], list[str], list[str]]:
    """Every record of the four family files, the refusals QML's parser gave, and every ``##``
    heading it does not read as a record (a file's own notes), so nothing is skipped unseen."""
    records: list[Record] = []
    refused: list[str] = []
    skipped: list[str] = []
    for path, family in sorted(FAMILIES.items()):
        data = (seed / path).read_bytes()
        for line in data.decode("utf-8").splitlines():
            if not line.startswith("## "):
                continue
            heading = _HEADING_RE.match(line.rstrip())
            if heading is None:
                skipped.append(f"{path}: {line.strip()}")
                continue
            found = resolve_dictionary_entry(data, file_path=path, entry_id=heading.group(1))
            if is_refusal(found):
                refused.append(f"{path}#{heading.group(1)}: {found}")
            else:
                records.append(Record(path, family, found.value))
    return records, refused, skipped


def _split(text: str) -> list[str]:
    return [p.strip().rstrip(".").strip() for p in re.split(r"[,;]", text) if p.strip(" .")]


def _roles(strings: Sequence[str], table: Mapping[str, list[str]]) -> tuple[list[str], list[str]]:
    """The roles ``strings`` map to, in the vocabulary's order, and the strings the table lacks."""
    mapped = {role for s in strings if s in table for role in table[s]}
    return [r.value for r in Role if r.value in mapped], [s for s in strings if s not in table]


def _transfer(notes: str) -> dict[str, str]:
    claims = {c.value: Transfer.NOT_ASSESSED.value for c in InstrumentClass}
    stated: set[str] = set()
    for sentence in re.split(r"(?<=\.)\s+", notes):
        for states, hedged, says in TRANSFER_RULES:
            if not states.search(sentence) or (hedged is not None and hedged.search(sentence)):
                continue
            for name, claim in says.items():
                if name not in stated:
                    claims[name] = claim
                    stated.add(name)
    return claims


def _component_type(family: str, roles: Sequence[str]) -> str:
    if Role.SIZER.value in roles:
        return "sizer"
    if Role.ENTRY_ORDER.value in roles and Role.EXIT.value not in roles:
        return "entry_order"
    return FAMILY_TYPE[family]


def port(seed: Path = SEED, table: Mapping[str, list[str]] | None = None) -> Port:
    """The drafts of every record in ``seed``, with ``table`` as the roles table."""
    roles_of = roles_table() if table is None else table
    found = sources(seed)
    records, refused, skipped = read(seed)
    qml_names = {
        alias_key(str(name)): f"{e['entry_id']}@{e['version']}"
        for e in own()
        for name in [e["entry_id"], *cast(list[object], e.get("aliases") or [])]
    }
    shared = Counter(r.entry.id for r in records)
    ids = {_locator(r): _entry_id(r, shared, qml_names) for r in records}
    by_slug: dict[str, list[str]] = {}
    for r in records:
        by_slug.setdefault(r.entry.id, []).append(ids[_locator(r)])
    taken = set(qml_names) | {alias_key(i) for i in ids.values()}
    unmapped: dict[str, list[str]] = {}
    held: dict[str, list[str]] = {}
    drafts: list[dict[str, object]] = []
    for r in records:
        entry_id = ids[_locator(r)]
        kept: list[str] = []
        for alias in _split(r.entry.fields["aliases"]):
            key = alias_key(alias)
            if key == alias_key(entry_id) or key in {alias_key(k) for k in kept}:
                continue
            if key in taken:
                held.setdefault(entry_id, []).append(alias)
            else:
                kept.append(alias)
                taken.add(key)
        roles, missing = _roles(r.entry.eligible_roles, roles_of)
        for s in missing:
            unmapped.setdefault(s, []).append(entry_id)
        face: dict[str, object] = {
            "schema": ENTRY_SCHEMA,
            "entry_id": entry_id,
            "version": 1,
            **{key: r.entry.fields[name] for name, key in FACED.items() if r.entry.fields[name]},
            "aliases": kept,
            "origin": EntryOrigin.PORT.value,
            "eligible_roles": roles,
            "sources": [
                {
                    "source_ref": f"{_locator(r)} {label}",
                    "quote": r.entry.fields[name],
                    "dated": DATED,
                }
                for name, label in QUOTED
                if r.entry.fields[name]
            ],
            "transfer": _transfer(r.entry.fields["transfer_notes"]),
        }
        others = [f"{i}@1" for i in by_slug[r.entry.id] if i != entry_id]
        others += [qml_names[k] for k in [alias_key(r.entry.id)] if k in qml_names]
        if others:
            face["same_word_as"] = others
        drafts.append(
            {
                "item": str(uuid.uuid5(_NAMESPACE, f"{found['fingerprint']}/{entry_id}")),
                "title": r.entry.title or r.entry.id,
                "tags": [EntryOrigin.PORT.value, r.family],
                "fields": {"component_type": _component_type(r.family, roles), "entry": face},
            }
        )
    collection: dict[str, object] = {
        "item": str(uuid.uuid5(_NAMESPACE, f"{found['fingerprint']}/collection")),
        "title": "The Stats dictionary of 26 Aug 2026, ported",
        "tags": [EntryOrigin.PORT.value],
        "fields": {
            "items": [d["item"] for d in drafts],
            "port": EntryOrigin.PORT.value,
            "source_fingerprint": found["fingerprint"],
        },
    }
    return Port(
        found,
        tuple(records),
        tuple(refused),
        tuple(skipped),
        tuple(drafts),
        collection,
        dict(sorted(unmapped.items())),
        held,
    )


def _entry_id(record: Record, shared: Counter[str], qml_names: Mapping[str, str]) -> str:
    """The slug, scoped by family when two families share it or a QML entry already answers to
    it (``rate-of-change`` is an alias of QML's ``roc-of-series``)."""
    slug = record.entry.id
    taken = shared[slug] > 1 or alias_key(slug) in qml_names
    return f"{record.family}.{slug}" if taken else slug


def freeze(source: Path, seed: Path = SEED) -> None:
    """Copy the README and the four family files from ``source``, which is only read."""
    for name in [README, *FAMILIES]:
        (seed / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, seed / name)


def _dumped(document: object) -> str:
    return json.dumps(document, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def stale(made: Port, seed: Path = SEED) -> list[str]:
    """The written files that differ from this port."""
    wanted = {SOURCES: _dumped(made.sources), PORT: _dumped(made.document())}
    return [
        name
        for name, text in wanted.items()
        if not (seed / name).is_file() or (seed / name).read_text("utf-8") != text
    ]


def write(made: Port, seed: Path = SEED) -> None:
    (seed / SOURCES).write_text(_dumped(made.sources), "utf-8", newline="\n")
    (seed / PORT).write_text(_dumped(made.document()), "utf-8", newline="\n")


def report(made: Port) -> tuple[list[str], int]:
    """The dry run's lines and its exit code."""
    lost, problems = made.lost(), made.problems()
    lines = [
        f"parsed {len(made.records)}",
        f"drafts {len(made.drafts)}",
        f"lost {len(lost)}",
        f"refused {len(made.refused)}",
        f"checker problems {len(problems)}",
        *(f"status {name} {n}" for name, n in sorted(made.statuses().items())),
        f"unmapped role strings {len(made.unmapped)}",
        *(f"  unmapped {s!r}: {', '.join(ids)}" for s, ids in made.unmapped.items()),
        f"aliases held back {sum(len(a) for a in made.held_aliases.values())}",
        *(
            f"transfer {name} {', '.join(f'{k} {v}' for k, v in claims.items())}"
            for name, claims in made.transfer().items()
        ),
        *(f"  not an entry: {s}" for s in made.skipped),
        *(f"  lost {k}" for k in lost),
        *(f"  refused {k}" for k in made.refused),
        *(f"  problem {p}" for p in problems),
    ]
    return lines, 1 if lost or made.refused or problems else 0


def land(home: Path) -> str:
    """Land the drafts into the Library of the QMX folder ``home`` as the host does at a start.
    The host lives in the qmx-agents environment, so it is imported only here."""
    store = importlib.import_module("qmx_control.library").open_store(home)
    first_start = importlib.import_module("qmx_host.first_start")
    try:
        landed = first_start.land_port(store, SEED)
    finally:
        store.close()
    return "nothing new: the port is in this Library already" if landed is None else str(landed)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Port the Stats dictionary into entry drafts.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="count and report; write nothing")
    mode.add_argument("--write", action="store_true", help="write SOURCES.json and port.json")
    mode.add_argument(
        "--freeze", type=Path, help="copy the five files from this folder, then write"
    )
    mode.add_argument("--home", type=Path, help="land the drafts into this QMX folder's Library")
    args = parser.parse_args(argv)
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")
    if args.home is not None:
        print(land(cast(Path, args.home)))
        return 0
    if args.freeze is not None:
        freeze(cast(Path, args.freeze))
    made = port()
    lines, code = report(made)
    if args.write or args.freeze is not None:
        write(made)
    late = stale(made)
    lines += [f"stale {name}: run --write" for name in late] or [f"current {SOURCES}, {PORT}"]
    print("\n".join(lines))
    return 1 if code or late else 0


if __name__ == "__main__":
    sys.exit(main())
