"""S9, no credential leak to a third party. A key chat on the fake model, through the relay,
from a throwaway QMX home whose plan home holds a canary login of the real token shape. One
operator turn; the fake model answers with text.

PASS when every request the fake model received authenticates with the fake provider key and
nothing else, and neither the canary nor any grant secret appears in any header or body.

    s09_leak.py
"""

from __future__ import annotations

import asyncio
import sys

from common import (
    CANARY,
    Log,
    Session,
    boot,
    capture_grants,
    chat_args,
    fake_row,
    plant_canary_login,
    put_providers,
    throwaway_home,
    use_fake_home,
    use_fake_key,
)
from fake_model import FAKE_KEY, FakeModel, Turn, text


async def run(log: Log) -> None:
    args = chat_args(__doc__).parse_args()
    from qma.harness import TestMode  # noqa: PLC0415

    root = throwaway_home("hp7-s09")
    plant_canary_login(root)
    fake = FakeModel([Turn([text("hello from the fake model")])]).start()
    put_providers(root, {"fake": fake_row(fake.url)})
    grants = capture_grants()
    session = await Session.start(
        root,
        model="opus",
        workspace=args.workspace,
        title="s09",
        test=TestMode(loopback_http_provider=True),
        profile="fake",
    )
    try:
        record, found = await session.turn(log, "Say hello.")
        log.check("the turn ended", record.turn == "idle", record.turn)
        log.check(
            "the reply arrived through the relay",
            any(b["type"] == "text" and "fake model" in b["content"]["text"] for b in found),
            [b["type"] for b in found],
        )
        posts = [seen for seen in fake.requests if seen.method == "POST"]
        log(f"fake model requests: {[(s.method, s.path, s.query) for s in fake.requests]}")
        auths = {
            (seen.headers.get("authorization"), seen.headers.get("x-api-key")) for seen in posts
        }
        log.check("the fake model got requests", bool(posts), len(posts))
        log.check(
            "every request carried only the fake provider key",
            auths == {(f"Bearer {FAKE_KEY}", None)},
            sorted({"fake key" if a == f"Bearer {FAKE_KEY}" else "other" for a, _ in auths}),
        )
        headers = "\n".join(fake.header_values()).encode()
        everything = headers + fake.bodies()
        log.check("the canary login never reached it", CANARY.encode() not in everything, False)
        log.check("a grant was minted", bool(grants), len(grants))
        leaked = [g for g in grants if g.secret.encode() in everything]
        log.check("no grant secret reached it", not leaked, len(leaked))
        log.check(
            "the relay saw no unknown bearer",
            session.relay.counters.bearer == 0,
            session.relay.counters.bearer,
        )
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp7-s09")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
