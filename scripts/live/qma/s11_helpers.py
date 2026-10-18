"""HP13 lanes 2 to 10 and the perf probe: native helpers (S11), `mcp__qmx__delegate` and its
refusals. Every part runs in a throwaway home on the fake model except `kimi`, whose helper
chat makes one short real OpenRouter turn under the spend guard. No part uses the plan.

    s11_helpers.py nested      lane 2. A helper asks for its own helper. PASS when the nested
                               Agent call gets an error result and no third conversation starts.
    s11_helpers.py background  lane 3. A helper started with run_in_background. PASS when a
                               completed task notification arrives and the chat ends idle.
    s11_helpers.py model       lane 4. A plugin helper whose definition says `model: haiku`, on a
                               row whose haiku tier is `fake-haiku`. PASS when the turn's
                               `model_usage` names fake-haiku and the helper's requests ran on it.
    s11_helpers.py kimi        lane 5. A fake parent delegates to the OpenRouter Kimi row. PASS
                               when the final text comes back, the child session's `parent_id` is
                               the parent, the child had its own grant in the relayed home, and
                               that grant gets 401 once the child ended.
    s11_helpers.py tools       lane 6. PASS when the child's server info, its `init` tool list
                               and the tools its requests offer hold no Task, Agent or
                               mcp__qmx__delegate.
    s11_helpers.py subagent    lane 7. A native helper calls mcp__qmx__delegate. PASS when the
                               gate denies it and no child session exists.
    s11_helpers.py full        lane 8. `max_live_chats` = 1. PASS when delegate returns a tool
                               error naming the busy chat in under 2 s and no child launched.
    s11_helpers.py allowlist   lane 9. PASS when delegate to a row outside `delegate_targets` is
                               refused with the allow-list named.
    s11_helpers.py unattended  lane 10. A Background parent in default mode delegates; the
                               child's Bash ask goes unanswered. PASS when the child launched
                               verbatim as Child(unattended=True), its ask expired after
                               `unattended_ask_seconds`, Bash never ran, and its final text came
                               back.
    s11_helpers.py perf        five delegations, fake parent and fake child (the same delegate
                               path a Kimi child takes, minus the provider). PASS when the median
                               time from the delegate call to the child's first upstream request
                               is under 5 s.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from common import (
    SCRATCH,
    Log,
    Session,
    boot,
    capture_grants,
    capture_launches,
    only_tools,
    put_claude,
    put_providers,
    session_blocks,
    show,
    throwaway_home,
    use_fake_home,
    use_fake_key,
    wait_turn,
)
from fake_model import FakeModel, Turn, text, tool_use
from hp12_lanes import relay_status
from money_lane import direct_row, results
from s31_chat_cap import put_budgets
from switch_lane import OPENROUTER_ROW, spend_ledger

DELEGATE: Final = "mcp__qmx__delegate"
WORKSPACE: Final = SCRATCH / "hp13-ws"
PERF_RUNS: Final = 5
PERF_LIMIT_S: Final = 5.0
ASK_S: Final = 5
KIMI_WORD: Final = "PINEAPPLE"
KIMI_USD: Final = 0.02
"""Above one short Kimi K2.5 turn with no built-in tools (HP12's check 8 paid $0.0091 for two
turns with Bash); the worst case, 2 calls at 40k input tokens, is $0.043."""


@dataclass(frozen=True)
class Delegated:
    prompt: str
    began: float
    took: float
    outcome: str


DELEGATED: list[Delegated] = []


def time_delegates() -> None:
    """Record every `Harness._delegate` call from now on: its prompt, start, length and result.
    Patched on the class, before any harness binds it."""
    from qma.harness.harness import Harness  # noqa: PLC0415

    real = Harness._delegate  # pyright: ignore[reportPrivateUsage]

    async def timed(self: Harness, parent: Any, profile: str, prompt: str) -> str:
        began = time.perf_counter()
        try:
            found = await real(self, parent, profile, prompt)
        except Exception as error:
            DELEGATED.append(Delegated(prompt, began, time.perf_counter() - began, repr(error)))
            raise
        DELEGATED.append(Delegated(prompt, began, time.perf_counter() - began, found))
        return found

    Harness._delegate = timed  # pyright: ignore[reportPrivateUsage]


def delegate(profile: str, prompt: str) -> dict[str, Any]:
    return tool_use(DELEGATE, {"profile": profile, "prompt": prompt})


def agent(prompt: str, **extra: Any) -> dict[str, Any]:
    return tool_use(
        "Agent",
        {
            "description": "Helper",
            "prompt": prompt,
            "subagent_type": "general-purpose",
            "run_in_background": False,
        }
        | extra,
    )


async def open_home(
    log: Log,
    slug: str,
    fake: FakeModel,
    *,
    tools: list[str],
    mode: str = "bypassPermissions",
    rows: dict[str, Any] | None = None,
    targets: tuple[str, ...] = ("fake", "fake2"),
    budgets: dict[str, object] | None = None,
    plugin_dir: Path | None = None,
    **spec: Any,
) -> Session:
    """A throwaway home with rows `fake`, `fake2` and `fake3` on `fake`, overridden or extended
    by `rows`, `targets` as `delegate_targets`, and one chat on `fake`. `spec` goes to
    `NewChat`."""
    from qma.harness import Harness, NewChat, QmxHome, TestMode  # noqa: PLC0415
    from qma.harness.home import plugin_digest  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    root = throwaway_home(slug)
    found = {name: direct_row(fake.url) for name in ("fake", "fake2", "fake3")}
    put_providers(root, found | (rows or {}) | {"delegate_targets": list(targets)})
    put_budgets(root, **(budgets or {}))
    only_tools(tools)
    home = (
        QmxHome(root)
        if plugin_dir is None
        else QmxHome(root, plugin_dir, plugin_digest(plugin_dir))
    )
    control = control_service(home)
    harness = await Harness.open(home, control=control, test=TestMode(loopback_http_provider=True))
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    chat = await harness.start_chat(
        NewChat(title=slug, model="opus", workspace=WORKSPACE, profile="fake", mode=mode, **spec)
    )
    log(f"home {root}, fake model {fake.url}, parent {chat}, delegate_targets {targets}")
    return Session(harness, home, control, chat)


def children(session: Session) -> list[str]:
    """Delegated child chats of the parent: child sessions with a chat record. A native
    helper's mirror session has the parent too, but no chat record."""
    from qma.harness.home import read_record, session_id  # noqa: PLC0415

    return [
        str(row["id"])
        for row in session.control.sessions_list()
        if row.get("parent_id") == session.chat
        and read_record(session.home, session_id(str(row["id"]))) is not None
    ]


