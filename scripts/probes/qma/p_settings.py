"""S20 prototype, DESIGN open questions 3 to 5. Inline settings with `setting_sources=[]`.

Plants a skill, a command, an agent and a `settings.json` hook in the ship home, connects
with inline settings that carry `forceLoginMethod`, `cleanupPeriodDays`, a ConfigChange
command hook and a PreToolUse command hook (the control that inline command hooks run at
all). The agent then writes `settings.json` into the home mid-session. Everything planted
is removed afterwards and any earlier `settings.json` is restored.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, SystemMessage
from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport
from common import (
    CONFIG_DIR,
    FORCE_LOGIN,
    SCRATCH,
    Log,
    bundled_cli,
    plan_options,
    require_plan_login,
    run_turns,
    scrub_process_env,
)

MARKERS = SCRATCH / "settings-markers"
HOME_SETTINGS = CONFIG_DIR / "settings.json"
CODEWORD = "HP0-MANGO"
PLANTS = {
    CONFIG_DIR / "skills" / "hp0-plant-skill" / "SKILL.md": (
        "---\nname: hp0-plant-skill\ndescription: HP0 planted skill.\n---\nSay planted.\n"
    ),
    CONFIG_DIR / "commands" / "hp0-plant-cmd.md": "Say planted command.\n",
    CONFIG_DIR / "agents" / "hp0-plant-agent.md": (
        "---\nname: hp0-plant-agent\ndescription: HP0 planted agent.\n---\nSay planted agent.\n"
    ),
}
WRITTEN_SETTINGS = {
    "apiKeyHelper": "echo sk-ant-api03-hp0-probe-fake-key-not-a-credential",
    "env": {"HTTPS_PROXY": "http://127.0.0.1:9", "NODE_EXTRA_CA_CERTS": "D:/hp0-missing.pem"},
    "enabledPlugins": {"hp0-plant-plugin@hp0-local": True},
    "permissions": {"allow": ["Bash(*)"]},
}


def marker_hook(tag: str) -> dict[str, str]:
    """A command hook that appends its stdin, one line per call, to `MARKERS/<tag>.jsonl`."""
    python = Path(sys.executable).as_posix()
    target = (MARKERS / f"{tag}.jsonl").as_posix()
    line = 'sys.stdin.read().replace(chr(10), " ") + chr(10)'
    program = f'import sys; open(r"{target}", "a").write({line})'
    return {"type": "command", "command": f"'{python}' -c '{program}'"}


def inline_settings() -> str:
    return json.dumps(
        FORCE_LOGIN
        | {
            "cleanupPeriodDays": 3650,
            "hooks": {
                "ConfigChange": [{"hooks": [marker_hook("configchange")]}],
                "PreToolUse": [{"matcher": "Bash", "hooks": [marker_hook("inline-pretool")]}],
            },
        }
    )


def plant() -> str | None:
    """Plant the home files. Returns the earlier `settings.json` text, if there was one."""
    MARKERS.mkdir(parents=True, exist_ok=True)
    for marker in MARKERS.glob("*.jsonl"):
        marker.unlink()
    earlier = HOME_SETTINGS.read_text(encoding="utf-8") if HOME_SETTINGS.exists() else None
    for path, text in PLANTS.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    home_hook = {
        "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [marker_hook("home-pretool")]}]}
    }
    HOME_SETTINGS.write_text(json.dumps(home_hook), encoding="utf-8")
    return earlier


def unplant(earlier: str | None) -> None:
    for path in PLANTS:
        path.unlink(missing_ok=True)
        if path.name == "SKILL.md":
            path.parent.rmdir()
    if earlier is None:
        HOME_SETTINGS.unlink(missing_ok=True)
    else:
        HOME_SETTINGS.write_text(earlier, encoding="utf-8")


def argv_length(options: ClaudeAgentOptions) -> int:
    transport: Any = SubprocessCLITransport(prompt="", options=options)
    transport._cli_path = str(bundled_cli())
    return len(subprocess.list2cmdline(transport._build_command()))


def markers(tag: str) -> list[str]:
    path = MARKERS / f"{tag}.jsonl"
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


async def main() -> int:
    log = Log("hp0-settings")
    require_plan_login(log, bundled_cli())
    scrub_process_env(os.environ)
    append_file = SCRATCH / "append-system-prompt.txt"
    append_file.write_text(f"The codeword is {CODEWORD}. When asked for it, reply with it.\n")
    options = plan_options(
        settings=inline_settings(),
        system_prompt={"type": "preset", "preset": "claude_code", "append": "Be brief."},
        extra_args={"append-system-prompt-file": append_file.as_posix()},
    )
    log(
        f"argv length with inline settings, preset append and the file flag: {argv_length(options)}"
    )
    write_settings = (
        "Run this exact Bash command and reply done: "
        f"cat > '{HOME_SETTINGS.as_posix()}' <<'JSON'\n{json.dumps(WRITTEN_SETTINGS)}\nJSON"
    )
    earlier = plant()
    try:
        messages = await run_turns(
            log, options, ["Reply with the codeword only.", write_settings, "say ok"]
        )
    except Exception as error:
        log(f"session failed: {type(error).__name__}: {error}")
        log.row("S20 CLI accepts inline settings and the file flag", repr(error)[:300], "FAIL")
        return 1
    finally:
        written = HOME_SETTINGS.read_text(encoding="utf-8") if HOME_SETTINGS.exists() else ""
        unplant(earlier)

    results = [m for m in messages if isinstance(m, ResultMessage)]
    init = next((m for m in messages if isinstance(m, SystemMessage) and m.subtype == "init"), None)
    init_data: dict[str, Any] = init.data if init else {}
    loaded = {
        key: [name for name in init_data.get(key, []) if "hp0" in json.dumps(name)]
        for key in ("slash_commands", "skills", "agents", "plugins")
    }
    codeword = CODEWORD in str(results[0].result) if results else False
    third_ok = len(results) == 3 and not results[2].is_error
    log(
        f"home settings.json after the agent's write held the S20 keys: {'apiKeyHelper' in written}"
    )
    log.row(
        "S20 CLI accepts inline settings", f"{len(results)} results", "PASS" if results else "FAIL"
    )
    log.row(
        "OQ4 append-system-prompt-file next to the preset",
        f"codeword returned={codeword}",
        "PASS" if codeword else "FAIL",
    )
    log.row(
        "S20 inline PreToolUse command hook fired (control)",
        len(markers("inline-pretool")),
        "PASS" if markers("inline-pretool") else "FAIL",
    )
    log.row(
        "OQ3 ConfigChange fired after the mid-session write",
        len(markers("configchange")),
        "RECORDED",
    )
    log.row("OQ5 home settings.json hook loaded", len(markers("home-pretool")), "RECORDED")
    log.row("OQ5 planted skill, command, agent or plugin in init", loaded, "RECORDED")
    log.row(
        "S20 next turn after the write stays on the plan",
        f"ok={third_ok}",
        "PASS" if third_ok else "FAIL",
    )
    for line in markers("configchange"):
        log(f"configchange input: {line[:400]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
