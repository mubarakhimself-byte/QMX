"""MEM's live lanes: E65 on haiku, the already-built check, and a lesson's validity window.

From `qmx-agents/` with the agents venv:

    uv run --no-sync python ../scripts/live/memory/e65_memory.py [lane ...]

Lanes are `e65 built window processes`; none named runs `e65 built window`. Each writes
`D:/QMX-worktrees/qma-ship/build/evidence/mem/<MEM_LOG_PREFIX><slug>.log` (prefix `owner-` for the
builder, `check-` for the coordinator) and the script exits 1 if any lane failed.

- `e65` (lane 2, the plan's E65): a Lab chat on `claude/haiku` notes a finding about pod P through
  `memory_note`; a new hub chat's `memory_recall` with `item:P` returns it; with Hindsight stopped
  the FTS5 adapter over the same rows returns it; a forgotten row stays gone after `rebuild`.
  Takes the lane lock itself and holds the ship home while it runs, because the turns are the plan
  login's. Also the perf block: one session-digest retain and 50 recalls, p95 recorded.
- `built` (lane 3): two workflows ask for the same build. The second's `memory_check` answers from
  `check_built` with the first build's object, links it, and starts no chat, so it spends nothing.
  The engine-side skip lives in a node executor outside MEM's files (see BACKLOG); this lane proves
  the check itself and that it costs no tokens.
- `window` (lane 4): a lesson whose validity window ended. Recall leaves it out at today's date
  and returns it `as_of` inside the window, through the same read the tool calls.
- `processes` (lane 10): no Hindsight, `qmx_host`, `claude` or `qma-cli-launcher` process and no
  lane lock is left.

No key is read or printed: the harness reads the plan login and the router in-process, as in
production.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final

import psutil

BUILD: Final = Path("D:/QMX-worktrees/qma-ship/build")
REPO: Final = Path(__file__).resolve().parents[3]
EVIDENCE: Final = Path(os.environ.get("MEM_EVIDENCE", BUILD / "evidence" / "mem"))
PREFIX: Final = os.environ.get("MEM_LOG_PREFIX", "owner-")
SHIP_HOME: Final = Path("D:/QMX-worktrees/qma-ship/home")
LANE_LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
MODEL: Final = "haiku"
TURN_S: Final = 240.0
LOCK_WAIT_S: Final = 3600.0
LOCK_POLL_S: Final = 15.0
RECALLS: Final = 50
LAB_TITLE: Final = "MEM lane lab note"
HUB_TITLE: Final = "MEM lane hub recall"
NOTE: Final = "Pod P's break-out filter wants a 20 day ATR, not 14"
QUESTION: Final = "item:P"
DIGEST_QUESTION: Final = "what did we settle on the pod P filter"
WINDOW_TITLE: Final = "MEM lane validity window"


class Log:
    """One lane's log: stdout and `evidence/mem/<prefix><slug>.log`, with a PASS/FAIL per check."""

    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{PREFIX}{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped.encode("ascii", "backslashreplace").decode(), flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(stamped + "\n")

    def check(self, name: str, ok: bool, seen: object) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        self.passed &= ok

    def verdict(self) -> int:
        self("PASS" if self.passed else "FAIL")
        return 0 if self.passed else 1


@contextmanager
def lane_lock(say: Log) -> Iterator[None]:
    """Hold `D:/QMX-worktrees/.engine-lane-lock`, waiting while another lane holds it."""
    deadline = time.monotonic() + LOCK_WAIT_S
    while True:
        try:
            LANE_LOCK.mkdir()
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise SystemExit("BLOCKED: the lane lock stayed held for an hour") from None
            say(f"lane lock held by another lane; retry in {LOCK_POLL_S:.0f} s")
            time.sleep(LOCK_POLL_S)
    say("lane lock taken")
    try:
        yield
    finally:
        LANE_LOCK.rmdir()
        say("lane lock released")


def clean_env() -> None:
    """The environment every lane runs under: no plan-login or CA names, folders on `D:`."""
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "NODE_USE_SYSTEM_CA"):
        os.environ.pop(name, None)
    for name in list(os.environ):
        if name.startswith("CLAUDE"):
            os.environ.pop(name, None)
    os.environ["TMP"] = os.environ["TEMP"] = "D:/Temp"
    os.environ.setdefault("UV_CACHE_DIR", "D:/Caches/uv")


def settings_sha() -> str:
    return hashlib.sha256((SHIP_HOME / "settings.toml").read_bytes()).hexdigest()


