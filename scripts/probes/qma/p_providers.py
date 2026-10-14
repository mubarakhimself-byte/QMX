"""S8 on the Claude engine: 02b probes B1, B3, B4, WebSearch and tool search per provider.

`p_providers.py <row> --budget USD` runs one row and writes hp1-<row>.log, and `--probes`
picks some of its probes. A row whose keyring entry `qmx/<row>` is empty prints NO KEY for
every probe. `perf --budget USD --runs N` times the first streamed event of a `say ok`
turn, N runs on the plan and on each keyed row, interleaved, into hp1-perf.log.
`toolsearch` collects the tool search and WebSearch rows of every row log into
hp1-toolsearch.log. Every keyed turn goes through the spend guard on `--ledger`.

`stub` runs the row code against the loopback echo server with a fake key, and `lockdown`
has that server ask for tool calls no probe allows. Neither spends anything or says
anything about a provider.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import shutil
import statistics
import sys
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, NamedTuple

from common import (
    HP1_EVIDENCE,
    SCRATCH,
    Lockdown,
    Log,
    Provider,
    bundled_cli,
    describe,
    home_env,
    is_ok,
    plan_options,
    provider_env,
    read_key,
    require_plan_login,
    run_turns,
    scrub_process_env,
    tool_results,
    tool_uses,
)
from p_echo import FAKE_KEY, ToolCall, serve
from spend import MAX_OUTPUT_VAR, Ledger, OverBudget, Prices, guarded_turns, key_usage, max_output

if TYPE_CHECKING:
    from claude_agent_sdk import ClaudeAgentOptions, McpSdkServerConfig, Message

PROVIDERS: Final = {
    p.name: p
    for p in (
        Provider("glm", "https://api.z.ai/api/anthropic", "glm-5.3"),
        Provider("kimi", "https://api.moonshot.ai/anthropic", "kimi-k3"),
        Provider("deepseek", "https://api.deepseek.com/anthropic", "deepseek-v4-pro"),
        Provider("minimax", "https://api.minimax.io/anthropic", "MiniMax-M3"),
        Provider("meta", "https://api.meta.ai", "muse-wonder-1.0"),
        Provider("openrouter", "https://openrouter.ai/api", "deepseek/deepseek-v4.1-flash"),
    )
}
PRICES: Final = {
    "openrouter": Prices(
        PROVIDERS["openrouter"].model,
        usd_per_input_token=2.016e-8,
        usd_per_output_token=8.91e-7,
        input_tokens_per_call=8_000,
    ),
}
"""A locked-down row request measured at most 6,150 bytes on the echo, about 2,000 tokens.
8,000 also covers a turn's earlier replies, each at most the output cap."""
LEDGER: Final = HP1_EVIDENCE / "openrouter-spend.tsv"

TOOL_SEARCH_ON: Final = {"ENABLE_TOOL_SEARCH": "true"}
BETAS_OFF: Final = {"CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1"}
THINKING: Final = {"type": "enabled", "budget_tokens": 1024}
OUTPUT_CAP: Final = {MAX_OUTPUT_VAR: "2048"}
PERF_RUNS: Final = 3
SLOW_FACTOR: Final = 3

PING: Final = "mcp__probe__ping"
ROW_TOOLS: Final = frozenset({"ToolSearch", PING})
B1_MARKER: Final = "hp1-b1-marker"
B1_LOCKDOWN: Final = Lockdown(frozenset({f"echo {B1_MARKER}"}), ROW_TOOLS)
B4_LOCKDOWN: Final = Lockdown(frozenset({"echo hp1-b4-a", "echo hp1-b4-b"}), ROW_TOOLS)
LOCKDOWN_CANARY: Final = "hp1-lockdown-canary-7f3a"
CUT_OFF: Final = re.compile(r"search was cut off", re.IGNORECASE)


class Turn(NamedTuple):
    ok: bool
    bash: int
    thinking: int


@dataclass(frozen=True)
class Budget:
    usd: float
    ledger: Path


@dataclass
class Row:
    log: Log
    name: str
    spend: Ledger
    env: dict[str, str]
    default_tool_search: str = "not read"


def ping_server() -> McpSdkServerConfig:
    """One MCP tool, so ToolSearch has a deferrable tool to stand in front of. The init
    tool list names deferred tools too, so ToolSearch itself is the signal."""
    from claude_agent_sdk import create_sdk_mcp_server, tool  # noqa: PLC0415

    @tool("ping", "Answers pong.", {})
    async def ping(_args: dict[str, Any]) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": "pong"}]}

    return create_sdk_mcp_server("probe", tools=[ping])


