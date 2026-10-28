"""HP12 lanes 7 to 10 and the perf probe. Only `model` and `perf` use the ship home; `model`
spends two plan turns (haiku, then sonnet) and `perf` none. The rest run on the fake model.

    hp12_lanes.py s41     lane 7, S41 quote half. A chat on a Kimi row (fake model). PASS when a
                          quote to `kimi-k2.7-code` is refused with no relaunch and the chat
                          unchanged, and `kimi-k3[1m]` and `haiku` pass both `quote` and the relay
                          under the chat's own grant.
    hp12_lanes.py mode    lane 8. PASS when a permission-mode quote has no warning, its only step
                          is `set_mode`, apply relaunches nothing, and the next turn's `init`
                          reports the new mode.
    hp12_lanes.py model   lane 9, plan. PASS when haiku to sonnet quotes `set_model` with a warning
                          naming the uncached tokens, apply relaunches nothing, and the next
                          reply's model is a sonnet.
    hp12_lanes.py revoke  lane 10. PASS when, after a `fake` to `fake2` relaunch, the old grant
                          secret gets 401 from the relay, the new one does not, and the
                          transcript is the same file with its bytes from before the switch
                          unchanged.
    hp12_lanes.py deepseek  OpenRouter host default, one short real turn. A throwaway home holds an
                          OpenRouter row as typed (no quirks) pinned to DeepSeek V4.1 Flash. PASS
                          when the launch env has `ENABLE_TOOL_SEARCH=false` and the reply is OK,
                          not a 400.
    hp12_lanes.py perf    five plan<->fake switches of a live chat in the ship home, with no plan
                          turn. PASS when the median time from `apply` to the chat being Live
                          again is under 10 s.
"""

from __future__ import annotations

import asyncio
import json
import statistics
import sys
from typing import Any

import httpx
from common import (
    SHIP_HOME,
    Log,
    boot,
    capture_launches,
    put_providers,
    require_login,
    throwaway_home,
    use_fake_home,
    use_fake_key,
)
from fake_model import FakeModel, Turn, text
from money_lane import direct_row
from switch_lane import (
    OPENROUTER_ROW,
    apply,
    assistant_entries,
    fake_pair,
    quote,
    spend_ledger,
    start,
)

PERF_SWITCHES = 5
PERF_LIMIT_S = 10.0
KIMI_TIERS = {"opus": "kimi-k3", "sonnet": "kimi-k3", "haiku": "kimi-k2.6", "fable": "kimi-k3"}


async def relay_status(session: Any, secret: str, model: str) -> int:
    """The relay's status for a one-token request for `model` under `secret`."""
    relay = session.harness._deps.relay
    async with httpx.AsyncClient(base_url=relay.base_url, trust_env=False) as client:
        reply = await client.post(
            "/v1/messages?beta=true",
            json={"model": model, "max_tokens": 8, "messages": [], "stream": True},
            headers={"authorization": f"Bearer {secret}"},
        )
    return reply.status_code


async def s41(log: Log) -> None:
    from qma.harness import LaunchRefused, TestMode  # noqa: PLC0415

    root = throwaway_home("hp12-s41")
    fake = FakeModel([Turn([text("hi")])], every_request=True).start()
    row = {**direct_row(fake.url), "tiers": KIMI_TIERS}
    put_providers(root, {"kimi": row})
    launched = capture_launches()
    session = await start(
        root, title="s41", profile="kimi", test=TestMode(loopback_http_provider=True), tools=[]
    )
    chat = session.harness._chat(session.chat)
    try:
        await session.turn(log, "Say hi.")
        secret = chat._live.grant.secret
        try:
            await quote(log, session, model="kimi-k2.7-code")
            refused = "quoted"
        except LaunchRefused as error:
            refused = f"refused: {error}"
        log.check(
            "kimi-k2.7-code is refused before any relaunch",
            refused.startswith("refused")
            and len(launched) == 1
            and chat.record.config.model == "opus",
            (refused, len(launched), chat.record.config.model),
        )
        for model, served in (("kimi-k3[1m]", "kimi-k3"), ("haiku", "kimi-k2.6")):
            found = await quote(log, session, model=model)
            before = len(fake.requests)
            status = await relay_status(session, secret, model)
            sent = [seen.json.get("model") for seen in fake.requests[before:]]
            log(f"relay under the chat's grant: {model} -> {status}, forwarded {sent}")
            log.check(
                f"{model} passes quote and the relay alike",
                [s.value for s in found.steps] == ["set_model"]
                and status == 200
                and sent == [served],
                ([s.value for s in found.steps], status, sent),
            )
        await apply(log, session, found.id)
        log.check(
            "applying the alias quote changed the model without a relaunch",
            chat.record.config.model == "haiku" and len(launched) == 1,
            (chat.record.config.model, len(launched)),
        )
    finally:
        await session.harness.close()
        fake.stop()


