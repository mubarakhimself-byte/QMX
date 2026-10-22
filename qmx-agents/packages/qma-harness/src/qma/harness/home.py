"""QMX's own Claude homes, the Claude settings QMA passes in code, and on-disk chat state.

Layout under the QMX home, never under the operator's `~/.claude`:

    claude/                  Plan home. CLAUDE_CONFIG_DIR for plan chats; the CLI keeps the
                             plan login and the transcripts here.
    claude-relayed/          Relayed home for key and GPT chats. It never holds a login. Its
                             `projects/` links to `claude/projects/`, so a provider switch
                             still resumes the same transcript.
    chats/<session>.json     One `ChatRecord` per chat. Each chat writes only its own.
    procs/<session>.json     Pid file, written only by that chat's launcher.
    state/                   Correctness records such as the GPT probe result.
    workspaces/              Default working folders, outside any dev repo.
    agent-memory/<ws>/       Auto memory per workspace (`autoMemoryDirectory`).

Settings in code. QMA writes no settings file the CLI loads, and `setting_sources=[]` loads
none from either home. Every Claude setting reaches the CLI as one inline JSON string
(`code_settings`), so nothing an agent edits during a session changes it. The operator's part
lives in `settings.toml [claude]`, written only through `ControlService` after
`parse_claude_settings` accepts it, and parsed again at every launch. The fixed values win.
"""

from __future__ import annotations

import contextlib
import copy
import functools
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from importlib.metadata import version
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Literal, cast

from claude_agent_sdk import PermissionResultDeny
from qmx_control.context import AttachedRef
from qmx_router.ids import SessionId
from qmx_router.profiles import PLAN, ProfileName, parse_profiles

from qma.boot import banned_fragment
from qma.harness import packs
from qma.harness.guard import SECRET_SHAPES
from qma.harness.launch import (
    ARGV_BUDGET,
    Background,
    Budgets,
    ChatConfig,
    ChatKind,
    ChatPermissions,
    Child,
    Home,
    Interactive,
    LaunchRefused,
    PlanLaunch,
    SubAgent,
    argv_length,
    build_options,
    launch_env,
)
from qma.harness.surface import SLOTS_PLUGIN, HomeSlots, Supply, build, declaration
from qma.harness.tools import DEFAULT_DOMAIN_WRITE, SERVER, SERVER_NAME, guard_rules
from qma.launcher import BLOCK_CONFIG_CHANGE, bundled_cli, is_chat_id

if TYPE_CHECKING:
    from claude_agent_sdk.types import PermissionResult, ToolPermissionContext
    from qmx_control.models import Document
    from qmx_control.service import ControlService


PLUGIN_DIR: Final = Path(__file__).resolve().parents[5] / "plugin"
"""`qmx-agents/plugin/`, QMX's shipped skills, agents, commands and rules."""


plugin_digest: Final = packs.folder_digest
"""The digest of a plugin folder, under the name the live lanes call it by."""


def plugin_refusal(home: QmxHome) -> str | None:
    """Why this launch may not load `home.plugin_dir`, or None. A `!` shell line in a command,
    skill or agent body runs outside every hook, so the gate never sees it. Otherwise the folder
    is checked against its manifest, or against `plugin_sha256` when a lane is testing a plugin
    of its own."""
    folder = home.plugin_dir
    for path in sorted(folder.rglob("*.md")):
        if "!`" in path.read_text(encoding="utf-8", errors="replace"):
            name = path.relative_to(folder).as_posix()
            return f"the QMX plugin runs shell lines outside every hook ({name})"
    if home.plugin_sha256 is None:
        return packs.manifest_refusal(folder)
    found = plugin_digest(folder)
    if found != home.plugin_sha256:
        return (
            f"the QMX plugin at {folder} changed since it shipped (sha256 {found}, shipped "
            f"{home.plugin_sha256}); restore it from git"
        )
    return None


def session_id(text: str) -> SessionId:
    if not is_chat_id(text):
        raise ValueError(f"{text!r} is not a session id")
    return SessionId(text)


@dataclass(frozen=True)
class QmxHome:
    root: Path
    plugin_dir: Path = PLUGIN_DIR
    plugin_sha256: str | None = None
    """What `plugin_digest(plugin_dir)` must be at each launch. None checks the shipped
    `plugin.manifest.json` instead, which names the file that changed; a live lane testing a
    plugin of its own passes that folder's own digest here."""

    @property
    def plan_dir(self) -> Path:
        return self.root / "claude"

    @property
    def packs_dir(self) -> Path:
        """Where each pack's materialised plugin view sits, one folder per pack."""
        return self.root / "plugins"

    @property
    def relayed_dir(self) -> Path:
        return self.root / "claude-relayed"

    @property
    def chats_dir(self) -> Path:
        return self.root / "chats"

    @property
    def procs_dir(self) -> Path:
        return self.root / "procs"

    @property
    def state_dir(self) -> Path:
        return self.root / "state"

    @property
    def workspaces_dir(self) -> Path:
        return self.root / "workspaces"

    @property
    def agent_memory_dir(self) -> Path:
        return self.root / "agent-memory"

    def launch_dir(self, chat: SessionId) -> Path:
        """The settings and system text files of the chat's current launch. Under `chats/`,
        which the gate protects, so no agent edits what its next launch reads."""
        return self.chats_dir / chat

    def memory_dir(self, workspace: Path) -> Path:
        """Auto memory for launches in `workspace`. Not a protected path, so agents read and
        write it as in vanilla."""
        key = workspace_key(workspace)
        slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", Path(key).name).strip("-.") or "root"
        return self.agent_memory_dir / f"{slug}-{hashlib.sha256(key.encode()).hexdigest()[:12]}"