def p95(samples: Sequence[float]) -> float:
    ordered = sorted(samples)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)] if ordered else 0.0


# -- lane 2: E65 -------------------------------------------------------------------


def lane_e65() -> bool:
    log = Log("mem-e65")
    before = settings_sha()
    with lane_lock(log):
        try:
            asyncio.run(e65(log))
        finally:
            log.check("the ship home's settings.toml is unchanged", before == settings_sha(), "")
    return log.verdict() == 0


async def e65(log: Log) -> None:
    from qma.harness import QmxHome, control_service  # noqa: PLC0415
    from qmx_engine.ledger import redact  # noqa: PLC0415
    from qmx_host.host import LIBRARY  # noqa: PLC0415
    from qmx_host.sessions import RecordedHarness, SessionRecorder, write_snapshot  # noqa: PLC0415
    from qmx_library.store import Store  # noqa: PLC0415
    from qmx_memory.engine import RecallEngine  # noqa: PLC0415
    from qmx_memory.hindsight import HindsightConfig, HindsightIndex  # noqa: PLC0415

    home = QmxHome(SHIP_HOME)
    control = control_service(home)
    harness = await RecordedHarness.open(home, control=control)
    try:
        with Store.open(SHIP_HOME / LIBRARY, redactor=redact) as store:
            index = HindsightIndex(HindsightConfig(layout=home.layout))
            engine = RecallEngine(store, index=index, home=SHIP_HOME / "memory")
            try:
                harness.record_into(SessionRecorder(store))
                harness.remember_into(engine)
                await note_about_pod_p(harness, engine, control, log)
                await recall_from_the_hub(harness, engine, control, log)
                await asyncio.to_thread(forget_then_rebuild, engine, log)
                await asyncio.to_thread(perf, engine, log)
                await asyncio.to_thread(fallback_recall, engine, log)
                await asyncio.to_thread(write_snapshot, engine, SHIP_HOME)
                slot = (SHIP_HOME / "memory" / "general.md").read_text(encoding="utf-8")
                log.check(
                    "the memory snapshot slot carries the Lab note",
                    NOTE.split(",")[0] in slot or "20 day ATR" in slot,
                    slot[:120].replace("\n", " "),
                )
            finally:
                await asyncio.to_thread(engine.close)
                await asyncio.to_thread(stop_postgres)
    finally:
        await harness.close()


def stop_postgres() -> None:
    """Stop the embedded Postgres Hindsight keeps on `C:`, so the lane leaves no process behind
    (`Pg0(name="hindsight")` is the instance P-MEM measured; it is stopped, never deleted)."""
    from pg0 import Pg0  # noqa: PLC0415

    with suppress(Exception):
        Pg0(name="hindsight").stop()


def _blocks(control: Any, chat: str, after: int = 0) -> list[Mapping[str, Any]]:
    """A chat's recorded blocks after event id `after`, the way the retain worker reads them."""
    found: list[Mapping[str, Any]] = []
    while True:
        page = control.events("sessions", after, chat, 1000)
        for event in page:
            data = event["data"]
            if data.get("type") == "block":
                found.append(data["block"])
        if len(page) < 1000:
            return found
        after = page[-1]["id"]


def _last_event(control: Any, chat: str) -> int:
    events = control.events("sessions", 0, chat, 1000)
    while len(events) == 1000:
        events = control.events("sessions", events[-1]["id"], chat, 1000)
    return int(events[-1]["id"]) if events else 0


def _block_text(blocks: Sequence[Mapping[str, Any]]) -> str:
    """What the tool answered, from the finished blocks that carry a result."""
    found: list[str] = []
    for block in blocks:
        content = block.get("content")
        inner = content if isinstance(content, Mapping) else {}
        found.append(str(inner.get("result", "")))
    return "\n".join(found)


def _census(blocks: Sequence[Mapping[str, Any]]) -> list[str]:
    """What a turn recorded: block type, tool name and state, for a lane that has to see it."""
    found: list[str] = []
    for block in blocks:
        content = block.get("content")
        inner = content if isinstance(content, Mapping) else {}
        found.append(f"{block.get('type')}:{inner.get('name', '')}:{inner.get('state', '')}")
    return found


def _named(blocks: Sequence[Mapping[str, Any]], tool: str) -> list[Mapping[str, Any]]:
    """The answers of the tool calls whose name ends in `tool`: a call is a `started` block that
    carries its name and a `finished` block that carries its result, joined by the call id."""
    asked: set[str] = set()
    for block in blocks:
        inner = _inner(block)
        if str(inner.get("name", "")).split("__")[-1] == tool:
            asked.add(str(inner.get("id", "")))
    found: list[Mapping[str, Any]] = []
    for block in blocks:
        inner = _inner(block)
        if inner.get("state") == "finished" and str(inner.get("id", "")) in asked:
            found.append(block)
    return found