def calls(fake: FakeModel, tool: str) -> list[tuple[dict[str, Any], bool, str]]:
    """Each call of `tool` the fake model made: input, is_error and result text."""
    return [(found, err, out) for name, found, err, out in results(fake).values() if name == tool]


def first_messages(fake: FakeModel) -> list[str]:
    return [json.dumps((seen.json.get("messages") or [{}])[0]) for seen in fake.requests]


async def nested(log: Log) -> None:
    fake = FakeModel(
        [Turn([agent("NEST-ONE: start a helper")]), Turn([text("parent done")])],
        routes={
            "NEST-ONE": [Turn([agent("NEST-TWO: count")]), Turn([text("helper done")])],
            "NEST-TWO": [Turn([text("nested helper ran")])],
        },
    ).start()
    session = await open_home(log, "hp13-nested", fake, tools=["Agent", "Bash"])
    try:
        await session.turn(log, "Ask a helper to start its own helper.")
        found = calls(fake, "Agent")
        for tool_input, err, out in found:
            log(f"Agent {tool_input.get('prompt')!r}: is_error={err} result={out[:200]!r}")
        inner = [(err, out) for tool_input, err, out in found if "NEST-TWO" in str(tool_input)]
        started = [m for m in first_messages(fake) if "NEST-TWO" in m]
        log.check(
            "the nested Agent call is refused at depth 1 and no third conversation starts",
            len(inner) == 1 and inner[0][0] and not started,
            (inner, len(started)),
        )
    finally:
        await session.harness.close()
        fake.stop()