def fresh_home(name: str) -> Path:
    root = SCRATCH / "hp1" / name / "claude"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def init_tools(messages: list[Message]) -> list[str]:
    from claude_agent_sdk import SystemMessage  # noqa: PLC0415

    for m in messages:
        if isinstance(m, SystemMessage) and m.subtype == "init":
            return [str(name) for name in m.data.get("tools", [])]
    return []


def tool_search_state(tools: list[str]) -> str:
    if not tools:
        return "no init"
    return f"ToolSearch={'on' if 'ToolSearch' in tools else 'off'}"


def tool_calls(messages: list[Message]) -> list[str]:
    from claude_agent_sdk import AssistantMessage, ToolUseBlock  # noqa: PLC0415

    return [
        block.name
        for m in messages
        if isinstance(m, AssistantMessage)
        for block in m.content
        if isinstance(block, ToolUseBlock)
    ]


def cache_reads(messages: list[Message]) -> list[int]:
    from claude_agent_sdk import ResultMessage  # noqa: PLC0415

    return [
        int((m.usage or {}).get("cache_read_input_tokens") or 0)
        for m in messages
        if isinstance(m, ResultMessage)
    ]


def api_errors(messages: list[Message]) -> list[str]:
    from claude_agent_sdk import ResultMessage  # noqa: PLC0415

    return [
        f"status={m.api_error_status} {str(m.result)[:200]}"
        for m in messages
        if isinstance(m, ResultMessage) and m.is_error
    ]


def thinking_blocks(messages: list[Message]) -> int:
    from claude_agent_sdk import AssistantMessage, ThinkingBlock  # noqa: PLC0415

    return sum(
        isinstance(block, ThinkingBlock)
        for m in messages
        if isinstance(m, AssistantMessage)
        for block in m.content
    )


def turns(messages: list[Message]) -> list[Turn]:
    from claude_agent_sdk import ResultMessage  # noqa: PLC0415

    done: list[Turn] = []
    current: list[Message] = []
    for m in messages:
        current.append(m)
        if isinstance(m, ResultMessage):
            done.append(Turn(is_ok(current), tool_uses(current, "Bash"), thinking_blocks(current)))
            current = []
    return done


def b1_verdict(bash_calls: int, marker_seen: bool, ok: bool) -> str:
    return "PASS" if bash_calls and marker_seen and ok else "FAIL"


def b3_verdict(reads: list[int]) -> str:
    return "PASS" if len(reads) >= 3 and reads[2] > 0 else "FAIL"


def b4_verdict(run: list[Turn], errors: list[str]) -> str:
    thinking_error = any(re.search(r"thinking|signature", e, re.IGNORECASE) for e in errors)
    if thinking_error or len(run) != 2 or not all(t.ok and t.bash for t in run):
        return "FAIL"
    return "PASS" if any(t.thinking for t in run) else "NO THINKING"


def tool_search_verdict(state: str, errors: list[str], calls: list[str]) -> str:
    if state != "ToolSearch=on":
        return "FAIL"
    if errors:
        return "LISTED, REJECTED"
    if PING not in calls:
        return "NOT LOADED"
    return "PASS" if "ToolSearch" in calls[: calls.index(PING)] else "NOT DEFERRED"


def websearch_verdict(calls: int, outcomes: list[tuple[bool, str]], ok: bool) -> str:
    """Reads each tool result's error flag, since a real result page can mention errors."""
    if not calls:
        return "NOT CALLED"
    if not ok or not outcomes:
        return "REFUSED"
    if any(not is_error for is_error, _ in outcomes):
        return "PASS"
    return "CUT OFF" if all(CUT_OFF.search(text) for _, text in outcomes) else "REFUSED"


def tool_outcomes(messages: list[Message]) -> list[tuple[bool, str]]:
    from claude_agent_sdk import ToolResultBlock, UserMessage  # noqa: PLC0415

    blocks = [
        block
        for m in messages
        if isinstance(m, UserMessage) and isinstance(m.content, list)
        for block in m.content
        if isinstance(block, ToolResultBlock)
    ]
    return [
        (bool(block.is_error), text)
        for block, text in zip(blocks, tool_results(messages), strict=True)
    ]


def perf_verdict(plan_ms: list[float], row_ms: list[float]) -> str:
    if not row_ms:
        return "FAIL"
    return (
        "SLOW" if statistics.median(row_ms) > SLOW_FACTOR * statistics.median(plan_ms) else "PASS"
    )


