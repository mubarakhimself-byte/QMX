"""Attempt overlays and staged commits (AD-51), and the script's run context and tool keys
(AD-24, AD-37), seen from a run and from the zone's own interface."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from flows import edge, folder, node, run_folder
from pydantic import JsonValue

from qmx_engine.definition.model import OutputFile
from qmx_engine.ledger.redact import redact
from qmx_engine.nodes.base import Failed, NodeJob, Ok
from qmx_engine.nodes.script import HostScript, Script
from qmx_engine.workers import zones
from qmx_engine.workers.zones import RunZone, ZoneError, home_of, zones_root
from qmx_home import resolve

START = node("start", "trigger")
CHUNK = """
    import json, os, sys
    from pathlib import Path
    item = json.load(sys.stdin)["in"]
    counter = Path(item["counter"])
    tries = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(tries))
    Path("out").mkdir()
    Path("out", f"{item['n']}.json").write_text(json.dumps({"n": item["n"], "try": tries}))
    Path("script.py").write_text("scratch")
    if item["n"] == item["fails"] and tries == 1:
        sys.exit(1)
    print(json.dumps(item["n"]))
"""


FAIL = """
    from pathlib import Path
    Path("result.json").write_text("{}")
    raise SystemExit(3)
"""


def chunks(tmp_path: Path, fails: int) -> tuple[Path, list[JsonValue]]:
    work = node("work", "script", script="scripts/chunk.py")
    work["outputs"] = {"files": [{"path": "out/<partition>.json"}]}
    work["retry"] = {"backoff_seconds": [0]}
    root = folder(
        tmp_path / "wf",
        [START, work],
        {"start": {"main": [edge("work", "broadcast")]}},
        {"chunk": CHUNK},
    )
    items: list[JsonValue] = [
        {"n": n, "fails": fails, "counter": str(tmp_path / f"tries-{n}.txt")} for n in range(3)
    ]
    return root, items


def shared(home: Path, run_id: str) -> list[str]:
    work = RunZone.of(home, run_id).work
    return sorted(p.relative_to(work).as_posix() for p in work.rglob("*") if p.is_file())


def test_a_three_chunk_run_leaves_only_the_declared_outputs_and_no_attempt_folder(
    tmp_path: Path,
) -> None:
    root, items = chunks(tmp_path, fails=-1)

    outcome, events = run_folder(root, tmp_path / "home", items)

    zone = RunZone.of(tmp_path / "home", outcome.run_id)
    committed = sorted(str(e.data["paths"]) for e in events if e.kind == "zone_committed")
    assert outcome.status == "passed"
    assert shared(tmp_path / "home", outcome.run_id) == ["out/0.json", "out/1.json", "out/2.json"]
    assert committed == ["['out/0.json']", "['out/1.json']", "['out/2.json']"]
    assert list(zone.attempts.iterdir()) == []


def test_a_retry_keeps_the_siblings_committed_files(tmp_path: Path) -> None:
    root, items = chunks(tmp_path, fails=1)

    outcome, events = run_folder(root, tmp_path / "home", items)

    work = RunZone.of(tmp_path / "home", outcome.run_id).work
    written = {n: json.loads((work / "out" / f"{n}.json").read_text()) for n in range(3)}
    retried = [e.data["partition"] for e in events if e.kind == "node_failed"]
    assert (outcome.status, retried) == ("passed", [1])
    assert written == {0: {"n": 0, "try": 1}, 1: {"n": 1, "try": 2}, 2: {"n": 2, "try": 1}}


def test_a_failed_attempt_commits_nothing_and_its_overlay_is_deleted(tmp_path: Path) -> None:
    fail = node("fail", "script", script="scripts/fail.py")
    fail["outputs"] = {"files": [{"path": "result.json"}]}
    fail["retry"] = {"max_tries": 1}
    root = folder(
        tmp_path / "wf",
        [START, fail],
        {"start": {"main": [edge("fail")]}},
        {"fail": FAIL},
    )

    outcome, events = run_folder(root, tmp_path / "home")

    zone = RunZone.of(tmp_path / "home", outcome.run_id)
    assert outcome.status == "failed"
    assert [e.kind for e in events if e.kind == "zone_committed"] == []
    assert shared(tmp_path / "home", outcome.run_id) == []
    assert list(zone.attempts.iterdir()) == []


def job(zone: RunZone, node_id: str, partition: int | None = None, attempt: int = 1) -> NodeJob:
    return NodeJob(
        run_id=zone.root.name,
        node_id=node_id,
        iteration=0,
        partition=partition,
        attempt=attempt,
        memo_key="m",
        idempotency_key=f"{zone.root.name}:{node_id}:0:{attempt}",
        node_definition={"type": "script"},
        inputs=None,
        now="2026-10-19T00:00:00+00:00",
        mode="test",
        workspace=str(zone.root),
    )


def declared(*paths: str, merge: str = "replace") -> list[OutputFile]:
    return [OutputFile.model_validate({"path": p, "merge": merge}) for p in paths]


def test_a_crash_between_the_renames_rolls_forward_at_recover(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    zone = RunZone(tmp_path / "home.zones" / "run-1")
    attempt = job(zone, "write")
    overlay = zone.open(attempt)
    (overlay.path / "a.txt").write_text("A")
    (overlay.path / "b.txt").write_text("B")
    real = os.replace

    def crash_before_the_second_file(source: str | Path, target: str | Path) -> None:
        if Path(target).name == "b.txt":
            raise KeyboardInterrupt
        real(source, target)

    monkeypatch.setattr(zones.os, "replace", crash_before_the_second_file)
    with pytest.raises(KeyboardInterrupt):
        zone.commit(attempt, overlay, declared("*.txt"), (), {"node_id": "write"})
    monkeypatch.setattr(zones.os, "replace", real)
    half = sorted(p.name for p in zone.work.iterdir() if p.is_file())

    rolled = zone.recover()

    assert half == ["a.txt"]
    assert [c.data()["paths"] for c in rolled] == [["a.txt", "b.txt"]]
    assert {p.name: p.read_text() for p in zone.work.glob("*.txt")} == {"a.txt": "A", "b.txt": "B"}
    assert list(zone.attempts.iterdir()) == []


def test_a_path_another_attempt_committed_since_this_one_opened_fails_zone_conflict(
    tmp_path: Path,
) -> None:
    zone = RunZone(tmp_path / "home.zones" / "run-1")
    first, second = job(zone, "left"), job(zone, "right")
    mine, theirs = zone.open(first), zone.open(second)
    (mine.path / "same.json").write_text('{"by": "left"}')
    (theirs.path / "same.json").write_text('{"by": "right"}')
    zone.finish(zone.commit(first, mine, declared("same.json"), (), {}))

    with pytest.raises(ZoneError) as refused:
        zone.commit(second, theirs, declared("same.json"), (), {})

    assert refused.value.code == "zone_conflict"
    assert (zone.work / "same.json").read_text() == '{"by": "left"}'


def test_append_and_keyed_merges_let_concurrent_writers_share_a_path(tmp_path: Path) -> None:
    zone = RunZone(tmp_path / "home.zones" / "run-1")
    attempts = [job(zone, "w", partition=n) for n in range(2)]
    overlays = [zone.open(a) for a in attempts]
    for n, overlay in enumerate(overlays):
        (overlay.path / "log.txt").write_text(f"line {n}\n")
        (overlay.path / "index.json").write_text(json.dumps({f"k{n}": n}))
    for a, overlay in zip(attempts, overlays, strict=True):
        files = [*declared("log.txt", merge="append"), *declared("index.json", merge="keyed")]
        zone.finish(zone.commit(a, overlay, files, (), {}))

    assert (zone.work / "log.txt").read_text() == "line 0\nline 1\n"
    assert json.loads((zone.work / "index.json").read_text()) == {"k0": 0, "k1": 1}


@pytest.mark.skipif(sys.platform != "win32", reason="a junction is a Windows link")
def test_a_junction_in_the_overlay_fails_zone_link_and_follows_nothing(tmp_path: Path) -> None:
    import _winapi

    zone = RunZone(tmp_path / "home.zones" / "run-1")
    attempt = job(zone, "link")
    overlay = zone.open(attempt)
    outside = tmp_path / "outside"
    outside.mkdir()
    _winapi.CreateJunction(str(outside), str(overlay.path / "escape"))

    with pytest.raises(ZoneError) as refused:
        zone.commit(attempt, overlay, declared("escape/*"), (), {})

    assert refused.value.code == "zone_link"


def test_the_zones_sit_in_the_folders_cache_and_lead_back_to_its_data(tmp_path: Path) -> None:
    folder = (tmp_path / "QMX").resolve()

    root = zones_root(folder / "data")

    assert root == folder / "cache" / "zones"
    assert home_of(root / "run-1" / "work") == folder / "data"


PRINT_CACHES = """
import json, os
print(json.dumps({name: os.environ.get(name) for name in ("HF_HOME", "TORCH_HOME", "XDG_CACHE_HOME")}))
"""


def test_a_script_in_a_qmx_folder_downloads_into_its_cache(tmp_path: Path) -> None:
    layout = resolve(tmp_path / "QMX", create=True, drives=[])
    code = tmp_path / "code"
    (code / "scripts").mkdir(parents=True)
    (code / "scripts" / "env.py").write_text(PRINT_CACHES)
    zone = RunZone.of(layout.home, "run-cache")
    attempt = replace(job(zone, "env"), node_definition=script_node({}))

    result = asyncio.run(Script(HostScript(code, None, (), fake=True)).run(attempt))

    assert isinstance(result, Ok)
    models = layout.root / "cache" / "models"
    assert result.outputs["main"] == {
        "HF_HOME": str(models / "huggingface"),
        "TORCH_HOME": str(models / "torch"),
        "XDG_CACHE_HOME": str(models / "xdg"),
    }


FAKE_TOOL_KEY = "fake-sec2a-tool-value-not-a-key"
PRINT_CONTEXT = """
import json, os
names = ("QMX_RUN_ID", "QMX_MODE", "QMX_FAKE", "QMX_NOW", "QMX_WORK", "QMX_WORK_SHARED",
         "QMX_CODE", "SEARCH_KEY")