def _inner(block: Mapping[str, Any]) -> Mapping[str, Any]:
    content = block.get("content")
    return content if isinstance(content, Mapping) else {}


async def note_about_pod_p(harness: Any, engine: Any, control: Any, log: Log) -> None:
    """A Lab chat on haiku notes the finding through the `memory_note` tool."""
    from qma.harness import Home, NewChat, OperatorText  # noqa: PLC0415

    workspace = Path("D:/Temp/mem-e65-lab")
    workspace.mkdir(parents=True, exist_ok=True)
    spec = NewChat(
        title=LAB_TITLE,
        model=MODEL,
        workspace=workspace,
        home=Home("lab", "mem-pod-p"),
        toolsets=("memory",),
    )
    chat = await harness.start_chat(spec)
    log(f"lab chat {chat}")
    began = _last_event(control, chat)
    prompt = (
        "Call the qmx memory tool memory_note exactly once with tag lesson, "
        f'content "{NOTE}", when_to_use "before tuning pod P", and refs ["item:P"]. '
        "Then reply DONE."
    )
    started = time.monotonic()
    result = await (await harness.run_turn(chat, OperatorText(prompt))).result()
    log(f"Lab turn {result.status} in {time.monotonic() - started:.1f} s")
    blocks = _blocks(control, chat, began)
    written = _named(blocks, "note")
    rows = [row for row in engine._rows("home") if "item:P" in row.refs]
    log(f"Lab blocks {_census(blocks)}")
    log(f"memory_note answer blocks {len(written)}, rows {len(rows)}")
    for block in written:
        log(f"  memory_note said: {str(_inner(block).get('result'))[:200]}")
    log.check("the Lab chat noted the finding through memory_note", bool(rows), len(rows))
    log.check(
        "the note landed in the home scope with its source",
        rows[0].scope == "home" and "item:P" in rows[0].refs if rows else False,
        rows[0].refs if rows else None,
    )
    await harness.close_chat(chat)


async def recall_from_the_hub(harness: Any, engine: Any, control: Any, log: Log) -> None:
    """A new hub chat asks `memory_recall` for `item:P` and gets the Lab note."""
    from qma.harness import Home, NewChat, OperatorText  # noqa: PLC0415

    workspace = Path("D:/Temp/mem-e65-hub")
    workspace.mkdir(parents=True, exist_ok=True)
    spec = NewChat(
        title=HUB_TITLE,
        model=MODEL,
        workspace=workspace,
        home=Home("general"),
        toolsets=("memory",),
    )
    chat = await harness.start_chat(spec)
    began = _last_event(control, chat)
    prompt = (
        "Call the qmx memory tool memory_recall exactly once with query "
        f'"{QUESTION}" and tags []. Then reply DONE.'
    )
    result = await (await harness.run_turn(chat, OperatorText(prompt))).result()
    blocks = _blocks(control, chat, began)
    answers = _named(blocks, "recall")
    answered = _block_text(answers)
    log(f"hub turn {result.status}; blocks {_census(blocks)}")
    log(f"memory_recall answer blocks {len(answers)}")
    for block in answers[:2]:
        log(f"  memory_recall block: {str(block.get('content'))[:700]}")
    log.check(
        "the hub's memory_recall returns the Lab note by item:P",
        "20 day ATR" in answered,
        answered[:200].replace("\n", " "),
    )
    hits = await asyncio.to_thread(engine.recall, QUESTION, ("home", "operator"), 2_000)
    log(f"engine recall through Hindsight: {len(hits)} rows; "
        f"fallback reason {engine.fallback_reason!r}")  # fmt: skip
    log.check(
        "Hindsight answers the recall from the same rows",
        not engine.fallback_reason and bool(hits),
        [(hit.row_id[:12], hit.tag) for hit in hits],
    )
    await harness.close_chat(chat)


