"""C-36 lanes 2 to 6: cTrader's Remote MCP in a real chat on `haiku`, on demo accounts only.

Usage, from `<worktree>/qmx-agents` with the agents venv:
`timeout 1800 uv run --no-sync python D:/QMX-worktrees/unit-ship/evidence/c36/owner_lane.py <lane>
<worktree>` where <lane> is copilot, live, engine, swap or noleak.

Every lane runs the harness in this process on the ship home's plan login under
`D:/QMX-worktrees/.engine-lane-lock`, as the engine's live checks do. The keyring is in memory in
this process, so no Credential Manager entry is read or written; qmx/ctrader-mcp holds a fixture
bearer. The server is `tools/lanes/fake_ctrader_mcp.py` on the loopback, which places nothing.
The ship home's settings.toml gets the enabled ctrader row for the lane and its exact text back
after. Account records come from a reader over two fixture rows (41500001 demo, 41500002 live);
the reader over the Library's main is proven by `test_mcp_credential.py`. Prints one PASS or FAIL
line per check, exits 1 on any FAIL, and writes `<evidence>/<prefix>c36-<lane>.log`, where the
prefix is `owner-` unless C36_LOG_PREFIX says otherwise.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any, Final

import keyring
from keyring.backend import KeyringBackend

SHIP_HOME: Final = Path("D:/QMX-worktrees/qma-ship/home")
LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
EVIDENCE: Final = Path("D:/QMX-worktrees/unit-ship/evidence/c36")
SCRATCH: Final = Path("D:/Temp/c36-lanes")
DEMO: Final = "lane-demo-41500001"
LIVE: Final = "lane-live-41500002"
BOUND: Final = {DEMO: 41500001, LIVE: 41500002}
RECORDS: Final = {"41500001": ["demo"], "41500002": ["live"]}
ASK: Final = (
    "Call the mcp__ctrader__get_trendbars tool with symbolId 1, period H_1 and count 1. "
    "Then answer with the bar's volume number and nothing else."
)
LIVE_NOTE: Final = (
    "the MCP server ctrader was refused: account 41500002 is recorded as live, and agents use "
    "demo accounts only"
)
TOOL: Final = "mcp__ctrader__get_trendbars"
VOLUME: Final = "3412"
TURN_S: Final = 300.0


class Memory(KeyringBackend):
    priority = 1  # pyright: ignore[reportAssignmentType, reportIncompatibleMethodOverride]

    def __init__(self) -> None:
        super().__init__()
        self.held: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.held.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.held[service, username] = password

    def delete_password(self, service: str, username: str) -> None:
        self.held.pop((service, username), None)


class Log:
    def __init__(self, lane: str) -> None:
        prefix = os.environ.get("C36_LOG_PREFIX", "owner-")
        self.path = EVIDENCE / f"{prefix}c36-{lane}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped.encode("ascii", "backslashreplace").decode(), flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(stamped + "\n")

    def check(self, name: str, ok: bool, seen: object) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        self.passed &= ok


@contextmanager
def lane_lock(log: Log) -> Iterator[None]:
    deadline = time.monotonic() + 3600
    while True:
        try:
            LOCK.mkdir()
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise SystemExit("BLOCKED: the lane lock stayed held for an hour") from None
            log("lane lock held by another lane; retry in 20 s")
            time.sleep(20)
    log("lane lock taken")
    try:
        yield
    finally:
        LOCK.rmdir()
        log("lane lock released")


@contextmanager
def fake_server(worktree: Path, log: Log) -> Iterator[str]:
    """The fixture server's url, stopped by its own PID."""
    folder = SCRATCH / "fake"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "accounts.json").write_text(json.dumps(BOUND), encoding="utf-8")
    port = folder / "port"
    port.unlink(missing_ok=True)
    script = worktree / "tools/lanes/fake_ctrader_mcp.py"
    args = ["--accounts", str(folder / "accounts.json"), "--port-file", str(port)]
    server = subprocess.Popen([sys.executable, str(script), *args])
    log(f"fake cTrader MCP started, pid {server.pid}")
    try:
        deadline = time.monotonic() + 60
        while not (port.exists() and port.read_text(encoding="utf-8")):
            if server.poll() is not None or time.monotonic() > deadline:
                raise SystemExit("FAIL the fake cTrader MCP did not start")
            time.sleep(0.05)
        yield f"http://127.0.0.1:{port.read_text(encoding='utf-8')}/mcp"
    finally:
        server.terminate()
        server.wait(timeout=30)
        log(f"fake cTrader MCP stopped, pid {server.pid}")