print(json.dumps({name: os.environ.get(name) for name in names}))
"""


def script_node(credentials: dict[str, JsonValue]) -> dict[str, JsonValue]:
    return {
        "type": "script",
        "parameters": {"script": "scripts/env.py"},
        "credentials": credentials,
    }


def test_a_script_gets_the_run_context_and_its_tool_key_registered_for_redaction(
    tmp_path: Path,
) -> None:
    code = tmp_path / "code"
    (code / "scripts").mkdir(parents=True)
    (code / "scripts" / "env.py").write_text(PRINT_CONTEXT)
    zone = RunZone(tmp_path / "home.zones" / "run-ctx")
    attempt = replace(
        job(zone, "env"), node_definition=script_node({"SEARCH_KEY": "qmx/tool/search"})
    )
    host = HostScript(code, None, (), fake=True, resolve={"qmx/tool/search": FAKE_TOOL_KEY}.get)

    result = asyncio.run(Script(host).run(attempt))

    assert isinstance(result, Ok)
    seen = result.outputs["main"]
    assert seen == {
        "QMX_RUN_ID": "run-ctx",
        "QMX_MODE": "test",
        "QMX_FAKE": "1",
        "QMX_NOW": "2026-10-19T00:00:00+00:00",
        "QMX_WORK": str(zone.overlay(attempt)),
        "QMX_WORK_SHARED": str(zone.work),
        "QMX_CODE": str(code),
        "SEARCH_KEY": FAKE_TOOL_KEY,
    }
    assert redact(json.dumps(seen)).count("[redacted:qmx/tool/search]") == 1


def test_a_provider_key_named_as_a_tool_credential_is_refused(tmp_path: Path) -> None:
    code = tmp_path / "code"
    (code / "scripts").mkdir(parents=True)
    (code / "scripts" / "env.py").write_text(PRINT_CONTEXT)
    zone = RunZone(tmp_path / "home.zones" / "run-ref")
    attempt = replace(job(zone, "env"), node_definition=script_node({"KEY": "qmx/openrouter"}))
    host = HostScript(code, None, (), resolve=lambda _: pytest.fail("no ref may be resolved"))

    result = asyncio.run(Script(host).run(attempt))

    assert isinstance(result, Failed)
    assert result.code == "credential_refused"