def lockdown_verdict(results: list[str], calls: int, leaked: bool) -> str:
    ran = sum(r.strip() == B1_MARKER for r in results)
    return "PASS" if len(results) == calls and not leaked and ran == 1 else "FAIL"


def spread(times: list[float]) -> str:
    if not times:
        return "no first event"
    return (
        f"median {statistics.median(times):.0f} ms, range {min(times):.0f} to "
        f"{max(times):.0f} ms over {len(times)} runs {[round(t) for t in times]}"
    )


def ledger(provider: Provider, secret: str, budget: Budget) -> Ledger | None:
    prices = PRICES.get(provider.name)
    if prices is None:
        return None
    return Ledger(budget.ledger, prices, key_usage(secret), budget.usd)


def capped_env(provider: Provider, secret: str, home: Path) -> dict[str, str]:
    return provider_env(os.environ, provider, secret, home) | OUTPUT_CAP


def no_key_rows(log: Log, provider: Provider) -> None:
    for probe in PROBES:
        log.row(f"{probe} {provider.name}", f"keyring {provider.keyring_service} empty", "NO KEY")


def row_options(env: dict[str, str], lockdown: Lockdown, **overrides: Any) -> ClaudeAgentOptions:
    row: dict[str, Any] = {
        "env": env,
        "model": "sonnet",
        "mcp_servers": {"probe": ping_server()},
        "max_turns": 2,
    }
    return plan_options(lockdown, **(row | overrides))


async def b1_turn(row: Row) -> tuple[str, list[Message]]:
    seen = await guarded_turns(
        row.spend,
        row.log,
        "B1",
        row_options(row.env, B1_LOCKDOWN),
        [f"Run this exact Bash command: echo {B1_MARKER}. Then reply with its output only."],
    )
    marker_seen = any(B1_MARKER in text for text in tool_results(seen))
    return b1_verdict(tool_uses(seen, "Bash"), marker_seen, is_ok(seen)), seen


async def probe_b1(row: Row) -> None:
    verdict, seen = await b1_turn(row)
    row.log(f"init tools, default env: {init_tools(seen)}")
    row.default_tool_search = tool_search_state(init_tools(seen))
    betas = "on"
    if verdict != "PASS":
        row.log(f"B1 failed with {api_errors(seen)}; retrying with experimental betas off")
        row.env |= BETAS_OFF
        verdict, seen = await b1_turn(row)
        betas = "off needed" if verdict == "PASS" else "off did not help"
    row.log.row(f"B1 {row.name}", f"betas {betas}; errors {api_errors(seen)}", verdict)


async def probe_tool_search(row: Row) -> None:
    seen = await guarded_turns(
        row.spend,
        row.log,
        "tool search",
        row_options(row.env | TOOL_SEARCH_ON, Lockdown(tools=ROW_TOOLS), max_turns=3),
        ["Find the probe server's ping tool with tool search, call it, and reply with its answer."],
    )
    row.log(f"init tools, ENABLE_TOOL_SEARCH=true: {init_tools(seen)}")
    on_state = tool_search_state(init_tools(seen))
    errors, calls = api_errors(seen), tool_calls(seen)
    row.log.row(
        f"tool search {row.name}",
        f"default: {row.default_tool_search}; ENABLE_TOOL_SEARCH=true: {on_state}; "
        f"calls {calls}; errors {errors}",
        tool_search_verdict(on_state, errors, calls),
    )


async def probe_b3(row: Row) -> None:
    seen = await guarded_turns(
        row.spend,
        row.log,
        "B3",
        row_options(row.env, Lockdown(tools=ROW_TOOLS), max_turns=1),
        [
            "Reply with the single word one.",
            "Reply with the single word two.",
            "Reply with the single word three.",
        ],
    )
    reads = cache_reads(seen)
    row.log.row(
        f"B3 {row.name}",
        f"cache_read_input_tokens per turn {reads}; errors {api_errors(seen)}",
        b3_verdict(reads),
    )


async def probe_b4(row: Row) -> None:
    seen = await guarded_turns(
        row.spend,
        row.log,
        "B4",
        row_options(row.env, B4_LOCKDOWN, thinking=THINKING),
        [
            "First work out which is larger, 37 x 43 or 39 x 41. Then run the Bash command "
            "`echo hp1-b4-a` and tell me its output and the larger product.",
            "Now run the Bash command `echo hp1-b4-b` and tell me its output.",
        ],
    )
    run, errors = turns(seen), api_errors(seen)
    row.log.row(f"B4 {row.name}", f"turns {run}; errors {errors}", b4_verdict(run, errors))


