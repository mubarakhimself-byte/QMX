"""S10, S37, S38 and S25. Run one case or all: `p_sdk.py [usage|effort|timeout|verbatim]`.

Each case writes its own log: hp0-usage, hp0-effort, hp0-timeout (timeout and verbatim).
"""

from __future__ import annotations

import asyncio
import os
import re
import sys

from claude_agent_sdk import (
    HookContext,
    HookInput,
    HookJSONOutput,
    HookMatcher,
    Message,
    ResultMessage,
    SystemMessage,
)
from common import (
    SCRATCH,
    Log,
    bundled_cli,
    plan_options,
    require_plan_login,
    run_turns,
    scrub_process_env,
    tap_raw,
)

HOOK_TIMEOUT_S = 2.0
HOOK_SLEEP_S = 10.0
SECRET = re.compile(r"(sk-ant-\S+|Bearer \S+|oauth\S*token\S*)", re.IGNORECASE)


def subtypes(messages: list[Message]) -> list[str]:
    return [m.subtype for m in messages if isinstance(m, SystemMessage)]


async def usage() -> None:
    log = Log("hp0-usage")
    with tap_raw(log):
        messages = await run_turns(log, plan_options(), ["/usage"])
    kinds = sorted({type(m).__name__ for m in messages})
    results = [str(m.result)[:400] for m in messages if isinstance(m, ResultMessage)]
    log(f"parsed message types: {kinds}")
    log(f"result text: {results}")
    log.row("S10 /usage reaches Python", f"types={kinds} result={results}", "RECORDED")


async def effort() -> None:
    log = Log("hp0-effort")
    debug_file = SCRATCH / "effort-debug.txt"
    debug_file.unlink(missing_ok=True)
    options = plan_options(
        model="sonnet", effort="low", extra_args={"debug-file": debug_file.as_posix()}
    )
    messages = await run_turns(log, options, ["say ok", "/effort high", "say ok"])
    lines = debug_file.read_text(encoding="utf-8", errors="replace").splitlines()
    debug_file.unlink(missing_ok=True)
    effort_lines = [
        SECRET.sub("[redacted]", line)[:300] for line in lines if "effort" in line.lower()
    ]
    for line in effort_lines:
        log(f"debug: {line}")
    replies = [str(m.result)[:200] for m in messages if isinstance(m, ResultMessage)]
    log(f"replies: {replies}")
    log.row(
        "S37 /effort high changes the next request",
        f"{len(effort_lines)} effort debug lines",
        "RECORDED",
    )


async def timeout() -> None:
    log = Log("hp0-timeout")
    marker = SCRATCH / "timeout-marker.txt"
    marker.unlink(missing_ok=True)

    async def sleeper(
        _input: HookInput, _tool_use_id: str | None, _context: HookContext
    ) -> HookJSONOutput:
        log(f"PreToolUse callback sleeping {HOOK_SLEEP_S}s against timeout {HOOK_TIMEOUT_S}s")
        await asyncio.sleep(HOOK_SLEEP_S)
        return {}

    options = plan_options(
        hooks={
            "PreToolUse": [HookMatcher(matcher="Bash", hooks=[sleeper], timeout=HOOK_TIMEOUT_S)]
        },
        max_turns=2,
    )
    prompt = f"Run this exact Bash command once and reply done: echo ran > '{marker.as_posix()}'"
    messages = await run_turns(log, options, [prompt])
    ran = marker.exists()
    errors = [
        line
        for line in map(str, messages)
        if "timeout" in line.lower() or "timed out" in line.lower()
    ]
    log(f"tool results naming a timeout: {[e[:300] for e in errors]}")
    log.row(
        "S38 sleeping PreToolUse callback blocks Bash in bypass mode",
        f"bash ran={ran}",
        "FAIL" if ran else "PASS",
    )


async def verbatim() -> None:
    log = Log("hp0-timeout")
    plain = await run_turns(log, plan_options(), ["say ok", "/compact"])
    log(f"control system subtypes without verbatim: {subtypes(plain)}")
    guarded = await run_turns(log, plan_options(verbatim_prompts=True), ["say ok", "/compact"])
    log(f"system subtypes with verbatim_prompts=True: {subtypes(guarded)}")
    control = "compact_boundary" in subtypes(plain)
    stopped = "compact_boundary" not in subtypes(guarded)
    log.row("S25 control /compact compacts without verbatim", control, "RECORDED")
    log.row(
        "S25 verbatim /compact produces no compact_boundary", stopped, "PASS" if stopped else "FAIL"
    )


CASES = {"usage": usage, "effort": effort, "timeout": timeout, "verbatim": verbatim}


async def main() -> int:
    chosen = sys.argv[1:] or list(CASES)
    require_plan_login(Log("hp0-sdk"), bundled_cli())
    scrub_process_env(os.environ)
    for name in chosen:
        await CASES[name]()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