async def background(log: Log) -> None:
    from claude_agent_sdk import TaskNotificationMessage  # noqa: PLC0415

    fake = FakeModel(
        [
            Turn([agent("BG-HELPER: say finished", run_in_background=True)]),
            Turn([text("helper started")]),
            Turn([text("helper reported back")]),
        ],
        routes={"BG-HELPER": [Turn([text("background helper finished")])]},
    ).start()
    launched = capture_launches()
    session = await open_home(log, "hp13-background", fake, tools=["Agent"])
    try:
        await session.turn(log, "Start a background helper and wait for it.")
        deadline = time.monotonic() + 60
        notes: list[Any] = []
        while not notes and time.monotonic() < deadline:
            notes = [m for m in launched[0].seen if isinstance(m, TaskNotificationMessage)]
            await asyncio.sleep(0.2)
        record = await wait_turn(session.home, session.chat, 60)
        for note in notes:
            log(f"task notification: task={note.task_id} status={note.status}")
        log.check(
            "the background helper finishes with a completed task notification",
            any(note.status == "completed" for note in notes) and record.turn == "idle",
            ([note.status for note in notes], record.turn),
        )
    finally:
        await session.harness.close()
        fake.stop()


def helper_plugin() -> Path:
    """The QMX plugin plus one agent whose definition names the haiku tier."""
    from qma.harness.home import PLUGIN_DIR  # noqa: PLC0415

    folder = SCRATCH / "hp13-plugin"
    shutil.rmtree(folder, ignore_errors=True)
    shutil.copytree(PLUGIN_DIR, folder)
    (folder / "agents").mkdir()
    (folder / "agents" / "counter.md").write_text(
        "---\nname: counter\ndescription: Counts things.\nmodel: haiku\n---\nYou count things.\n",
        encoding="utf-8",
    )
    return folder


async def model(log: Log) -> None:
    from claude_agent_sdk import ResultMessage  # noqa: PLC0415

    fake = FakeModel(
        [
            Turn([agent("MODEL-HELPER: count", subagent_type="qmx:counter")]),
            Turn([text("parent done")]),
        ],
        routes={"MODEL-HELPER": [Turn([text("counted 3")])]},
    ).start()
    tiers = {"opus": "fake-model", "sonnet": "fake-model", "haiku": "fake-haiku"}
    row = direct_row(fake.url) | {"tiers": tiers | {"fable": "fake-model"}}
    launched = capture_launches()
    session = await open_home(
        log, "hp13-model", fake, tools=["Agent"], rows={"fake": row}, plugin_dir=helper_plugin()
    )
    try:
        await session.turn(log, "Run the counter helper.")
        usage = [m.model_usage for m in launched[0].seen if isinstance(m, ResultMessage)]
        helper = [
            seen.json.get("model")
            for seen in fake.requests
            if "MODEL-HELPER" in json.dumps((seen.json.get("messages") or [{}])[0])
        ]
        log(f"model_usage per result: {usage}; helper request models: {helper}")
        log.check(
            "model_usage shows the model the helper's definition names",
            bool(usage) and "fake-haiku" in (usage[-1] or {}) and set(helper) == {"fake-haiku"},
            (usage, helper),
        )
    finally:
        await session.harness.close()
        fake.stop()


