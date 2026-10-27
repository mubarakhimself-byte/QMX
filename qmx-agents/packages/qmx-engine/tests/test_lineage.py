"""A funnel template writes its own lineage (Library AD-32, DATA-PLAN DR12), into the real Library.

The lineage step is a script in each of the seven funnel templates, so what it writes is the
template's own rule and never a model's choice. Run as a subgraph it needs no model and no broker:
it reads the run's inputs and lists the variant record this run made and the edge to every parent
the inputs name; the runner writes them through the host's store and hands back their receipts.

The engine's Library port declares eight edges (`EDGES`), so an edge outside that set (the
`merged-from` a composite writes, the `uses` a combination writes) is reported as refused rather
than silently dropped; the real Library's relation set carries both.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import JsonValue
from qmx_home import resolve
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.store import Store

from qmx_engine.ledger import redact
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import Bundle
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR

TEMPLATES = Path(__file__).parents[1] / "src" / "qmx_engine" / "templates"
D4 = TEMPLATES / "d4-variant-comparison"
P1 = TEMPLATES / "p1-portfolio-combination"


@pytest.fixture
def svc(tmp_path: Path) -> Iterator[EngineService]:
    """The engine on a QMX folder made the way `--create` makes one, over its real Library."""
    home = resolve(tmp_path / "QMX", create=True, drives=[]).home
    with (
        Store.open(home / "library", redactor=redact) as store,
        EngineService.open(home, library=EngineLibraryAdapter(store)) as service,
    ):
        yield service


def opened(folder: Path) -> Bundle:
    """The template as a draft that may be tested: its `meta.needs` are the coordinator's to open,
    and the lineage step needs no model, no broker and no QMB door."""
    bundle = Bundle.read(folder)
    meta = cast(dict[str, JsonValue], bundle.definition.get("meta") or {})
    return Bundle({**bundle.definition, "meta": {**meta, "needs": []}}, bundle.files)


def ran(svc: EngineService, folder: Path, inputs: JsonValue) -> tuple[Any, list[dict[str, Any]]]:
    """Run the template's lineage step alone and return its report and the step's receipts."""
    item = svc.drafts.put(folder.name, opened(folder), 0, caller=OPERATOR).item
    report = asyncio.run(svc.tests.run(item, caller=OPERATOR, inputs=inputs, subgraph=["lineage"]))
    with Reader.open(svc.ctx.home) as reader:
        printed = [
            cast(dict[str, Any], e.data["outputs"])["main"]
            for e in reader.events(report.run_id)
            if e.kind == "node_finished" and e.data.get("node_id") == "lineage"
        ]
    return report, cast(list[dict[str, Any]], printed[0]["library_written"])


def parent_of(svc: EngineService) -> str:
    stored = svc.ctx.library.put_artifact(
        b"a strategy version", "strategy-version", {}, run_id="seed", principal="run:seed"
    )
    return stored.object_id


def test_a_variant_step_writes_variant_of_with_what_changed(svc: EngineService) -> None:
    parent = parent_of(svc)
    report, receipts = ran(
        svc,
        D4,
        {
            "strategy": {
                "object_id": parent,
                "label": "instrument",
                "overrides": {"instrument": "GBPUSD"},
            },
            "request": "try GBPUSD on 15 minutes",
        },
    )
    record = receipts[0]["object_id"]
    library = svc.ctx.library
    stored = library.get(record)

    assert report.status == "passed"
    assert [(r["op"], r["handle"], r["refused"]) for r in receipts] == [
        ("put_artifact", "record", None),
        ("link", None, None),
    ]
    assert receipts[1]["object_id"] == record
    assert [(edge.edge, edge.to_id) for edge in library.edges(record, "variant-of")] == [
        ("variant-of", parent)
    ]
    assert (stored.ref, stored.principal) == (f"refs/runs/{report.run_id}", f"run:{report.run_id}")
    assert stored.fields["metadata"] == {
        "what_changed": "instrument",
        "run_id": report.run_id,
        "parents": [{"edge": "variant-of", "object_id": parent}],
        "write_key": f"{report.run_id}:lineage:0::0",
    }


def test_a_composite_names_every_parent_it_merges_even_where_the_port_lacks_the_edge(
    svc: EngineService,
) -> None:
    first = parent_of(svc)
    report, receipts = ran(
        svc,
        P1,
        {
            "lineage": [
                {"edge": "merged-from", "object_id": first, "what_changed": "combining the book"},
                {"edge": "uses", "object_id": first},
            ],
            "request": "combine these two",
        },
    )

    assert report.status == "passed"
    assert [(r["edge"], r["to"], r["refused"]) for r in receipts[1:]] == [
        ("merged-from", first, "edge_not_in_set"),
        ("uses", first, "edge_not_in_set"),
    ]
