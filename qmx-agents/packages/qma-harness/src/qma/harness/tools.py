"""QMX's own tools for a chat, built from the operation catalog (engine AD-61).

"The copilot is the same API as the UI" (01 section 11.1), so every tool is a catalog row
(`qmx_control.catalog`) bound to the control-plane, broker, domain or host function that already
serves it. In-process means the CLI never receives the qmx-control bearer token (HOW seam 2).

A row with `agent=False` never joins. Which tools ask and the grant check derive from the row's
`approval`. Each toolset is one in-process server, `qmx_<toolset>`, and a chat's surface is the
set of those servers switched on (probe P-PK found no mid-chat re-list for one server; P-TG
passed toggling). A tool's full name is `mcp__qmx_<toolset>__<op>`, the same length as the
`mcp__qmx__<toolset>_<op>` the catalog checks.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import re
import sys
from collections.abc import Awaitable, Callable, Iterable, Mapping
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Literal, NewType, cast

from claude_agent_sdk import SdkMcpTool, create_sdk_mcp_server
from qmx_broker.service import BrokerService
from qmx_control.catalog import CORE_TOOLSETS, OperationSpec, name_problem, rows, spill

from qma.harness.guard import QMX_SERVER, GuardRules, Rule, is_qmx_server, normalize_path
from qma.harness.money_words import named_money_act

if TYPE_CHECKING:
    from claude_agent_sdk import McpSdkServerConfig, McpServerConfig
    from claude_agent_sdk.types import McpStatusResponse
    from fastmcp import FastMCP
    from fastmcp.tools import Tool
    from qmx_control.service import ControlService
    from qmx_tools.service import DomainContext

    from qma.harness.home import QmxHome

SERVER: Final = QMX_SERVER


class Effect(Enum):
    """What a QMX tool does to the world, from its row's `approval`. Closed. There is no member
    for moving money: agents have no path to money (ruling 116).

    READ           reads QMX or broker state. Runs without asking.
    DOMAIN_WRITE   writes QMX research state (library, backtests, run results). Asks or not
                   per `settings.toml [agents] domain_write` ("allow" | "ask"). `delegate`
                   is DOMAIN_WRITE: its child chat's own acts face their own gates.
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


def server_name(toolset: str) -> str:
    return f"{SERVER}_{toolset}"


def tool_name(toolset: str, op: str) -> str:
    """The name the CLI gives a tool: `mcp__qmx_<toolset>__<op>`."""
    return f"mcp__{server_name(toolset)}__{op}"


@dataclass(frozen=True)
class ToolDef:
    toolset: str
    op: str
    description: str
    input_schema: Mapping[str, object]
    effect: Effect
    """Required, no default. A tool without one does not construct."""
    call: ToolCall
    metadata: Mapping[str, object] = field(default_factory=dict[str, object])
    """The MCP annotations and `_meta`."""
    target: object = None
    """The function the tool runs. PROPOSE_MONEY is accepted by its identity."""

    def __post_init__(self) -> None:
        if not isinstance(self.effect, Effect):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"{self.name} declares no Effect")

    @property
    def name(self) -> str:
        """The wire name, `<toolset>_<op>`."""
        return f"{self.toolset}_{self.op}"

    @property
    def full(self) -> str:
        return tool_name(self.toolset, self.op)


FIXED_REFS: Final[frozenset[str]] = frozenset({"qmx/chatgpt", "qmx/control-token"})
"""Fixed `qmx/*` entries every chat's guard refuses by name, besides the settings.toml ones."""


ArgsDigest = NewType("ArgsDigest", str)
"""sha256 over the tool name and the canonical JSON of its input (sorted keys, no
whitespace, UTF-8)."""


def args_digest(name: str, tool_input: Mapping[str, object]) -> ArgsDigest:
    body = json.dumps([name, tool_input], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
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


NEXT_STEPS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "not_found": "check the id with the matching list tool, then call again",
        "invalid_arguments": "fix the arguments to match this tool's input schema",
        "unavailable": "this part of QMX is not running here; tell the operator",
        "conflict": "read the current state, then call again with it",
    }
)
DEFAULT_NEXT_STEP: Final = "read the message; call again only after changing what it names"


