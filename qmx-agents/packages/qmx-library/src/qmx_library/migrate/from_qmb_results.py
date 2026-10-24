"""MIGRATION: QMB's own result files and the old `backtest` items, one `backtest-result` each.

Library AD-29 retires the other two result shapes. QMB wrote its results as CT-32 files on disk,
and the tools wrote `backtest` items; this step reads both once and puts each as one
`backtest-result` whose `report` blob is the file byte for byte, so nothing is re-rendered and
nothing is lost. It links the three edges the shape names when the caller supplies them:
`consumed` to the dataset card version, `uses` to the bot version and `tests` to a hypothesis.

A file is read two ways, by what it says: a CT-32 result (a body carrying `performance_result`,
`outcome_identity` or `data_points_processed`) or an old `backtest` item (`{"name", "kind":
"backtest", "content": …}`). The object's item is the file's own run id when it carries one, else
`qmb-result:<sha256 of the file>`, and every import also records that sha256 in
`fields.legacy_qmb_result`, so a second run over the same folder skips what is already there.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, cast

from qmx_library.migrate import MIGRATOR, head, place, with_legacy
from qmx_library.port import Draft, JsonObject, LibraryRefused, ObjectId
from qmx_library.principal import MAIN
from qmx_library.store import Store

__all__ = ["EDGES", "Imported", "Report", "import_qmb_results"]

EDGES: Final[tuple[str, ...]] = ("consumed", "uses", "tests")
"""The three edges a landed result may carry, in the order this importer writes them."""

_SKIPPED_FIELDS: Final[frozenset[str]] = frozenset(
    {"performance_result", "content", "name", "kind", "slices"}
)
"""What stays in the report blob only: the tables and the old item's envelope."""


@dataclass(frozen=True, slots=True)
class Imported:
    """One file that became one `backtest-result`."""

    item: str
    source: str
    object_id: ObjectId
    edges: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class Report:
    """What one import did: what it put, what it skipped, and what it could not link."""

    imported: tuple[Imported, ...] = ()
    skipped: tuple[str, ...] = ()
    alarms: tuple[str, ...] = field(default=())
    missing: tuple[str, ...] = field(default=())
    """The edge targets named for a result that the Library does not hold, so nothing links to a
    guess."""


def _declared(body: Mapping[str, object], *names: str) -> object:
    for name in names:
        value = body.get(name)
        if value is not None:
            return value
    return None


def _body_of(document: Mapping[str, object]) -> Mapping[str, object]:
    """The result body of a CT-32 file or of an old `backtest` item, or what there is."""
    content = document.get("content")
    if isinstance(content, Mapping):
        typed = json_object(cast("Mapping[object, object]", content))
        if "performance_result" in typed or "data_points_processed" in typed:
            return typed
    performance = document.get("performance_result")
    if isinstance(performance, Mapping):
        return json_object(cast("Mapping[object, object]", performance))
    return json_object(document)


def json_object(value: object) -> JsonObject:
    """A JSON object from `value`, refusing anything else the way a typed door would."""
    if not isinstance(value, Mapping):
        raise LibraryRefused("schema_invalid", "a result file is a JSON object")
    return {str(key): item for key, item in value.items()}  # type: ignore[misc]


def _fields(document: Mapping[str, object], body: Mapping[str, object], digest: str) -> JsonObject:
    fields: JsonObject = {}
    for name in ("world", "claim_class", "role", "fidelity"):
        declared = _declared(body, name) or _declared(document, name)
        if isinstance(declared, str) and declared.strip():
            fields[name] = declared
    outcome = _declared(body, "outcome")
    if isinstance(outcome, str) and outcome in {"supports", "refutes", "inconclusive"}:
        fields["outcome"] = outcome
    memo = _declared(body, "memo_key") or _declared(document, "memo_key")
    if isinstance(memo, str) and memo.strip():
        fields["memo_key"] = memo
    provenance: JsonObject = {"qmb_result_sha256": digest}
    run_id = _declared(body, "run_id") or _declared(document, "run_id")
    if isinstance(run_id, str) and run_id.strip():
        provenance["run_id"] = run_id
    for key, value in body.items():
        if key in _SKIPPED_FIELDS or key in fields or key in {"run_id", "outcome", "memo_key"}:
            continue
        if isinstance(value, str | int | float | bool):
            provenance.setdefault(key, value)
    fields["provenance"] = provenance
    fields["legacy_qmb_result"] = digest
    return fields


def _edges_for(
    edges: Mapping[str, Mapping[str, str]], keys: tuple[str, ...]
) -> tuple[tuple[str, str], ...]:
    for key in keys:
        named = edges.get(key)
        if named is None:
            continue
        return tuple((relation, named[relation]) for relation in EDGES if relation in named)
    return ()


def import_qmb_results(
    results_root: Path,
    store: Store,
    *,
    edges: Mapping[str, Mapping[str, str]] | None = None,
) -> Report:
    """Import every JSON result file under `results_root` as one `backtest-result`.

    ``edges`` maps a run id, or the file's name, to the ids of its `consumed`, `uses` and `tests`
    targets. A result that names none lands with the edges the file itself declares (none today),
    rather than with an invented link: a result with no data, bot or hypothesis link is still one
    result, and a wrong edge is worse than a missing one.
    """
    try:
        files = sorted(results_root.glob("*.json"))
    except OSError as error:
        raise LibraryRefused(
            "storage_failure", f"cannot read the QMB results folder: {error}"
        ) from error
    imported: list[Imported] = []
    skipped: list[str] = []
    alarms: list[str] = []
    missing: list[str] = []
    named: Mapping[str, Mapping[str, str]] = edges if edges is not None else {}
    for path in files:
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        existing = with_legacy(store, "legacy_qmb_result", digest)
        if existing is not None:
            skipped.append(path.name)
            continue
        try:
            document: object = json.loads(data)
        except (ValueError, UnicodeDecodeError) as error:
            alarms.append(f"{path.name}: {error}")
            continue
        if not isinstance(document, Mapping):
            alarms.append(f"{path.name}: a result file is a JSON object")
            continue
        result = cast("Mapping[str, object]", document)
        body = _body_of(json_object(result))
        run_id = _declared(body, "run_id") or _declared(result, "run_id")
        item = str(run_id) if isinstance(run_id, str) and run_id.strip() else f"qmb-result:{digest}"
        fields = _fields(json_object(result), body, digest)
        placed = place(
            store,
            Draft(
                kind="backtest-result",
                item=item,
                title=str(_declared(result, "name") or item),
                summary=f"imported from {path.name}",
                fields=fields,
                blobs={"report": data},
            ),
        )
        written: list[tuple[str, str]] = []
        for relation, target in _edges_for(named, (item, path.name, path.stem)):
            found = head(store, target, MAIN)
            if found is None:
                missing.append(target)
                continue
            store.relate(MIGRATOR, placed.object_id, relation, found)
            written.append((relation, target))
        imported.append(
            Imported(item=item, source=path.name, object_id=placed.object_id, edges=tuple(written))
        )
    return Report(
        imported=tuple(imported),
        skipped=tuple(skipped),
        alarms=tuple(alarms),
        missing=tuple(sorted(set(missing))),
    )