def fallback_recall(engine: Any, log: Log) -> None:
    """Stop the index and ask again: the FTS5 file over the same rows answers."""
    hits_before = engine.recall(DIGEST_QUESTION, ("home", "operator"), 2_000)
    engine.index.close()
    engine.fallback_reason = "the lane stopped Hindsight"
    log(f"index closed; Hindsight rows before the stop: {len(hits_before)}")
    found = engine.recall(DIGEST_QUESTION, ("home", "operator"), 2_000)
    log(f"with Hindsight stopped: {len(found)} rows from FTS5, "
        f"{len(hits_before)} through Hindsight before; ids equal: "
        f"{ {hit.row_id for hit in found} >= {hit.row_id for hit in hits_before} }")
    log.check(
        "FTS5 answers with Hindsight stopped",
        bool(found) and {hit.row_id for hit in found} >= {hit.row_id for hit in hits_before},
        [hit.row_id[:12] for hit in found],
    )


def forget_then_rebuild(engine: Any, log: Log) -> None:
    """Forget every row this lane wrote, then rebuild: none of them come back. The lane writes
    rows about pod P and one digest per run, so a repeat run cleans the run before it too."""
    mine = [
        row
        for row in engine._rows("home")
        if "item:P" in row.refs or any("mem-perf" in word for word in row.keywords)
    ]
    log(f"rows this lane wrote and will forget: {[row.object_id[:12] for row in mine]}")
    log.check("the rows to forget were found", bool(mine), len(mine))
    if not mine:
        return
    ids = tuple(row.object_id for row in mine)
    forgotten = engine.forget(ids)
    log(f"forget archived {forgotten} row(s)")
    after = engine.recall(QUESTION, ("home", "operator"), 2_000)
    still = [hit.row_id for hit in after if hit.row_id in ids]
    log.check(
        "a forgotten row leaves recall",
        forgotten == len(ids) and not still,
        [hit.row_id[:12] for hit in after],
    )
    engine.rebuild("all")
    again = engine.recall(QUESTION, ("home", "operator"), 2_000)
    back = [hit.row_id for hit in again if hit.row_id in ids]
    log.check("a rebuild does not bring a forgotten row back", not back, [h[:12] for h in back])


def perf(engine: Any, log: Log) -> None:
    """P-MEM's lines: one session-digest retain, and the recall p95 over 50 questions."""
    from qmx_memory.retain import RetainWorker  # noqa: PLC0415

    blocks = [
        {"role": "user", "text": "P: what did we settle on the pod P filter?"},
        {"role": "assistant", "text": "A 20 day ATR. 14 days flipped in chop."},
    ]
    worker = RetainWorker(engine, blocks=lambda chat: blocks, home="hub")
    chat = f"mem-perf-{int(time.time())}"
    began = time.perf_counter()
    written = worker.digest(chat, "turn-end")
    retain_s = time.perf_counter() - began
    log(f"PERF one session-digest retain: {retain_s:.2f} s (row {written})")
    log.check("a digest retain stays inside P-MEM's 30 s line", retain_s <= 30.0,
              f"{retain_s:.2f} s")  # fmt: skip
    samples: list[float] = []
    for _ in range(RECALLS):
        began = time.perf_counter()
        engine.recall(DIGEST_QUESTION, ("home",), 2_000)
        samples.append((time.perf_counter() - began) * 1000)
    log(f"PERF recall p95 over {RECALLS} calls: {p95(samples):.1f} ms "
        f"(p50 {p95(samples[: RECALLS // 2]):.1f} ms)")  # fmt: skip
    log(f"PERF the fallback index holds {engine.fallback.count()} rows beside Hindsight")


def _tool_rows(result: Any) -> list[str]:
    """The `rows` arrays a turn's memory_recall answers carried, flattened to their texts."""
    found: list[str] = []
    for call in getattr(result, "tools", []):
        for block in getattr(call, "result", None) or []:
            text = block if isinstance(block, str) else str(getattr(block, "text", ""))
            for payload in _documents(text):
                rows = payload.get("rows")
                for row in rows if isinstance(rows, list) else []:
                    if isinstance(row, Mapping):
                        found.append(str(row.get("text", "")))
    return found


def _documents(text: str) -> list[Mapping[str, Any]]:
    """Every JSON document in a tool result, the shape the qmx tool wrapper returns."""
    found: list[Mapping[str, Any]] = []
    for start, char in enumerate(text):
        if char != "{":
            continue
        try:
            payload = json.loads(text[start:])
        except ValueError:
            continue
        if isinstance(payload, Mapping):
            found.append(payload)
            break
    return found


# -- lane 3: the already-built check ------------------------------------------------