def failure(code: str, message: str) -> dict[str, Any]:
    """The tool error shape: a code, the message and a next step, never a raw exception."""
    next_step = NEXT_STEPS.get(code, DEFAULT_NEXT_STEP)
    body = {"error": {"code": code, "message": message, "next_step": next_step}}
    return {"content": [{"type": "text", "text": json.dumps(body)}], "is_error": True}


def _failure_of(error: Exception) -> dict[str, Any]:
    """A control error arrives as its JSON document; anything else is named by its type."""
    with contextlib.suppress(ValueError, TypeError, KeyError):
        found = json.loads(str(error))["error"]
        return failure(str(found["code"]), str(found["message"]))
    if type(error).__name__ in ("ValidationError", "ToolError") and "validation" in str(error):
        return failure("invalid_arguments", str(error))
    return failure(type(error).__name__, str(error))


def _text(result: Any) -> str:
    return "".join(block.text for block in result.content if getattr(block, "type", None) == "text")


def _paged(
    row: OperationSpec, result: Any, arguments: Mapping[str, object], limit: int
) -> tuple[str, dict[str, object]]:
    """A list answer as one page with the offset of the next, and that cursor alone; or the
    answer's own text and no cursor."""
    structured = cast("Mapping[str, object] | None", getattr(result, "structured_content", None))
    data = (structured or {}).get("result")
    if not row.cursor or not isinstance(data, list):
        return _text(result), {}
    items = cast("list[object]", data)
    offset = arguments.get("offset", 0)
    start = offset if isinstance(offset, int) else 0
    wanted = arguments.get("limit", limit)
    full = len(items) >= (wanted if isinstance(wanted, int) else limit)
    cursor: dict[str, object] = {"next_offset": start + len(items) if full else None}
    return json.dumps({"items": items, **cursor}), cursor


def wrap(row: OperationSpec, tool: Tool, save: Callable[..., Any]) -> ToolDef:
    """One row as a tool: forced arguments left out of the schema, a list answer paged with a
    cursor, a long answer spilled to the Library, and an error in the tool error shape."""
    forced = dict(row.forced)
    schema = dict(tool.parameters)
    properties = cast("dict[str, Any]", schema.get("properties", {}))
    if forced:
        schema["properties"] = {k: v for k, v in properties.items() if k not in forced}
        required = cast("list[str]", schema.get("required", []))
        schema["required"] = [name for name in required if name not in forced]
    limit_default = cast("dict[str, Any]", properties.get("limit", {})).get("default", 100)

    async def call(arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            result = await tool.run({**arguments, **forced})
        except Exception as error:
            return _failure_of(error)
        text, cursor = _paged(row, result, arguments, int(limit_default))
        answer = await asyncio.to_thread(spill, text, row, save, cursor)
        return {"content": [{"type": "text", "text": answer}]}

    metadata: dict[str, object] = {"_meta": dict(tool.meta or {})}
    if tool.annotations is not None:
        metadata["annotations"] = tool.annotations.model_dump(exclude_none=True)
    return ToolDef(
        toolset=row.toolset,
        op=row.op,
        description=row.description or tool.description or row.name,
        input_schema=schema,
        effect=Effect(row.approval),
        call=call,
        metadata=metadata,
        target=getattr(tool, "fn", None),
    )


def _plain(row: OperationSpec, schema: Mapping[str, object], call: ToolCall) -> ToolDef:
    return ToolDef(
        toolset=row.toolset,
        op=row.op,
        description=row.description,
        input_schema=schema,
        effect=Effect(row.approval),
        call=call,
    )


async def _bound(
    found: Iterable[OperationSpec],
    servers: list[FastMCP],
    save: Callable[..., Any],
    *,
    by_name: bool = False,
) -> list[ToolDef]:
    """Each row as a tool from the server that serves it, by `target` or, for the control door,
    by wire name. A row with no tool behind it raises, so a renamed or removed function never
    drops out of the surface unnoticed."""
    tools = {tool.name: tool for server in servers for tool in await server.list_tools()}
    keyed = [(row.name if by_name else row.target, row) for row in found]
    missing = sorted(key for key, _ in keyed if key not in tools)
    if missing:
        raise ToolSurfaceError(f"catalog rows are missing on their server: {', '.join(missing)}")
    return [wrap(row, tools[key], save) for key, row in keyed]


type HostRead = Callable[[dict[str, Any]], Awaitable[Mapping[str, object]]]
"""A host read the harness serves itself: the chat-slot table or a chat's journal."""

HOST_SCHEMAS: Final[Mapping[str, Mapping[str, object]]] = MappingProxyType(
    {
        "slot_table": {"type": "object", "properties": {}},
        "journal": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The chat's session id"},
                "offset": {"type": "integer", "minimum": 0, "default": 0},
                "limit": {"type": "integer", "minimum": 1, "default": 50},
            },
            "required": ["session_id"],
        },
    }
)


