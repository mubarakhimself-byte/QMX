"""Shared pieces of the HP0 probes. Standard library at import time; the SDK loads lazily.

Run every probe with the probe venv's Python that `p_install.py` builds, for example
`D:/QMX-worktrees/qma-ship/probe-venv/Scripts/python.exe scripts/probes/qma/p_env.py`.
"""

from __future__ import annotations

import json
import operator
import os
import re
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Generator, Iterable, Mapping, MutableMapping
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from enum import Enum
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, NamedTuple, TextIO, cast

from plants import Locked, heal

if TYPE_CHECKING:
    from claude_agent_sdk import (
        ClaudeAgentOptions,
        ClaudeSDKClient,
        ContentBlock,
        HookCallback,
        HookContext,
        HookInput,
        HookJSONOutput,
        Message,
    )

SHIP: Final = Path("D:/QMX-worktrees/qma-ship")
CONFIG_DIR: Final = SHIP / "home" / "claude"
EVIDENCE: Final = SHIP / "evidence" / "hp0" / os.environ.get("HP0_EVIDENCE_SUBDIR", "")
HP1_EVIDENCE: Final = SHIP / "evidence" / "hp1"
PROBE_VENV: Final = SHIP / "probe-venv"
SHIM_EXE: Final = PROBE_VENV / "Scripts" / "qma-cli-launcher.exe"
SCRATCH: Final = Path("D:/Temp/qma-hp0")
UV_CACHE: Final = Path("D:/Caches/uv")
FAKE_HOME: Final = SCRATCH / "home"
CHAT_CWD: Final = SCRATCH / "chat"
MARKERS: Final = SCRATCH / "settings-markers"
PLANT_BACKUP: Final = SCRATCH / "settings-plant-backup.json"
PLANT_LOCK: Final = SCRATCH / "settings-plant.lock"
CLI_FLOOR: Final = (2, 1, 248)
PROBE_MODEL: Final = "haiku"
FORCE_LOGIN: Final = {"forceLoginMethod": "claudeai"}
TIER_VARS: Final = (
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_FABLE_MODEL",
)

KEEP_NAMES: Final[frozenset[str]] = frozenset(
    {
        "PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TERM", "USER", "LOGNAME", "SHELL",
        "TMPDIR", "SSH_AUTH_SOCK",
        "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATHEXT", "USERPROFILE", "USERNAME",
        "USERDOMAIN", "COMPUTERNAME", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA",
        "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "COMMONPROGRAMFILES",
        "TEMP", "TMP", "OS", "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS",
        "CLAUDE_CODE_GIT_BASH_PATH",
        "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS", "DISPLAY", "WAYLAND_DISPLAY",
    }
)  # fmt: skip
"""The sketch's `boot.KEEP_NAMES` (DESIGN, `sketch/qma/boot.py`), copied verbatim."""

PROBE_KEEP: Final = KEEP_NAMES | {"CLAUDE_CONFIG_DIR"}


def reduced_env(environ: Mapping[str, str]) -> dict[str, str]:
    return {name: value for name, value in environ.items() if name.upper() in PROBE_KEEP}


def scrub_process_env(environ: MutableMapping[str, str]) -> tuple[str, ...]:
    """Reduce `environ` in place to `reduced_env`. Returns the removed names, never values.

    The SDK builds the CLI's environment from `os.environ` with `options.env` merged over
    it (02a trap 6), so a probe scrubs `os.environ` itself before it connects.
    """
    removed = sorted(name for name in environ if name.upper() not in PROBE_KEEP)
    for name in removed:
        del environ[name]
    return tuple(removed)


def parse_version(text: str) -> tuple[int, ...]:
    match = re.match(r"\d+(?:\.\d+)*", text.strip())
    if match is None:
        raise ValueError(f"no version in {text!r}")
    return tuple(int(part) for part in match[0].split("."))


def is_final_release(version: str) -> bool:
    return re.fullmatch(r"\d+(?:\.\d+)*", version) is not None