async def kimi(log: Log) -> None:
    from qma.harness.home import read_record, session_id  # noqa: PLC0415

    ledger = spend_ledger()
    prompt = f"Reply with the single word {KIMI_WORD} and nothing else."
    fake = FakeModel([Turn([delegate("kimi", prompt)]), Turn([text("parent done")])]).start()
    minted = capture_grants()
    launched = capture_launches()
    session = await open_home(
        log, "hp13-kimi", fake, tools=[], rows={"kimi": OPENROUTER_ROW}, targets=("kimi",)
    )
    try:
        await ledger.spend(
            "hp13 lane 5 delegate to Kimi",
            2,
            512,
            lambda: session.turn(log, "Delegate the word to Kimi."),
            measured=KIMI_USD,
        )
        [(tool_input, err, out)] = calls(fake, DELEGATE)
        log(f"delegate {tool_input} -> is_error={err} result={out!r}")
        kids = children(session)
        child = kids[0] if kids else ""
        record = read_record(session.home, session_id(child)) if child else None
        for block in session_blocks(session.control, child) if child else []:
            show(log, block)
        log.check(
            "the final text returns and the child session has parent_id set",
            not err and KIMI_WORD in out.upper() and len(kids) == 1 and record is not None,
            (err, out, kids),
        )
        grants = {grant.session_id: grant for grant in minted}
        own = grants.get(child)
        parent = grants.get(session.chat)
        env = launched[1].options.env if len(launched) > 1 else {}
        status = await relay_status(session, own.secret, "opus") if own else 0
        log(
            f"grants by chat: {sorted(grants)}; child grant profile "
            f"{own.profile.name if own else None}; relay with it after the child ended -> {status}"
        )
        log.check(
            "the child ran on its own grant in the relayed home, revoked when it ended",
            own is not None
            and parent is not None
            and own.secret != parent.secret
            and env.get("ANTHROPIC_AUTH_TOKEN") == own.secret
            and env.get("CLAUDE_CONFIG_DIR") == str(session.home.relayed_dir)
            and status == 401,
            (own is not None, env.get("CLAUDE_CONFIG_DIR"), status),
        )
    finally:
        await session.harness.close()
        fake.stop()


def tool_names(seen_body: dict[str, Any]) -> list[str]:
    return [str(tool.get("name")) for tool in seen_body.get("tools") or []]


async def tools(log: Log) -> None:
    import qma.harness.chat as chat_module  # noqa: PLC0415
    from claude_agent_sdk import SystemMessage  # noqa: PLC0415

    fake = FakeModel(
        [Turn([delegate("fake2", "CHILD-TOOLS: say hi")]), Turn([text("parent done")])],
        routes={"CHILD-TOOLS": [Turn([text("child says hi")])]},
    ).start()
    launched = capture_launches()
    infos: list[dict[str, Any]] = []
    base = chat_module.ClaudeSDKClient

    class Info(base):
        async def get_server_info(self) -> Any:
            found = await super().get_server_info()
            infos.append(found or {})
            return found

    chat_module.ClaudeSDKClient = Info
    session = await open_home(log, "hp13-tools", fake, tools=["Agent", "Bash", "Read"])
    banned = {"Task", "Agent", DELEGATE}
    try:
        await session.turn(log, "Delegate a greeting.")
        parent_offered = tool_names(fake.requests[0].json) if fake.requests else []
        child_offered = sorted(
            {
                name
                for seen in fake.requests
                if "CHILD-TOOLS" in json.dumps((seen.json.get("messages") or [{}])[0])
                for name in tool_names(seen.json)
            }
        )
        init = [
            m.data.get("tools", [])
            for m in (launched[1].seen if len(launched) > 1 else [])
            if isinstance(m, SystemMessage) and m.subtype == "init"
        ]
        info = infos[1] if len(infos) > 1 else {}
        in_info = sorted(name for name in banned if f'"{name}"' in json.dumps(info))
        log(f"child server info keys: {sorted(info)}; banned names in it: {in_info}")
        log(f"child init tools: {init}")
        log(f"child request tools: {child_offered}")
        log(f"parent request tools hold Agent and delegate: {sorted(banned & set(parent_offered))}")
        log(f"child disallowed_tools head: {launched[1].options.disallowed_tools[:2]}")
        log.check(
            "the child's server info, init tools and offered tools lack Task, Agent and delegate",
            len(infos) > 1
            and not in_info
            and bool(init)
            and not banned & set(init[0])
            and bool(child_offered)
            and not banned & set(child_offered)
            and {"Agent", DELEGATE} <= set(parent_offered),
            (in_info, init[:1], child_offered),
        )
    finally:
        await session.harness.close()
        fake.stop()


