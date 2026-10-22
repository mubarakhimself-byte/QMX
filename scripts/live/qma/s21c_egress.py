"""S21c, the relay egress stop alone. A key chat on the fake model with
`TestMode(gate_hook=False, deny_rules=False, redaction=False)` in bypass mode.

Negative case first: the fake model reads copies of `relay.py` and `project.py` and an
`.env.example` holding `ANTHROPIC_API_KEY=sk-ant-...`, then answers two more turns. Then it
prints a fake token of the real shape (no real login involved) and the operator sends one more
message. Then the chat is rewound to before the token turn, forked with `resume_session_at`
through a fresh relay grant, and sent a message.

PASS when the negative case keeps working with no egress count; the message after the token
gets 400, the egress counter moves, the chat shows `needs_you` and the fake model never
receives the token; and after the rewind the chat works again with no new egress count.

    s21c_egress.py
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from common import (
    Log,
    Session,
    boot,
    chat_args,
    fake_row,
    put_providers,
    session_blocks,
    throwaway_home,
    use_fake_home,
    use_fake_key,
)
from fake_model import FakeModel, Turn, text, tool_use

FAKE = "sk-ant-oat01-QMXCANARY" + "Zq7Xw2Lp9V" * 4
PACKAGES = Path(__file__).resolve().parents[3] / "qmx-agents/packages"
HARNESS = PACKAGES / "qma-harness/src/qma/harness"
ROUTER = PACKAGES / "qmx-router/src/qmx_router"
TOKEN_PROMPT = "Print the test string now."  # noqa: S105
TOOLS = ["Read"]


def read(path: Path) -> Turn:
    return Turn([tool_use("Read", {"file_path": str(path)})])


def fork_point(transcript: str) -> str | None:
    """The last entry before the token turn's prompt. The rewind drops that turn and the
    refused one after it."""
    entries: list[dict[str, Any]] = [json.loads(line) for line in transcript.splitlines() if line]
    last: str | None = None
    for entry in entries:
        content = json.dumps(entry.get("message", {}).get("content", ""))
        if entry.get("type") == "user" and TOKEN_PROMPT in content:
            return last
        last = entry.get("uuid") or last
    return None


async def rewound_turn(session: Session, workspace: Path, at: str) -> Any:
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ResultMessage  # noqa: PLC0415
    from qma.harness.launch import RelayedLaunch, launch_env  # noqa: PLC0415
    from qmx_router.profiles import ProfileName  # noqa: PLC0415

    grant = await session.relay.grant(session.chat, ProfileName("fake"))
    env = launch_env(RelayedLaunch(grant), home=session.home, session_id=session.chat, cap="none")
    options = ClaudeAgentOptions(
        env={k: v for k, v in env.items() if not k.startswith("QMA_")},
        setting_sources=[],
        permission_mode="bypassPermissions",
        tools=TOOLS,
        model="opus",
        cwd=str(workspace),
        resume=session.chat,
        fork_session=True,
        resume_session_at=at,
        max_turns=2,
    )
    async with ClaudeSDKClient(options) as client:
        await client.query("After the rewind: say something.")
        async for message in client.receive_response():
            if isinstance(message, ResultMessage):
                await session.relay.revoke(grant)
                return message
    return None


async def run(log: Log) -> None:
    args = chat_args(__doc__).parse_args()
    from qma.harness import TestMode  # noqa: PLC0415

    root = throwaway_home("hp7-s21c")
    workspace = args.workspace / "s21c"
    shutil.rmtree(workspace, ignore_errors=True)
    workspace.mkdir(parents=True)
    for source, name in ((ROUTER, "relay.py"), (HARNESS, "project.py")):
        shutil.copyfile(source / name, workspace / name)
    (workspace / ".env.example").write_text("ANTHROPIC_API_KEY=sk-ant-...\n", encoding="utf-8")
    fake = FakeModel(
        [
            read(workspace / "relay.py"),
            read(workspace / "project.py"),
            read(workspace / ".env.example"),
            Turn([text("read all three")]),
            Turn([text("turn two ok")]),
            Turn([text("turn three ok")]),
            Turn([text(f"This is a fake test string: {FAKE}")]),
            Turn([text("should never be asked")]),
            Turn([text("works again")]),
        ]
    ).start()
    put_providers(root, {"fake": fake_row(fake.url)})
    session = await Session.start(
        root,
        model="opus",
        workspace=workspace,
        title="s21c",
        test=TestMode(
            gate_hook=False, deny_rules=False, redaction=False, loopback_http_provider=True
        ),
        profile="fake",
        mode="bypassPermissions",
        tools=TOOLS,
    )
    relay = session.relay
    try:
        _, first = await session.turn(log, "Read relay.py, project.py and .env.example.")
        _, second = await session.turn(log, "Turn two.")
        _, third = await session.turn(log, "Turn three.")
        reads = [
            b for b in first if b["type"] == "tool" and b["content"].get("state") == "finished"
        ]
        log.check("the three reads ran", len(reads) == 3, len(reads))
        replies = [b["content"]["text"] for b in [*first, *second, *third] if b["type"] == "text"]
        log.check(
            "the negative case kept working",
            replies == ["read all three", "turn two ok", "turn three ok"],
            replies,
        )
        log.check("no egress count yet", relay.counters.egress == 0, relay.counters.egress)
        await session.turn(log, TOKEN_PROMPT)
        _, after = await session.turn(log, "Continue.")
        log.check("the egress counter moved", relay.counters.egress >= 1, relay.counters.egress)
        stopped = [
            b
            for b in session_blocks(session.control, session.chat)
            if b["type"] == "needs_you" and b["content"]["reason"].startswith("egress stop")
        ]
        log.check("the chat shows needs_you", bool(stopped), len(stopped))
        log.check(
            "the fake model never received the token",
            b"QMXCANARY" not in fake.bodies(),
            False,
        )
        log(f"after the token: {[b['type'] for b in after]}")
        await session.harness._chat(session.chat).close()
        at = fork_point(session.transcript())
        log(f"fork point found: {at is not None}")
        egress = relay.counters.egress
        result = await rewound_turn(session, workspace, at or "")
        log.check(
            "after the rewind the chat works again",
            result is not None and not result.is_error,
            result and (result.subtype, result.is_error),
        )
        log.check("no new egress count", relay.counters.egress == egress, relay.counters.egress)
        log.check(
            "the fake model still never received the token",
            b"QMXCANARY" not in fake.bodies(),
            False,
        )
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp7-s21c")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