class Log:
    def __init__(self, slug: str, directory: Path | None = None) -> None:
        directory = directory or EVIDENCE
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / f"{slug}.log"
        self._secrets: list[str] = []
        self._file: TextIO = self.path.open("a", encoding="utf-8")
        self(f"=== {slug} {time.strftime('%Y-%m-%dT%H:%M:%S%z')} python {sys.version.split()[0]}")

    def redact(self, secret: str) -> None:
        self._secrets.append(secret)

    def __call__(self, line: str) -> None:
        for secret in self._secrets:
            line = line.replace(secret, "<redacted key>")
        print(line, flush=True)
        self._file.write(line + "\n")
        self._file.flush()

    def row(self, question: str, value: object, verdict: str) -> None:
        self(f"FINDING\t{question}\t{value}\t{verdict}")


def bundled_cli() -> Path:
    import claude_agent_sdk  # noqa: PLC0415

    exe = "claude.exe" if os.name == "nt" else "claude"
    return Path(claude_agent_sdk.__file__).parent / "_bundled" / exe


def sdk_version() -> str:
    from claude_agent_sdk import __version__  # noqa: PLC0415

    return __version__


def uv_env() -> dict[str, str]:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    return (
        {"UV_CACHE_DIR": str(UV_CACHE)}
        | dict(os.environ)
        | {"TMP": str(SCRATCH), "TEMP": str(SCRATCH)}
    )


def home_env() -> dict[str, str]:
    roaming, local = FAKE_HOME / "AppData" / "Roaming", FAKE_HOME / "AppData" / "Local"
    roaming.mkdir(parents=True, exist_ok=True)
    local.mkdir(parents=True, exist_ok=True)
    return {
        "CLAUDE_CONFIG_DIR": str(CONFIG_DIR),
        "HOME": str(FAKE_HOME),
        "USERPROFILE": str(FAKE_HOME),
        "APPDATA": str(roaming),
        "LOCALAPPDATA": str(local),
    }


def cli_env() -> dict[str, str]:
    return reduced_env(os.environ) | home_env()


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    model: str
    """Every tier alias is pinned to this one id. Kimi warns that a partial map fails silently."""
    quirks: Mapping[str, str] = field(default_factory=dict[str, str])

    @property
    def keyring_service(self) -> str:
        return f"qmx/{self.name}"


def provider_env(
    environ: Mapping[str, str], provider: Provider, secret: str, config_dir: Path
) -> dict[str, str]:
    """The CLI env for one provider launch. The base URL never goes out without its own
    token (02a trap 7), and `config_dir` must hold no plan login."""
    return (
        reduced_env(environ)
        | home_env()
        | {
            "CLAUDE_CONFIG_DIR": str(config_dir),
            "ANTHROPIC_BASE_URL": provider.base_url,
            "ANTHROPIC_AUTH_TOKEN": secret,
            "ANTHROPIC_API_KEY": "",
        }
        | dict.fromkeys(TIER_VARS, provider.model)
        | dict(provider.quirks)
    )


def read_key(provider: Provider) -> str | None:
    import keyring  # noqa: PLC0415

    return keyring.get_password(provider.keyring_service, provider.name)


def auth_method(cli: Path) -> dict[str, Any]:
    """Only the login fields of `claude auth status`. Never the email or org."""
    done = subprocess.run(
        [str(cli), "auth", "status"],
        env=cli_env(),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    try:
        status: dict[str, Any] = json.loads(done.stdout)
    except json.JSONDecodeError:
        return {"exit": done.returncode, "parsed": False}
    keep = ("loggedIn", "authMethod", "apiProvider", "subscriptionType")
    return {key: status.get(key) for key in keep}


def heal_ship_home(log: Log) -> None:
    try:
        failures = heal(PLANT_BACKUP, PLANT_LOCK)
    except Locked as error:
        failures = [str(error)]
    log(f"leftover plant restore failures before any CLI start: {failures}")
    if failures:
        log.row("ship home free of plants", failures, "BLOCKED")
        raise SystemExit(3)


def require_plan_login(log: Log, cli: Path) -> None:
    """Checks only that the credentials file exists, never its content, before any CLI start,
    so a probe run without the login leaves the ship home untouched."""
    heal_ship_home(log)
    status: dict[str, Any] = {"credentials_file": (CONFIG_DIR / ".credentials.json").exists()}
    if status["credentials_file"]:
        status = auth_method(cli)
    log(f"auth status fields: {status}")
    if not status.get("loggedIn") or status.get("apiProvider") not in (None, "firstParty"):
        log.row("plan login present", status, "BLOCKED")
        log("BLOCKED: run p_login.py with the operator at the keyboard first.")
        raise SystemExit(3)


@dataclass(frozen=True)
class Marker:
    event: str
    tag: str
    matcher: str | None = None

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z0-9-]+", self.tag):
            raise ValueError(
                f"a marker tag is lowercase letters, digits and dashes, not {self.tag!r}"
            )

    def hook(self) -> dict[str, str]:
        python = Path(sys.executable).as_posix()
        target = (MARKERS / f"{self.tag}.jsonl").as_posix()
        line = 'sys.stdin.read().replace(chr(10), " ") + chr(10)'
        program = f'import sys; open(r"{target}", "a").write({line})'
        return {"type": "command", "command": f"'{python}' -c '{program}'"}


