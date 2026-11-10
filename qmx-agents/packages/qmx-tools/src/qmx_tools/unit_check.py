"""Check a unit document at layers A to F and name every problem: `python -m qmx_tools.unit_check`.

The `unit_check` row and this command answer with the same `qmx.check/1` result, plus `notes`,
the lines `gather` adds about where the check's inputs came from (Part A AD-117). The command
reads a file, or standard input for `-`, prints the result as one line of JSON, and exits 0 when
the unit passes and 1 when it does not or cannot be read. It opens no Library, so it checks
against QML's own blocks; the row checks against the Library's as well.

`offline_checked` is what a step with no Library can say: the plugin's hook and the `unit-check`
block ask it, and it defers to `notes` what only the Library can settle.

A market whose record the store does not hold reads the record QML ships with its numbers
(`qml/src/qml/numbers/shipped_records.json`), through `ShippedStore`: the same `with_field`,
`head` and `get` calls `gather` makes of a Library, so day one needs no broker.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

from qmf.core import is_refusal
from qmf.core.fingerprint import fingerprint
from qml.compile import CompiledUnit, compile_unit
from qml.door import check
from qmx_library.port import LibraryRefused, ObjectView
from qmx_library.principal import MAIN, Principal, state_ref

from qmx_tools.gather import gather

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from qmx_library.port import JsonObject, ObjectId
    from qmx_library.store import Store

PASSED = 0
FAILED = 1

LIBRARY_SETTLES: Final = frozenset(
    {"no_record", "no_pip", "calendar_not_held", "data_level_missing", "pin_unresolved"}
)
"""The kinds a check with no Library cannot settle, because it holds only QML's blocks and fixture
records. QMB's lander compiles the pin with the Library before any run, so nothing unsafe passes."""
NO_SOURCE: Final = "block_missing"
"""What the compiler adds for a pin only the Library holds, beside that pin's `pin_unresolved`."""
NOT_BUILT_HINT: Final = "the compiler format does not run this yet; write it another way"
SHIPPED_RECORDS: Final = files("qml.numbers") / "shipped_records.json"
"""The instrument records that ship with QML, beside the parser that reads their keys."""
SHIPPED_ITEM: Final = "shipped-instrument-"
"""The item a shipped record answers under. No Library item carries this name, so a shipped
record and one on `main` never answer for each other."""


def shipped_records() -> tuple[dict[str, object], ...]:
    """The instrument records QML ships, each labelled `source: shipped` in the file."""
    body = cast("dict[str, object]", json.loads(SHIPPED_RECORDS.read_text("utf-8")))
    return tuple(cast("list[dict[str, object]]", body["records"]))


@dataclass
class ShippedStore:
    """A store that answers QML's shipped instrument records where the Library holds none.

    `gather` reads it exactly as it reads a Library: `with_field` for a symbol, then `head`, then
    `get`. A live record on `main` wins, because a shipped answer is offered only for a venue and
    symbol the store holds no live record for: one on a draft, or on an archived item, binds
    nothing (`gather._held` reads it the same way), so one market still binds one record. Wrapped
    around None it is what a check with no Library reads, and every other verb goes to the real
    store.
    """

    store: Store | None = None
    records: tuple[dict[str, object], ...] = ()

    def __post_init__(self) -> None:
        if not self.records:
            self.records = shipped_records()

    @property
    def engine(self) -> Principal:
        """The principal a read names; with no Library behind it, a shipped engine answers."""
        return Principal("engine", "shipped") if self.store is None else self.store.engine

    def with_field(self, kind_name: str, key: str, value: str) -> list[ObjectId]:
        held = [] if self.store is None else self.store.with_field(kind_name, key, value)
        if kind_name != "instrument" or key != "symbol":
            return held
        taken: set[str] = set()
        for object_id in held:
            view = self.get(self.engine, object_id)
            head, state = self.head(view.item, MAIN), self.head(view.item, state_ref(view.item))
            if head is not None and not (state is not None and state[0] == "archived"):
                taken.add(str(view.fields.get("venue")))
        return [
            *held,
            *(
                SHIPPED_ITEM + str(record["symbol"])
                for record in self.records
                if record.get("symbol") == value and str(record.get("venue")) not in taken
            ),
        ]

    def head(self, item: str, ref: str) -> tuple[ObjectId, int] | None:
        if item.startswith(SHIPPED_ITEM):
            return (item, 1) if ref == MAIN else None
        return None if self.store is None else self.store.head(item, ref)

    def get(self, who: Principal, object_id: ObjectId) -> ObjectView:
        if object_id.startswith(SHIPPED_ITEM):
            return self._view(object_id)
        if self.store is None:
            raise LibraryRefused("not_found", f"no object {object_id} and no Library to read it")
        return self.store.get(who, object_id)

    def read_blob(self, blob_id: str) -> bytes:
        if self.store is None:
            raise LibraryRefused("not_found", f"no blob {blob_id} and no Library to read it")
        return self.store.read_blob(blob_id)

    def _view(self, object_id: str) -> ObjectView:
        symbol = object_id.removeprefix(SHIPPED_ITEM)
        record = next(record for record in self.records if record.get("symbol") == symbol)
        return ObjectView(
            object_id,
            object_id,
            "instrument",
            "record",
            symbol,
            "",
            cast("JsonObject", {**record, "record_version": 1}),
            {},
            (),
            (),
            {},
        )

    def __getattr__(self, name: str) -> Any:
        store = self.__dict__.get("store")
        if store is None:
            raise AttributeError(name)
        return getattr(store, name)


