"""P-SET (H21, H53). Claude settings go to the CLI as a file path, and chats in different
folders share one cached system prefix.

Cases, as HARNESS-REQUESTS "Probes named above" writes them:

- path: the launcher passes `settings` as a file path on Windows (`--settings <path>`).
- shrink: the command line shrinks by the settings' size against the same settings inline.
- hook: a `UserPromptSubmit` command hook in that file fires.
- cache: two Background chats with `exclude_dynamic_sections: true` (and `snapshot: false`, as
  H53 sets every preset) in two different folders share a fresh nonce in their `append`; the
  second reads the system prefix from cache. Recorded as `cache_read_input_tokens`. PASS when
  the second chat's cache read exceeds the first chat's by at least 70 % of what the first
  wrote, so the second read the append the first wrote. A control pair with the option omitted
  is recorded beside it, and the fake model records where the working folder sits in the
  request (system text or first user message) with and without the option.
- skills: a launch with a 150-skill filter and the settings file fits the harness's
  command-line check (`ARGV_BUDGET`, 30,000) and the CLI starts on it (L8).

Fail: settings stay on the command line and the append text goes through
`--append-system-prompt-file`. Cache-case fail: Claude's default; an agent chat's working folder
stays the workflow's shared workspace and AGW passes the overlay as an added folder.

    <venv>/Scripts/python.exe p_set.py
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any, Final

from common import (
    ARGV_BUDGET,
    LIVE_QMA,
    PLAN_MODEL,
    Case,
    Log,
    Verdict,
    argv_tap,
    argv_value,
    fresh,
    home_env,
    lane_lock,
    plan_env,
    quoted_length,
    scrub_process_env,
    ship_settings_hash,
    turn,
)

sys.path.append(str(LIVE_QMA))

FALLBACK: Final = (
    "settings stay on the command line and the append text goes through "
    "--append-system-prompt-file (passed in HP0 S20)"
)
CACHE_FALLBACK: Final = (
    "Claude's default: an agent chat's working folder stays the workflow's shared workspace, as "
    "built, and AGW passes the overlay as an added folder with write rules scoped to it"
)
READ_SHARE: Final = 0.7
SKILL_COUNT: Final = 150
DENY_RULES: Final = [
    f"{tool}(//{path})"
    for tool in ("Read", "Edit")
    for path in (
        "D:/QMX-worktrees/qma-ship/home/claude/**",
        "C:/Users/Mubarak/.claude/**",
        "C:/Users/Mubarak/.claude.json",
        "D:/QMX-worktrees/qma-ship/home/settings.toml",
        "D:/QMX-worktrees/qma-ship/home/state/**",
        "D:/QMX-worktrees/qma-ship/home/chats/**",
    )
]
"""Deny rules shaped like the harness's login and secret paths, so the file has a real size."""


def skill_names() -> list[str]:
    return [f"pack-{n % 12:02d}-research:skill-{n:03d}-weekly-review-steps" for n in range(SKILL_COUNT)]


def settings_body(marker: Path) -> dict[str, Any]:
    return {
        "forceLoginMethod": "claudeai",
        "cleanupPeriodDays": 30,
        "autoMemoryEnabled": False,
        "permissions": {"deny": DENY_RULES},
        "hooks": {
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": f'echo fired >> "{marker.as_posix()}"'}]}
            ]
        },
    }


def nonce_append(nonce: str) -> str:
    rule = (
        "Rule {n} for run {nonce}: a node reads its inputs from the run ledger, writes one "
        "output artifact named node-{n}.json, and never calls a model twice for one input hash."
    )
    return "\n".join(rule.format(n=n, nonce=nonce) for n in range(1, 161))


