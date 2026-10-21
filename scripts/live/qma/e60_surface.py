"""SURF lanes (E60, engine AD-62): what each chat is offered, live.

    e60_surface.py fake      the fake model in a throwaway home. An intake chat built the way an
                             engine agent node's is (`Read`, toolsets library, research, data and
                             memory, no skills) is offered exactly those tools; its call to a
                             `workflows` tool is refused; a copilot chat and a Background chat
                             are offered no CLI scheduling tool or skill, and the Background chat
                             no worktree tool.
    e60_surface.py e60       haiku on the ship home's plan (the caller holds the engine lane
                             lock): an intake `agent` node declaring `toolsets: [library,
                             research, data, memory]` runs in a live workflow. PASS when its
                             launch offered only those toolsets, the model names only their
                             tools, and the span carries the digest the chat record holds.
                             Logs the first request's input tokens (perf).
    e60_surface.py baseline  the same node at the parent, which has no node `toolsets` and so
                             loads every tool: run this file with the parent's venv. Logs the
                             first request's input tokens.
    e60_surface.py resume    haiku on the ship home (lane lock held by the caller): a persona slot
                             is changed between two turns of one chat, which relaunches by resume.
                             PASS when the model follows the new persona and a second digest is
                             recorded. The slot file is removed afterwards.
    e60_surface.py child     the fake model: a Lab-shaped chat (home lab, toolsets library,
                             research and delegate) starts a helper. PASS when the helper's
                             surface is within its parent's.
    e60_surface.py spill     the fake model: a 20,000-character methodology spills to the chat's
                             `qmx-slots` skill and the launch passes.

Logs go to `<QMA_EVIDENCE_DIR>/owner-surf-<lane>.log`.
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from common import SHIP_HOME, Log, boot, put_providers, throwaway_home, use_fake_home
from fake_model import FakeModel, Turn, text, tool_use
from money_lane import direct_row, results

LOCK = Path("D:/QMX-worktrees/.engine-lane-lock")
TURN_S = 300.0
SCHEDULING = {"CronCreate", "CronDelete", "CronList", "ScheduleWakeup", "RemoteTrigger", "Workflow"}
WORKTREE = {"EnterWorktree", "ExitWorktree"}
INTAKE = ("library", "research", "data", "memory")
WORKFLOWS_TOOL = "mcp__qmx_workflows__list"
SKILL_LINE = re.compile(r"^- (schedule|loop):", re.MULTILINE)
BRIEF = (
    "You are the intake reader. Before anything else, look at the tools you were given. Reply "
    "with one JSON document whose `tools` lists the exact name of every tool you have whose name "
    "starts with mcp__, and whose `read` is the word of the input item."
)
SCHEMA = {
    "type": "object",
    "required": ["tools", "read"],
    "properties": {"tools": {"type": "array", "items": {"type": "string"}}, "read": {}},
}


def folder(root: Path, name: str) -> Path:
    found = root / "workspaces" / name
    found.mkdir(parents=True, exist_ok=True)
    return found


def offered(fake: FakeModel) -> list[set[str]]:
    return [
        {str(tool.get("name")) for tool in seen.json.get("tools", [])}
        for seen in fake.requests
        if seen.scripted
    ]


def strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for item in value.values() for s in strings(item)]
    if isinstance(value, list):
        return [s for item in value for s in strings(item)]
    return []


def bodies(fake: FakeModel) -> list[str]:
    """Every text a scripted request carried (system, messages and tool descriptions), decoded."""
    return ["\n".join(strings(seen.json)) for seen in fake.requests if seen.scripted]


def manifest(home: Any, chat: str) -> dict[str, Any]:
    return json.loads((home.launch_dir(chat) / "surface.json").read_text(encoding="utf-8"))


async def fake_harness(slug: str, script: list[Turn]) -> tuple[Any, Any, FakeModel]:
    from qma.harness import Harness, QmxHome, TestMode  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    root = throwaway_home(slug)
    fake = FakeModel(script).start()
    put_providers(root, {"fake": direct_row(fake.url), "delegate_targets": ["fake"]})
    home = QmxHome(root)
    harness = await Harness.open(
        home, control=control_service(home), test=TestMode(loopback_http_provider=True)
    )
    return harness, home, fake


async def fake_lane(log: Log) -> None:
    from qma.harness import (  # noqa: PLC0415
        Background,
        InjectedText,
        Interactive,
        NewChat,
        OperatorText,
    )
    from qmx_engine.ports.harness_adapter import HarnessAdapter  # noqa: PLC0415

    script = [
        Turn([tool_use(WORKFLOWS_TOOL, {})]),
        Turn([text('{"tools": [], "read": "otter"}')]),
        Turn([text("copilot done")]),
        Turn([text("background done")]),
    ]
    harness, home, fake = await fake_harness("surf-fake", script)
    try:
        adapter = HarnessAdapter(harness)
        intake = await adapter.start_chat(
            title="surf intake",
            profile="fake",
            model="opus",
            effort=None,
            workspace=folder(home.root, "intake"),
            tools=("Read",),
            toolsets=INTAKE,
            skills=(),
            system=BRIEF,
        )
        await adapter.send(intake, 'Input:\n{"word": "otter"}')
        turn = await asyncio.wait_for(adapter.wait_turn(intake), TURN_S)
        log(f"intake turn: text={turn.text!r} tools={[c.name for c in turn.tools]}")
        found = manifest(home, intake)
        log(f"intake surface.json: toolsets={found['toolsets']} builtins={found['builtins']}")
        for kind, title in ((Interactive(), "surf copilot"), (Background(), "surf background")):
            chat = await harness.start_chat(
                NewChat(
                    title=title,
                    model="opus",
                    profile="fake",
                    mode="bypassPermissions",
                    workspace=folder(home.root, title.replace(" ", "-")),
                    kind=kind,
                )
            )
            words = f"{title}: reply done"
            prompt = OperatorText(words) if isinstance(kind, Interactive) else InjectedText(words)
            handle = await harness.run_turn(chat, prompt)
            done = await asyncio.wait_for(handle.result(), TURN_S)
            log(f"{title}: status={done.status} text={(done.text or '')[:60]!r}")
    finally:
        await harness.close()
        fake.stop()
    lists = offered(fake)
    texts = bodies(fake)
    first = lists[0] if lists else set()
    wanted = {"Read", *(name for name in first if name.startswith("mcp__qmx_"))}
    served = {
        name.split("__")[1].removeprefix("qmx_") for name in first if name.startswith("mcp__")
    }
    log(f"intake request 1 offered {len(first)} tools: {sorted(first)}")
    log.check(
        "the intake chat is offered only Read and tools of its declared toolsets",
        bool(first) and first == wanted and served <= set(INTAKE) and "Read" in first,
        {"toolsets": sorted(served), "builtins": sorted(n for n in first if "__" not in n)},
    )
    log.check(
        "its launch records the toolsets the host serves (memory has no rows yet)",
        found["toolsets"] == ["library", "research", "data"] and found["builtins"] == ["Read"],
        found["toolsets"],
    )
    calls = list(results(fake).values())
    for tool, _, is_error, said in calls:
        log(f"  call {tool}: error={is_error} {said[:200]!r}")
    log.check(
        "the workflows call is refused and does not run",
        len(calls) >= 1 and calls[0][0] == WORKFLOWS_TOOL and calls[0][2],
        calls[0][3][:160] if calls else None,
    )
    copilot, background = (lists[2], lists[3]) if len(lists) >= 4 else (set(), set())
    log(f"copilot offered {len(copilot)} tools; background {len(background)}")
    log.check(
        "no chat is offered a CLI scheduling tool",
        bool(copilot and background) and not (SCHEDULING & (first | copilot | background)),
        sorted(SCHEDULING & (first | copilot | background)),
    )
    log.check(
        "the Background chat has no worktree tool and the copilot keeps them",
        not (WORKTREE & background) and copilot >= WORKTREE,
        {"background": sorted(WORKTREE & background), "copilot": sorted(WORKTREE & copilot)},
    )
    listing = texts[2] if len(texts) > 2 else ""
    at = listing.find("dataviz")
    log(f"copilot skill listing sample: {listing[max(0, at - 60) : at + 80]!r}")
    log.check(
        "the copilot's skill listing names CLI skills but not schedule or loop",
        "dataviz" in listing and not SKILL_LINE.search(listing) and '"schedule"' not in listing,
        SKILL_LINE.findall(listing),
    )
    log.check(
        "the intake chat is offered no Skill tool and no skill listing",
        "Skill" not in first and "dataviz" not in (texts[0] if texts else ""),
        "Skill" in first,
    )


def intake_workflow(root: Path, *, declared: bool) -> Path:
    node: dict[str, Any] = {
        "id": "intake",
        "name": "intake",
        "type": "agent",
        "typeVersion": 1,
        "role": "reader",
        "parameters": {
            "brief_ref": "prompts/brief.md",
            "output_schema_ref": "schemas/out.json",
            "tools": ["Read"],
        },
    }
    if declared:
        node["toolsets"] = list(INTAKE)
    document = {
        "schema": "qmx.workflow/1",
        "id": "surf-intake",
        "name": "surf-intake",
        "nodes": [
            {"id": "start", "name": "start", "type": "trigger", "typeVersion": 1},
            node,
        ],
        "connections": {"start": {"main": [[{"node": "intake", "port": "in", "map": "one"}]]}},
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "definition.json").write_text(json.dumps(document, indent=2), encoding="utf-8")
    (root / "prompts").mkdir(exist_ok=True)
    (root / "prompts" / "brief.md").write_text(BRIEF, encoding="utf-8")
    (root / "schemas").mkdir(exist_ok=True)
    (root / "schemas" / "out.json").write_text(json.dumps(SCHEMA), encoding="utf-8")
    return root


def first_request_tokens(home_root: Path, chat: str) -> int | None:
    path = home_root / "runs" / chat / "journal.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("event") == "model_call":
            payload = row.get("payload", {})
            names = ("input_tokens", "cache_read_tokens", "cache_write_tokens")
            return sum(int(payload.get(name) or 0) for name in names)
    return None


async def engine_lane(log: Log, *, declared: bool) -> None:
    import hashlib  # noqa: PLC0415

    from qma.harness import Harness, QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415
    from qmx_engine.definition.validate import checked  # noqa: PLC0415
    from qmx_engine.ledger.store import Ledger, Reader  # noqa: PLC0415
    from qmx_engine.ports.harness_adapter import HarnessAdapter  # noqa: PLC0415
    from qmx_engine.runner import Engine  # noqa: PLC0415
    from qmx_engine.settings import DEFAULTS  # noqa: PLC0415

    if not LOCK.is_dir():
        raise SystemExit(f"plan lanes run only while holding {LOCK}")
    settings_file = SHIP_HOME / "settings.toml"
    before = hashlib.sha256(settings_file.read_bytes()).hexdigest()
    slug = "e60" if declared else "baseline"
    scratch = throwaway_home(f"surf-{slug}-{int(time.time())}")
    root = intake_workflow(scratch / "wf", declared=declared)
    engine_home = scratch / "engine"
    engine_home.mkdir()
    found = checked(root)
    if isinstance(found, list):
        raise SystemExit(f"BLOCKED: the workflow does not validate: {found}")
    home = QmxHome(SHIP_HOME)
    harness = await Harness.open(home, control=control_service(home))
    try:
        port = HarnessAdapter(harness)
        with Ledger.open(engine_home) as ledger:
            engine = Engine(
                engine_home,
                ledger,
                settings={**DEFAULTS, "roles.reader": ("claude/haiku",)},
                harness=port,
            )
            outcome = await engine.start(
                root, found[1], mode="live", inputs={"word": "otter"}, run_id=f"surf-{slug}"
            )
        with Reader.open(engine_home) as reader:
            events, spans = reader.events(outcome.run_id), reader.spans(outcome.run_id)
        recorded = None
        chats = [e.data["session_id"] for e in events if "session_id" in e.data]
        chat = chats[0] if chats else None
        if declared and chat is not None:
            recorded = harness.surface_digest(chat)
    finally:
        await harness.close()
    after = hashlib.sha256(settings_file.read_bytes()).hexdigest()
    log(f"run {outcome.run_id}: {outcome.status} {outcome.reason or ''}; chat {chat}")
    answer: Any = next(
        (
            e.data["outputs"]["main"]
            for e in events
            if e.kind == "node_finished" and e.data.get("node_id") == "intake"
        ),
        {},
    )
    named = sorted(answer.get("tools", [])) if isinstance(answer, dict) else []
    log(f"the model names {len(named)} mcp tools: {named}")
    node_spans = [s for s in spans if s.kind == "node" and s.node_id == "intake"]
    tokens = first_request_tokens(SHIP_HOME, chat) if chat else None
    log(f"PERF first request input tokens (input + cache read + cache write): {tokens}")
    log.check("the ship home's settings.toml is unchanged", after == before, after)
    log.check(
        "the intake node passed on claude/haiku",
        outcome.status == "passed"
        and [(s.profile, s.model, s.status) for s in node_spans] == [("claude", "haiku", "ok")],
        [(s.profile, s.model, s.status) for s in node_spans],
    )
    if not declared:
        log(f"baseline: the parent offered the node {len(named)} mcp tools")
        return
    surface = manifest(home, chat) if chat else {}
    toolsets = {name.split("__")[1].removeprefix("qmx_") for name in named}
    log(f"surface.json toolsets={surface.get('toolsets')} builtins={surface.get('builtins')}")
    log.check(
        "the launch offered only the declared toolsets the host serves",
        surface.get("toolsets") == ["library", "research", "data"]
        and surface.get("builtins") == ["Read"],
        surface.get("toolsets"),
    )
    log.check(
        "the model sees only tools of its declared toolsets",
        bool(named) and toolsets <= set(INTAKE),
        sorted(toolsets),
    )
    digest = node_spans[0].surface_digest if node_spans else None
    log.check(
        "the span carries the surface digest the chat record holds",
        digest is not None and digest == recorded and digest == surface.get("digest"),
        {"span": digest, "record": recorded},
    )


async def resume_lane(log: Log) -> None:
    from qma.harness import Harness, Interactive, NewChat, OperatorText, QmxHome  # noqa: PLC0415
    from qma.harness.home import read_record  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    if not LOCK.is_dir():
        raise SystemExit(f"plan lanes run only while holding {LOCK}")
    slots = SHIP_HOME / "slots"
    persona = slots / "persona.md"
    if slots.exists():
        raise SystemExit(f"BLOCKED: {slots} already exists; this lane only adds and removes it")
    ask = "What is the persona word? Reply with that word only."
    home = QmxHome(SHIP_HOME)
    harness = await Harness.open(home, control=control_service(home))
    try:
        slots.mkdir()
        persona.write_text("When asked for the persona word, it is HERON-ALPHA.", "utf-8")
        chat = await harness.start_chat(
            NewChat(
                title="surf resume",
                model="haiku",
                workspace=folder(throwaway_home("surf-resume"), "resume"),
                kind=Interactive(),
            )
        )

        async def turn(label: str) -> str:
            handle = await harness.run_turn(chat, OperatorText(ask))
            done = await asyncio.wait_for(handle.result(), TURN_S)
            log(f"{label}: status={done.status} text={(done.text or '')[:120]!r}")
            return done.text or ""

        first = await turn("persona A")
        await harness.close_chat(chat)
        persona.write_text("When asked for the persona word, it is LYNX-BETA.", "utf-8")
        second = await turn("persona B after a relaunch by resume")
        record = read_record(home, chat)
        digests = list(record.digests) if record else []
        log(f"digests recorded: {digests}")
        transcripts = list((home.plan_dir / "projects").glob(f"*/{chat}.jsonl"))
    finally:
        await harness.close()
        shutil.rmtree(slots, ignore_errors=True)
    log.check("the first turn follows persona A", "HERON-ALPHA" in first, first[:80])
    log.check("after the resume the model quotes the new persona", "LYNX-BETA" in second, second)
    log.check("one session, resumed", len(transcripts) == 1, [p.name for p in transcripts])
    log.check(
        "a new digest is recorded for the relaunch",
        len(digests) == 2 and digests[0] != digests[1],
        len(digests),
    )
    log.check("the slot folder is removed from the ship home", not slots.exists(), slots)


async def child_lane(log: Log) -> None:
    from qma.harness import Background, Home, InjectedText, NewChat  # noqa: PLC0415
    from qma.harness.home import list_records  # noqa: PLC0415

    delegate = "mcp__qmx_delegate__run"
    script = [
        Turn([tool_use(delegate, {"profile": "fake", "prompt": "Name your tools, then stop."})]),
        Turn([text("helper done")]),
        Turn([text("parent done")]),
    ]
    harness, home, fake = await fake_harness("surf-child", script)
    try:
        parent = await harness.start_chat(
            NewChat(
                title="surf lab parent",
                model="opus",
                profile="fake",
                mode="bypassPermissions",
                workspace=folder(home.root, "lab"),
                kind=Background(),
                home=Home("lab", "pod-7"),
                toolsets=("library", "research", "delegate"),
            )
        )
        handle = await harness.run_turn(parent, InjectedText("start a helper"))
        done = await asyncio.wait_for(handle.result(), TURN_S)
        log(f"parent: status={done.status} text={(done.text or '')[:80]!r}")
        children = [r for r in list_records(home) if r.session_id != parent]
    finally:
        await harness.close()
        fake.stop()
    calls = list(results(fake).values())
    for tool, _, is_error, said in calls:
        log(f"  call {tool}: error={is_error} {said[:160]!r}")
    log.check(
        "the helper ran and answered",
        any(t == delegate and not e for t, _, e, _ in calls),
        [c[:1] for c in calls],
    )
    if not children:
        log.check("a helper chat exists", False, None)
        return
    up, down = manifest(home, parent), manifest(home, children[0].session_id)
    for name, found in (("parent", up), ("helper", down)):
        sizes = f"builtins={len(found['builtins'])} skills={len(found['skills'])}"
        log(f"{name}: toolsets={found['toolsets']} {sizes}")
    log(f"helper home: {children[0].config.home}")
    within = (
        set(down["toolsets"]) <= set(up["toolsets"])
        and set(down["tools"]) <= set(up["tools"])
        and set(down["builtins"]) <= set(up["builtins"])
        and set(down["skills"]) <= set(up["skills"])
    )
    log.check("the helper's surface is within its parent's", within, down["toolsets"])
    log.check(
        "the helper has no delegate and no Agent tool",
        "delegate" not in down["toolsets"] and "Task" not in down["builtins"],
        down["toolsets"],
    )
    helper_request = offered(fake)[1] if len(offered(fake)) > 1 else set()
    log.check(
        "the helper's request offers only tools within the parent's",
        bool(helper_request) and helper_request <= set(up["tools"]) | set(up["builtins"]),
        sorted(helper_request - set(up["tools"]) - set(up["builtins"])),
    )


async def spill_lane(log: Log) -> None:
    from qma.harness import Background, InjectedText, NewChat  # noqa: PLC0415

    script = [Turn([text("spill done")])]
    harness, home, fake = await fake_harness("surf-spill", script)
    methodology = home.root / "slots" / "methodology" / "general.md"
    methodology.parent.mkdir(parents=True)
    methodology.write_text("Check the data before the model. " * 610, encoding="utf-8")
    try:
        chat = await harness.start_chat(
            NewChat(
                title="surf spill",
                model="opus",
                profile="fake",
                mode="bypassPermissions",
                workspace=folder(home.root, "spill"),
                kind=Background(),
            )
        )
        handle = await harness.run_turn(chat, InjectedText("go"))
        done = await asyncio.wait_for(handle.result(), TURN_S)
        log(f"turn: status={done.status} text={(done.text or '')[:60]!r}")
        found = manifest(home, chat)
        skill = home.launch_dir(chat) / "qmx-slots" / "skills" / "methodology" / "SKILL.md"
    finally:
        await harness.close()
        fake.stop()
    size = len(methodology.read_text(encoding="utf-8"))
    body = bodies(fake)[0] if bodies(fake) else ""
    log(f"methodology {size} characters; slot {found['slots']['methodology']}")
    log.check("the launch passed and the turn ended ok", done.status == "ok", done.status)
    log.check(
        "the slot spilled and the system text keeps a pointer to the skill",
        found["slots"]["methodology"]["spilled"] and "qmx-slots:methodology" in body,
        found["slots"]["methodology"],
    )
    log.check(
        "the full text is the skill, which the chat's skills filter lists",
        skill.is_file()
        and skill.read_text(encoding="utf-8").count("Check the data") == 610
        and "qmx-slots:methodology" in found["skills"],
        skill,
    )


def main() -> int:
    lane = sys.argv[1] if len(sys.argv) > 1 else ""
    lanes = ("fake", "e60", "baseline", "resume", "child", "spill")
    if lane not in lanes:
        raise SystemExit(f"usage: e60_surface.py {{{','.join(lanes)}}}")
    log = Log(f"owner-surf-{lane}")
    boot()
    use_fake_home()
    if lane in ("fake", "child", "spill"):
        from common import use_fake_key  # noqa: PLC0415

        use_fake_key()
    runs = {
        "fake": fake_lane,
        "resume": resume_lane,
        "child": child_lane,
        "spill": spill_lane,
    }
    if lane in ("e60", "baseline"):
        asyncio.run(engine_lane(log, declared=lane == "e60"))
    else:
        asyncio.run(runs[lane](log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
