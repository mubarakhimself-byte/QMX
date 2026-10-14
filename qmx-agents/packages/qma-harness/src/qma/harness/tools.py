"""The `qmx` in-process MCP server: QMX's own tools, nothing else.

"The copilot is the same API as the UI" (01 section 11.1), so the tools are the existing
control-plane, broker and domain functions, read from the FastMCP servers that already serve
them, not new code. In-process means the CLI never receives the qmx-control bearer token
(HOW seam 2).

One list. `tool_defs` is the only place a QMX tool joins the agent surface. Every tool
declares an `Effect` in an explicit table; a function missing from its table does not join.
Which tools ask, the proposal exemption and the grant check all derive from that one field.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from collections.abc import Awaitable, Callable, Mapping
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Literal, NewType, cast

from claude_agent_sdk import SdkMcpTool, create_sdk_mcp_server
from qmx_broker.service import BrokerService

from qma.harness.money import (
    NON_BROKER_REFS,
    GateRules,
    MoneySurfaceError,
    check_tool_surface,
    normalize_path,
)

if TYPE_CHECKING:
    from claude_agent_sdk import McpSdkServerConfig, McpServerConfig
    from fastmcp import FastMCP
    from fastmcp.tools import Tool
    from qmx_control.service import ControlService
    from qmx_tools.service import DomainContext

    from qma.harness.home import QmxHome

SERVER: Final = "qmx"
PREFIX: Final = f"mcp__{SERVER}__"


class Effect(Enum):
    """What a QMX tool does to the world. Closed. There is no member for moving money, so no
    tool can be registered as a money act: the type has no slot for it.

    READ           reads QMX or broker state. Runs without asking.
    DOMAIN_WRITE   writes QMX research state (library, backtests, run results). Asks or not
                   per `settings.toml [agents] domain_write` ("allow" | "ask").
    MANAGE         publish, install, schedule, run, cancel, destructive control-plane ops.
                   Always asks (R35).
    PROPOSE_MONEY  writes an unsigned order proposal. Always asks. Accepted on
                   `BrokerService.propose_order` only, by identity.
    """

    READ = "read"
    DOMAIN_WRITE = "domain_write"
    MANAGE = "manage"
    PROPOSE_MONEY = "propose_money"


type DomainWritePolicy = Literal["allow", "ask"]
DEFAULT_DOMAIN_WRITE: Final[DomainWritePolicy] = "allow"
"""R35 names publish, install, scheduling and managing as always asking; research writes
follow the setting, and run without asking until the operator changes it."""


def asks(effect: Effect, domain_write: DomainWritePolicy) -> bool:
    """The one table: READ no; DOMAIN_WRITE per policy; MANAGE and PROPOSE_MONEY yes."""
    match effect:
        case Effect.READ:
            return False
        case Effect.DOMAIN_WRITE:
            return domain_write == "ask"
        case Effect.MANAGE | Effect.PROPOSE_MONEY:
            return True


def domain_write_policy(agents: Mapping[str, object]) -> DomainWritePolicy:
    """`settings.toml [agents] domain_write`. Anything but "allow" reads as "ask"."""
    value = agents.get("domain_write", DEFAULT_DOMAIN_WRITE)
    return "allow" if value == "allow" else "ask"


type ToolCall = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ToolDef:
    name: str
    description: str
    input_schema: Mapping[str, object]
    effect: Effect
    """Required, no default. A tool without one does not construct."""
    call: ToolCall
    metadata: Mapping[str, object] = field(default_factory=dict[str, object])
    """The MCP annotations and `_meta`, for the surface check."""
    target: object = None
    """The function the tool runs. The proposal exemption is granted by its identity."""

    def __post_init__(self) -> None:
        if not isinstance(self.effect, Effect):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"{self.name} declares no Effect")


AGENT_OPERATIONS: Final[Mapping[str, Effect]] = MappingProxyType(
    {
        "apps_list": Effect.READ,
        "apps_registry": Effect.READ,
        "apps_get": Effect.READ,
        "apps_create": Effect.MANAGE,
        "apps_update": Effect.MANAGE,
        "apps_versions": Effect.READ,
        "apps_test": Effect.DOMAIN_WRITE,
        "apps_publish": Effect.MANAGE,
        "apps_rollback": Effect.MANAGE,
        "apps_start": Effect.MANAGE,
        "apps_stop": Effect.MANAGE,
        "apps_restart": Effect.MANAGE,
        "apps_call": Effect.MANAGE,
        "apps_resource": Effect.READ,
        "apps_logs": Effect.READ,
        "apps_evidence": Effect.READ,
        "apps_backup": Effect.DOMAIN_WRITE,
        "apps_restore": Effect.MANAGE,
        "workflows_get": Effect.READ,
        "workflows_put": Effect.MANAGE,
        "workflows_validate": Effect.READ,
        "workflows_run": Effect.MANAGE,
        "runs_list": Effect.READ,
        "runs_start_remote": Effect.MANAGE,
        "runs_status": Effect.READ,
        "runs_logs": Effect.READ,
        "runs_fetch": Effect.DOMAIN_WRITE,
        "runs_resume": Effect.MANAGE,
        "runs_stop": Effect.MANAGE,
        "run_job": Effect.MANAGE,
        "job_status": Effect.READ,
        "job_logs": Effect.READ,
        "job_fetch": Effect.DOMAIN_WRITE,
        "runs_get": Effect.READ,
        "runs_cancel": Effect.MANAGE,
        "jobs_list": Effect.READ,
        "jobs_cancel": Effect.MANAGE,
        "library_search": Effect.READ,
        "library_save": Effect.DOMAIN_WRITE,
        "library_get": Effect.READ,
        "library_versions": Effect.READ,
        "library_links": Effect.READ,
        "library_link": Effect.DOMAIN_WRITE,
        "aggregates_get": Effect.READ,
        "settings_get": Effect.READ,
        "portfolio_proposals": Effect.READ,
        "sessions_list": Effect.READ,
    }
)
"""Names from `qmx_control.server.OPERATIONS` the agent may call, each with its effect. An
explicit allow-list; `OPERATIONS_LEFT_OUT` says why each other row stays out."""

OPERATIONS_LEFT_OUT: Final[Mapping[str, str]] = MappingProxyType(
    {
        "settings_put": "an agent that edits a provider row could send a stored key to a host",
        "backup_weekly": "a host maintenance job, not an agent act",
        "sessions_create": "chats are created by the harness",
        "sessions_append": "an agent could forge permission or needs_you blocks",
        "sessions_stream": "a live event stream, not a tool",
    }
)

DOMAIN_EFFECTS: Final[Mapping[str, Effect]] = MappingProxyType(
    {
        "list_instruments": Effect.READ,
        "read_bars": Effect.READ,
        "read_features": Effect.READ,
        "calendar": Effect.READ,
        "run_backtest": Effect.DOMAIN_WRITE,
        "backtest_status": Effect.READ,
        "backtest_results": Effect.READ,
        "compare_runs": Effect.READ,
        "qml_run": Effect.READ,
        "node_state": Effect.READ,
    }
)
"""`qmx_tools.functions.domain_functions` by name. `DOMAIN_LEFT_OUT` lists the rest."""

DOMAIN_LEFT_OUT: Final[Mapping[str, str]] = MappingProxyType(
    {
        "library_search": "the control-plane library_search serves the same library",
        "library_save": "the control-plane library_save serves the same library",
        "propose_order": "the broker's propose_order is the one proposal writer",
    }
)
DOMAIN_GROUPS: Final = ("data", "backtest", "research", "node")

BROKER_EFFECTS: Final[Mapping[str, Effect]] = MappingProxyType(
    {
        "list_accounts": Effect.READ,
        "account_state": Effect.READ,
        "positions": Effect.READ,
        "quotes": Effect.READ,
        "symbol_info": Effect.READ,
        "bars": Effect.READ,
        "propose_order": Effect.PROPOSE_MONEY,
    }
)

BROKER_HOSTS: Final[frozenset[str]] = frozenset({"ctraderapi.com", "ctrader.com", "spotware.com"})
"""The cTrader Open API hosts (`qmx_broker.ctrader_transport`) and Spotware's sign-in host."""


