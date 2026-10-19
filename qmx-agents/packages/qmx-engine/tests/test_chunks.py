"""Fan-out by chunk (ruling 78): one partition per chunk of items, sized by items or by tokens, with
stable ids and a memo per chunk, so a failed chunk reruns alone."""

from __future__ import annotations

from pathlib import Path

from flows import LATER, Flow, Script, edge, node, of, started_slots, workflow
from pydantic import JsonValue

from qmx_engine.core.partitions import Span, chunks
from qmx_engine.definition.model import Chunk, Workflow

SETTINGS: dict[str, JsonValue] = {"chunk.size": 10, "chunk.fill": 0.3, "context_window": 200_000}


def test_60_items_by_10_make_6_chunks_and_61_make_7_with_a_last_chunk_of_1() -> None:
    by_10 = Chunk(by="items", size=10)

    assert chunks(list(range(60)), by_10, SETTINGS) == [
        Span(0, 10, 10),
        Span(10, 20, 10),
        Span(20, 30, 10),
        Span(30, 40, 10),
        Span(40, 50, 10),
        Span(50, 60, 10),
    ]
    sixty_one = chunks(list(range(61)), by_10, SETTINGS)
    assert len(sixty_one) == 7
    assert sixty_one[-1] == Span(60, 61, 1)


def test_a_chunk_without_a_size_takes_the_chunk_size_setting() -> None:
    spans = chunks(list(range(60)), Chunk(by="items"), SETTINGS | {"chunk.size": 15})

    assert [(s.start, s.end) for s in spans] == [(0, 15), (15, 30), (30, 45), (45, 60)]


def test_a_token_chunk_fills_to_fill_times_the_window_and_no_further() -> None:
    items: list[JsonValue] = ["x" * 398] * 10  # 400 JSON bytes each: 100 estimated tokens

    spans = chunks(items, Chunk(by="tokens", fill=0.3), SETTINGS | {"context_window": 1000})

    assert spans == [Span(0, 3, 300), Span(3, 6, 300), Span(6, 9, 300), Span(9, 10, 100)]


def chunked() -> Workflow:
    return workflow(
        [node("start", "trigger"), node("read", "script"), node("gather", "join")],
        {
            "start": {"main": [edge("read", "chunk", chunk={"by": "items", "size": 10})]},
            "read": {"main": [edge("gather")]},
        },
    )


def test_two_failed_chunks_rerun_alone_and_the_join_keeps_partition_order(tmp_path: Path) -> None:
    script = Script(
        lambda job, chunk: [job.partition, len(chunk) if isinstance(chunk, list) else 0],
        failing={("read", 0, 1), ("read", 0, 4)},
    )
    flow = Flow(tmp_path, chunked(), {"script": script})

    first = flow.start(list(range(60)))
    mark = len(flow.events)
    ended = flow.resume(LATER)

    assert (first.status, first.reason) == (
        "failed",
        "join gather join_failed: all join has 4 of 6 needed partitions; 2 of 6 failed",
    )
    assert sorted(c for c in script.calls[:6] if c[0] == "read") == [
        ("read", 0, p) for p in range(6)
    ]
    assert [c for c in script.calls[6:] if c[0] == "read"] == [("read", 0, 1), ("read", 0, 4)]
    assert started_slots(flow.events[mark:], "read") == [(1, 2), (4, 2)]
    assert ended.outputs == {"gather": {"main": [[p, 10] for p in range(6)]}}


def test_partition_ids_and_chunk_plans_are_the_same_for_the_same_item_list(tmp_path: Path) -> None:
    plans: list[list[tuple[JsonValue, JsonValue]]] = []
    for run_id in ("run-a", "run-b"):
        flow = Flow(tmp_path, chunked(), {"script": Script()}, run_id=run_id)
        flow.start(list(range(25)))
        plans.append(
            [(e["partition"], e["plan"]) for e in of(flow.events, "node_scheduled", "read")]
        )

    assert plans[0] == plans[1]
    assert plans[0][2] == (2, {"chunk": {"by": "items", "items": [20, 25], "tokens": 5}, "of": 3})
