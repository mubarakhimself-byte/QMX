"""S30. The OS memory cap through the launcher: three plan chats, one runs a memory-heavy Bash
command, and only that chat's tree dies. Three model turns on haiku.

PASS on Windows and Linux with user systemd: `report().last_killed` names the heavy chat, its
CLI is gone, and the other two chats still answer. Where the platform has no OS cap
(`os_cap` False), PASS needs the chats to run anyway; the heavy step is skipped.
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

from claude_agent_sdk import ClaudeSDKClient, ResultMessage
from common import SCRATCH, Log, boot, chat_env, chat_options, require_login
from qma.harness.procs import AgentProcessCap

CHATS = ("calm-1", "heavy", "calm-2")
HEADROOM_MB = 600
ALLOCATE = "b = [bytearray(64 * 2**20) for _ in range(96)]; print(len(b))"
ASK_BASH = "Use the Bash tool once to run this exact command, then reply with its output:\n"


async def ask(client: ClaudeSDKClient, prompt: str, log: Log, chat: str) -> bool:
    ok = False
    try:
        await client.query(prompt)
        async for message in client.receive_response():
            if isinstance(message, ResultMessage):
                ok = not message.is_error
                log(
                    f"{chat}: result is_error={message.is_error} text={str(message.result)[:120]!r}"
                )
    except Exception as error:
        log(f"{chat}: turn ended by {type(error).__name__}: {str(error)[:200]}")
    return ok


async def run(log: Log, cap: AgentProcessCap) -> None:
    clients: dict[str, ClaudeSDKClient] = {}
    for chat in CHATS:
        env = chat_env(chat, cap.procs_dir, cap.handle_name)
        clients[chat] = ClaudeSDKClient(options=chat_options(env, SCRATCH / "s30" / chat))
        await clients[chat].connect()
    try:
        report = cap.report()
        log(f"after connect: {report}")
        log.check(
            "all three chats live under the cap", report.chats == tuple(sorted(CHATS)), report.chats
        )
        if not report.os_cap:
            for chat in ("calm-1", "calm-2"):
                log.check(
                    f"{chat} answers without an OS cap",
                    await ask(clients[chat], "Reply with the word ok.", log, chat),
                    chat,
                )
            return
        limit = (report.used_mb or 0) + HEADROOM_MB
        cap.set_limit(limit)
        log(f"limit set to {limit} MB, commit in use {report.used_mb} MB")
        python = Path(sys.executable).as_posix()
        command = f'"{python}" -c "{ALLOCATE}"'
        prompt = ASK_BASH + command
        log(f"heavy command: {command}")
        began = time.monotonic()
        await ask(clients["heavy"], prompt, log, "heavy")
        deadline = time.monotonic() + 30
        while cap.alive("heavy") and time.monotonic() < deadline:
            await asyncio.sleep(0.2)
        report = cap.report()
        log(f"after the heavy turn ({time.monotonic() - began:.1f} s): {report}")
        log.check("heavy chat's CLI is gone", not cap.alive("heavy"), report.chats)
        log.check(
            "last_killed names the heavy chat", report.last_killed == "heavy", report.last_killed
        )
        for chat in ("calm-1", "calm-2"):
            log.check(
                f"{chat} still answers",
                await ask(clients[chat], "Reply with the word ok.", log, chat),
                chat,
            )
    finally:
        for client in clients.values():
            try:
                await client.disconnect()
            except Exception as error:
                log(f"disconnect: {type(error).__name__}")


def main() -> int:
    log = Log("hp4-s30")
    removed = boot()
    log(f"scrubbed {len(removed)} inherited names")
    require_login(log)
    procs = SCRATCH / "s30" / "procs"
    cap = AgentProcessCap.for_platform(procs, None)
    log(f"cap {cap.handle_name!r} os_cap={cap.report().os_cap} orphans killed {cap.kill_orphans()}")
    try:
        asyncio.run(run(log, cap))
    finally:
        cap.close()
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
