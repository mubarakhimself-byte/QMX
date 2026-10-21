"""P-PL (H43, H55; review 48 H8). Several local plugins per chat under `setting_sources=[]` and
`strict_mcp_config=True`: the core plugin (`qmx-agents/plugin/`) plus materialised pack views.

The two views in `fixtures/` are copied into a throwaway home's `plugins/` folder, as
`qma.harness.packs` would materialise them: `plugin.json`, `skills/`, `agents/`, `commands/`.

- skills: a chat with the core plugin and both views lists both packs' skills (`plugin:skill`).
- agent: it spawns a pack agent (`pack-alpha:alpha-agent`) through the Agent tool.
- command: it runs a pack command (`/pack-beta:beta-cmd`).
- no MCP, no hook: it starts no MCP server and runs no hook from either pack.
- outside the set: a chat on the core plugin and `pack-alpha` only, with `pack-beta`
  materialised beside it, lists no agent, command or skill of `pack-beta`.
- join by resume: that chat is told a word, closed, and relaunched by resume with `pack-beta`
  added; the next turn lists `pack-beta`'s skill, agent and command and still knows the word.

PASS when every case holds. Fail: PACK materialises one combined plugin view per pack set.

Recorded beside the verdict, not gating it: the skills filter (H48), where a chat with
`skills=["pack-alpha:alpha-skill"]` should not list `pack-beta:beta-skill` and its Skill tool
should refuse it; and the perf block, the connect time of a chat with the core plugin and both
views, three times, against the core plugin alone.

    <venv>/Scripts/python.exe p_pl.py
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import shutil
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Final

from common import (
    FIXTURES,
    LIVE_QMA,
    PLAN_MODEL,
    Case,
    Log,
    Verdict,
    fresh,
    home_env,
    lane_lock,
    plan_env,
    scrub_process_env,
    ship_settings_hash,
    turn,
)

sys.path.append(str(LIVE_QMA))

FALLBACK: Final = "PACK materialises one combined plugin view per pack set"
CORE_PLUGIN: Final = Path(__file__).resolve().parents[3] / "qmx-agents" / "plugin"
PACKS: Final = ("pack-alpha", "pack-beta")
LAUNCHES: Final = 3
AGENT_ASK: Final = (
    "Use the Agent tool once with subagent_type pack-alpha:alpha-agent and the prompt go. Then "
    "reply with exactly the text the agent returned."
)


def materialise(root: Path) -> dict[str, Path]:
    plugins = root / "plugins"
    views = {}
    for pack in PACKS:
        shutil.copytree(FIXTURES / pack, plugins / pack)
        views[pack] = plugins / pack
    return views


def plugin_list(*paths: Path) -> list[dict[str, str]]:
    return [{"type": "local", "path": str(path)} for path in paths]


def options(slug: str, cwd: Path, plugins: list[dict[str, str]], **more: Any) -> Any:
    from claude_agent_sdk import ClaudeAgentOptions  # noqa: PLC0415

    return ClaudeAgentOptions(
        env=plan_env(slug),
        cwd=str(cwd),
        model=PLAN_MODEL,
        setting_sources=[],
        strict_mcp_config=True,
        tools=["Agent", "Skill"],
        permission_mode="default",
        allowed_tools=["Agent", "Skill"],
        plugins=plugins,  # type: ignore[arg-type]
        include_hook_events=True,
        **more,
    )


def listing(init: dict[str, Any]) -> dict[str, Any]:
    return {
        "skills": sorted(str(s) for s in init.get("skills", [])),
        "agents": sorted(str(a) for a in init.get("agents", [])),
        "commands": sorted(str(c) for c in init.get("slash_commands", [])),
        "mcp_servers": init.get("mcp_servers", []),
        "plugins": [p.get("name") for p in init.get("plugins", [])],
    }


def has_pack(found: dict[str, Any], pack: str) -> dict[str, bool]:
    short = pack.removeprefix("pack-")
    return {
        "skill": f"{pack}:{short}-skill" in found["skills"],
        "agent": f"{pack}:{short}-agent" in found["agents"],
        "command": f"{pack}:{short}-cmd" in found["commands"],
    }


def agent_output(tasks: list[dict[str, Any]]) -> str:
    """The pack agent's output file, when the completion notice names one that still exists. The
    Agent tool launches the agent in the background, so the tool result holds no reply; the
    notice's `summary` carries the agent's final text."""
    for task in tasks:
        path = task.get("output_file")
        if task["subtype"] == "task_notification" and path and Path(path).is_file():
            return Path(path).read_text(encoding="utf-8", errors="replace")[-2000:]
    return ""


async def main_chat(say: Log, root: Path, views: dict[str, Path]) -> dict[str, Any]:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    plugins = plugin_list(CORE_PLUGIN, *views.values())
    async with ClaudeSDKClient(options("pl-main", fresh("pl-main-ws"), plugins)) as client:
        command = await turn(client, "/pack-beta:beta-cmd", say)
        agent = await turn(client, AGENT_ASK, say)
    found = listing(command.init)
    tasks = [
        json.loads(m["data"]) | {"subtype": m["subtype"]}
        for m in agent.system
        if m["subtype"].startswith("task_")
    ]
    hooks = [m for seen in (command, agent) for m in seen.system if "hook" in m["subtype"]]
    row = {
        "listing": found,
        "command_reply": command.text(),
        "agent_calls": [u for u in agent.tool_uses if u["name"] in {"Agent", "Task"}],
        "agent_results": [r["text"] for r in agent.tool_results],
        "agent_reply": agent.text(),
        "agent_tasks": tasks,
        "agent_output": agent_output(tasks),
        "hook_events": hooks,
        "system_subtypes": sorted({m["subtype"] for seen in (command, agent) for m in seen.system}),
        "model_turns": command.num_turns + agent.num_turns,
    }
    say(f"[main] {row}")
    return row


async def resume_chat(say: Log, views: dict[str, Path]) -> dict[str, Any]:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    word = f"KEPT-{secrets.token_hex(3).upper()}"
    workspace = fresh("pl-resume-ws")
    before = plugin_list(CORE_PLUGIN, views["pack-alpha"])
    async with ClaudeSDKClient(options("pl-resume", workspace, before)) as client:
        first = await turn(client, f"Remember the word {word}. Reply with the single word OK.", say)
    after = plugin_list(CORE_PLUGIN, *views.values())
    resumed = options("pl-resume", workspace, after, resume=first.session_id)
    async with ClaudeSDKClient(resumed) as client:
        second = await turn(
            client, "What word did I ask you to remember? Reply with only that word.", say
        )
        command = await turn(client, "/pack-beta:beta-cmd", say)
    row = {
        "word": word,
        "before": listing(first.init),
        "after": listing(second.init),
        "recall_reply": second.text(),
        "command_reply": command.text(),
        "same_session": first.session_id == second.session_id,
        "model_turns": first.num_turns + second.num_turns + command.num_turns,
    }
    say(f"[resume] {row}")
    return row


async def skills_filter(say: Log, views: dict[str, Path]) -> dict[str, Any]:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    plugins = plugin_list(CORE_PLUGIN, *views.values())
    opts = options("pl-filter", fresh("pl-filter-ws"), plugins, skills=["pack-alpha:alpha-skill"])
    async with ClaudeSDKClient(opts) as client:
        seen = await turn(
            client,
            "Use the Skill tool once to run the skill pack-beta:beta-skill, then reply with "
            "exactly what happened in one line.",
            say,
        )
    row = {
        "skills": listing(seen.init)["skills"],
        "skill_calls": seen.tool_uses,
        "skill_results": seen.tool_results,
        "reply": seen.text(),
        "model_turns": seen.num_turns,
        "model_sees_beta_skill": {
            "filtered": await skill_on_wire(say, views, ["pack-alpha:alpha-skill"]),
            "unfiltered": await skill_on_wire(say, views, None),
        },
    }
    say(f"[skills filter, recorded] {row}")
    return row


async def skill_on_wire(say: Log, views: dict[str, Path], skills: list[str] | None) -> bool:
    """Whether `beta-skill` appears anywhere in the requests the CLI sends, read from the fake
    model, since the init listing names every discovered skill either way."""
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient  # noqa: PLC0415
    from fake_model import FAKE_KEY, MODEL, FakeModel, Turn, text  # noqa: PLC0415

    root = fresh(f"pl-wire-{'filtered' if skills else 'unfiltered'}")
    fake = FakeModel([Turn([text("OK")])]).start()
    opts = ClaudeAgentOptions(
        env=home_env(root / "home", root / "claude")
        | {"ANTHROPIC_BASE_URL": fake.url, "ANTHROPIC_API_KEY": FAKE_KEY},
        cwd=str(root),
        model=MODEL,
        setting_sources=[],
        strict_mcp_config=True,
        tools=["Agent", "Skill"],
        plugins=plugin_list(CORE_PLUGIN, *views.values()),  # type: ignore[arg-type]
        skills=skills,
    )
    try:
        async with ClaudeSDKClient(opts) as client:
            await turn(client, "Reply with OK.", say)
    finally:
        fake.stop()
    return any(b"beta-skill" in seen.body for seen in fake.requests if seen.method == "POST")


async def launch_ms(plugins: list[dict[str, str]], slug: str) -> float:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    started = time.perf_counter()
    async with ClaudeSDKClient(options(slug, fresh(f"{slug}-ws"), plugins)) as client:
        await client.get_server_info()
        elapsed = (time.perf_counter() - started) * 1000
    return round(elapsed, 1)


async def perf(say: Log, views: dict[str, Path]) -> dict[str, Any]:
    with_packs = [
        await launch_ms(plugin_list(CORE_PLUGIN, *views.values()), "pl-perf-packs")
        for _ in range(LAUNCHES)
    ]
    core_only = [await launch_ms(plugin_list(CORE_PLUGIN), "pl-perf-core") for _ in range(LAUNCHES)]
    row = {
        "core_and_two_packs_ms": with_packs,
        "core_only_ms": core_only,
        "median_packs_ms": statistics.median(with_packs),
        "median_core_ms": statistics.median(core_only),
    }
    say(f"[perf] {row}")
    return row


async def run(say: Log) -> dict[str, Any]:
    root = fresh("pl")
    views = materialise(root)
    say(f"core plugin {CORE_PLUGIN}; views {', '.join(str(v) for v in views.values())}")
    observation = {
        "main": await main_chat(say, root, views),
        "resume": await resume_chat(say, views),
        "skills_filter": await skills_filter(say, views),
        "perf": await perf(say, views),
    }
    observation["plan_turns"] = sum(
        observation[key]["model_turns"] for key in ("main", "resume", "skills_filter")
    )
    return observation


def verdict(observation: dict[str, Any]) -> Verdict:
    main, resume = observation["main"], observation["resume"]
    listed = main["listing"]
    pack_names = set(PACKS) | {p.removeprefix("pack-") for p in PACKS}
    outside = has_pack(resume["before"], "pack-beta")
    joined = has_pack(resume["after"], "pack-beta")
    cases = (
        Case(
            "the chat lists both packs' skills as plugin:skill",
            has_pack(listed, "pack-alpha")["skill"] and has_pack(listed, "pack-beta")["skill"],
            listed["skills"],
        ),
        Case(
            "it spawns a pack agent",
            any(
                c["input"].get("subagent_type") == "pack-alpha:alpha-agent"
                for c in main["agent_calls"]
            )
            and any(t["subtype"] == "task_started" for t in main["agent_tasks"])
            and any(
                t["subtype"] == "task_notification"
                and t.get("status") == "completed"
                and "ALPHA-AGENT-OK" in f"{t.get('summary')} {main['agent_output']}"
                for t in main["agent_tasks"]
            ),
            {
                "calls": main["agent_calls"],
                "tasks": [
                    {k: t.get(k) for k in ("subtype", "status", "summary")}
                    for t in main["agent_tasks"]
                ],
                "output_tail": main["agent_output"][-300:],
            },
        ),
        Case(
            "it runs a pack command",
            "BETA-CMD-OK" in main["command_reply"],
            {"listed": has_pack(listed, "pack-beta")["command"], "reply": main["command_reply"]},
        ),
        Case(
            "it starts no MCP server from either pack",
            not any(
                any(name in str(server) for name in pack_names) for server in listed["mcp_servers"]
            ),
            listed["mcp_servers"],
        ),
        Case(
            "it runs no hook from either pack",
            not any(any(name in m["data"] for name in pack_names) for m in main["hook_events"]),
            {"hook events": len(main["hook_events"]), "system subtypes": main["system_subtypes"]},
        ),
        Case(
            "an enabled pack outside the set lists no agent, command or skill",
            not any(outside.values()),
            outside,
        ),
        Case(
            "a pack added mid-session joins by relaunch-by-resume with its context kept",
            all(joined.values())
            and resume["same_session"]
            and resume["word"] in resume["recall_reply"]
            and "BETA-CMD-OK" in resume["command_reply"],
            {
                "listed": joined,
                "recall": resume["recall_reply"],
                "command": resume["command_reply"],
                "same_session": resume["same_session"],
            },
        ),
    )
    return Verdict("P-PL", cases, FALLBACK)


def main() -> int:
    removed = scrub_process_env(os.environ)
    say = Log("prb-h-pl")
    say(f"scrubbed {len(removed)} names from the process env (names only)")
    before = ship_settings_hash()
    say(f"ship settings.toml sha256 before {before}")
    with lane_lock(say):
        say("lane lock taken")
        observation = asyncio.run(run(say))
    after = ship_settings_hash()
    say(f"ship settings.toml sha256 after {after}, unchanged={before == after}")
    say(f"haiku plan model turns: {observation['plan_turns']}")
    perf_row = observation["perf"]
    say(
        f"PERF launch ms, core plus two pack views {perf_row['core_and_two_packs_ms']} (median "
        f"{perf_row['median_packs_ms']}), core only {perf_row['core_only_ms']} (median "
        f"{perf_row['median_core_ms']})"
    )
    say.save(observation)
    return say.verdict(verdict(observation))


if __name__ == "__main__":
    sys.exit(main())