@dataclass(frozen=True)
class Lockdown:
    """What one probe chat may run. The CLI gets only these built-in tools, and a PreToolUse
    hook denies every other call and every Bash command that is not exactly in `commands`.
    Probe chats run under the operator's own account, where Credential Manager holds the
    `qmx/*` broker keys, so a tool call no probe needs must never run."""

    commands: frozenset[str] = frozenset()
    tools: frozenset[str] = frozenset()
    markers: tuple[Marker, ...] = ()
    command_plugins: tuple[Path, ...] = ()
    user_settings: bool = False

    def __post_init__(self) -> None:
        if "Bash" in self.tools:
            raise ValueError("Bash is allowed only through exact commands")
        if self.user_settings and (
            self.commands or self.tools or self.markers or self.command_plugins
        ):
            raise ValueError("user settings load only into a chat that may run nothing")

    @property
    def builtins(self) -> list[str]:
        named = {tool for tool in self.tools if not tool.startswith("mcp__")}
        return sorted(named | ({"Bash"} if self.commands else set()))

    def refusal(self, tool: str, tool_input: Mapping[str, Any]) -> str | None:
        if tool != "Bash":
            return None if tool in self.tools else f"This probe chat may not use {tool}."
        if str(tool_input.get("command", "")).strip() in self.commands:
            return None
        return f"This probe chat may run only these exact Bash commands: {sorted(self.commands)}."


PROBE_SETTINGS: Final = frozenset({*FORCE_LOGIN, "cleanupPeriodDays"})
PLUGIN_MANIFEST: Final = frozenset({"name", "version", "description"})
COMMAND_FRONTMATTER: Final = frozenset({"description", "argument-hint"})
COMMAND_TEXT: Final = r"[\w\s.,;:'\"?()$\[\]\ufeff-]*"
"""No `!` (the CLI runs !`command` when it expands a command) and no `@` (a file mention)."""
PROBE_HOOK_EVENTS: Final = frozenset({"PreToolUse", "Stop"})


def deny(reason: str) -> HookJSONOutput:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def fail_closed(hook: HookCallback) -> HookCallback:
    """The CLI runs a tool whose PreToolUse hook raised, so a raise must become a deny."""

    async def run(
        hook_input: HookInput, tool_use_id: str | None, context: HookContext
    ) -> HookJSONOutput:
        try:
            return await hook(hook_input, tool_use_id, context)
        except Exception as error:
            return deny(
                f"A PreToolUse hook failed ({type(error).__name__}), so this call is denied."
            )

    return run


def deny_only(hook: HookCallback) -> HookCallback:
    async def run(
        hook_input: HookInput, tool_use_id: str | None, context: HookContext
    ) -> HookJSONOutput:
        output = cast("Mapping[str, Any]", await hook(hook_input, tool_use_id, context))
        if not output:
            return {}
        decision = cast("Mapping[str, Any]", output.get("hookSpecificOutput") or {})
        if decision.get("permissionDecision") == "deny":
            return deny(str(decision.get("permissionDecisionReason", "")))
        return deny("A probe hook may only deny a call; it returned allow or a changed input.")

    return fail_closed(run)


def guard(lockdown: Lockdown) -> HookCallback:
    async def deny_outside(
        hook_input: HookInput, _tool_use_id: str | None, _context: HookContext
    ) -> HookJSONOutput:
        call: Mapping[str, Any] = cast("Mapping[str, Any]", hook_input)
        reason = lockdown.refusal(str(call.get("tool_name", "")), call.get("tool_input") or {})
        return {} if reason is None else deny(reason)

    return deny_outside


