"""A funnel template writes its own lineage (Library AD-32, DATA-PLAN DR12).

The lineage step is a script in each of the seven funnel templates, so what it writes is the
template's own rule and never a model's choice. Run as a subgraph it needs no model and no broker:
it reads the run's inputs, stores the variant record this run made, and writes the edge to the
parent the inputs name, with what changed.

The engine's Library port declares eight edges (`EDGES`), so an edge outside that set (the
`merged-from` a composite writes, the `uses` a combination writes) is reported as refused rather
than silently dropped; the real Library's relation set carries both.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import JsonValue
from qmx_home import resolve

from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR

TEMPLATES = Path(__file__).parents[1] / "src" / "qmx_engine" / "templates"
D4 = TEMPLATES / "d4-variant-comparison"
P1 = TEMPLATES / "p1-portfolio-combination"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    """A QMX folder made the way `--create` makes one, and its home `data/`."""
    return resolve(tmp_path / "QMX", create=True, drives=[]).home


def opened(folder: Path) -> Bundle:
    """The template as a draft that may be tested: its `meta.needs` are the coordinator's to open,
    and the lineage step needs no model, no broker and no QMB door."""
    bundle = Bundle.read(folder)
    meta = cast(dict[str, JsonValue], bundle.definition.get("meta") or {})
    return Bundle({**bundle.definition, "meta": {**meta, "needs": []}}, bundle.files)


def ran(home: Path, folder: Path, inputs: JsonValue) -> tuple[Any, dict[str, Any]]:
    """Run the template's lineage step alone and return its report and what it printed."""
    with EngineService.open(home) as svc:
        item = svc.drafts.put(folder.name, opened(folder), 0, caller=OPERATOR).item
        report = asyncio.run(
            svc.tests.run(item, caller=OPERATOR, inputs=inputs, subgraph=["lineage"])
        )
    with Reader.open(home) as reader:
        printed = [
            cast(dict[str, Any], e.data["outputs"])["main"]
            for e in reader.events(report.run_id)
            if e.kind == "node_finished" and e.data.get("node_id") == "lineage"
        ]
    found = printed[0]
    return report, cast(dict[str, Any], found[0] if isinstance(found, list) else found)


def parent_of(svc: EngineService) -> str:
    stored = svc.ctx.library.put_artifact(
        b"a strategy version", "strategy-version", {}, run_id="seed", principal="run:seed"
    )
    return stored.object_id


def test_a_variant_step_writes_variant_of_with_what_changed(home: Path) -> None:
    with EngineService.open(home) as svc:
        parent = parent_of(svc)
    report, printed = ran(
        home,
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

    assert report.status == "passed"
    assert printed["what_changed"] == "instrument"
    with LibraryFake.open(home) as library:
        edges = [(edge.edge, edge.to_id) for edge in library.edges(printed["record"], "variant-of")]
        record = library.get(printed["record"])

    assert edges == [("variant-of", parent)]
    assert record.fields["metadata"] == {
        "what_changed": "instrument",
        "run_id": report.run_id,
        "parents": [{"edge": "variant-of", "object_id": parent}],
    }


def test_a_composite_names_every_parent_it_merges_even_where_the_port_lacks_the_edge(
    home: Path,
) -> None:
    with EngineService.open(home) as svc:
        first = parent_of(svc)
    report, printed = ran(
        home,
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
    assert printed["what_changed"] == "combining the book"
    assert [(row["edge"], row["to"]) for row in printed["edges"]] == [
        ("merged-from", first),
        ("uses", first),
    ]
    assert [row.get("refused") for row in printed["edges"]] == ["edge_not_in_set"] * 2