def workspace_key(workspace: Path) -> str:
    """One spelling per folder: resolved, forward slashes, casefolded where paths are."""
    key = workspace.resolve().as_posix()
    return key.casefold() if sys.platform in ("win32", "darwin") else key


LOGIN_FILES: Final = (".credentials.json",)


def relayed_logins(home: QmxHome) -> list[Path]:
    return [path for path in (home.relayed_dir / name for name in LOGIN_FILES) if path.exists()]


def _inside_personal_claude(path: Path) -> bool:
    return path.resolve().is_relative_to((Path.home() / ".claude").resolve())


def ensure_homes(home: QmxHome) -> None:
    """Create both homes, the state folders and the relayed `projects/` link. Idempotent.
    Refuses a home inside the operator's `~/.claude` and a login file in the relayed home."""
    for claude_home in (home.plan_dir, home.relayed_dir):
        if _inside_personal_claude(claude_home):
            raise LaunchRefused(f"{claude_home} is inside the operator's own ~/.claude")
    for folder in (
        home.plan_dir / "projects",
        home.relayed_dir,
        home.chats_dir,
        home.procs_dir,
        home.state_dir,
        home.workspaces_dir,
    ):
        folder.mkdir(parents=True, exist_ok=True)
    _link_projects(home.relayed_dir / "projects", home.plan_dir / "projects")
    found = relayed_logins(home)
    if found:
        raise LaunchRefused(f"the relayed home holds a login file: {found[0]}")


def _link_projects(link: Path, target: Path) -> None:
    if link.is_junction() or link.is_symlink():
        if link.resolve() == target.resolve():
            return
        raise LaunchRefused(f"{link} links to {link.resolve()}, not {target}")
    if link.exists():
        try:
            link.rmdir()
        except OSError as error:
            raise LaunchRefused(f"{link} is a folder with content, not a link") from error
    if sys.platform == "win32":
        import _winapi  # noqa: PLC0415

        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)


CLAUDE_SETTING_KEYS: Final[frozenset[str]] = frozenset(
    {
        "permissions", "env", "hooks",
        "outputStyle", "attribution", "includeCoAuthoredBy", "alwaysThinkingEnabled",
        "language", "respectGitignore",
        "remembered", "external_tools_unattended",
    }
)  # fmt: skip
"""Top-level keys allowed in `settings.toml [claude]`. Everything else refuses, including
`apiKeyHelper`, `forceLoginMethod`, `disableAllHooks`, `enabledPlugins`, marketplaces and
`model`. `remembered` is QMX's, never passed through as is: per-workspace "always allow"
rules merged into `permissions.allow` only for launches in that workspace.
`external_tools_unattended` is QMX's too: the `server/tool` and `server/*` entries whose
external MCP tools may run in an unattended chat or mode (`guard.GuardRules`). Neither reaches
the CLI."""

QMX_ONLY_KEYS: Final = frozenset({"remembered", "external_tools_unattended"})

PERMISSION_KEYS: Final = frozenset({"allow", "ask", "deny", "additionalDirectories"})

CLAUDE_ENV_NAMES: Final[frozenset[str]] = frozenset(
    {
        "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH",
        "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS",
        "BASH_DEFAULT_TIMEOUT_MS",
        "BASH_MAX_TIMEOUT_MS",
        "MCP_TOOL_TIMEOUT",
        "CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS",
    }
)
"""The only names allowed under `[claude] env`. No routing, proxy, CA or wrapper name."""

_HOOK_COMMON: Final = frozenset({"type", "if", "timeout", "statusMessage", "once"})
HOOK_KEYS: Final[Mapping[str, frozenset[str]]] = {
    "command": _HOOK_COMMON | {"command", "args", "async", "asyncRewake", "shell", "onFailure"},
    "http": _HOOK_COMMON | {"url", "headers", "allowedEnvVars", "onFailure"},
    "prompt": _HOOK_COMMON | {"prompt", "model", "continueOnBlock"},
    "agent": _HOOK_COMMON | {"prompt", "model"},
}
"""Hook handler keys per type, as https://code.claude.com/docs/en/hooks documents them."""
HEADER_VALUE: Final = re.compile(r"(Bearer |Basic )?\$(\{[A-Z_][A-Z0-9_]*\}|[A-Z_][A-Z0-9_]*)")
HOOK_URL: Final = re.compile(r"https?://[^\s\\/?#@]+(?:[/?#]\S*)?")
"""An http hook url. No user info, backslash or whitespace, so no URL parser can read a
credential out of it."""
ATTRIBUTION_KEYS: Final[Mapping[str, type]] = {"commit": str, "pr": str, "sessionUrl": bool}
"""`attribution` sub-keys, as https://code.claude.com/docs/en/settings-reference documents them."""
SET: Final = "<set>"
TEXT_KEYS: Final = frozenset({"outputStyle", "language"})
FLAG_KEYS: Final = frozenset({"includeCoAuthoredBy", "alwaysThinkingEnabled", "respectGitignore"})