def is_link(path: Path) -> bool:
    attributes: int = getattr(path.lstat(), "st_file_attributes", 0)
    return path.is_symlink() or bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def frontmatter_keys(text: str) -> set[str]:
    lines = text.lstrip("\ufeff \t\r\n").splitlines()
    if not lines or lines[0].strip() != "---":
        return set()
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        return {"<unclosed>"}
    return {
        key[1] if (key := re.match(r"([A-Za-z0-9_-]+):(\s|$)", line)) else f"<{line.strip()}>"
        for line in lines[1:end]
        if line.strip()
    }


def command_plugin(root: Path) -> dict[str, str]:
    def plain(folder: Path) -> dict[str, Path]:
        entries = {entry.name: entry for entry in folder.iterdir()}
        if linked := sorted(name for name, entry in entries.items() if is_link(entry)):
            raise TypeError(f"{folder.as_posix()} holds links {linked}")
        return entries

    if is_link(root):
        raise TypeError(f"{root.as_posix()} is a link")
    top = plain(root)
    meta, commands = root / ".claude-plugin", root / "commands"
    layout = sorted(top) == [".claude-plugin", "commands"] and meta.is_dir() and commands.is_dir()
    if not layout or sorted(plain(meta)) != ["plugin.json"] or not (meta / "plugin.json").is_file():
        raise TypeError(f"{root.as_posix()} holds more than a manifest and commands: {sorted(top)}")
    for command in plain(commands).values():
        if not (command.is_file() and command.suffix == ".md"):
            raise TypeError(f"{command.as_posix()} is not a command file")
        text = command.read_text("utf-8")
        if extra := sorted(frontmatter_keys(text) - COMMAND_FRONTMATTER):
            raise TypeError(f"{command.as_posix()} frontmatter may not set {extra}")
        if not re.fullmatch(COMMAND_TEXT, text):
            raise TypeError(f"{command.as_posix()} holds more than plain text")
    manifest = json.loads((meta / "plugin.json").read_text(encoding="utf-8"))
    if extra := sorted(manifest.keys() - PLUGIN_MANIFEST):
        raise TypeError(f"{root.as_posix()} manifest may not set {extra}")
    return {"type": "local", "path": root.as_posix()}


def settings_json(raw: str, markers: tuple[Marker, ...]) -> str:
    hooks: dict[str, list[dict[str, Any]]] = {}
    for marker in markers:
        matcher = {"matcher": marker.matcher} if marker.matcher else {}
        hooks.setdefault(marker.event, []).append(matcher | {"hooks": [marker.hook()]})
    return json.dumps(json.loads(raw) | ({"hooks": hooks} if hooks else {}))


def unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    if len({key for key, _ in pairs}) != len(pairs):
        raise ValueError("duplicate key")
    return dict(pairs)


def settings_refusal(raw: Any) -> str | None:
    settings: dict[str, Any] = json.loads(raw, object_pairs_hook=unique_keys)
    if extra := sorted(settings.keys() - PROBE_SETTINGS):
        return f"keys {extra}; hooks go through Lockdown.markers"
    days = settings.get("cleanupPeriodDays", 1)
    if settings.get("forceLoginMethod", "claudeai") != "claudeai" or type(days) is not int:
        return "forceLoginMethod is claudeai and cleanupPeriodDays a whole number"
    return None


def under_scratch(raw: str) -> bool:
    return SCRATCH.resolve() in Path(raw).resolve().parents


def bundled(raw: str) -> bool:
    return Path(raw) == bundled_cli()