# --- approvals bound to arguments (03 CO-6) ---

ArgsDigest = NewType("ArgsDigest", str)
"""sha256 over the tool name and the canonical JSON of its input (sorted keys, no
whitespace, UTF-8)."""


def args_digest(tool_name: str, tool_input: Mapping[str, object]) -> ArgsDigest:
    body = json.dumps(
        [tool_name, tool_input], sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return ArgsDigest(hashlib.sha256(body.encode()).hexdigest())


@dataclass(frozen=True)
class Grant:
    tool: str
    digest: ArgsDigest


class Grants:
    """One chat's approvals for asking QMX tools. A grant is consumed by the first handler run
    that matches it, so an approval never outlives the arguments the operator saw. Until
    approvals are wired, nothing records one and every asking tool is refused."""

    def __init__(self) -> None:
        self._open: list[Grant] = []

    def record(self, grant: Grant) -> None:
        self._open.append(grant)

    def consume(self, tool: str, digest: ArgsDigest) -> bool:
        """True once per recorded grant, then False."""
        grant = Grant(tool, digest)
        if grant in self._open:
            self._open.remove(grant)
            return True
        return False


# --- the tool list ---


def _text(result: Any) -> dict[str, Any]:
    blocks = [
        {"type": "text", "text": block.text}
        for block in result.content
        if getattr(block, "type", None) == "text"
    ]
    return {"content": blocks or [{"type": "text", "text": ""}]}


def _from_fastmcp(tool: Tool, effect: Effect) -> ToolDef:
    async def call(arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            return _text(await tool.run(arguments))
        except Exception as error:
            return {"content": [{"type": "text", "text": str(error)}], "is_error": True}

    metadata: dict[str, object] = {"_meta": dict(tool.meta or {})}
    if tool.annotations is not None:
        metadata["annotations"] = tool.annotations.model_dump(exclude_none=True)
    return ToolDef(
        name=tool.name,
        description=tool.description or tool.name,
        input_schema=tool.parameters,
        effect=effect,
        call=call,
        metadata=metadata,
        target=getattr(tool, "fn", None),
    )


async def _listed(server: FastMCP, effects: Mapping[str, Effect]) -> list[ToolDef]:
    return [
        _from_fastmcp(tool, effects[tool.name])
        for tool in await server.list_tools()
        if tool.name in effects
    ]


async def tool_defs(
    *, control: ControlService, broker: BrokerService, domain: DomainContext
) -> list[ToolDef]:
    """Every QMX tool for one chat, each with its declared `Effect`: the `AGENT_OPERATIONS`
    rows of the control plane, the broker's reads and `propose_order`, and the domain
    functions in `DOMAIN_EFFECTS`. `domain` shares `control`, so no second writer runs."""
    from qmx_broker.server import create_server as broker_server  # noqa: PLC0415
    from qmx_control.server import create_mcp  # noqa: PLC0415
    from qmx_tools.servers import create_server as domain_server  # noqa: PLC0415

    found = await _listed(create_mcp(control), AGENT_OPERATIONS)
    found += await _listed(broker_server(broker), BROKER_EFFECTS)
    for group in DOMAIN_GROUPS:
        found += await _listed(domain_server(group, domain), DOMAIN_EFFECTS)
    return found


class ToolSurfaceError(RuntimeError):
    """The `qmx` server cannot be built from these defs."""


def is_proposal_writer(target: object) -> bool:
    return getattr(target, "__func__", None) is BrokerService.propose_order


def build_server(
    defs: list[ToolDef],
    *,
    grants: Grants,
    domain_write: DomainWritePolicy,
    enforce_grants: bool = True,
) -> McpSdkServerConfig:
    """`create_sdk_mcp_server(name="qmx", ...)`. Refuses to build on a duplicate name, a
    name or metadata the surface check flags, and PROPOSE_MONEY on anything but the broker's
    `propose_order` (identity, not name). Every asking tool's handler first consumes a grant
    for its exact arguments and returns an error naming the rule without one.
    `enforce_grants=False` exists for one live check only (`TestMode.grants`)."""
    names = [tool.name for tool in defs]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ToolSurfaceError(f"duplicate QMX tool names: {', '.join(duplicates)}")
    for tool in defs:
        if tool.effect is Effect.PROPOSE_MONEY and not is_proposal_writer(tool.target):
            raise MoneySurfaceError(
                f"{tool.name} is not the broker's propose_order and cannot propose money"
            )
    exempt = frozenset(tool.name for tool in defs if tool.effect is Effect.PROPOSE_MONEY)
    check_tool_surface(names, {tool.name: tool.metadata for tool in defs}, exempt)
    return create_sdk_mcp_server(
        SERVER, tools=sdk_tools(defs, grants, domain_write, enforce_grants=enforce_grants)
    )


def sdk_tools(
    defs: list[ToolDef],
    grants: Grants,
    domain_write: DomainWritePolicy,
    *,
    enforce_grants: bool = True,
) -> list[SdkMcpTool[Any]]:
    """The server's tools. Each asking tool's handler consumes a grant first."""
    return [
        SdkMcpTool(
            tool.name,
            tool.description,
            dict(tool.input_schema),
            _guarded(tool, grants)
            if enforce_grants and asks(tool.effect, domain_write)
            else tool.call,
        )
        for tool in defs
    ]


def _guarded(tool: ToolDef, grants: Grants) -> ToolCall:
    async def call(arguments: dict[str, Any]) -> dict[str, Any]:
        if not grants.consume(PREFIX + tool.name, args_digest(PREFIX + tool.name, arguments)):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"{tool.name} runs only after you approve these exact "
                        "arguments, and no approval was given",
                    }
                ],
                "is_error": True,
            }
        return await tool.call(arguments)

    return call