async def probe_websearch(row: Row) -> None:
    seen = await guarded_turns(
        row.spend,
        row.log,
        "WebSearch",
        row_options(row.env, Lockdown(tools=ROW_TOOLS | {"WebSearch"}), max_turns=3),
        [
            "Use the WebSearch tool to search for 'Anthropic Messages API'. "
            "Reply with the first result's title."
        ],
        extra_calls=2,
    )
    calls = tool_uses(seen, "WebSearch")
    outcomes = tool_outcomes(seen)
    row.log.row(
        f"WebSearch {row.name}",
        f"calls {calls}; results {[(e, t[:200]) for e, t in outcomes]}; errors {api_errors(seen)}",
        websearch_verdict(calls, outcomes, is_ok(seen)),
    )


PROBES: Final[dict[str, Callable[[Row], Awaitable[None]]]] = {
    "B1": probe_b1,
    "tool search": probe_tool_search,
    "B3": probe_b3,
    "B4": probe_b4,
    "WebSearch": probe_websearch,
}


async def probe_row(
    log: Log, provider: Provider, secret: str, spend: Ledger, only: frozenset[str]
) -> None:
    log.redact(secret)
    row = Row(log, provider.name, spend, capped_env(provider, secret, fresh_home(provider.name)))
    for name, probe in PROBES.items():
        if name in only:
            await probe(row)


async def first_event_ms(
    log: Log, options: ClaudeAgentOptions
) -> tuple[float | None, list[Message]]:
    from claude_agent_sdk import ClaudeSDKClient, StreamEvent  # noqa: PLC0415

    first: float | None = None
    seen: list[Message] = []
    async with ClaudeSDKClient(options=options) as client:
        start = time.perf_counter()
        await client.query("say ok")
        async for message in client.receive_response():
            elapsed = (time.perf_counter() - start) * 1000
            if isinstance(message, StreamEvent):
                if first is None:
                    first = elapsed
                    log(f"first stream event {message.event.get('type')} at {elapsed:.0f} ms")
                continue
            log(f"{elapsed:.0f} ms {describe(message)}")
            seen.append(message)
    return first, seen


async def perf(log: Log, budget: Budget, runs: int) -> int:
    require_plan_login(log, bundled_cli())
    keyed = {
        n: (k, spend)
        for n, p in PROVIDERS.items()
        if (k := read_key(p)) is not None and (spend := ledger(p, k, budget)) is not None
    }
    for name in PROVIDERS.keys() - keyed.keys():
        log.row(f"perf {name}", f"keyring qmx/{name} empty or no prices pinned", "NO KEY")
    times: dict[str, list[float]] = {"plan": [], **{n: [] for n in keyed}}
    lockdown = Lockdown(tools=ROW_TOOLS)
    plan = plan_options(
        lockdown,
        env=home_env(),
        mcp_servers={"probe": ping_server()},
        include_partial_messages=True,
        max_turns=1,
    )
    try:
        for run in range(runs):
            for name, row_ms in times.items():
                if name == "plan":
                    ms, seen = await first_event_ms(log, plan)
                else:
                    secret, spend = keyed[name]
                    log.redact(secret)
                    env = capped_env(PROVIDERS[name], secret, fresh_home(name))
                    options = row_options(env, lockdown, include_partial_messages=True, max_turns=1)
                    ms, seen = await spend.spend(
                        f"perf {name} run {run}",
                        2,
                        max_output(options),
                        partial(first_event_ms, log, options),
                    )
                if run == 0 and name == "plan":
                    log(f"plan init tools {init_tools(seen)}")
                    log.row(
                        "tool search plan (control)",
                        tool_search_state(init_tools(seen)),
                        "RECORDED",
                    )
                log(f"perf run {run} {name}: first streamed event {ms} ms")
                if ms is not None:
                    row_ms.append(ms)
    except OverBudget as refusal:
        log(f"perf stopped by the spend guard: {refusal}")
    plan_ms = times.pop("plan")
    log.row("perf plan", spread(plan_ms), "BASELINE")
    for name, row_ms in times.items():
        log.row(f"perf {name}", spread(row_ms), perf_verdict(plan_ms, row_ms))
    return 0


def collect_toolsearch(log: Log) -> int:
    for name in PROVIDERS:
        path = HP1_EVIDENCE / f"hp1-{name}.log"
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        latest: dict[str, str] = {}
        for line in lines:
            parts = line.split("\t")
            if parts[0] == "FINDING" and parts[1].startswith(("tool search", "WebSearch")):
                latest[parts[1]] = line
        log(f"{name}: {len(latest)} rows from {path.name if lines else 'no log yet'}")
        for line in latest.values():
            log(line)
    return 0


