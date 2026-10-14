"""S21e, the relayed home holds no login. A key chat on the fake model with
`TestMode(gate_hook=False, deny_rules=False)` in bypass mode; the fake model scripts one Bash
call that lists `$CLAUDE_CONFIG_DIR` and its `projects`. The plan home of this throwaway QMX
home holds a canary login, so a leak would show.

PASS when the listing is of the relayed home, holds no `.credentials.json`, the folder on disk
holds no login file, and its `projects` resolves to the plan home's.

    s21e_relayed_home.py
"""

from __future__ import annotations

import asyncio
import json
import sys

from common import (
    CANARY,
    Log,
    Session,
    boot,
    chat_args,
    fake_row,
    plant_canary_login,
    put_providers,
    throwaway_home,
    use_fake_home,
    use_fake_key,
)
from fake_model import FakeModel, Turn, text, tool_use

LIST = (
    'echo "home=$CLAUDE_CONFIG_DIR"; ls -a "$CLAUDE_CONFIG_DIR"; echo ---; '
    'ls -a "$CLAUDE_CONFIG_DIR/projects"'
)


def tool_results(body: dict[str, object]) -> str:
    return json.dumps(
        [
            block
            for message in body.get("messages", [])
            for block in (
                message.get("content") if isinstance(message.get("content"), list) else []
            )
            if block.get("type") == "tool_result"
        ]
    )


async def run(log: Log) -> None:
    args = chat_args(__doc__).parse_args()
    from qma.harness import TestMode  # noqa: PLC0415

    root = throwaway_home("hp7-s21e")
    plant_canary_login(root)
    fake = FakeModel(
        [Turn([tool_use("Bash", {"command": LIST, "description": "list"})]), Turn([text("listed")])]
    ).start()
    put_providers(root, {"fake": fake_row(fake.url)})
    session = await Session.start(
        root,
        model="opus",
        workspace=args.workspace,
        title="s21e",
        test=TestMode(gate_hook=False, deny_rules=False, loopback_http_provider=True),
        profile="fake",
        mode="bypassPermissions",
    )
    try:
        await session.turn(log, "List the Claude home.")
        listing = next(
            (
                tool_results(seen.json)
                for seen in fake.requests
                if "tool_result" in seen.body.decode("utf-8", "replace")
            ),
            "",
        )
        log(f"tool result: {listing[:600]}")
        relayed = session.home.relayed_dir
        log.check("the Bash call ran", "home=" in listing, bool(listing))
        log.check(
            "it listed the relayed home",
            "claude-relayed" in listing.replace("\\\\", "/"),
            "claude-relayed" in listing,
        )
        log.check("the listing holds no login file", ".credentials.json" not in listing, False)
        on_disk = sorted(path.name for path in relayed.iterdir())
        log.check("no login file on disk", ".credentials.json" not in on_disk, on_disk)
        target = (relayed / "projects").resolve()
        log.check(
            "projects resolves to the plan home's",
            target == (session.home.plan_dir / "projects").resolve(),
            target,
        )
        log.check("the canary never left", CANARY.encode() not in fake.bodies(), False)
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp7-s21e")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
