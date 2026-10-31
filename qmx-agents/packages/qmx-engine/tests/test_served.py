"""A script node's Library reads and writes, served by the runner through the host's real store.

Every case runs against `EngineLibraryAdapter(Store.open(tmp))`, because what it proves (a new
item on every put, the intent annotation, the `find_by_intent` join, landing) is the store's own
behaviour, which no recording port has.
"""

from __future__ import annotations

import ast
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import JsonValue
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.store import Store

from qmx_engine.ledger import redact
from qmx_engine.nodes.base import Failed, NodeJob
from qmx_engine.nodes.script import Served
from qmx_engine.ports.library import JsonObject, Mode, RunStatus, RunSummary, Stored
from qmx_engine.service.api import EngineService

SRC = Path(__file__).parents[1] / "src" / "qmx_engine"


class FullAfter(EngineLibraryAdapter):
    """The real adapter on a store that runs out of room after `room` artifacts."""

    def __init__(self, store: Store, room: int) -> None:
        super().__init__(store)
        self.room = room

    def put_artifact(self, data: bytes, type_: str, metadata: JsonObject, **given: Any) -> Stored:
        self.room -= 1
        if self.room < 0:
            self.store.floor_bytes = 1 << 62
        return super().put_artifact(data, type_, metadata, **given)


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "library", redactor=redact) as opened:
        yield opened


def job(run_id: str, attempt: int, inputs: JsonValue = None, **parameters: JsonValue) -> NodeJob:
    return NodeJob(
        run_id=run_id,
        node_id="write",
        iteration=0,
        partition=None,
        attempt=attempt,
        memo_key="m",
        idempotency_key=f"{run_id}:write:0:{attempt}",
        node_definition={"type": "script", "parameters": parameters},
        inputs=inputs if inputs is not None else {"in": {}},
        now=None,
    )


def bodies(overlay: Path, *names: str) -> Path:
    (overlay / "library").mkdir(parents=True, exist_ok=True)
    for name in names:
        (overlay / "library" / name).write_text(json.dumps({"name": name}), encoding="utf-8")
    return overlay


def put(name: str, **more: JsonValue) -> JsonObject:
    return {"op": "put_artifact", "as": name, "type": "clipping", "body": f"library/{name}"} | more


def written(done: JsonValue | Failed) -> list[dict[str, Any]]:
    assert isinstance(done, dict), done
    return cast(list[dict[str, Any]], done["library_written"])


def on_ref(store: Store, run_id: str) -> list[str]:
    return [object_id for _, object_id in store.heads_on(f"refs/runs/{run_id}")]


def summary(run_id: str, status: str, mode: str = "live", *, fake: bool = False) -> RunSummary:
    return RunSummary(
        run_id, "clips", "obj", cast(Mode, mode), cast(RunStatus, status), None, {}, {}, None,
        "operator", fake,
    )  # fmt: skip


def test_a_retried_attempt_of_the_same_slot_writes_nothing_twice(
    store: Store, tmp_path: Path
) -> None:
    served = Served(EngineLibraryAdapter(store), "r1", "clips")
    overlay = bodies(tmp_path / "o", "a.json", "b.json")
    output: JsonObject = {"summary": "two", "library": [put("a.json"), put("b.json")]}

    first = served.writes(job("r1", 1), output, overlay)
    second = served.writes(job("r1", 2), output, overlay)

    assert first == second
    assert {r["object_id"] for r in written(first)} == set(on_ref(store, "r1"))
    assert len(on_ref(store, "r1")) == 2
    assert sorted(cast(dict[str, Any], first)) == ["library_written", "summary"]


def test_a_write_refused_for_room_fails_the_node_and_the_retry_writes_only_what_is_left(
    store: Store, tmp_path: Path
) -> None:
    overlay = bodies(tmp_path / "o", "a.json", "b.json", "c.json")
    output: JsonObject = {"library": [put("a.json"), put("b.json"), put("c.json")]}

    failed = Served(FullAfter(store, 2), "r1", "clips").writes(job("r1", 1), output, overlay)
    store.floor_bytes = 0
    adapter = EngineLibraryAdapter(store)
    adapter.put_run_summary(summary("r1", "failed"), principal="run:r1")
    landed_after_failure = adapter.moved_to_main(0)
    retried = Served(adapter, "r1", "clips").writes(job("r1", 2), output, overlay)

    assert isinstance(failed, Failed)
    assert (failed.code, failed.retryable, failed.effect_state) == ("disk_full", False, "after")
    assert len(on_ref(store, "r1")) == 4
    assert [r["refused"] for r in written(retried)] == [None, None, None]
    assert landed_after_failure == []