def env_refusal(env: Any) -> str | None:
    home = home_env()
    rules: dict[str, Callable[[str], bool]] = {
        **{name: partial(operator.eq, os.environ.get(name)) for name in KEEP_NAMES - home.keys()},
        **{name: partial(operator.eq, home[name]) for name in home.keys() - {"CLAUDE_CONFIG_DIR"}},
        "CLAUDE_CONFIG_DIR": lambda raw: Path(raw) == CONFIG_DIR or under_scratch(raw),
        "ANTHROPIC_BASE_URL": partial(
            re.fullmatch, r"(https://[a-z0-9.-]+|http://127\.0\.0\.1:\d+)(/[\w./-]*)?"
        ),
        "ANTHROPIC_AUTH_TOKEN": bool,
        "CLAUDE_CODE_OAUTH_TOKEN": bool,
        "ANTHROPIC_API_KEY": partial(operator.eq, ""),
        **dict.fromkeys(TIER_VARS, partial(re.fullmatch, r"[\w./:-]+")),
        "CLAUDE_CODE_MAX_OUTPUT_TOKENS": str.isdecimal,
        "MAX_THINKING_TOKENS": str.isdecimal,
        "ENABLE_TOOL_SEARCH": {"true", "false"}.__contains__,
        "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": partial(operator.eq, "1"),
        "QMA_CLI_PATH": bundled,
        "QMA_CHAT_ID": partial(re.fullmatch, r"[a-z0-9-]+"),
    }

    def allowed(name: str, value: object) -> bool:
        rule = rules.get(name)
        return rule is not None and isinstance(value, str) and bool(rule(value))

    if refused := sorted(name for name, value in dict(env).items() if not allowed(name, value)):
        return f"names or values {refused}"
    return None


def only(test: Callable[[Any], object], wanted: str) -> Callable[[Any], str | None]:
    return lambda value: None if test(value) else f"it must be {wanted}"


class Rule(Enum):
    LOCKED = "the lockdown sets it"
    REFUSED = "no probe needs it"