def keyring_refs(control: ControlService) -> frozenset[str]:
    """Every `qmx/*` reference named in settings.toml [providers], [brokers] and
    [mcp_servers], plus the fixed entries, casefolded. Names only; nothing is read."""
    found: set[str] = set(NON_BROKER_REFS)

    def walk(value: object) -> None:
        if isinstance(value, str) and value.casefold().startswith("qmx/"):
            found.add(value.casefold())
        elif isinstance(value, Mapping):
            for item in cast("Mapping[str, object]", value).values():
                walk(item)
        elif isinstance(value, list):
            for item in cast("list[object]", value):
                walk(item)

    for section in ("providers", "brokers", "mcp_servers"):
        walk(control.settings_get(section))
    return frozenset(found)


def _posix(path: Path) -> str:
    home = str(Path.home())
    return normalize_path(str(path.resolve()), cwd="/", home=home, case_insensitive=False)


def gate_rules(
    defs: list[ToolDef],
    *,
    domain_write: DomainWritePolicy,
    home: QmxHome,
    config_dir: Path,
    keyring_names: frozenset[str],
    broker_hosts: frozenset[str] = BROKER_HOSTS,
) -> GateRules:
    """Derive `GateRules` from the same defs: proposal_tools are the PROPOSE_MONEY names,
    mandatory_asks the names where `asks(effect, domain_write)`, each prefixed
    `mcp__qmx__`. Paths come from `home` and the OS user's home."""
    personal = Path.home() / ".claude"
    protected = [
        home.plan_dir,
        home.relayed_dir,
        home.chats_dir,
        home.procs_dir,
        home.state_dir,
        home.plugin_dir,
        *(
            home.root / f"{name}{suffix}"
            for name in ("control.db", "portfolio.db")
            for suffix in ("", "-wal", "-shm", "-journal")
        ),
        home.root / "settings.toml",
    ]
    secrets = [
        folder / name
        for folder in (home.plan_dir, home.relayed_dir, personal)
        for name in (".credentials.json", ".claude.json")
    ] + [Path.home() / ".claude.json"]
    return GateRules(
        proposal_tools=frozenset(
            PREFIX + tool.name for tool in defs if tool.effect is Effect.PROPOSE_MONEY
        ),
        mandatory_asks=frozenset(
            PREFIX + tool.name for tool in defs if asks(tool.effect, domain_write)
        ),
        protected_paths=tuple(map(_posix, protected)),
        secret_paths=tuple(map(_posix, secrets)),
        personal_home=_posix(personal),
        keyring_names=frozenset(name.casefold() for name in keyring_names),
        broker_hosts=frozenset(host.casefold() for host in broker_hosts),
        variables=MappingProxyType(
            {
                "HOME": _posix(Path.home()),
                "USERPROFILE": _posix(Path.home()),
                "CLAUDE_CONFIG_DIR": _posix(config_dir),
            }
        ),
        case_insensitive=sys.platform in ("win32", "darwin"),
    )


