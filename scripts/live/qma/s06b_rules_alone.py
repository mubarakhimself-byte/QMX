"""S6b, the deny rules alone. A key chat on the fake model in bypass mode with
`TestMode(gate_hook=False)`. The fake model makes S6's path calls: a Read, an Edit and a
Write of settings.toml, a Read of the plan login, and a Read of a login file in the throwaway
HOME's `.claude`. A Read of a state file in the QMX home is the control.

PASS when every path call is refused by a rule in `//c/...` (here `//d/...`) form, the control
read runs, and the rendered rules are printed.

    s06b_rules_alone.py
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
from money_lane import Call, plant_personal_login, run_calls

TOOLS = ["Read", "Edit", "Write"]
CONTROL = "s06-control.txt"


async def run(log: Log) -> None:
    from qma.harness import TestMode  # noqa: PLC0415

    root = throwaway_home("hp8-s06b")
    plant_canary_login(root)
    (root / "state").mkdir(parents=True, exist_ok=True)
    (root / "state" / CONTROL).write_text("control", encoding="utf-8")
    personal = plant_personal_login()
    launches = capture_launches()
    settings = (root / "settings.toml").as_posix()
    plan = [
        Call("control read state", "Read", {"file_path": (root / "state" / CONTROL).as_posix()}),
        Call("read settings.toml", "Read", {"file_path": settings}),
        Call(
            "edit settings.toml",
            "Edit",
            {"file_path": settings, "old_string": "[providers.fake]", "new_string": "[x]"},
        ),
        Call("write settings.toml", "Write", {"file_path": settings, "content": "x = 1\n"}),
        Call(
            "read plan login", "Read", {"file_path": (root / "claude/.credentials.json").as_posix()}
        ),
        Call("read personal login", "Read", {"file_path": personal.as_posix()}),
    ]
    session, fake, outcomes = await run_calls(
        log,
        root,
        plan,
        test=TestMode(gate_hook=False, loopback_http_provider=True),
        mode="bypassPermissions",
        tools=TOOLS,
        title="s06b",
    )
    try:
        rules = launches[-1].options.disallowed_tools
        log("rendered deny rules:")
        for rule in rules:
            log(f"  {rule}")
        log.check(
            "rules use the //<drive>/ form",
            all(r.split("(", 1)[1].startswith("//") for r in rules),
            len(rules),
        )
        log.check(
            "no hook on the launch", launches[-1].options.hooks is None, launches[-1].options.hooks
        )
        for call in plan:
            want = "ran" if call.label.startswith("control") else "rule"
            log.check(call.label, outcomes[call.label][0] == want, outcomes[call.label][0])
        log.check(
            "settings.toml unchanged",
            "x = 1" not in (root / "settings.toml").read_text(encoding="utf-8"),
            "checked",
        )
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp8-s06b")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