def test_a_forged_principal_ref_or_engine_edge_is_ignored_or_refused(
    store: Store, tmp_path: Path
) -> None:
    adapter = EngineLibraryAdapter(store)
    held = adapter.put_artifact(b"his", "clipping", {}, run_id="old", principal="run:old")
    overlay = bodies(tmp_path / "o", "a.json")
    forged = put("a.json", principal="operator", ref="main", run_id="old")
    output: JsonObject = {
        "library": [
            forged,
            {"op": "link", "from": "$a.json", "edge": "produced-by", "to": held.object_id},
            {"op": "link", "from": held.object_id, "edge": "consumed", "to": held.object_id},
            {"op": "link", "from": "$a.json", "edge": "consumed", "to": "fp1:no-such-object"},
            {"op": "link", "from": "$a.json", "edge": "consumed", "to": held.object_id},
        ]
    }

    receipts = written(Served(adapter, "r1", "clips").writes(job("r1", 1), output, overlay))
    made = adapter.get(receipts[0]["object_id"])

    assert (made.ref, made.principal) == ("refs/runs/r1", "run:r1")
    assert [r["refused"] for r in receipts[1:]] == [
        "produced-by is not an edge a script writes",
        "from is not a write of this step",
        "unknown_object",
        None,
    ]
    assert [(e.edge, e.to_id) for e in adapter.edges(made.object_id)] == [
        ("consumed", held.object_id)
    ]


def test_a_replica_store_fails_the_node_with_its_own_refusal(tmp_path: Path) -> None:
    overlay = bodies(tmp_path / "o", "a.json")
    with Store.open(tmp_path / "pc", redactor=redact, role="replica") as replica:
        done = Served(EngineLibraryAdapter(replica), "r1", "clips").writes(
            job("r1", 1), {"library": [put("a.json")]}, overlay
        )

    assert isinstance(done, Failed)
    assert (done.code, done.retryable, done.effect_state) == ("read_only_replica", False, "before")


def test_an_inline_body_or_a_body_outside_the_overlay_library_fails_by_name(
    store: Store, tmp_path: Path
) -> None:
    served = Served(EngineLibraryAdapter(store), "r1", "clips")
    overlay = bodies(tmp_path / "o")
    (overlay / "secret.json").write_text("{}", encoding="utf-8")

    inline = served.writes(job("r1", 1), {"library": [put("x", body=None, text="hi")]}, overlay)
    outside = served.writes(job("r1", 1), {"library": [put("x", body="secret.json")]}, overlay)

    assert isinstance(inline, Failed) and isinstance(outside, Failed)
    assert (inline.code, outside.code) == ("library_body_missing", "library_body_missing")
    assert on_ref(store, "r1") == []


def test_duplicates_count_only_a_passed_live_run_on_real_models_of_the_same_workflow(
    store: Store, tmp_path: Path
) -> None:
    adapter = EngineLibraryAdapter(store)
    overlay = bodies(tmp_path / "o", "a.json")
    ask = job(
        "r9",
        1,
        {"in": {"clippings": [{"intent_key": "k1"}]}},
        library_reads={"held": {"find_by_intent": "clippings.intent_key"}},
    )
    made: dict[str, str] = {}
    for run_id, status, mode, fake in (
        ("test", "passed", "test", False),
        ("fake", "passed", "live", True),
        ("failed", "failed", "live", False),
        ("live", "passed", "live", False),
    ):
        done = Served(adapter, run_id, "clips").writes(
            job(run_id, 1), {"library": [put("a.json", intent_key="k1")]}, overlay
        )
        made[run_id] = written(done)[0]["object_id"]
        ran = adapter.put_run_summary(
            summary(run_id, status, mode, fake=fake), principal=f"run:{run_id}"
        )
        adapter.link(made[run_id], "produced-by", ran.object_id, principal=f"run:{run_id}")

    mine = Served(adapter, "r9", "clips").reads(ask)
    theirs = Served(adapter, "r9", "other-workflow").reads(ask)
    landed = {event.object_id for event in adapter.moved_to_main(0)}

    assert mine == {"held": {"k1": [made["live"]]}}
    assert theirs == {"held": {"k1": []}}
    assert landed & set(made.values()) == {made["live"]}


def test_a_read_is_served_while_the_hosts_store_holds_the_writer_lock(
    store: Store, tmp_path: Path
) -> None:
    adapter = EngineLibraryAdapter(store)
    adapter.put_artifact(b"x", "clipping", {}, run_id="r1", principal="run:r1")
    adapter.put_run_summary(summary("r1", "passed"), principal="run:r1")
    served = Served(adapter, "r2", "digest")
    reads = served.reads(
        job(
            "r2",
            1,
            {"in": {"position": 0}},
            library_reads={
                "landed": {"moved_to_main_after": "position"},
                "log": {"last_seq": ""},
            },
        )
    )

    assert isinstance(reads, dict)
    assert sorted(row["name"] for row in cast(list[dict[str, str]], reads["landed"])) == [
        "library.artifact.landed",
        "library.workflow-run.landed",
    ]
    assert reads["log"] == store.last_seq() > 0


def test_no_production_module_imports_the_library_fake() -> None:
    importing = sorted(
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if path.name != "library_fake.py"
        and any(
            isinstance(node, ast.ImportFrom) and node.module == "qmx_engine.ports.library_fake"
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        )
    )

    assert importing == []


def test_the_engine_service_has_no_library_default(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="library"):
        EngineService.open(tmp_path).__enter__()  # type: ignore[call-arg]