# --- external MCP servers ---

VET_TIMEOUT_S: Final = 30.0


@dataclass(frozen=True)
class VettedServers:
    """External MCP servers that passed `vet_mcp_servers`, as SDK configs, and each refused
    server with its reason. Only `configs` reach `mcp_servers`; `strict_mcp_config=True` makes
    the CLI ignore every other MCP config (02a section 7)."""

    configs: Mapping[str, McpServerConfig]
    refused: Mapping[str, str]


def server_config(name: str, row: Mapping[str, object]) -> McpServerConfig:
    """One settings.toml [mcp_servers] row as an SDK config: `command` with `args` and `env`
    for stdio, or `url` for HTTP. Raises ValueError naming what is wrong."""
    if name == SERVER:
        raise ValueError(f"the name {SERVER} belongs to QMX's own tools")
    if row.get("credential_ref"):
        raise ValueError("servers that need a stored credential are not wired yet")
    command, url = row.get("command"), row.get("url")
    if isinstance(command, str) and command:
        args = row.get("args", [])
        env = row.get("env", {})
        if not isinstance(args, list) or not isinstance(env, dict):
            raise ValueError("args must be a list and env a table")
        return {
            "type": "stdio",
            "command": command,
            "args": [str(arg) for arg in cast("list[object]", args)],
            "env": {str(k): str(v) for k, v in cast("dict[object, object]", env).items()},
        }
    if isinstance(url, str) and url:
        return {"type": "http", "url": url}
    raise ValueError("a server needs a command or a url")


