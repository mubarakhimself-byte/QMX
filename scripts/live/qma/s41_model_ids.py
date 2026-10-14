"""S41, one model-id parser, relay half. A harness on a throwaway QMX home with a Kimi row
pointed at the fake model. `start_chat` and the relay, under one Kimi grant, are each asked for
an id outside the Kimi tier set, for `kimi-k3[1m]` and for a tier alias.

PASS when the outside id is refused by both (start_chat refuses, the relay answers 400) and
`kimi-k3[1m]` and `opus` pass both.

    s41_model_ids.py
"""

from __future__ import annotations

import asyncio
import sys

import httpx
from common import Log, boot, put_providers, throwaway_home, use_fake_home, use_fake_key
from fake_model import FAKE_REF, FakeModel

IDS = (
    ("kimi-k2.7-code", False),
    ("kimi-k3[1m]", True),
    ("opus", True),
    ("KIMI-K3", True),
    ("k\u0456mi-k3", False),
)


async def run(log: Log) -> None:
    from qma.harness import Harness, LaunchRefused, NewChat, QmxHome, TestMode  # noqa: PLC0415
    from qma.harness.profiles import ProfileName  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    root = throwaway_home("hp7-s41")
    fake = FakeModel([], every_request=True).start()
    tiers = {"opus": "kimi-k3", "sonnet": "kimi-k3", "haiku": "kimi-k2.6", "fable": "kimi-k3"}
    put_providers(
        root, {"kimi": {"base_url": fake.url, "credential_ref": FAKE_REF, "tiers": tiers}}
    )
    home = QmxHome(root)
    harness = await Harness.open(
        home, control=control_service(home), test=TestMode(loopback_http_provider=True)
    )
    relay = harness._deps.relay
    try:
        grant = await relay.grant("0b9c2f4e-1d3a-4c5b-8e7f-6a5b4c3d2e1f", ProfileName("kimi"))
        async with httpx.AsyncClient(base_url=relay.base_url, trust_env=False) as client:
            for model, allowed in IDS:
                try:
                    await harness.start_chat(NewChat(title="s41", model=model, profile="kimi"))
                    started = "started"
                except LaunchRefused as refused:
                    started = f"refused: {refused}"
                answer = await client.post(
                    "/v1/messages?beta=true",
                    json={"model": model, "max_tokens": 8, "messages": [], "stream": True},
                    headers={"authorization": f"Bearer {grant.secret}"},
                )
                sent = fake.requests[-1].json.get("model") if fake.requests else None
                log(f"{model}: start_chat {started}; relay {answer.status_code}; sent {sent}")
                expected = ("started", 200) if allowed else ("refused", 400)
                log.check(
                    f"{model} is {'accepted' if allowed else 'refused'} by both",
                    (started.split(":")[0], answer.status_code) == expected,
                    (started, answer.status_code),
                )
                if allowed:
                    log.check(f"{model} reaches the provider as kimi-k3", sent == "kimi-k3", sent)
    finally:
        await harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp7-s41")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
