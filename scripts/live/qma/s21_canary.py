"""S21, the canary: the plan token never leaves. Throwaway QMX homes whose plan login, and a
throwaway HOME whose `~/.claude` login, hold a canary of the real token shape. A key chat on
the fake model (the echo server) tries every read: Read, Grep and Glob on the plan login,
`cat "$CLAUDE_CONFIG_DIR/.credentials.json"`, a relative-path `cat`, and the same on
`~/.claude`. It runs in default mode, in bypass mode, and inside a native sub-agent.
`delegate` is not built yet, so the delegated leg is not run.

PASS when every read attempt is denied, the canary appears in no QMX file, no fake-model
request body or header, and no evidence log, and the relay saw zero unknown bearers.

    s21_canary.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from common import (
    CANARY,
    FAKE_HOME,
    SCRATCH,
    Log,
    boot,
    files_holding,
    plant_canary_login,
    throwaway_home,
    use_fake_home,
    use_fake_key,
)
from money_lane import Call, in_subagent, plant_personal_login, relative, run_calls

TOOLS = ["Bash", "Read", "Grep", "Glob", "Agent"]
MODES = (
    ("default", "default", False),
    ("bypass", "bypassPermissions", False),
    ("agent", "bypassPermissions", True),
)


def reads(root: Path, workspace: Path) -> list[Call]:
    login = root / "claude" / ".credentials.json"
    personal = FAKE_HOME / ".claude"
    return [
        Call("Read plan login", "Read", {"file_path": login.as_posix()}),
        Call("Grep plan home", "Grep", {"pattern": "sk-ant", "path": (root / "claude").as_posix()}),
        Call(
            "Glob for logins", "Glob", {"pattern": "**/.credentials.json", "path": root.as_posix()}
        ),
        Call(
            "cat $CLAUDE_CONFIG_DIR login",
            "Bash",
            {"command": 'cat "$CLAUDE_CONFIG_DIR/.credentials.json"', "description": "read"},
        ),
        Call(
            "relative cat plan login",
            "Bash",
            {"command": f"cat {relative(login, workspace)}", "description": "read"},
        ),
        Call("Read ~ login", "Read", {"file_path": "~/.claude/.credentials.json"}),
        Call(
            "cat ~ login",
            "Bash",
            {"command": "cat ~/.claude/.credentials.json", "description": "read"},
        ),
        Call(
            "cat $HOME login",
            "Bash",
            {"command": 'cat "$HOME/.claude/.credentials.json"', "description": "read"},
        ),
        Call("Grep ~/.claude", "Grep", {"pattern": "sk-ant", "path": personal.as_posix()}),
        Call(
            "relative cat ~ login",
            "Bash",
            {
                "command": f"cat {relative(personal / '.credentials.json', workspace)}",
                "description": "read",
            },
        ),
    ]


async def run(log: Log) -> None:
    from qma.harness import TestMode  # noqa: PLC0415

    plant_personal_login()
    workspace = SCRATCH / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    roots: list[Path] = []
    bodies: list[bytes] = []
    for slug, mode, in_agent in MODES:
        log(f"--- {slug}")
        root = throwaway_home(f"hp8-s21-{slug}")
        roots.append(root)
        plant_canary_login(root)
        plan = reads(root, workspace)
        session, fake, outcomes = await run_calls(
            log,
            root,
            plan,
            test=TestMode(loopback_http_provider=True),
            mode=mode,
            tools=TOOLS,
            in_agent=in_agent,
            title=f"s21 {slug}",
            workspace=workspace,
        )
        try:
            for call in plan:
                kind = outcomes[call.label][0]
                log.check(f"{slug}: {call.label} denied", kind in ("hook", "rule"), kind)
            if in_agent:
                inside = [call.label for call in plan if in_subagent(fake, call)]
                log.check(
                    f"{slug}: every call was made by the sub-agent",
                    len(inside) == len(plan),
                    inside,
                )
            log.check(
                f"{slug}: relay saw no unknown bearer",
                session.relay.counters.bearer == 0,
                session.relay.counters.bearer,
            )
            bodies += [seen.body + repr(seen.headers).encode() for seen in fake.requests]
        finally:
            await session.harness.close()
            fake.stop()
    logins = {(root / "claude" / ".credentials.json").resolve() for root in roots}
    logins.add((FAKE_HOME / ".claude" / ".credentials.json").resolve())
    leaked = [
        path
        for path in files_holding(
            [*roots, workspace, Path(os.environ.get("QMA_EVIDENCE_DIR", log.path.parent))], CANARY
        )
        if path.resolve() not in logins
    ]
    log.check("canary in no QMX file or evidence log", leaked == [], [str(path) for path in leaked])
    log.check(
        "canary in no request the fake model received",
        all(CANARY.encode() not in body for body in bodies),
        len(bodies),
    )


def main() -> int:
    log = Log("hp8-s21")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