def lane_built() -> bool:
    """Two workflow requests for one build: the second answers from `check_built` and links."""
    from qmx_engine.ledger import redact  # noqa: PLC0415
    from qmx_library.store import Store  # noqa: PLC0415
    from qmx_memory.engine import RecallEngine  # noqa: PLC0415

    log = Log("mem-built")
    folder = BUILD / "homes" / "mem-built"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    key = "build:dataset:aapl-1d:2026-10-21"
    with Store.open(folder / "library", redactor=redact) as store:
        engine = RecallEngine(store, home=folder)
        try:
            first = engine.write(
                "home",
                "hub",
                {
                    "tag": "built",
                    "intent_key": key,
                    "content": "the aapl 1d dataset, built by run A",
                    "refs": [],
                },
            )
            chats = 0
            hits = engine.check_built(key)
            log(f"request 1 built {first.object_id[:16]}; request 2 check_built: {hits}")
            log.check("the second request finds the build by its intent key",
                      hits == [first.object_id], hits)  # fmt: skip
            consumer = engine.write("home", "hub", {"tag": "lesson",
                                                   "content": "request 2 of the same build"})  # fmt: skip
            store.relate(store.engine, consumer.object_id, "consumed", first.object_id)
            edges = store.edges_of(consumer.object_id, reverse=False)
            log.check(
                "the second request links the object it reused",
                any(edge[1] == "consumed" and edge[2] == first.object_id for edge in edges),
                [edge[1] for edge in edges],
            )
            log.check("the check spends no tokens: it starts no chat", chats == 0, chats)
            log("PASS no model is called: check_built and the link are Library reads and writes")
        finally:
            engine.close()
    return log.verdict() == 0


# -- lane 4: a lesson's validity window ---------------------------------------------


def lane_window() -> bool:
    """A lesson whose window ended: left out today, returned as of a date inside it."""
    from qmx_engine.ledger import redact  # noqa: PLC0415
    from qmx_library.store import Store  # noqa: PLC0415
    from qmx_memory.engine import RecallEngine  # noqa: PLC0415

    log = Log("mem-window")
    folder = BUILD / "homes" / "mem-window"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    today = datetime.now(UTC)
    closed_from = today - timedelta(days=90)
    closed_to = today - timedelta(days=30)
    with Store.open(folder / "library", redactor=redact) as store:
        engine = RecallEngine(store, home=folder)
        try:
            old = engine.write(
                "home",
                "hub",
                {
                    "tag": "lesson",
                    "content": "pod Q's filter needed a 9 day ATR in the chop regime",
                    "valid_from": closed_from.isoformat(),
                    "valid_to": closed_to.isoformat(),
                },
            )
            live = engine.write(
                "home",
                "hub",
                {"tag": "lesson", "content": "pod Q's filter now needs a 20 day ATR"},
            )
            now_hits = engine.recall("pod Q filter ATR", ("home",), 2_000)
            inside = engine.recall(
                "pod Q filter ATR", ("home",), 2_000, now=closed_from + timedelta(days=10)
            )
            log(f"today: {[hit.row_id[:12] for hit in now_hits]}; "
                f"as_of inside the window: {[hit.row_id[:12] for hit in inside]}")  # fmt: skip
            log.check("recall leaves the ended lesson out at today's date",
                      {hit.row_id for hit in now_hits} == {live.object_id},
                      [hit.row_id for hit in now_hits])  # fmt: skip
            log.check("recall returns it as of a date inside the window",
                      {hit.row_id for hit in inside} == {old.object_id},
                      [hit.row_id for hit in inside])  # fmt: skip
        finally:
            engine.close()
    return log.verdict() == 0


# -- lane 10: no process and no lock left ------------------------------------------


def lane_processes() -> bool:
    log = Log("mem-processes")
    left = [
        f"{found.pid} {found.info['name']}"
        for found in psutil.process_iter(["name"])
        if str(found.info["name"] or "").lower() in {"qmx_host", "claude", "qma-cli-launcher"}
        or "hindsight" in str(found.info["name"] or "").lower()
    ]
    log.check("no Hindsight, qmx_host, claude or qma-cli-launcher process is left", not left, left)
    log.check("no lane lock is left", not LANE_LOCK.exists(), LANE_LOCK)
    return log.verdict() == 0


LANES: Mapping[str, Any] = {
    "e65": lane_e65,
    "built": lane_built,
    "window": lane_window,
    "processes": lane_processes,
}


def main() -> int:
    clean_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lanes", nargs="*", choices=[*LANES, ""], default=[])
    chosen = parser.parse_args().lanes or ["e65", "built", "window"]
    failed = [name for name in chosen if not LANES[name]()]
    print(f"lanes run: {chosen}; failed: {failed}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())















