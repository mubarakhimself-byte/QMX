"""S7, isolation both ways, and the planted-plugin part of S6. The harness runs in this process.

1. The throwaway HOME gets a marker of every kind in its `~/.claude`: a skill, an agent, a
   command, a settings hook, an MCP server in `~/.claude.json`, a CLAUDE.md phrase and an
   auto-memory file. A plan chat connects; with `--turn` it is also asked to repeat any
   instruction holding the marker. PASS when no marker reaches the server info, the MCP status
   or the reply, and the throwaway `~/.claude` and `~/.claude.json` are byte-identical after.
2. A plugin is installed with `claude plugin install` into the plan home and the relayed home
   of `--home` (snapshot first, restored on exit, under the HP0 plant lock). A chat connects.
   PASS when the plugin never reaches the first prompt: the post-connect check closes the chat,
   or the CLI never loaded it (which one is logged; HP0 OQ5 saw the second).

    s07_isolation.py [--home D:/QMX-worktrees/qma-ship/home] [--turn] [--model haiku]
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from common import FAKE_HOME, SCRATCH, Log, Session, boot, chat_args, require_login, use_fake_home
from plants import exclusive, restore, snapshot

MARK = "QMXMARK"
MARKET = "qmx-s07-market"
PLUGIN = "qmx-s07-plant"
PLANT_LOCK = Path("D:/Temp/qma-hp0/settings-plant.lock")
"""The plant lock, so two planting runs never overlap."""
BACKUP = SCRATCH / "s07-plant-backup.json"


def plant_markers() -> None:
    claude = FAKE_HOME / ".claude"
    files = {
        claude / "skills" / "qmxmark-skill" / "SKILL.md": (
            f"---\nname: qmxmark-skill\ndescription: {MARK} skill.\n---\nSay {MARK}.\n"
        ),
        claude / "agents" / "qmxmark-agent.md": (
            f"---\nname: qmxmark-agent\ndescription: {MARK} agent.\n---\nSay {MARK}.\n"
        ),
        claude / "commands" / "qmxmark-cmd.md": f"Say {MARK} command.\n",
        claude / "CLAUDE.md": f"Always mention the phrase {MARK}-PHRASE in every reply.\n",
        claude / "projects" / "marker" / "memory" / "MEMORY.md": f"- {MARK} memory\n",
        claude / "settings.json": json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": f"echo {MARK} > {SCRATCH}/s07-hook.txt",
                                }
                            ]
                        }
                    ]
                }
            }
        ),
        FAKE_HOME / ".claude.json": json.dumps(
            {"mcpServers": {"qmxmark-mcp": {"command": "python", "args": ["-c", "pass"]}}}
        ),
    }
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def fingerprint() -> dict[str, str]:
    paths = [p for p in (FAKE_HOME / ".claude").rglob("*") if p.is_file()]
    paths.append(FAKE_HOME / ".claude.json")
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.exists()}


async def connect_only(session: Session) -> tuple[str, str]:
    """Connect the chat without a prompt; the server info and MCP status, or the refusal."""
    from qma.harness import LaunchRefused  # noqa: PLC0415

    chat = session.harness._chat(session.chat)
    try:
        live = await chat._connect()
    except LaunchRefused as refused:
        return "refused", str(refused)
    info = json.dumps(await live.client.get_server_info())
    status = json.dumps(await live.client.get_mcp_status())
    chat._live = live
    await chat.close()
    return "connected", info + status


def plugin_cli(home: Path, log: Log, *args: str) -> None:
    from qma.launcher import bundled_cli  # noqa: PLC0415

    done = subprocess.run(
        [str(bundled_cli()), "plugin", *args],
        env={**os.environ, "CLAUDE_CONFIG_DIR": str(home)},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    log(f"claude plugin {' '.join(args)} in {home}: exit {done.returncode}")


def plant_plugin(homes: list[Path], log: Log) -> None:
    market = SCRATCH / "s07-market"
    shutil.rmtree(market, ignore_errors=True)
    (market / ".claude-plugin").mkdir(parents=True)
    manifest = {
        "name": MARKET,
        "owner": {"name": "s07"},
        "plugins": [{"name": PLUGIN, "source": f"./{PLUGIN}"}],
    }
    (market / ".claude-plugin" / "marketplace.json").write_text(json.dumps(manifest))
    root = market / PLUGIN
    (root / ".claude-plugin").mkdir(parents=True)
    (root / "commands").mkdir()
    plugin = {"name": PLUGIN, "version": "0.0.1", "description": f"{MARK} planted plugin."}
    (root / ".claude-plugin" / "plugin.json").write_text(json.dumps(plugin))
    (root / "commands" / "planted.md").write_text(f"Say {MARK} plugin.\n")
    files = [
        h / name
        for h in homes
        for name in (
            "settings.json",
            "plugins/installed_plugins.json",
            "plugins/known_marketplaces.json",
        )
    ]
    folders = [h / "plugins" / kind / MARKET for h in homes for kind in ("cache", "marketplaces")]
    snapshot(BACKUP, homes[0].parent, files, folders)
    for home in homes:
        plugin_cli(home, log, "marketplace", "add", market.as_posix())
        plugin_cli(home, log, "install", f"{PLUGIN}@{MARKET}")


async def run(log: Log) -> None:
    parser = chat_args(__doc__)
    parser.add_argument("--turn", action="store_true")
    args = parser.parse_args()
    shutil.rmtree(FAKE_HOME / ".claude", ignore_errors=True)
    plant_markers()
    before = fingerprint()
    session = await Session.start(
        args.home, model=args.model, workspace=args.workspace, title="s07"
    )
    try:
        outcome, seen = await connect_only(session)
        log.check(
            "the marked home loads nothing into the chat",
            outcome == "connected" and MARK.lower() not in seen.lower(),
            outcome if outcome == "refused" else "no marker",
        )
        if args.turn:
            _, reply = await session.turn(
                log,
                f"Quote any instruction or memory line holding {MARK}, else say none.",
            )
            text = json.dumps([b["content"] for b in reply if b["type"] == "text"])
            leaked = [m for m in (f"{MARK}-PHRASE", f"{MARK} memory", f"{MARK} skill") if m in text]
            log.check("no marker reaches the model", leaked == [], text[:200])
        hook = (SCRATCH / "s07-hook.txt").exists()
        log.check("the home settings hook never ran", not hook, hook)
    finally:
        await session.harness.close()
    log.check("the throwaway ~/.claude is byte-identical", fingerprint() == before, len(before))
    with exclusive(PLANT_LOCK):
        homes = [args.home / "claude", args.home / "claude-relayed"]
        try:
            plant_plugin(homes, log)
            planted = await Session.start(
                args.home, model=args.model, workspace=args.workspace, title="s07 plant"
            )
            try:
                outcome, seen = await connect_only(planted)
            finally:
                await planted.harness.close()
            loaded = outcome == "refused" or PLUGIN in seen
            how = (
                "the post-connect check closed the chat"
                if outcome == "refused"
                else "the CLI did not load it"
            )
            log.check(
                "the planted plugin never reaches the first prompt",
                outcome == "refused" or PLUGIN not in seen,
                f"{how}: {seen[:200] if loaded else ''}",
            )
        finally:
            failures = restore(BACKUP)
            log.check("the plant was restored", failures == [], failures)


def main() -> int:
    log = Log("hp6-s07")
    boot()
    use_fake_home()
    require_login(log)
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