def shipped(store: Store | None) -> ShippedStore:
    """`store` with QML's shipped instrument records behind it."""
    return ShippedStore(store)


def checked(
    store: Store | None, document: object, previous_problem_set: str | None = None
) -> dict[str, object]:
    """`document`'s check result with what `gather` found in `store`, and gather's notes."""
    found = gather(shipped(store), document)
    result = check(document, found.context, previous_problem_set)
    return {**result.to_json(), "notes": list(found.warnings)}


def _compiler_problems(document: object) -> list[dict[str, object]]:
    """What only the compiler refuses, in the check's own problem shape, without the blind spot."""
    built = compile_unit(document, gather(shipped(None), document).context)
    if isinstance(built, CompiledUnit):
        return []
    return [
        {
            "kind": problem.kind,
            "layer": problem.layer,
            "where": [problem.where],
            "message": problem.message,
            "hint": NOT_BUILT_HINT,
        }
        for problem in built
        if problem.kind not in LIBRARY_SETTLES and problem.kind != NO_SOURCE
    ]


def _problem_set(problems: Iterable[Mapping[str, Any]]) -> str:
    """The fingerprint `qml.check.result.problem_set` takes, over problems in their JSON form."""
    rows = sorted([p["layer"], p["kind"], p["where"], p["message"]] for p in problems)
    made = fingerprint(rows)
    if is_refusal(made):
        raise ValueError(str(made.context))
    return made.value.value


def offline_checked(document: object, previous: str | None = None) -> dict[str, object]:
    """`checked` with no Library, with every kind only the Library can settle moved to `notes`.

    A market only the Library knows reads `no_record` from the layers, and `check` compiles only
    when the layers found nothing. So when that move is what emptied `errors`, the compiler runs
    here, or everything it alone refuses would be invisible on that market. In any other case the
    check reached the compiler already or still has errors to fix.
    """
    result = checked(None, document, previous)
    errors = cast("list[dict[str, Any]]", result["errors"])
    deferred = [p for p in errors if p["kind"] in LIBRARY_SETTLES]
    if not deferred:
        return result
    left: list[dict[str, Any]] = [p for p in errors if p["kind"] not in LIBRARY_SETTLES]
    left = left or _compiler_problems(document)
    warnings = cast("list[dict[str, Any]]", result["warnings"])
    current = _problem_set([*left, *warnings])
    return {
        **result,
        "verdict": "fail" if left else "pass",
        "counts": {"errors": len(left), "warnings": len(warnings)},
        "errors": left,
        "problem_set": current,
        "no_progress": bool(left) and previous == current,
        "notes": [
            *cast("list[str]", result["notes"]),
            *(
                f"{p['kind']} at {', '.join(p['where'])}: {p['message']}. A check with no Library "
                "cannot settle this, and QMB's lander checks it with the Library before any run."
                for p in deferred
            ),
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m qmx_tools.unit_check", description="Check a unit document at A to F."
    )
    parser.add_argument("document", help="a unit document's JSON file, or - for standard input")
    parser.add_argument(
        "--previous", help="the problem_set of the last check, to learn no_progress"
    )
    given = parser.parse_args(argv)
    try:
        text = (
            sys.stdin.read() if given.document == "-" else Path(given.document).read_text("utf-8")
        )
        document: object = json.loads(text)
    except (OSError, UnicodeDecodeError, ValueError) as unreadable:
        print(f"{given.document} does not read as JSON: {unreadable}", file=sys.stderr)
        return FAILED
    result = checked(None, document, given.previous)
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return PASSED if result["verdict"] == "pass" else FAILED


if __name__ == "__main__":
    raise SystemExit(main())
