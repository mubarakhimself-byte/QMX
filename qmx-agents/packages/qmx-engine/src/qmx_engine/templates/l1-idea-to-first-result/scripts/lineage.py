"""Write this run's lineage edges into the Library (Library AD-32, DATA-PLAN DR12).

The template writes its own lineage; no model chooses it. The step reads the run's inputs and the
output of the last step before it, and stores one `artifact` of type `lineage` on the run's ref:
the variant record this run made. It then writes an edge from that record to every parent the
inputs name, and annotates the record with the change, so one family read returns the parent, the
children, the siblings and what changed between them.

An input names a parent in one of two ways:

* a row that carries an `object_id` (the Library object id of a strategy version, a component, a
  dataset card, a hypothesis or a run), optionally with `what_changed` and `edge`;
* a `lineage` list of rows, each `{"edge": ..., "object_id": ..., "what_changed": ...}`, which is
  how a step that makes several variants names each one.

The edge of a row is its own `edge`, else `variant-of` when the row is a variant (it carries a
`variant`, a `label` or an `overrides`) and `derived-from` otherwise; a row may say
`merged-from`, `uses` or `consumed` instead. A row with no `object_id` is left out, never guessed.

The record this step stores is the child the edges start from, so the numbers are the run's own:
the template id, the run id, what changed, and every parent it was given.
"""

import json
import os
import sys
from pathlib import Path

from qmx_engine.ports.library import LibraryRefused
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.workers.zones import home_of

VARIANT_KEYS = ("variant", "label", "overrides")
LINEAGE_EDGE = "variant-of"
DERIVED_EDGE = "derived-from"
DEPTH = 4
"""How deep a run input may nest the row that names a Library object."""
NAMED_LISTS = ("lineage", "parents", "uses", "consumed", "merged_from")
"""The keys whose list is rows rather than values, so a row is collected once."""


def flat(given):
    """The inputs with each grader's envelope opened, so a check sees what it checked."""
    found = []
    for value in given if isinstance(given, list) else [given]:
        if isinstance(value, dict) and set(value) == {"input", "verdict", "feedback"}:
            found += flat(value["input"])
        else:
            found.append(value)
    return found


def rows_of(items):
    """Every row the inputs give that names a Library object, and any explicit `lineage` list."""
    rows = []
    for value in items:
        walk(value, rows, 0)
    return rows


def walk(value, rows, depth):
    """Collect the rows at any depth: a run input nests the item it names under its own name."""
    if depth > DEPTH:
        return
    if isinstance(value, list):
        for entry in value:
            walk(entry, rows, depth + 1)
        return
    if not isinstance(value, dict):
        return
    handled = set()
    for key in NAMED_LISTS:
        if isinstance(value.get(key), list):
            walk(value[key], rows, depth + 1)
            handled.add(key)
    if "object_id" in value:
        rows.append(value)
        return
    for key, entry in value.items():
        if key not in handled:
            walk(entry, rows, depth + 1)


def edge_of(row):
    """The relation a row asks for: its own, or the one its shape implies."""
    if row.get("edge"):
        return str(row["edge"])
    if any(key in row for key in VARIANT_KEYS):
        return LINEAGE_EDGE
    return DERIVED_EDGE


def change_of(row):
    """What changed, in the row's own words; empty when the row says nothing."""
    for key in ("what_changed", "label", "name"):
        if row.get(key):
            return str(row[key])
    overrides = row.get("overrides")
    if isinstance(overrides, dict) and overrides:
        return "overrides " + json.dumps(overrides, sort_keys=True)
    return ""


given = flat(json.load(sys.stdin)["in"])
run_id = os.environ["QMX_RUN_ID"]
principal = f"run:{run_id}"
named = [row for row in rows_of(given) if row.get("object_id")]
changes = [change for change in map(change_of, named) if change]
what_changed = " | ".join(dict.fromkeys(changes))

record = {
    "run_id": run_id,
    "what_changed": what_changed,
    "parents": [{"edge": edge_of(row), "object_id": str(row["object_id"])} for row in named],
}
written = []
with LibraryFake.open(home_of(Path(os.environ["QMX_WORK_SHARED"]))) as library:
    stored = library.put_artifact(
        json.dumps(record, sort_keys=True).encode(),
        "lineage",
        {"what_changed": what_changed, "run_id": run_id, "parents": record["parents"]},
        run_id=run_id,
        principal=principal,
        intent_key=f"lineage|{run_id}",
    )
    for row in named:
        edge = edge_of(row)
        line = {
            "edge": edge,
            "from": stored.object_id,
            "to": str(row["object_id"]),
            "what_changed": change_of(row),
        }
        try:
            library.link(stored.object_id, edge, str(row["object_id"]), principal=principal)
        except LibraryRefused as refused:
            line["refused"] = refused.code
        written.append(line)  # fmt: skip
print(json.dumps({"record": stored.object_id, "what_changed": what_changed, "edges": written}))