def free_ledger(name: str) -> Ledger:
    path = SCRATCH / "hp1" / f"{name}-spend.tsv"
    return Ledger(path, Prices("echo-model", 0, 0, 0), lambda: None, 0.0)


async def stub(log: Log) -> int:
    log(f"scrubbed from this process: {scrub_process_env(os.environ)}")
    with serve() as (url, echo):
        stub_row = Provider("stub", url, "echo-model")
        await probe_row(log, stub_row, FAKE_KEY, free_ledger("stub"), frozenset(PROBES))
    log(f"echo received {[f'{r.method} {r.path} {r.auth}' for r in echo.requests]}")
    return 0


async def lockdown_check(log: Log) -> int:
    log(f"scrubbed from this process: {scrub_process_env(os.environ)}")
    canary = SCRATCH / "hp1" / "lockdown-canary.txt"
    canary.parent.mkdir(parents=True, exist_ok=True)
    canary.write_text(LOCKDOWN_CANARY, encoding="utf-8")
    target = canary.as_posix()
    script = [
        ToolCall("Bash", {"command": f"cat '{target}'"}),
        ToolCall("Bash", {"command": f"echo {B1_MARKER}; cat '{target}'"}),
        ToolCall("Read", {"file_path": target}),
        ToolCall("WebFetch", {"url": "https://example.com", "prompt": "title"}),
        ToolCall("Bash", {"command": f"echo {B1_MARKER}"}),
    ]
    with serve(script) as (url, echo):
        env = capped_env(Provider("stub", url, "echo-model"), FAKE_KEY, fresh_home("lockdown"))
        options = row_options(env, B1_LOCKDOWN, max_turns=len(script) + 1)
        log(f"CLI tools {options.tools}")
        seen = await run_turns(log, options, ["Run the probe."])
    results = tool_results(seen)
    leaked = any(LOCKDOWN_CANARY.encode() in body for body in echo.bodies)
    for call, result in zip(script, results, strict=False):
        log(f"{call.name} {call.input} -> {result[:300]!r}")
    log.row(
        "lockdown: a probe chat runs only its exact command",
        f"{len(results)} results for {len(script)} calls; canary in a request {leaked}",
        lockdown_verdict(results, len(script), leaked),
    )
    return 0


async def row(log: Log, name: str, budget: Budget, only: frozenset[str] = frozenset(PROBES)) -> int:
    log(f"scrubbed from this process: {scrub_process_env(os.environ)}")
    provider = PROVIDERS[name]
    secret = read_key(provider)
    if secret is None:
        no_key_rows(log, provider)
        return 0
    spend = ledger(provider, secret, budget)
    if spend is None:
        log.row(f"B1 {name}", "no prices pinned for the spend guard", "BLOCKED")
        return 0
    await probe_row(log, provider, secret, spend, only)
    return 0


def add_budget(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--budget", type=float, help="USD this run may spend on keyed turns")
    parser.add_argument("--ledger", type=Path, default=LEDGER, help="the spend guard's ledger")


def budget_from(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Budget:
    if args.budget is None:
        parser.error("--budget is required for a run that can spend")
    return Budget(args.budget, args.ledger)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="p_providers.py")
    parser.add_argument("choice", choices=[*PROVIDERS, "perf", "toolsearch", "stub", "lockdown"])
    add_budget(parser)
    parser.add_argument("--probes", default=",".join(PROBES), help="comma-separated probes")
    parser.add_argument("--runs", type=int, default=PERF_RUNS, help="perf runs per side")
    args = parser.parse_args(argv[1:])
    only = frozenset(args.probes.split(","))
    if unknown := only - PROBES.keys():
        parser.error(f"unknown probes {sorted(unknown)}; choose from {list(PROBES)}")
    choice: str = args.choice
    if choice in PROVIDERS:
        log = Log(f"hp1-{choice}", HP1_EVIDENCE)
        return asyncio.run(row(log, choice, budget_from(parser, args), only))
    if choice == "perf":
        log = Log("hp1-perf", HP1_EVIDENCE)
        log(f"scrubbed from this process: {scrub_process_env(os.environ)}")
        return asyncio.run(perf(log, budget_from(parser, args), args.runs))
    if choice == "stub":
        return asyncio.run(stub(Log("hp1-stub", HP1_EVIDENCE)))
    if choice == "lockdown":
        return asyncio.run(lockdown_check(Log("hp1-lockdown", HP1_EVIDENCE)))
    return collect_toolsearch(Log("hp1-toolsearch", HP1_EVIDENCE))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