def init_modes(launched: list[Any]) -> list[str]:
    return [
        str(message.data.get("permissionMode"))
        for client in launched
        for message in client.seen
        if getattr(message, "subtype", None) == "init"
    ]


async def mode(log: Log) -> None:
    fake, session, launched = await fake_pair(
        log, "hp12-mode", [Turn([text("one")]), Turn([text("two")])], tools=["Bash"]
    )
    chat = session.harness._chat(session.chat)
    try:
        await session.turn(log, "Say one.")
        found = await quote(log, session, mode="acceptEdits")
        took = await apply(log, session, found.id)
        log.check(
            "the quote has no warning and its only step is set_mode",
            found.warning is None and [s.value for s in found.steps] == ["set_mode"],
            (found.warning, [s.value for s in found.steps]),
        )
        log.check(
            "it applied at once, with no relaunch",
            took < 2 and len(launched) == 1 and chat.record.config.mode == "acceptEdits",
            (f"{took:.2f} s", len(launched), chat.record.config.mode),
        )
        await session.turn(log, "Say two.")
        modes = init_modes(launched)
        log.check("the next turn's init reports acceptEdits", modes[-1:] == ["acceptEdits"], modes)
    finally:
        await session.harness.close()
        fake.stop()


async def model(log: Log) -> None:
    launched = capture_launches()
    session = await start(SHIP_HOME, title="hp12 lane 9", model="haiku", profile="claude", tools=[])
    try:
        await session.turn(log, "Reply with the single word ONE.")
        found = await quote(log, session, model="sonnet")
        log.check(
            "the quote's only step is set_model and the warning names the uncached tokens",
            [s.value for s in found.steps] == ["set_model"]
            and found.recomputed_tokens > 0
            and str(found.warning).startswith("Switching to sonnet resends ~")
            and "tokens uncached" in str(found.warning),
            (found.warning, found.recomputed_tokens),
        )
        await apply(log, session, found.id)
        await session.turn(log, "Reply with the single word TWO.")
        models = [
            entry["message"].get("model") for entry in assistant_entries(session.transcript())
        ]
        log(f"reply models in the transcript: {models}")
        log.check(
            "no relaunch, and the reply after the change ran on sonnet",
            len(launched) == 1 and "haiku" in str(models[0]) and "sonnet" in str(models[-1]),
            (len(launched), models),
        )
    finally:
        await session.harness.close()


async def revoke(log: Log) -> None:
    fake, session, launched = await fake_pair(
        log, "hp12-revoke", [Turn([text("one")])], tools=["Bash"]
    )
    chat = session.harness._chat(session.chat)
    try:
        await session.turn(log, "Say one.")
        old = chat._live.grant.secret
        from qma.harness.chat import transcript  # noqa: PLC0415

        path = transcript(session.home, session.chat)
        before = path.read_bytes() if path else b""
        found = await quote(log, session, profile="fake2")
        await apply(log, session, found.id)
        new = chat._live.grant.secret
        statuses = [await relay_status(session, secret, "opus") for secret in (old, new)]
        log(f"relay with the old grant secret -> {statuses[0]}, with the new one -> {statuses[1]}")
        log.check(
            "the old grant secret gets 401 and the new one does not",
            statuses[0] == 401 and statuses[1] != 401 and len(launched) == 2,
            statuses,
        )
        after_path = transcript(session.home, session.chat)
        after = after_path.read_bytes() if after_path else b""
        added = [
            json.loads(line).get("type") for line in after[len(before) :].decode().splitlines()
        ]
        log(f"transcript {path} {len(before)} -> {len(after)} bytes; lines added: {added}")
        log.check(
            "the transcript is the same file, and the bytes before the switch are unchanged",
            path is not None and after_path == path and after.startswith(before),
            (str(after_path), len(before), len(after)),
        )
    finally:
        await session.harness.close()
        fake.stop()


