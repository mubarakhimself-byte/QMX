"""S20 prototype, DESIGN open questions 3 to 5. Inline settings with `setting_sources=[]`.

Plants a skill, a command and an agent in the ship home, installs a local plugin there with
the CLI's own `plugin install`, and adds a `settings.json` PreToolUse hook. A connect with
`setting_sources=["user"]` is the control that the plants would load. The probe session
then connects with `setting_sources=[]`, a second plugin passed through `plugins`, and
inline settings that carry `forceLoginMethod`, `cleanupPeriodDays`, a ConfigChange command
hook and a PreToolUse command hook. A fixed Bash turn fires the PreToolUse hooks. The agent
then writes `settings.json` mid-session, or the probe writes it when the model refuses.
`plants.restore` undoes everything on exit, and every probe heals a crashed run's plant at its
next start. A pid lock keeps two runs from sharing one backup.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
from typing import Any

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    Message,
    ResultMessage,
    SystemMessage,
)
from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport
from common import (
    CONFIG_DIR,
    FORCE_LOGIN,
    MARKERS,
    PLANT_BACKUP,
    PLANT_LOCK,
    SCRATCH,
    Lockdown,
    Log,
    Marker,
    bundled_cli,
    cli_env,
    describe,
    oq5_home_verdict,
    plan_options,
    require_plan_login,
    scrub_process_env,
    tool_uses,
)
from plants import exclusive, restore, snapshot

MARKET = SCRATCH / "plugin-market"
HOME_SETTINGS = CONFIG_DIR / "settings.json"
SYNCED = CONFIG_DIR / "plugins" / "synced"
FILE_CODEWORD = "HP0-MANGO"
INLINE_CODEWORD = "HP0-KIWI"
MARKETPLACE = "hp0-local"
HOME_PLUGIN = "hp0-plant-plugin"
HOME_PLANTS = frozenset({HOME_PLUGIN, "hp0-plant-skill", "hp0-plant-cmd", "hp0-plant-agent"})
SDK_PLUGIN = "hp0-sdk-plugin"
PLANTS = {
    CONFIG_DIR / "skills" / "hp0-plant-skill" / "SKILL.md": (
        "---\nname: hp0-plant-skill\ndescription: HP0 planted skill.\n---\nSay planted.\n"
    ),
    CONFIG_DIR / "commands" / "hp0-plant-cmd.md": "Say planted command.\n",
    CONFIG_DIR / "agents" / "hp0-plant-agent.md": (
        "---\nname: hp0-plant-agent\ndescription: HP0 planted agent.\n---\nSay planted agent.\n"
    ),
}
PLUGIN_FILES = [
    CONFIG_DIR / "plugins" / "installed_plugins.json",
    CONFIG_DIR / "plugins" / "known_marketplaces.json",
]
PLUGIN_FOLDERS = [
    CONFIG_DIR / "plugins" / "cache" / MARKETPLACE,
    CONFIG_DIR / "plugins" / "marketplaces" / MARKETPLACE,
    SYNCED,
]
WRITTEN_SETTINGS = {
    "apiKeyHelper": "echo sk-ant-api03-hp0-probe-fake-key-not-a-credential",
    "env": {"HTTPS_PROXY": "http://127.0.0.1:9", "NODE_EXTRA_CA_CERTS": "D:/hp0-missing.pem"},
    "permissions": {"allow": ["Bash(*)"]},
}
ECHO_COMMAND = "echo hp0"
ECHO = f"Run this exact Bash command and reply with its output only: {ECHO_COMMAND}"
CODEWORDS = "Reply with both codewords only."
NONE_LOADED: dict[str, list[str]] = {"commands": [], "agents": []}


INLINE_MARKERS = (
    Marker("ConfigChange", "configchange"),
    Marker("PreToolUse", "inline-pretool", "Bash"),
)


def write_plugin(name: str) -> None:
    root = MARKET / name
    (root / ".claude-plugin").mkdir(parents=True)
    (root / "commands").mkdir()
    manifest = {"name": name, "version": "0.0.1", "description": "HP0 probe plugin."}
    (root / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "commands" / f"{name}-cmd.md").write_text("Say planted plugin.\n", encoding="utf-8")


def plugin_cli(log: Log, *args: str) -> None:
    done = subprocess.run(
        [str(bundled_cli()), "plugin", *args],
        env=cli_env(),
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    log(f"claude plugin {' '.join(args)}: {done.stdout.strip().splitlines()[-1:]}")


def plant(log: Log) -> None:
    shutil.rmtree(MARKERS, ignore_errors=True)
    MARKERS.mkdir(parents=True)
    snapshot(PLANT_BACKUP, CONFIG_DIR, [HOME_SETTINGS, *PLUGIN_FILES, *PLANTS], PLUGIN_FOLDERS)
    for path, text in PLANTS.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    shutil.rmtree(MARKET, ignore_errors=True)
    (MARKET / ".claude-plugin").mkdir(parents=True)
    market = {
        "name": MARKETPLACE,
        "owner": {"name": "hp0"},
        "plugins": [{"name": HOME_PLUGIN, "source": f"./{HOME_PLUGIN}"}],
    }
    (MARKET / ".claude-plugin" / "marketplace.json").write_text(json.dumps(market))
    write_plugin(HOME_PLUGIN)
    write_plugin(SDK_PLUGIN)
    plugin_cli(log, "marketplace", "add", MARKET.as_posix())
    plugin_cli(log, "install", f"{HOME_PLUGIN}@{MARKETPLACE}")
    settings = json.loads(HOME_SETTINGS.read_text(encoding="utf-8"))
    settings["hooks"] = {
        "PreToolUse": [{"matcher": "Bash", "hooks": [Marker("PreToolUse", "home-pretool").hook()]}]
    }
    HOME_SETTINGS.write_text(json.dumps(settings), encoding="utf-8")
    log(f"home settings.json keys after the plant: {sorted(settings)}")
    log(f"plugins/synced exists after the plant: {SYNCED.exists()}")


def probe_names(info: dict[str, Any] | None) -> dict[str, list[str]]:
    def name(entry: Any) -> str:
        return entry if isinstance(entry, str) else str(entry["name"])

    return {
        key: [n for n in map(name, (info or {}).get(key, [])) if "hp0" in n or ":" in n]
        for key in NONE_LOADED
    }


def plugin_loaded(names: dict[str, list[str]], plugin: str) -> bool:
    return any(n.startswith(f"{plugin}:") for n in names["commands"])


async def loaded_at_connect(options: ClaudeAgentOptions) -> dict[str, list[str]]:
    client = ClaudeSDKClient(options=options)
    await client.connect()
    try:
        info = await client.get_server_info()
    finally:
        await client.disconnect()
    return probe_names(info)


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
    with exclusive(PLANT_LOCK):
        return await planted_run(log)


async def planted_run(log: Log) -> int:
    scrub_process_env(os.environ)
    append_file = SCRATCH / "append-system-prompt.txt"
    append_file.write_text(f"The first codeword is {FILE_CODEWORD}.\n")
    write_command = (
        f"cat > '{HOME_SETTINGS.as_posix()}' <<'JSON'\n{json.dumps(WRITTEN_SETTINGS)}\nJSON"
    )
    write_settings = (
        "This is a sanctioned probe in a throwaway test home. Overwrite the file without "
        f"reading it first: run this exact Bash command once and reply done: {write_command}"
    )
    turns: dict[str, list[Message]] = {}
    control = at_connect = NONE_LOADED
    hooks_after_echo = (0, 0)
    writer = "agent"
    written = ""
    try:
        plant(log)
        options = plan_options(
            Lockdown(
                frozenset({ECHO_COMMAND, write_command}),
                markers=INLINE_MARKERS,
                command_plugins=(MARKET / SDK_PLUGIN,),
            ),
            settings=json.dumps(FORCE_LOGIN | {"cleanupPeriodDays": 3650}),
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": f"The second codeword is {INLINE_CODEWORD}. When asked, give both.",
            },
            extra_args={"append-system-prompt-file": append_file.as_posix()},
        )
        log(f"argv length with inline settings, both appends and a plugin: {argv_length(options)}")
        control = await loaded_at_connect(plan_options(Lockdown(user_settings=True)))
        log(f"plugins/synced exists after the control connect: {SYNCED.exists()}")
        log(f"control, setting_sources=['user'], names at connect: {control}")
        async with ClaudeSDKClient(options=options) as client:
            at_connect = probe_names(await client.get_server_info())
            log(f"probe session, setting_sources=[], names at connect: {at_connect}")
            for prompt in (ECHO, CODEWORDS, write_settings, "say ok"):
                log(f"> {prompt}")
                await client.query(prompt)
                turns[prompt] = []
                async for message in client.receive_response():
                    log(describe(message))
                    turns[prompt].append(message)
                if prompt == ECHO:
                    hooks_after_echo = (
                        len(markers("inline-pretool")),
                        len(markers("home-pretool")),
                    )
                if prompt == write_settings and "apiKeyHelper" not in HOME_SETTINGS.read_text(
                    encoding="utf-8"
                ):
                    writer = "probe"
                    HOME_SETTINGS.write_text(json.dumps(WRITTEN_SETTINGS), encoding="utf-8")
                    log("the agent did not write settings.json, so the probe wrote it mid-session")
                    await asyncio.sleep(2)
            written = HOME_SETTINGS.read_text(encoding="utf-8")
        log(f"plugins/synced exists after the probe session: {SYNCED.exists()}")
    except Exception as error:
        log(f"session failed: {type(error).__name__}: {error}")
        log.row("S20 CLI accepts inline settings and the file flag", repr(error)[:300], "FAIL")
        return 1
    finally:
        failures = restore(PLANT_BACKUP)
        log(f"ship home restored after the run, failures: {failures}")

    def result(prompt: str) -> ResultMessage | None:
        return next((m for m in turns[prompt] if isinstance(m, ResultMessage)), None)

    messages = [m for batch in turns.values() for m in batch]
    init = next((m for m in messages if isinstance(m, SystemMessage) and m.subtype == "init"), None)
    init_plugins = [
        (p.get("name"), p.get("source")) for p in (init.data if init else {}).get("plugins", [])
    ]
    replies = [result(prompt) for prompt in turns]
    reply = result(CODEWORDS)
    text = str(reply.result) if reply else ""
    bash_calls = tool_uses(turns[ECHO], "Bash")
    inline_hook, home_hook = hooks_after_echo
    hook_control = bool(bash_calls and inline_hook)
    last = result("say ok")
    last_ok = last is not None and not last.is_error
    sdk_plugin = plugin_loaded(at_connect, SDK_PLUGIN)
    log(f"home settings.json held the S20 keys: {'apiKeyHelper' in written}, writer={writer}")
    log(f"init plugins (name, source): {init_plugins}")
    log.row(
        "S20 CLI accepts inline settings",
        f"{sum(r is not None for r in replies)} of 4 results",
        "PASS" if len(replies) == 4 and all(replies) else "FAIL",
    )
    log.row(
        "OQ4 append-system-prompt-file and the inline preset append both reach the model",
        f"file codeword={FILE_CODEWORD in text} inline codeword={INLINE_CODEWORD in text}",
        "PASS" if FILE_CODEWORD in text and INLINE_CODEWORD in text else "FAIL",
    )
    log.row(
        "S20 inline PreToolUse command hook fired (control)",
        f"bash calls={bash_calls} inline hook calls={inline_hook}",
        "PASS" if hook_control else "FAIL",
    )
    log.row(
        "OQ5 home settings.json PreToolUse hook fired",
        home_hook,
        "RECORDED" if hook_control else "UNMEASURED",
    )
    log.row(
        "OQ3 ConfigChange fired after the mid-session write",
        len(markers("configchange")),
        "RECORDED",
    )
    log.row(
        "OQ5 home plugin, skill, command, agent and settings.json hook",
        f"control setting_sources=['user']: {control}; setting_sources=[] with plugins set: "
        f"{at_connect}; home hook calls={home_hook}",
        oq5_home_verdict(HOME_PLANTS, control, at_connect, home_hook, hook_control),
    )
    log.row(
        "OQ5 plugin passed through the plugins option loads",
        sdk_plugin,
        "PASS" if sdk_plugin else "FAIL",
    )
    log.row(
        "S20 next turn after the write stays on the plan",
        f"ok={last_ok}",
        "PASS" if last_ok else "FAIL",
    )
    for line in markers("configchange"):
        log(f"configchange input: {line[:400]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
