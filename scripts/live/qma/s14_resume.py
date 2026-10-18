"""S14, restart and resume, against `qma.serve` in its own process, killed hard between runs.

    s14_resume.py clean       a turn, kill the host, restart, ask a recall question
    s14_resume.py midturn     kill the host mid-turn; restart; the chat shows the unknown
                              outcome, then the next send resumes the same transcript
    s14_resume.py connect     kill between connect and the first result, once before and once
                              after the CLI wrote the prompt to the JSONL (the timing each
                              attempt landed is logged); then send
    s14_resume.py deleted     delete a started chat's JSONL, then send: refused, no new JSONL
    s14_resume.py old         age a chat's JSONL by 40 days, then ask a recall question
    s14_resume.py all         every case above

Each case passes as DESIGN S14 says. Logs go to hp6-s14-<case>.log.

    s14_resume.py <case> [--home D:/QMX-worktrees/qma-ship/home] [--port 8878] [--model haiku]
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import keyring
from common import Log, boot, chat_args, require_login, use_fake_home

CODEWORD = "PLUM-41"
UNKNOWN = "unknown outcome"
RECALL = "What was the codeword? Reply with the codeword only."


class Host:
    """`python -m qma.serve serve` on its own port, killed hard on `kill`."""

    def __init__(self, home: Path, port: int, log: Log) -> None:
        self.home, self.port, self.log = home, port, log
        self.process: subprocess.Popen[bytes] | None = None
        token = keyring.get_password("qmx/control-token", "control-token")
        self.client = httpx.Client(
            base_url=f"http://127.0.0.1:{port}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=180,
        )

    def start(self) -> None:
        command = [sys.executable, "-m", "qma.serve", "serve", "--home", str(self.home)]
        self.process = subprocess.Popen(
            [*command, "--port", str(self.port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                if self.client.get("/api/health").status_code == 200:
                    self.log(f"host up, pid {self.process.pid}")
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
        raise SystemExit("the host did not come up")

    def kill(self) -> None:
        if self.process is not None:
            self.process.kill()
            self.process.wait(30)
            self.log(f"host pid {self.process.pid} killed")
            self.process = None

    def chat(self, title: str, model: str, workspace: Path) -> str:
        workspace.mkdir(parents=True, exist_ok=True)
        body = {"title": title, "model": model, "workspace": str(workspace)}
        chat = str(self.client.post("/api/chats", json=body).json()["session_id"])
        self.log(f"chat {chat}")
        return chat

    def record(self, chat: str) -> dict[str, Any]:
        return json.loads((self.home / "chats" / f"{chat}.json").read_text(encoding="utf-8"))

    def blocks(self, chat: str) -> list[dict[str, Any]]:
        rows = self.client.get(f"/api/sessions/{chat}/events", params={"limit": 1000}).json()
        return [row["data"]["block"] for row in rows if row["data"].get("type") == "block"]

    def send(self, chat: str, text: str) -> httpx.Response:
        sent = self.client.post(f"/api/sessions/{chat}/turns", json={"text": text})
        self.log(f"send {text!r} -> {sent.status_code} {sent.text[:200]}")
        return sent

    def turn(self, chat: str, text: str) -> str:
        """Send, wait for the turn to end, and return the reply text."""
        before = len(self.blocks(chat))
        if self.send(chat, text).status_code != 202:
            return ""
        deadline = time.monotonic() + 300
        while self.record(chat)["turn"] != "idle" and time.monotonic() < deadline:
            time.sleep(0.5)
        new = self.blocks(chat)[before:]
        reply = " ".join(b["content"]["text"] for b in new if b["type"] == "text")
        self.log(f"reply: {reply[:300]}")
        return reply

    def transcript(self, chat: str) -> Path | None:
        return next((self.home / "claude" / "projects").glob(f"*/{chat}.jsonl"), None)


def remember(host: Host, args: Any, title: str) -> str:
    chat = host.chat(title, args.model, args.workspace)
    host.turn(chat, f"The codeword is {CODEWORD}. Reply with ok.")
    return chat


def clean(host: Host, args: Any) -> None:
    chat = remember(host, args, "s14 clean")
    host.kill()
    host.start()
    reply = host.turn(chat, RECALL)
    host.log.check("recall right after the restart", CODEWORD in reply, reply[:80])


def midturn(host: Host, args: Any) -> None:
    chat = remember(host, args, "s14 midturn")
    host.send(chat, "Write a 1500-word essay on tides. No tools.")
    host.kill()
    record = host.record(chat)
    host.log(f"record at the kill: {record}")
    host.start()
    needs = [b["content"] for b in host.blocks(chat) if b["type"] == "needs_you"]
    shown = any(UNKNOWN in str(content.get("reason")) for content in needs)
    host.log.check("the unknown outcome is shown", shown, needs)
    idle = host.record(chat)["turn"] == "idle"
    host.log.check("the record is idle after open", idle, host.record(chat))
    reply = host.turn(chat, RECALL)
    host.log.check("the next send resumes the same transcript", CODEWORD in reply, reply[:80])


def connect(host: Host, args: Any) -> None:
    for attempt in ("early", "late"):
        chat = host.chat(f"s14 connect {attempt}", args.model, args.workspace)
        host.send(chat, f"The codeword is {CODEWORD}. Reply with ok.")
        if attempt == "late":
            deadline = time.monotonic() + 30
            while host.transcript(chat) is None and time.monotonic() < deadline:
                time.sleep(0.05)
        host.kill()
        jsonl = host.transcript(chat)
        state = "present" if jsonl else "absent"
        host.log(f"{attempt}: killed with the JSONL {state}, record {host.record(chat)}")
        host.start()
        reply = host.turn(chat, "What was the codeword, if I told you one? One line.")
        after = host.transcript(chat)
        if jsonl is None:
            host.log.check(f"{attempt}: no JSONL, so a fresh start", after is not None, after)
        else:
            host.log.check(f"{attempt}: partial JSONL, so it resumed", after == jsonl, after)
        host.log(f"{attempt}: what the CLI answered after the restart: {reply[:160]}")


def deleted(host: Host, args: Any) -> None:
    chat = remember(host, args, "s14 deleted")
    jsonl = host.transcript(chat)
    host.kill()
    if jsonl is not None:
        jsonl.unlink()
    host.start()
    sent = host.send(chat, RECALL)
    last = host.blocks(chat)[-1]
    host.log.check("the send is refused", sent.status_code == 409, sent.status_code)
    host.log.check("an error block names it", "transcript is gone" in json.dumps(last), last)
    host.log.check("no new transcript", host.transcript(chat) is None, host.transcript(chat))


def old(host: Host, args: Any) -> None:
    chat = remember(host, args, "s14 old")
    host.kill()
    jsonl = host.transcript(chat)
    if jsonl is not None:
        aged = time.time() - 40 * 86400
        os.utime(jsonl, (aged, aged))
    host.start()
    reply = host.turn(chat, RECALL)
    host.log.check("a 40-day-old transcript resumes", CODEWORD in reply, reply[:80])


CASES = {"clean": clean, "midturn": midturn, "connect": connect, "deleted": deleted, "old": old}


def main() -> int:
    parser = chat_args(__doc__)
    parser.add_argument("case", choices=[*CASES, "all"])
    parser.add_argument("--port", type=int, default=8878)
    args = parser.parse_args()
    boot()
    use_fake_home()
    failed = 0
    for name in CASES if args.case == "all" else [args.case]:
        log = Log(f"hp6-s14-{name}")
        require_login(log)
        host = Host(args.home, args.port, log)
        host.start()
        try:
            CASES[name](host, args)
        finally:
            host.kill()
        failed |= log.verdict()
    return failed


if __name__ == "__main__":
    sys.exit(main())