async def _list_tools(config: McpServerConfig) -> list[Any]:
    from mcp import ClientSession, StdioServerParameters  # noqa: PLC0415
    from mcp.client.stdio import stdio_client  # noqa: PLC0415
    from mcp.client.streamable_http import streamable_http_client  # noqa: PLC0415

    async with AsyncExitStack() as stack:
        spec = cast("dict[str, Any]", config)
        if spec["type"] == "stdio":
            parameters = StdioServerParameters(
                command=spec["command"], args=spec["args"], env=spec["env"] or None
            )
            streams = await stack.enter_async_context(stdio_client(parameters))
        else:
            streams = await stack.enter_async_context(streamable_http_client(spec["url"]))
        session = await stack.enter_async_context(ClientSession(streams[0], streams[1]))
        await session.initialize()
        return list((await session.list_tools()).tools)


async def vet_server(name: str, row: Mapping[str, object]) -> McpServerConfig:
    """Start one declared server with the Python MCP client, list its tools and run the
    surface check on their names and metadata. Raises ValueError or MoneySurfaceError."""
    config = server_config(name, row)
    listed = await asyncio.wait_for(_list_tools(config), VET_TIMEOUT_S)
    metadata = {
        tool.name: {
            "annotations": tool.annotations.model_dump(exclude_none=True)
            if tool.annotations
            else {},
            "_meta": dict(tool.meta or {}),
        }
        for tool in listed
    }
    check_tool_surface(list(metadata), metadata, frozenset())
    return config


async def vet_mcp_servers(declared: Mapping[str, object]) -> VettedServers:
    """Before any launch uses them: vet every enabled server in settings.toml [mcp_servers].
    A server that exposes a money act, or that cannot be listed, is refused and never
    launched (A8, B10). A tool that a server adds later is still denied by name in the gate.
    Servers are vetted at each launch, so a changed config is always vetted again."""
    configs: dict[str, McpServerConfig] = {}
    refused: dict[str, str] = {}
    for name, row in declared.items():
        if not isinstance(row, Mapping) or not cast("Mapping[str, object]", row).get(
            "enabled", True
        ):
            continue
        try:
            configs[name] = await vet_server(name, cast("Mapping[str, object]", row))
        except MoneySurfaceError as error:
            refused[name] = f"it exposes a money act ({error})"
        except Exception as error:
            refused[name] = f"it could not be vetted ({type(error).__name__}: {error})"
    return VettedServers(MappingProxyType(configs), MappingProxyType(refused))