async def perf(log: Log) -> None:
    from qma.harness import TestMode  # noqa: PLC0415

    fake = FakeModel([Turn([text("one")])]).start()
    session = await start(
        SHIP_HOME,
        title="hp12 perf",
        profile="claude",
        test=TestMode(loopback_http_provider=True),
        tools=[],
    )
    control = session.control
    found = dict(control.settings_get("providers"))
    control.settings_put("providers", found | {"fake": direct_row(fake.url)})
    log("ship home [providers] += fake (loopback fake model) for the probe")
    chat = session.harness._chat(session.chat)
    times: list[float] = []
    try:
        first = await quote(log, session, profile="fake")
        await apply(log, session, first.id)
        await session.turn(log, "Say one.")
        for n in range(PERF_SWITCHES):
            target = "claude" if chat.record.config.profile == "fake" else "fake"
            switch = await quote(log, session, profile=target)
            took = await apply(log, session, switch.id)
            log(f"switch {n + 1} to {target}: live={chat.is_live} in {took:.2f} s")
            times.append(took if chat.is_live else float("inf"))
    finally:
        await session.harness.close()
        control.settings_update("providers", lambda _current: found)
        log(f"ship home [providers] restored to {sorted(control.settings_get('providers'))}")
        fake.stop()
    median = statistics.median(times)
    log(f"apply to Live, seconds: {[round(t, 2) for t in times]}; median {median:.2f}")
    log("baseline: trunk has no mid-chat switch, so there is no trunk number")
    log.check(f"median under {PERF_LIMIT_S:.0f} s", median < PERF_LIMIT_S, f"{median:.2f} s")


async def deepseek(log: Log) -> None:
    from spend import DEEPSEEK_FLASH  # noqa: PLC0415

    root = throwaway_home("hp12-deepseek")
    row = {**OPENROUTER_ROW, "tiers": dict.fromkeys(KIMI_TIERS, DEEPSEEK_FLASH.model)}
    put_providers(root, {"openrouter": row})
    log(f"row as typed: {row}")
    launched = capture_launches()
    session = await start(root, title="hp12 deepseek", profile="openrouter", tools=["Bash"])
    try:
        ledger = spend_ledger(DEEPSEEK_FLASH)
        _, found = await ledger.spend(
            "deepseek tool search off", 2, 512, lambda: session.turn(log, "Reply with OK.")
        )
        flag = launched[0].options.env.get("ENABLE_TOOL_SEARCH")
        texts = [str(b["content"].get("text")) for b in found if b["type"] == "text"]
        needs = [b for b in found if b["type"] == "needs_you"]
        log(f"ENABLE_TOOL_SEARCH in launch env: {flag}")
        log.check(
            "DeepSeek on the default OpenRouter row answers with tool search off",
            flag == "false" and not needs and any("OK" in t for t in texts),
            (flag, texts, len(needs)),
        )
    finally:
        await session.harness.close()


PARTS = {
    "deepseek": deepseek,
    "s41": s41,
    "mode": mode,
    "model": model,
    "revoke": revoke,
    "perf": perf,
}


def main() -> int:
    part = sys.argv[1] if len(sys.argv) > 1 else ""
    if part not in PARTS:
        raise SystemExit(f"usage: hp12_lanes.py {{{'|'.join(PARTS)}}}")
    log = Log(f"hp12-{part}")
    boot()
    use_fake_home()
    use_fake_key()
    if part in {"model", "perf"}:
        require_login(log)
    asyncio.run(PARTS[part](log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
