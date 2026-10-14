"""S6a, the gate hook alone. A key chat on the fake model in bypass mode with
`TestMode(deny_rules=False, grants=False)`. The fake model makes S6's calls: the mixed-case
keyring read, a shell command naming a broker host (the fake profile's CLI offers no Monitor
tool; the plan lane covers Monitor), an Edit and a Write of settings.toml, and a Read of the
plan login. A Read of settings.toml is the control: reads of QMX state run.

PASS when every denied call is denied by the hook (its text names the money rule), the control
read runs, the rendered launch carries no deny rules, and no CLI connected to a broker host.

    s06a_gate_alone.py
"""

from __future__ import annotations

import asyncio
import sys

from common import (
    Log,
    boot,
    capture_launches,
    plant_canary_login,
    throwaway_home,
    use_fake_home,
    use_fake_key,
)
from money_lane import Call, run_calls

KEYRING = "python -c \"import keyring; keyring.get_password('QMX/ctrader','ctrader')\""
BROKER = "curl -s --max-time 3 https://demo.ctraderapi.com:5035"
TOOLS = ["Bash", "Read", "Edit", "Write"]


def calls(root_text: str) -> list[Call]:
    settings = f"{root_text}/settings.toml"
    return [
        Call("keyring read", "Bash", {"command": KEYRING, "description": "read"}),
        Call("broker host", "Bash", {"command": BROKER, "description": "fetch"}),
        Call("control read settings.toml", "Read", {"file_path": settings}),
        Call(
            "edit settings.toml",
            "Edit",
            {"file_path": settings, "old_string": "[providers.fake]", "new_string": "[x]"},
        ),
        Call("write settings.toml", "Write", {"file_path": settings, "content": "x = 1\n"}),
        Call("read plan login", "Read", {"file_path": f"{root_text}/claude/.credentials.json"}),
    ]


async def run(log: Log) -> None:
    from qma.harness import TestMode  # noqa: PLC0415

    root = throwaway_home("hp8-s06a")
    plant_canary_login(root)
    launches = capture_launches()
    plan = calls(root.as_posix())
    session, fake, outcomes = await run_calls(
        log,
        root,
        plan,
        test=TestMode(deny_rules=False, grants=False, loopback_http_provider=True),
        mode="bypassPermissions",
        tools=TOOLS,
        title="s06a",
    )
    try:
        for call in plan:
            want = "ran" if call.label.startswith("control") else "hook"
            log.check(call.label, outcomes[call.label][0] == want, outcomes[call.label][0])
        options = launches[-1].options
        log.check(
            "no deny rules rendered", options.disallowed_tools == [], options.disallowed_tools
        )
        log.check(
            "settings.toml unchanged",
            "x = 1" not in (root / "settings.toml").read_text(encoding="utf-8"),
            "checked",
        )
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp8-s06a")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
