"""CAT lanes: the operation catalog, each toolset's server and a scope change, live.

    cat_lanes.py relist    haiku on the ship home's plan (needs the engine lane lock held by the
                           caller): a Background chat with only the library toolset is asked to
                           call `mcp__qmx_ops__capacity`; the ops toolset is added, the same
                           question asked, then removed and asked again, and added once more.
                           PASS when the tool is missing, then answers, then is gone, with the
                           same CLI process throughout. Records each scope change in ms (perf).
    cat_lanes.py outside   the fake model in a throwaway home: the chat calls
                           `mcp__qmx_ops__capacity` while ops is off; then, with ops listed by
                           the CLI but the guard's surface left stale without it, calls it again;
                           then with the surface restored. PASS when the stale call is the
                           guard's refusal and the restored call answers.
    cat_lanes.py rest <out.json>
                           calls every REST route of the parent's OPERATIONS table on a fresh
                           home and writes each status and JSON shape; run it at the parent and
                           at the head, then `compare`.
    cat_lanes.py compare <parent.json> <head.json>
    cat_lanes.py cursor    600 Library items through the `library_search` tool: a page and a
                           cursor.
    cat_lanes.py grep      every `mcp__qmx...` name in the tree is a catalog row's full name.
    cat_lanes.py count     the tools a hub chat loads, per toolset.

Logs go to `<QMA_EVIDENCE_DIR>/owner-cat-<lane>.log`.
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from common import SCRATCH, SHIP_HOME, Log, boot, put_providers, throwaway_home, use_fake_home
from fake_model import FakeModel, Turn, text, tool_use
from money_lane import HOOK_MARK, direct_row, results

LOCK = Path("D:/QMX-worktrees/.engine-lane-lock")
MODEL = "haiku"
TURN_S = 300.0
CAPACITY = "mcp__qmx_ops__capacity"
ASK = (
    f"If you have a tool named {CAPACITY}, call it exactly once and reply CAP-OK followed by the "
    "capacity number it returns. If you have no tool with that exact name, do not call any tool "
    "and reply exactly NO-TOOL."
)
REPO = Path(__file__).resolve().parents[3]


def folder(name: str) -> Path:
    found = SCRATCH / f"cat-{name}"
    found.mkdir(parents=True, exist_ok=True)
    return found


def cli_pid(home: Any, chat: str) -> int | None:
    from qma.launcher import pid_path, read_pid_record  # noqa: PLC0415

    record = read_pid_record(pid_path(home.procs_dir, chat))
    return None if record is None else record.cli_pid


async def relist(log: Log) -> None:
    from qma.harness import Background, Harness, InjectedText, NewChat, QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    if not LOCK.is_dir():
        raise SystemExit(f"plan lanes run only while holding {LOCK}")
    home = QmxHome(SHIP_HOME)
    harness = await Harness.open(home, control=control_service(home))
    timings: list[float] = []
    try:
        chat = await harness.start_chat(
            NewChat(
                title="cat relist",
                model=MODEL,
                workspace=folder("relist"),
                kind=Background(),
                toolsets=("library",),
            )
        )

        async def ask(label: str) -> tuple[str, list[str]]:
            handle = await harness.run_turn(chat, InjectedText(ASK))
            done = await asyncio.wait_for(handle.result(), TURN_S)
            called = [call.name for call in done.tools]
            log(f"{label}: status={done.status} tools={called} text={(done.text or '')[:160]!r}")
            return done.text or "", called

        async def scope(toolsets: tuple[str, ...]) -> None:
            started = time.perf_counter()
            await harness.set_toolsets(chat, toolsets)
            timings.append((time.perf_counter() - started) * 1000)
            log(f"scope -> {toolsets} in {timings[-1]:.1f} ms")

        before, called = await ask("library only")
        log.check("ops is not offered before the change", CAPACITY not in called, called)
        log.check("the model says it has no such tool", "NO-TOOL" in before, before[:80])
        pid = cli_pid(home, chat)
        client = id(harness._chat(chat)._live.client)
        await scope(("library", "ops"))
        after, called = await ask("library and ops")
        log.check("the added tool answers on the next request", CAPACITY in called, called)
        log.check("the model read its answer", "CAP-OK" in after, after[:80])
        await scope(("library",))
        removed, called = await ask("ops removed")
        log.check("the removed tool is gone", CAPACITY not in called, called)
        await scope(("library", "ops"))
        same = cli_pid(home, chat) == pid and id(harness._chat(chat)._live.client) == client
        log.check("the CLI was not relaunched", same, f"pid {pid} -> {cli_pid(home, chat)}")
        log(f"PERF scope change ms: {', '.join(f'{t:.1f}' for t in timings)}")
        del removed
    finally:
        await harness.close()


async def outside(log: Log) -> None:
    from qma.harness import (  # noqa: PLC0415
        Background,
        Harness,
        InjectedText,
        NewChat,
        QmxHome,
        TestMode,
    )
    from qma.harness.routes import control_service  # noqa: PLC0415

    root = throwaway_home("cat-outside")
    script = [
        Turn([tool_use(CAPACITY, {})]),
        Turn([text("first done")]),
        Turn([tool_use(CAPACITY, {})]),
        Turn([text("stale done")]),
        Turn([tool_use(CAPACITY, {})]),
        Turn([text("restored done")]),
    ]
    fake = FakeModel(script).start()
    put_providers(root, {"fake": direct_row(fake.url)})
    home = QmxHome(root)
    harness = await Harness.open(
        home, control=control_service(home), test=TestMode(loopback_http_provider=True)
    )
    try:
        chat = await harness.start_chat(
            NewChat(
                title="cat outside",
                model="opus",
                profile="fake",
                mode="bypassPermissions",
                workspace=folder("outside"),
                kind=Background(),
                toolsets=("library",),
            )
        )

        async def turn(label: str) -> None:
            handle = await harness.run_turn(chat, InjectedText(label))
            done = await asyncio.wait_for(handle.result(), TURN_S)
            log(f"{label}: status={done.status} text={(done.text or '')[:120]!r}")

        await turn("ops off")
        await harness.set_toolsets(chat, ("library", "ops"))
        gate = harness._chat(chat)._gate
        gate.surface.discard("qmx_ops")
        log(f"the CLI lists ops; the guard's surface is left stale: {sorted(gate.surface)}")
        await turn("stale list")
        await harness.set_toolsets(chat, ("library", "ops"))
        await turn("restored")
    finally:
        await harness.close()
        fake.stop()
    calls = list(results(fake).values())
    for tool, _, is_error, said in calls:
        log(f"  call {tool}: error={is_error} {said[:200]!r}")
    offered = [
        CAPACITY in {tool.get("name") for tool in seen.json.get("tools", [])}
        for seen in fake.requests
        if seen.scripted
    ]
    log(f"ops offered per scripted request: {offered}")
    log.check(
        "with ops off the call does not run",
        len(calls) >= 1 and calls[0][2],
        calls[0][3][:120] if calls else None,
    )
    log.check(
        "the stale call is the guard's refusal",
        len(calls) >= 2
        and calls[1][2]
        and HOOK_MARK in calls[1][3]
        and "outside this chat's tools" in calls[1][3],
        calls[1][3][:160] if len(calls) > 1 else None,
    )
    log.check(
        "the restored call answers",
        len(calls) >= 3 and not calls[2][2] and '"capacity"' in calls[2][3],
        calls[2][3][:160] if len(calls) > 2 else None,
    )


ROUTE = re.compile(r'\("(\w+)", "(GET|POST|PUT)", "([^"]+)", (?:True|False)\)')
SAMPLES: dict[str, object] = {
    "app_id": "missing-app",
    "workflow_id": "missing-workflow",
    "run_id": "missing-run",
    "job_id": "missing-job",
    "trigger_id": "missing-trigger",
    "artifact_id": "missing-artifact",
    "section": "budgets",
    "session_id": "missing-session",
    "tool": "missing-tool",
}


def shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: shape(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [shape(value[0])] if value else []
    return type(value).__name__


def rest(log: Log, out: Path) -> None:
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from qmx_control.server import create_app  # noqa: PLC0415
    from qmx_control.service import ControlService  # noqa: PLC0415

    parent = subprocess.run(
        ["git", "-C", str(REPO), "show", "319baa47:qmx-agents/packages/qmx-control/src/qmx_control/server.py"],
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    table = ROUTE.findall(parent)
    root = throwaway_home(f"cat-rest-{out.stem}")
    service = ControlService(root)
    found: dict[str, Any] = {}
    with TestClient(create_app(service, "cat-rest-bearer")) as client:
        for name, verb, path in table:
            if name in ("sessions_stream", "backup_weekly"):
                continue
            url = re.sub(r"\{(\w+)\}", lambda m: str(SAMPLES[m.group(1)]), path)
            response = client.request(
                verb, url, headers={"Authorization": "Bearer cat-rest-bearer"}, json={}
            )
            body: Any
            try:
                body = response.json()
            except ValueError:
                body = response.text[:80]
            found[f"{name} {verb} {path}"] = {"status": response.status_code, "shape": shape(body)}
    out.write_text(json.dumps(found, indent=1, sort_keys=True), encoding="utf-8")
    log(f"{len(found)} routes of the parent's table answered; written to {out}")
    log.check("every route was called", len(found) == len(table) - 2, len(found))


def compare(log: Log, parent: Path, head: Path) -> None:
    before = json.loads(parent.read_text(encoding="utf-8"))
    after = json.loads(head.read_text(encoding="utf-8"))
    differ = sorted(key for key in before if before[key] != after.get(key))
    for key in sorted(before):
        log(f"  {key}: parent {before[key]['status']} head {after.get(key, {}).get('status')}")
    log.check("the same routes answered", sorted(before) == sorted(after), len(after))
    log.check("each route answers as at the parent (status and JSON shape)", differ == [], differ)


def domain_for(root: Path) -> tuple[Any, Any]:
    from qmx_control.service import ControlService  # noqa: PLC0415
    from qmx_tools.service import DomainContext  # noqa: PLC0415

    control = ControlService(root)
    domain = DomainContext(root=root)
    domain.control, domain.library = control, control.library
    return control, domain


def cursor(log: Log) -> None:
    from qmx_broker.service import BrokerService  # noqa: PLC0415
    from qmx_control.models import LibraryInput  # noqa: PLC0415

    from qma.harness.tools import tool_defs  # noqa: PLC0415

    root = throwaway_home("cat-cursor")
    control, domain = domain_for(root)
    for n in range(600):
        control.library_save(LibraryInput(title=f"item {n}", kind="note", content={"n": n}))
    defs = asyncio.run(
        tool_defs(control=control, broker=BrokerService(root), domain=domain, delegate=None)
    )
    search = next(tool for tool in defs if tool.name == "library_search")

    def page(arguments: dict[str, Any]) -> dict[str, Any]:
        return json.loads(asyncio.run(search.call(arguments))["content"][0]["text"])

    small = page({"limit": 20})
    last = page({"offset": 590, "limit": 20})
    first = page({})
    log(f"default page: spilled={first.get('spilled', False)} keys={sorted(first)}")
    log(f"  next_offset {first['next_offset']}, chars {first.get('chars')}")
    log(f"limit 20: {len(small['items'])} items, next_offset {small['next_offset']}")
    log(f"offset 590: {len(last['items'])} items, next_offset {last['next_offset']}")
    log.check(
        "the default page spills to the Library and keeps its cursor",
        first.get("spilled") is True and first["next_offset"] == 100,
        first["next_offset"],
    )
    log.check(
        "a page and a cursor",
        (len(small["items"]), small["next_offset"]) == (20, 20),
        small["next_offset"],
    )
    log.check(
        "the last page ends the cursor",
        (len(last["items"]), last["next_offset"]) == (10, None),
        last["next_offset"],
    )


def grep(log: Log) -> None:
    from qmx_control.catalog import rows  # noqa: PLC0415

    names = {f"mcp__qmx_{row.toolset}__{row.op}" for row in rows()}
    listed = subprocess.run(
        ["git", "-C", str(REPO), "grep", "-n", "-o", "-E", r"mcp__qmx_?[A-Za-z0-9_]*",
         "--", ".", ":!scripts/probes", ":!qmx-agents/packages/qma-daemon",
         ":!qmx-agents/packages/qma-harness/tests/test_translate.py"],
        capture_output=True, text=True, check=False,
    ).stdout.splitlines()  # fmt: skip
    bad: list[str] = []
    for line in listed:
        where, _, name = line.rpartition(":")
        generic = name in ("mcp__qmx", "mcp__qmx_", "mcp__qmx__") or name.endswith("__")
        fixture = "/tests/" in where
        if not generic and not fixture and name not in names:
            bad.append(f"{where} {name}")
    old = [
        line
        for line in listed
        if line.rpartition(":")[2].startswith("mcp__qmx__") and not line.endswith("mcp__qmx__")
    ]
    log(f"{len(listed)} mentions scanned; outside the catalog: {bad}")
    log.check("no mcp__qmx__ name is left", old == [], old)
    log.check("every mcp__qmx_<toolset>__<op> name is a catalog row", bad == [], bad)


def count(log: Log) -> None:
    from collections import Counter  # noqa: PLC0415

    from qmx_broker.service import BrokerService  # noqa: PLC0415

    from qma.harness.tools import surface, tool_defs  # noqa: PLC0415

    root = throwaway_home("cat-count")
    control, domain = domain_for(root)

    async def delegate(profile: str, prompt: str) -> str:
        return ""

    host = {"slot_table": None, "journal": None}
    defs = asyncio.run(
        tool_defs(
            control=control, broker=BrokerService(root), domain=domain, delegate=delegate, host=host
        )  # type: ignore[arg-type]
    )
    per = Counter(tool.toolset for tool in defs)
    servers = surface(None, defs)
    log(f"hub chat: {len(defs)} QMX tools on {len(servers)} servers")
    for toolset, n in sorted(per.items()):
        log(f"  {toolset}: {n}")
    log.check("the count is recorded for SURF", len(defs) > 0, len(defs))


def main() -> int:
    lane = sys.argv[1] if len(sys.argv) > 1 else ""
    lanes = ("relist", "outside", "rest", "compare", "cursor", "grep", "count")
    if lane not in lanes:
        raise SystemExit(f"usage: cat_lanes.py {{{','.join(lanes)}}}")
    suffix = f"-{Path(sys.argv[2]).stem}" if lane == "rest" else ""
    log = Log(f"owner-cat-{lane}{suffix}")
    if lane == "rest":
        rest(log, Path(sys.argv[2]))
    elif lane == "compare":
        compare(log, Path(sys.argv[2]), Path(sys.argv[3]))
    elif lane in ("cursor", "grep", "count"):
        {"cursor": cursor, "grep": grep, "count": count}[lane](log)
    else:
        boot()
        use_fake_home()
        if lane == "outside":
            from common import use_fake_key  # noqa: PLC0415

            use_fake_key()
        asyncio.run({"relist": relist, "outside": outside}[lane](log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
