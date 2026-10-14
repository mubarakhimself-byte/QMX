"""S23, no provider key in any CLI env. A key chat on the fake model in bypass mode; the fake
model scripts a Bash `env` and `set`. The fake provider key stands in for a real key, so the
check spends nothing.

PASS when the only routing names in the listing are the relay URL, the grant secret and the
four pinned tiers, the base URL is the relay's, the token is this chat's grant secret, and the
key value is in neither the listing, the transcript nor any file of the QMX home.

    s23_no_key_env.py
"""

from __future__ import annotations

import asyncio
import re
import sys

from common import (
    Log,
    Session,
    boot,
    capture_grants,
    chat_args,
    fake_row,
    files_holding,
    put_providers,
    throwaway_home,
    use_fake_home,
    use_fake_key,
)
from fake_model import FAKE_KEY, FakeModel, Turn, text, tool_use

ROUTING = re.compile(r"^(ANTHROPIC_\w+|CLAUDE_CODE_OAUTH_TOKEN|\w*API_KEY\w*)=(.*)$", re.M)
ALLOWED = {
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_FABLE_MODEL",
}


async def run(log: Log) -> None:
    args = chat_args(__doc__).parse_args()
    from qma.harness import TestMode  # noqa: PLC0415

    root = throwaway_home("hp7-s23")
    fake = FakeModel(
        [
            Turn([tool_use("Bash", {"command": "env; echo ---; set", "description": "env"})]),
            Turn([text("listed")]),
        ]
    ).start()
    put_providers(root, {"fake": fake_row(fake.url)})
    grants = capture_grants()
    session = await Session.start(
        root,
        model="opus",
        workspace=args.workspace,
        title="s23",
        test=TestMode(loopback_http_provider=True),
        profile="fake",
        mode="bypassPermissions",
        tools=["Bash"],
    )
    try:
        _, found = await session.turn(log, "Show the environment.")
        listing = next(
            (
                str(b["content"].get("result", ""))
                for b in found
                if b["type"] == "tool" and b["content"].get("state") == "finished"
            ),
            "",
        )
        pairs = {name: value.strip().strip("'\"") for name, value in ROUTING.findall(listing)}
        log(f"routing names in the listing: {sorted(pairs)}")
        log.check("the Bash call ran", "PATH=" in listing, len(listing))
        log.check("only relay names appear", set(pairs) <= ALLOWED, sorted(set(pairs) - ALLOWED))
        grant = grants[-1] if grants else None
        log.check(
            "the base URL is the relay",
            grant is not None and pairs.get("ANTHROPIC_BASE_URL") == grant.base_url,
            pairs.get("ANTHROPIC_BASE_URL"),
        )
        log.check(
            "the token is this chat's grant secret",
            grant is not None and pairs.get("ANTHROPIC_AUTH_TOKEN") == grant.secret,
            "grant secret"
            if grant and pairs.get("ANTHROPIC_AUTH_TOKEN") == grant.secret
            else "other",
        )
        log.check("no key value in the listing", FAKE_KEY not in listing, False)
        log.check("no key value in the transcript", FAKE_KEY not in session.transcript(), False)
        holders = files_holding([root], FAKE_KEY)
        log.check("no key value in the QMX home", not holders, [str(p) for p in holders])
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp7-s23")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