CLEANUP_PERIOD_DAYS: Final = 3650
"""Transcripts outlive the CLI's 30-day sweep. The settings reference rejects `0`."""
SPAWN_DEPTH_DEFAULT: Final = "1"

_RULE = re.compile(r"[A-Za-z][\w-]*(?:\(.+\))?", re.DOTALL)


@dataclass(frozen=True)
class ClaudeSettings:
    """The validated `settings.toml [claude]` section."""

    raw: Mapping[str, object] = field(default_factory=dict[str, object])

    @property
    def external_tools_unattended(self) -> frozenset[str]:
        return frozenset(cast("list[str]", self.raw.get("external_tools_unattended", [])))

    def remembered(self, workspace: Path) -> list[str]:
        table = cast("Mapping[str, Mapping[str, list[str]]]", self.raw.get("remembered", {}))
        return list(table.get(workspace_key(workspace), {}).get("allow", []))


def _refuse(key: str, why: str) -> LaunchRefused:
    return LaunchRefused(f"[claude] {key} {why}")


def _strings(value: object, key: str, check: re.Pattern[str] | None = None) -> None:
    if not isinstance(value, list):
        raise _refuse(key, "must be a list of strings")
    for item in cast("list[object]", value):
        if not isinstance(item, str):
            raise _refuse(key, f"holds {item!r}, which is not a string")
        if check is not None and not check.fullmatch(item):
            raise _refuse(key, f"holds {item!r}, which is not a permission rule")


