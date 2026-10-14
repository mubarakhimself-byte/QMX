"""S8 and the HP7 OpenRouter checks, through the relay, under the spend guard.

    s08_providers.py rows     S8: each keyed row of HP1's table. OpenRouter runs B1 (a Read
                              returns a marker), B4 (two Reads across thinking turns), B3
                              (cache reads on turn three, read from the relay's journal rows),
                              WebSearch and the tool-search state; every other row reads
                              NO KEY until its key is in the keyring.
    s08_providers.py check2   Operator check 2 on the OpenRouter profile: "What is in this
                              folder? Summarise the README." The reads and the text arrive,
                              each upstream request has one model_call row, and the CLI env
                              holds only the relay URL, the grant secret and the tiers.
    s08_providers.py perf     Time to the first streamed event of a "say ok" turn, five direct
                              runs (base URL set to OpenRouter) and five through the relay,
                              interleaved. Fails when the relay median is over 150 ms above.

Real chats run in default mode from a throwaway QMX home and workspace on D:, with reads
allowed and Bash, edits, web fetches and sub-agents denied, and C: and the worktrees denied to
Read; anything that would ask is rejected by the approval floor. Only `rows` allows WebSearch.
Each real turn goes through `spend.Ledger` with `--budget` and `--ledger`.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Final

from common import (
    SCRATCH,
    Log,
    Session,
    boot,
    capture_grants,
    capture_launches,
    put_claude,
    put_providers,
    throwaway_home,
    use_fake_home,
)
from spend import DEEPSEEK_FLASH, Ledger, OverBudget, key_usage, openrouter_key

MODEL: Final = "deepseek/deepseek-v4.1-flash"
MAX_OUTPUT: Final = 2048
CALLS_PER_TURN: Final = 6
ROWS: Final = {
    "openrouter": ("https://openrouter.ai/api", MODEL),
    "glm": ("https://api.z.ai/api/anthropic", "glm-5.3"),
    "kimi": ("https://api.moonshot.ai/anthropic", "kimi-k3"),
    "deepseek": ("https://api.deepseek.com/anthropic", "deepseek-v4-pro"),
    "minimax": ("https://api.minimax.io/anthropic", "MiniMax-M3"),
    "meta": ("https://api.meta.ai", "muse-wonder-1.0"),
}
DENY: Final = [
    "Bash",
    "PowerShell",
    "WebFetch",
    "Write",
    "Edit",
    "NotebookEdit",
    "Agent",
    "Read(//c/**)",
    "Read(//C:/**)",
    "Read(//d/QMX-worktrees/**)",
    "Read(//D:/QMX-worktrees/**)",
]
MARKER: Final = "QMX-HP7-MARKER-7741"
TIERS: Final = ("opus", "sonnet", "haiku", "fable")
ROUTING = re.compile(r"^(ANTHROPIC_\w+|CLAUDE_CODE_OAUTH_TOKEN|\w*API_KEY\w*)$")


def row(name: str) -> dict[str, Any]:
    base, model = ROWS[name]
    return {
        "base_url": base,
        "credential_ref": f"qmx/{name}",
        "tiers": dict.fromkeys(TIERS, model),
        "quirks": {"env": {"CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(MAX_OUTPUT)}},
    }


def has_key(name: str) -> bool:
    import keyring  # noqa: PLC0415

    return keyring.get_password(f"qmx/{name}", name) is not None


def workspace(slug: str) -> Path:
    folder = SCRATCH / "workspaces" / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "README.md").write_text(
        "# Tide tables\n\nA tiny tool that prints tomorrow's high and low tide for a harbour.\n"
        "Run it with `tide <harbour>`. It reads `harbours.csv` in this folder.\n",
        encoding="utf-8",
    )
    (folder / "harbours.csv").write_text("name,offset\nDover,0\nCalais,12\n", encoding="utf-8")
    (folder / "marker.txt").write_text(MARKER + "\n", encoding="utf-8")
    (folder / "a.txt").write_text("amber\n", encoding="utf-8")
    (folder / "b.txt").write_text("basalt\n", encoding="utf-8")
    return folder


def ledger(args: argparse.Namespace) -> Ledger:
    secret = openrouter_key()
    if secret is None:
        raise SystemExit(3)
    return Ledger(args.ledger, args.budget, DEEPSEEK_FLASH, key_usage(secret))


def started_tools(found: list[dict[str, Any]]) -> list[str]:
    return [
        b["content"]["name"]
        for b in found
        if b["type"] == "tool" and b["content"].get("state") == "started"
    ]


def replies(found: list[dict[str, Any]]) -> str:
    return "\n".join(b["content"]["text"] for b in found if b["type"] == "text")


def failed(found: list[dict[str, Any]]) -> list[str]:
    return [b["content"]["reason"] for b in found if b["type"] == "needs_you"]


async def open_router_chat(slug: str, *, allow: list[str], thinking: bool) -> Session:
    from qma.harness import TestMode  # noqa: PLC0415

    root = throwaway_home(slug)
    put_providers(root, {"openrouter": row("openrouter")})
    claude: dict[str, Any] = {"permissions": {"allow": allow, "deny": DENY}}
    if thinking:
        claude["alwaysThinkingEnabled"] = True
    put_claude(root, claude)
    return await Session.start(
        root,
        model="opus",
        workspace=workspace(slug),
        title=slug,
        test=TestMode(),
        profile="openrouter",
    )


async def guarded_turn(
    book: Ledger, session: Session, log: Log, label: str, text: str
) -> list[dict[str, Any]]:
    async def run() -> list[dict[str, Any]]:
        _, found = await session.turn(log, text)
        return found

    return await book.spend(label, CALLS_PER_TURN, MAX_OUTPUT, run)


async def rows_check(log: Log, args: argparse.Namespace) -> None:
    for name in ROWS:
        if name != "openrouter":
            log(f"{name}: {'KEY PRESENT, not run in HP7' if has_key(name) else 'NO KEY'}")
    if not has_key("openrouter"):
        log("BLOCKED: no qmx/openrouter key")
        raise SystemExit(3)
    book = ledger(args)
    launched = capture_launches()
    session = await open_router_chat(
        "hp7-s08", allow=["Read", "Glob", "Grep", "WebSearch"], thinking=True
    )
    try:
        found = await guarded_turn(
            book, session, log, "s08-b1",
            "Use the Read tool to read marker.txt in this folder, then reply with its exact "
            "contents.",
        )  # fmt: skip
        log.check(
            "B1: a Read returned the marker",
            "Read" in started_tools(found) and MARKER in replies(found) and not failed(found),
            (started_tools(found), failed(found)),
        )
        found = await guarded_turn(
            book, session, log, "s08-b4",
            "Read a.txt. Think about the word you found. Then read b.txt and tell me both words.",
        )  # fmt: skip
        thinking = sum(
            1
            for message in launched[-1].seen
            for block in getattr(message, "content", []) or []
            if type(block).__name__ == "ThinkingBlock"
        )
        reads = started_tools(found).count("Read")
        log.check(
            "B4: two Reads across thinking turns, no thinking or signature error",
            reads >= 2 and thinking >= 1 and not failed(found),
            {"reads": reads, "thinking blocks": thinking, "errors": failed(found)},
        )
        before = len(session.journal())
        await guarded_turn(book, session, log, "s08-b3", "Say ok.")
        third = session.journal()[before:]
        reads_cached = [r["payload"]["cache_read_tokens"] for r in third]
        log.check("B3: cache reads on turn three", any(reads_cached), reads_cached)
        found = await guarded_turn(
            book, session, log, "s08-websearch",
            "Use the WebSearch tool once to search for 'Claude Code documentation' and reply "
            "with the title of the first result.",
        )  # fmt: skip
        searched = "WebSearch" in started_tools(found)
        log(f"WebSearch: {'CALLED' if searched else 'NOT CALLED'}; reply: {replies(found)[:200]}")
        log.check("WebSearch ran", searched and not failed(found), failed(found))
        init = next(
            (m.data for c in launched for m in c.seen if getattr(m, "subtype", "") == "init"), {}
        )
        tools = init.get("tools", [])
        log.check(
            "tool search is listed with the row's default env", "ToolSearch" in tools, len(tools)
        )
        profile = session.relay.profiles().get("openrouter")
        log(f"quirks recorded: env={dict(profile.quirks.env)} wire={profile.quirks.wire}")
        rows = session.journal()
        upstream = session.relay.counters.upstream
        log(f"journal model_call rows: {len(rows)}; relay upstream: {upstream}")
        log.check(
            "one row per upstream request", len(rows) == session.relay.counters.upstream, len(rows)
        )
    finally:
        await session.harness.close()
        log(f"OpenRouter spent by this ledger so far: {book.spent():.6f} USD")


async def check2(log: Log, args: argparse.Namespace) -> None:
    if not has_key("openrouter"):
        log("BLOCKED: no qmx/openrouter key")
        raise SystemExit(3)
    book = ledger(args)
    launched = capture_launches()
    grants = capture_grants()
    session = await open_router_chat("hp7-check2", allow=["Read", "Glob", "Grep"], thinking=False)
    try:
        found = await guarded_turn(
            book, session, log, "check2", "What is in this folder? Summarise the README."
        )
        tools = started_tools(found)
        log.check("the reads arrived", bool(tools) and not failed(found), (tools, failed(found)))
        log.check("the text arrived", "tide" in replies(found).lower(), replies(found)[:200])
        rows = [r for r in session.journal() if r["event"] == "model_call"]
        upstream = session.relay.counters.upstream
        log.check(
            "each upstream request has one model_call row",
            len(rows) == upstream and upstream > 0,
            (len(rows), upstream),
        )
        env = dict(launched[-1].options.env)
        grant = grants[-1]
        routing = sorted(name for name in env if ROUTING.match(name))
        log(f"routing names in the CLI env: {routing}")
        log.check(
            "the CLI env holds only the relay URL, the grant secret and the tiers",
            routing
            == sorted(
                [
                    "ANTHROPIC_AUTH_TOKEN",
                    "ANTHROPIC_BASE_URL",
                    *(f"ANTHROPIC_DEFAULT_{t.upper()}_MODEL" for t in TIERS),
                ]
            )
            and env["ANTHROPIC_BASE_URL"] == grant.base_url
            and env["ANTHROPIC_AUTH_TOKEN"] == grant.secret,
            env["ANTHROPIC_BASE_URL"],
        )
        secret = openrouter_key()
        log.check(
            "no key value in the CLI env", secret is not None and secret not in env.values(), False
        )
    finally:
        await session.harness.close()
        log(f"OpenRouter spent by this ledger so far: {book.spent():.6f} USD")


async def first_event(options: Any) -> float:
    from claude_agent_sdk import ClaudeSDKClient, ResultMessage  # noqa: PLC0415
    from claude_agent_sdk.types import StreamEvent  # noqa: PLC0415

    first: float | None = None
    async with ClaudeSDKClient(options) as client:
        start = time.perf_counter()
        await client.query("say ok")
        async for message in client.receive_response():
            if first is None and isinstance(message, StreamEvent):
                first = time.perf_counter() - start
            if isinstance(message, ResultMessage):
                break
    return (first if first is not None else float("inf")) * 1000


async def perf(log: Log, args: argparse.Namespace) -> None:
    from claude_agent_sdk import ClaudeAgentOptions  # noqa: PLC0415
    from qma.harness.home import SessionId  # noqa: PLC0415
    from qma.harness.profiles import ProfileName, parse_profiles  # noqa: PLC0415
    from qma.harness.relay import Relay, keyring_secret  # noqa: PLC0415

    secret = openrouter_key()
    if secret is None:
        log("BLOCKED: no qmx/openrouter key")
        raise SystemExit(3)
    book = ledger(args)
    config_dir = SCRATCH / "homes" / "hp7-perf-claude"
    config_dir.mkdir(parents=True, exist_ok=True)
    ws = workspace("hp7-perf")

    async def ignore(*_: Any) -> None:
        return None

    relay = await Relay(
        secrets=keyring_secret,
        usage=ignore,
        alert=ignore,
        profiles=lambda: parse_profiles({"openrouter": row("openrouter")}),
    ).start()

    def options(base_url: str, token: str) -> Any:
        env = {
            "CLAUDE_CONFIG_DIR": str(config_dir),
            "ANTHROPIC_BASE_URL": base_url,
            "ANTHROPIC_AUTH_TOKEN": token,
            "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "256",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            "NO_PROXY": "127.0.0.1,localhost",
            **{f"ANTHROPIC_DEFAULT_{t.upper()}_MODEL": MODEL for t in TIERS},
        }
        return ClaudeAgentOptions(
            env=env,
            tools=[],
            setting_sources=[],
            model="opus",
            max_turns=1,
            cwd=str(ws),
            permission_mode="default",
            include_partial_messages=True,
        )

    direct: list[float] = []
    relayed: list[float] = []
    try:
        for index in range(5):
            ms = await book.spend(
                f"perf-direct-{index}",
                2,
                256,
                lambda: first_event(options(ROWS["openrouter"][0], secret)),
            )
            direct.append(ms)
            grant = relay.grant(
                SessionId(f"0b9c2f4e-1d3a-4c5b-8e7f-6a5b4c3d2e{index:02d}"),
                ProfileName("openrouter"),
            )
            ms = await book.spend(
                f"perf-relay-{index}",
                2,
                256,
                lambda grant=grant: first_event(options(grant.base_url, grant.secret)),
            )
            relayed.append(ms)
            log(f"run {index}: direct {direct[-1]:.0f} ms, relay {relayed[-1]:.0f} ms")
    except OverBudget as over:
        log(f"REFUSED by the spend guard: {over}")
    finally:
        await relay.close()
        log(f"OpenRouter spent by this ledger so far: {book.spent():.6f} USD")
    if direct and relayed:
        base, head = statistics.median(direct), statistics.median(relayed)
        log(
            f"baseline direct median {base:.0f} ms over {len(direct)}: {[round(x) for x in direct]}"
        )
        log(f"relay median {head:.0f} ms over {len(relayed)}: {[round(x) for x in relayed]}")
        log.check(
            "relay median within 150 ms of direct", head - base <= 150, f"{head - base:+.0f} ms"
        )
    else:
        log.check("perf ran", False, "no runs")


def main() -> int:
    parser = argparse.ArgumentParser(prog="s08_providers.py")
    parser.add_argument("mode", choices=["rows", "check2", "perf"])
    parser.add_argument("--budget", type=float, default=0.10)
    parser.add_argument(
        "--ledger",
        type=Path,
        default=Path("D:/QMX-worktrees/qma-ship/evidence/hp7/openrouter-spend.tsv"),
    )
    args = parser.parse_args()
    log = Log({"rows": "hp7-s08", "check2": "hp7-check2", "perf": "hp7-perf"}[args.mode])
    boot()
    use_fake_home()
    check = {"rows": rows_check, "check2": check2, "perf": perf}[args.mode]
    try:
        asyncio.run(check(log, args))
    except OverBudget as over:
        log.check("the spend guard allowed the run", False, str(over))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
