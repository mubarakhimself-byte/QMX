from __future__ import annotations

import asyncio
import json
import secrets
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from fastmcp import Client

from qmx_control.cache import read_cache
from qmx_control.library import Library, encoded
from qmx_control.models import Document, MemoKey
from qmx_control.server import create_app, create_mcp
from qmx_control.service import ControlError, ControlService, LibraryInput

TOKEN = secrets.token_urlsafe(32)
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def test_library_versions_fts_links_and_restart(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    first = service.library_save(
        LibraryInput(
            title="Rates",
            kind="strategy",
            tags=["macro"],
            content={"lookback": 10},
            extracted_text="Treasury momentum",
        )
    )
    second = service.library_save(
        LibraryInput(
            title="Rates v2",
            kind="strategy",
            previous_id=str(first["id"]),
            content={"lookback": 20},
        )
    )
    assert service.library_get(str(first["id"])) == first
    assert service.library_versions(str(second["id"])) == [first, second]
    assert first["root_id"] == first["id"]
    for query in ("macro", "momentum", 'title:"Rates"'):
        assert first in service.library_search(query)
    assert service.library_search("nonsense") == []
    with pytest.raises(ControlError, match="latest"):
        service.library_save(
            LibraryInput(title="stale", kind="strategy", content={}, previous_id=str(first["id"]))
        )
    with pytest.raises(ControlError, match="type"):
        service.library_save(
            LibraryInput(title="wrong", kind="pod", content={}, previous_id=str(second["id"]))
        )
    linked = service.library_link(str(first["id"]), str(second["id"]), "derived")
    assert service.library_links(str(second["id"])) == [linked]
    reopened = ControlService(tmp_path)
    assert reopened.library_versions(str(second["id"])) == [first, second]
    assert (tmp_path / str(first["ref"])).read_bytes() == encoded(first["content"])
    assert (tmp_path / "library.db").exists()
    with pytest.raises(ControlError, match="FTS5"):
        service.library_search('"')
    (tmp_path / str(first["ref"])).write_bytes(b"tampered")
    with pytest.raises(ControlError, match="hash"):
        reopened.library_get(str(first["id"]))


def test_web_results_are_saved_once_per_url_and_day(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    item = LibraryInput(
        title="Article",
        kind="article",
        source="https://example.org/article",
        fetched_date="2026-10-08",
        content={"text": "research"},
    )
    first = service.library_save(item)
    assert service.library_save(item.model_copy(update={"content": "new"})) == first
    next_day = service.library_save(item.model_copy(update={"fetched_date": "2026-10-09"}))
    assert next_day["id"] != first["id"]
    assert next_day["sha256"] == first["sha256"]
    with pytest.raises(ControlError, match="valid"):
        service.library_save(item.model_copy(update={"fetched_date": "2026-02-30"}))


def test_old_control_catalog_is_migrated(tmp_path: Path) -> None:
    tmp_path.mkdir(exist_ok=True)
    with closing(sqlite3.connect(tmp_path / "control.db")) as db, db:
        db.execute("CREATE TABLE library(id TEXT PRIMARY KEY,data TEXT)")
        db.execute(
            "INSERT INTO library VALUES(?,?)",
            (
                "saved-id",
                json.dumps(
                    {
                        "id": "saved-id",
                        "title": "old",
                        "kind": "pod",
                        "content": {"value": 1},
                    }
                ),
            ),
        )
    service = ControlService(tmp_path)
    assert service.library_get("saved-id")["content"] == {"value": 1}
    assert ControlService(tmp_path).library_get("saved-id")["id"] == "saved-id"


def test_legacy_domain_envelopes_enter_the_shared_catalog(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    body = json.dumps({"name": "legacy note", "kind": "note", "content": "precious"}).encode()
    digest = sha256(body).hexdigest()
    (artifacts / f"{digest}.json").write_bytes(body)
    service = ControlService(tmp_path)
    saved = service.library_search("precious")[0]
    assert saved["id"] == digest
    assert service.library.by_ref(f"artifacts/{digest}.json") == saved
    assert len(ControlService(tmp_path).library_search()) == 1


def test_aggregate_cache_detects_another_owner_event(tmp_path: Path) -> None:
    reader = ControlService(tmp_path)
    assert reader.aggregates_get()["library_items"] == 0
    writer = ControlService(tmp_path)
    writer.library_save(LibraryInput(title="later", kind="note", content={}))
    assert reader.aggregates_get()["library_items"] == 1
    pushed = reader.events("aggregates")[-1]["data"]
    assert isinstance(pushed, dict)
    assert pushed["library_items"] == 1


@pytest.mark.parametrize(
    "changed",
    [
        {"strategy_version": "v2"},
        {"data_snapshot": "bars2"},
        {"params": {"lookback": 21}},
        {"engine_version": "qmb2"},
    ],
)
def test_memo_uses_all_four_parts_and_survives_restart(
    tmp_path: Path, changed: dict[str, Any]
) -> None:
    library = Library(tmp_path)
    identity = MemoKey(
        strategy_version="v1", data_snapshot="bars1", params={"lookback": 20}, engine_version="qmb1"
    )
    calls = 0

    def produce() -> LibraryInput:
        nonlocal calls
        calls += 1
        return LibraryInput(title="backtest", kind="report", content={"calls": calls})

    first = library.memoized(identity, produce)
    assert library.memoized(identity, produce) == first
    assert Library(tmp_path).memoized(identity, produce) == first
    assert calls == 1
    assert library.memoized(identity.model_copy(update=changed), produce)["id"] != first["id"]
    assert calls == 2


def test_concurrent_memo_only_computes_once(tmp_path: Path) -> None:
    library = Library(tmp_path)
    identity = MemoKey(strategy_version="v1", data_snapshot="data", params={}, engine_version="1")
    calls = 0

    def produce() -> LibraryInput:
        nonlocal calls
        calls += 1
        return LibraryInput(title="result", kind="report", content={"ok": True})

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [
            future.result()
            for future in [pool.submit(library.memoized, identity, produce) for _ in range(4)]
        ]
    assert all(result == results[0] for result in results)
    assert calls == 1


def test_read_cache_expires_without_caching_failures() -> None:
    clock = [0.0]
    calls = 0

    @read_cache(ttl=5, timer=lambda: clock[0])
    def expensive(value: int) -> int:
        nonlocal calls
        calls += 1
        if value < 0:
            raise ValueError("unavailable")
        return calls

    assert expensive(1) == expensive(1) == 1
    clock[0] = 6
    assert expensive(1) == 2
    expensive.cache_clear()
    assert expensive(1) == 3
    for _ in range(2):
        with pytest.raises(ValueError):
            expensive(-1)
    assert calls == 5


def append(path: Path, run_id: str, seq: int, event: str, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record: Document = {
        "run_id": run_id,
        "seq": seq,
        "time": f"2026-10-08T00:00:0{seq}+00:00",
        "event": event,
        "payload": payload,
    }
    record["fingerprint"] = sha256(encoded(record)).hexdigest()
    with path.open("ab") as stream:
        stream.write(encoded(record) + b"\n")


def test_run_projection_validates_journal_and_updates_events(tmp_path: Path) -> None:
    path = tmp_path / "journals" / "remote-r1.jsonl"
    append(path, "r1", 1, "run_start", {"kind": "workflow", "target": "laptop", "node": "local"})
    append(
        path,
        "r1",
        2,
        "model_call",
        {"agent": "researcher", "model": {"resolved": "fake:model"}, "metadata": {"cost": "0.05"}},
    )
    append(path, "r1", 3, "tool_end", {"result_ref": "artifacts/abc"})
    service = ControlService(tmp_path)
    service.aggregates_get()
    run = service.run_index.get("r1")
    assert run["model"] == {"researcher": {"resolved": "fake:model"}}
    assert run["cost"] == "0.05"
    assert run["artifacts"] == ["artifacts/abc"]
    assert run["target"] == "laptop"
    assert run["status"] == "running"
    events = service.events("runs")
    service.aggregates_get()
    assert service.events("runs") == events
    append(path, "r1", 4, "run_end", {"status": "completed"})
    service.aggregates_get()
    assert service.run_index.get("r1")["ended"] == "2026-10-08T00:00:04+00:00"
    assert service.aggregates_get()["runs"] == 1
    assert len(service.events("runs")) == 2
    with path.open("ab") as stream:
        stream.write(b'{"seq":5')
    assert service.run_index.get("r1")["status"] == "completed"
    path.write_bytes(path.read_bytes().replace(b"completed", b"cancelled"))
    with pytest.raises(ControlError, match="journal"):
        service.aggregates_get()


def test_library_run_and_aggregate_doors_match(tmp_path: Path) -> None:
    service = ControlService(tmp_path)

    async def exercise() -> None:
        async with Client(create_mcp(service)) as mcp:
            with TestClient(create_app(service, TOKEN)) as rest:
                initial = rest.get("/api/aggregates", headers=HEADERS).json()
                assert initial["library_items"] == 0
                item = rest.post(
                    "/api/library",
                    headers=HEADERS,
                    json={
                        "title": "pod",
                        "kind": "pod",
                        "content": {"strategy": "alpha"},
                    },
                ).json()
                artifact_id = item["id"]
                cases: list[tuple[str, str, dict[str, Any]]] = [
                    ("library_get", f"/api/library/{artifact_id}", {"artifact_id": artifact_id}),
                    (
                        "library_versions",
                        f"/api/library/{artifact_id}/versions",
                        {"artifact_id": artifact_id},
                    ),
                    (
                        "library_links",
                        f"/api/library/{artifact_id}/links",
                        {"artifact_id": artifact_id},
                    ),
                    ("ops_aggregates", "/api/aggregates", {}),
                ]
                for name, url, args in cases:
                    assert (await mcp.call_tool(name, args)).data == rest.get(
                        url, headers=HEADERS
                    ).json()
                updated = rest.get("/api/aggregates", headers=HEADERS).json()
                assert updated["library_items"] == 1
                assert updated["revision"] > initial["revision"]
                stream = rest.get("/api/events/aggregates?max_events=1", headers=HEADERS)
                assert "event: aggregates" in stream.text
                assert '"library_items": 1' in stream.text

    asyncio.run(exercise())


def test_the_run_index_never_lists_a_chat_journal(tmp_path: Path) -> None:
    chat = tmp_path / "runs" / "chat-1" / "journal.jsonl"
    append(chat, "chat-1", 1, "run_start", {"kind": "agent", "session_id": "chat-1"})
    remote = tmp_path / "journals" / "remote-r2.jsonl"
    append(remote, "r2", 1, "run_start", {"kind": "job", "target": "contabo"})
    with closing(sqlite3.connect(tmp_path / "runs.db")) as db, db:
        db.execute("CREATE TABLE runs(id TEXT PRIMARY KEY,data TEXT NOT NULL)")
        db.execute(
            "INSERT INTO runs VALUES(?,?)",
            ("chat-0", json.dumps({"id": "chat-0", "journal": str(chat.with_name("old.jsonl"))})),
        )
    service = ControlService(tmp_path)
    service.run_index.refresh()
    assert [run["id"] for run in service.run_index.list(0, 100)] == ["r2"]
    with pytest.raises(ControlError, match="Unknown run id"):
        service.run_index.get("chat-1")


def test_a_background_run_keeps_its_model_and_a_mirrored_chat_stays_out(tmp_path: Path) -> None:
    ControlService(tmp_path).close()
    chat = tmp_path / "runs" / "chat-1" / "journal.jsonl"
    append(chat, "chat-1", 1, "run_start", {"agent": "primary", "session_id": "chat-1"})
    row = {"id": "chat-1", "kind": "agent", "session_id": "chat-1", "journal": str(chat)}
    with closing(sqlite3.connect(tmp_path / "runs.db")) as db, db:
        db.execute("INSERT INTO runs VALUES(?,?)", ("chat-1", json.dumps(row)))
    service = ControlService(tmp_path)
    service.run_index.record("bg-1", {"session_id": "child-1", "status": "running"})
    background = tmp_path / "runs" / "bg-1" / "journal.jsonl"
    append(background, "bg-1", 1, "run_start", {"agent": "builder", "session_id": "child-1"})
    append(background, "bg-1", 2, "model_call", {"agent": "builder", "model": "fake:model"})
    append(background, "bg-1", 3, "run_end", {"status": "completed"})
    assert [run["id"] for run in service.run_index.refresh()] == ["bg-1"]
    assert service.run_index.get("bg-1")["model"] == {"builder": "fake:model"}
    service.close()
    service = ControlService(tmp_path)
    service.run_index.refresh()
    assert [run["id"] for run in service.run_index.list(0, 100)] == ["bg-1"]
    assert service.run_index.get("bg-1")["status"] == "completed"
