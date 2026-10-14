"""S22, the relay is not general-purpose. A relay like the harness starts, with a Kimi row and
an OpenRouter row both pointed at the fake model, driven over HTTP:

    no bearer, a revoked grant                          -> 401, 401
    Kimi grant asking for claude-opus-5-5               -> 400
    OpenRouter grant asking for openai/gpt-5, openrouter/auto, @preset/x -> 400, 400, 400
    a connection to the relay port on the LAN address   -> refused
    /v1/other with a valid grant                        -> 404
    /v1/messages?beta=true with a valid grant           -> forwarded, query string intact
    the fake model serving claude-opus-x                -> stream ends with an error event
    the fake model serving kimi-k3-20261001             -> streams to message_stop

    s22_relay.py
"""

from __future__ import annotations

import asyncio
import socket
import sys
from typing import Any

import httpx
from common import Log, boot
from fake_model import FAKE_KEY, FakeModel, Turn, text

CHAT = "0b9c2f4e-1d3a-4c5b-8e7f-6a5b4c3d2e1f"
OTHER = "1c9c2f4e-1d3a-4c5b-8e7f-6a5b4c3d2e1f"


def lan_address() -> str | None:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 9))
        address = probe.getsockname()[0]
    except OSError:
        return None
    finally:
        probe.close()
    return None if address.startswith("127.") else address


def message(model: str) -> dict[str, Any]:
    return {
        "model": model,
        "stream": True,
        "max_tokens": 16,
        "messages": [{"role": "user", "content": "hi"}],
    }


async def run(log: Log) -> None:
    from qma.harness.launch import TestMode  # noqa: PLC0415
    from qma.harness.profiles import ProfileName, parse_profiles  # noqa: PLC0415
    from qma.harness.relay import Relay  # noqa: PLC0415

    script = [
        Turn([text("hi")]),
        Turn([text("barred")], served="claude-opus-x"),
        Turn([text("dated")], served="kimi-k3-20261001"),
    ]
    fake = FakeModel(script, every_request=True).start()
    rows = {
        "kimi": {
            "base_url": fake.url,
            "credential_ref": "qmx/kimi",
            "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "kimi-k3"),
        },
        "openrouter": {
            "base_url": fake.url,
            "credential_ref": "qmx/openrouter",
            "tiers": dict.fromkeys(
                ("opus", "sonnet", "haiku", "fable"), "deepseek/deepseek-v4.1-flash"
            ),
        },
    }

    async def ignore(*_: Any) -> None:
        return None

    relay = await Relay(
        secrets=lambda _ref: FAKE_KEY,
        usage=ignore,
        alert=ignore,
        profiles=lambda: parse_profiles(rows, allow_loopback_http=True),
        test=TestMode(loopback_http_provider=True),
    ).start()
    statuses: list[str] = []
    try:
        async with httpx.AsyncClient(base_url=relay.base_url, trust_env=False) as client:

            async def post(path: str, secret: str | None, body: dict[str, Any]) -> httpx.Response:
                headers = {"authorization": f"Bearer {secret}"} if secret else {}
                return await client.post(path, json=body, headers=headers)

            statuses.append(str((await post("/v1/messages", None, message("kimi-k3"))).status_code))
            revoked = relay.grant(OTHER, ProfileName("kimi"))
            relay.revoke(OTHER)
            answer = await post("/v1/messages", revoked.secret, message("kimi-k3"))
            statuses.append(str(answer.status_code))
            kimi = relay.grant(CHAT, ProfileName("kimi"))
            answer = await post("/v1/messages", kimi.secret, message("claude-opus-5-5"))
            statuses.append(str(answer.status_code))
            router = relay.grant(OTHER, ProfileName("openrouter"))
            for model in ("openai/gpt-5", "openrouter/auto", "@preset/x"):
                answer = await post("/v1/messages", router.secret, message(model))
                statuses.append(str(answer.status_code))
            lan = lan_address()
            port = int(relay.base_url.rsplit(":", 1)[1])
            if lan is None:
                statuses.append("no LAN address")
            else:
                try:
                    with socket.create_connection((lan, port), timeout=3):
                        statuses.append("accepted")
                except OSError:
                    statuses.append("refused")
            answer = await post("/v1/other", kimi.secret, message("kimi-k3"))
            statuses.append(str(answer.status_code))
            before = len(fake.requests)
            answer = await post("/v1/messages?beta=true", kimi.secret, message("kimi-k3"))
            forwarded = fake.requests[before:]
            seen_query = forwarded[0].query if forwarded else None
            statuses.append(
                f"forwarded {seen_query}" if answer.status_code == 200 and forwarded else "lost"
            )
            log(f"statuses: {statuses}")
            log.check(
                "the statuses read 401, 401, 400 x4, refused, 404, forwarded with the query",
                statuses
                == [
                    "401",
                    "401",
                    "400",
                    "400",
                    "400",
                    "400",
                    "refused",
                    "404",
                    "forwarded beta=true",
                ],
                statuses,
            )
            log.check(
                "the fake model saw the fake key",
                forwarded[0].headers.get("authorization") == f"Bearer {FAKE_KEY}"
                if forwarded
                else False,
                "",
            )
            family = relay.counters.family
            barred = await post("/v1/messages", kimi.secret, message("kimi-k3"))
            log(f"barred stream: {barred.text[:200]!r}")
            log.check(
                "a barred served model ends the stream with an error",
                barred.text.startswith("event: error") and "claude-opus-x" in barred.text,
                barred.text[:80],
            )
            log.check(
                "the family counter moved",
                relay.counters.family == family + 1,
                relay.counters.family,
            )
            dated = await post("/v1/messages", kimi.secret, message("kimi-k3"))
            log.check(
                "a dated id of the right family streams to the end",
                "kimi-k3-20261001" in dated.text
                and dated.text.rstrip().endswith('{"type": "message_stop"}'),
                dated.text[-60:],
            )
            log(f"counters: {relay.counters}")
    finally:
        await relay.close()
        fake.stop()


def main() -> int:
    log = Log("hp7-s22")
    boot()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