def verdict(observation: dict[str, Any]) -> Verdict:
    launch = observation["launch"]
    cache = observation["cache"]
    first, second = cache["eds"]["a"], cache["eds"]["b"]
    gained = second["cache_read"] - first["cache_read"]
    skills = observation["skills"]
    cases = (
        Case(
            "settings reach the CLI as a file path",
            launch["settings_arg"] == launch["settings_path"],
            {"--settings": launch["settings_arg"]},
        ),
        Case(
            "the command line shrinks by the settings' size",
            launch["inline_length"] - launch["path_length"]
            == launch["inline_part"] - launch["path_part"]
            and launch["inline_part"] > launch["path_part"],
            {k: launch[k] for k in ("inline_length", "path_length", "inline_part", "path_part")},
        ),
        Case(
            "a hook in the settings file fires",
            launch["hook_fired"] >= 1,
            {"marker lines": launch["hook_fired"]},
        ),
        Case(
            "the second folder's chat reads the first chat's system prefix from cache",
            gained >= READ_SHARE * first["cache_write"],
            {
                "a": first,
                "b": second,
                "b read minus a read": gained,
                "needed": READ_SHARE * first["cache_write"],
            },
        ),
        Case(
            f"a launch with a {SKILL_COUNT}-skill filter fits {ARGV_BUDGET} and starts",
            skills["length"] <= ARGV_BUDGET and skills["started"],
            skills,
        ),
    )
    fallback = CACHE_FALLBACK if not cases[3].ok and all(c.ok for c in cases[:3]) else FALLBACK
    return Verdict("P-SET", cases, fallback)


def preset(append: str, *, eds: bool | None) -> dict[str, Any]:
    prompt: dict[str, Any] = {"type": "preset", "preset": "claude_code", "append": append}
    if eds is not None:
        prompt |= {"exclude_dynamic_sections": eds, "snapshot": False}
    return prompt


def options(env: dict[str, str], cwd: Path, **more: Any) -> Any:
    from claude_agent_sdk import ClaudeAgentOptions  # noqa: PLC0415

    return ClaudeAgentOptions(
        env=env, cwd=str(cwd), setting_sources=[], strict_mcp_config=True, tools=[], **more
    )


def built_argv(opts: Any) -> list[str]:
    from claude_agent_sdk._internal.transport.subprocess_cli import (  # noqa: PLC0415
        SubprocessCLITransport,
    )

    transport: Any = SubprocessCLITransport(prompt="", options=opts)
    transport._cli_path = "claude.exe"
    return list(transport._build_command())


def usage_of(seen: Any) -> dict[str, int]:
    return {
        "cache_read": int(seen.usage.get("cache_read_input_tokens") or 0),
        "cache_write": int(seen.usage.get("cache_creation_input_tokens") or 0),
        "input": int(seen.usage.get("input_tokens") or 0),
        "model_turns": int(seen.num_turns),
    }


async def cache_pair(say: Log, settings: Path, *, eds: bool | None) -> dict[str, Any]:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    nonce = secrets.token_hex(8)
    label = "eds" if eds else "control"
    say(f"[cache {label}] nonce {nonce} in the append ({len(nonce_append(nonce))} characters)")
    pair: dict[str, Any] = {"nonce": nonce}
    for name in ("a", "b"):
        folder = fresh(f"set-{label}-{name}-ws")
        opts = options(
            plan_env(f"set-{label}-{name}"),
            folder,
            model=PLAN_MODEL,
            settings=str(settings),
            system_prompt=preset(nonce_append(nonce), eds=eds),
        )
        async with ClaudeSDKClient(opts) as client:
            seen = await turn(client, "Reply with the single word OK.", say)
        pair[name] = usage_of(seen) | {"cwd": str(folder)}
        say(f"[cache {label}] chat {name} in {folder}: {pair[name]}")
    return pair