OPTION_RULES: Final[Mapping[str, Rule | Callable[[Any], str | None]]] = {
    "tools": Rule.LOCKED,
    "allowed_tools": Rule.LOCKED,
    "cwd": Rule.LOCKED,
    "permission_mode": Rule.LOCKED,
    "can_use_tool": Rule.LOCKED,
    "add_dirs": Rule.LOCKED,
    "setting_sources": Rule.LOCKED,
    "plugins": Rule.LOCKED,
    "strict_mcp_config": Rule.LOCKED,
    "env": env_refusal,
    "settings": settings_refusal,
    "hooks": only(
        lambda hooks: (
            hooks.keys() <= PROBE_HOOK_EVENTS
            and all(callable(h) for matchers in hooks.values() for m in matchers for h in m.hooks)
        ),
        f"callbacks on {sorted(PROBE_HOOK_EVENTS)}",
    ),
    "extra_args": only(
        lambda args: (
            args.keys() <= {"append-system-prompt-file"}
            and all(under_scratch(path) for path in args.values())
        ),
        f"append-system-prompt-file with a file under {SCRATCH.as_posix()}",
    ),
    "system_prompt": only(
        lambda prompt: (
            isinstance(prompt, str)
            or (
                prompt.keys() <= {"type", "preset", "append"}
                and (prompt["type"], prompt["preset"]) == ("preset", "claude_code")
                and isinstance(prompt.get("append", ""), str)
            )
        ),
        "text or the claude_code preset with an append",
    ),
    "mcp_servers": only(
        lambda servers: all(
            re.fullmatch(r"[a-z0-9_-]+", name) and config["type"] == "sdk"
            for name, config in servers.items()
        ),
        "in-process SDK servers",
    ),
    "cli_path": only(lambda path: Path(path) == SHIM_EXE, f"the shim {SHIM_EXE.as_posix()}"),
    "model": only({"haiku", "sonnet"}.__contains__, "haiku or sonnet"),
    "max_turns": only(lambda turns: type(turns) is int and 1 <= turns <= 8, "1 to 8"),
    "resume": only(partial(re.fullmatch, r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}"), "a UUID"),
    "thinking": only(
        lambda thinking: (
            thinking in ({"type": "adaptive"}, {"type": "disabled"})
            or (
                thinking.keys() == {"type", "budget_tokens"}
                and thinking["type"] == "enabled"
                and type(thinking["budget_tokens"]) is int
                and 1024 <= thinking["budget_tokens"] <= 16000
            )
        ),
        "adaptive, disabled, or enabled with 1024 to 16000 budget tokens",
    ),
    "effort": only({"low", "medium", "high", "xhigh", "max"}.__contains__, "an effort level"),
    "verbatim_prompts": only(lambda flag: type(flag) is bool, "a bool"),
    "include_partial_messages": only(lambda flag: type(flag) is bool, "a bool"),
    **dict.fromkeys(
        (
            "continue_conversation",
            "session_id",
            "max_budget_usd",
            "disallowed_tools",
            "fallback_model",
            "betas",
            "permission_prompt_tool_name",
            "max_buffer_size",
            "debug_stderr",
            "stderr",
            "user",
            "include_hook_events",
            "forward_subagent_text",
            "fork_session",
            "resume_session_at",
            "resume_drops_turn",
            "agents",
            "skills",
            "sandbox",
            "max_thinking_tokens",
            "output_format",
            "enable_file_checkpointing",
            "session_store",
            "session_store_flush",
            "load_timeout_ms",
            "task_budget",
        ),
        Rule.REFUSED,
    ),
}


def option_refusal(name: str, value: Any) -> str | None:
    rule = OPTION_RULES.get(name, Rule.REFUSED)
    if isinstance(rule, Rule):
        return rule.value
    try:
        return rule(value)
    except Exception as error:
        return f"its value could not be read ({type(error).__name__})"


def plan_options(lockdown: Lockdown, **overrides: Any) -> ClaudeAgentOptions:
    for name, value in overrides.items():
        if reason := option_refusal(name, value):
            raise TypeError(f"a probe may not set {name}: {reason}")
    settings = settings_json(overrides.pop("settings", json.dumps(FORCE_LOGIN)), lockdown.markers)
    plugins = [command_plugin(root) for root in lockdown.command_plugins]
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher  # noqa: PLC0415

    probe_hooks: dict[str, list[HookMatcher]] = dict(overrides.pop("hooks", {}))
    CHAT_CWD.mkdir(parents=True, exist_ok=True)
    probe_pre = [
        replace(matcher, hooks=[deny_only(hook) for hook in matcher.hooks])
        for matcher in probe_hooks.get("PreToolUse", [])
    ]
    hooks = probe_hooks | {
        "PreToolUse": [HookMatcher(hooks=[fail_closed(guard(lockdown))]), *probe_pre]
    }
    kwargs: dict[str, Any] = {
        "env": home_env(),
        "setting_sources": ["user"] if lockdown.user_settings else [],
        "settings": settings,
        "plugins": plugins,
        "strict_mcp_config": True,
        "model": PROBE_MODEL,
        "cwd": str(CHAT_CWD),
        "tools": lockdown.builtins,
        "hooks": hooks,
        "permission_mode": "bypassPermissions",
        "max_turns": 4,
    }
    return ClaudeAgentOptions(**(kwargs | overrides))


def describe(message: Message) -> str:
    from claude_agent_sdk import (  # noqa: PLC0415
        AssistantMessage,
        RateLimitEvent,
        ResultMessage,
        SystemMessage,
        UserMessage,
    )

    match message:
        case RateLimitEvent(rate_limit_info=info):
            return f"RateLimitEvent status={info.status} type={info.rate_limit_type}"
        case ResultMessage():
            return (
                f"ResultMessage subtype={message.subtype} is_error={message.is_error} "
                f"turns={message.num_turns} ms={message.duration_ms} "
                f"result={message.result!r:.200}"
            )
        case SystemMessage():
            return f"SystemMessage subtype={message.subtype}"
        case AssistantMessage():
            return f"AssistantMessage model={message.model} blocks={_blocks(message.content)}"
        case UserMessage(content=list() as content):
            return f"UserMessage blocks={_blocks(content)}"
        case _:
            return type(message).__name__


def _blocks(blocks: list[ContentBlock]) -> list[str]:
    from claude_agent_sdk import (  # noqa: PLC0415
        TextBlock,
        ThinkingBlock,
        ToolResultBlock,
        ToolUseBlock,
    )

    def one(block: ContentBlock) -> str:
        match block:
            case TextBlock():
                return f"Text({block.text!r:.200})"
            case ThinkingBlock():
                return f"Thinking(signed={bool(block.signature)})"
            case ToolUseBlock():
                return f"ToolUse({block.name} {json.dumps(block.input)[:200]})"
            case ToolResultBlock():
                return f"ToolResult(error={block.is_error} {str(block.content)[:300]!r})"
            case _:
                return type(block).__name__

    return [one(block) for block in blocks]


def tool_uses(messages: list[Message], name: str) -> int:
    from claude_agent_sdk import AssistantMessage, ToolUseBlock  # noqa: PLC0415

    return sum(
        isinstance(block, ToolUseBlock) and block.name == name
        for m in messages
        if isinstance(m, AssistantMessage)
        for block in m.content
    )


def tool_results(messages: list[Message]) -> list[str]:
    from claude_agent_sdk import ToolResultBlock, UserMessage  # noqa: PLC0415

    def text(content: str | list[dict[str, Any]] | None) -> str:
        if isinstance(content, list):
            return "\n".join(str(part.get("text", "")) for part in content)
        return content or ""

    return [
        text(block.content)
        for m in messages
        if isinstance(m, UserMessage) and isinstance(m.content, list)
        for block in m.content
        if isinstance(block, ToolResultBlock)
    ]


def is_ok(messages: list[Message]) -> bool:
    from claude_agent_sdk import ResultMessage  # noqa: PLC0415

    results = [m for m in messages if isinstance(m, ResultMessage)]
    return bool(results) and not results[-1].is_error


@contextmanager
def tap_raw(log: Log) -> Generator[None]:
    """Log every frame the CLI sends, cut to 800 characters, before the SDK parses or drops it."""
    from claude_agent_sdk._internal import message_parser  # noqa: PLC0415

    parse = message_parser.parse_message

    def logged(data: dict[str, Any]) -> Message | None:
        log(f"raw {json.dumps(data)[:800]}")
        return parse(data)

    message_parser.parse_message = logged
    try:
        yield
    finally:
        message_parser.parse_message = parse


async def run_turns(log: Log, options: ClaudeAgentOptions, prompts: list[str]) -> list[Message]:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    seen: list[Message] = []
    async with ClaudeSDKClient(options=options) as client:
        for prompt in prompts:
            log(f"> {prompt}")
            await client.query(prompt)
            async for message in client.receive_response():
                log(describe(message))
                seen.append(message)
    return seen


def cli_pid(client: ClaudeSDKClient) -> int:
    transport: Any = client._transport  # pyright: ignore[reportPrivateUsage]
    return int(transport._process.pid)


class Memory(NamedTuple):
    working_set: float
    commit: float
    """Private committed memory (`PagefileUsage`), what a job memory limit counts."""


def memory_mb(pid: int) -> Memory:
    import ctypes  # noqa: PLC0415
    from ctypes import wintypes  # noqa: PLC0415

    class Counters(ctypes.Structure):
        _fields_ = (
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        )

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    query_limited_and_vm_read = 0x1000 | 0x0010
    handle = kernel32.OpenProcess(query_limited_and_vm_read, False, pid)
    if not handle:
        raise OSError(ctypes.get_last_error(), f"OpenProcess {pid}")
    try:
        counters = Counters()
        counters.cb = ctypes.sizeof(Counters)
        if not kernel32.K32GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            raise OSError(ctypes.get_last_error(), f"K32GetProcessMemoryInfo {pid}")
        return Memory(
            round(counters.WorkingSetSize / 2**20, 1), round(counters.PagefileUsage / 2**20, 1)
        )
    finally:
        kernel32.CloseHandle(handle)


def s19_scrub_verdict(
    planted: Iterable[str], removed: Iterable[str], bash_calls: int, ok: bool, listing: set[str]
) -> tuple[list[str], str]:
    leaked = [name for name in planted if name in listing]
    scrubbed = set(planted) <= set(removed)
    return leaked, "PASS" if bash_calls and ok and scrubbed and not leaked else "FAIL"


def s38_verdict(bash_calls: int, timeout_texts: int, ran: bool) -> str:
    return "PASS" if bash_calls and timeout_texts and not ran else "FAIL"


def s25_verdict(control: bool, answered: bool, turns: int, boundary: bool) -> str:
    return "PASS" if control and answered and turns >= 1 and not boundary else "FAIL"


def oq5_home_verdict(
    planted: frozenset[str],
    control: Mapping[str, Iterable[str]],
    probe: Mapping[str, Iterable[str]],
    home_hook: int,
    hook_control: bool,
) -> str:
    def loaded(names: Mapping[str, Iterable[str]]) -> set[str]:
        return {n.partition(":")[0] for group in names.values() for n in group} & planted

    if loaded(probe) or home_hook:
        return "FAIL"
    return "PASS" if loaded(control) >= planted and hook_control else "UNMEASURED"