@asynccontextmanager
async def ship_harness(url: str, log: Log) -> AsyncIterator[Any]:
    """The harness on the ship home with the ctrader row on; settings.toml's text is put back."""
    from qma.harness import Harness, QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    settings = SHIP_HOME / "settings.toml"
    before = settings.read_text(encoding="utf-8") if settings.exists() else None
    home = QmxHome(SHIP_HOME)
    control = control_service(home)
    control.settings_put("mcp_servers", {"ctrader": {"url": url, "enabled": True}})
    harness = await Harness.open(
        home, control=control, accounts=lambda account: RECORDS.get(account, [])
    )
    try:
        yield harness
    finally:
        await harness.close()
        if before is None:
            settings.unlink(missing_ok=True)
        else:
            settings.write_text(before, encoding="utf-8")
        log("ship home settings.toml put back")


def blocks(harness: Any, chat: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    after = 0
    while True:
        page = harness.control.events("sessions", after, chat, 1000)
        found += [e["data"]["block"] for e in page if e["data"].get("type") == "block"]
        if len(page) < 1000:
            return found
        after = page[-1]["id"]


async def turn(harness: Any, chat: str, text: str, *, injected: bool = False) -> None:
    """Sends `text` and allows each ask for a ctrader tool once, as he would, until idle."""
    from qma.harness import AllowOnce, AskId, InjectedText, OperatorText  # noqa: PLC0415
    from qma.harness.home import read_record, session_id  # noqa: PLC0415

    await harness.send(chat, InjectedText(text) if injected else OperatorText(text))
    answered: set[int] = set()
    deadline = time.monotonic() + TURN_S
    while time.monotonic() < deadline:
        for event in harness.control.events("sessions", 0, chat, 1000):
            block = event["data"].get("block") or {}
            content = block.get("content") or {}
            seq = block.get("seq")
            asking = block.get("type") == "permission" and content.get("state") == "asking"
            if asking and str(content.get("tool", "")).startswith("mcp__ctrader__"):
                if isinstance(seq, int) and seq not in answered:
                    answered.add(seq)
                    harness.answer(AskId(session_id(chat), seq), AllowOnce())
        record = read_record(harness._deps.home, session_id(chat))  # noqa: SLF001
        if record is not None and record.turn == "idle":
            return
        await asyncio.sleep(0.5)


def called(found: list[dict[str, Any]]) -> list[str]:
    return [str(b["content"]["name"]) for b in found if b.get("type") == "tool" and "name" in b["content"]]


def text_of(found: list[dict[str, Any]]) -> str:
    return " ".join(str(b["content"].get("text", "")) for b in found if b.get("type") == "text")


def notes(found: list[dict[str, Any]]) -> list[str]:
    return [str(b["content"].get("reason")) for b in found if b.get("type") == "needs_you"]


async def copilot(harness: Any, log: Log, vault: Memory, url: str) -> None:
    from qma.harness import NewChat  # noqa: PLC0415
    from qma.harness.tools import VetCache, vet_mcp_servers  # noqa: PLC0415

    row = {"url": url, "credential_ref": "qmx/ctrader-mcp"}
    started = time.monotonic()
    await vet_mcp_servers({"ctrader": row}, VetCache(), accounts=RECORDS.get)
    plain = time.monotonic() - started
    started = time.monotonic()
    await vet_mcp_servers({"ctrader": {**row, "venue": "ctrader"}}, VetCache(), accounts=RECORDS.get)
    checked = time.monotonic() - started
    log(f"perf: vetting {plain:.3f} s without the demo check, {checked:.3f} s with it")
    chat = await harness.start_chat(NewChat(title="c36 copilot", model="haiku"))
    await turn(harness, str(chat), ASK)
    found = blocks(harness, str(chat))
    log.check("the chat called the cTrader trendbars tool", TOOL in called(found), called(found))
    log.check("the chat answered from it", VOLUME in text_of(found).replace(",", ""), text_of(found))
    log.check("no note left the server out", notes(found) == [], notes(found))


async def live(harness: Any, log: Log, vault: Memory, url: str) -> None:
    from qma.harness import NewChat  # noqa: PLC0415

    vault.set_password("qmx/ctrader-mcp", "ctrader-mcp", LIVE)
    chat = await harness.start_chat(NewChat(title="c36 live", model="haiku"))
    await turn(harness, str(chat), ASK)
    found = blocks(harness, str(chat))
    log.check("the chat started without the server", TOOL not in called(found), called(found))
    log.check("the note says demo only", LIVE_NOTE in notes(found), notes(found))


async def engine(harness: Any, log: Log, vault: Memory, url: str) -> None:
    from qmx_engine.ports.harness_adapter import HarnessAdapter  # noqa: PLC0415

    adapter = HarnessAdapter(harness)
    workspace = SCRATCH / "step"
    chat = await adapter.start_chat(
        title="c36-run:read-bars",
        profile="claude",
        model="haiku",
        effort=None,
        workspace=workspace,
        toolsets=("mcp:ctrader",),
    )
    await turn(harness, chat, ASK, injected=True)
    found = blocks(harness, chat)
    refusals = [
        str(b["content"].get("result"))
        for b in found
        if b.get("type") == "tool" and b["content"].get("state") == "error"
    ]
    log.check("the step called the cTrader trendbars tool", TOOL in called(found), called(found))
    log.check("no guard or policy refused it", refusals == [], refusals)
    log.check("the step answered from it", VOLUME in text_of(found).replace(",", ""), text_of(found))


async def swap(harness: Any, log: Log, vault: Memory, url: str) -> None:
    from qma.harness import NewChat  # noqa: PLC0415

    first = await harness.start_chat(NewChat(title="c36 swap 1", model="haiku"))
    await turn(harness, str(first), "Reply with the word OK.")
    log.check("the first chat had the server", notes(blocks(harness, str(first))) == [], "")
    vault.set_password("qmx/ctrader-mcp", "ctrader-mcp", LIVE)
    second = await harness.start_chat(NewChat(title="c36 swap 2", model="haiku"))
    await turn(harness, str(second), "Reply with the word OK.")
    found = notes(blocks(harness, str(second)))
    log.check("the second chat, on the swapped token, was refused", LIVE_NOTE in found, found)


async def noleak(harness: Any, log: Log, vault: Memory, url: str) -> None:
    await copilot(harness, log, vault, url)
    vault.set_password("qmx/ctrader-mcp", "ctrader-mcp", LIVE)
    await live(harness, log, vault, url)


LANES: Final = {"copilot": copilot, "live": live, "engine": engine, "swap": swap, "noleak": noleak}


def leaks(since: float) -> list[str]:
    """Files written since the lane started, under the ship home, the scratch folder and this
    PR's evidence, that hold either fixture bearer."""
    roots = [SHIP_HOME, SCRATCH, EVIDENCE]
    found: list[str] = []
    for root in roots:
        for path in root.rglob("*"):
            try:
                if path.is_file() and path.stat().st_mtime >= since and path.suffix != ".py":
                    body = path.read_bytes()
                    if DEMO.encode() in body or LIVE.encode() in body:
                        found.append(str(path))
            except OSError:
                continue
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lane", choices=sorted(LANES))
    parser.add_argument("worktree", type=Path)
    args = parser.parse_args()
    log = Log(args.lane)
    from qma.boot import scrub_process_env  # noqa: PLC0415

    scrub_process_env(os.environ)
    shutil.rmtree(SCRATCH, ignore_errors=True)
    for name in ("HOME", "USERPROFILE"):
        os.environ[name] = str(SCRATCH / "profile")
    os.environ["APPDATA"] = str(SCRATCH / "profile/AppData/Roaming")
    os.environ["LOCALAPPDATA"] = str(SCRATCH / "profile/AppData/Local")
    for name in ("HOME", "APPDATA", "LOCALAPPDATA"):
        Path(os.environ[name]).mkdir(parents=True, exist_ok=True)
    login = (SHIP_HOME / "claude" / ".credentials.json").exists()
    log(f"ship home plan login present: {login}")
    if not login:
        log("BLOCKED: the ship home has no plan login")
        return 3
    vault = Memory()
    keyring.set_keyring(vault)
    vault.set_password("qmx/ctrader-mcp", "ctrader-mcp", DEMO)
    since = time.time()

    async def run(url: str) -> None:
        async with ship_harness(url, log) as harness:
            await LANES[args.lane](harness, log, vault, url)

    with lane_lock(log), fake_server(args.worktree.resolve(), log) as url:
        asyncio.run(run(url))
    if args.lane == "noleak":
        found = leaks(since)
        log.check("no file written in the lane holds a bearer value", found == [], found)
    shutil.rmtree(SCRATCH, ignore_errors=True)
    log.check("throwaway folder removed", not SCRATCH.exists(), SCRATCH)
    log("PASS" if log.passed else "FAIL")
    return 0 if log.passed else 1


if __name__ == "__main__":
    sys.exit(main())
