"""S33, one writer on `[claude]`, on the fake model. A chat asks once for a built-in Bash call
and the operator answers AllowAlways through `POST /api/approvals/{ask_id}`.

PASS when `settings.toml` parsed after the answer equals the file parsed before it plus exactly
the suggested rule under `[claude.remembered."<workspace>"]`, and no other line changed.

    s33_one_writer.py
"""

from __future__ import annotations

import asyncio
import copy
import difflib
import sys
from typing import Any

import tomllib
from approval_lane import ALLOW_ALWAYS, Host, answered_turn, fake_session, in_order
from common import SCRATCH, Log, boot, put_claude, use_fake_home, use_fake_key
from fake_model import Turn, text, tool_use

COMMAND = "touch s33.txt"


async def run(log: Log) -> None:
    from qma.harness.home import workspace_key  # noqa: PLC0415

    workspace = SCRATCH / "hp9-s33-workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "s33.txt").unlink(missing_ok=True)
    script = [
        Turn([tool_use("Bash", {"command": COMMAND, "description": "scripted"})]),
        Turn([text("done")]),
    ]
    root, fake, session = await fake_session("hp9-s33", script, tools=["Bash"], workspace=workspace)
    put_claude(root, {"permissions": {"allow": ["Bash(echo *)"]}})
    settings = root / "settings.toml"
    try:
        async with Host(session) as host:
            before_text = settings.read_text(encoding="utf-8")
            answerer = await answered_turn(log, host, session.chat, in_order([ALLOW_ALWAYS]))
            after_text = settings.read_text(encoding="utf-8")
    finally:
        await session.harness.close()
        fake.stop()
    [ask] = answerer.asks
    log(f"  offered always={ask.get('always')}")
    diff = list(
        difflib.unified_diff(
            before_text.splitlines(), after_text.splitlines(), "before", "after", lineterm=""
        )
    )
    for line in diff:
        log(f"  {line}")
    before: dict[str, Any] = tomllib.loads(before_text)
    expected = copy.deepcopy(before)
    expected["claude"]["remembered"] = {workspace_key(workspace): {"allow": ask["always"]}}
    log.check(
        "AllowAlways resolved and the call ran",
        [a.status for a in answerer.answered] == ["resolved"] and (workspace / "s33.txt").exists(),
        [a.status for a in answerer.answered],
    )
    log.check(
        "settings.toml changed by exactly the remembered rule",
        tomllib.loads(after_text) == expected,
        tomllib.loads(after_text).get("claude"),
    )
    changed = [line for line in diff if line[:1] in "+-" and line[:3] not in {"+++", "---"}]
    log.check(
        "the text diff only adds lines",
        bool(changed) and all(line.startswith("+") for line in changed),
        changed,
    )


def main() -> int:
    log = Log("hp9-s33")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