def _table(value: object, key: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise _refuse(key, "must be a table")
    return cast("dict[str, object]", value)


_EXTERNAL_ENTRY = re.compile(rf"({SERVER_NAME.pattern})/(\*|[A-Za-z0-9_.-]+)")


def _external_entries(value: object) -> None:
    key = "external_tools_unattended"
    _strings(value, key)
    for entry in cast("list[str]", value):
        found = _EXTERNAL_ENTRY.fullmatch(entry)
        if found is None:
            raise _refuse(key, f"holds {entry!r}, which is not server/tool or server/*")
        if found.group(1) == SERVER:
            raise _refuse(key, f"holds {entry!r}; QMX's own tools follow their effect table")


def _hooks(value: object) -> None:
    for event, groups in _table(value, "hooks").items():
        if not isinstance(groups, list):
            raise _refuse(f"hooks.{event}", "must be a list of matcher groups")
        for group in cast("list[object]", groups):
            entry = _table(group, f"hooks.{event}")
            if set(entry) - {"matcher", "hooks"} or not isinstance(entry.get("hooks"), list):
                raise _refuse(f"hooks.{event}", "needs a hooks list and an optional matcher")
            for hook in cast("list[object]", entry["hooks"]):
                table = _table(hook, f"hooks.{event}")
                kind = table.get("type")
                if not isinstance(kind, str) or kind not in HOOK_KEYS:
                    raise _refuse(f"hooks.{event}", f"hook types are {sorted(HOOK_KEYS)}")
                unknown = sorted(table.keys() - HOOK_KEYS[kind])
                if unknown:
                    raise _refuse(f"hooks.{event} {kind} hook key {unknown[0]}", "is not allowed")
                if "headers" in table:
                    _headers(table["headers"], f"hooks.{event}")
                url = table.get("url")
                if "url" in table and not (isinstance(url, str) and HOOK_URL.fullmatch(url)):
                    raise _refuse(
                        f"hooks.{event} {kind} hook url",
                        "must be http(s)://host[/path] with no user, password, backslash or "
                        "whitespace; put a credential in a $NAME header",
                    )


def _headers(value: object, key: str) -> None:
    for name, text in _table(value, f"{key} headers").items():
        if not isinstance(text, str) or not HEADER_VALUE.fullmatch(text):
            raise _refuse(
                f"{key} header {name}", "must be $NAME or ${NAME}, optionally after Bearer or Basic"
            )


def parse_claude_settings(raw: Mapping[str, object]) -> ClaudeSettings:
    """Allow-list validation. Raises `LaunchRefused` naming the first key that is not allowed."""
    parsed: dict[str, object] = {}
    for key, value in raw.items():
        if key not in CLAUDE_SETTING_KEYS:
            raise _refuse(key, "is not allowed")
        if key == "permissions":
            table = _table(value, key)
            for name, rules in table.items():
                if name not in PERMISSION_KEYS:
                    raise _refuse(f"permissions.{name}", "is not allowed")
                check = None if name == "additionalDirectories" else _RULE
                _strings(rules, f"permissions.{name}", check)
        elif key == "env":
            for name, setting in _table(value, key).items():
                if name not in CLAUDE_ENV_NAMES:
                    raise _refuse(f"env.{name}", "is not allowed")
                if not isinstance(setting, str):
                    raise _refuse(f"env.{name}", "must be a string")
        elif key == "hooks":
            _hooks(value)
        elif key == "external_tools_unattended":
            _external_entries(value)
        elif key == "remembered":
            for workspace, rules in _table(value, key).items():
                entry = _table(rules, f"remembered.{workspace}")
                if set(entry) != {"allow"}:
                    raise _refuse(f"remembered.{workspace}", "holds only an allow list")
                _strings(entry["allow"], f"remembered.{workspace}.allow", _RULE)
        elif key == "attribution" and value is not False:
            if not isinstance(value, dict):
                raise _refuse(key, "must be a table or false")
            for name, setting in cast("dict[str, object]", value).items():
                kind = ATTRIBUTION_KEYS.get(name)
                if kind is None:
                    raise _refuse(f"attribution.{name}", "is not allowed")
                if not isinstance(setting, kind):
                    why = "must be a string" if kind is str else "must be true or false"
                    raise _refuse(f"attribution.{name}", why)
        elif key in TEXT_KEYS and not isinstance(value, str):
            raise _refuse(key, "must be a string")
        elif key in FLAG_KEYS and not isinstance(value, bool):
            raise _refuse(key, "must be true or false")
        parsed[key] = value
    try:
        return ClaudeSettings(json.loads(json.dumps(parsed)))
    except TypeError as error:
        raise LaunchRefused(f"[claude] holds a value JSON cannot carry: {error}") from error


def config_change_hook(launcher: Path) -> dict[str, object]:
    """Blocks every settings change the CLI lets a hook block. No matcher, so every source."""
    return {
        "hooks": [
            {
                "type": "command",
                "command": f"'{launcher.as_posix()}' {BLOCK_CONFIG_CHANGE}",
                "timeout": 10,
            }
        ]
    }


def code_settings(
    user: ClaudeSettings,
    *,
    launcher: Path,
    workspace: Path,
    memory_dir: Path,
    allow: Sequence[str] = (),
    deny: Sequence[str] = (),
    claude_hooks: Mapping[str, object] = MappingProxyType({}),
    auto_memory: bool = True,
) -> str:
    """The settings document of one launch, as JSON, rendered per launch. Pure.
    The operator's keys, the workspace's remembered rules and the chat's own `allow`, `deny`
    and `claude_hooks`, then the fixed values, which win."""
    document: dict[str, Any] = {
        key: value
        for key, value in json.loads(json.dumps(user.raw)).items()
        if key not in QMX_ONLY_KEYS
    }
    for name, rules in (("allow", [*user.remembered(workspace), *allow]), ("deny", deny)):
        if rules:
            permissions: dict[str, Any] = document.setdefault("permissions", {})
            listed: list[str] = permissions.setdefault(name, [])
            listed.extend(rule for rule in rules if rule not in listed)
    document["env"] = {
        "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": SPAWN_DEPTH_DEFAULT,
        **document.get("env", {}),
    }
    hooks: dict[str, list[Any]] = {
        event: list(groups) for event, groups in document.get("hooks", {}).items()
    }
    for event, groups in json.loads(json.dumps(dict(claude_hooks))).items():
        hooks.setdefault(event, []).extend(groups)
    document["hooks"] = {**hooks, "ConfigChange": [config_change_hook(launcher)]}
    document |= {
        "forceLoginMethod": "claudeai",
        "cleanupPeriodDays": CLEANUP_PERIOD_DAYS,
        "autoMemoryDirectory": memory_dir.as_posix(),
    }
    if not auto_memory:
        document["autoMemoryEnabled"] = False
    return json.dumps(document, sort_keys=True, separators=(",", ":"))


def check_hooks(value: Mapping[str, object]) -> None:
    """Refuse hooks outside the settings `hooks` shape or with a key `HOOK_KEYS` does not list."""
    _hooks(dict(value))


def check_rules(rules: Sequence[str], key: str) -> None:
    """Refuse an entry that is not a permission rule."""
    _strings(list(rules), key, _RULE)


CREDENTIAL_NAME: Final = re.compile(r"(?i)key|token|secret|passw|auth|credential|bearer|cookie")
"""A name under which a value is a credential, so the value must be a keyring reference."""
KEYRING_REF: Final = re.compile(r"qmx/[A-Za-z0-9._/-]+")
MASK: Final = "[redacted]"


def _secret_paths(value: object, path: str) -> Iterator[str]:
    """Where in `value` a string, key or value, has a key's shape."""
    match value:
        case str() if SECRET_SHAPES.search(value):
            yield path
        case Mapping():
            for key, item in cast("Mapping[object, object]", value).items():
                yield from _secret_paths(str(key), path)
                yield from _secret_paths(item, f"{path}.{key}")
        case list() | tuple():
            for n, item in enumerate(cast("Sequence[object]", value)):
                yield from _secret_paths(item, f"{path}[{n}]")
        case _:
            return


def _literal_credentials(table: object, path: str) -> Iterator[str]:
    """Credential-named entries of `table` whose value is not a `qmx/*` keyring reference."""
    if not isinstance(table, Mapping):
        return
    for name, value in cast("Mapping[object, object]", table).items():
        if CREDENTIAL_NAME.search(str(name)) and not (
            isinstance(value, str) and KEYRING_REF.fullmatch(value)
        ):
            yield f"{path}.{name}"


def check_secrets(
    mcp_servers: Mapping[str, object],
    policy_args: Mapping[str, object],
    claude_hooks: Mapping[str, object],
) -> None:
    """Refuse chat options that would put a literal secret on the chat record: any string with
    a key's shape, and any credential-named server `env` or `headers` entry, server
    `credential_ref` or policy argument that is not a `qmx/*` keyring reference."""
    found = [
        *_secret_paths(dict(mcp_servers), "mcp_servers"),
        *_secret_paths(dict(policy_args), "policy_args"),
        *_secret_paths(dict(claude_hooks), "claude_hooks"),
        *_literal_credentials(policy_args, "policy_args"),
    ]
    for name, row in mcp_servers.items():
        if isinstance(row, Mapping):
            server = cast("Mapping[str, object]", row)
            for table in ("env", "headers"):
                found += _literal_credentials(server.get(table), f"mcp_servers.{name}.{table}")
            if "credential_ref" in server:
                found += _literal_credentials(
                    {"credential_ref": server["credential_ref"]}, f"mcp_servers.{name}"
                )
    if found:
        raise LaunchRefused(
            f"{', '.join(sorted(set(found)))} would store a secret on the chat record; name a "
            "qmx/* keyring reference instead"
        )


def _masked(value: Any) -> Any:
    """`value` with every key-shaped string masked, the record's second guard."""
    match value:
        case str():
            return SECRET_SHAPES.sub(MASK, value)
        case Mapping():
            return {
                _masked(str(key)): _masked(item)
                for key, item in cast("Mapping[object, object]", value).items()
            }
        case list() | tuple():
            return [_masked(item) for item in cast("Sequence[object]", value)]
        case _:
            return value


def claude_section(raw: Mapping[str, object], current: Mapping[str, object]) -> dict[str, object]:
    """Parse a whole-section write. A write that does not name `remembered` keeps the stored
    rules, so saving permissions never drops an "always allow"."""
    if "remembered" not in raw and "remembered" in current:
        raw = {**raw, "remembered": current["remembered"]}
    return dict(parse_claude_settings(raw).raw)


def remember_rule(control: ControlService, rule: str, workspace: Path) -> None:
    """Append an allow rule to `[claude.remembered."<workspace>"]` through `ControlService`, the
    one writer, as one read-modify-write under its lock. Idempotent. Chats in that workspace pick
    it up at their next launch."""

    def add(current: Document) -> Document:
        section = cast("dict[str, Any]", copy.deepcopy(current))
        remembered: dict[str, Any] = section.setdefault("remembered", {})
        allow: list[str] = remembered.setdefault(workspace_key(workspace), {}).setdefault(
            "allow", []
        )
        if rule not in allow:
            allow.append(rule)
        return section

    control.settings_update("claude", add)


PLAN_AUTH_METHOD: Final = "claude.ai"
"""What `claude auth status` reports for a Max login (HP0 S2), with `firstParty`."""
PLAN_API_PROVIDER: Final = "firstParty"


@dataclass(frozen=True)
class PlanAuth:
    """The login fields of `claude auth status`. Never the token, email or organisation."""

    logged_in: bool
    method: str | None
    provider: str | None
    subscription: str | None

    @property
    def is_subscription(self) -> bool:
        return (
            self.logged_in
            and self.method == PLAN_AUTH_METHOD
            and self.provider == PLAN_API_PROVIDER
        )

    def require(self) -> None:
        if not self.is_subscription:
            raise LaunchRefused(
                f"the plan home is not signed in to a claude.ai plan "
                f"(method {self.method}, provider {self.provider}); run /login in the console"
            )


def cli_env(config_dir: Path) -> dict[str, str]:
    """This process's env without any banned name, plus the home. No inherited token, key,
    base URL or proxy ever reaches a CLI QMA starts."""
    clean = {name: value for name, value in os.environ.items() if not banned_fragment(name)}
    return clean | {"CLAUDE_CONFIG_DIR": str(config_dir)}


def plan_auth_method(home: QmxHome, settings_json: str) -> PlanAuth:
    """Run the bundled CLI's `auth status` in the plan home with the settings stack a launch
    uses: no settings file from any source, then the same inline settings."""
    cli = bundled_cli()
    if cli is None:
        return PlanAuth(logged_in=False, method=None, provider=None, subscription=None)
    done = subprocess.run(
        [cli, "--setting-sources=", "--settings", settings_json, "auth", "status"],
        env=cli_env(home.plan_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    try:
        status = cast("dict[str, object]", json.loads(done.stdout))
    except ValueError:
        status = {}

    def text(key: str) -> str | None:
        value = status.get(key)
        return value if isinstance(value, str) else None

    return PlanAuth(
        logged_in=status.get("loggedIn") is True,
        method=text("authMethod"),
        provider=text("apiProvider"),
        subscription=text("subscriptionType"),
    )


@functools.cache
def cli_version() -> str | None:
    cli = bundled_cli()
    if cli is None:
        return None
    done = subprocess.run([cli, "-v"], capture_output=True, text=True, timeout=60, check=False)
    found = re.search(r"\d+\.\d+\.\d+", done.stdout)
    return found.group() if found else None


type TurnState = Literal["idle", "running"]


@dataclass(frozen=True)
class ChatRecord:
    """What QMA must remember about a chat across restarts. The transcript is the SDK's JSONL.

    `started` is False until the chat's first `ResultMessage`. It is a hint; resume is decided
    by whether the JSONL exists, and a started chat with no JSONL is refused.
    `turn` is "running" from before a prompt is sent until its `ResultMessage`; "running" at
    boot means the outcome is unknown."""

    session_id: SessionId
    config: ChatConfig
    started: bool
    turn: TurnState
    digests: tuple[str, ...] = ()
    """The surface digest of each launch whose surface differed from the one before (AD-62)."""
    attached: tuple[AttachedRef, ...] = ()
    """The chat's attached context references (AD-63, H49), changed only by
    `Harness.set_attached`. Beside `home` and `packs` on the record, never in a table of its
    own. The session recorder mirrors them into the Library session item (Library AD-21)."""


def _kind_document(kind: ChatKind) -> dict[str, object]:
    match kind:
        case Interactive():
            return {"type": "interactive"}
        case Background():
            return {"type": "background"}
        case Child(parent=parent, unattended=flag):
            return {"type": "child", "parent": parent, "unattended": flag}


def _kind(document: Mapping[str, Any]) -> ChatKind:
    match document["type"]:
        case "interactive":
            return Interactive()
        case "background":
            return Background()
        case "child":
            return Child(session_id(document["parent"]), bool(document["unattended"]))
        case other:
            raise ValueError(f"unknown chat kind {other!r}")


def _record_document(record: ChatRecord) -> dict[str, object]:
    config = record.config
    permissions = config.permissions
    return {
        "session_id": record.session_id,
        "config": {
            "profile": config.profile,
            "model": config.model,
            "effort": config.effort,
            "mode": config.mode,
            "workspace": str(config.workspace),
            "kind": _kind_document(config.kind),
            "compact_at": config.compact_at,
            "tools": None if config.tools is None else list(config.tools),
            "home": {"kind": config.home.kind, "project_id": config.home.project_id},
            "packs": list(config.packs),
            "toolsets": None if config.toolsets is None else list(config.toolsets),
            "skills": None if config.skills is None else list(config.skills),
            "agents": {
                name: {
                    "description": agent.description,
                    "prompt": _masked(agent.prompt),
                    "tools": None if agent.tools is None else list(agent.tools),
                    "model": agent.model,
                }
                for name, agent in config.agents.items()
            },
            "mcp_servers": _masked(config.mcp_servers),
            "append_system_prompt": _masked(config.append_system_prompt),
            "hook_sink": config.hook_sink,
            "permissions": {
                "policy": permissions.policy,
                "allow": list(permissions.allow),
                "deny": list(permissions.deny),
            },
            "policy_args": _masked(config.policy_args),
            "claude_hooks": _masked(config.claude_hooks),
        },
        "started": record.started,
        "turn": record.turn,
        "digests": list(record.digests),
        "attached": [entry.document() for entry in record.attached],
    }


def _record(document: Mapping[str, Any]) -> ChatRecord:
    """A record written before an option existed reads that option's default."""
    config = document["config"]
    if document["turn"] not in ("idle", "running"):
        raise ValueError(f"unknown turn state {document['turn']!r}")
    home = cast("dict[str, Any]", config.get("home") or {})
    permissions = cast("dict[str, Any]", config.get("permissions") or {})
    agents = cast("dict[str, dict[str, Any]]", config.get("agents") or {})
    tools = config.get("tools")
    return ChatRecord(
        session_id=session_id(document["session_id"]),
        config=ChatConfig(
            profile=ProfileName(config["profile"]),
            model=str(config["model"]),
            effort=config["effort"],
            mode=config["mode"],
            workspace=Path(config["workspace"]),
            kind=_kind(config["kind"]),
            compact_at=config.get("compact_at"),
            tools=None if tools is None else tuple(tools),
            home=Home(home.get("kind", "general"), home.get("project_id")),
            packs=tuple(config.get("packs", ())),
            toolsets=None if config.get("toolsets") is None else tuple(config["toolsets"]),
            skills=None if config.get("skills") is None else tuple(config["skills"]),
            agents=MappingProxyType(
                {
                    name: SubAgent(
                        agent["description"],
                        agent["prompt"],
                        None if agent.get("tools") is None else tuple(agent["tools"]),
                        agent.get("model"),
                    )
                    for name, agent in agents.items()
                }
            ),
            mcp_servers=MappingProxyType(config.get("mcp_servers") or {}),
            append_system_prompt=config.get("append_system_prompt"),
            hook_sink=config.get("hook_sink"),
            permissions=ChatPermissions(
                permissions.get("policy"),
                tuple(permissions.get("allow", ())),
                tuple(permissions.get("deny", ())),
            ),
            policy_args=MappingProxyType(config.get("policy_args") or {}),
            claude_hooks=MappingProxyType(config.get("claude_hooks") or {}),
        ),
        started=bool(document["started"]),
        turn=document["turn"],
        digests=tuple(document.get("digests", ())),
        attached=tuple(AttachedRef.from_document(page) for page in document.get("attached") or ()),
    )


def record_path(home: QmxHome, chat: SessionId) -> Path:
    return home.chats_dir / f"{chat}.json"


def read_record(home: QmxHome, chat: SessionId) -> ChatRecord | None:
    try:
        text = record_path(home, chat).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    return _record(json.loads(text))


def write_record(home: QmxHome, record: ChatRecord) -> None:
    """Atomic replace of one chat's file. Writing the same record twice changes nothing."""
    path = record_path(home, record.session_id)
    encoded = json.dumps(_record_document(record), indent=2, sort_keys=True)
    with contextlib.suppress(FileNotFoundError):
        if path.read_text(encoding="utf-8") == encoded:
            return
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    staged.write_text(encoded, encoding="utf-8")
    staged.replace(path)


def list_records(home: QmxHome) -> list[ChatRecord]:
    return [
        _record(json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(home.chats_dir.glob("*.json"))
    ]


@dataclass(frozen=True)
class DoctorLine:
    name: str
    ok: bool
    detail: str


CLI_FLOOR: Final = (2, 1, 248)

DEPARTURES: Final[tuple[str, ...]] = (
    "Only the workspace root's CLAUDE.md and AGENTS.md are read, once, into the system prompt "
    "append; parent and subfolder CLAUDE.md files are not loaded.",
    ".claude/rules/ and CLAUDE.local.md are not loaded; @import lines stay raw text.",
    "/memory, # quick memory and /init edit files that apply only at the next launch, and only "
    "at the workspace root.",
    "Project settings, project hooks and .mcp.json are off.",
    "Project skills, commands and agents are off; only the QMX plugin's load.",
    "Auto memory lives in <qmx_home>/agent-memory/<workspace>/, one per workspace, shared by "
    "every provider.",
    "Plan mode may fail to write its plan file, which defaults to a protected Claude home.",
    'Always allow is saved to [claude.remembered."<workspace>"], not the project\'s local '
    "settings file.",
    "User settings: only permissions, six env names, hooks, outputStyle, attribution, "
    "includeCoAuthoredBy, alwaysThinkingEnabled, language and respectGitignore can be set.",
    "Settings edits apply at the next launch, never mid-session.",
    "Skills and plugins do not hot-reload; the ConfigChange guard blocks reloads.",
    "His personal ~/.claude, plugins, mods and claude.ai connectors never load.",
    "Agent Bash sees an allow-listed environment; other names need the UI keep list and a restart.",
    "No proxy and no corporate CA for plan traffic.",
    "Background and Child chats are verbatim: no slash commands, no @file reads.",
    "Nonessential traffic is off, TodoWrite is on, Workflow is off.",
    "/rewind file checkpoints do not cross a provider switch (inferred).",
    "In the QMX repo, edits under qmx-agents/plugin/ and Bash naming that folder are denied.",
    "Asking QMX tools have no always allow.",
)


def managed_policy_paths() -> tuple[Path, ...]:
    """Where Claude Code reads managed policy on this OS. Policy beats every other layer."""
    if sys.platform == "win32":
        roots = (Path("C:/Program Files/ClaudeCode"), Path("C:/ProgramData/ClaudeCode"))
        names = ("managed-settings.json", "managed-settings.d", "managed-mcp.json")
        return tuple(root / name for root in roots for name in names)
    root = (
        Path("/Library/Application Support/ClaudeCode")
        if sys.platform == "darwin"
        else Path("/etc/claude-code")
    )
    return tuple(
        root / name for name in ("managed-settings.json", "managed-settings.d", "managed-mcp.json")
    )


def _policy_lines() -> list[DoctorLine]:
    lines = [
        DoctorLine(
            f"managed policy {path.as_posix()}",
            not path.exists(),
            "present" if path.exists() else "absent",
        )
        for path in managed_policy_paths()
    ]
    if sys.platform == "win32":
        import winreg  # noqa: PLC0415

        for hive, label in (
            (winreg.HKEY_LOCAL_MACHINE, "HKLM"),
            (winreg.HKEY_CURRENT_USER, "HKCU"),
        ):
            try:
                winreg.OpenKey(hive, r"SOFTWARE\Policies\ClaudeCode").Close()
                present = True
            except FileNotFoundError:
                present = False
            name = f"managed policy {label}\\SOFTWARE\\Policies\\ClaudeCode"
            lines.append(DoctorLine(name, not present, "present" if present else "absent"))
    return lines


def _git_bash() -> DoctorLine:
    if sys.platform != "win32":
        return DoctorLine("git bash", True, "not needed on this OS")
    chosen = os.environ.get("CLAUDE_CODE_GIT_BASH_PATH")
    if chosen:
        return DoctorLine(
            "git bash", Path(chosen).is_file(), f"{chosen} (kept from CLAUDE_CODE_GIT_BASH_PATH)"
        )
    git = shutil.which("git")
    roots = Path(git).parents if git else (Path("C:/Program Files/Git"),)
    found = next(
        (root / "bin" / "bash.exe" for root in roots if (root / "bin" / "bash.exe").is_file()),
        None,
    )
    if found is None:
        return DoctorLine("git bash", False, "no Git Bash found; set CLAUDE_CODE_GIT_BASH_PATH")
    return DoctorLine("git bash", True, f"{found} (found from git on PATH)")


def _home_lines(home: QmxHome) -> list[DoctorLine]:
    lines = [
        DoctorLine(
            name,
            path.is_dir() and not _inside_personal_claude(path),
            f"{path} {'exists' if path.is_dir() else 'missing'}; "
            f"{'is' if _inside_personal_claude(path) else 'is not'} inside ~/.claude",
        )
        for name, path in (("plan home", home.plan_dir), ("relayed home", home.relayed_dir))
    ]
    link, target = home.relayed_dir / "projects", home.plan_dir / "projects"
    linked = link.exists() and link.resolve() == target.resolve()
    lines.append(DoctorLine("relayed projects link", linked, f"{link} -> {link.resolve()}"))
    found = relayed_logins(home)
    detail = f"login file found: {found[0]}; launches are refused" if found else "no login file"
    lines.append(DoctorLine("relayed home login", not found, detail))
    return lines


def _pack_lines(home: QmxHome) -> list[DoctorLine]:
    """One line per materialised pack view: whether its bytes still match what was published.
    A view that no longer holds is not loaded, and this is the line that names it."""
    found = packs.survey(home.packs_dir, packs.names(home.packs_dir))
    lines = [
        DoctorLine(
            f"pack view {view.name}",
            True,
            f"{view.folder}, {len(view.skills)} skills, {len(view.objects)} objects",
        )
        for view in found.views
    ]
    lines += [DoctorLine(f"pack view {name}", False, reason) for name, reason in found.refusals]
    return lines


def _hooks_outline(hooks: dict[str, list[dict[str, Any]]], launcher: Path) -> dict[str, Any]:
    fixed = config_change_hook(launcher)
    return {
        event: [
            group
            if group == fixed
            else {
                **({"matcher": group["matcher"]} if "matcher" in group else {}),
                "hooks": [
                    {name: value if name == "type" else SET for name, value in hook.items()}
                    for hook in group["hooks"]
                ],
            }
            for group in groups
        ]
        for event, groups in hooks.items()
    }


async def _no_tools(
    name: str, _input: dict[str, Any], _context: ToolPermissionContext
) -> PermissionResult:
    return PermissionResultDeny(message=f"{name}: doctor never runs a chat")


DOCTOR_CHAT: Final = session_id("00000000-0000-4000-8000-000000000000")


def _argv_line(home: QmxHome, workspace: Path, launcher: Path) -> DoctorLine:
    files = home.launch_dir(DOCTOR_CHAT)
    config = ChatConfig(PLAN, "opus", None, "default", workspace, Interactive())
    supply = Supply((), HomeSlots(home), {}, (home.plugin_dir,), files / SLOTS_PLUGIN / "skills")
    options = build_options(
        config,
        build(config.kind, config.home, (), declaration(config), supply, workspace=workspace),
        session_id=DOCTOR_CHAT,
        transcript_exists=False,
        env=launch_env(PlanLaunch(), home=home, session_id=DOCTOR_CHAT, cap=""),
        settings_file=files / "settings.json",
        system_file=files / "system.md",
        launcher=launcher,
        can_use_tool=_no_tools,
        mcp_servers={},
        budgets=Budgets(),
        gate=guard_rules(
            [],
            domain_write=DEFAULT_DOMAIN_WRITE,
            home=home,
            config_dir=home.plan_dir,
            keyring_names=frozenset(),
            unattended=False,
            external_unattended=frozenset(),
        ),
    )
    total, parts = argv_length(options)
    name, size = max(parts.items(), key=lambda part: part[1])
    return DoctorLine(
        "plan launch command line",
        total <= ARGV_BUDGET,
        f"{total} characters of {ARGV_BUDGET} for a plan launch in {workspace}; "
        f"largest part: {name} at {size}",
    )


def doctor(
    home: QmxHome,
    control: ControlService,
    *,
    scrubbed: Sequence[str],
    keep: Sequence[str],
    launcher: Path,
) -> list[DoctorLine]:
    """One read-only page of facts. Runs `claude auth status`, so call it off the event loop."""
    sdk = version("claude-agent-sdk")
    cli = cli_version()
    cli_ok = cli is not None and tuple(int(part) for part in cli.split(".")) >= CLI_FLOOR
    lines = [
        DoctorLine("sdk", True, f"claude-agent-sdk {sdk}"),
        DoctorLine("cli", cli_ok, f"bundled CLI {cli}, floor {'.'.join(map(str, CLI_FLOOR))}"),
        *_home_lines(home),
        *_pack_lines(home),
    ]
    try:
        user = parse_claude_settings(control.settings_get("claude"))
        lines.append(DoctorLine("[claude] settings", True, "parsed"))
    except LaunchRefused as error:
        user = ClaudeSettings()
        lines.append(DoctorLine("[claude] settings", False, str(error)))
    workspace = home.workspaces_dir
    settings = code_settings(
        user, launcher=launcher, workspace=workspace, memory_dir=home.memory_dir(workspace)
    )
    document = json.loads(settings)
    document["hooks"] = _hooks_outline(document["hooks"], launcher)
    shown = json.dumps(document, sort_keys=True, separators=(",", ":"))
    lines.append(
        DoctorLine(
            "launch settings",
            True,
            f"{len(settings)} characters, passed by file, for {workspace}: {shown}",
        )
    )
    lines.append(_argv_line(home, workspace, launcher))
    auth = plan_auth_method(home, settings)
    lines.append(
        DoctorLine(
            "plan auth method",
            auth.is_subscription,
            f"logged in {auth.logged_in}, method {auth.method}, provider {auth.provider}, "
            f"subscription {auth.subscription}",
        )
    )
    errors = parse_profiles(control.settings_get("providers")).errors
    lines.append(
        DoctorLine("[providers]", not errors, "; ".join(errors.values()) or "every row parses")
    )
    lines += _policy_lines()
    lines += [
        DoctorLine("boot scrub removed", True, ", ".join(scrubbed) or "nothing"),
        _git_bash(),
        DoctorLine(
            "keep list", True, f"{', '.join(keep) or 'empty'}; an edit applies at the next start"
        ),
        *(
            DoctorLine(f"departure {number}", True, text)
            for number, text in enumerate(DEPARTURES, start=1)
        ),
    ]
    return lines
