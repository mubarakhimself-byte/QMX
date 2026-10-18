"""EP0 p_compact_window. No plan turn and no provider spend.

1. The harness parses an OpenRouter row carrying `quirks.env.CLAUDE_CODE_AUTO_COMPACT_WINDOW`
   and keeps the host default `ENABLE_TOOL_SEARCH=false` beside it.
2. The same quirk on a fake-model key row in a throwaway home: a Background chat's launched CLI
   gets the value in its options env, and the CLI's own Bash child echoes it back, so the value
   reached the CLI process. The env path is the same for every relayed row (`launch_env`).
3. Background chats are verbatim: `/compact` sent as `InjectedText` reaches the model as text
   and no `compacted` block appears. No chat is driven to compaction.

    p_compact_window.py
"""

from __future__ import annotations

from common import (
    OPENROUTER_ROW,
    boot,
    fake_key_row,
    launched_options,
    live,
    log,
    opened,
    run,
    throwaway_home,
    workspace,
)

WINDOW = "50000"
NAME = "CLAUDE_CODE_AUTO_COMPACT_WINDOW"


async def main() -> int:
    from fake_model import FakeModel, Turn, text, tool_use  # noqa: PLC0415
    from qma.harness import TestMode  # noqa: PLC0415
    from qma.harness.launch import Background, verbatim  # noqa: PLC0415
    from qma.harness.profiles import parse_profiles  # noqa: PLC0415

    say = log("ep0-compact")
    boot()
    live.use_fake_key()
    quirks = {"env": {NAME: WINDOW}}
    parsed = parse_profiles({"openrouter": OPENROUTER_ROW | {"quirks": quirks}})
    say(f"row errors: {dict(parsed.errors)}")
    env = dict(parsed.get("openrouter").quirks.env)
    say(f"parsed OpenRouter row quirks.env: {env}")
    say.check(
        "the OpenRouter row keeps the window beside the host default",
        env == {"ENABLE_TOOL_SEARCH": "false", NAME: WINDOW},
        env,
    )

    fake = FakeModel(
        [
            Turn([tool_use("Bash", {"command": f"echo WINDOW=${NAME}"})]),
            Turn([text("echoed")]),
        ]
    ).start()
    root = throwaway_home("compact")
    live.put_providers(root, {"fake": fake_key_row(fake.url, **{NAME: WINDOW})})
    live.only_tools(["Bash"])
    options = launched_options()
    try:
        async with opened(root, test=TestMode(loopback_http_provider=True)) as h:
            chat = await h.background(
                "ep0 compact",
                workspace("compact"),
                model="opus",
                profile="fake",
                mode="bypassPermissions",
            )
            mark = h.mark(chat)
            await h.inject(chat, "Echo the window.")
            await h.wait_idle(chat, 120)
            blocks = h.blocks(chat, mark)
            for block in blocks:
                live.show(say, block)
            seen = [dict(o.env or {}).get(NAME) for o in options]
            say(f"launched CLIs' options env {NAME}: {seen}")
            say.check("the launched CLI's options env holds the row's window", WINDOW in seen, seen)
            results = [str(b["content"]) for b in blocks if b["type"] == "tool"]
            say.check(
                "the CLI's Bash child echoed the window, so the CLI process held it",
                any(f"WINDOW={WINDOW}" in r for r in results),
                [r[:200] for r in results],
            )

            say(f"launch.verbatim(Background()) = {verbatim(Background())}")
            before = len(fake.requests)
            mark = h.mark(chat)
            await h.inject(chat, "/compact")
            await h.wait_idle(chat, 120)
            after = h.blocks(chat, mark)
            compacted = [b for b in after if b["type"] == "changed"]
            sent = [s for s in fake.requests[before:] if b"/compact" in s.body]
            say(f"blocks after /compact: {[b['type'] for b in after]}")
            say.check(
                "Background /compact reached the model as text and did not compact",
                verbatim(Background()) and bool(sent) and not compacted,
                {"requests_holding_/compact": len(sent), "changed_blocks": compacted},
            )
    finally:
        fake.stop()
    return int(say.verdict())


if __name__ == "__main__":
    run(main)