async def subagent(log: Log) -> None:
    fake = FakeModel(
        [Turn([agent("SUB-DELEGATE: delegate")]), Turn([text("parent done")])],
        routes={
            "SUB-DELEGATE": [Turn([delegate("fake2", "never runs")]), Turn([text("sub done")])]
        },
    ).start()
    session = await open_home(log, "hp13-subagent", fake, tools=["Agent"])
    try:
        await session.turn(log, "Have a helper delegate.")
        found = calls(fake, DELEGATE)
        for _, err, out in found:
            log(f"delegate inside the helper: is_error={err} result={out!r}")
        log.check(
            "the native helper's delegate call is denied by the gate and no child starts",
            len(found) == 1
            and found[0][1]
            and "a sub-agent cannot start a helper chat" in found[0][2]
            and not children(session)
            and not DELEGATED,
            (found, children(session), len(DELEGATED)),
        )
    finally:
        await session.harness.close()
        fake.stop()


async def full(log: Log) -> None:
    fake = FakeModel(
        [Turn([delegate("fake2", "FULL: never runs")]), Turn([text("parent done")])]
    ).start()
    launched = capture_launches()
    session = await open_home(log, "hp13-full", fake, tools=["Bash"], budgets={"max_live_chats": 1})
    try:
        await session.turn(log, "Delegate while the table is full.")
        found = calls(fake, DELEGATE)
        took = [round(d.took, 3) for d in DELEGATED]
        log(f"delegate results: {found}; delegate took {took} s; launches {len(launched)}")
        log.check(
            "delegate returns a tool error at once",
            len(found) == 1
            and found[0][1]
            and f"all 1 live chats are busy ({session.chat})" in found[0][2]
            and len(DELEGATED) == 1
            and DELEGATED[0].took < 2
            and len(launched) == 1,
            (found, took, len(launched)),
        )
    finally:
        await session.harness.close()
        fake.stop()


async def allowlist(log: Log) -> None:
    fake = FakeModel([Turn([delegate("fake3", "never runs")]), Turn([text("parent done")])]).start()
    session = await open_home(log, "hp13-allowlist", fake, tools=["Bash"])
    try:
        await session.turn(log, "Delegate to a row outside the allow-list.")
        found = calls(fake, DELEGATE)
        log(f"delegate results: {found}")
        log.check(
            "the call is refused with the allow-list named",
            len(found) == 1
            and found[0][1]
            and found[0][2]
            == "'fake3' is not in the delegate allow-list, [providers] delegate_targets, "
            "which lists fake, fake2"
            and not children(session),
            found,
        )
    finally:
        await session.harness.close()
        fake.stop()