async def layout(say: Log, *, eds: bool | None) -> dict[str, Any]:
    """Where the fake model finds the working folder: in the system text or the first user
    message."""
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415
    from fake_model import FAKE_KEY, MODEL, FakeModel, Turn, text  # noqa: PLC0415

    label = "eds" if eds else "control"
    root = fresh(f"set-layout-{label}")
    folder = root / "folder-marker-ws"
    folder.mkdir()
    fake = FakeModel([Turn([text("OK")])]).start()
    env = home_env(root / "home", root / "claude") | {
        "ANTHROPIC_BASE_URL": fake.url,
        "ANTHROPIC_API_KEY": FAKE_KEY,
    }
    opts = options(env, folder, model=MODEL, system_prompt=preset("APPEND-MARK", eds=eds))
    try:
        async with ClaudeSDKClient(opts) as client:
            await turn(client, "Reply with OK.", say)
    finally:
        fake.stop()
    body = next(
        seen.json
        for seen in fake.requests
        if seen.method == "POST" and "APPEND-MARK" in json.dumps(seen.json.get("system", ""))
    )
    system = json.dumps(body.get("system", ""))
    first = json.dumps((body.get("messages") or [{}])[0])
    found = {
        "folder_in_system": "folder-marker-ws" in system,
        "folder_in_first_user_message": "folder-marker-ws" in first,
        "append_in_system": "APPEND-MARK" in system,
        "append_after_folder_in_system": system.find("APPEND-MARK") > system.find("folder-marker-ws") >= 0,
    }
    say(f"[layout {label}] {found}")
    return found


async def run(say: Log) -> dict[str, Any]:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    root = fresh("set")
    marker = root / "hook-marker.txt"
    body = settings_body(marker)
    settings = root / "settings.json"
    settings.write_text(json.dumps(body), encoding="utf-8")
    inline = json.dumps(body)
    path_argv = built_argv(options({}, root, model=PLAN_MODEL, settings=str(settings)))
    inline_argv = built_argv(options({}, root, model=PLAN_MODEL, settings=inline))
    observation: dict[str, Any] = {
        "layout": {"eds": await layout(say, eds=True), "control": await layout(say, eds=None)}
    }
    with argv_tap() as started:
        observation["cache"] = {
            "eds": await cache_pair(say, settings, eds=True),
            "control": await cache_pair(say, settings, eds=None),
        }
    hook_lines = marker.read_text(encoding="utf-8").splitlines() if marker.exists() else []
    observation["launch"] = {
        "settings_path": str(settings),
        "settings_arg": argv_value(started[0], "--settings") if started else None,
        "path_length": quoted_length(path_argv),
        "inline_length": quoted_length(inline_argv),
        "path_part": quoted_length([str(settings)]),
        "inline_part": quoted_length([inline]),
        "hook_fired": len(hook_lines),
    }
    say(f"[launch] {observation['launch']}")

    skills_opts = options(
        plan_env("set-skills"),
        fresh("set-skills-ws"),
        model=PLAN_MODEL,
        settings=str(settings),
        skills=skill_names(),
        system_prompt=preset("", eds=True),
    )
    length = quoted_length(built_argv(skills_opts))
    started_ok, error = False, None
    try:
        async with ClaudeSDKClient(skills_opts) as client:
            info = await client.get_server_info()
            started_ok = info is not None
    except Exception as failure:  # noqa: BLE001
        error = f"{type(failure).__name__}: {failure}"
    observation["skills"] = {"count": SKILL_COUNT, "length": length, "started": started_ok, "error": error}
    say(f"[skills] {observation['skills']}")
    observation["plan_turns"] = sum(
        chat["model_turns"] for pair in observation["cache"].values() for chat in (pair["a"], pair["b"])
    )
    return observation


def main() -> int:
    removed = scrub_process_env(os.environ)
    say = Log("prb-h-set")
    say(f"scrubbed {len(removed)} names from the process env (names only)")
    before = ship_settings_hash()
    say(f"ship settings.toml sha256 before {before}")
    with lane_lock(say):
        say("lane lock taken")
        observation = asyncio.run(run(say))
    after = ship_settings_hash()
    say(f"ship settings.toml sha256 after {after}, unchanged={before == after}")
    say(f"haiku plan model turns: {observation['plan_turns']}")
    say.save(observation)
    return say.verdict(verdict(observation))


if __name__ == "__main__":
    sys.exit(main())
