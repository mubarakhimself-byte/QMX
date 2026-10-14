"""S10, S37, S38 and S25. Run one case or all: `p_sdk.py [usage|effort|timeout|verbatim]`.

Each case writes its own log: hp0-usage, hp0-effort, hp0-timeout (timeout and verbatim).
"""

from __future__ import annotations

import asyncio
import os
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
    describe,
    plan_options,
    require_plan_login,
    run_turns,
    s25_verdict,
    s38_verdict,
    scrub_process_env,
    tap_raw,
    tool_results,
    tool_uses,
)

HOOK_TIMEOUT_S = 2.0
HOOK_SLEEP_S = 10.0


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
    levels: list[object] = []

    async def on_stop(
        hook_input: HookInput, _tool_use_id: str | None, _context: HookContext
    ) -> HookJSONOutput:
        level = hook_input.get("effort", {}).get("level")
        levels.append(level)
        log(f"Stop hook effort level: {level}")
        return {}

    options = plan_options(
        model="sonnet", effort="low", hooks={"Stop": [HookMatcher(hooks=[on_stop])]}
    )
    messages = await run_turns(log, options, ["say ok", "/effort high", "say ok"])
    replies = [str(m.result)[:200] for m in messages if isinstance(m, ResultMessage)]
    log(f"replies: {replies}")
    if levels[:1] == ["low"] and levels[-1:] == ["high"]:
        verdict = "PASS"
    elif levels[:1] == ["low"] and levels[-1:] == ["low"]:
        verdict = "FAIL"
    else:
        verdict = "INCONCLUSIVE"
    log.row("S37 /effort high changes the next request", f"Stop effort levels={levels}", verdict)


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
    bash_calls = tool_uses(messages, "Bash")
    blocked = [text for text in tool_results(messages) if "before its timeout" in text]
    log(f"tool results naming the hook timeout: {[text[:300] for text in blocked]}")
    log.row(
        "S38 sleeping PreToolUse callback blocks Bash in bypass mode",
        f"bash calls={bash_calls} timeout results={len(blocked)} bash ran={ran}",
        s38_verdict(bash_calls, len(blocked), ran),
    )


async def verbatim() -> None:
    log = Log("hp0-timeout")
    plain = await run_turns(log, plan_options(), ["say ok", "/compact"])
    log(f"control system subtypes without verbatim: {subtypes(plain)}")
    guarded = await run_turns(log, plan_options(verbatim_prompts=True), ["say ok", "/compact"])
    log(f"system subtypes with verbatim_prompts=True: {subtypes(guarded)}")
    control = "compact_boundary" in subtypes(plain)
    boundary = "compact_boundary" in subtypes(guarded)
    replies = [m for m in guarded if isinstance(m, ResultMessage)]
    compact_reply = replies[1] if len(replies) == 2 else None
    answered = compact_reply is not None and not compact_reply.is_error
    turns = compact_reply.num_turns if compact_reply else 0
    log(f"verbatim /compact reply: {describe(compact_reply) if compact_reply else None}")
    log.row("S25 control /compact compacts without verbatim", control, "RECORDED")
    log.row(
        "S25 verbatim /compact reaches the CLI and produces no compact_boundary",
        f"control={control} answered={answered} turns={turns} compact_boundary={boundary}",
        s25_verdict(control, answered, turns, boundary),
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
