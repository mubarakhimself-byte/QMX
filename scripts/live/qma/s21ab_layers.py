"""S21a and S21b, the credential layers one at a time. Key chats on the fake model in bypass
mode, against a throwaway QMX home whose plan login, and a throwaway HOME whose `~/.claude`
login, hold a canary.

S21a, deny rules alone: `TestMode(gate_hook=False, relay_egress_stop=False, redaction=False)`.
Read, Grep and Glob on each login file.
S21b, gate patterns alone: `TestMode(deny_rules=False, relay_egress_stop=False,
redaction=False)`. Bash reads of each login in literal, `$CLAUDE_CONFIG_DIR`, `~`, `$HOME` and
relative form.

PASS when every S21a call is refused by a rule and every S21b call by the hook, and no result
the fake model received holds the canary.

    s21ab_layers.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from common import (
    CANARY,
    FAKE_HOME,
    SCRATCH,
    Log,
    boot,
    plant_canary_login,
    throwaway_home,
    use_fake_home,
    use_fake_key,
)
from money_lane import Call, plant_personal_login, relative, run_calls


def builtin_reads(root: Path) -> list[Call]:
    found: list[Call] = []
    for name, login in (
        ("plan", root / "claude" / ".credentials.json"),
        ("personal", FAKE_HOME / ".claude" / ".credentials.json"),
    ):
        found += [
            Call(f"Read {name} login", "Read", {"file_path": login.as_posix()}),
            Call(f"Grep {name} login", "Grep", {"pattern": "sk-ant", "path": login.as_posix()}),
            Call(
                f"Glob {name} login",
                "Glob",
                {"pattern": ".credentials.json", "path": login.parent.as_posix()},
            ),
        ]
    return found


def bash_reads(root: Path, workspace: Path) -> list[Call]:
    plan = root / "claude" / ".credentials.json"
    personal = FAKE_HOME / ".claude" / ".credentials.json"
    commands = {
        "literal plan": f"cat {plan.as_posix()}",
        "literal personal": f"cat {personal.as_posix()}",
        "$CLAUDE_CONFIG_DIR": 'cat "$CLAUDE_CONFIG_DIR/.credentials.json"',
        "~": "cat ~/.claude/.credentials.json",
        "$HOME": 'cat "$HOME/.claude/.credentials.json"',
        "relative plan": f"cat {relative(plan, workspace)}",
        "relative personal": f"cat {relative(personal, workspace)}",
    }
    return [
        Call(f"Bash {label}", "Bash", {"command": command, "description": "read"})
        for label, command in commands.items()
    ]


def refused_or_unreached(call: Call, kind: str, said: str) -> bool:
    """A Glob that the rules let through passes only when it cannot list the login: Glob
    skips dot files, so `.credentials.json` never matches."""
    if kind == "rule":
        return True
    return call.tool == "Glob" and kind == "ran" and ".credentials" not in said


async def layer(
    log: Log, slug: str, calls: list[Call], test: object, tools: list[str], want: str
) -> None:
    root = throwaway_home(f"hp8-{slug}")
    plant_canary_login(root)
    workspace = SCRATCH / "workspace"
    session, fake, outcomes = await run_calls(
        log,
        root,
        calls,
        test=test,
        mode="bypassPermissions",
        tools=tools,
        title=slug,
        workspace=workspace,
    )
    try:
        for call in calls:
            kind, said = outcomes[call.label]
            ok = kind == want or (want == "rule" and refused_or_unreached(call, kind, said))
            log.check(f"{slug}: {call.label}", ok, kind if kind == want else f"{kind}: {said!r}")
        log.check(
            f"{slug}: canary in no request",
            all(CANARY.encode() not in seen.body for seen in fake.requests),
            len(fake.requests),
        )
    finally:
        await session.harness.close()
        fake.stop()


async def run(log: Log) -> None:
    from qma.harness import TestMode  # noqa: PLC0415

    plant_personal_login()
    workspace = SCRATCH / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    log("--- S21a, deny rules alone")
    root_a = SCRATCH / "homes" / "hp8-s21a"
    await layer(
        log,
        "s21a",
        builtin_reads(root_a),
        TestMode(
            gate_hook=False,
            relay_egress_stop=False,
            redaction=False,
            loopback_http_provider=True,
        ),
        ["Read", "Grep", "Glob"],
        "rule",
    )
    log("--- S21b, gate patterns alone")
    root_b = SCRATCH / "homes" / "hp8-s21b"
    await layer(
        log,
        "s21b",
        bash_reads(root_b, workspace),
        TestMode(
            deny_rules=False,
            relay_egress_stop=False,
            redaction=False,
            loopback_http_provider=True,
        ),
        ["Bash"],
        "hook",
    )


def main() -> int:
    log = Log("hp8-s21ab")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