async def unattended(log: Log) -> None:
    from qma.harness import InjectedText  # noqa: PLC0415
    from qma.harness.home import read_record, session_id  # noqa: PLC0415
    from qma.harness.launch import Background, Child  # noqa: PLC0415

    folder = WORKSPACE / "hp13-unattended"
    shutil.rmtree(folder, ignore_errors=True)
    fake = FakeModel(
        [],
        routes={
            "BG-PARENT": [
                Turn([delegate("fake2", "CHILD-ASK: make the folder")]),
                Turn([text("parent done")]),
            ],
            "CHILD-ASK": [
                Turn([tool_use("Bash", {"command": f"mkdir {folder.as_posix()}"})]),
                Turn([text("child finished without the folder")]),
            ],
        },
    ).start()
    launched = capture_launches()
    session = await open_home(
        log,
        "hp13-unattended",
        fake,
        tools=["Bash"],
        mode="default",
        budgets={"unattended_ask_seconds": ASK_S},
        kind=Background(),
    )
    put_claude(session.home.root, {"permissions": {"allow": [DELEGATE]}})
    try:
        log("turn (injected): BG-PARENT delegate")
        await session.harness.send(session.chat, InjectedText("BG-PARENT: delegate the job"))
        record = await wait_turn(session.home, session.chat, 120)
        for block in session_blocks(session.control, session.chat):
            show(log, block)
        kids = children(session)
        child = kids[0] if kids else ""
        child_blocks = session_blocks(session.control, child) if child else []
        for block in child_blocks:
            show(log, block)
        kind = read_record(session.home, session_id(child)).config.kind if child else None
        options = launched[1].options if len(launched) > 1 else None
        expired = [
            b for b in child_blocks if b["type"] == "permission" and b["content"].get("state")
        ]
        found = calls(fake, DELEGATE)
        took = [round(d.took, 2) for d in DELEGATED]
        log(f"parent turn {record.turn}; child kind {kind}; delegate took {took} s -> {found}")
        log.check(
            "the child launched verbatim as Child(unattended=True)",
            kind == Child(session.chat, unattended=True)
            and options is not None
            and options.verbatim_prompts is True
            and options.max_turns is not None,
            (kind, options.verbatim_prompts if options else None),
        )
        log.check(
            f"the child's ask expired after {ASK_S} s, Bash never ran, and its text came back",
            any(b["content"].get("state") == "expired" for b in expired)
            and not folder.exists()
            and bool(DELEGATED)
            and DELEGATED[0].took >= ASK_S
            and len(found) == 1
            and not found[0][1]
            and found[0][2] == "child finished without the folder",
            ([b["content"] for b in expired], folder.exists(), took, found),
        )
    finally:
        await session.harness.close()
        fake.stop()


async def perf(log: Log) -> None:
    script = [Turn([delegate("fake2", f"PERF-{n}: say done")]) for n in range(PERF_RUNS)]
    fake = FakeModel(
        [*script, Turn([text("parent done")])],
        routes={f"PERF-{n}": [Turn([text(f"child {n} done")])] for n in range(PERF_RUNS)},
    ).start()
    session = await open_home(log, "hp13-perf", fake, tools=[])
    try:
        await session.turn(log, "Delegate five times.")
        times: list[float] = []
        for done in DELEGATED:
            marker = done.prompt.split(":")[0]
            first = min(
                (
                    seen.at
                    for seen in fake.requests
                    if marker in seen.body.decode("utf-8", "replace")
                ),
                default=float("inf"),
            )
            times.append(first - done.began)
            log(
                f"{marker}: first upstream request {first - done.began:.2f} s after the call; "
                f"whole delegation {done.took:.2f} s -> {done.outcome!r}"
            )
        median = statistics.median(times) if times else float("inf")
        log("baseline: trunk has no delegate tool, so there is no trunk number")
        log(
            "the child provider is the fake model; the path from the call to the child's first "
            "request (start_chat, slot, relay grant, CLI launch) is the one a Kimi child takes"
        )
        log.check(
            f"median under {PERF_LIMIT_S:.0f} s over {PERF_RUNS} delegations",
            len(times) == PERF_RUNS and median < PERF_LIMIT_S,
            f"{[round(t, 2) for t in times]} median {median:.2f} s",
        )
    finally:
        await session.harness.close()
        fake.stop()


PARTS = {
    "nested": nested,
    "background": background,
    "model": model,
    "kimi": kimi,
    "tools": tools,
    "subagent": subagent,
    "full": full,
    "allowlist": allowlist,
    "unattended": unattended,
    "perf": perf,
}
SLUGS = {"kimi": "delegate", "tools": "child-tools"}


def main() -> int:
    part = sys.argv[1] if len(sys.argv) > 1 else ""
    if part not in PARTS:
        raise SystemExit(f"usage: s11_helpers.py {{{'|'.join(PARTS)}}}")
    log = Log(f"hp13-{SLUGS.get(part, part)}")
    boot()
    use_fake_home()
    use_fake_key()
    time_delegates()
    asyncio.run(PARTS[part](log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
