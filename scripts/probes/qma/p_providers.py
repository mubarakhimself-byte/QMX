"""S8 on the Claude engine: 02b probes B1, B3, B4, WebSearch and tool search per provider.

`p_providers.py <row>` runs one row and writes hp1-<row>.log. A row whose keyring entry
`qmx/<row>` is empty prints NO KEY for every probe. `p_providers.py perf` times the first
streamed event of a `say ok` turn, three runs on the plan and on each keyed row,
interleaved, into hp1-perf.log. `p_providers.py toolsearch` collects the tool search and
WebSearch rows of every row log into hp1-toolsearch.log. `p_providers.py stub` runs the
row code against the loopback echo server with a fake key, which proves the path end to
end with no key and no plan turn; its verdicts say nothing about any provider.
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import statistics
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from common import (
    HP1_EVIDENCE,
    SCRATCH,
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
from p_echo import FAKE_KEY, serve

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
        Provider("openrouter", "https://openrouter.ai/api", "moonshotai/kimi-k3"),
    )
}

PROBES: Final = ("B1", "B3", "B4", "WebSearch", "tool search")
TOOL_SEARCH_ON: Final = {"ENABLE_TOOL_SEARCH": "true"}
BETAS_OFF: Final = {"CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1"}
THINKING: Final = {"type": "enabled", "budget_tokens": 2048}
PERF_RUNS: Final = 3
SLOW_FACTOR: Final = 3


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


def b1_verdict(bash_calls: int, marker_seen: bool, ok: bool) -> str:
    return "PASS" if bash_calls and marker_seen and ok else "FAIL"


def b3_verdict(reads: list[int]) -> str:
    return "PASS" if len(reads) >= 3 and reads[2] > 0 else "FAIL"


def b4_verdict(ok: bool, bash_calls: int, errors: list[str]) -> str:
    thinking_error = any(re.search(r"thinking|signature", e, re.IGNORECASE) for e in errors)
    return "PASS" if ok and bash_calls >= 2 and not thinking_error else "FAIL"


def websearch_verdict(calls: int, results: list[str], ok: bool) -> str:
    if not calls:
        return "NOT CALLED"
    refused = (
        not ok or not results or any(re.search(r"error|not supported", r, re.I) for r in results)
    )
    return "REFUSED" if refused else "PASS"


def perf_verdict(plan_ms: list[float], row_ms: list[float]) -> str:
    if not row_ms:
        return "FAIL"
    return (
        "SLOW" if statistics.median(row_ms) > SLOW_FACTOR * statistics.median(plan_ms) else "PASS"
    )


def no_key_rows(log: Log, provider: Provider) -> None:
    for probe in PROBES:
        log.row(f"{probe} {provider.name}", f"keyring {provider.keyring_service} empty", "NO KEY")


def row_options(env: dict[str, str], **overrides: Any) -> ClaudeAgentOptions:
    return plan_options(
        env=env, model="sonnet", mcp_servers={"probe": ping_server()}, max_turns=6, **overrides
    )


async def b1(log: Log, env: dict[str, str]) -> tuple[str, list[Message]]:
    marker = "hp1-b1-marker"
    seen = await run_turns(
        log,
        row_options(env),
        [f"Run this exact Bash command: echo {marker}. Then reply with its output only."],
    )
    marker_seen = any(marker in text for text in tool_results(seen))
    return b1_verdict(tool_uses(seen, "Bash"), marker_seen, is_ok(seen)), seen


async def probe_row(log: Log, provider: Provider, secret: str) -> None:
    log.redact(secret)
    env = provider_env(os.environ, provider, secret, fresh_home(provider.name))
    name = provider.name

    verdict, seen = await b1(log, env)
    log(f"init tools, default env: {init_tools(seen)}")
    default_state = tool_search_state(init_tools(seen))
    betas = "on"
    if verdict != "PASS":
        log(f"B1 failed with {api_errors(seen)}; retrying with experimental betas off")
        env |= BETAS_OFF
        verdict, seen = await b1(log, env)
        betas = "off needed" if verdict == "PASS" else "off did not help"
    log.row(f"B1 {name}", f"betas {betas}; errors {api_errors(seen)}", verdict)

    env |= TOOL_SEARCH_ON
    seen = await run_turns(
        log,
        row_options(env),
        [
            "Reply with the single word one.",
            "Reply with the single word two.",
            "Reply with the single word three.",
        ],
    )
    reads = cache_reads(seen)
    log(f"init tools, ENABLE_TOOL_SEARCH=true: {init_tools(seen)}")
    on_state = tool_search_state(init_tools(seen))
    log.row(f"B3 {name}", f"cache_read_input_tokens per turn {reads}", b3_verdict(reads))
    log.row(
        f"tool search {name}",
        f"default: {default_state}; ENABLE_TOOL_SEARCH=true: {on_state}",
        "PASS" if "ToolSearch=on" in on_state else "FAIL",
    )

    seen = await run_turns(
        log,
        row_options(env, thinking=THINKING),
        [
            "Think it through, then run the Bash command `echo hp1-b4-a` and tell me its output.",
            "Now run the Bash command `echo hp1-b4-b` and tell me its output.",
        ],
    )
    errors = api_errors(seen)
    log.row(
        f"B4 {name}",
        f"thinking blocks {thinking_blocks(seen)}; errors {errors}",
        b4_verdict(is_ok(seen), tool_uses(seen, "Bash"), errors),
    )

    seen = await run_turns(
        log,
        row_options(env),
        [
            "Use the WebSearch tool to search for 'Anthropic Messages API'. "
            "Reply with the first result's title."
        ],
    )
    calls = tool_uses(seen, "WebSearch")
    results = tool_results(seen)
    log.row(
        f"WebSearch {name}",
        f"calls {calls}; result {[r[:200] for r in results]}; errors {api_errors(seen)}",
        websearch_verdict(calls, results, is_ok(seen)),
    )


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


async def perf(log: Log) -> int:
    require_plan_login(log, bundled_cli())
    keyed = {n: k for n, p in PROVIDERS.items() if (k := read_key(p)) is not None}
    for name in PROVIDERS.keys() - keyed.keys():
        log.row(f"perf {name}", f"keyring qmx/{name} empty", "NO KEY")
    times: dict[str, list[float]] = {"plan": [], **{n: [] for n in keyed}}
    plan = plan_options(
        env=home_env(),
        mcp_servers={"probe": ping_server()},
        include_partial_messages=True,
        max_turns=1,
    )
    for run in range(PERF_RUNS):
        for name, row_ms in times.items():
            options = plan
            if name != "plan":
                log.redact(keyed[name])
                env = provider_env(os.environ, PROVIDERS[name], keyed[name], fresh_home(name))
                options = row_options(
                    env | TOOL_SEARCH_ON, include_partial_messages=True, max_turns=1
                )
            ms, seen = await first_event_ms(log, options)
            if run == 0 and name == "plan":
                log(f"plan init tools {init_tools(seen)}")
                log.row(
                    "tool search plan (control)", tool_search_state(init_tools(seen)), "RECORDED"
                )
            log(f"perf run {run} {name}: first streamed event {ms} ms")
            if ms is not None:
                row_ms.append(ms)
    plan_ms = times.pop("plan")
    log.row("perf plan", f"median {statistics.median(plan_ms):.0f} ms of {plan_ms}", "BASELINE")
    for name, row_ms in times.items():
        median = f"median {statistics.median(row_ms):.0f} ms" if row_ms else "no first event"
        log.row(f"perf {name}", f"{median} of {row_ms}", perf_verdict(plan_ms, row_ms))
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


async def stub(log: Log) -> int:
    log(f"scrubbed from this process: {scrub_process_env(os.environ)}")
    with serve() as (url, echo):
        await probe_row(log, Provider("stub", url, "echo-model"), FAKE_KEY)
    log(f"echo received {[f'{r.method} {r.path} {r.auth}' for r in echo.requests]}")
    return 0


async def row(log: Log, name: str) -> int:
    log(f"scrubbed from this process: {scrub_process_env(os.environ)}")
    provider = PROVIDERS[name]
    secret = read_key(provider)
    if secret is None:
        no_key_rows(log, provider)
        return 0
    await probe_row(log, provider, secret)
    return 0


def main(argv: list[str]) -> int:
    choice = argv[1] if len(argv) > 1 else ""
    if choice in PROVIDERS:
        return asyncio.run(row(Log(f"hp1-{choice}", HP1_EVIDENCE), choice))
    if choice == "perf":
        log = Log("hp1-perf", HP1_EVIDENCE)
        log(f"scrubbed from this process: {scrub_process_env(os.environ)}")
        return asyncio.run(perf(log))
    if choice == "stub":
        return asyncio.run(stub(Log("hp1-stub", HP1_EVIDENCE)))
    if choice == "toolsearch":
        return collect_toolsearch(Log("hp1-toolsearch", HP1_EVIDENCE))
    print(f"usage: p_providers.py {'|'.join(PROVIDERS)}|perf|toolsearch|stub", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
