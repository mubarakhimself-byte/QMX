"""The fanning edge maps: one partition per item, per zipped pair, per cartesian pair or per
matched key."""

from __future__ import annotations

from pathlib import Path

import pytest
from flows import Flow, Script, edge, node, of, workflow
from pydantic import JsonValue

from qmx_engine.core.edges import FanError, Part, fan
from qmx_engine.definition.model import Target
from qmx_engine.nodes.base import NodeJob

NO_SETTINGS: dict[str, JsonValue] = {}


def target(map_: str, **extra: JsonValue) -> Target:
    return Target.model_validate({"node": "t", "port": "in", "map": map_, **extra})


def test_broadcast_and_zip_make_one_partition_per_item_and_per_pair() -> None:
    assert fan([(target("broadcast"), ["a", "b"])], NO_SETTINGS) == [
        Part({"in": "a"}, {"item": 0}),
        Part({"in": "b"}, {"item": 1}),
    ]
    assert fan([(target("zip"), [1, 2]), (target("zip"), ["x", "y"])], NO_SETTINGS) == [
        Part({"in": [1, "x"]}, {"item": 0}),
        Part({"in": [2, "y"]}, {"item": 1}),
    ]
    with pytest.raises(FanError, match=r"unequal lengths \[1, 2\]"):
        fan([(target("zip"), [1, 2]), (target("zip"), ["x"])], NO_SETTINGS)


def test_keyed_join_pairs_items_by_key_and_reports_unmatched_keys() -> None:
    cards: list[JsonValue] = [{"paper_id": "p1", "card": 1}, {"paper_id": "p2", "card": 2}]
    checks: list[JsonValue] = [{"paper_id": "p2", "ok": True}, {"paper_id": "p3", "ok": False}]

    parts = fan(
        [
            (target("keyed-join", key="paper_id"), cards),
            (target("keyed-join", key="paper_id"), checks),
        ],
        NO_SETTINGS,
    )

    assert parts == [
        Part(
            {"in": [{"paper_id": "p2", "card": 2}, {"paper_id": "p2", "ok": True}]},
            {"key": '"p2"', "unmatched": ['"p1"', '"p3"']},
        )
    ]


def pick(job: NodeJob, value: JsonValue) -> JsonValue:
    """The `rows` and `cols` nodes take their list out of the run input."""
    return value[job.node_id] if isinstance(value, dict) else value


def test_a_cartesian_edge_of_3_by_4_runs_12_partitions_in_row_major_order(
    tmp_path: Path,
) -> None:
    definition = workflow(
        [
            node("start", "trigger"),
            node("rows", "script"),
            node("cols", "script"),
            node("pair", "script"),
            node("gather", "join"),
        ],
        {
            "start": {"main": [edge("rows"), edge("cols")]},
            "rows": {"main": [edge("pair", "cartesian", explicit=True)]},
            "cols": {"main": [edge("pair", "cartesian", explicit=True)]},
            "pair": {"main": [edge("gather")]},
        },
    )
    flow = Flow(tmp_path, definition, {"script": Script(pick)})

    ended = flow.start({"rows": [1, 2, 3], "cols": ["a", "b", "c", "d"]})

    assert len(of(flow.events, "node_started", "pair")) == 12
    pairs: list[JsonValue] = [[r, c] for r in (1, 2, 3) for c in "abcd"]
    assert ended.outputs == {"gather": {"main": pairs}}
