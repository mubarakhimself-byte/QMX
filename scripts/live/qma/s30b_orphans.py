"""S30b. Orphans after a crash. `s30b_orphans.py [crash] [orphans]`, both by default.

`crash`: a holder process owns the cap and three plan chats; one chat starts a background Bash
`sleep` grandchild (one model turn on haiku). The holder is killed hard. PASS when every CLI
and the grandchild are gone within 10 s, with the time recorded.

`orphans`: a launcher tree runs outside any cap with its pid file, as after a crash where the
parent job survived. A new cap holder calls `kill_orphans`. PASS when the tree dies and the
returned ids name its chat. No model turn: the CLI waits for input it never gets.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ResultMessage
from common import LAUNCHER, SCRATCH, Log, boot, chat_env, chat_options, home_env, require_login
from qma.harness.procs import AgentProcessCap
from qma.launcher import bundled_cli

TOOLS: dict[str, list[str]] = {"bg": ["Bash"], "idle-1": [], "idle-2": []}
CHATS = tuple(TOOLS)
GONE_WITHIN_S = 10.0
BACKGROUND = (
    "Use the Bash tool with run_in_background set to true to run exactly: sleep 300\n"
    "Then reply with the word started."
)


def options(chat: str, procs_dir: Path, cap: str) -> ClaudeAgentOptions:
    env = chat_env(chat, procs_dir, cap)
    return chat_options(env, SCRATCH / "s30b" / chat, tools=TOOLS[chat])


async def hold(procs: Path, ready: Path) -> None:
    cap = AgentProcessCap.for_platform(procs, None)
    clients: list[ClaudeSDKClient] = []
    for chat in CHATS:
        client = ClaudeSDKClient(options=options(chat, procs, cap.handle_name))
        await client.connect()
        clients.append(client)
    await clients[0].query(BACKGROUND)
    result = "none"
    async for message in clients[0].receive_response():
        if isinstance(message, ResultMessage):
            result = f"is_error={message.is_error} text={str(message.result)[:80]!r}"
    await asyncio.sleep(2)
    tree = [
        {
            "pid": child.pid,
            "ppid": child.ppid(),
            "name": child.name(),
            "created": child.create_time(),
            "tools": tools_flag(child),
        }
        for child in psutil.Process().children(recursive=True)
    ]
    ready.write_text(json.dumps({"result": result, "tree": tree}), encoding="utf-8")
    await asyncio.sleep(3600)


def tools_flag(process: psutil.Process) -> str | None:
    try:
        args = process.cmdline()
    except psutil.Error:
        return None
    return args[args.index("--tools") + 1] if "--tools" in args[:-1] else None


def gone(member: dict[str, object]) -> bool:
    try:
        return psutil.Process(int(str(member["pid"]))).create_time() != member["created"]
    except psutil.NoSuchProcess:
        return True


def crash(log: Log) -> None:
    require_login(log)
    procs = SCRATCH / "s30b" / "procs"
    ready = SCRATCH / "s30b" / "ready.json"
    ready.unlink(missing_ok=True)
    holder = subprocess.Popen([sys.executable, __file__, "--hold", str(procs), str(ready)])
    deadline = time.monotonic() + 240
    while not ready.exists() and holder.poll() is None and time.monotonic() < deadline:
        time.sleep(0.5)
    if not ready.exists():
        log.check("holder came up with three chats", False, f"holder exit {holder.poll()}")
        holder.kill()
        return
    state = json.loads(ready.read_text(encoding="utf-8"))
    tree: list[dict[str, object]] = state["tree"]
    log(f"background turn: {state['result']}")
    for member in tree:
        log(
            f"member pid={member['pid']} parent={member['ppid']} name={member['name']}"
            f" tools={member['tools']!r}"
        )
    clis = [m for m in tree if str(m["name"]).lower().startswith("claude")]
    cli_pids = {m["pid"] for m in clis}
    shells = [m for m in tree if m["ppid"] in cli_pids]
    log.check("three CLIs live", len(clis) == len(CHATS), len(clis))
    given = sorted(str(m["tools"]) for m in clis)
    wanted = sorted(",".join(tools) for tools in TOOLS.values())
    log.check("each CLI runs with only its chat's tools", given == wanted, given)
    log.check(
        "a CLI child (the background Bash) runs", len(shells) >= 1, [m["name"] for m in shells]
    )
    psutil.Process(holder.pid).kill()
    began = time.monotonic()
    while not all(gone(m) for m in tree) and time.monotonic() - began < 30:
        time.sleep(0.05)
    took = time.monotonic() - began
    survivors = [m for m in tree if not gone(m)]
    log(f"every member gone after {took:.2f} s; survivors {survivors}")
    log.check(
        f"every CLI and grandchild gone within {GONE_WITHIN_S:.0f} s",
        not survivors and took <= GONE_WITHIN_S,
        f"{took:.2f} s",
    )
    leftover = AgentProcessCap.for_platform(procs, None)
    try:
        log(f"restart kill_orphans: {leftover.kill_orphans()}")
    finally:
        leftover.close()


def orphans(log: Log) -> None:
    procs = SCRATCH / "s30b" / "orphan-procs"
    cli = bundled_cli()
    if cli is None:
        log.check("bundled CLI found", False, None)
        return
    env = dict(os.environ) | chat_env("orphan", procs, "") | {"QMA_REAL_CLI": cli}
    args = ["-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose"]
    tree = subprocess.Popen([str(LAUNCHER), *args], env=env, stdin=subprocess.PIPE)
    record = procs / "orphan.json"
    deadline = time.monotonic() + 30
    while not record.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    cli_pid = json.loads(record.read_text(encoding="utf-8"))["cli_pid"] if record.exists() else 0
    log(f"orphan tree: launcher pid {tree.pid}, CLI pid {cli_pid}, pid file {record.exists()}")
    cap = AgentProcessCap.for_platform(procs, None)
    try:
        killed = cap.kill_orphans()
        tree.wait(timeout=30)
    finally:
        cap.close()
        if tree.poll() is None:
            tree.kill()
    log.check("kill_orphans names the orphan chat", killed == ("orphan",), killed)
    log.check("the orphan CLI is gone", not psutil.pid_exists(cli_pid), cli_pid)
    log.check("the pid file is gone", not record.exists(), record)


def main() -> int:
    if sys.argv[1:2] == ["--hold"]:
        boot()
        asyncio.run(hold(Path(sys.argv[2]), Path(sys.argv[3])))
        return 0
    steps = sys.argv[1:] or ["crash", "orphans"]
    log = Log("hp4-" + "-".join(["s30b" if step == "crash" else step for step in steps]))
    boot()
    log(f"home {home_env()['CLAUDE_CONFIG_DIR']}")
    for step in steps:
        {"crash": crash, "orphans": orphans}[step](log)
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