def _host_def(row: OperationSpec, read: HostRead) -> ToolDef:
    async def call(arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            found = await read(arguments)
        except KeyError as error:
            return failure("not_found", str(error))
        except ValueError as error:
            return failure("invalid_arguments", str(error))
        except OSError as error:
            return failure("unavailable", str(error))
        return {"content": [{"type": "text", "text": json.dumps(found, default=str)}]}

    return _plain(row, HOST_SCHEMAS[row.target], call)


async def tool_defs(
    *,
    control: ControlService,
    broker: BrokerService,
    domain: DomainContext,
    delegate: Delegate | None,
    host: Mapping[str, HostRead] | None = None,
) -> list[ToolDef]:
    """Every agent row of the catalog as a tool for one chat: control operations, the broker's
    reads and `propose_order`, the domain functions, the host reads in `host` by target, and
    `delegate` when not None (a Child chat passes None). `domain` shares `control`, so no
    second writer runs."""
    from qmx_broker.server import create_server as broker_server  # noqa: PLC0415
    from qmx_control.server import create_mcp  # noqa: PLC0415
    from qmx_tools.servers import create_server as domain_server  # noqa: PLC0415

    agent = [row for row in rows() if row.agent]
    save = control.library_save
    domain_servers = [domain_server(group, domain) for group in DOMAIN_GROUPS]
    reads = host or {}
    return [
        *await _bound(
            [row for row in agent if row.binds == "control_op"],
            [create_mcp(control)],
            save,
            by_name=True,
        ),
        *await _bound(
            [row for row in agent if row.binds == "broker"], [broker_server(broker)], save
        ),
        *await _bound([row for row in agent if row.binds == "domain_fn"], domain_servers, save),
        *(
            _host_def(row, reads[row.target])
            for row in agent
            if row.binds == "agent_tool" and row.target in reads
        ),
        *(
            delegate_def(row, delegate)
            for row in agent
            if row.binds == "delegate" and delegate is not None
        ),
    ]


DOMAIN_GROUPS: Final = ("data", "backtest", "research", "node")


type Delegate = Callable[[str, str], Awaitable[str]]
"""Runs a helper chat on a profile with a prompt, to its end, and returns its final text.
Bound to the calling chat by the harness."""


class DelegateRefused(RuntimeError):
    """The helper chat was not started, or ended without an answer. The tool returns the
    reason as an error result."""


DELEGATE_SCHEMA: Final[Mapping[str, object]] = MappingProxyType(
    {
        "type": "object",
        "properties": {
            "profile": {"type": "string", "description": "A provider profile from the allow-list"},
            "prompt": {"type": "string", "description": "The whole task for the helper"},
        },
        "required": ["profile", "prompt"],
    }
)


def delegate_def(row: OperationSpec, delegate: Delegate) -> ToolDef:
    """`mcp__qmx_delegate__run`, the one QMX tool that adds what the SDK lacks: native
    sub-agents cannot change provider. The helper is a full chat with its own process, relay
    grant, qmx-control child session, asks and verbatim prompts, so every rule above holds in it."""

    async def call(arguments: dict[str, Any]) -> dict[str, Any]:
        profile, prompt = arguments.get("profile"), arguments.get("prompt")
        if not isinstance(profile, str) or not isinstance(prompt, str) or not prompt.strip():
            return failure("invalid_arguments", "delegate needs a profile name and a prompt")
        try:
            return {"content": [{"type": "text", "text": await delegate(profile, prompt)}]}
        except DelegateRefused as refused:
            return failure("refused", str(refused))

    return _plain(row, DELEGATE_SCHEMA, call)


class ToolSurfaceError(RuntimeError):
    """The QMX servers cannot be built from these defs."""


class OrderToolRefused(RuntimeError):
    """An external MCP server offers a tool whose name spells an order act."""


def rule_rows(table: object) -> tuple[Rule, ...]:
    """His list as `Rule`s: each row a `{pattern, ...}` table or a bare pattern string, as
    `ControlService` stores `[rules]`. A row that does not parse is skipped."""
    found: list[Rule] = []
    for row in cast("list[object]", table) if isinstance(table, list) else []:
        text = cast("Mapping[str, object]", row).get("pattern") if isinstance(row, Mapping) else row
        if isinstance(text, str):
            with contextlib.suppress(ValueError):
                found.append(Rule.parse(text))
    return tuple(found)


def is_proposal_writer(target: object) -> bool:
    return getattr(target, "__func__", None) is BrokerService.propose_order


def surface(toolsets: Iterable[str] | None, defs: Iterable[ToolDef]) -> frozenset[str]:
    """The servers a chat has switched on: `toolsets` (None is every core toolset) among the
    toolsets `defs` serve."""
    served = {tool.toolset for tool in defs}
    wanted = CORE_TOOLSETS if toolsets is None else tuple(toolsets)
    return frozenset(server_name(name) for name in wanted if name in served)


def build_servers(
    defs: list[ToolDef],
    *,
    grants: Grants,
    domain_write: DomainWritePolicy,
    enforce_grants: bool = True,
) -> dict[str, McpSdkServerConfig]:
    """One `create_sdk_mcp_server(name="qmx_<toolset>")` per toolset in `defs`. Refuses to
    build on a duplicate or unservable name and on PROPOSE_MONEY on anything but the broker's
    `propose_order` (identity, not name). Every asking tool's handler first consumes a grant for
    its exact arguments and returns an error naming the rule without one.
    `enforce_grants=False` exists for one live check only (`TestMode.grants`)."""
    names = [tool.name for tool in defs]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ToolSurfaceError(f"duplicate QMX tool names: {', '.join(duplicates)}")
    problems = [problem for name in names if (problem := name_problem(name)) is not None]
    if problems:
        raise ToolSurfaceError("; ".join(problems))
    for tool in defs:
        if tool.effect is Effect.PROPOSE_MONEY and not is_proposal_writer(tool.target):
            raise ToolSurfaceError(
                f"{tool.name} is not the broker's propose_order and cannot propose money"
            )
    toolsets: dict[str, list[ToolDef]] = {}
    for tool in defs:
        toolsets.setdefault(tool.toolset, []).append(tool)
    return {
        server_name(toolset): create_sdk_mcp_server(
            server_name(toolset),
            tools=sdk_tools(found, grants, domain_write, enforce_grants=enforce_grants),
        )
        for toolset, found in toolsets.items()
    }


def sdk_tools(
    defs: list[ToolDef],
    grants: Grants,
    domain_write: DomainWritePolicy,
    *,
    enforce_grants: bool = True,
) -> list[SdkMcpTool[Any]]:
    """A server's tools, each named by its op. Each asking tool's handler consumes a grant."""
    return [
        SdkMcpTool(
            tool.op,
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
        if not grants.consume(tool.full, args_digest(tool.full, arguments)):
            return failure(
                "not_approved",
                f"{tool.name} runs only after you approve these exact arguments, and no "
                "approval was given",
            )
        return await tool.call(arguments)

    return call


def keyring_refs(control: ControlService) -> frozenset[str]:
    """Every `qmx/*` reference named in settings.toml [providers], [brokers] and
    [mcp_servers], plus the fixed entries, casefolded. Names only; nothing is read."""
    found: set[str] = set(FIXED_REFS)

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


def _both(paths: list[Path]) -> tuple[str, ...]:
    """Each path as written (absolute) and as resolved, so a home behind a junction or link
    matches either spelling."""
    home = str(Path.home())
    return tuple(
        dict.fromkeys(
            normalize_path(str(form), cwd="/", home=home, case_insensitive=False)
            for path in paths
            for form in (path.absolute(), path.resolve())
        )
    )


def secret_files(home: QmxHome) -> list[Path]:
    """Files that hold or may hold a login or a key: the plan login in both forms under each
    QMX Claude home and his `~/.claude`, his `~/.claude.json`, and the QMX home's
    `settings.toml` and `rclone.conf`."""
    personal = Path.home() / ".claude"
    return [
        folder / name
        for folder in (home.plan_dir, home.relayed_dir, personal)
        for name in (".credentials.json", ".claude.json")
    ] + [Path.home() / ".claude.json", home.root / "settings.toml", home.root / "rclone.conf"]


STORE_FILES: Final = ("control.db", "portfolio.db", "library.db", "memory.db", "runs.db")
"""The QMX home's SQLite stores, each with its `-wal`, `-shm` and `-journal` files."""


def guard_rules(
    defs: list[ToolDef],
    *,
    domain_write: DomainWritePolicy,
    home: QmxHome,
    config_dir: Path,
    keyring_names: frozenset[str],
    unattended: bool,
    external_unattended: frozenset[str],
    workspace: Path | None = None,
    rules: Mapping[str, object] | None = None,
    on: frozenset[str] | None = None,
) -> GuardRules:
    """Derive `GuardRules` from the same defs: `mandatory_asks` are the full names where
    `asks(effect, domain_write)`, and the QMX servers are each toolset's, of which `on` (None
    is all) form the chat's surface. Paths come from `home`, the OS user's home and this
    Python's environment. `workspace` is where a recursive delete runs without asking; `rules`
    is `settings.toml [rules]`, his two lists."""
    personal = Path.home() / ".claude"
    protected = [
        home.plan_dir,
        home.relayed_dir,
        home.chats_dir,
        home.procs_dir,
        home.state_dir,
        home.plugin_dir,
        home.root / "engine",
        *(
            home.root / f"{name}{suffix}"
            for name in STORE_FILES
            for suffix in ("", "-wal", "-shm", "-journal")
        ),
        home.root / "settings.toml",
    ]
    lists = rules or {}
    servers = frozenset(server_name(tool.toolset) for tool in defs)
    return GuardRules(
        mandatory_asks=frozenset(tool.full for tool in defs if asks(tool.effect, domain_write)),
        protected_paths=_both(protected),
        qmx_homes=_both([home.root]),
        writable_paths=_both([home.workspaces_dir, home.agent_memory_dir]),
        install_paths=_both([Path(sys.prefix)]),
        secret_paths=_both(secret_files(home)),
        personal_homes=_both([personal]),
        keyring_names=frozenset(name.casefold() for name in keyring_names),
        delete_zones=() if workspace is None else _both([workspace]),
        never=rule_rows(lists.get("never_allow")),
        always=rule_rows(lists.get("always_allow")),
        variables=MappingProxyType(
            {
                "HOME": _posix(Path.home()),
                "USERPROFILE": _posix(Path.home()),
                "CLAUDE_CONFIG_DIR": _posix(config_dir),
            }
        ),
        case_insensitive=sys.platform in ("win32", "darwin"),
        unattended=unattended,
        external_unattended=external_unattended,
        qmx_servers=servers,
        surface=set(servers if on is None else on & servers),
    )


VET_TIMEOUT_S: Final = 30.0


@dataclass(frozen=True)
class VettedServers:
    """External MCP servers that passed `vet_mcp_servers`, as SDK configs with the tool names
    vetting saw, and each refused server with its reason. Only `configs` reach `mcp_servers`;
    `strict_mcp_config=True` makes the CLI ignore every other MCP config (02a section 7)."""

    configs: Mapping[str, McpServerConfig]
    tools: Mapping[str, frozenset[str]]
    refused: Mapping[str, str]


class VetCache:
    """Tool names vetted per config digest, for one harness. A changed row has a new digest
    and is vetted again. A server that changes its tools under the same row is caught after
    connect (`unvetted_tools`)."""

    def __init__(self) -> None:
        self._tools: dict[str, frozenset[str]] = {}

    def get(self, digest: str) -> frozenset[str] | None:
        return self._tools.get(digest)

    def put(self, digest: str, tools: frozenset[str]) -> None:
        self._tools[digest] = tools


def config_digest(config: McpServerConfig) -> str:
    body = json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode()).hexdigest()


SERVER_NAME: Final = re.compile(r"[A-Za-z0-9-]+(?:_[A-Za-z0-9-]+)*")
"""An external MCP server name the CLI keeps unchanged in its tool names, with no `__`."""


def server_config(name: str, row: Mapping[str, object]) -> McpServerConfig:
    """One settings.toml [mcp_servers] row as an SDK config: `command` with `args` and `env`
    for stdio, or `url` for HTTP. Raises ValueError naming what is wrong."""
    if is_qmx_server(name):
        raise ValueError(f"the names {SERVER} and {SERVER}_* belong to QMX's own tools")
    if not SERVER_NAME.fullmatch(name):
        raise ValueError(
            "a server name takes letters, digits, - and single _ between them, so its tools "
            "read as mcp__<server>__<tool>"
        )
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
    from mcp.types import PaginatedRequestParams  # noqa: PLC0415

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
        found: list[Any] = []
        cursor: str | None = None
        while True:
            params = PaginatedRequestParams(cursor=cursor) if cursor else None
            page = await session.list_tools(params=params)
            found += page.tools
            cursor = page.next_cursor
            if not cursor:
                return found


@dataclass(frozen=True)
class VettedServer:
    config: McpServerConfig
    tools: frozenset[str]


async def vet_server(name: str, row: Mapping[str, object], cache: VetCache) -> VettedServer:
    """Start one declared server with the Python MCP client, list every page of its tools and
    refuse it when a tool name spells an order act (`money_words`, H58). A config already in
    `cache` is not started again. Raises ValueError or OrderToolRefused."""
    config = server_config(name, row)
    digest = config_digest(config)
    cached = cache.get(digest)
    if cached is not None:
        return VettedServer(config, cached)
    listed = await asyncio.wait_for(_list_tools(config), VET_TIMEOUT_S)
    tools = frozenset(str(tool.name) for tool in listed)
    for tool in sorted(tools):
        act = named_money_act(tool)
        if act is not None:
            raise OrderToolRefused(f"{tool} is {act}")
    cache.put(digest, tools)
    return VettedServer(config, tools)


async def vet_mcp_servers(declared: Mapping[str, object], cache: VetCache) -> VettedServers:
    """Before any launch uses them: vet every enabled server in settings.toml [mcp_servers],
    all at once. A server that offers an order-shaped tool, or that cannot be listed, is refused
    and never launched (H58). A tool the CLI loads that vetting never saw refuses the launch."""
    rows = {
        name: cast("Mapping[str, object]", row)
        for name, row in declared.items()
        if isinstance(row, Mapping) and cast("Mapping[str, object]", row).get("enabled", True)
    }
    results = await asyncio.gather(
        *(vet_server(name, row, cache) for name, row in rows.items()), return_exceptions=True
    )
    configs: dict[str, McpServerConfig] = {}
    tools: dict[str, frozenset[str]] = {}
    refused: dict[str, str] = {}
    for name, result in zip(rows, results, strict=True):
        match result:
            case VettedServer():
                configs[name], tools[name] = result.config, result.tools
            case OrderToolRefused():
                refused[name] = f"it offers an order tool ({result})"
            case Exception():
                refused[name] = f"it could not be vetted ({type(result).__name__}: {result})"
            case _:
                raise result
    return VettedServers(
        MappingProxyType(configs), MappingProxyType(tools), MappingProxyType(refused)
    )


def unvetted_tools(status: McpStatusResponse, vetted: Mapping[str, frozenset[str]]) -> list[str]:
    """`server: tool` for each tool the CLI loaded from a vetted server that vetting never
    saw. The CLI may report a name bare or as `mcp__<server>__<tool>`."""
    return sorted(
        f"{server['name']}: {bare}"
        for server in status["mcpServers"]
        if server["name"] in vetted
        for tool in server.get("tools", [])
        if (bare := tool["name"].removeprefix(f"mcp__{server['name']}__"))
        not in vetted[server["name"]]
    )
